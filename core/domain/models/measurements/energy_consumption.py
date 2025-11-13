"""Building energy consumption tracking model."""

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from core.domain.enums.countries import Country
from core.domain.models.base.base_measurement import UtilityConsumption


class EnergyConsumption(UtilityConsumption):
    """
    Tracks energy consumption data for a building across different systems.

    Supports multiple units with automatic conversion to kWh for EPC calculations.
    Extends UtilityConsumption with energy-specific fields and EPC calculation support.

    Legacy fields are maintained for backward compatibility but internally
    managed through the consumption_by_source and production_by_source dicts.
    """

    # Heating consumption (legacy fields - maintained for compatibility)
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

    # Renewable energy generation (legacy fields)
    solar_pv_kwh: float | None = Field(default=0.0, ge=0, description="Solar PV energy generated in kWh")
    wind_kwh: float | None = Field(default=0.0, ge=0, description="Wind energy generated in kWh")
    other_renewable_kwh: float | None = Field(default=0.0, ge=0, description="Other renewable energy in kWh")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to sync legacy fields with base consumption dicts."""
        # Sync to consumption_by_source
        if self.heating_kwh > 0:
            self.consumption_by_source["heating"] = self.heating_kwh
        if self.cooling_kwh > 0:
            self.consumption_by_source["cooling"] = self.cooling_kwh
        if self.electricity_kwh > 0:
            self.consumption_by_source["electricity"] = self.electricity_kwh
        if self.hot_water_kwh > 0:
            self.consumption_by_source["hot_water"] = self.hot_water_kwh
        if self.ventilation_kwh > 0:
            self.consumption_by_source["ventilation"] = self.ventilation_kwh

        # Add raw sources for conversion
        if self.heating_gas_m3:
            self.consumption_by_source["heating_gas_m3"] = self.heating_gas_m3
        if self.heating_oil_liters:
            self.consumption_by_source["heating_oil_liters"] = self.heating_oil_liters
        if self.heating_district_kwh:
            self.consumption_by_source["heating_district"] = self.heating_district_kwh

        # Sync to production_by_source
        if self.solar_pv_kwh and self.solar_pv_kwh > 0:
            self.production_by_source["solar_pv"] = self.solar_pv_kwh
        if self.wind_kwh and self.wind_kwh > 0:
            self.production_by_source["wind"] = self.wind_kwh
        if self.other_renewable_kwh and self.other_renewable_kwh > 0:
            self.production_by_source["other_renewable"] = self.other_renewable_kwh

        # Set conversion factors
        self.conversion_factors = {
            "gas_m3_to_kwh": 10.0,  # 1 m³ natural gas ≈ 10.0 kWh
            "oil_liters_to_kwh": 10.0,  # 1 liter heating oil ≈ 10.0 kWh
            "hot_water_liters_to_kwh": 0.058,  # Heating water from 10°C to 60°C
        }

        # Set unit
        self.unit = "kWh"

    @property
    def total_heating_kwh(self) -> float:
        """Calculate total heating energy in kWh including all heating sources."""
        total = self.heating_kwh

        # Convert natural gas (m³ to kWh)
        if self.heating_gas_m3:
            total += self.heating_gas_m3 * 10.0

        # Convert heating oil (liters to kWh)
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

    def annualize(self) -> "EnergyConsumption":
        """
        Convert consumption to annual values if measurement period is not 365 days.

        Returns:
            New EnergyConsumption instance with annualized values
        """
        if self.is_annual():
            return self

        factor = self.get_annualization_factor()

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
            notes=f"Annualized from {self.measurement_period_days} days: {self.notes or ''}"
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
        if not self.is_annual():
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
