"""
Energy conversion utilities and models.

Provides canonical data structures for energy carriers, primary energy factors,
and helper methods to convert between delivered, fuel, and primary energy.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pydantic import BaseModel, Field

from .enums import EnergyCarrier, FuelUnit, PrimaryEnergyScope


class FuelProperty(BaseModel):
    """
    Describes the calorific value and characteristics of an energy carrier.
    """

    carrier: EnergyCarrier
    unit: FuelUnit
    energy_density_kwh_per_unit: float
    description: Optional[str] = None
    source: Optional[str] = None
    co2_factor_kg_per_kwh: Optional[float] = None
    default_efficiency: Optional[float] = None


class PrimaryEnergyFactor(BaseModel):
    """
    Primary energy factor for a given carrier, country, and scope.
    """

    country_code: str
    carrier: EnergyCarrier
    scope: PrimaryEnergyScope = PrimaryEnergyScope.TOTAL
    factor: float
    source: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class EnergyUse(BaseModel):
    """
    Represents delivered/site energy for an energy carrier.
    """

    carrier: EnergyCarrier
    delivered_kwh: float
    scope: PrimaryEnergyScope = PrimaryEnergyScope.TOTAL
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PrimaryEnergyComponent(BaseModel):
    carrier: EnergyCarrier
    delivered_kwh: float
    primary_kwh: float
    factor: float
    scope: PrimaryEnergyScope
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PrimaryEnergyBreakdown(BaseModel):
    """
    Aggregated view of primary energy (total, renewable, non-renewable).
    """

    total_primary_kwh: float
    renewable_primary_kwh: float
    non_renewable_primary_kwh: float
    components: List[PrimaryEnergyComponent] = Field(default_factory=list)


def _build_fuel_index(properties: Iterable[FuelProperty]) -> Dict[Tuple[EnergyCarrier, FuelUnit], FuelProperty]:
    return {
        (prop.carrier, prop.unit): prop
        for prop in properties
    }


def _build_primary_index(factors: Iterable[PrimaryEnergyFactor]) -> Dict[Tuple[str, EnergyCarrier, PrimaryEnergyScope], PrimaryEnergyFactor]:
    return {
        (factor.country_code.upper(), factor.carrier, factor.scope): factor
        for factor in factors
    }


DEFAULT_FUEL_PROPERTIES: List[FuelProperty] = [
    FuelProperty(
        carrier=EnergyCarrier.NATURAL_GAS,
        unit=FuelUnit.M3,
        energy_density_kwh_per_unit=10.55,
        description="Natural gas LHV per normal m³",
        source="EU EN16239",
        default_efficiency=0.92,
    ),
    FuelProperty(
        carrier=EnergyCarrier.LPG,
        unit=FuelUnit.LITER,
        energy_density_kwh_per_unit=6.6,
        description="Liquified petroleum gas (propane) per liter",
        source="EU default",
        default_efficiency=0.9,
    ),
    FuelProperty(
        carrier=EnergyCarrier.FUEL_OIL_LIGHT,
        unit=FuelUnit.LITER,
        energy_density_kwh_per_unit=10.0,
        description="Light fuel oil per liter",
        source="EU default",
        default_efficiency=0.88,
    ),
    FuelProperty(
        carrier=EnergyCarrier.DIESEL,
        unit=FuelUnit.LITER,
        energy_density_kwh_per_unit=10.1,
        description="Diesel fuel per liter",
        source="EU default",
    ),
    FuelProperty(
        carrier=EnergyCarrier.WOOD_PELLETS,
        unit=FuelUnit.KG,
        energy_density_kwh_per_unit=4.7,
        description="Wood pellets (LHV) per kg",
        source="ENplus",
        default_efficiency=0.85,
    ),
    FuelProperty(
        carrier=EnergyCarrier.WOOD_CHIPS,
        unit=FuelUnit.KG,
        energy_density_kwh_per_unit=3.2,
        description="Wood chips (35% moisture) per kg",
        source="EA NIRAS",
        default_efficiency=0.8,
    ),
    FuelProperty(
        carrier=EnergyCarrier.COAL,
        unit=FuelUnit.KG,
        energy_density_kwh_per_unit=7.5,
        description="Coal average LHV per kg",
        source="EU default",
    ),
    FuelProperty(
        carrier=EnergyCarrier.BIOMASS,
        unit=FuelUnit.KG,
        energy_density_kwh_per_unit=4.0,
        description="Generic biomass (wood mix) per kg",
    ),
    FuelProperty(
        carrier=EnergyCarrier.BIOGAS,
        unit=FuelUnit.M3,
        energy_density_kwh_per_unit=6.0,
        description="Biogas per normal m³",
    ),
    FuelProperty(
        carrier=EnergyCarrier.HYDROGEN,
        unit=FuelUnit.KG,
        energy_density_kwh_per_unit=33.3,
        description="Hydrogen LHV per kg",
    ),
]


DEFAULT_PRIMARY_ENERGY_FACTORS: List[PrimaryEnergyFactor] = [
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.ELECTRICITY,
        scope=PrimaryEnergyScope.TOTAL,
        factor=2.1,
        source="EPBD default",
    ),
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.ELECTRICITY,
        scope=PrimaryEnergyScope.NON_RENEWABLE,
        factor=1.7,
    ),
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.ELECTRICITY,
        scope=PrimaryEnergyScope.RENEWABLE,
        factor=0.4,
    ),
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.DISTRICT_HEATING,
        scope=PrimaryEnergyScope.TOTAL,
        factor=1.5,
    ),
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.DISTRICT_HEATING,
        scope=PrimaryEnergyScope.NON_RENEWABLE,
        factor=1.0,
    ),
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.DISTRICT_HEATING,
        scope=PrimaryEnergyScope.RENEWABLE,
        factor=0.5,
    ),
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.NATURAL_GAS,
        scope=PrimaryEnergyScope.TOTAL,
        factor=1.1,
    ),
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.FUEL_OIL_LIGHT,
        scope=PrimaryEnergyScope.TOTAL,
        factor=1.1,
    ),
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.BIOMASS,
        scope=PrimaryEnergyScope.TOTAL,
        factor=1.0,
    ),
    PrimaryEnergyFactor(
        country_code="EU",
        carrier=EnergyCarrier.BIOMASS,
        scope=PrimaryEnergyScope.NON_RENEWABLE,
        factor=0.2,
    ),
    PrimaryEnergyFactor(
        country_code="DK",
        carrier=EnergyCarrier.ELECTRICITY,
        scope=PrimaryEnergyScope.TOTAL,
        factor=1.9,
        source="Danish Building Regulations 2020",
    ),
    PrimaryEnergyFactor(
        country_code="DK",
        carrier=EnergyCarrier.DISTRICT_HEATING,
        scope=PrimaryEnergyScope.TOTAL,
        factor=0.85,
    ),
]


class EnergyConversionService:
    """
    Provides conversion utilities between physical energy units and primary energy.
    """

    def __init__(
        self,
        primary_factors: Optional[Iterable[PrimaryEnergyFactor]] = None,
        fuel_properties: Optional[Iterable[FuelProperty]] = None,
        fallback_country: str = "EU",
    ) -> None:
        self._fuel_index = _build_fuel_index(fuel_properties or DEFAULT_FUEL_PROPERTIES)
        self._primary_index = _build_primary_index(primary_factors or DEFAULT_PRIMARY_ENERGY_FACTORS)
        self.fallback_country = fallback_country.upper()

    # ------------------------------------------------------------------
    # Fuel property helpers
    # ------------------------------------------------------------------
    def register_fuel_property(self, property_: FuelProperty) -> None:
        """Register or override calorific values."""
        self._fuel_index[(property_.carrier, property_.unit)] = property_

    def get_fuel_property(self, carrier: EnergyCarrier, unit: FuelUnit) -> Optional[FuelProperty]:
        return self._fuel_index.get((carrier, unit))

    def convert_quantity_to_kwh(
        self,
        carrier: EnergyCarrier,
        quantity: float,
        unit: FuelUnit,
        efficiency: Optional[float] = None,
    ) -> float:
        """
        Convert a physical quantity of fuel to delivered kWh.
        """
        prop = self.get_fuel_property(carrier, unit)
        if not prop:
            raise ValueError(f"No calorific value for {carrier.value} in {unit.value}")
        eff = efficiency if efficiency is not None else prop.default_efficiency or 1.0
        return quantity * prop.energy_density_kwh_per_unit * eff

    # ------------------------------------------------------------------
    # Primary energy helpers
    # ------------------------------------------------------------------
    def register_primary_factor(self, factor: PrimaryEnergyFactor) -> None:
        self._primary_index[(factor.country_code.upper(), factor.carrier, factor.scope)] = factor

    def get_primary_factor(
        self,
        country_code: str,
        carrier: EnergyCarrier,
        scope: PrimaryEnergyScope = PrimaryEnergyScope.TOTAL,
        default: float = 1.0,
    ) -> float:
        country_code = country_code.upper()
        factor = self._primary_index.get((country_code, carrier, scope))
        if factor:
            return factor.factor
        # fall back to same country total
        if scope != PrimaryEnergyScope.TOTAL:
            total_factor = self._primary_index.get((country_code, carrier, PrimaryEnergyScope.TOTAL))
            if total_factor:
                return total_factor.factor
        # fallback country
        fallback = self._primary_index.get((self.fallback_country, carrier, scope))
        if fallback:
            return fallback.factor
        if scope != PrimaryEnergyScope.TOTAL:
            fallback_total = self._primary_index.get((self.fallback_country, carrier, PrimaryEnergyScope.TOTAL))
            if fallback_total:
                return fallback_total.factor
        return default

    def convert_to_primary(
        self,
        country_code: str,
        carrier: EnergyCarrier,
        delivered_kwh: float,
        scope: PrimaryEnergyScope = PrimaryEnergyScope.TOTAL,
        factor_override: Optional[float] = None,
    ) -> float:
        """
        Convert delivered kWh to primary energy for a given country.
        """
        factor = factor_override if factor_override is not None else self.get_primary_factor(
            country_code, carrier, scope
        )
        return delivered_kwh * factor

    def convert_fuel_quantity_to_primary(
        self,
        country_code: str,
        carrier: EnergyCarrier,
        quantity: float,
        unit: FuelUnit,
        efficiency: Optional[float] = None,
        scope: PrimaryEnergyScope = PrimaryEnergyScope.TOTAL,
    ) -> float:
        delivered = self.convert_quantity_to_kwh(carrier, quantity, unit, efficiency=efficiency)
        return self.convert_to_primary(country_code, carrier, delivered, scope=scope)

    def calculate_primary_breakdown(
        self,
        country_code: str,
        energy_uses: Iterable[EnergyUse],
    ) -> PrimaryEnergyBreakdown:
        """
        Aggregate primary energy for a set of delivered energies.
        """
        components: List[PrimaryEnergyComponent] = []
        total_primary = 0.0
        renewable_primary = 0.0
        non_renewable_primary = 0.0

        for use in energy_uses:
            total = self.convert_to_primary(country_code, use.carrier, use.delivered_kwh, scope=PrimaryEnergyScope.TOTAL)
            non_renewable = self.convert_to_primary(
                country_code, use.carrier, use.delivered_kwh, scope=PrimaryEnergyScope.NON_RENEWABLE
            )
            renewable = self.convert_to_primary(
                country_code, use.carrier, use.delivered_kwh, scope=PrimaryEnergyScope.RENEWABLE
            )
            total_primary += total
            # If explicit renewable factor not available, derive as difference
            if renewable == 0 and total > non_renewable:
                renewable = max(0.0, total - non_renewable)
            renewable_primary += renewable
            non_renewable_primary += non_renewable
            components.append(
                PrimaryEnergyComponent(
                    carrier=use.carrier,
                    delivered_kwh=use.delivered_kwh,
                    primary_kwh=total,
                    factor=total / use.delivered_kwh if use.delivered_kwh else 0.0,
                    scope=use.scope,
                    metadata=use.metadata,
                )
            )

        return PrimaryEnergyBreakdown(
            total_primary_kwh=total_primary,
            renewable_primary_kwh=renewable_primary,
            non_renewable_primary_kwh=non_renewable_primary,
            components=components,
        )

    def convert_energy_mix_to_primary(
        self,
        country_code: str,
        energy_mix: Dict[EnergyCarrier, float],
    ) -> float:
        """
        Convenience wrapper returning total primary energy for a delivered mix.
        """
        uses = [
            EnergyUse(carrier=carrier, delivered_kwh=value)
            for carrier, value in energy_mix.items()
            if value
        ]
        breakdown = self.calculate_primary_breakdown(country_code, uses)
        return breakdown.total_primary_kwh

    # ------------------------------------------------------------------
    # Technology helpers (heat pumps, cogeneration)
    # ------------------------------------------------------------------
    @staticmethod
    def heat_pump_input_from_output(thermal_output_kwh: float, cop: float) -> float:
        """
        Convert heat pump thermal output to electrical input using COP.
        """
        if cop <= 0:
            raise ValueError("COP must be > 0")
        return thermal_output_kwh / cop

    @staticmethod
    def heat_pump_output_from_input(electrical_input_kwh: float, cop: float) -> float:
        if cop <= 0:
            raise ValueError("COP must be > 0")
        return electrical_input_kwh * cop

    @staticmethod
    def cogeneration_outputs(
        fuel_input_kwh: float,
        electrical_efficiency: float,
        thermal_efficiency: float,
    ) -> Tuple[float, float]:
        """
        Estimate electrical and thermal output from a CHP plant.
        """
        electrical = fuel_input_kwh * electrical_efficiency
        thermal = fuel_input_kwh * thermal_efficiency
        return electrical, thermal


__all__ = [
    "FuelProperty",
    "PrimaryEnergyFactor",
    "EnergyUse",
    "PrimaryEnergyComponent",
    "PrimaryEnergyBreakdown",
    "EnergyConversionService",
    "DEFAULT_FUEL_PROPERTIES",
    "DEFAULT_PRIMARY_ENERGY_FACTORS",
]
