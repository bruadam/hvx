# Building Type Configuration System

This directory contains YAML configuration files for building types used in IEQ analysis.

## Overview

The building type configuration system allows you to:
- Define typical occupancy hours per building type
- Specify default parameters to monitor
- Mark building types as supported or experimental
- Override defaults with custom configurations
- Add new building types without code changes

## Configuration Files

### `default_building_types.yaml`

Default configuration shipped with the system. Contains standard building types:
- Office
- Hotel
- School
- Residential
- Hospital
- Retail
- Laboratory
- Industrial
- Mixed Use
- Other

**Do not modify this file.** It may be overwritten during updates.

### `user_building_types_example.yaml`

Example of user-defined configuration showing how to:
- Override default building type settings
- Add custom building types (co-working, data center, museum, etc.)
- Customize occupancy hours for your region/use case

Copy and modify this file to create your custom configuration.

## Configuration Format

```yaml
building_type_id:
  display_name: "Human-readable Name"
  typical_occupancy_hours:
    start: 8   # Hour in 24h format (0-23)
    end: 18    # Hour in 24h format (0-23)
  description: "Brief description of building type"
  supported: true   # Whether fully supported by the system
  default_parameters:
    - temperature
    - co2
    - humidity
    - illuminance
    - noise
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `display_name` | string | Human-readable name shown in UI/reports |
| `typical_occupancy_hours.start` | integer (0-23) | Typical start hour in 24h format |
| `typical_occupancy_hours.end` | integer (0-24) | Typical end hour in 24h format |
| `description` | string | Brief description of building type |
| `supported` | boolean | Whether this type is fully supported |
| `default_parameters` | list[string] | Default IEQ parameters to monitor |

### Special Cases

**24/7 Facilities** (hospitals, hotels, residential):
```yaml
typical_occupancy_hours:
  start: 0
  end: 24
```

## Usage Examples

### 1. Using Default Configuration

```python
from core.domain.enums.building_type import BuildingType

# Access occupancy hours
office = BuildingType.OFFICE
start, end = office.typical_occupancy_hours
# Returns: (8, 18)

# Check if 24/7 facility
hotel = BuildingType.HOTEL
is_always_occupied = hotel.is_24_7
# Returns: True

# Get default parameters
params = office.default_parameters
# Returns: ['temperature', 'co2', 'humidity', 'illuminance', 'noise']
```

### 2. Loading User Configuration

```python
from pathlib import Path
from core.domain.enums.building_type_config import building_type_config_loader

# Load your custom config
user_config = Path("config/building_types/my_custom_types.yaml")
building_type_config_loader.load_user_config(user_config)

# Now BuildingType will use your custom settings
office = BuildingType.OFFICE
start, end = office.typical_occupancy_hours
# Returns your custom hours if overridden
```

### 3. Creating Custom Building Types

Create `my_custom_types.yaml`:

```yaml
# Add new custom type
coworking:
  display_name: "Co-working Space"
  typical_occupancy_hours:
    start: 7
    end: 22
  description: "Flexible co-working space"
  supported: true
  default_parameters:
    - temperature
    - co2
    - humidity
    - noise

# Override existing type
office:
  display_name: "Extended Hours Office"
  typical_occupancy_hours:
    start: 7
    end: 20  # Extended hours
  description: "Office with extended operating hours"
  supported: true
  default_parameters:
    - temperature
    - co2
    - humidity
    - illuminance
    - noise
```

Then load it:

```python
building_type_config_loader.load_user_config(Path("my_custom_types.yaml"))
```

### 4. Programmatic Access

```python
from core.domain.enums.building_type_config import building_type_config_loader

# Get config for any building type
config = building_type_config_loader.get_config("office")

# Access properties
print(config.display_name)
print(config.occupancy_hours_tuple)
print(config.is_24_7)
print(config.default_parameters)

# List all building types
all_types = building_type_config_loader.get_all_building_types()

