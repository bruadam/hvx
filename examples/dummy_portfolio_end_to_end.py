#!/usr/bin/env python
"""
End-to-end example
==================

This script shows how to:
1. Load the `data/samples/dummy_data` folder with the CSV connector.
2. Materialize portfolio → building → floor → room spatial entities.
3. Attach metering points/time series as sensor definitions.
4. Run indoor-environment standards (EN 16798 + TAIL) per room.
5. Execute occupancy & ventilation simulations per room.
6. Aggregate compliance up through floors, buildings, and the portfolio.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Iterable, Optional, Tuple

from connectors.csv import load_dummy_data
from core.entities import Building, Floor, Portfolio, Room
from core.enums import MetricType, SpatialEntityType
from core.metering import SensorDefinition, SensorSourceType
from core.spacial_entity import SpatialEntity


def main() -> None:
    data_root = Path(__file__).resolve().parents[1] / "data" / "samples" / "dummy_data"
    result = load_dummy_data(data_root)

    if hasattr(result, "rooms"):
        rooms = result.rooms
        buildings = result.buildings
        floors = result.floors
        portfolio = result.portfolio or Portfolio(
            id="dummy_portfolio",
            name="Dummy Sample Portfolio",
            type=SpatialEntityType.PORTFOLIO,
        )
    else:
        entities, metering_points, timeseries = result
        portfolio, buildings, floors, rooms = build_portfolio_hierarchy(entities)
        attach_sensors_and_series(entities, metering_points, timeseries)

    # Create entity lookup registry
    entity_registry = {}
    entity_registry[portfolio.id] = portfolio
    for building_id, building in buildings.items():
        entity_registry[building_id] = building
    for floor_id, floor in floors.items():
        entity_registry[floor_id] = floor
    for room_id, room in rooms.items():
        entity_registry[room_id] = room
    
    def get_entity(entity_id: str):
        return entity_registry.get(entity_id)

    run_room_standards_and_simulations(rooms, buildings, floors, portfolio, get_entity)

    # Auto-aggregate sensor data from children to parents
    print("\n=== Auto-Aggregating Sensor Data ===")
    for building_id, building in buildings.items():
        print(f"Aggregating data for {building_id}...")
        building.auto_aggregate_sensor_data(child_lookup=get_entity, force_recompute=True)
    
    portfolio.auto_aggregate_sensor_data(child_lookup=get_entity, force_recompute=True)

    # Aggregate standards results from rooms up to floors, buildings, and portfolio
    floor_metrics = {
        floor_id: floor.compute_standards(
            room_lookup=rooms.get,
            country="DK",
            region="Europe",
            building_type="office",
            season="winter",
            force_recompute=True,
        )
        for floor_id, floor in floors.items()
    }
    
    building_metrics = {
        building_id: building.compute_standards(
            floor_lookup=floors.get,
            room_lookup=rooms.get,
            season="winter",
            force_recompute=True,
        )
        for building_id, building in buildings.items()
    }
    
    portfolio_metrics = portfolio.compute_standards(
        building_lookup=buildings.get,
        floor_lookup=floors.get,
        room_lookup=rooms.get,
        season="winter",
        force_recompute=True,
    )

    print_portfolio_summary(
        portfolio,
        portfolio_metrics,
        building_metrics,
        floor_metrics,
        rooms.values(),
        buildings,
    )


def build_portfolio_hierarchy(
    entities: Dict[str, SpatialEntity],
) -> Tuple[Portfolio, Dict[str, Building], Dict[str, Floor], Dict[str, Room]]:
    """Fallback helper to reconstruct hierarchy when loader returns legacy tuple."""
    portfolio = Portfolio(
        id="dummy_portfolio",
        name="Dummy Sample Portfolio",
        type=SpatialEntityType.PORTFOLIO,
    )

    buildings: Dict[str, Building] = {}
    floors: Dict[str, Floor] = {}
    rooms: Dict[str, Room] = {}

    for entity_id, entity in entities.items():
        if isinstance(entity, Building):
            buildings[entity_id] = entity
        elif isinstance(entity, Floor):
            floors[entity_id] = entity
        elif isinstance(entity, Room):
            rooms[entity_id] = entity

    for building_id, building in buildings.items():
        portfolio.add_building(building_id)
        if portfolio.id not in building.parent_ids:
            building.parent_ids.append(portfolio.id)

    for floor in floors.values():
        if floor.building_id and floor.building_id in buildings:
            buildings[floor.building_id].add_floor(floor.id)
            if floor.building_id not in floor.parent_ids:
                floor.parent_ids.append(floor.building_id)

    for room in rooms.values():
        if room.floor_id and room.floor_id in floors:
            floors[room.floor_id].add_room(room.id)
            if room.floor_id not in room.parent_ids:
                room.parent_ids.append(room.floor_id)
        elif room.building_id and room.building_id in buildings:
            buildings[room.building_id].add_room(room.id)
            if room.building_id not in room.parent_ids:
                room.parent_ids.append(room.building_id)

    return portfolio, buildings, floors, rooms


def attach_sensors_and_series(
    entities: Dict[str, SpatialEntity],
    metering_points,
    timeseries,
) -> None:
    """Fallback helper for attaching sensors when loader returns legacy tuple."""
    for point in metering_points.values():
        target_entity = entities.get(point.spatial_entity_id)
        if not isinstance(target_entity, Room):
            continue

        ts_objects = [timeseries[ts_id] for ts_id in point.timeseries_ids if ts_id in timeseries]
        csv_file = ts_objects[0].metadata.get("csv_file") if ts_objects else None

        sensor = SensorDefinition(
            id=f"sensor::{point.id}",
            spatial_entity_id=target_entity.id,
            metric=point.metric,
            parameter=point.metric.value or point.parameter or point.id,
            unit=point.unit or "",
            name=point.name,
            metadata={"source_point_id": point.id},
        )

        source_kwargs = {"file": csv_file} if csv_file else {}
        target_entity.load_sensor(
            sensor,
            source_type=SensorSourceType.CSV,
            **source_kwargs,
        )

        for ts in ts_objects:
            timestamps = ts.metadata.get("timestamps", [])
            values = ts.metadata.get("values", [])
            if not timestamps or not values:
                continue

            csv_column = ts.metadata.get("csv_column") or point.metric.value
            sensor.metadata.setdefault("timeseries", {})[ts.id] = {
                "timestamps": timestamps,
                "values": values,
                "point_id": point.id,
                "timeseries_id": ts.id,
                "label": csv_column,
            }
            target_entity.add_timeseries(csv_column, values, timestamps)


def run_room_standards_and_simulations(
    rooms: Dict[str, Room],
    buildings: Dict[str, Building],
    floors: Dict[str, Floor],
    portfolio: Portfolio,
    entity_lookup: Callable[[str], SpatialEntity | None],
) -> None:
    """Execute standards and simulations for each room using the new registry-based approach."""
    
    for room in rooms.values():
        if not room.timestamps:
            continue
        
        # Determine context from room's parent building
        country = None
        region = None
        building_type = None
        
        if room.building_id and room.building_id in buildings:
            building = buildings[room.building_id]
            country = building.country
            region = building.metadata.get('region')
            building_type = building.building_type
        
        # Compute all applicable standards
        # Room can now access outdoor_temperature from parent entities via entity_lookup
        room.compute_standards(
            country=country,
            region=region,
            building_type=building_type,
            season="winter",
            force_recompute=True,
            entity_lookup=entity_lookup,  # Enable hierarchy traversal
        )
        
        # Compute all applicable simulations
        room.compute_simulations(force_recompute=True)


def get_outdoor_temperature_series(room: Room, buildings: Dict[str, Building]) -> Optional[list[float]]:
    """Return the outdoor temperature series for the room's building (if available)."""
    if not room.building_id or room.building_id not in buildings:
        return None

    building = buildings[room.building_id]
    sensor_group = building.sensor_groups.get(MetricType.OUTDOOR_TEMPERATURE.value)
    if sensor_group:
        for sensor in sensor_group.sensors:
            ts_payloads = sensor.metadata.get("timeseries", {})
            if ts_payloads:
                first_ts = next(iter(ts_payloads.values()))
                values = first_ts.get("values")
                if values:
                    return list(values)

    climate_data = building.metadata.get("climate_timeseries", {})
    possible_keys = {
        MetricType.OUTDOOR_TEMPERATURE.value,
        "outdoor_temperature",
        "temperature",
    }
    for key in possible_keys:
        outdoor_series = climate_data.get(key)
        if outdoor_series and outdoor_series.get("values"):
            return list(outdoor_series.get("values"))
    return None

