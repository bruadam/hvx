"""
Occupancy detection from CO2 patterns.

Infers occupancy patterns from CO2 concentration changes.
Higher CO2 = likely occupied, decreasing CO2 = likely unoccupied.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class OccupancyPattern:
    """Detected occupancy pattern."""

    occupied_periods: list[tuple[pd.Timestamp, pd.Timestamp]]
    avg_co2_occupied: float
    avg_co2_unoccupied: float
    typical_occupancy_hours: list[int]  # Hour of day (0-23)
    occupancy_rate: float  # 0-1, fraction of time occupied
    description: str


class OccupancyDetector:
    """
    Detect occupancy patterns from CO2 data.

    Uses threshold-based and rate-of-change detection.
    """

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
            OccupancyPattern
        """
        # Create occupancy mask (True = occupied)
        occupancy_mask = co2_series > self.occupied_threshold

        # Identify occupied periods
        occupied_periods = self._identify_periods(co2_series.index, occupancy_mask)

        # Calculate statistics
        avg_co2_occupied = float(co2_series[occupancy_mask].mean()) if occupancy_mask.any() else 0.0
        avg_co2_unoccupied = float(co2_series[~occupancy_mask].mean()) if (~occupancy_mask).any() else self.outdoor_co2

        # Typical occupancy hours
        if isinstance(co2_series.index, pd.DatetimeIndex):
            occupied_hours_count = occupancy_mask.groupby(co2_series.index.hour).sum()
            typical_hours = occupied_hours_count[occupied_hours_count > 0].index.tolist()
        else:
            typical_hours = []

        # Occupancy rate
        occupancy_rate = float(occupancy_mask.sum() / len(occupancy_mask))

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
                f"Typical occupancy hours: {hours_str}. "
                f"Average CO2: {avg_co2_occupied:.0f} ppm (occupied), "
                f"{avg_co2_unoccupied:.0f} ppm (unoccupied)."
            )
        else:
            description = (
                f"Room is {occ_desc} ({occupancy_rate*100:.1f}% of time). "
                f"Average CO2: {avg_co2_occupied:.0f} ppm (occupied), "
                f"{avg_co2_unoccupied:.0f} ppm (unoccupied)."
            )

        return OccupancyPattern(
            occupied_periods=occupied_periods,
            avg_co2_occupied=round(avg_co2_occupied, 1),
            avg_co2_unoccupied=round(avg_co2_unoccupied, 1),
            typical_occupancy_hours=typical_hours,
            occupancy_rate=round(occupancy_rate, 3),
            description=description,
        )

    def _identify_periods(
        self,
        index: pd.Index,
        mask: pd.Series,
    ) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
        """Identify continuous periods where mask is True."""
        if not isinstance(index, pd.DatetimeIndex):
            return []

        periods = []
        in_period = False
        period_start = None

        for i, (ts, is_occupied) in enumerate(zip(index, mask, strict=False)):
            if is_occupied and not in_period:
                # Start new period
                in_period = True
                period_start = ts
            elif not is_occupied and in_period:
                # End period
                periods.append((period_start, index[i - 1]))
                in_period = False
                period_start = None

        # Handle period extending to end
        if in_period and period_start is not None:
            periods.append((period_start, index[-1]))

        return periods

    def _format_hours(self, hours: list[int]) -> str:
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


def detect_occupancy_from_co2(
    co2_series: pd.Series,
    occupied_threshold: float = 600.0,
) -> OccupancyPattern:
    """
    Convenience function to detect occupancy from CO2.

    Args:
        co2_series: Time series of CO2 measurements
        occupied_threshold: CO2 threshold for occupancy (ppm)

    Returns:
        OccupancyPattern

    Example:
        >>> co2_data = pd.Series([450, 800, 950, 900, 850, 500, 420])
        >>> pattern = detect_occupancy_from_co2(co2_data, occupied_threshold=600)
        >>> print(pattern.occupancy_rate)
        0.571
    """
    detector = OccupancyDetector(occupied_threshold=occupied_threshold)
    return detector.detect_occupancy(co2_series)
