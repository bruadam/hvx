#!/usr/bin/env python
"""
Example: Hierarchy Sensor Access

Demonstrates how SpatialEntity can access sensor data from anywhere
in the hierarchy (parents, grandparents, children, grandchildren).
"""

from core.entities import Portfolio, Building, Floor, Room
from core.enums import MetricType, SpatialEntityType
from core.metering import SensorDefinition

# Create a simple hierarchy
portfolio = Portfolio(
    id="portfolio_1",
    name="Example Portfolio",
    type=SpatialEntityType.PORTFOLIO,
)

building = Building(
    id="building_1",
    name="Office Building A",
    type=SpatialEntityType.BUILDING,
    country="DK",
)

floor = Floor(
    id="floor_1",
    name="Level 1",
    type=SpatialEntityType.FLOOR,
    building_id="building_1",
    floor_number=1,
)

room = Room(
    id="room_101",
    name="Room 101",
    type=SpatialEntityType.ROOM,
    floor_id="floor_1",
    building_id="building_1",
    room_type="office",
)

# Link hierarchy
portfolio.add_building("building_1")
building.parent_ids.append("portfolio_1")

building.add_floor("floor_1")
floor.parent_ids.append("building_1")

floor.add_room("room_101")
room.parent_ids.append("floor_1")

# Add outdoor temperature sensor to building (like a weather station)
outdoor_sensor = SensorDefinition(
    id="sensor_outdoor_temp",
    spatial_entity_id="building_1",
    metric=MetricType.OUTDOOR_TEMPERATURE,
    parameter="outdoor_temperature",
    unit="°C",
    name="Outdoor Temperature Sensor",
)
outdoor_sensor.metadata["timeseries"] = {
    "ts_1": {
        "values": [10.0, 11.0, 12.0, 11.5, 10.5] * 100,  # 500 points
        "timestamps": [f"2024-01-01T{i:02d}:00:00" for i in range(500)],
    }
}
building.load_sensor(outdoor_sensor)

# Add indoor temperature sensor to room
indoor_sensor = SensorDefinition(
    id="sensor_indoor_temp",
    spatial_entity_id="room_101",
    metric=MetricType.TEMPERATURE,
    parameter="temperature",
    unit="°C",
    name="Indoor Temperature Sensor",
)
indoor_sensor.metadata["timeseries"] = {
    "ts_2": {
        "values": [20.0, 21.0, 22.0, 21.5, 20.5] * 100,  # 500 points
        "timestamps": [f"2024-01-01T{i:02d}:00:00" for i in range(500)],
    }
}
room.load_sensor(indoor_sensor)

# Add CO2 sensor to room
co2_sensor = SensorDefinition(
    id="sensor_co2",
    spatial_entity_id="room_101",
    metric=MetricType.CO2,
    parameter="co2",
    unit="ppm",
    name="CO2 Sensor",
)
co2_sensor.metadata["timeseries"] = {
    "ts_3": {
        "values": [400.0, 500.0, 600.0, 550.0, 450.0] * 100,  # 500 points
        "timestamps": [f"2024-01-01T{i:02d}:00:00" for i in range(500)],
    }
}
room.load_sensor(co2_sensor)

# Create entity lookup function
def entity_lookup(entity_id: str):
    """Lookup function for hierarchy traversal."""
    entities = {
        "portfolio_1": portfolio,
        "building_1": building,
        "floor_1": floor,
        "room_101": room,
    }
    return entities.get(entity_id)


print("=" * 70)
print("HIERARCHY SENSOR ACCESS EXAMPLE")
print("=" * 70)

print("\n1. Room accessing its own sensors:")
print("-" * 70)
temp_sensor = room.get_sensor_data("temperature")
print(f"   temperature: {temp_sensor is not None} (from {room.id})")

co2_sensor_group = room.get_sensor_data("co2")
print(f"   co2: {co2_sensor_group is not None} (from {room.id})")

print("\n2. Room accessing parent building's outdoor temperature:")
print("-" * 70)
outdoor_sensor_group = room.get_sensor_data(
    "outdoor_temperature",
    search_parents=True,
    parent_lookup=entity_lookup,
)
print(f"   outdoor_temperature: {outdoor_sensor_group is not None}")
if outdoor_sensor_group:
    print(f"   Found in sensor group: {outdoor_sensor_group.parameter}")
    print(f"   Number of sensors: {len(outdoor_sensor_group.sensors)}")

print("\n3. Getting timeseries values from hierarchy:")
print("-" * 70)
indoor_values = room.get_timeseries_from_hierarchy(
    "temperature",
    parent_lookup=entity_lookup,
)
print(f"   Indoor temp values: {len(indoor_values) if indoor_values else 0} points")
if indoor_values:
    print(f"   Sample: {indoor_values[:5]}")

outdoor_values = room.get_timeseries_from_hierarchy(
    "outdoor_temperature",
    parent_lookup=entity_lookup,
    prefer_parents=True,
)
print(f"   Outdoor temp values: {len(outdoor_values) if outdoor_values else 0} points")
if outdoor_values:
    print(f"   Sample: {outdoor_values[:5]}")

print("\n4. Building accessing child room sensors:")
print("-" * 70)
indoor_from_building = building.get_sensor_data(
    "temperature",
    search_children=True,
    child_lookup=entity_lookup,
)
print(f"   temperature from children: {indoor_from_building is not None}")

co2_from_building = building.get_sensor_data(
    "co2",
    search_children=True,
    child_lookup=entity_lookup,
)
print(f"   co2 from children: {co2_from_building is not None}")

print("\n5. All available parameters in room's hierarchy:")
print("-" * 70)
available_params = room.get_available_parameters(
    include_parents=True,
    include_children=False,
    parent_lookup=entity_lookup,
)
for param, entity_id in available_params.items():
    print(f"   {param}: available in {entity_id}")

print("\n6. All available parameters in building's hierarchy:")
print("-" * 70)
building_params = building.get_available_parameters(
    include_parents=True,
    include_children=True,
    parent_lookup=entity_lookup,
    child_lookup=entity_lookup,
)
for param, entity_id in building_params.items():
    print(f"   {param}: available in {entity_id}")

print("\n" + "=" * 70)
print("DEMONSTRATION COMPLETE")
print("=" * 70)
print("\nKey Takeaways:")
print("- Rooms can access outdoor_temperature from parent buildings")
print("- Buildings can access indoor sensors from child rooms")
print("- Any entity can traverse up/down the hierarchy for sensor data")
print("- This enables complex analyses using data from multiple levels")
