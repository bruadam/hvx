# Hierarchy Sensor Access

## Overview

Each `SpatialEntity` in the building hierarchy is now aware of sensor parameters from its entire hierarchy tree - including parents, grandparents, children, and grandchildren. This enables sophisticated analyses that require data from multiple levels of the hierarchy.

## Key Concepts

### Hierarchy Structure
```
Portfolio (outdoor weather station, climate data)
  └── Building (outdoor temperature, energy meters)
      └── Floor (floor-level sensors)
          └── Room (indoor sensors: temperature, CO2, humidity)
              └── Zone (zone-level sensors)
```

### Use Cases

1. **Room Analysis with Building Context**
   - Room needs indoor temperature (from itself) + outdoor temperature (from building/portfolio)
   - Enables adaptive comfort calculations, thermal modeling, etc.

2. **Building Analysis from Room Data**
   - Building aggregates indoor conditions from all child rooms
   - Enables whole-building performance assessment

3. **Cross-Level Data Requirements**
   - Standards like EN16798 may need outdoor temp for adaptive comfort
   - Energy models may need weather data from portfolio level
   - Occupancy patterns from rooms inform building-level ventilation

## API Methods

### 1. `get_sensor_data()`

Get sensor data from the entity or its hierarchy.

```python
def get_sensor_data(
    self,
    parameter: str,
    search_parents: bool = True,
    search_children: bool = False,
    parent_lookup: Optional[Callable[[str], SpatialEntity]] = None,
    child_lookup: Optional[Callable[[str], SpatialEntity]] = None,
) -> Optional[SensorGroup]:
    """
    Get sensor data for a parameter from this entity or its hierarchy.
    
    Args:
        parameter: Parameter name (e.g., 'temperature', 'outdoor_temperature')
        search_parents: If True, search up the hierarchy
        search_children: If True, search down the hierarchy
        parent_lookup: Function to retrieve parent entities by ID
        child_lookup: Function to retrieve child entities by ID
    
    Returns:
        SensorGroup if found, None otherwise
    """
```

**Examples:**

```python
# Get room's own temperature sensor
temp_sensor = room.get_sensor_data('temperature')

# Get outdoor temperature from parent building/portfolio
outdoor_sensor = room.get_sensor_data(
    'outdoor_temperature',
    search_parents=True,
    parent_lookup=entity_registry.get,
)

# Building gets average indoor temp from all child rooms
indoor_sensors = building.get_sensor_data(
    'temperature',
    search_children=True,
    child_lookup=entity_registry.get,
)
```

### 2. `get_timeseries_from_hierarchy()`

Convenience method to get actual timeseries values from the hierarchy.

```python
def get_timeseries_from_hierarchy(
    self,
    parameter: str,
    parent_lookup: Optional[Callable[[str], SpatialEntity]] = None,
    child_lookup: Optional[Callable[[str], SpatialEntity]] = None,
    prefer_parents: bool = True,
) -> Optional[List[float]]:
    """
    Get timeseries data for a parameter from anywhere in the hierarchy.
    
    Args:
        parameter: Parameter name
        parent_lookup: Function to retrieve parent entities
        child_lookup: Function to retrieve child entities
        prefer_parents: Search parents first (True) or children first (False)
    
    Returns:
        List of timeseries values if found, None otherwise
    """
```

**Examples:**

```python
# Room gets outdoor temperature from portfolio weather station
outdoor_temp = room.get_timeseries_from_hierarchy(
    'outdoor_temperature',
    parent_lookup=entity_registry.get,
    prefer_parents=True,
)

# Building gets indoor temperature (will find from first child room)
indoor_temp = building.get_timeseries_from_hierarchy(
    'temperature',
    child_lookup=entity_registry.get,
    prefer_parents=False,
)
```

### 3. `get_available_parameters()`

Discover all available sensor parameters across the hierarchy.

```python
def get_available_parameters(
    self,
    include_parents: bool = True,
    include_children: bool = True,
    parent_lookup: Optional[Callable[[str], SpatialEntity]] = None,
    child_lookup: Optional[Callable[[str], SpatialEntity]] = None,
) -> Dict[str, str]:
    """
    Get all available sensor parameters across the hierarchy.
    
    Returns:
        Dictionary mapping parameter names to entity IDs where found
    """
```

**Example:**

