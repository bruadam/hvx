"""Fuel consumption tracking model."""

from typing import Any

from pydantic import Field

from core.domain.models.base.base_measurement import UtilityConsumption


class FuelConsumption(UtilityConsumption):
    """
    Tracks fuel consumption data for a building.

    Supports multiple fuel types:
    - Fossil fuels (natural gas, heating oil, propane, coal)
    - Renewable fuels (wood, biomass, biogas, hydrogen)
    - Co-generation systems

    All fuels are tracked in their native units with conversion to kWh.
    """

    # Fossil fuels
    natural_gas_m3: float = Field(
        default=0.0,
        ge=0,
        description="Natural gas consumption in m³"
    )

    heating_oil_liters: float = Field(
        default=0.0,
        ge=0,
        description="Heating oil consumption in liters"
    )

    propane_kg: float = Field(
        default=0.0,
        ge=0,
        description="Propane consumption in kg"
    )

    coal_kg: float = Field(
        default=0.0,
        ge=0,
        description="Coal consumption in kg"
    )

    # Renewable fuels
    wood_kg: float = Field(
        default=0.0,
        ge=0,
        description="Wood/biomass consumption in kg"
    )

    wood_pellets_kg: float = Field(
        default=0.0,
        ge=0,
        description="Wood pellet consumption in kg"
    )

    biogas_m3: float = Field(
        default=0.0,
        ge=0,
        description="Biogas consumption in m³"
    )

    hydrogen_kg: float = Field(
        default=0.0,
        ge=0,
        description="Hydrogen consumption in kg"
    )

    # Co-generation (both consumption and production)
    cogeneration_gas_m3: float = Field(
        default=0.0,
        ge=0,
        description="Gas consumed by co-generation system in m³"
    )

    cogeneration_electricity_kwh: float = Field(
        default=0.0,
        ge=0,
        description="Electricity produced by co-generation in kWh"
    )

    cogeneration_heat_kwh: float = Field(
        default=0.0,
        ge=0,
        description="Heat produced by co-generation in kWh"
    )

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to sync fuel sources with base consumption dict."""
        # Set unit (will be converted to kWh)
        self.unit = "kWh"

        # Conversion factors to kWh
        # Source: European standards and typical values
        self.conversion_factors = {
            "natural_gas_m3_to_kwh": 10.0,  # 1 m³ ≈ 10 kWh
            "heating_oil_liters_to_kwh": 10.0,  # 1 liter ≈ 10 kWh
            "propane_kg_to_kwh": 12.87,  # 1 kg ≈ 12.87 kWh
            "coal_kg_to_kwh": 8.14,  # 1 kg ≈ 8.14 kWh
            "wood_kg_to_kwh": 4.0,  # 1 kg dry wood ≈ 4 kWh
            "wood_pellets_kg_to_kwh": 4.9,  # 1 kg ≈ 4.9 kWh
            "biogas_m3_to_kwh": 5.5,  # 1 m³ ≈ 5.5 kWh (lower than natural gas)
            "hydrogen_kg_to_kwh": 33.33,  # 1 kg ≈ 33.33 kWh (LHV)
        }

        # Sync consumption in kWh
        if self.natural_gas_m3 > 0:
            self.consumption_by_source["natural_gas"] = (
                self.natural_gas_m3 * self.conversion_factors["natural_gas_m3_to_kwh"]
            )
        if self.heating_oil_liters > 0:
            self.consumption_by_source["heating_oil"] = (
                self.heating_oil_liters * self.conversion_factors["heating_oil_liters_to_kwh"]
            )
        if self.propane_kg > 0:
            self.consumption_by_source["propane"] = (
                self.propane_kg * self.conversion_factors["propane_kg_to_kwh"]
            )
        if self.coal_kg > 0:
            self.consumption_by_source["coal"] = (
                self.coal_kg * self.conversion_factors["coal_kg_to_kwh"]
            )
        if self.wood_kg > 0:
            self.consumption_by_source["wood"] = (
                self.wood_kg * self.conversion_factors["wood_kg_to_kwh"]
            )
        if self.wood_pellets_kg > 0:
            self.consumption_by_source["wood_pellets"] = (
                self.wood_pellets_kg * self.conversion_factors["wood_pellets_kg_to_kwh"]
            )
        if self.biogas_m3 > 0:
            self.consumption_by_source["biogas"] = (
                self.biogas_m3 * self.conversion_factors["biogas_m3_to_kwh"]
            )
        if self.hydrogen_kg > 0:
            self.consumption_by_source["hydrogen"] = (
                self.hydrogen_kg * self.conversion_factors["hydrogen_kg_to_kwh"]
            )

        # Co-generation
        if self.cogeneration_gas_m3 > 0:
            self.consumption_by_source["cogeneration_gas"] = (
                self.cogeneration_gas_m3 * self.conversion_factors["natural_gas_m3_to_kwh"]
            )

        # Co-generation production
        if self.cogeneration_electricity_kwh > 0:
            self.production_by_source["cogeneration_electricity"] = self.cogeneration_electricity_kwh
        if self.cogeneration_heat_kwh > 0:
            self.production_by_source["cogeneration_heat"] = self.cogeneration_heat_kwh

    @property
    def total_fossil_fuel_kwh(self) -> float:
        """Get total fossil fuel consumption in kWh."""
        return (
            self.natural_gas_m3 * self.conversion_factors.get("natural_gas_m3_to_kwh", 10.0) +
            self.heating_oil_liters * self.conversion_factors.get("heating_oil_liters_to_kwh", 10.0) +
            self.propane_kg * self.conversion_factors.get("propane_kg_to_kwh", 12.87) +
            self.coal_kg * self.conversion_factors.get("coal_kg_to_kwh", 8.14)
        )

    @property
    def total_renewable_fuel_kwh(self) -> float:
        """Get total renewable fuel consumption in kWh."""
        return (
            self.wood_kg * self.conversion_factors.get("wood_kg_to_kwh", 4.0) +
            self.wood_pellets_kg * self.conversion_factors.get("wood_pellets_kg_to_kwh", 4.9) +
            self.biogas_m3 * self.conversion_factors.get("biogas_m3_to_kwh", 5.5) +
            self.hydrogen_kg * self.conversion_factors.get("hydrogen_kg_to_kwh", 33.33)
        )

    @property
    def renewable_fuel_percentage(self) -> float:
        """
        Calculate percentage of fuel from renewable sources.

        Returns:
            Percentage (0-100) of fuel from renewable sources
        """
        total = self.total_consumption
        if total == 0:
            return 0.0

        return (self.total_renewable_fuel_kwh / total) * 100

    @property
    def cogeneration_efficiency(self) -> float | None:
        """
        Calculate co-generation system efficiency.

        Returns:
            Efficiency percentage, or None if no co-generation
        """
        if self.cogeneration_gas_m3 == 0:
            return None

        input_kwh = self.cogeneration_gas_m3 * self.conversion_factors.get("natural_gas_m3_to_kwh", 10.0)
        output_kwh = self.cogeneration_electricity_kwh + self.cogeneration_heat_kwh

        if input_kwh == 0:
            return None

        return (output_kwh / input_kwh) * 100

    def annualize(self) -> "FuelConsumption":
        """
        Convert consumption to annual values.

        Returns:
            New FuelConsumption instance with annualized values
        """
        if self.is_annual():
            return self

        factor = self.get_annualization_factor()

        return FuelConsumption(
            measurement_start=self.measurement_start,
            measurement_end=self.measurement_end,
            natural_gas_m3=self.natural_gas_m3 * factor,
            heating_oil_liters=self.heating_oil_liters * factor,
            propane_kg=self.propane_kg * factor,
            coal_kg=self.coal_kg * factor,
            wood_kg=self.wood_kg * factor,
            wood_pellets_kg=self.wood_pellets_kg * factor,
            biogas_m3=self.biogas_m3 * factor,
            hydrogen_kg=self.hydrogen_kg * factor,
            cogeneration_gas_m3=self.cogeneration_gas_m3 * factor,
            cogeneration_electricity_kwh=self.cogeneration_electricity_kwh * factor,
            cogeneration_heat_kwh=self.cogeneration_heat_kwh * factor,
            notes=f"Annualized from {self.measurement_period_days} days: {self.notes or ''}"
        )

    def get_summary(self) -> dict[str, Any]:
        """Get summary of fuel consumption."""
        summary = super().get_summary()
        summary.update({
            "total_fossil_fuel_kwh": round(self.total_fossil_fuel_kwh, 2),
            "total_renewable_fuel_kwh": round(self.total_renewable_fuel_kwh, 2),
            "renewable_fuel_percentage": round(self.renewable_fuel_percentage, 2),
            "cogeneration_efficiency": (
                round(self.cogeneration_efficiency, 2)
                if self.cogeneration_efficiency is not None
                else None
            ),
        })
        return summary

    def __str__(self) -> str:
        """String representation."""
        return (
            f"FuelConsumption(period={self.measurement_period_days}d, "
            f"total={self.total_consumption:.0f} kWh, "
            f"renewable={self.renewable_fuel_percentage:.0f}%)"
        )
