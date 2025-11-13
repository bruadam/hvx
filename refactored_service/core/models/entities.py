"""
Enhanced Spatial Entity Implementations

Provides specific implementations for Portfolio, Building, Floor, and Room
with domain-specific methods, aggregation capabilities, and self-analysis.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pydantic import Field

from .base_entities import SpatialEntity
from .enums import SpatialEntityType, VentilationType


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
        Compute portfolio-wide aggregated metrics from buildings.

        Args:
            building_lookup: Function to retrieve Building objects by ID
            force_recompute: If True, recompute even if cached

        Returns:
            Dictionary with aggregated metrics
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

        # Cache results
        self.computed_metrics['portfolio_metrics'] = results
        self.metrics_computed_at = datetime.now()

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

    def calculate_primary_energy_per_m2(self) -> Optional[float]:
        """
        Calculate primary energy consumption per m² per year.

        Returns:
            Primary energy in kWh/m²/year, or None if data missing
        """
        if not self.area_m2 or self.area_m2 <= 0:
            return None

        total_energy = 0.0
        if self.annual_heating_kwh:
            total_energy += self.annual_heating_kwh * 1.0  # Primary energy factor
        if self.annual_cooling_kwh:
            total_energy += self.annual_cooling_kwh * 2.5
        if self.annual_electricity_kwh:
            total_energy += self.annual_electricity_kwh * 2.5
        if self.annual_hot_water_kwh:
            total_energy += self.annual_hot_water_kwh * 1.0

        # Subtract renewable energy
        if self.annual_renewable_kwh or self.annual_solar_pv_kwh:
            renewable = self.annual_renewable_kwh or self.annual_solar_pv_kwh or 0
            total_energy = max(0, total_energy - renewable)

        return total_energy / self.area_m2 if self.area_m2 > 0 else None

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
        primary_energy = self.calculate_primary_energy_per_m2()
        if primary_energy is not None:
            summary["primary_energy_kwh_m2"] = primary_energy
        summary["epc_rating"] = self.epc_rating

        return summary

    def compute_metrics(
        self,
        metrics: Optional[List[str]] = None,
        force_recompute: bool = False
    ) -> Dict[str, Any]:
        """
        Compute building-level metrics (energy, EPC, etc.).

        Args:
            metrics: List of metrics to compute (['energy', 'epc'])
            force_recompute: If True, recompute even if cached

        Returns:
            Dictionary with computed metrics
        """
        if not force_recompute and 'building_metrics' in self.computed_metrics:
            return self.computed_metrics['building_metrics']

        results: Dict[str, Any] = {}

        if metrics is None:
            metrics = ['energy']

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

        # Cache results
        for key, value in results.items():
            self.computed_metrics[key] = value

        self.computed_metrics['building_metrics'] = results
        self.metrics_computed_at = datetime.now()

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
        Compute floor-wide aggregated metrics from rooms.

        Args:
            room_lookup: Function to retrieve Room objects by ID
            force_recompute: If True, recompute even if cached

        Returns:
            Dictionary with aggregated metrics
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

        for room_id in self.child_ids:
            room = room_lookup(room_id)
            if room is None:
                continue

            if room.area_m2:
                total_area += room.area_m2

            if hasattr(room, 'computed_metrics'):
                if 'overall_compliance_rate' in room.computed_metrics:
                    compliance_rates.append(room.computed_metrics['overall_compliance_rate'])

                if 'tail_overall_rating' in room.computed_metrics:
                    tail_ratings.append(room.computed_metrics['tail_overall_rating'])

                if 'en16798_category' in room.computed_metrics:
                    en16798_categories.append(room.computed_metrics['en16798_category'])

        results['total_area_m2'] = total_area

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
        force_recompute: bool = False
    ) -> Dict[str, Any]:
        """
        Perform self-analysis of room data.

        Args:
            analyses: List of analyses to run (['en16798', 'tail'])
            force_recompute: If True, recompute even if cached

        Returns:
            Dictionary with analysis results
        """
        if not force_recompute and 'room_metrics' in self.computed_metrics:
            return self.computed_metrics['room_metrics']

        results: Dict[str, Any] = {
            'room_id': self.id,
            'has_data': self.has_data,
            'available_metrics': self.available_metrics,
        }

        if not self.has_data:
            self.computed_metrics['room_metrics'] = results
            return results

        # Calculate basic statistics
        for metric_name, values in self.timeseries_data.items():
            if values:
                results[f'{metric_name}_mean'] = sum(values) / len(values)
                results[f'{metric_name}_min'] = min(values)
                results[f'{metric_name}_max'] = max(values)

        # Cache results
        self.computed_metrics['room_metrics'] = results
        self.metrics_computed_at = datetime.now()

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
