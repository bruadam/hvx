"""
Enhanced Spatial Entity Implementations

Provides specific implementations for Portfolio, Building, Floor, and Room
with domain-specific methods, aggregation capabilities, and self-analysis.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pydantic import Field

from .spacial_entity import SpatialEntity
from .energy import EnergyConversionService, EnergyUse
from .enums import SpatialEntityType, VentilationType, EnergyCarrier
from .metering import EnergyMeter, AggregatedEnergyData
from simulations.models.real_epc import calculate_epc_rating


# ============================================================
#  PORTFOLIO - Top Level Collection
# ============================================================

class Portfolio(SpatialEntity):
    """
    Portfolio entity representing a collection of buildings.

    Provides portfolio-wide aggregation and analysis capabilities.
    """
    type: SpatialEntityType = SpatialEntityType.PORTFOLIO

    # Computed metrics cache (inherited pattern)
    computed_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Cached computed metrics",
        exclude=True
    )
    metrics_computed_at: Optional[datetime] = None

    @property
    def building_ids(self) -> List[str]:
        """Get building IDs (alias for child_ids)."""
        return self.child_ids

    def add_building(self, building_id: str) -> None:
        """Add a building to this portfolio."""
        if building_id not in self.child_ids:
            self.child_ids.append(building_id)

    def remove_building(self, building_id: str) -> bool:
        """Remove a building from this portfolio."""
        if building_id in self.child_ids:
            self.child_ids.remove(building_id)
            return True
        return False

    def has_building(self, building_id: str) -> bool:
        """Check if portfolio contains a specific building."""
        return building_id in self.child_ids

    @property
    def building_count(self) -> int:
        """Get number of buildings in portfolio."""
        return len(self.child_ids)

    def compute_metrics(
        self,
        building_lookup: Optional[Callable[[str], Any]] = None,
        force_recompute: bool = False
    ) -> Dict[str, Any]:
        """
        Compute portfolio-wide aggregated metrics from buildings including EN16798 compliance.

        Args:
            building_lookup: Function to retrieve Building objects by ID
            force_recompute: If True, recompute even if cached

        Returns:
            Dictionary with aggregated metrics including EN16798 portfolio-wide analysis
        """
        if not force_recompute and 'portfolio_metrics' in self.computed_metrics:
            return self.computed_metrics['portfolio_metrics']

        results: Dict[str, Any] = {
            'building_count': self.building_count,
            'portfolio_id': self.id,
            'portfolio_name': self.name,
        }

        if building_lookup is None or not self.child_ids:
            self.computed_metrics['portfolio_metrics'] = results
            return results

        # Aggregate from buildings
        total_area = 0.0
        total_energy = 0.0
        total_rooms = 0
        compliance_rates = []
        tail_ratings = []
        epc_ratings = []

        # EN16798 aggregation
        en16798_aggregated = {
            'buildings_analyzed': 0,
            'total_rooms': 0,
            'rooms_analyzed': 0,
            'category_counts': {},
            'weighted_compliance_rate': 0.0,
            'total_area': 0.0,
            'actual_area_m2': 0.0,
            'time_in_cat_I_weighted': 0.0,
            'time_in_cat_II_weighted': 0.0,
            'time_in_cat_III_weighted': 0.0,
            'time_in_cat_IV_weighted': 0.0,
            'total_violations': 0,
            'buildings_by_category': {'I': [], 'II': [], 'III': [], 'IV': [], 'non_compliant': []},
        }

        for building_id in self.child_ids:
            building = building_lookup(building_id)
            if building is None:
                continue

            if building.area_m2:
                total_area += building.area_m2

            if hasattr(building, 'has_metric') and building.has_metric('total_energy_kwh'):
                total_energy += building.get_metric('total_energy_kwh', 0)

            if hasattr(building, 'has_metric') and building.has_metric('room_count'):
                total_rooms += building.get_metric('room_count', 0)

            if hasattr(building, 'has_metric') and building.has_metric('average_compliance_rate'):
                compliance_rates.append(building.get_metric('average_compliance_rate'))

            if hasattr(building, 'has_metric') and building.has_metric('average_tail_rating'):
                tail_ratings.append(building.get_metric('average_tail_rating'))

            if hasattr(building, 'epc_rating') and building.epc_rating:
                epc_ratings.append(building.epc_rating)

            # Aggregate EN16798 data from building
            if hasattr(building, 'computed_metrics') and 'building_metrics' in building.computed_metrics:
                building_metrics = building.computed_metrics['building_metrics']
                if 'en16798' in building_metrics:
                    building_en16798 = building_metrics['en16798']
                    en16798_aggregated['buildings_analyzed'] += 1

                    # Aggregate category counts
                    for cat, count in building_en16798.get('category_distribution', {}).items():
                        en16798_aggregated['category_counts'][cat] = en16798_aggregated['category_counts'].get(cat, 0) + count

                    # Track building by its achieved category
                    building_cat = building_en16798.get('building_achieved_category')
                    if building_cat:
                        en16798_aggregated['buildings_by_category'][building_cat].append(building_id)
                    else:
                        en16798_aggregated['buildings_by_category']['non_compliant'].append(building_id)

                    # Weighted metrics
                    building_area = building.area_m2 if building.area_m2 and building.area_m2 > 0 else 0.0
                    fallback_weight = (
                        building_en16798.get('total_area_analyzed_m2')
                        or building_en16798.get('rooms_analyzed', 0)
                    )
                    weight = building_area if building_area > 0 else fallback_weight
                    if weight and weight > 0:
                        en16798_aggregated['weighted_compliance_rate'] += building_en16798.get('weighted_compliance_rate', 0) * weight
                        en16798_aggregated['time_in_cat_I_weighted'] += building_en16798.get('weighted_time_in_cat_I_pct', 0) * weight
                        en16798_aggregated['time_in_cat_II_weighted'] += building_en16798.get('weighted_time_in_cat_II_pct', 0) * weight
                        en16798_aggregated['time_in_cat_III_weighted'] += building_en16798.get('weighted_time_in_cat_III_pct', 0) * weight
                        en16798_aggregated['time_in_cat_IV_weighted'] += building_en16798.get('weighted_time_in_cat_IV_pct', 0) * weight
                        en16798_aggregated['total_area'] += weight
                        en16798_aggregated['actual_area_m2'] += building_area

                    en16798_aggregated['total_violations'] += building_en16798.get('total_violations', 0)
                    en16798_aggregated['rooms_analyzed'] += building_en16798.get('rooms_analyzed', 0)
                    en16798_aggregated['total_rooms'] += building_en16798.get('total_rooms', 0)

        # Calculate portfolio-wide metrics
        results['total_area_m2'] = total_area
        results['total_energy_kwh'] = total_energy
        results['total_rooms'] = total_rooms

        if total_area > 0 and total_energy > 0:
            results['energy_intensity_kwh_m2'] = total_energy / total_area

        if compliance_rates:
            results['average_compliance_rate'] = sum(compliance_rates) / len(compliance_rates)
            results['min_compliance_rate'] = min(compliance_rates)
            results['max_compliance_rate'] = max(compliance_rates)

        if tail_ratings:
            results['average_tail_rating'] = sum(tail_ratings) / len(tail_ratings)
            results['worst_tail_rating'] = max(tail_ratings)
            results['best_tail_rating'] = min(tail_ratings)

        # Calculate final EN16798 portfolio metrics
        weight = en16798_aggregated['total_area'] if en16798_aggregated['total_area'] > 0 else en16798_aggregated['rooms_analyzed']
        if weight > 0:
            analyzed_area = en16798_aggregated['actual_area_m2'] if en16798_aggregated['actual_area_m2'] > 0 else weight
            results['en16798'] = {
                'buildings_analyzed': en16798_aggregated['buildings_analyzed'],
                'total_rooms': en16798_aggregated['total_rooms'],
                'rooms_analyzed': en16798_aggregated['rooms_analyzed'],
                'category_distribution': en16798_aggregated['category_counts'],
                'buildings_by_category': en16798_aggregated['buildings_by_category'],
                'weighted_compliance_rate': round(en16798_aggregated['weighted_compliance_rate'] / weight, 2),
                'weighted_time_in_cat_I_pct': round(en16798_aggregated['time_in_cat_I_weighted'] / weight, 2),
                'weighted_time_in_cat_II_pct': round(en16798_aggregated['time_in_cat_II_weighted'] / weight, 2),
                'weighted_time_in_cat_III_pct': round(en16798_aggregated['time_in_cat_III_weighted'] / weight, 2),
                'weighted_time_in_cat_IV_pct': round(en16798_aggregated['time_in_cat_IV_weighted'] / weight, 2),
                'total_violations': en16798_aggregated['total_violations'],
                'portfolio_achieved_category': self._determine_portfolio_category(en16798_aggregated['category_counts']),
                'total_area_analyzed_m2': round(analyzed_area, 2),
            }

        # Cache results
        self.computed_metrics['portfolio_metrics'] = results
        self.metrics_computed_at = datetime.now()

        return results

    def _determine_portfolio_category(self, category_counts: Dict[str, int]) -> Optional[str]:
        """
        Determine the portfolio's overall EN16798 category based on room categories.

        Uses a conservative approach: portfolio achieves a category only if
        >= 70% of rooms achieve that category or better.
        """
        if not category_counts:
            return None

        total_rooms = sum(category_counts.values())
        if total_rooms == 0:
            return None

        # Check from best to worst category
        cat_order = ['I', 'II', 'III', 'IV']
        cumulative_rooms = 0

        for cat in cat_order:
            cumulative_rooms += category_counts.get(cat, 0)
            percentage = (cumulative_rooms / total_rooms) * 100
            if percentage >= 70.0:
                return cat

        return None

    def compute_standards(
        self,
        building_lookup: Optional[Callable[[str], Any]] = None,
        floor_lookup: Optional[Callable[[str], Any]] = None,
        room_lookup: Optional[Callable[[str], Any]] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        season: str = "winter",
        force_recompute: bool = False,
    ) -> Dict[str, Any]:
        """
        Aggregate standards results from all buildings in this portfolio.
        
        Args:
            building_lookup: Function to retrieve Building objects by ID
            floor_lookup: Function to retrieve Floor objects by ID  
            room_lookup: Function to retrieve Room objects by ID
            country: Country code (defaults to portfolio's country)
            region: Region name (defaults to portfolio's region)
            season: Season for analysis
            force_recompute: If True, recompute even if cached
        
        Returns:
            Dictionary with aggregated standards results
        """
        if not force_recompute and 'portfolio_standards' in self.computed_metrics:
            return self.computed_metrics['portfolio_standards']
        
        results = {}
        
        if building_lookup is None or not self.child_ids:
            self.computed_metrics['portfolio_standards'] = results
            return results
        
        # Use portfolio's properties as defaults
        country = country or self.country
        region = region or self.region
        
        # Ensure all buildings have computed their standards
        for building_id in self.child_ids:
            building = building_lookup(building_id)
            if building is None or not hasattr(building, 'compute_standards'):
                continue
            
            # Compute building standards if not already done
            if 'building_standards' not in building.computed_metrics:
                building.compute_standards(
                    floor_lookup=floor_lookup,
                    room_lookup=room_lookup,
                    country=country,
                    region=region,
                    season=season,
                    force_recompute=False,
                )
        
        from .standards_registry import get_registry
        
        # Get all child buildings
        child_buildings = []
        for building_id in self.child_ids:
            building = building_lookup(building_id)
            if building is not None:
                child_buildings.append(building)
        
        # Get registry to access standard configs
        registry = get_registry()
        
        # Aggregate results for each standard
        for standard_id, standard_config in registry.standards.items():
            aggregation_config = standard_config.config_data.get('aggregation', {})
            
            # Check if this standard should aggregate to portfolio level
            aggregate_to_types = aggregation_config.get('aggregate_to_types', [])
            if 'portfolio' not in aggregate_to_types:
                continue
            
            # Collect child results for this standard
            child_results = []
            child_weights = []
            
            for building in child_buildings:
                if hasattr(building, 'computed_metrics'):
                    building_standard_results = building.computed_metrics.get('building_standards', {})
                    
                    if standard_id in building_standard_results:
                        result = building_standard_results[standard_id]
                        child_results.append(result)
                        
                        # Get weight for weighted aggregation
                        weight = building.area_m2 if hasattr(building, 'area_m2') else 1.0
                        child_weights.append(weight)
            
            if not child_results:
                continue
            
            # Apply aggregation based on config
            aggregated_result = self._aggregate_standard_results(
                standard_id=standard_id,
                child_results=child_results,
                child_weights=child_weights,
                aggregation_config=aggregation_config,
            )
            
            if aggregated_result:
                results[standard_id] = aggregated_result
        
        # Cache results
        self.computed_metrics['portfolio_standards'] = results
        return results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary information about this portfolio."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'building_count': self.building_count,
            'building_ids': self.building_ids,
            'country': self.country,
            'region': self.region,
            'total_area_m2': self.area_m2,
            'has_computed_metrics': bool(self.computed_metrics),
        }


# ============================================================
#  BUILDING - Individual Building
# ============================================================

class Building(SpatialEntity):
    """
    Building entity representing a physical building.

    Contains floors and rooms with building-specific properties
    like location, systems, energy consumption, and EPC rating.
    """
    type: SpatialEntityType = SpatialEntityType.BUILDING

    # Building-specific properties
    year_built: Optional[int] = Field(default=None, ge=1800, le=2100)

    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)

    # Building systems
    hvac_system: Optional[str] = None
    heating_system: Optional[str] = None
    heating_energy_carrier: Optional[EnergyCarrier] = Field(
        default=None, description="Energy carrier used for space heating"
    )
    cooling_energy_carrier: Optional[EnergyCarrier] = Field(
        default=None, description="Energy carrier used for space cooling"
    )
    dhw_energy_carrier: Optional[EnergyCarrier] = Field(
        default=None, description="Energy carrier for domestic hot water"
    )
    electricity_energy_carrier: EnergyCarrier = EnergyCarrier.ELECTRICITY
    ventilation_energy_carrier: Optional[EnergyCarrier] = Field(
        default=None, description="Carrier for ventilation systems"
    )

    # Energy consumption tracking
    annual_heating_kwh: Optional[float] = Field(default=None, ge=0)
    annual_cooling_kwh: Optional[float] = Field(default=None, ge=0)
    annual_electricity_kwh: Optional[float] = Field(default=None, ge=0)
    annual_hot_water_kwh: Optional[float] = Field(default=None, ge=0)
    annual_ventilation_kwh: Optional[float] = Field(default=None, ge=0)

    # Water consumption
    annual_water_m3: Optional[float] = Field(default=None, ge=0)

    # Renewable energy
    annual_solar_pv_kwh: Optional[float] = Field(default=None, ge=0)
    annual_renewable_kwh: Optional[float] = Field(default=None, ge=0)

    # EPC rating
    epc_rating: Optional[str] = None

    # Additional hierarchy tracking
    floor_ids: List[str] = Field(
        default_factory=list,
        description="Direct floor children"
    )
    room_ids: List[str] = Field(
        default_factory=list,
        description="Rooms assigned directly without floors"
    )

    # Energy meters
    energy_meters: List[EnergyMeter] = Field(
        default_factory=list,
        description="Energy meters attached to this building"
    )

    # Computed metrics cache
    computed_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        exclude=True
    )
    metrics_computed_at: Optional[datetime] = None

    @property
    def level_ids(self) -> List[str]:
        """Get floor IDs (alias for child_ids)."""
        return self.child_ids

    def add_floor(self, floor_id: str) -> None:
        """Add a floor to this building."""
        if floor_id not in self.child_ids:
            self.child_ids.append(floor_id)
        if floor_id not in self.floor_ids:
            self.floor_ids.append(floor_id)

    def add_room(self, room_id: str) -> None:
        """Add a room directly to this building (without floor)."""
        if room_id not in self.room_ids:
            self.room_ids.append(room_id)

    def remove_floor(self, floor_id: str) -> bool:
        """Remove a floor from this building."""
        removed = False
        if floor_id in self.child_ids:
            self.child_ids.remove(floor_id)
            removed = True
        if floor_id in self.floor_ids:
            self.floor_ids.remove(floor_id)
            removed = True
        return removed

    def remove_room(self, room_id: str) -> bool:
        """Remove a room from this building."""
        if room_id in self.room_ids:
            self.room_ids.remove(room_id)
            return True
        return False

    @property
    def floor_count(self) -> int:
        """Get number of floors in building."""
        return len(self.floor_ids)

    @property
    def room_count(self) -> int:
        """Get number of rooms directly assigned to building."""
        return len(self.room_ids)

    def _resolve_country_code(self) -> str:
        """Resolve country code for primary energy conversions."""
        if self.country:
            return self.country.upper()
        country_meta = self.metadata.get("country_code")
        if country_meta:
            return str(country_meta).upper()
        return "EU"

    def calculate_primary_energy_per_m2(
        self,
        country_code: Optional[str] = None,
        conversion_service: Optional[EnergyConversionService] = None,
    ) -> Optional[float]:
        """
        Calculate primary energy consumption per m² per year with country-specific factors.
        """
        if not self.area_m2 or self.area_m2 <= 0:
            return None

        uses: List[EnergyUse] = []

        def add_use(value: Optional[float], carrier: EnergyCarrier, end_use: str) -> None:
            if value and value > 0:
                uses.append(
                    EnergyUse(
                        carrier=carrier,
                        delivered_kwh=value,
                        metadata={"end_use": end_use},
                    )
                )

        heating_carrier = self.heating_energy_carrier or EnergyCarrier.DISTRICT_HEATING
        cooling_carrier = self.cooling_energy_carrier or EnergyCarrier.ELECTRICITY
        dhw_carrier = self.dhw_energy_carrier or heating_carrier
        ventilation_carrier = self.ventilation_energy_carrier or EnergyCarrier.ELECTRICITY
        electricity_carrier = self.electricity_energy_carrier or EnergyCarrier.ELECTRICITY

        add_use(self.annual_heating_kwh, heating_carrier, "space_heating")
        add_use(self.annual_cooling_kwh, cooling_carrier, "space_cooling")
        add_use(self.annual_hot_water_kwh, dhw_carrier, "hot_water")
        add_use(self.annual_ventilation_kwh, ventilation_carrier, "ventilation")
        add_use(self.annual_electricity_kwh, electricity_carrier, "electricity_general")

        if not uses:
            return None

        service = conversion_service or EnergyConversionService()
        country = (country_code or self._resolve_country_code())

        breakdown = service.calculate_primary_breakdown(country, uses)
        total_primary = breakdown.total_primary_kwh

        renewable_offset = self.annual_renewable_kwh or 0.0
        if not renewable_offset and self.annual_solar_pv_kwh:
            renewable_offset = self.annual_solar_pv_kwh
        if renewable_offset:
            total_primary = max(0.0, total_primary - renewable_offset)

        # Persist breakdown for downstream consumers
        self.computed_metrics["primary_energy_breakdown"] = breakdown.model_dump()

        return total_primary / self.area_m2 if self.area_m2 else None

    def add_energy_meter(self, meter: EnergyMeter) -> None:
        """Add an energy meter to this building."""
        # Remove existing meter with same ID if exists
        self.energy_meters = [m for m in self.energy_meters if m.id != meter.id]
        self.energy_meters.append(meter)

    def get_meter_by_carrier(self, carrier: EnergyCarrier) -> Optional[EnergyMeter]:
        """Get energy meter for a specific carrier."""
        for meter in self.energy_meters:
            if meter.carrier == carrier:
                return meter
        return None

    def calculate_primary_energy_from_meters(
        self,
        aggregated_data: List[AggregatedEnergyData],
        country_code: Optional[str] = None,
        conversion_service: Optional[EnergyConversionService] = None,
    ) -> Optional[float]:
        """
        Calculate primary energy per m² from energy meter data.

        This enables automatic calculation from sensor/meter readings instead of
        manually entered annual consumption values.

        Args:
            aggregated_data: List of aggregated energy consumption data by carrier
            country_code: Country code for primary energy factors
            conversion_service: Energy conversion service (uses default if None)

        Returns:
            Primary energy consumption per m² per year (kWh/m²/year) or None
        """
        if not self.area_m2 or self.area_m2 <= 0:
            return None

        if not aggregated_data:
            return None

        # Create EnergyUse objects from aggregated data
        uses: List[EnergyUse] = []
        for agg in aggregated_data:
            if agg.total_kwh > 0:
                uses.append(
                    EnergyUse(
                        carrier=agg.carrier,
                        delivered_kwh=agg.total_kwh,
                        metadata={
                            "period_start": agg.period_start.isoformat(),
                            "period_end": agg.period_end.isoformat(),
                            "resolution": agg.resolution,
                        },
                    )
                )

        if not uses:
            return None

        service = conversion_service or EnergyConversionService()
        country = (country_code or self._resolve_country_code())

        breakdown = service.calculate_primary_breakdown(country, uses)
        total_primary = breakdown.total_primary_kwh

        # Account for renewable generation offset
        renewable_offset = self.annual_renewable_kwh or 0.0
        if not renewable_offset and self.annual_solar_pv_kwh:
            renewable_offset = self.annual_solar_pv_kwh
        if renewable_offset:
            total_primary = max(0.0, total_primary - renewable_offset)

        # Persist breakdown for downstream consumers
        self.computed_metrics["primary_energy_breakdown"] = breakdown.model_dump()
        self.computed_metrics["primary_energy_from_meters"] = True

        return total_primary / self.area_m2 if self.area_m2 else None

    def calculate_and_update_epc_from_meters(
        self,
        aggregated_data: List[AggregatedEnergyData],
        country_code: Optional[str] = None,
        conversion_service: Optional[EnergyConversionService] = None,
    ) -> Optional[str]:
        """
        Calculate and update EPC rating automatically from energy meter data.

        This is the automatic workflow: meter readings → primary energy → EPC rating.

        Args:
            aggregated_data: List of aggregated energy consumption data by carrier
            country_code: Country code for primary energy factors and EPC thresholds
            conversion_service: Energy conversion service (uses default if None)

        Returns:
            EPC rating (e.g., 'A', 'B', 'C') or None if cannot be calculated
        """
        # Calculate primary energy from meters
        primary_energy_kwh_m2 = self.calculate_primary_energy_from_meters(
            aggregated_data,
            country_code=country_code,
            conversion_service=conversion_service,
        )

        if primary_energy_kwh_m2 is None:
            return None

        # Calculate EPC rating
        country = country_code or self._resolve_country_code()
        epc_result = calculate_epc_rating(
            primary_energy_kwh_m2,
            country_code=country,
        )

        rating = epc_result.get("rating")
        if rating is not None:
            self.epc_rating = str(rating)
            self.computed_metrics["epc_rating_auto_calculated"] = True
            self.computed_metrics["epc_primary_energy_kwh_m2"] = primary_energy_kwh_m2

        return self.epc_rating

    def get_energy_summary(self) -> Dict[str, Any]:
        """Get summary of building energy consumption and performance."""
        summary = {
            "total_area_m2": self.area_m2,
            "country": self.country,
            "region": self.region,
            "heating_system": self.heating_system,
            "hvac_system": self.hvac_system,
            "ventilation_type": self.ventilation_type.value if self.ventilation_type else None,
        }

        # Annual consumption
        consumption = {}
        if self.annual_heating_kwh is not None:
            consumption["heating_kwh"] = self.annual_heating_kwh
            if self.area_m2:
                consumption["heating_kwh_m2"] = self.annual_heating_kwh / self.area_m2

        if self.annual_cooling_kwh is not None:
            consumption["cooling_kwh"] = self.annual_cooling_kwh
            if self.area_m2:
                consumption["cooling_kwh_m2"] = self.annual_cooling_kwh / self.area_m2

        if self.annual_electricity_kwh is not None:
            consumption["electricity_kwh"] = self.annual_electricity_kwh
            if self.area_m2:
                consumption["electricity_kwh_m2"] = self.annual_electricity_kwh / self.area_m2

        # Total consumption
        total_kwh = sum([
            self.annual_heating_kwh or 0.0,
            self.annual_cooling_kwh or 0.0,
            self.annual_electricity_kwh or 0.0,
            self.annual_hot_water_kwh or 0.0,
            self.annual_ventilation_kwh or 0.0
        ])
        consumption["total_kwh"] = total_kwh
        if self.area_m2:
            consumption["total_kwh_m2"] = total_kwh / self.area_m2

        summary["consumption"] = consumption

        # Renewable energy
        if self.annual_solar_pv_kwh or self.annual_renewable_kwh:
            summary["renewable_energy"] = {
                "solar_pv_kwh": self.annual_solar_pv_kwh,
                "total_renewable_kwh": self.annual_renewable_kwh,
            }

        # EPC information
        conversion_service = EnergyConversionService()
        primary_energy = self.calculate_primary_energy_per_m2(
            conversion_service=conversion_service
        )
        if primary_energy is not None:
            summary["primary_energy_kwh_m2"] = primary_energy
            breakdown = self.computed_metrics.get("primary_energy_breakdown")
            if breakdown:
                summary["primary_energy_breakdown"] = breakdown
        epc = calculate_epc_rating(
            primary_energy,
            country_code=self.country or (self.metadata.get("country_code") if self.metadata else None),
        )
        rating = epc.get("rating")
        self.epc_rating = str(rating) if rating is not None else None
        summary["epc_rating"] = self.epc_rating

        return summary

    def compute_metrics(
        self,
        metrics: Optional[List[str]] = None,
        force_recompute: bool = False,
        floor_lookup: Optional[Callable[[str], Any]] = None,
        room_lookup: Optional[Callable[[str], Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute building-level metrics including EN16798 aggregation from floors and rooms.

        Args:
            metrics: List of metrics to compute (['energy', 'epc', 'en16798'])
            force_recompute: If True, recompute even if cached
            floor_lookup: Function to retrieve Floor objects by ID
            room_lookup: Function to retrieve Room objects by ID

        Returns:
            Dictionary with computed metrics including EN16798 compliance
        """
        if not force_recompute and 'building_metrics' in self.computed_metrics:
            return self.computed_metrics['building_metrics']

        results: Dict[str, Any] = {}

        if metrics is None:
            metrics = ['energy', 'en16798']

        # Compute energy metrics
        if 'energy' in metrics:
            try:
                energy_summary = self.get_energy_summary()
                results['energy_summary'] = energy_summary

                if 'consumption' in energy_summary:
                    consumption = energy_summary['consumption']
                    if 'total_kwh' in consumption:
                        results['total_energy_kwh'] = consumption['total_kwh']
                    if 'total_kwh_m2' in consumption:
                        results['energy_intensity'] = consumption['total_kwh_m2']

                # Primary energy
                primary_energy = self.calculate_primary_energy_per_m2()
                if primary_energy is not None:
                    results['primary_energy_kwh_m2'] = primary_energy
            except Exception as e:
                print(f"Warning: Could not compute energy metrics: {e}")

        # Compute EN16798 aggregation from floors and rooms
        if 'en16798' in metrics:
            try:
                en16798_results = self._aggregate_en16798_from_floors_and_rooms(
                    floor_lookup, room_lookup
                )
                if en16798_results:
                    results['en16798'] = en16798_results
            except Exception as e:
                print(f"Warning: Could not compute EN16798 metrics: {e}")
                import traceback
                traceback.print_exc()
                results['en16798_error'] = str(e)

        # Cache results
        for key, value in results.items():
            self.computed_metrics[key] = value

        self.computed_metrics['building_metrics'] = results
        self.metrics_computed_at = datetime.now()

        return results

    def _aggregate_en16798_from_floors_and_rooms(
        self,
        floor_lookup: Optional[Callable[[str], Any]],
        room_lookup: Optional[Callable[[str], Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate EN16798 results from all floors and rooms in the building.

        Args:
            floor_lookup: Function to retrieve Floor objects by ID
            room_lookup: Function to retrieve Room objects by ID

        Returns:
            Aggregated EN16798 metrics for the entire building
        """
        aggregated = {
            'total_rooms': 0,
            'rooms_analyzed': 0,
            'category_counts': {},
            'weighted_compliance_rate': 0.0,
            'total_area': 0.0,
            'actual_area_m2': 0.0,
            'time_in_cat_I_weighted': 0.0,
            'time_in_cat_II_weighted': 0.0,
            'time_in_cat_III_weighted': 0.0,
            'time_in_cat_IV_weighted': 0.0,
            'total_violations': 0,
            'floors_analyzed': 0,
            'rooms_by_category': {'I': [], 'II': [], 'III': [], 'IV': [], 'non_compliant': []},
        }

        # Aggregate from floors (if floor structure exists)
        if floor_lookup and self.floor_ids:
            for floor_id in self.floor_ids:
                floor = floor_lookup(floor_id)
                if floor is None:
                    continue

                # Ensure floor metrics are computed
                if hasattr(floor, 'compute_metrics'):
                    floor_metrics = floor.compute_metrics(room_lookup=room_lookup)
                    if 'en16798' in floor_metrics:
                        floor_en16798 = floor_metrics['en16798']
                        aggregated['floors_analyzed'] += 1

                        # Aggregate category counts
                        for cat, count in floor_en16798.get('category_distribution', {}).items():
                            aggregated['category_counts'][cat] = aggregated['category_counts'].get(cat, 0) + count

                        # Aggregate rooms by category
                        for cat, room_ids in floor_en16798.get('rooms_by_category', {}).items():
                            aggregated['rooms_by_category'][cat].extend(room_ids)

                        # Weighted metrics (already weighted by floor)
                        floor_area = floor.area_m2 if floor.area_m2 and floor.area_m2 > 0 else 0.0
                        fallback_weight = (
                            floor_en16798.get('total_area_analyzed_m2')
                            or floor_en16798.get('rooms_analyzed', 0)
                        )
                        weight = floor_area if floor_area > 0 else fallback_weight
                        if weight and weight > 0:
                            aggregated['weighted_compliance_rate'] += floor_en16798.get('weighted_compliance_rate', 0) * weight
                            aggregated['time_in_cat_I_weighted'] += floor_en16798.get('weighted_time_in_cat_I_pct', 0) * weight
                            aggregated['time_in_cat_II_weighted'] += floor_en16798.get('weighted_time_in_cat_II_pct', 0) * weight
                            aggregated['time_in_cat_III_weighted'] += floor_en16798.get('weighted_time_in_cat_III_pct', 0) * weight
                            aggregated['time_in_cat_IV_weighted'] += floor_en16798.get('weighted_time_in_cat_IV_pct', 0) * weight
                            aggregated['total_area'] += weight
                            aggregated['actual_area_m2'] += floor_area

                        aggregated['total_violations'] += floor_en16798.get('total_violations', 0)
                        aggregated['rooms_analyzed'] += floor_en16798.get('rooms_analyzed', 0)
                        aggregated['total_rooms'] += floor_en16798.get('total_rooms', 0)

        # Aggregate from rooms directly assigned to building (without floors)
        if room_lookup and self.room_ids:
            for room_id in self.room_ids:
                room = room_lookup(room_id)
                if room is None:
                    continue

                aggregated['total_rooms'] += 1

                if hasattr(room, 'computed_metrics') and 'en16798_category' in room.computed_metrics:
                    category = room.computed_metrics['en16798_category']
                    room_area = room.area_m2 if room.area_m2 and room.area_m2 > 0 else 1.0

                    if category:
                        aggregated['category_counts'][category] = aggregated['category_counts'].get(category, 0) + 1
                        aggregated['rooms_by_category'][category].append(room_id)
                        aggregated['rooms_analyzed'] += 1
                    else:
                        aggregated['rooms_by_category']['non_compliant'].append(room_id)

                    # Weighted metrics
                    if room_area > 0:
                        if 'en16798_compliance_rate' in room.computed_metrics:
                            aggregated['weighted_compliance_rate'] += room.computed_metrics['en16798_compliance_rate'] * room_area
                            aggregated['total_area'] += room_area
                            if room.area_m2 and room.area_m2 > 0:
                                aggregated['actual_area_m2'] += room.area_m2

                        if 'en16798_time_in_cat_I' in room.computed_metrics:
                            aggregated['time_in_cat_I_weighted'] += room.computed_metrics['en16798_time_in_cat_I'] * room_area
                        if 'en16798_time_in_cat_II' in room.computed_metrics:
                            aggregated['time_in_cat_II_weighted'] += room.computed_metrics['en16798_time_in_cat_II'] * room_area
                        if 'en16798_time_in_cat_III' in room.computed_metrics:
                            aggregated['time_in_cat_III_weighted'] += room.computed_metrics['en16798_time_in_cat_III'] * room_area
                        if 'en16798_time_in_cat_IV' in room.computed_metrics:
                            aggregated['time_in_cat_IV_weighted'] += room.computed_metrics['en16798_time_in_cat_IV'] * room_area

                        if 'en16798_violations' in room.computed_metrics:
                            aggregated['total_violations'] += room.computed_metrics['en16798_violations']

        # Calculate final weighted averages
        weight = aggregated['total_area'] if aggregated['total_area'] > 0 else aggregated['rooms_analyzed']
        if weight > 0:
            analyzed_area = aggregated['actual_area_m2'] if aggregated['actual_area_m2'] > 0 else weight
            return {
                'total_rooms': aggregated['total_rooms'],
                'rooms_analyzed': aggregated['rooms_analyzed'],
                'floors_analyzed': aggregated['floors_analyzed'],
                'category_distribution': aggregated['category_counts'],
                'rooms_by_category': aggregated['rooms_by_category'],
                'weighted_compliance_rate': round(aggregated['weighted_compliance_rate'] / weight, 2),
                'weighted_time_in_cat_I_pct': round(aggregated['time_in_cat_I_weighted'] / weight, 2),
                'weighted_time_in_cat_II_pct': round(aggregated['time_in_cat_II_weighted'] / weight, 2),
                'weighted_time_in_cat_III_pct': round(aggregated['time_in_cat_III_weighted'] / weight, 2),
                'weighted_time_in_cat_IV_pct': round(aggregated['time_in_cat_IV_weighted'] / weight, 2),
                'total_violations': aggregated['total_violations'],
                'building_achieved_category': self._determine_building_category(aggregated['category_counts']),
                'total_area_analyzed_m2': round(analyzed_area, 2),
            }

        return {}

    def _determine_building_category(self, category_counts: Dict[str, int]) -> Optional[str]:
        """
        Determine the building's overall EN16798 category based on room categories.

        Uses a conservative approach: building achieves a category only if
        >= 75% of rooms achieve that category or better.
        """
        if not category_counts:
            return None

        total_rooms = sum(category_counts.values())
        if total_rooms == 0:
            return None

        # Check from best to worst category
        cat_order = ['I', 'II', 'III', 'IV']
        cumulative_rooms = 0

        for cat in cat_order:
            cumulative_rooms += category_counts.get(cat, 0)
            percentage = (cumulative_rooms / total_rooms) * 100
            if percentage >= 75.0:
                return cat

        return None

    def compute_standards(
        self,
        floor_lookup: Optional[Callable[[str], Any]] = None,
        room_lookup: Optional[Callable[[str], Any]] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        season: str = "winter",
        force_recompute: bool = False,
    ) -> Dict[str, Any]:
        """
        Aggregate standards results from all floors and rooms in this building.
        
        Args:
            floor_lookup: Function to retrieve Floor objects by ID
            room_lookup: Function to retrieve Room objects by ID
            country: Country code (defaults to building's country)
            region: Region name
            season: Season for analysis
            force_recompute: If True, recompute even if cached
        
        Returns:
            Dictionary with aggregated standards results
        """
        if not force_recompute and 'building_standards' in self.computed_metrics:
            return self.computed_metrics['building_standards']
        
        from .standards_registry import get_registry
        
        results = {}
        
        # Use building's properties as defaults
        country = country or self.country
        region = region or self.metadata.get('region')
        building_type = self.building_type
        
        # Ensure all floors have computed their standards
        if floor_lookup and self.floor_ids:
            for floor_id in self.floor_ids:
                floor = floor_lookup(floor_id)
                if floor is None or not hasattr(floor, 'compute_standards'):
                    continue
                
                # Compute floor standards if not already done
                if 'floor_standards' not in floor.computed_metrics:
                    floor.compute_standards(
                        room_lookup=room_lookup,
                        country=country,
                        region=region,
                        building_type=building_type,
                        season=season,
                        force_recompute=False,
                    )
        
        # Ensure all direct rooms have computed their standards
        if room_lookup and self.room_ids:
            for room_id in self.room_ids:
                room = room_lookup(room_id)
                if room is None or not hasattr(room, 'compute_standards'):
                    continue
                
                # Compute room standards if not already done
                if 'standards_results' not in room.computed_metrics:
                    room.compute_standards(
                        country=country,
                        region=region,
                        building_type=building_type,
                        season=season,
                        force_recompute=False,
                    )
        
        # Get all child entities (floors and direct rooms)
        child_entities = []
        if floor_lookup and self.floor_ids:
            for floor_id in self.floor_ids:
                floor = floor_lookup(floor_id)
                if floor is not None:
                    child_entities.append(floor)
        
        if room_lookup and self.room_ids:
            for room_id in self.room_ids:
                room = room_lookup(room_id)
                if room is not None:
                    child_entities.append(room)
        
        # Get registry to access standard configs
        registry = get_registry()
        
        # Aggregate results for each standard
        for standard_id, standard_config in registry.standards.items():
            aggregation_config = standard_config.config_data.get('aggregation', {})
            
            # Check if this standard should aggregate to building level
            aggregate_to_types = aggregation_config.get('aggregate_to_types', [])
            if 'building' not in aggregate_to_types:
                continue
            
            # Collect child results for this standard
            child_results = []
            child_weights = []
            
            # Convert standard_id to match storage key (hyphen to underscore)
            storage_key = standard_id.replace('-', '_')
            
            for child in child_entities:
                # Get the appropriate results dict based on entity type
                if hasattr(child, 'computed_metrics'):
                    # Check if this is a Room by looking at the type name
                    is_room = child.__class__.__name__ == 'Room'
                    
                    if is_room:
                        child_standard_results = child.computed_metrics.get('standards_results', {})
                    else:  # Floor or other
                        child_standard_results = child.computed_metrics.get('floor_standards', {})
                    
                    if storage_key in child_standard_results:
                        result = child_standard_results[storage_key]
                        child_results.append(result)
                        
                        # Get weight for weighted aggregation
                        weight = child.area_m2 if hasattr(child, 'area_m2') else 1.0
                        child_weights.append(weight)
            
            if not child_results:
                continue
            
            # Apply aggregation based on config
            aggregated_result = self._aggregate_standard_results(
                standard_id=standard_id,
                child_results=child_results,
                child_weights=child_weights,
                aggregation_config=aggregation_config,
            )
            
            if aggregated_result:
                results[standard_id] = aggregated_result
        
        # Cache results
        self.computed_metrics['building_standards'] = results
        return results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary information about this building."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'building_type': self.building_type,
            'floor_count': self.floor_count,
            'room_count': self.room_count,
            'total_area_m2': self.area_m2,
            'year_built': self.year_built,
            'location': {
                'address': self.address,
                'city': self.city,
                'country': self.country,
                'coordinates': {'lat': self.latitude, 'lon': self.longitude} if self.latitude and self.longitude else None,
            },
            'floor_ids': self.floor_ids,
            'room_ids': self.room_ids,
            'epc_rating': self.epc_rating,
        }


# ============================================================
#  FLOOR - Single Floor Level
# ============================================================

class Floor(SpatialEntity):
    """
    Floor/level entity representing a single floor in a building.

    Aggregates multiple rooms on the same floor level.
    """
    type: SpatialEntityType = SpatialEntityType.FLOOR

    # Floor information
    floor_number: Optional[int] = Field(default=None, description="Floor number (0=ground, negative=basement)")
    building_id: Optional[str] = None

    # Computed metrics cache
    computed_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        exclude=True
    )
    metrics_computed_at: Optional[datetime] = None

    @property
    def room_ids(self) -> List[str]:
        """Get room IDs (alias for child_ids)."""
        return self.child_ids

    def add_room(self, room_id: str) -> None:
        """Add a room to this floor."""
        if room_id not in self.child_ids:
            self.child_ids.append(room_id)

    def remove_room(self, room_id: str) -> bool:
        """Remove a room from this floor."""
        if room_id in self.child_ids:
            self.child_ids.remove(room_id)
            return True
        return False

    def has_room(self, room_id: str) -> bool:
        """Check if floor contains a specific room."""
        return room_id in self.child_ids

    @property
    def room_count(self) -> int:
        """Get number of rooms on this floor."""
        return len(self.child_ids)

    def compute_metrics(
        self,
        room_lookup: Optional[Callable[[str], Any]] = None,
        force_recompute: bool = False
    ) -> Dict[str, Any]:
        """
        Compute floor-wide aggregated metrics from rooms including EN16798 analysis.

        Args:
            room_lookup: Function to retrieve Room objects by ID
            force_recompute: If True, recompute even if cached

        Returns:
            Dictionary with aggregated metrics including EN16798 compliance
        """
        if not force_recompute and 'floor_metrics' in self.computed_metrics:
            return self.computed_metrics['floor_metrics']

        results: Dict[str, Any] = {
            'room_count': self.room_count,
            'floor_number': self.floor_number,
        }

        if room_lookup is None or not self.child_ids:
            self.computed_metrics['floor_metrics'] = results
            return results

        # Aggregate metrics from rooms
        total_area = 0.0
        compliance_rates = []
        tail_ratings = []
        en16798_categories = []

        # EN16798-specific aggregation
        en16798_data = {
            'rooms_analyzed': 0,
            'category_counts': {},
            'weighted_compliance_rate': 0.0,
            'total_area': 0.0,
            'actual_area_m2': 0.0,
            'time_in_cat_I_weighted': 0.0,
            'time_in_cat_II_weighted': 0.0,
            'time_in_cat_III_weighted': 0.0,
            'time_in_cat_IV_weighted': 0.0,
            'total_violations': 0,
            'rooms_by_category': {'I': [], 'II': [], 'III': [], 'IV': [], 'non_compliant': []},
        }

        for room_id in self.child_ids:
            room = room_lookup(room_id)
            if room is None:
                continue

            room_area = room.area_m2 if room.area_m2 and room.area_m2 > 0 else None
            weight = room_area if room_area and room_area > 0 else 1.0
            if room_area:
                total_area += room_area

            if hasattr(room, 'computed_metrics'):
                # EN16798 aggregation
                if 'en16798_category' in room.computed_metrics:
                    category = room.computed_metrics['en16798_category']
                    if category:
                        en16798_categories.append(category)
                        en16798_data['category_counts'][category] = en16798_data['category_counts'].get(category, 0) + 1
                        en16798_data['rooms_by_category'][category].append(room_id)
                        en16798_data['rooms_analyzed'] += 1
                    else:
                        en16798_data['rooms_by_category']['non_compliant'].append(room_id)

                    # Weighted compliance rate (by area)
                    if 'en16798_compliance_rate' in room.computed_metrics and weight > 0:
                        compliance_rate = room.computed_metrics['en16798_compliance_rate']
                        en16798_data['weighted_compliance_rate'] += compliance_rate * weight
                        en16798_data['total_area'] += weight
                        if room_area:
                            en16798_data['actual_area_m2'] += room_area

                    # Aggregate time-in-category (weighted by area)
                    if weight > 0:
                        if 'en16798_time_in_cat_I' in room.computed_metrics:
                            en16798_data['time_in_cat_I_weighted'] += room.computed_metrics['en16798_time_in_cat_I'] * weight
                        if 'en16798_time_in_cat_II' in room.computed_metrics:
                            en16798_data['time_in_cat_II_weighted'] += room.computed_metrics['en16798_time_in_cat_II'] * weight
                        if 'en16798_time_in_cat_III' in room.computed_metrics:
                            en16798_data['time_in_cat_III_weighted'] += room.computed_metrics['en16798_time_in_cat_III'] * weight
                        if 'en16798_time_in_cat_IV' in room.computed_metrics:
                            en16798_data['time_in_cat_IV_weighted'] += room.computed_metrics['en16798_time_in_cat_IV'] * weight

                    # Aggregate violations
                    if 'en16798_violations' in room.computed_metrics:
                        en16798_data['total_violations'] += room.computed_metrics['en16798_violations']

                # Legacy metrics
                if 'overall_compliance_rate' in room.computed_metrics:
                    compliance_rates.append(room.computed_metrics['overall_compliance_rate'])

                if 'tail_overall_rating' in room.computed_metrics:
                    tail_ratings.append(room.computed_metrics['tail_overall_rating'])

        results['total_area_m2'] = total_area

        # Calculate weighted EN16798 metrics
        if en16798_data['total_area'] > 0:
            analyzed_area = en16798_data['actual_area_m2'] if en16798_data['actual_area_m2'] > 0 else en16798_data['total_area']
            results['en16798'] = {
                'rooms_analyzed': en16798_data['rooms_analyzed'],
                'total_rooms': len(self.child_ids),
                'category_distribution': en16798_data['category_counts'],
                'rooms_by_category': en16798_data['rooms_by_category'],
                'weighted_compliance_rate': round(en16798_data['weighted_compliance_rate'] / en16798_data['total_area'], 2),
                'weighted_time_in_cat_I_pct': round(en16798_data['time_in_cat_I_weighted'] / en16798_data['total_area'], 2),
                'weighted_time_in_cat_II_pct': round(en16798_data['time_in_cat_II_weighted'] / en16798_data['total_area'], 2),
                'weighted_time_in_cat_III_pct': round(en16798_data['time_in_cat_III_weighted'] / en16798_data['total_area'], 2),
                'weighted_time_in_cat_IV_pct': round(en16798_data['time_in_cat_IV_weighted'] / en16798_data['total_area'], 2),
                'total_violations': en16798_data['total_violations'],
                'floor_achieved_category': self._determine_floor_category(en16798_data['category_counts']),
                'total_area_analyzed_m2': round(analyzed_area, 2),
            }

        # Legacy metrics
        if compliance_rates:
            results['average_compliance_rate'] = sum(compliance_rates) / len(compliance_rates)
            results['min_compliance_rate'] = min(compliance_rates)
            results['max_compliance_rate'] = max(compliance_rates)
            results['rooms_analyzed'] = len(compliance_rates)

        if tail_ratings:
            results['average_tail_rating'] = sum(tail_ratings) / len(tail_ratings)
            results['worst_tail_rating'] = max(tail_ratings)
            results['best_tail_rating'] = min(tail_ratings)

        if en16798_categories:
            category_counts: Dict[str, int] = {}
            for cat in en16798_categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            results['en16798_category_distribution'] = category_counts

        # Cache results
        for key, value in results.items():
            self.computed_metrics[key] = value

        self.computed_metrics['floor_metrics'] = results
        self.metrics_computed_at = datetime.now()

        return results

    def _determine_floor_category(self, category_counts: Dict[str, int]) -> Optional[str]:
        """
        Determine the floor's overall EN16798 category based on room categories.

        Uses a conservative approach: floor achieves a category only if
        >= 80% of rooms achieve that category or better.
        """
        if not category_counts:
            return None

        total_rooms = sum(category_counts.values())
        if total_rooms == 0:
            return None

        # Check from best to worst category
        cat_order = ['I', 'II', 'III', 'IV']
        cumulative_rooms = 0

        for cat in cat_order:
            cumulative_rooms += category_counts.get(cat, 0)
            percentage = (cumulative_rooms / total_rooms) * 100
            if percentage >= 80.0:
                return cat

        return None

    def compute_standards(
        self,
        room_lookup: Optional[Callable[[str], Any]] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        building_type: Optional[str] = None,
        season: str = "winter",
        force_recompute: bool = False,
    ) -> Dict[str, Any]:
        """
        Aggregate standards results from all rooms on this floor.
        
        Args:
            room_lookup: Function to retrieve Room objects by ID
            country: Country code
            region: Region name  
            building_type: Building type
            season: Season for analysis
            force_recompute: If True, recompute even if cached
        
        Returns:
            Dictionary with aggregated standards results
        """
        if not force_recompute and 'floor_standards' in self.computed_metrics:
            return self.computed_metrics['floor_standards']
        
        results = {}
        
        if room_lookup is None or not self.child_ids:
            self.computed_metrics['floor_standards'] = results
            return results
        
        # Ensure all rooms have computed their standards
        for room_id in self.child_ids:
            room = room_lookup(room_id)
            if room is None or not hasattr(room, 'compute_standards'):
                continue
            
            # Compute room standards if not already done
            if 'standards_results' not in room.computed_metrics:
                room.compute_standards(
                    country=country,
                    region=region,
                    building_type=building_type,
                    season=season,
                    force_recompute=False,
                )
        
        from .standards_registry import get_registry
        
        # Get all child rooms
        child_rooms = []
        for room_id in self.child_ids:
            room = room_lookup(room_id)
            if room is not None:
                child_rooms.append(room)
        
        # Get registry to access standard configs
        registry = get_registry()
        
        print(f"DEBUG Floor.compute_standards() for floor {self.id}")
        print(f"  child_ids: {self.child_ids}")
        print(f"  child_rooms collected: {len(child_rooms)}")
        print(f"  standards in registry: {list(registry.standards.keys())}")
        
        # Aggregate results for each standard
        for standard_id, standard_config in registry.standards.items():
            aggregation_config = standard_config.config_data.get('aggregation', {})
            
            # Check if this standard should aggregate to floor level
            aggregate_to_types = aggregation_config.get('aggregate_to_types', [])
            print(f"  Standard {standard_id}: aggregate_to_types={aggregate_to_types}")
            
            if 'floor' not in aggregate_to_types:
                continue
            
            # Collect child results for this standard
            child_results = []
            child_weights = []
            
            for room in child_rooms:
                if hasattr(room, 'computed_metrics'):
                    room_standard_results = room.computed_metrics.get('standards_results', {})
                    
                    if standard_id in room_standard_results:
                        result = room_standard_results[standard_id]
                        child_results.append(result)
                        
                        # Get weight for weighted aggregation
                        weight = room.area_m2 if hasattr(room, 'area_m2') else 1.0
                        child_weights.append(weight)
            
            if not child_results:
                print(f"    No child results for {standard_id}")
                continue
            
            print(f"    Aggregating {len(child_results)} results for {standard_id}")
            
            # Apply aggregation based on config
            aggregated_result = self._aggregate_standard_results(
                standard_id=standard_id,
                child_results=child_results,
                child_weights=child_weights,
                aggregation_config=aggregation_config,
            )
            
            if aggregated_result:
                results[standard_id] = aggregated_result
        
        # Cache results
        self.computed_metrics['floor_standards'] = results
        return results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary information about this floor."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'building_id': self.building_id,
            'floor_number': self.floor_number,
            'room_count': self.room_count,
            'total_area_m2': self.area_m2,
            'room_ids': self.room_ids,
        }


# ============================================================
#  UNIT - Individual Unit/Apartment
# ============================================================

class Unit(SpatialEntity):
    """
    Unit entity representing an individual apartment or unit within a building.

    Contains unit-specific properties.
    """
    type: SpatialEntityType = SpatialEntityType.ZONE

    # Hierarchy
    building_id: Optional[str] = None
    floor_id: Optional[str] = None
    zone_id: Optional[str] = None
    room_ids: List[str] = Field(
        default_factory=list,
        description="Rooms assigned to this unit"
    )

    # Unit-specific metadata
    number_of_occupants: Optional[int] = Field(default=None, ge=0)
    ownership_type: Optional[str] = None  # e.g., 'owner-occupied', 'rental'

    def get_summary(self) -> Dict[str, Any]:
        """Get summary information about this unit."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'building_id': self.building_id,
            'floor_id': self.floor_id,
            'area_m2': self.area_m2,
            'number_of_occupants': self.number_of_occupants,
            'ownership_type': self.ownership_type,
        }
# ============================================================
#  ROOM - Individual Room/Space
# ============================================================

class Room(SpatialEntity):
    """
    Room entity representing a physical space with environmental measurements.

    Contains room-specific properties and provides self-analysis capabilities.
    """
    type: SpatialEntityType = SpatialEntityType.ROOM

    # Hierarchy
    floor_id: Optional[str] = None
    building_id: Optional[str] = None

    # Room-specific metadata
    activity_level: Optional[str] = None
    pollution_level: Optional[str] = None

    # Physical properties
    glass_to_wall_ratio: Optional[float] = Field(default=None, ge=0, le=1)
    last_renovation_year: Optional[int] = Field(default=None, ge=1800, le=2100)

    # Time series data
    timeseries_data: Dict[str, List[float]] = Field(
        default_factory=dict,
        description="Time series data by metric name"
    )
    timestamps: List[str] = Field(
        default_factory=list,
        description="Timestamps for time series data"
    )

    # Computed metrics cache
    computed_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        exclude=True
    )
    metrics_computed_at: Optional[datetime] = None

    @property
    def has_data(self) -> bool:
        """Check if room has time series data loaded."""
        return len(self.timeseries_data) > 0

    @property
    def available_metrics(self) -> List[str]:
        """Get list of available metric names in data."""
        return list(self.timeseries_data.keys())

    def add_timeseries(
        self,
        metric_name: str,
        values: List[float],
        timestamps: Optional[List[str]] = None
    ) -> None:
        """Add time series data for a metric."""
        self.timeseries_data[metric_name] = values
        if timestamps and not self.timestamps:
            self.timestamps = timestamps

    def get_timeseries(self, metric_name: str) -> Optional[List[float]]:
        """Get time series data for a specific metric."""
        return self.timeseries_data.get(metric_name)

    def compute_metrics(
        self,
        analyses: Optional[List[str]] = None,
        force_recompute: bool = False,
        season: str = "heating",
        outdoor_temperature: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Perform self-analysis of room data including en16798_1 compliance.

        Args:
            analyses: List of analyses to run (['en16798', 'tail', 'basic'])
            force_recompute: If True, recompute even if cached
            season: "heating" or "cooling" for EN16798 analysis
            outdoor_temperature: Outdoor temperature data for adaptive comfort

        Returns:
            Dictionary with analysis results including EN16798 compliance
        """
        if not force_recompute and 'room_metrics' in self.computed_metrics:
            return self.computed_metrics['room_metrics']

        results: Dict[str, Any] = {
            'room_id': self.id,
            'room_name': self.name,
            'has_data': self.has_data,
            'available_metrics': self.available_metrics,
        }

        if not self.has_data:
            self.computed_metrics['room_metrics'] = results
            return results

        # Default analyses
        if analyses is None:
            analyses = ['basic', 'en16798']

        # Calculate basic statistics
        if 'basic' in analyses:
            for metric_name, values in self.timeseries_data.items():
                if values:
                    results[f'{metric_name}_mean'] = sum(values) / len(values)
                    results[f'{metric_name}_min'] = min(values)
                    results[f'{metric_name}_max'] = max(values)

        # Run en16798_1 compliance analysis
        if 'en16798' in analyses and self._has_en16798_data():
            try:
                en16798_results = self._compute_en16798_compliance(season, outdoor_temperature)
                results['en16798'] = en16798_results

                # Store key metrics at top level for easy access
                if en16798_results:
                    results['en16798_category'] = en16798_results.get('achieved_category')
                    results['en16798_compliance_rate'] = en16798_results.get('overall_compliance_rate', 0.0)
                    results['en16798_time_in_cat_I'] = en16798_results.get('time_in_category_I_pct', 0.0)
                    results['en16798_time_in_cat_II'] = en16798_results.get('time_in_category_II_pct', 0.0)
                    results['en16798_time_in_cat_III'] = en16798_results.get('time_in_category_III_pct', 0.0)
                    results['en16798_time_in_cat_IV'] = en16798_results.get('time_in_category_IV_pct', 0.0)
                    results['en16798_violations'] = en16798_results.get('total_violations', 0)
            except Exception as e:
                results['en16798_error'] = str(e)

        # Cache results
        self.computed_metrics['room_metrics'] = results
        self.metrics_computed_at = datetime.now()

        return results

    def _has_en16798_data(self) -> bool:
        """Check if room has necessary data for EN16798 analysis."""
        # At minimum, need temperature data
        return 'temperature' in self.timeseries_data and len(self.timeseries_data['temperature']) > 0

    def _compute_en16798_compliance(
        self,
        season: str = "heating",
        outdoor_temperature: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Compute en16798_1 compliance for this room.

        Args:
            season: "heating" or "cooling"
            outdoor_temperature: Outdoor temperature data

        Returns:
            Dictionary with EN16798 compliance results
        """
        import pandas as pd

        from standards.en16798.analysis import (
            EN16798Calculator,
            VentilationType as CalcVentType,
        )

        # Convert timeseries data to pandas Series
        temperature = None
        co2 = None
        humidity = None
        outdoor_temp = None
        ts_index = None

        if self.timestamps:
            try:
                ts_index = pd.to_datetime(self.timestamps)
            except Exception:
                ts_index = None

        def _series(values: List[float], fallback_index: Optional[pd.DatetimeIndex]) -> pd.Series:
            if values is None:
                return pd.Series(dtype=float)
            if fallback_index is not None and len(values) == len(fallback_index):
                return pd.Series(values, index=fallback_index)
            return pd.Series(values)

        if 'temperature' in self.timeseries_data:
            temperature = _series(self.timeseries_data['temperature'], ts_index)

        if 'co2' in self.timeseries_data:
            co2 = _series(self.timeseries_data['co2'], ts_index)

        if 'humidity' in self.timeseries_data:
            humidity = _series(self.timeseries_data['humidity'], ts_index)

        if outdoor_temperature:
            outdoor_idx = ts_index if outdoor_temperature and ts_index is not None and len(outdoor_temperature) == len(ts_index) else None
            outdoor_temp = _series(outdoor_temperature, outdoor_idx)

        # Determine ventilation type
        vent_type = CalcVentType.MECHANICAL
        if self.ventilation_type and hasattr(self.ventilation_type, 'value'):
            vent_str = self.ventilation_type.value.lower()
            if 'natural' in vent_str:
                vent_type = CalcVentType.NATURAL
            elif 'mixed' in vent_str:
                vent_type = CalcVentType.MIXED_MODE

        # Run detailed analysis
        detailed_result = EN16798Calculator.assess_detailed_timeseries(
            temperature=temperature,
            co2=co2,
            humidity=humidity,
            outdoor_temperature=outdoor_temp,
            season=season,
            ventilation_type=vent_type
        )

        # Convert to dictionary
        return {
            'achieved_category': detailed_result.achieved_category.value if detailed_result.achieved_category else None,
            'all_compliant_categories': [cat.value for cat in detailed_result.all_compliant_categories],
            'overall_compliance_rate': detailed_result.overall_compliance_rate,
            'time_in_category_I_pct': detailed_result.time_in_category_I_pct,
            'time_in_category_II_pct': detailed_result.time_in_category_II_pct,
            'time_in_category_III_pct': detailed_result.time_in_category_III_pct,
            'time_in_category_IV_pct': detailed_result.time_in_category_IV_pct,
            'time_out_of_all_categories_pct': detailed_result.time_out_of_all_categories_pct,
            'total_data_points': detailed_result.total_data_points,
            'total_violations': detailed_result.total_violations,
            'temperature_metrics': detailed_result.temperature_metrics,
            'co2_metrics': detailed_result.co2_metrics,
            'humidity_metrics': detailed_result.humidity_metrics,
            'season': detailed_result.season,
            'adaptive_model_used': detailed_result.adaptive_model_used,
            'ventilation_type': detailed_result.ventilation_type,
        }

    def compute_standards(
        self,
        country: Optional[str] = None,
        region: Optional[str] = None,
        building_type: Optional[str] = None,
        season: str = "winter",
        outdoor_temperature: Optional[List[float]] = None,
        force_recompute: bool = False,
        entity_lookup: Optional[Callable[[str], Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compute all applicable standards for this room based on configuration.
        
        Automatically determines which standards to run based on:
        - Country and region
        - Building type and room type
        - Available sensor data
        - Season
        
        The room can access sensor data from anywhere in the hierarchy:
        - Indoor sensors from the room itself
        - Outdoor sensors from parent buildings or portfolio
        - Additional context from parent/child entities
        
        Args:
            country: Country code (e.g., 'DK', 'DE'). If None, tries to infer from building.
            region: Region name (e.g., 'Europe', 'Nordic'). If None, tries to infer from building.
            building_type: Building type. If None, tries to infer from parent entities.
            season: Season for analysis ('winter', 'summer', 'all_year')
            outdoor_temperature: Outdoor temperature data. If None, tries to get from hierarchy.
            force_recompute: If True, recompute even if cached
            entity_lookup: Function to retrieve any entity by ID for hierarchy traversal
        
        Returns:
            Dictionary with results from all applicable standards
        
        Examples:
            # With entity lookup, room can access outdoor_temperature from portfolio
            room.compute_standards(
                country='DK',
                season='winter',
                entity_lookup=lambda id: entity_registry.get(id),
            )
        """
        from .standards_registry import get_registry
        
        if not force_recompute and 'standards_results' in self.computed_metrics:
            return self.computed_metrics['standards_results']

        # Persist inferred building type for downstream standards (TAIL uses it for schedules)
        if building_type and not self.building_type:
            self.building_type = building_type
        
        results = {}
        
        if not self.has_data:
            self.computed_metrics['standards_results'] = results
            return results
        
        # Get the registry
        registry = get_registry()
        
        # Determine ventilation type
        vent_type_str = None
        if self.ventilation_type and hasattr(self.ventilation_type, 'value'):
            vent_type_str = self.ventilation_type.value.lower()
        
        # If outdoor_temperature not provided, try to get it from hierarchy
        if outdoor_temperature is None and entity_lookup is not None:
            outdoor_temp_values = self.get_timeseries_from_hierarchy(
                'outdoor_temperature',
                parent_lookup=entity_lookup,
                prefer_parents=True,
            )
            if outdoor_temp_values:
                outdoor_temperature = list(outdoor_temp_values)
        
        # Get applicable standards
        applicable_standards = registry.get_applicable_standards(
            country=country,
            region=region,
            building_type=building_type,
            room_type=self.room_type,
            ventilation_type=vent_type_str,
            season=season,
            available_metrics=set(self.available_metrics),
        )
        
        # Run each applicable standard
        for standard_config in applicable_standards:
            try:
                # Load the analysis function
                analysis_func = registry.load_analysis_module(standard_config.analysis_module)
                
                # Prepare timeseries dict
                timeseries_dict = dict(self.timeseries_data)
                
                # Run the analysis
                analysis_result = analysis_func(
                    spatial_entity=self,
                    timeseries_dict=timeseries_dict,
                    timestamps=self.timestamps,
                    season=season,
                    outdoor_temperature=outdoor_temperature,
                )
                
                # Store results
                standard_key = standard_config.id.replace('-', '_')
                summary = analysis_result.summary_results
                results[standard_key] = summary
                
                if standard_key == 'tail':
                    overall_rating = summary.get('overall_rating')
                    self.computed_metrics['tail_overall_rating'] = overall_rating
                    self.computed_metrics['tail_overall_rating_label'] = summary.get('overall_rating_label')
                    self.computed_metrics['tail_domains'] = summary.get('domains', {})
                    if 'visualization' in summary:
                        self.computed_metrics['tail_visualization'] = summary['visualization']
                    self.tail_rating = overall_rating
                    self.tail_rating_label = summary.get('overall_rating_label')
                    self.tail_domains = summary.get('domains', {})
                    self.tail_visualization = summary.get('visualization')
                
                # Also store in metadata for backward compatibility
                self.metadata[f'{standard_key}_analysis'] = summary
                
            except Exception as e:
                print(f"Warning: Could not run standard {standard_config.id}: {e}")
                import traceback
                traceback.print_exc()
                results[f'{standard_config.id}_error'] = str(e)
        
        # Cache results
        self.computed_metrics['standards_results'] = results
        return results

    def compute_simulations(
        self,
        force_recompute: bool = False,
    ) -> Dict[str, Any]:
        """
        Compute all applicable simulations for this room.
        
        Automatically determines which simulations to run based on:
        - Available sensor data
        - Entity type
        
        Args:
            force_recompute: If True, recompute even if cached
        
        Returns:
            Dictionary with results from all applicable simulations
        """
        from dataclasses import asdict
        
        import pandas as pd
        
        from .standards_registry import get_registry
        
        if not force_recompute and 'simulation_results' in self.computed_metrics:
            return self.computed_metrics['simulation_results']
        
        results = {}
        
        if not self.has_data:
            self.computed_metrics['simulation_results'] = results
            return results
        
        # Get the registry
        registry = get_registry()
        
        # Get applicable simulations
        applicable_simulations = registry.get_applicable_simulations(
            entity_type=self.type,
            available_metrics=set(self.available_metrics),
        )
        
        # Run each applicable simulation
        for simulation_config in applicable_simulations:
            try:
                # Load the simulation class
                simulation_class = registry.load_simulation_class(simulation_config.module_path)
                simulator = simulation_class()
                
                # Prepare data based on simulation type
                if simulation_config.id == 'occupancy':
                    # Occupancy simulation needs CO2 as pandas Series
                    if 'co2' in self.timeseries_data and self.timestamps:
                        idx = pd.to_datetime(self.timestamps)
                        co2_series = pd.Series(self.timeseries_data['co2'], index=idx)
                        
                        occupancy_result = simulator.detect_occupancy(co2_series)
                        results['occupancy'] = asdict(occupancy_result)
                        
                        # Store in metadata for backward compatibility
                        self.metadata['occupancy_simulation'] = asdict(occupancy_result)
                
                elif simulation_config.id == 'ventilation':
                    # Ventilation simulation needs CO2
                    if 'co2' in self.timeseries_data:
                        # Implementation depends on VentilationCalculator interface
                        # For now, skip if not implemented
                        pass
                
            except Exception as e:
                print(f"Warning: Could not run simulation {simulation_config.id}: {e}")
                import traceback
                traceback.print_exc()
                results[f'{simulation_config.id}_error'] = str(e)
        
        # Cache results
        self.computed_metrics['simulation_results'] = results
        return results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary information about this room."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'floor_id': self.floor_id,
            'building_id': self.building_id,
            'room_type': self.room_type,
            'area_m2': self.area_m2,
            'volume_m3': self.volume_m3,
            'design_occupancy': self.design_occupancy,
            'ventilation_type': self.ventilation_type.value if self.ventilation_type else None,
            'has_data': self.has_data,
            'available_metrics': self.available_metrics,
            'data_points': len(self.timestamps) if self.timestamps else 0,
        }


__all__ = [
    "Portfolio",
    "Building",
    "Floor",
    "Room",
]
