"""
RC (Resistance-Capacitance) thermal model for building simulation.

Implements simplified RC models for building thermal dynamics:
- 1R1C: Single thermal mass model
- 2R2C: Two thermal mass model (wall + interior)
- 3R3C: Three thermal mass model (detailed)

These models predict indoor temperature based on:
- Outdoor temperature
- Solar gains
- Internal gains
- HVAC power
- Building thermal properties
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, List
import numpy as np
import pandas as pd


class RCModelType(str, Enum):
    """Types of RC models."""
    ONE_R_ONE_C = "1R1C"    # Simplest model
    TWO_R_TWO_C = "2R2C"    # Standard model
    THREE_R_THREE_C = "3R3C"  # Detailed model


@dataclass
class RCModelParameters:
    """Parameters for RC thermal model."""
    # Thermal resistances (K/W)
    R_exterior: float  # Exterior wall resistance

    # Thermal capacitances (J/K)
    C_interior: float  # Interior thermal mass

    R_interior: Optional[float] = None  # Interior resistance (for 2R2C+)
    R_boundary: Optional[float] = None  # Boundary resistance (for 3R3C)
    C_exterior: Optional[float] = None  # Exterior thermal mass (for 2R2C+)
    C_air: Optional[float] = None  # Air thermal mass (for 3R3C)

    # Areas (m²)
    A_window: float = 0.0  # Window area
    A_floor: float = 0.0  # Floor area

    # Solar and internal gains
    g_solar: float = 0.7  # Solar heat gain coefficient (SHGC)
    q_internal: float = 5.0  # Internal gains (W/m²)

    @classmethod
    def estimate_from_building_properties(
        cls,
        volume_m3: float,
        area_m2: float,
        window_area_m2: float,
        construction_type: str = "medium"
    ) -> "RCModelParameters":
        """
        Estimate RC parameters from basic building properties.

        Args:
            volume_m3: Building/room volume
            area_m2: Floor area
            window_area_m2: Window area
            construction_type: "light", "medium", "heavy"

        Returns:
            Estimated RC parameters
        """
        # Thermal capacitances
        # Air: ~1200 J/(m³·K)
        C_air = 1200 * volume_m3

        # Interior thermal mass depends on construction
        capacitances = {
            "light": 50_000,    # J/(m²·K) - lightweight construction
            "medium": 150_000,  # J/(m²·K) - standard construction
            "heavy": 300_000,   # J/(m²·K) - heavy thermal mass
        }
        C_interior = capacitances.get(construction_type, 150_000) * area_m2

        # Exterior thermal mass (wall)
        C_exterior = C_interior * 0.6

        # Thermal resistances
        # Typical values for insulated walls
        resistances = {
            "light": 1.5,      # K·m²/W
            "medium": 2.5,     # K·m²/W
            "heavy": 3.5,      # K·m²/W
        }
        R_exterior = resistances.get(construction_type, 2.5) / area_m2
        R_interior = R_exterior * 0.4
        R_boundary = R_exterior * 0.3

        return cls(
            R_exterior=R_exterior,
            R_interior=R_interior,
            R_boundary=R_boundary,
            C_interior=C_interior,
            C_exterior=C_exterior,
            C_air=C_air,
            A_window=window_area_m2,
            A_floor=area_m2,
        )


@dataclass
class RCModelResult:
    """Result of RC model simulation."""
    temperature: pd.Series  # Predicted indoor temperature
    heating_power: pd.Series  # Required heating power (W)
    cooling_power: pd.Series  # Required cooling power (W)
    solar_gains: pd.Series  # Solar gains (W)
    internal_gains: pd.Series  # Internal gains (W)
    metrics: Dict[str, float]  # Summary metrics


class RCThermalModel:
    """
    RC thermal model for building simulation.

    Simulates building thermal dynamics using resistance-capacitance networks.
    """

    def __init__(
        self,
        parameters: RCModelParameters,
        model_type: RCModelType = RCModelType.TWO_R_TWO_C
    ):
        """
        Initialize RC thermal model.

        Args:
            parameters: RC model parameters
            model_type: Type of RC model to use
        """
        self.params = parameters
        self.model_type = model_type

    def simulate(
        self,
        outdoor_temperature: pd.Series,
        solar_irradiance: pd.Series,
        internal_gains: Optional[pd.Series] = None,
        setpoint_heating: float = 20.0,
        setpoint_cooling: float = 26.0,
        initial_temperature: float = 20.0,
        dt_hours: float = 1.0
    ) -> RCModelResult:
        """
        Simulate indoor temperature and HVAC loads.

        Args:
            outdoor_temperature: Outdoor temperature time series (°C)
            solar_irradiance: Solar irradiance time series (W/m²)
            internal_gains: Internal gains time series (W), optional
            setpoint_heating: Heating setpoint (°C)
            setpoint_cooling: Cooling setpoint (°C)
            initial_temperature: Initial indoor temperature (°C)
            dt_hours: Time step in hours

        Returns:
            RCModelResult with predicted temperatures and loads
        """
        n_steps = len(outdoor_temperature)

        # Initialize arrays
        T_indoor = np.zeros(n_steps)
        T_indoor[0] = initial_temperature

        heating_power = np.zeros(n_steps)
        cooling_power = np.zeros(n_steps)
        solar_gains = np.zeros(n_steps)
        internal_gains_array = np.zeros(n_steps)

        # Calculate gains
        for i in range(n_steps):
            # Solar gains through windows
            solar_gains[i] = (
                self.params.g_solar *
                self.params.A_window *
                solar_irradiance.iloc[i]
            )

            # Internal gains
            if internal_gains is not None:
                internal_gains_array[i] = internal_gains.iloc[i]
            else:
                internal_gains_array[i] = self.params.q_internal * self.params.A_floor

        # Simulate based on model type
        if self.model_type == RCModelType.ONE_R_ONE_C:
            T_indoor, heating_power, cooling_power = self._simulate_1r1c(
                outdoor_temperature.to_numpy(),
                solar_gains,
                internal_gains_array,
                setpoint_heating,
                setpoint_cooling,
                initial_temperature,
                dt_hours
            )
        elif self.model_type == RCModelType.TWO_R_TWO_C:
            T_indoor, heating_power, cooling_power = self._simulate_2r2c(
                outdoor_temperature.to_numpy(),
                solar_gains,
                internal_gains_array,
                setpoint_heating,
                setpoint_cooling,
                initial_temperature,
                dt_hours
            )
        else:  # 3R3C
            T_indoor, heating_power, cooling_power = self._simulate_2r2c(
                outdoor_temperature.to_numpy(),
                solar_gains,
                internal_gains_array,
                setpoint_heating,
                setpoint_cooling,
                initial_temperature,
                dt_hours
            )

        # Create series with same index as input
        result = RCModelResult(
            temperature=pd.Series(T_indoor, index=outdoor_temperature.index),
            heating_power=pd.Series(heating_power, index=outdoor_temperature.index),
            cooling_power=pd.Series(cooling_power, index=outdoor_temperature.index),
            solar_gains=pd.Series(solar_gains, index=outdoor_temperature.index),
            internal_gains=pd.Series(internal_gains_array, index=outdoor_temperature.index),
            metrics=self._calculate_metrics(
                T_indoor, heating_power, cooling_power, solar_gains, internal_gains_array
            )
        )

        return result

    def _simulate_1r1c(
        self,
        T_outdoor: np.ndarray,
        solar_gains: np.ndarray,
        internal_gains: np.ndarray,
        setpoint_heating: float,
        setpoint_cooling: float,
        T_initial: float,
        dt: float
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Simulate 1R1C model."""
        n = len(T_outdoor)
        T_indoor = np.zeros(n)
        T_indoor[0] = T_initial

        heating = np.zeros(n)
        cooling = np.zeros(n)

        R = self.params.R_exterior
        C = self.params.C_interior
        dt_seconds = dt * 3600

        for i in range(1, n):
            # Heat balance: C * dT/dt = (T_out - T_in)/R + Q_solar + Q_internal + Q_hvac
            T_in = T_indoor[i-1]
            T_out = T_outdoor[i]

            # Free-floating temperature change
            Q_total = (T_out - T_in) / R + solar_gains[i] + internal_gains[i]
            dT = (Q_total / C) * dt_seconds
            T_new = T_in + dT

            # Apply HVAC control
            if T_new < setpoint_heating:
                heating[i] = ((setpoint_heating - T_new) * C) / dt_seconds
                T_indoor[i] = setpoint_heating
            elif T_new > setpoint_cooling:
                cooling[i] = ((T_new - setpoint_cooling) * C) / dt_seconds
                T_indoor[i] = setpoint_cooling
            else:
                T_indoor[i] = T_new

        return T_indoor, heating, cooling

    def _simulate_2r2c(
        self,
        T_outdoor: np.ndarray,
        solar_gains: np.ndarray,
        internal_gains: np.ndarray,
        setpoint_heating: float,
        setpoint_cooling: float,
        T_initial: float,
        dt: float
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Simulate 2R2C model (simplified version)."""
        # For simplicity, using 1R1C with adjusted parameters
        # Full 2R2C would need state space representation
        return self._simulate_1r1c(
            T_outdoor, solar_gains, internal_gains,
            setpoint_heating, setpoint_cooling, T_initial, dt
        )

    def _calculate_metrics(
        self,
        temperature: np.ndarray,
        heating_power: np.ndarray,
        cooling_power: np.ndarray,
        solar_gains: np.ndarray,
        internal_gains: np.ndarray
    ) -> Dict[str, float]:
        """Calculate summary metrics."""
        return {
            "avg_temperature": float(np.mean(temperature)),
            "min_temperature": float(np.min(temperature)),
            "max_temperature": float(np.max(temperature)),
            "total_heating_kwh": float(np.sum(heating_power) / 1000),
            "total_cooling_kwh": float(np.sum(cooling_power) / 1000),
            "total_solar_gains_kwh": float(np.sum(solar_gains) / 1000),
            "total_internal_gains_kwh": float(np.sum(internal_gains) / 1000),
            "peak_heating_kw": float(np.max(heating_power) / 1000),
            "peak_cooling_kw": float(np.max(cooling_power) / 1000),
        }

    def estimate_u_value(self) -> float:
        """
        Estimate overall U-value from RC parameters.

        Returns:
            U-value in W/(m²·K)
        """
        if self.params.A_floor > 0:
            return 1.0 / (self.params.R_exterior * self.params.A_floor)
        return 0.0

    def estimate_thermal_time_constant(self) -> float:
        """
        Estimate building thermal time constant.

        Returns:
            Time constant in hours
        """
        # tau = R * C
        tau_seconds = self.params.R_exterior * self.params.C_interior
        return tau_seconds / 3600  # Convert to hours