# List only supported types
supported = building_type_config_loader.get_supported_building_types()
```

## Integration with Analysis Pipeline

The occupancy hours are automatically used in:

1. **Data filtering** - Focus analysis on occupied hours
2. **Compliance calculation** - EN 16798-1 requires % of occupied time
3. **Aggregation** - Occupant-weighted spatial aggregation
4. **Reporting** - Show results per occupied hour

Example in analysis workflow:

```python
from core.domain.models.building import Building
from core.domain.enums.building_type import BuildingType

# Create building
building = Building(
    id="office_001",
    name="Main Office",
    building_type=BuildingType.OFFICE
)

# Get occupancy hours for filtering
start_hour, end_hour = building.building_type.typical_occupancy_hours

# Use in data filtering
occupied_data = data[
    (data['hour'] >= start_hour) & 
    (data['hour'] < end_hour)
]

# Calculate compliance during occupied hours only
compliance_rate = calculate_compliance(occupied_data)
```

## Regional Customization

Different regions may have different typical hours. Create region-specific configs:

**EU Office Configuration** (`config_eu.yaml`):
```yaml
office:
  typical_occupancy_hours:
    start: 8
    end: 17  # EU typical 9-5 = 8-17 in 24h
```

**US Office Configuration** (`config_us.yaml`):
```yaml
office:
  typical_occupancy_hours:
    start: 8
    end: 18  # US typical 9-6 = 8-18 in 24h
```

**Asia Office Configuration** (`config_asia.yaml`):
```yaml
office:
  typical_occupancy_hours:
    start: 8
    end: 20  # Extended hours common in Asia
```

## Best Practices

1. **Don't modify `default_building_types.yaml`**
   - Create a separate user config file instead
   - Allows you to update the system without losing customizations

2. **Use descriptive IDs**
   - Use lowercase with underscores: `coworking_space`
   - Keep IDs short but clear

3. **Document your custom types**
   - Add meaningful descriptions
   - Explain why custom hours are needed

4. **Version control your custom configs**
   - Keep user config files in version control
   - Document changes with commit messages

5. **Validate occupancy hours**
   - Start hour: 0-23
   - End hour: 1-24 (24 means end of day)
   - End > Start (except for 24/7: start=0, end=24)

6. **Choose appropriate parameters**
   - Consider building type requirements
   - Include minimum: temperature, co2, humidity
   - Add type-specific (e.g., radon for residential)

## Troubleshooting

### Config file not loading

```python
# Check if file exists
from pathlib import Path
config_path = Path("my_config.yaml")
print(f"File exists: {config_path.exists()}")

# Check for YAML syntax errors
import yaml
with open(config_path) as f:
    data = yaml.safe_load(f)
    print(data)
```

### Custom building type not recognized

Custom types are not added to the `BuildingType` enum automatically. Access via config loader:

```python
# Won't work - custom types not in enum
bt = BuildingType("coworking")  # Error!

# Use config loader instead
config = building_type_config_loader.get_config("coworking")
hours = config.occupancy_hours_tuple
```

### Hours not updating after config load

Config is cached. Reload if needed:

```python
# Reload default config
building_type_config_loader.reload_configs()

# Load user config again
building_type_config_loader.load_user_config(user_config_path)
```

## Migration from Hardcoded Values

If you have existing code with hardcoded hours:

**Before:**
```python
if building_type == "office":
    start_hour = 8
    end_hour = 18
```

**After:**
```python
from core.domain.enums.building_type import BuildingType

building_type = BuildingType.OFFICE
start_hour, end_hour = building_type.typical_occupancy_hours
```

## See Also

- `examples/demo_building_type_config.py` - Complete demonstration
- `docs/ARCHITECTURE.md` - System architecture overview
- `core/domain/enums/building_type.py` - BuildingType enum implementation
- `core/domain/enums/building_type_config.py` - Config loader implementation
