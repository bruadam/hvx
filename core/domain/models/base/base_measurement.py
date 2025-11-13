"""Base measurement models for consumption and sensor data.

Provides common functionality for time-series measurements like energy,
water, and other utility consumption tracking.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


TValue = TypeVar("TValue")


class BaseMeasurement(BaseModel, Generic[TValue]):
    """
    Base class for all measurement/consumption tracking.

    Supports:
    - Time-bounded measurements
    - Generic value types (float, dict, etc.)
    - Annualization for different measurement periods
    - Summary and aggregation

    Used for:
    - Energy consumption (electricity, gas, heating, etc.)
    - Water consumption
    - Any time-series resource tracking
    """

    # Measurement period
    measurement_start: datetime = Field(
        ...,
        description="Start of measurement period"
    )
    measurement_end: datetime = Field(
        ...,
        description="End of measurement period"
    )

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the measurement"
    )

    notes: str | None = Field(
        default=None,
        description="Optional notes about the measurement"
    )

    @property
    def measurement_period_days(self) -> int:
        """Get the measurement period in days."""
        delta = self.measurement_end - self.measurement_start
        return max(delta.days, 0)

    @property
    def measurement_period_hours(self) -> float:
        """Get the measurement period in hours."""
        delta = self.measurement_end - self.measurement_start
        return max(delta.total_seconds() / 3600, 0)

    def get_annualization_factor(self) -> float:
        """
        Calculate factor to convert measurement to annual values.

        Returns:
            Multiplication factor (365 / measurement_days)

        Raises:
            ValueError: If measurement period is zero
        """
        days = self.measurement_period_days
        if days == 0:
            raise ValueError("Measurement period cannot be zero days")
        return 365.0 / days

    def is_annual(self, tolerance_days: int = 3) -> bool:
        """
        Check if measurement period is approximately one year.

        Args:
            tolerance_days: Days of tolerance for annual period (default: 3)

        Returns:
            True if period is within tolerance of 365 days
        """
        days = self.measurement_period_days
        return abs(days - 365) <= tolerance_days

    def get_summary(self) -> dict[str, Any]:
        """Get summary of measurement period."""
        return {
            "measurement_start": self.measurement_start.isoformat(),
            "measurement_end": self.measurement_end.isoformat(),
            "period_days": self.measurement_period_days,
            "period_hours": round(self.measurement_period_hours, 2),
            "is_annual": self.is_annual(),
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"period={self.measurement_period_days}d, "
            f"start={self.measurement_start.date()})"
        )


class UtilityConsumption(BaseMeasurement[float]):
    """
    Base class for utility consumption tracking (energy, water, etc.).

    Supports:
    - Multiple consumption sources (e.g., grid, solar, gas)
    - Production tracking (e.g., PV generation, co-generation)
    - Unit conversion
    - Net consumption calculation
    - Annualization

    Can be used for:
    - Electricity (grid, PV production)
    - Gas (natural gas, biogas)
    - Water (municipal, well)
    - Heating (district, boiler, heat pump)
    - Fuel (oil, wood, hydrogen)
    """

    # Consumption sources
    consumption_by_source: dict[str, float] = Field(
        default_factory=dict,
        description="Consumption breakdown by source (e.g., {'grid': 1000, 'solar': 200})"
    )

    # Production sources (negative consumption)
    production_by_source: dict[str, float] = Field(
        default_factory=dict,
        description="Production breakdown by source (e.g., {'pv': 500, 'cogen': 100})"
    )

    # Unit information
    unit: str = Field(
        default="kWh",
        description="Measurement unit (kWh, m3, liters, etc.)"
    )

    # Conversion factors for unit conversions
    conversion_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Conversion factors to primary unit (e.g., {'m3_to_kwh': 10.0})"
    )

    @property
    def total_consumption(self) -> float:
        """Get total consumption across all sources."""
        return sum(self.consumption_by_source.values())

    @property
    def total_production(self) -> float:
        """Get total production across all sources."""
        return sum(self.production_by_source.values())

    @property
    def net_consumption(self) -> float:
        """
        Get net consumption (consumption - production).

        Can be negative if production exceeds consumption.
        """
        return self.total_consumption - self.total_production

    @property
    def self_consumption_rate(self) -> float:
        """
        Calculate self-consumption rate as percentage.

        Returns:
            Percentage of consumption covered by production (0-100+)
        """
        if self.total_consumption == 0:
            return 0.0
        return min((self.total_production / self.total_consumption) * 100, 100.0)

    def annualize(self) -> "UtilityConsumption":
        """
        Convert consumption to annual values.

        Returns:
            New UtilityConsumption instance with annualized values
        """
        if self.is_annual():
            return self

        factor = self.get_annualization_factor()

        annualized_consumption = {
            source: value * factor
            for source, value in self.consumption_by_source.items()
        }

        annualized_production = {
            source: value * factor
            for source, value in self.production_by_source.items()
        }

        return UtilityConsumption(
            measurement_start=self.measurement_start,
            measurement_end=self.measurement_end,
            consumption_by_source=annualized_consumption,
            production_by_source=annualized_production,
            unit=self.unit,
            conversion_factors=self.conversion_factors,
            metadata=self.metadata,
            notes=f"Annualized from {self.measurement_period_days} days: {self.notes or ''}"
        )

    def convert_source(
        self,
        source_name: str,
        conversion_key: str,
        target_unit: str | None = None
    ) -> float:
        """
        Convert a consumption source to different units.

        Args:
            source_name: Name of the consumption source
            conversion_key: Key in conversion_factors to use
            target_unit: Optional target unit name

        Returns:
            Converted value

        Raises:
            ValueError: If source or conversion factor not found
        """
        if source_name not in self.consumption_by_source:
            raise ValueError(f"Source '{source_name}' not found in consumption")

        if conversion_key not in self.conversion_factors:
            raise ValueError(f"Conversion factor '{conversion_key}' not found")

        value = self.consumption_by_source[source_name]
        factor = self.conversion_factors[conversion_key]

        return value * factor

    def get_summary(self) -> dict[str, Any]:
        """Get summary of utility consumption."""
        summary = super().get_summary()
        summary.update({
            "unit": self.unit,
            "total_consumption": round(self.total_consumption, 2),
            "total_production": round(self.total_production, 2),
            "net_consumption": round(self.net_consumption, 2),
            "self_consumption_rate": round(self.self_consumption_rate, 2),
            "consumption_sources": list(self.consumption_by_source.keys()),
            "production_sources": list(self.production_by_source.keys()),
        })
        return summary

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"period={self.measurement_period_days}d, "
            f"consumption={self.total_consumption:.0f} {self.unit}, "
            f"production={self.total_production:.0f} {self.unit})"
        )
