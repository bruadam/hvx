# Enhanced Spatial Entities

This document describes the enhanced implementations of Portfolio, Building, Floor, and Room entities in the refactored service.

## Overview

The refactored service provides four main spatial entity types with rich domain functionality:

- **Portfolio**: Collection of buildings with portfolio-wide aggregation
- **Building**: Individual building with energy metrics, EPC rating, and system properties
- **Floor**: Single floor/level within a building with room aggregation
- **Room**: Individual space with time series data and self-analysis capabilities

All entities inherit from `SpatialEntity` and follow a hierarchical structure:
```
Portfolio → Building → Floor → Room
```

## Key Features

### 1. Hierarchy Management

Each entity type manages its relationships in the hierarchy:

```python
# Portfolio
portfolio.add_building(building_id)
portfolio.building_count  # Number of buildings
portfolio.building_ids    # List of building IDs

# Building
building.add_floor(floor_id)
building.add_room(room_id)  # Direct room without floor
building.floor_count
building.room_count

# Floor
floor.add_room(room_id)
floor.room_count

# Room (leaf node, no children)
room.floor_id
room.building_id
```

### 2. Property Aggregation

Entities can compute aggregated metrics from their children:

```python
# Portfolio aggregates from buildings
portfolio_metrics = portfolio.compute_metrics(
    building_lookup=lambda id: buildings_dict[id]
)
# Returns: total_area_m2, total_energy_kwh, energy_intensity, etc.

# Building can compute energy metrics
building_metrics = building.compute_metrics(metrics=['energy', 'epc'])
# Returns: total_energy_kwh, energy_intensity, primary_energy_kwh_m2, etc.

# Floor aggregates from rooms
floor_metrics = floor.compute_metrics(
    room_lookup=lambda id: rooms_dict[id]
)
# Returns: total_area_m2, average_compliance_rate, tail_ratings, etc.

# Room can compute statistics from time series
room_metrics = room.compute_metrics()
# Returns: temperature_mean, co2_mean, humidity_mean, etc.
```

### 3. Caching

All computed metrics are cached to avoid redundant calculations:

```python
# First call computes
metrics = building.compute_metrics()

# Subsequent calls return cached results
metrics = building.compute_metrics()  # Fast, from cache

# Force recomputation
metrics = building.compute_metrics(force_recompute=True)
```

### 4. Summaries

Each entity provides a structured summary:

```python
summary = entity.get_summary()
# Returns dict with entity-specific information
```

## Entity-Specific Features

### Portfolio

**Properties:**
- `building_ids`: List of building IDs
- `building_count`: Number of buildings

**Methods:**
- `add_building(building_id)`: Add a building
- `remove_building(building_id)`: Remove a building
- `compute_metrics(building_lookup, force_recompute)`: Aggregate portfolio metrics

**Computed Metrics:**
- `total_area_m2`: Total floor area across all buildings
- `total_energy_kwh`: Total energy consumption
- `energy_intensity_kwh_m2`: Portfolio-wide energy intensity
- `total_rooms`: Total number of rooms
- `average_compliance_rate`: Average compliance across buildings
- `average_tail_rating`: Average TAIL rating

### Building

**Properties:**
- `year_built`: Construction year
- `address`, `city`, `latitude`, `longitude`: Location
- `hvac_system`, `heating_system`: Building systems
- `annual_heating_kwh`, `annual_cooling_kwh`, `annual_electricity_kwh`: Energy consumption
- `annual_water_m3`: Water consumption
- `annual_solar_pv_kwh`, `annual_renewable_kwh`: Renewable energy
- `epc_rating`: Energy Performance Certificate rating
- `floor_ids`, `room_ids`: Child entity IDs

**Methods:**
- `add_floor(floor_id)`: Add a floor
- `add_room(room_id)`: Add a room (without floor)
- `calculate_primary_energy_per_m2()`: Calculate primary energy intensity
- `get_energy_summary()`: Get detailed energy breakdown
- `compute_metrics(metrics, force_recompute)`: Compute building metrics

**Computed Metrics:**
- `total_energy_kwh`: Total annual energy consumption
- `energy_intensity`: Energy per m²
- `primary_energy_kwh_m2`: Primary energy intensity
- `energy_summary`: Detailed energy breakdown

### Floor

**Properties:**
- `floor_number`: Floor number (0=ground, negative=basement)
- `building_id`: Parent building ID
- `room_ids`: Child room IDs

**Methods:**
- `add_room(room_id)`: Add a room to this floor
- `remove_room(room_id)`: Remove a room
- `compute_metrics(room_lookup, force_recompute)`: Aggregate from rooms

**Computed Metrics:**
- `total_area_m2`: Total floor area
- `average_compliance_rate`: Average compliance from rooms
- `average_tail_rating`: Average TAIL rating from rooms
- `en16798_category_distribution`: Distribution of EN16798 categories

### Room

