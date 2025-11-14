"""
Base Spatial Entity Models

Base SpatialEntity class and simple Zone entity.
Enhanced entities (Portfolio, Building, Floor, Room) are in entities.py.
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from .aggregators import Aggregator
from .analysis import AnalysisContext, AnalysisResult, SimulationResult
from .access import AccessControlEntry, UserContext
from .enums import (
    PermissionScope,
    SpatialEntityType,
    VentilationType,
    SpatialEntityType,
)
from .metering import SensorDefinition, SensorGroup, SensorSource, SensorSourceType


class SpatialEntity(BaseModel):
    """
    Base spatial entity model.

    Represents any spatial element in a building hierarchy:
    Portfolio → Building → Floor → Room → Zone
    """
    id: str
    name: str
    type: SpatialEntityType

    parent_ids: List[str] = Field(default_factory=list)
    child_ids: List[str] = Field(default_factory=list)

    # Context for rule selection
    country: Optional[str] = None        # e.g. "EU", "US", "DK"
    region: Optional[str] = None         # e.g. "NA", "Nordic", state, etc.
    climate_zone: Optional[str] = None   # any scheme you want

    # Semantic building metadata
    building_type: Optional[str] = None  # e.g. "office", "school", ...
    room_type: Optional[str] = None      # e.g. "classroom", "meeting_room"
    ventilation_type: Optional[VentilationType] = VentilationType.UNKNOWN

    area_m2: Optional[float] = None
    volume_m3: Optional[float] = None
    design_occupancy: Optional[int] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    geometry_ref: Optional[str] = None

    sensor_groups: Dict[str, SensorGroup] = Field(
        default_factory=dict,
        exclude=True,
    )
    computed_metrics: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    access_control: List[AccessControlEntry] = Field(default_factory=list, exclude=True)

    def load_sensor(
        self,
        sensor: SensorDefinition,
        source: Optional[SensorSource] = None,
        source_type: Optional[SensorSourceType] = None,
        **kwargs: Any,
    ) -> SensorGroup:
        """
        Attach a sensor definition to this spatial entity.
        """
        if sensor.spatial_entity_id != self.id:
            sensor.spatial_entity_id = self.id

        if source:
            sensor.sources.append(source)
        elif source_type:
            sensor.sources.append(
                SensorSource(
                    id=f"{sensor.id}:{source_type}",
                    type=source_type,
                    config={k: v for k, v in kwargs.items()},
                )
            )

        parameter = sensor.parameter or sensor.metric.value
        group = self.sensor_groups.get(parameter)
        if not group:
            group = SensorGroup(parameter=parameter, metric=sensor.metric)
            self.sensor_groups[parameter] = group

        group.add_sensor(sensor)
        return group

    def compute_analysis(
        self,
        calculators: Optional[List[Callable[..., AnalysisResult]]] = None,
        standards_resolver: Optional[Callable[["SpatialEntity"], List[str]]] = None,
        aggregator: Optional[Aggregator] = None,
        child_results: Optional[List[AnalysisResult]] = None,
        user_context: Optional[UserContext] = None,
        **kwargs: Any,
    ) -> Dict[str, AnalysisResult]:
        """
        Run calculators applicable to this entity and cache their results.
        """
        self._enforce_access(user_context, PermissionScope.EXECUTE)

        calculators = calculators or []
        standards = standards_resolver(self) if standards_resolver else []
        spatial_level = self._to_granularity()

        context = AnalysisContext(
            spatial_entity_id=self.id,
            spatial_level=spatial_level,
            sensor_parameters=list(self.sensor_groups.keys()),
            standard_ids=standards,
            metadata={"building_type": self.building_type, "room_type": self.room_type},
        )

        results: Dict[str, AnalysisResult] = {}
        for calculator in calculators:
            result = calculator(
                entity=self,
                context=context,
                sensor_groups=self.sensor_groups,
                standards=standards,
                **kwargs,
            )
            if isinstance(result, AnalysisResult):
                results[result.id] = result

        if aggregator and child_results:
            aggregate_key = kwargs.get("aggregate_key")
            values: List[float] = []
            weights: List[float] = []
            for child in child_results:
                if aggregate_key is None:
                    continue
                value = child.results.get(aggregate_key)
                if value is None:
                    continue
                values.append(value)
                weights.append(child.results.get("weight", 1.0))

            aggregated_value = aggregator.aggregate(values, weights or None) if values else None
            if aggregated_value is not None:
                results[f"{aggregator.id}:{aggregate_key}"] = AnalysisResult(
                    id=f"{self.id}:{aggregator.id}:{aggregate_key}",
                    analysis_type=child_results[0].analysis_type if child_results else None,
                    context=context,
                    results={aggregate_key: aggregated_value},
                    provenance={"aggregation": aggregator.type.value},
                )

        if results:
            self.computed_metrics.setdefault("analysis_results", {}).update(results)
        return results

    def compute_simulation(
        self,
        simulators: Optional[List[Callable[..., SimulationResult]]] = None,
        user_context: Optional[UserContext] = None,
        **kwargs: Any,
    ) -> Dict[str, SimulationResult]:
        """
        Execute simulation models tied to this spatial entity.
        """
        self._enforce_access(user_context, PermissionScope.EXECUTE)

        simulators = simulators or []
        spatial_level = self._to_granularity()
        context = AnalysisContext(
            spatial_entity_id=self.id,
            spatial_level=spatial_level,
            sensor_parameters=list(self.sensor_groups.keys()),
            standard_ids=[],
            metadata={"simulation": True},
        )

        results: Dict[str, SimulationResult] = {}
        for simulator in simulators:
            result = simulator(
                entity=self,
                context=context,
                sensor_groups=self.sensor_groups,
                **kwargs,
            )
            if isinstance(result, SimulationResult):
                results[result.id] = result

        if results:
            self.computed_metrics.setdefault("simulation_results", {}).update(results)
        return results

    def _to_granularity(self) -> SpatialEntityType:
        try:
            return SpatialEntityType(self.type.value)
        except ValueError:
            return SpatialEntityType.BUILDING

    def _enforce_access(
        self,
        user_context: Optional[UserContext],
        scope: PermissionScope,
    ) -> None:
        if user_context is None:
            return
        if not user_context.has_access(self.id, scope):
            raise PermissionError(f"User {user_context.user.id} lacks {scope.value} access to {self.id}")

    def get_sensor_data(
        self,
        parameter: str,
        search_parents: bool = True,
        search_children: bool = False,
        parent_lookup: Optional[Callable[[str], Optional["SpatialEntity"]]] = None,
        child_lookup: Optional[Callable[[str], Optional["SpatialEntity"]]] = None,
    ) -> Optional[SensorGroup]:
        """
        Get sensor data for a parameter from this entity or its hierarchy.
        
        Args:
            parameter: Parameter name (e.g., 'temperature', 'outdoor_temperature')
            search_parents: If True, search up the hierarchy if not found locally
            search_children: If True, search down the hierarchy if not found locally
            parent_lookup: Function to retrieve parent entities by ID
            child_lookup: Function to retrieve child entities by ID
        
        Returns:
            SensorGroup if found, None otherwise
        
        Examples:
            # Get room temperature from the room itself
            room.get_sensor_data('temperature')
            
            # Get outdoor temperature from parent building/portfolio
            room.get_sensor_data('outdoor_temperature', search_parents=True, parent_lookup=get_entity)
            
            # Get average indoor temperature from all child rooms
            building.get_sensor_data('temperature', search_children=True, child_lookup=get_entity)
        """
        # First check this entity
        if parameter in self.sensor_groups:
            return self.sensor_groups[parameter]
        
        # Search parents (up the hierarchy)
        if search_parents and parent_lookup:
            for parent_id in self.parent_ids:
                parent = parent_lookup(parent_id)
                if parent is None:
                    continue
                
                # Check parent directly
                if parameter in parent.sensor_groups:
                    return parent.sensor_groups[parameter]
                
                # Recursively search parent's parents
                result = parent.get_sensor_data(
                    parameter,
                    search_parents=True,
                    search_children=False,
                    parent_lookup=parent_lookup,
                )
                if result:
                    return result
        
        # Search children (down the hierarchy)
        if search_children and child_lookup:
            for child_id in self.child_ids:
                child = child_lookup(child_id)
                if child is None:
                    continue
                
                # Check child directly
                if parameter in child.sensor_groups:
                    return child.sensor_groups[parameter]
                
                # Recursively search child's children
                result = child.get_sensor_data(
                    parameter,
                    search_parents=False,
                    search_children=True,
                    child_lookup=child_lookup,
                )
                if result:
                    return result
        
        return None

    def get_timeseries_from_hierarchy(
        self,
        parameter: str,
        parent_lookup: Optional[Callable[[str], Optional["SpatialEntity"]]] = None,
        child_lookup: Optional[Callable[[str], Optional["SpatialEntity"]]] = None,
        prefer_parents: bool = True,
    ) -> Optional[List[float]]:
        """
        Get timeseries data for a parameter from anywhere in the hierarchy.
        
        This is a convenience method that searches the hierarchy and extracts
        the actual timeseries values from the sensor.
        
        Args:
            parameter: Parameter name (e.g., 'temperature', 'outdoor_temperature')
            parent_lookup: Function to retrieve parent entities by ID
            child_lookup: Function to retrieve child entities by ID
            prefer_parents: If True, search parents first; otherwise search children first
        
        Returns:
            List of timeseries values if found, None otherwise
        
        Examples:
            # Get outdoor temperature from portfolio-level weather station
            outdoor_temp = room.get_timeseries_from_hierarchy(
                'outdoor_temperature',
                parent_lookup=entity_registry.get,
                prefer_parents=True
            )
            
            # Get room temperature locally or from children
            indoor_temp = building.get_timeseries_from_hierarchy(
                'temperature',
                child_lookup=entity_registry.get,
                prefer_parents=False
            )
        """
        if prefer_parents:
            # Try parents first, then self, then children
            sensor_group = self.get_sensor_data(
                parameter,
                search_parents=True,
                search_children=False,
                parent_lookup=parent_lookup,
            )
            
            if not sensor_group and child_lookup:
                sensor_group = self.get_sensor_data(
                    parameter,
                    search_parents=False,
                    search_children=True,
                    child_lookup=child_lookup,
                )
        else:
            # Try children first, then self, then parents
            sensor_group = self.get_sensor_data(
                parameter,
                search_parents=False,
                search_children=True,
                child_lookup=child_lookup,
            )
            
            if not sensor_group and parent_lookup:
                sensor_group = self.get_sensor_data(
                    parameter,
                    search_parents=True,
                    search_children=False,
                    parent_lookup=parent_lookup,
                )
        
        if not sensor_group or not sensor_group.sensors:
            return None
        
        # Extract timeseries data from the first sensor
        first_sensor = sensor_group.sensors[0]
        
        # Try to get timeseries from sensor metadata
        if 'timeseries' in first_sensor.metadata:
            ts_data = first_sensor.metadata['timeseries']
            if isinstance(ts_data, dict):
                # Multiple timeseries - get the first one
                first_ts = next(iter(ts_data.values()))
                if isinstance(first_ts, dict) and 'values' in first_ts:
                    return first_ts['values']
            elif isinstance(ts_data, list):
                return ts_data
        
        return None

    def get_available_parameters(
        self,
        include_parents: bool = True,
        include_children: bool = True,
        parent_lookup: Optional[Callable[[str], Optional["SpatialEntity"]]] = None,
        child_lookup: Optional[Callable[[str], Optional["SpatialEntity"]]] = None,
    ) -> Dict[str, str]:
        """
        Get all available sensor parameters across the hierarchy.
        
        Args:
            include_parents: Include parameters from parent entities
            include_children: Include parameters from child entities
            parent_lookup: Function to retrieve parent entities by ID
            child_lookup: Function to retrieve child entities by ID
        
        Returns:
            Dictionary mapping parameter names to entity IDs where they're found
        
        Examples:
            # Get all available parameters
            params = room.get_available_parameters(
                parent_lookup=get_entity,
                child_lookup=get_entity
            )
            # params = {
            #     'temperature': 'room_id',
            #     'co2': 'room_id',
            #     'outdoor_temperature': 'building_id',
            #     'humidity': 'room_id'
            # }
        """
        available = {}
        
        # Add this entity's parameters
        for parameter in self.sensor_groups.keys():
            available[parameter] = self.id
        
        # Add parent parameters
        if include_parents and parent_lookup:
            for parent_id in self.parent_ids:
                parent = parent_lookup(parent_id)
                if parent is None:
                    continue
                
                # Add parent's parameters (don't override if already found)
                for parameter in parent.sensor_groups.keys():
                    if parameter not in available:
                        available[parameter] = parent_id
                
                # Recursively get parent's parents' parameters
                parent_params = parent.get_available_parameters(
                    include_parents=True,
                    include_children=False,
                    parent_lookup=parent_lookup,
                )
                for parameter, entity_id in parent_params.items():
                    if parameter not in available:
                        available[parameter] = entity_id
        
        # Add child parameters
        if include_children and child_lookup:
            for child_id in self.child_ids:
                child = child_lookup(child_id)
                if child is None:
                    continue
                
                # Add child's parameters (don't override if already found)
                for parameter in child.sensor_groups.keys():
                    if parameter not in available:
                        available[parameter] = child_id
                
                # Recursively get child's children's parameters
                child_params = child.get_available_parameters(
                    include_parents=False,
                    include_children=True,
                    child_lookup=child_lookup,
                )
                for parameter, entity_id in child_params.items():
                    if parameter not in available:
                        available[parameter] = entity_id
        
        return available

    def aggregate_timeseries_from_children(
        self,
        parameter: str,
        child_lookup: Callable[[str], Optional["SpatialEntity"]],
        aggregation_method: str = "mean",
        recursive: bool = True,
    ) -> Optional[List[float]]:
        """
        Aggregate timeseries data from all child entities.
        
        Args:
            parameter: Parameter name to aggregate (e.g., 'temperature', 'co2')
            child_lookup: Function to retrieve child entities by ID
            aggregation_method: How to aggregate ('mean', 'median', 'min', 'max', 'sum')
            recursive: If True, aggregate from all descendants; if False, only direct children
        
        Returns:
            Aggregated timeseries values, or None if no data found
        
        Examples:
            # Get average temperature across all rooms in a building
            avg_temp = building.aggregate_timeseries_from_children(
                'temperature',
                child_lookup=get_entity,
                aggregation_method='mean'
            )
        """
        import numpy as np
        
        # Collect timeseries from all children
        all_timeseries = []
        
        for child_id in self.child_ids:
            child = child_lookup(child_id)
            if child is None:
                continue
            
            # Get data from direct child
            if parameter in child.sensor_groups:
                ts_data = child.get_timeseries_from_hierarchy(
                    parameter,
                    prefer_parents=False,
                )
                if ts_data:
                    all_timeseries.append(ts_data)
            
            # Recursively get from grandchildren
            if recursive and child.child_ids:
                child_agg = child.aggregate_timeseries_from_children(
                    parameter,
                    child_lookup=child_lookup,
                    aggregation_method=aggregation_method,
                    recursive=True,
                )
                if child_agg:
                    all_timeseries.append(child_agg)
        
        if not all_timeseries:
            return None
        
        # Find minimum length to align all series
        min_length = min(len(ts) for ts in all_timeseries)
        aligned_series = [ts[:min_length] for ts in all_timeseries]
        
        # Convert to numpy array for easy aggregation
        array = np.array(aligned_series)
        
        # Apply aggregation method
        if aggregation_method == "mean":
            result = np.mean(array, axis=0)
        elif aggregation_method == "median":
            result = np.median(array, axis=0)
        elif aggregation_method == "min":
            result = np.min(array, axis=0)
        elif aggregation_method == "max":
            result = np.max(array, axis=0)
        elif aggregation_method == "sum":
            result = np.sum(array, axis=0)
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation_method}")
        
        return result.tolist()

    def compute_statistics_from_children(
        self,
        parameter: str,
        child_lookup: Callable[[str], Optional["SpatialEntity"]],
        recursive: bool = True,
    ) -> Optional[Dict[str, float]]:
        """
        Compute statistical summary of a parameter across all children.
        
        Args:
            parameter: Parameter name to analyze
            child_lookup: Function to retrieve child entities by ID
            recursive: If True, include all descendants; if False, only direct children
        
        Returns:
            Dictionary with statistics: mean, median, min, max, std, q25, q75, count
        
        Examples:
            # Get temperature statistics across all rooms in a building
            stats = building.compute_statistics_from_children('temperature', get_entity)
            # stats = {
            #     'mean': 22.5,
            #     'median': 22.3,
            #     'min': 20.1,
            #     'max': 24.8,
            #     'std': 1.2,
            #     'q25': 21.5,
            #     'q75': 23.4,
            #     'count': 50,
            #     'rooms_analyzed': 10
            # }
        """
        import numpy as np
        
        # Collect all values from children
        all_values = []
        rooms_analyzed = 0
        
        for child_id in self.child_ids:
            child = child_lookup(child_id)
            if child is None:
                continue
            
            # Get timeseries from child
            ts_data = None
            if parameter in child.sensor_groups:
                ts_data = child.get_timeseries_from_hierarchy(
                    parameter,
                    prefer_parents=False,
                )
            
            if ts_data:
                all_values.extend(ts_data)
                if child.type == SpatialEntityType.ROOM:
                    rooms_analyzed += 1
            
            # Recursively get from descendants
            if recursive and child.child_ids:
                child_stats = child.compute_statistics_from_children(
                    parameter,
                    child_lookup=child_lookup,
                    recursive=True,
                )
                if child_stats and 'values' in child_stats:
                    all_values.extend(child_stats['values'])
                    rooms_analyzed += child_stats.get('rooms_analyzed', 0)
        
        if not all_values:
            return None
        
        # Compute statistics
        values_array = np.array(all_values)
        
        stats = {
            'mean': float(np.mean(values_array)),
            'median': float(np.median(values_array)),
            'min': float(np.min(values_array)),
            'max': float(np.max(values_array)),
            'std': float(np.std(values_array)),
            'q25': float(np.percentile(values_array, 25)),
            'q75': float(np.percentile(values_array, 75)),
            'count': len(all_values),
            'rooms_analyzed': rooms_analyzed,
            'values': all_values,  # Include raw values for potential re-aggregation
        }
        
        return stats

    def auto_aggregate_sensor_data(
        self,
        child_lookup: Callable[[str], Optional["SpatialEntity"]],
        force_recompute: bool = False,
    ) -> Dict[str, Any]:
        """
        Automatically aggregate sensor data from all children.
        
        Creates aggregated timeseries and statistics for all sensor parameters
        found in child entities. Results are cached in computed_metrics.
        
        Args:
            child_lookup: Function to retrieve child entities by ID
            force_recompute: If True, recompute even if cached
        
        Returns:
            Dictionary with aggregated data:
            {
                'temperature': {
                    'mean_timeseries': [...],
                    'median_timeseries': [...],
                    'min_timeseries': [...],
                    'max_timeseries': [...],
                    'statistics': {'mean': 22.5, 'median': 22.3, ...}
                },
                'co2': {...},
                ...
            }
        
        Examples:
            # Auto-aggregate all sensor data for a building
            building.auto_aggregate_sensor_data(child_lookup=get_entity)
            
            # Access aggregated data
            avg_temp = building.computed_metrics['aggregated_sensors']['temperature']['mean_timeseries']
            temp_stats = building.computed_metrics['aggregated_sensors']['temperature']['statistics']
        """
        cache_key = 'aggregated_sensors'
        
        if not force_recompute and cache_key in self.computed_metrics:
            return self.computed_metrics[cache_key]
        
        if not self.child_ids:
            return {}
        
        # Find all parameters available in children
        available_params = set()
        for child_id in self.child_ids:
            child = child_lookup(child_id)
            if child is None:
                continue
            
            child_params = child.get_available_parameters(
                include_parents=False,
                include_children=True,
                child_lookup=child_lookup,
            )
            available_params.update(child_params.keys())
        
        # Aggregate each parameter
        aggregated = {}
        
        for parameter in available_params:
            param_data = {}
            
            # Compute aggregated timeseries
            for method in ['mean', 'median', 'min', 'max']:
                try:
                    ts = self.aggregate_timeseries_from_children(
                        parameter,
                        child_lookup=child_lookup,
                        aggregation_method=method,
                        recursive=True,
                    )
                    if ts:
                        param_data[f'{method}_timeseries'] = ts
                except Exception as e:
                    print(f"Warning: Could not aggregate {parameter} with {method}: {e}")
            
            # Compute statistics
            try:
                stats = self.compute_statistics_from_children(
                    parameter,
                    child_lookup=child_lookup,
                    recursive=True,
                )
                if stats:
                    # Remove raw values from cached stats to save memory
                    stats_without_values = {k: v for k, v in stats.items() if k != 'values'}
                    param_data['statistics'] = stats_without_values
            except Exception as e:
                print(f"Warning: Could not compute statistics for {parameter}: {e}")
            
            if param_data:
                aggregated[parameter] = param_data
        
        # Cache results
        self.computed_metrics[cache_key] = aggregated
        
        return aggregated


__all__ = [
    "SpatialEntity"
]
