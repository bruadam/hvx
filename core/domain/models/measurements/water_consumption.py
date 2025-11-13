"""Water consumption tracking model."""

from typing import Any

from pydantic import Field

from core.domain.models.base.base_measurement import UtilityConsumption


class WaterConsumption(UtilityConsumption):
    """
    Tracks water consumption data for a building.

    Supports multiple water sources (municipal, well, rainwater, etc.)
    with unit tracking and conversion.

    Examples:
        - Municipal water
        - Well water
        - Rainwater harvesting
        - Greywater recycling
    """

    # Water sources (m³)
    municipal_water_m3: float = Field(
        default=0.0,
        ge=0,
        description="Municipal/mains water consumption in m³"
    )

    well_water_m3: float = Field(
        default=0.0,
        ge=0,
        description="Well water consumption in m³"
    )

    rainwater_m3: float = Field(
        default=0.0,
        ge=0,
        description="Rainwater harvested and used in m³"
    )

    greywater_recycled_m3: float = Field(
        default=0.0,
        ge=0,
        description="Greywater recycled and reused in m³"
    )

    # Water usage breakdown
    hot_water_m3: float | None = Field(
        default=None,
        ge=0,
        description="Hot water usage in m³"
    )

    cold_water_m3: float | None = Field(
        default=None,
        ge=0,
        description="Cold water usage in m³"
    )

    irrigation_m3: float | None = Field(
        default=None,
        ge=0,
        description="Irrigation water usage in m³"
    )

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to sync water sources with base consumption dict."""
        # Set unit
        self.unit = "m³"

        # Sync to consumption_by_source
        if self.municipal_water_m3 > 0:
            self.consumption_by_source["municipal"] = self.municipal_water_m3
        if self.well_water_m3 > 0:
            self.consumption_by_source["well"] = self.well_water_m3
        if self.rainwater_m3 > 0:
            self.consumption_by_source["rainwater"] = self.rainwater_m3
        if self.greywater_recycled_m3 > 0:
            self.consumption_by_source["greywater_recycled"] = self.greywater_recycled_m3

        # Usage breakdown
        if self.hot_water_m3:
            self.consumption_by_source["hot_water"] = self.hot_water_m3
        if self.cold_water_m3:
            self.consumption_by_source["cold_water"] = self.cold_water_m3
        if self.irrigation_m3:
            self.consumption_by_source["irrigation"] = self.irrigation_m3

        # Set conversion factors
        self.conversion_factors = {
            "m3_to_liters": 1000.0,  # 1 m³ = 1000 liters
            "m3_to_gallons": 264.172,  # 1 m³ = 264.172 US gallons
        }

    @property
    def total_water_m3(self) -> float:
        """Get total water consumption in m³."""
        return (
            self.municipal_water_m3 +
            self.well_water_m3 +
            self.rainwater_m3 +
            self.greywater_recycled_m3
        )

    @property
    def sustainable_water_percentage(self) -> float:
        """
        Calculate percentage of water from sustainable sources (non-municipal).

        Returns:
            Percentage (0-100) of water from sustainable sources
        """
        total = self.total_water_m3
        if total == 0:
            return 0.0

        sustainable = self.well_water_m3 + self.rainwater_m3 + self.greywater_recycled_m3
        return (sustainable / total) * 100

    def get_water_in_liters(self) -> float:
        """Get total water consumption in liters."""
        return self.total_water_m3 * 1000.0

    def annualize(self) -> "WaterConsumption":
        """
        Convert consumption to annual values.

        Returns:
            New WaterConsumption instance with annualized values
        """
        if self.is_annual():
            return self

        factor = self.get_annualization_factor()

        return WaterConsumption(
            measurement_start=self.measurement_start,
            measurement_end=self.measurement_end,
            municipal_water_m3=self.municipal_water_m3 * factor,
            well_water_m3=self.well_water_m3 * factor,
            rainwater_m3=self.rainwater_m3 * factor,
            greywater_recycled_m3=self.greywater_recycled_m3 * factor,
            hot_water_m3=self.hot_water_m3 * factor if self.hot_water_m3 else None,
            cold_water_m3=self.cold_water_m3 * factor if self.cold_water_m3 else None,
            irrigation_m3=self.irrigation_m3 * factor if self.irrigation_m3 else None,
            notes=f"Annualized from {self.measurement_period_days} days: {self.notes or ''}"
        )

    def get_summary(self) -> dict[str, Any]:
        """Get summary of water consumption."""
        summary = super().get_summary()
        summary.update({
            "total_water_m3": round(self.total_water_m3, 2),
            "total_water_liters": round(self.get_water_in_liters(), 2),
            "sustainable_water_percentage": round(self.sustainable_water_percentage, 2),
            "municipal_water_m3": round(self.municipal_water_m3, 2),
            "sustainable_sources_m3": round(
                self.well_water_m3 + self.rainwater_m3 + self.greywater_recycled_m3, 2
            ),
        })
        return summary

    def __str__(self) -> str:
        """String representation."""
        return (
            f"WaterConsumption(period={self.measurement_period_days}d, "
            f"total={self.total_water_m3:.1f} m³, "
            f"sustainable={self.sustainable_water_percentage:.0f}%)"
        )
