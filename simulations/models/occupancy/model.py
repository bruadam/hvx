"""
Occupancy detection and estimation from CO2 patterns.

Infers occupancy patterns from CO2 concentration changes.
Higher CO2 indicates occupancy, decreasing CO2 indicates vacancy.
"""

from dataclasses import dataclass
from typing import List, Tuple
import pandas as pd


@dataclass
class OccupancyPattern:
    """Detected occupancy pattern."""
    occupied_periods: List[Tuple[pd.Timestamp, pd.Timestamp]]
    avg_co2_occupied: float
    avg_co2_unoccupied: float
    typical_occupancy_hours: List[int]  # Hour of day (0-23)
    occupancy_rate: float  # 0-1, fraction of time occupied
    estimated_occupant_count: int
    description: str


class OccupancyCalculator:
    """
    Detect occupancy patterns and estimate occupant count from CO2 data.

    Uses threshold-based and rate-of-change detection.
    """

    # CO2 generation rate per person (L/s of CO2)
    # At sedentary activity: ~0.0052 L/s per person
    # At office work: ~0.0063 L/s per person
    CO2_GENERATION_RATE_PER_PERSON = 0.0063  # L/s

    # CO2 generation in ppm increase
    # Depends on ventilation rate, but approximate
    CO2_INCREASE_PER_PERSON = 150  # ppm per person (typical office)

    def __init__(
        self,
        occupied_threshold: float = 600.0,
        unoccupied_threshold: float = 500.0,
        outdoor_co2: float = 400.0,
    ):
        """
        Initialize occupancy detector.

        Args:
            occupied_threshold: CO2 above this = likely occupied (ppm)
            unoccupied_threshold: CO2 below this = likely unoccupied (ppm)
            outdoor_co2: Baseline outdoor CO2 (ppm)
        """
        self.occupied_threshold = occupied_threshold
        self.unoccupied_threshold = unoccupied_threshold
        self.outdoor_co2 = outdoor_co2

    def detect_occupancy(
        self,
        co2_series: pd.Series,
    ) -> OccupancyPattern:
        """
        Detect occupancy pattern from CO2 time series.

        Args:
            co2_series: Time series of CO2 measurements

        Returns:
            OccupancyPattern with detected patterns
        """
        # Create occupancy mask
        occupancy_mask = co2_series > self.occupied_threshold

        # Identify occupied periods
        occupied_periods = self._identify_periods(co2_series.index, occupancy_mask)

        # Calculate statistics
        if occupancy_mask.any():
            avg_co2_occupied = float(co2_series[occupancy_mask].mean())
        else:
            avg_co2_occupied = self.outdoor_co2

        if (~occupancy_mask).any():
            avg_co2_unoccupied = float(co2_series[~occupancy_mask].mean())
        else:
            avg_co2_unoccupied = self.outdoor_co2

        # Typical occupancy hours
        typical_hours = []
        if isinstance(co2_series.index, pd.DatetimeIndex):
            occupied_hours_count = occupancy_mask.groupby(co2_series.index.hour).sum()
            typical_hours = occupied_hours_count[occupied_hours_count > 0].index.tolist()

        # Occupancy rate
        occupancy_rate = float(occupancy_mask.sum() / len(occupancy_mask))

        # Estimate occupant count
        co2_increase = avg_co2_occupied - avg_co2_unoccupied
        estimated_occupants = max(1, int(co2_increase / self.CO2_INCREASE_PER_PERSON))

        # Description
        if occupancy_rate > 0.8:
            occ_desc = "heavily occupied"
        elif occupancy_rate > 0.5:
            occ_desc = "frequently occupied"
        elif occupancy_rate > 0.2:
            occ_desc = "occasionally occupied"
        else:
            occ_desc = "rarely occupied"

        if typical_hours:
            hours_str = self._format_hours(typical_hours)
            description = (
                f"Room is {occ_desc} ({occupancy_rate*100:.1f}% of time). "
                f"Typical hours: {hours_str}. "
                f"Estimated {estimated_occupants} occupants. "
                f"Avg CO2: {avg_co2_occupied:.0f} ppm (occupied), "
                f"{avg_co2_unoccupied:.0f} ppm (unoccupied)."
            )
        else:
            description = (
                f"Room is {occ_desc} ({occupancy_rate*100:.1f}% of time). "
                f"Estimated {estimated_occupants} occupants. "
                f"Avg CO2: {avg_co2_occupied:.0f} ppm (occupied), "
                f"{avg_co2_unoccupied:.0f} ppm (unoccupied)."
            )

        return OccupancyPattern(
            occupied_periods=occupied_periods,
            avg_co2_occupied=round(avg_co2_occupied, 1),
            avg_co2_unoccupied=round(avg_co2_unoccupied, 1),
            typical_occupancy_hours=typical_hours,
            occupancy_rate=round(occupancy_rate, 3),
            estimated_occupant_count=estimated_occupants,
            description=description,
        )

    def estimate_occupant_count(
        self,
        co2_occupied: float,
        co2_unoccupied: float,
        volume_m3: float,
        ventilation_ach: float
    ) -> int:
        """
        Estimate occupant count using CO2 mass balance.

        Args:
            co2_occupied: CO2 during occupied periods (ppm)
            co2_unoccupied: CO2 during unoccupied periods (ppm)
            volume_m3: Room volume (m³)
            ventilation_ach: Air change rate (ACH)

        Returns:
            Estimated number of occupants
        """
        # CO2 mass balance:
        # N * G = V * ACH * (C_in - C_out) / 1000000
        # Where:
        # N = number of occupants
        # G = CO2 generation per person (L/s)
        # V = volume (m³)
        # ACH = air changes per hour
        # C_in = indoor CO2 (ppm)
        # C_out = outdoor CO2 (ppm)

        co2_increase_ppm = co2_occupied - co2_unoccupied

        if co2_increase_ppm <= 0 or ventilation_ach <= 0:
            return 1

        # Convert ACH to L/s
        ventilation_l_s = (ventilation_ach * volume_m3 * 1000) / 3600

        # CO2 increase in volume fraction
        co2_increase_fraction = co2_increase_ppm / 1_000_000

        # N = (V_vent * delta_CO2) / G
        n_occupants = (ventilation_l_s * co2_increase_fraction) / self.CO2_GENERATION_RATE_PER_PERSON

        return max(1, int(round(n_occupants)))

    def _identify_periods(
        self,
        index: pd.Index,
        mask: pd.Series,
    ) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
        """Identify continuous periods where mask is True."""
        if not isinstance(index, pd.DatetimeIndex):
            return []

        periods = []
        in_period = False
        period_start = None

        for i, (ts, is_occupied) in enumerate(zip(index, mask, strict=False)):
            if is_occupied and not in_period:
                in_period = True
                period_start = ts
            elif not is_occupied and in_period:
                periods.append((period_start, index[i - 1]))
                in_period = False
                period_start = None

        # Handle period extending to end
        if in_period and period_start is not None:
            periods.append((period_start, index[-1]))

        return periods

    def _format_hours(self, hours: List[int]) -> str:
        """Format list of hours into readable string."""
        if not hours:
            return "none"

        # Group consecutive hours
        groups = []
        current_group = [hours[0]]

        for hour in hours[1:]:
            if hour == current_group[-1] + 1:
                current_group.append(hour)
            else:
                groups.append(current_group)
                current_group = [hour]

        groups.append(current_group)

        # Format groups
        formatted = []
        for group in groups:
            if len(group) == 1:
                formatted.append(f"{group[0]:02d}:00")
            else:
                formatted.append(f"{group[0]:02d}:00-{group[-1]:02d}:00")

        return ", ".join(formatted)
