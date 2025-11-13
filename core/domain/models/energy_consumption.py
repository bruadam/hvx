"""Building energy consumption tracking model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from core.domain.enums.countries import Country


class EnergyConsumption(BaseModel):
    """
    Tracks energy consumption data for a building across different systems.

    Supports multiple units with automatic conversion to kWh for EPC calculations.
    """

    # Measurement period
    measurement_start: datetime = Field(..., description="Start of measurement period")
    measurement_end: datetime = Field(..., description="End of measurement period")

    # Heating consumption
    heating_kwh: float = Field(default=0.0, ge=0, description="Heating energy consumption in kWh")
    heating_gas_m3: float | None = Field(default=None, ge=0, description="Natural gas consumption in m³")
    heating_oil_liters: float | None = Field(default=None, ge=0, description="Heating oil consumption in liters")
    heating_district_kwh: float | None = Field(default=None, ge=0, description="District heating in kWh")

    # Cooling consumption
    cooling_kwh: float = Field(default=0.0, ge=0, description="Cooling energy consumption in kWh")

    # Electricity consumption
    electricity_kwh: float = Field(default=0.0, ge=0, description="Electricity consumption in kWh")
    electricity_lighting_kwh: float | None = Field(default=None, ge=0, description="Lighting electricity in kWh")
    electricity_appliances_kwh: float | None = Field(default=None, ge=0, description="Appliances electricity in kWh")
    electricity_hvac_kwh: float | None = Field(default=None, ge=0, description="HVAC electricity in kWh")

    # Hot water consumption
    hot_water_kwh: float = Field(default=0.0, ge=0, description="Hot water energy consumption in kWh")
    hot_water_liters: float | None = Field(default=None, ge=0, description="Hot water consumption in liters")

    # Ventilation consumption
    ventilation_kwh: float = Field(default=0.0, ge=0, description="Ventilation energy consumption in kWh")

    # Water consumption (for reference, not part of EPC)
    cold_water_m3: float | None = Field(default=None, ge=0, description="Cold water consumption in m³")

    # Renewable energy generation (reduces EPC rating)
    solar_pv_kwh: float | None = Field(default=0.0, ge=0, description="Solar PV energy generated in kWh")
    wind_kwh: float | None = Field(default=0.0, ge=0, description="Wind energy generated in kWh")
    other_renewable_kwh: float | None = Field(default=0.0, ge=0, description="Other renewable energy in kWh")

    # Metadata
    notes: str | None = Field(default=None, description="Additional notes about the consumption data")

    @property
    def total_heating_kwh(self) -> float:
        """Calculate total heating energy in kWh including all heating sources."""
        total = self.heating_kwh

        # Convert natural gas (m³ to kWh)
        # 1 m³ natural gas ≈ 10.0 kWh (typical conversion factor)
        if self.heating_gas_m3:
            total += self.heating_gas_m3 * 10.0

        # Convert heating oil (liters to kWh)
        # 1 liter heating oil ≈ 10.0 kWh (typical conversion factor)
        if self.heating_oil_liters:
            total += self.heating_oil_liters * 10.0

        # Add district heating
        if self.heating_district_kwh:
            total += self.heating_district_kwh

        return total

    @property
    def total_electricity_kwh(self) -> float:
        """Calculate total electricity consumption in kWh."""
        # If we have breakdowns, use them; otherwise use total
        if any([
            self.electricity_lighting_kwh,
            self.electricity_appliances_kwh,
            self.electricity_hvac_kwh
        ]):
            return (
                (self.electricity_lighting_kwh or 0.0) +
                (self.electricity_appliances_kwh or 0.0) +
                (self.electricity_hvac_kwh or 0.0)
            )
        return self.electricity_kwh

    @property
    def total_hot_water_kwh(self) -> float:
        """Calculate total hot water energy in kWh."""
        total = self.hot_water_kwh

        # Convert liters to kWh
        # Assuming: heating water from 10°C to 60°C (ΔT = 50K)
        # Energy = Volume (L) × 4.18 kJ/(L·K) × ΔT / 3600 (to convert to kWh)
        # ≈ Volume (L) × 0.058 kWh/L
        if self.hot_water_liters:
            total += self.hot_water_liters * 0.058

        return total

    @property
    def total_renewable_kwh(self) -> float:
        """Calculate total renewable energy generation in kWh."""
        return (
            (self.solar_pv_kwh or 0.0) +
            (self.wind_kwh or 0.0) +
            (self.other_renewable_kwh or 0.0)
        )

    @property
    def measurement_period_days(self) -> int:
        """Get the measurement period in days."""
        return (self.measurement_end - self.measurement_start).days

    def annualize(self) -> "EnergyConsumption":
        """
        Convert consumption to annual values if measurement period is not 365 days.

        Returns:
            New EnergyConsumption instance with annualized values
        """
        days = self.measurement_period_days
        if days == 0:
            raise ValueError("Measurement period cannot be zero days")

        factor = 365.0 / days

        return EnergyConsumption(
            measurement_start=self.measurement_start,
            measurement_end=self.measurement_end,
            heating_kwh=self.heating_kwh * factor,
            heating_gas_m3=self.heating_gas_m3 * factor if self.heating_gas_m3 else None,
            heating_oil_liters=self.heating_oil_liters * factor if self.heating_oil_liters else None,
            heating_district_kwh=self.heating_district_kwh * factor if self.heating_district_kwh else None,
            cooling_kwh=self.cooling_kwh * factor,
            electricity_kwh=self.electricity_kwh * factor,
            electricity_lighting_kwh=self.electricity_lighting_kwh * factor if self.electricity_lighting_kwh else None,
            electricity_appliances_kwh=self.electricity_appliances_kwh * factor if self.electricity_appliances_kwh else None,
            electricity_hvac_kwh=self.electricity_hvac_kwh * factor if self.electricity_hvac_kwh else None,
            hot_water_kwh=self.hot_water_kwh * factor,
            hot_water_liters=self.hot_water_liters * factor if self.hot_water_liters else None,
            ventilation_kwh=self.ventilation_kwh * factor,
            cold_water_m3=self.cold_water_m3 * factor if self.cold_water_m3 else None,
            solar_pv_kwh=self.solar_pv_kwh * factor if self.solar_pv_kwh else None,
            wind_kwh=self.wind_kwh * factor if self.wind_kwh else None,
            other_renewable_kwh=self.other_renewable_kwh * factor if self.other_renewable_kwh else None,
            notes=f"Annualized from {days} days: {self.notes or ''}"
        )

    def calculate_primary_energy(
        self,
        country: Country,
        floor_area_m2: float
    ) -> float:
        """
        Calculate primary energy consumption per m² per year.

        Uses country-specific conversion factors to convert final energy to primary energy.

        Args:
            country: Country for primary energy factors
            floor_area_m2: Building floor area in m²

        Returns:
            Primary energy in kWh/m²/year
        """
        from core.domain.enums.epc import EPCRating

        # Annualize if needed
        if self.measurement_period_days != 365:
            consumption = self.annualize()
        else:
            consumption = self

        return EPCRating.calculate_primary_energy(
            heating_kwh=consumption.total_heating_kwh,
            cooling_kwh=consumption.cooling_kwh,
            electricity_kwh=consumption.total_electricity_kwh,
            hot_water_kwh=consumption.total_hot_water_kwh,
            country=country,
            floor_area_m2=floor_area_m2,
            renewable_energy_kwh=consumption.total_renewable_kwh
        )

    def get_summary(self) -> dict[str, Any]:
        """Get summary of energy consumption."""
        return {
            "period_days": self.measurement_period_days,
            "heating_kwh": self.total_heating_kwh,
            "cooling_kwh": self.cooling_kwh,
            "electricity_kwh": self.total_electricity_kwh,
            "hot_water_kwh": self.total_hot_water_kwh,
            "ventilation_kwh": self.ventilation_kwh,
            "renewable_kwh": self.total_renewable_kwh,
            "total_consumption_kwh": (
                self.total_heating_kwh +
                self.cooling_kwh +
                self.total_electricity_kwh +
                self.total_hot_water_kwh +
                self.ventilation_kwh
            ),
            "net_consumption_kwh": (
                self.total_heating_kwh +
                self.cooling_kwh +
                self.total_electricity_kwh +
                self.total_hot_water_kwh +
                self.ventilation_kwh -
                self.total_renewable_kwh
            ),
        }

    def __str__(self) -> str:
        """String representation."""
        summary = self.get_summary()
        return (
            f"EnergyConsumption(period={self.measurement_period_days}d, "
            f"total={summary['total_consumption_kwh']:.0f} kWh, "
            f"renewable={summary['renewable_kwh']:.0f} kWh)"
        )