def print_portfolio_summary(
    portfolio: Portfolio,
    portfolio_metrics: Dict[str, object],
    building_metrics: Dict[str, Dict[str, object]],
    floor_metrics: Dict[str, Dict[str, object]],
    rooms: Iterable[Room],
    buildings: Dict[str, Building],
) -> None:
    """Log a concise overview of the hierarchy and computed analytics."""
    rooms_with_data = sum(1 for room in rooms if room.has_data)
    print("\n=== Portfolio Hierarchy Loaded ===")
    print(f"Portfolio: {portfolio.name} ({portfolio.id})")
    print(f"Buildings: {len(building_metrics)}")
    print(f"Floors:    {len(floor_metrics)}")
    print(f"Rooms:     {rooms_with_data} with telemetry\n")

    print("\n=== Room-Level Example ===")
    for room in rooms:
        if not room.has_data:
            continue
        
        # Get results from new compute_standards approach
        standards_results = room.computed_metrics.get('standards_results', {})
        simulation_results = room.computed_metrics.get('simulation_results', {})
        
        en16798_summary = standards_results.get('en16798_1', {})
        tail_summary = standards_results.get('tail', {})
        occupancy_summary = simulation_results.get('occupancy', {})
        
        print(f"- {room.name} ({room.id})")
        print(f"  EN16798 achieved category: {en16798_summary.get('achieved_category', 'n/a')}")
        print(f"  TAIL overall rating: {tail_summary.get('overall_rating_label', 'n/a')}")
        print(f"  Occupancy rate: {occupancy_summary.get('occupancy_rate', 'n/a')}")
        print(f"  Standards run: {list(standards_results.keys())}")
        print(f"  Simulations run: {list(simulation_results.keys())}")
        break

    print("\n=== Building-Level Aggregation ===")
    for building_id, building in buildings.items():
        aggregated = building.computed_metrics.get('aggregated_sensors', {})
        if aggregated:
            print(f"\n{building_id} aggregated sensors:")
            for param, stats in aggregated.items():
                if isinstance(stats, dict):
                    mean_val = stats.get('mean', 'n/a')
                    min_val = stats.get('min', 'n/a')
                    max_val = stats.get('max', 'n/a')
                    print(f"  {param}: mean={mean_val:.2f}, min={min_val:.2f}, max={max_val:.2f}" if isinstance(mean_val, (int, float)) else f"  {param}: {stats}")
        
        metrics = building_metrics.get(building_id, {})
        if isinstance(metrics, dict):
            en16798_summary = metrics.get('en16798_1', {})
            tail_summary = metrics.get('tail', {})
            
            print(f"{building_id}:")
            print(f"  EN16798 achieved category: {en16798_summary.get('achieved_category', 'n/a')}")
            print(f"  TAIL overall rating: {tail_summary.get('overall_rating_label', 'n/a')}")
        break

    print("\n=== Portfolio-Level Aggregation ===")
    portfolio_aggregated = portfolio.computed_metrics.get('aggregated_sensors', {})
    if portfolio_aggregated:
        print(f"\nPortfolio aggregated sensors:")
        for param, stats in portfolio_aggregated.items():
            if isinstance(stats, dict):
                mean_val = stats.get('mean', 'n/a')
                min_val = stats.get('min', 'n/a')
                max_val = stats.get('max', 'n/a')
                print(f"  {param}: mean={mean_val:.2f}, min={min_val:.2f}, max={max_val:.2f}" if isinstance(mean_val, (int, float)) else f"  {param}: {stats}")
    
    if isinstance(portfolio_metrics, dict):
        en16798_summary = portfolio_metrics.get('en16798_1', {})
        tail_summary = portfolio_metrics.get('tail', {})
        
        print(f"\nPortfolio standards:")
        print(f"  EN16798 achieved category: {en16798_summary.get('achieved_category', 'n/a')}")
        print(f"  TAIL overall rating: {tail_summary.get('overall_rating_label', 'n/a')}")


if __name__ == "__main__":
    main()