```python
# Discover all available sensors in room's hierarchy
available = room.get_available_parameters(
    parent_lookup=entity_registry.get,
    child_lookup=entity_registry.get,
)
# Result: {
#     'temperature': 'room_101',
#     'co2': 'room_101', 
#     'humidity': 'room_101',
#     'outdoor_temperature': 'building_1',
#     'wind_speed': 'portfolio_1',
# }
```

## Integration with Standards

The `compute_standards()` method now supports hierarchy traversal via an `entity_lookup` parameter:

```python
# Create entity lookup function
def entity_lookup(entity_id: str):
    entities = {
        portfolio.id: portfolio,
        **buildings,
        **floors,
        **rooms,
    }
    return entities.get(entity_id)

# Compute standards with hierarchy access
room.compute_standards(
    country='DK',
    season='winter',
    entity_lookup=entity_lookup,  # Enables automatic outdoor_temperature lookup
    force_recompute=True,
)
```

When `entity_lookup` is provided:
- Room automatically searches for `outdoor_temperature` in parent entities
- Standards like EN16798 can use adaptive comfort models
- No need to manually pass outdoor_temperature parameter

## Complete Example

See `examples/hierarchy_sensor_access_example.py` for a full demonstration:

```python
# Setup hierarchy
portfolio → building → floor → room

# Add sensors at different levels
building.load_sensor(outdoor_temperature_sensor)  # Building level
room.load_sensor(indoor_temperature_sensor)       # Room level
room.load_sensor(co2_sensor)                      # Room level

# Room accesses outdoor temp from building
outdoor_values = room.get_timeseries_from_hierarchy(
    'outdoor_temperature',
    parent_lookup=entity_lookup,
    prefer_parents=True,
)

# Building accesses indoor sensors from rooms  
indoor_values = building.get_timeseries_from_hierarchy(
    'temperature',
    child_lookup=entity_lookup,
    prefer_parents=False,
)
```

## Implementation Details

### Entity Lookup Function

Most methods require an `entity_lookup` function to traverse the hierarchy. This function should:

1. Accept an entity ID (string)
2. Return the corresponding `SpatialEntity` object or `None`
3. Have access to all entities in the hierarchy

**Example Implementation:**

```python
def create_entity_lookup(portfolio, buildings, floors, rooms):
    """Create a lookup function for all entities."""
    def lookup(entity_id: str):
        # Check portfolio
        if entity_id == portfolio.id:
            return portfolio
        # Check buildings
        if entity_id in buildings:
            return buildings[entity_id]
        # Check floors
        if entity_id in floors:
            return floors[entity_id]
        # Check rooms
        if entity_id in rooms:
            return rooms[entity_id]
        return None
    return lookup
```

### Recursive Search

The hierarchy traversal uses recursive algorithms:
- **Parent search**: Searches current → parent → grandparent → ...
- **Child search**: Searches current → children → grandchildren → ...
- **Stops at first match** to avoid unnecessary traversal

### Performance Considerations

1. **Caching**: Sensor lookups are not cached - consider caching results if called repeatedly
2. **Depth**: Hierarchy traversal can be deep - ensure your entity structure is reasonable
3. **Circular References**: The implementation assumes a proper tree structure (no circular parent/child relationships)

## Benefits

✅ **Automatic Data Discovery**: Standards can find required data without manual parameter passing  
✅ **Flexible Analysis**: Mix data from any level of hierarchy  
✅ **Clear Semantics**: Explicit `search_parents` and `search_children` parameters  
✅ **Backward Compatible**: Existing code without `entity_lookup` still works  
✅ **Type Safe**: Returns properly typed `SensorGroup` objects  

## Migration Guide

### Before (Manual Outdoor Temperature Lookup)

```python
# Old approach - manual outdoor temperature retrieval
outdoor_temp = None
if room.building_id and room.building_id in buildings:
    building = buildings[room.building_id]
    outdoor_temp = get_outdoor_temperature_series(building)

room.compute_standards(
    country='DK',
    outdoor_temperature=outdoor_temp,
)
```

### After (Automatic Hierarchy Traversal)

```python
# New approach - automatic via entity_lookup
room.compute_standards(
    country='DK',
    entity_lookup=lambda id: entity_registry.get(id),
)
# outdoor_temperature automatically found from parent building!
```

## See Also

- `examples/hierarchy_sensor_access_example.py` - Full working example
- `examples/dummy_portfolio_end_to_end.py` - Real-world usage in end-to-end pipeline
- `core/spacial_entity.py` - Implementation source code