**Properties:**
- `floor_id`, `building_id`: Parent entity IDs
- `activity_level`, `pollution_level`: Room-specific metadata
- `glass_to_wall_ratio`, `last_renovation_year`: Physical properties
- `timeseries_data`: Dict of metric_name → values
- `timestamps`: Timestamp list for time series data

**Methods:**
- `add_timeseries(metric_name, values, timestamps)`: Add time series data
- `get_timeseries(metric_name)`: Get time series values
- `compute_metrics(analyses, force_recompute)`: Compute room statistics

**Properties:**
- `has_data`: Boolean indicating if time series data is available
- `available_metrics`: List of metric names with data

**Computed Metrics:**
- `{metric}_mean`: Mean value for each metric
- `{metric}_min`: Minimum value
- `{metric}_max`: Maximum value

## Usage Example

```python
from core.models import Portfolio, Building, Floor, Room, VentilationType

# Create portfolio
portfolio = Portfolio(
    id="p1",
    name="My Portfolio",
    country="Denmark"
)

# Create building
building = Building(
    id="b1",
    name="Office Building",
    building_type="office",
    area_m2=5000.0,
    year_built=2015,
    ventilation_type=VentilationType.MECHANICAL,
    annual_heating_kwh=150000.0,
    annual_electricity_kwh=200000.0,
)

# Add to portfolio
portfolio.add_building(building.id)

# Create floor
floor = Floor(
    id="f1",
    name="Ground Floor",
    floor_number=0,
    building_id=building.id,
    area_m2=1250.0,
)

building.add_floor(floor.id)

# Create room
room = Room(
    id="r1",
    name="Conference Room A",
    room_type="meeting_room",
    floor_id=floor.id,
    building_id=building.id,
    area_m2=50.0,
    volume_m3=150.0,
    design_occupancy=12,
)

floor.add_room(room.id)

# Add time series data
room.add_timeseries(
    "temperature",
    [21.5, 22.0, 21.8, 22.2],
    ["2024-01-01 12:00:00", "2024-01-02 12:00:00", "2024-01-03 12:00:00", "2024-01-04 12:00:00"]
)

# Compute metrics
room_metrics = room.compute_metrics()
print(f"Temperature mean: {room_metrics['temperature_mean']:.1f}°C")

building_metrics = building.compute_metrics(metrics=['energy'])
print(f"Energy intensity: {building_metrics['energy_intensity']:.1f} kWh/m²")

# Get summaries
print(building.get_summary())
print(room.get_summary())
```

## Integration with Standards

The enhanced entities work seamlessly with the standards modules:

```python
from ingestion.csv import load_from_csv
from standards.en16798_1 import analysis as en16798
from standards.tail import analysis as tail

# Load data using CSV ingestion
entities, points, ts = load_from_csv(
    'data.csv',
    format='wide',
    spatial_entity_id='room_1',
    spatial_entity_name='Meeting Room',
    entity_type=SpatialEntityType.ROOM,
    area_m2=50.0,
    volume_m3=150.0,
)

# Get entity (returns enhanced Room instance)
room = list(entities.values())[0]

# Run standards analysis
en_result = en16798.run(
    spatial_entity=room,
    timeseries_dict={'temperature': temp_values, 'co2': co2_values},
    timestamps=timestamps,
    season='winter'
)

tail_result = tail.run(
    spatial_entity=room,
    timeseries_dict={'temperature': temp_values, 'co2': co2_values, 'humidity': humidity_values},
    timestamps=timestamps
)

# Results are automatically cached in room.computed_metrics
print(room.computed_metrics)
```

## Comparison with Core Models

The refactored enhanced entities include all functionality from the core implementation:

| Feature | Core | Refactored |
|---------|------|------------|
| Hierarchy management | ✓ | ✓ |
| Property aggregation | ✓ | ✓ |
| Energy calculations | ✓ | ✓ |
| Metric caching | ✓ | ✓ |
| Self-analysis | ✓ | ✓ |
| Standards integration | Limited | Full |
| Time series support | pandas DataFrame | Dict-based |
| Pydantic validation | ✓ | ✓ |

## Migration from Core

If migrating from core entities to refactored entities:

1. **Import change:**
   ```python
   # Old
   from core.domain.models.entities import Building, Room

   # New
   from refactored_service.core.models import Building, Room
   ```

2. **Time series data:**
   ```python
   # Old (pandas DataFrame)
   room.time_series_data = df

   # New (dict-based)
   room.add_timeseries("temperature", temp_values, timestamps)
   room.add_timeseries("co2", co2_values)
   ```

3. **Computed metrics:**
   ```python
   # Both use same pattern
   metrics = entity.compute_metrics()
   value = entity.computed_metrics['metric_name']
   ```

## See Also

- [Ingestion README](../../ingestion/README.md) - How to load data into entities
- [EN16798-1 README](../../standards/en16798-1/README.md) - EN16798 standard analysis
- [TAIL README](../../standards/tail/README.md) - TAIL rating analysis
- [Enhanced Entities Demo](../../examples/enhanced_entities_demo.py) - Complete example
