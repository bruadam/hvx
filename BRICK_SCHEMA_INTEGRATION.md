# BrickSchema Integration - Complete ✓

## Summary

Successfully integrated **BrickSchema** ontology with the IEQ Analytics platform. This enables semantic modeling of buildings, rooms, HVAC systems, and energy consumption using industry-standard ontology.

## What Was Implemented

### 1. Core Infrastructure (`core/infrastructure/brick/`)

#### `BrickMapper` Class
The main mapper that converts domain models to Brick Schema RDF triples:

- **Building Mapping**: Maps `Building` models to Brick Building entities with:
  - Building types (Office, Residential, School, etc.)
  - Location data (coordinates, address)
  - Physical properties (area, year built)
  - HVAC systems
  - Ventilation systems
  - Heating systems

- **Room Mapping**: Maps `Room` models to Brick Room entities with:
  - Room properties (area, volume)
  - Parent-child relationships with buildings
  - Automatic sensor detection and mapping

- **Energy System Mapping**: Maps `EnergyConsumption` to Brick energy meters:
  - Heating thermal energy meters
  - Cooling thermal energy meters
  - Electrical energy meters
  - Renewable generation meters

#### `BrickNamespaceManager` Class
Manages all RDF namespaces:
- Brick Schema namespace
- RDF/RDFS/OWL namespaces
- QUDT units namespace
- Custom namespaces for building instances

### 2. Features

✓ **SPARQL Querying**: Query building models using SPARQL
✓ **Multiple Export Formats**: Turtle, RDF/XML, JSON-LD
✓ **Graph Validation**: Validate Brick models for consistency
✓ **Hierarchy Queries**: Get complete building hierarchies
✓ **Sensor Discovery**: Find sensors by type across buildings
✓ **Statistics**: Track graph size and entity counts

### 3. Examples

Created comprehensive examples:
- `examples/brick_schema_example.py`: Full featured example
- `test_brick_integration.py`: Quick verification test
- `docs/BRICK_INTEGRATION.md`: Complete usage documentation

## Installation

```bash
# Using uv (recommended)
uv pip install "brickschema[allegro]"

# Or using pip
pip install brickschema rdflib
```

Dependencies added to:
- `requirements.txt`
- `pyproject.toml`

## Quick Start

```python
from core.infrastructure.brick.mapper import BrickMapper
from core.domain.models.building import Building

# Initialize
mapper = BrickMapper()

# Create and map building
building = Building(id="bldg_001", name="My Building", ...)
building_uri = mapper.add_building(building)

# Query
results = mapper.query("""
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    SELECT ?room WHERE { ?room a brick:Room }
""")

# Export
mapper.export_to_turtle("building_model.ttl")
```

## Testing

All tests pass successfully:

```bash
$ python test_brick_integration.py
============================================================
[1] Initializing BrickMapper...
✓ Mapper initialized
  Graph size: 53816 triples

[2] Creating and mapping building...
✓ Building mapped

[3] Creating and mapping rooms...
✓ Room mapped

[4] Adding energy consumption...
✓ Added 3 energy meters

[5] Querying the graph...
✓ Found 8 entities

[6] Graph statistics...
  total_triples: 53844
  buildings: 1
  rooms: 1

[7] Exporting to Turtle format...
✓ Exported to: test_brick_model.ttl

✓ All tests passed! BrickSchema integration is working.
============================================================
```

## Mapped Entities

### Building Types
- Office Building
- Residential Building
- Education Building (School)
- Healthcare Building (Hospital)
- Retail Building
- Industrial Building

### HVAC Systems
- Variable Air Volume (VAV)
- Constant Air Volume (CAV)
- Radiant Heating/Cooling
- Fan Coil Units

### Ventilation Systems
- Natural Ventilation
- Mechanical Ventilation
- Mixed-Mode Ventilation

### Energy Meters
- Heating Thermal Energy Meter
- Cooling Thermal Energy Meter
- Electrical Energy Meter
- Solar Panel Energy Meter

### Sensors (Auto-detected from Room data)
- Temperature Sensor
- Humidity Sensor
- CO2 Level Sensor
- PM2.5 Sensor
- PM10 Sensor
- TVOC Sensor
- Illuminance Sensor

## Integration Points

The Brick mapper integrates seamlessly with existing IEQ Analytics components:

1. **Domain Models**: Direct mapping from `Building`, `Room`, `EnergyConsumption`
2. **Data Loaders**: Can be called after loading data from Excel/CSV
3. **Analysis Results**: Building models can include analysis results
4. **Reporting**: Export semantic models alongside reports

## Benefits

1. **Standardization**: Use industry-standard building ontology
2. **Interoperability**: Exchange data with other BMS systems
3. **Querying**: Powerful SPARQL queries over building data
4. **Integration**: Connect with semantic web technologies
5. **Documentation**: Self-documenting building structure
6. **Extensibility**: Easy to add custom properties and relationships

## Use Cases

### 1. Building Portfolio Management
```python
# Map entire portfolio
for building in portfolio.buildings:
    mapper.add_building(building)
    for room in building.rooms:
        mapper.add_room(room, building_uri)

# Query across portfolio
results = mapper.query("""
    SELECT ?building ?area WHERE {
        ?building a brick:Office_Building .
        ?building brick:area ?area .
        FILTER (?area > 1000)
    }
""")
```

### 2. Energy Analysis
```python
# Add energy consumption for multiple periods
for period in energy_periods:
    mapper.add_energy_consumption(building_uri, period)

# Query energy meters
results = mapper.query("""
    SELECT ?meter ?type WHERE {
        ?meter a ?type .
        FILTER(CONTAINS(STR(?type), "Energy_Meter"))
    }
""")
```

### 3. Sensor Network Mapping
```python
# Map all rooms with sensors
for room in rooms_with_data:
    mapper.add_room(room, building_uri)

# Find all CO2 sensors
co2_sensors = mapper.find_sensors_by_type("CO2_Level_Sensor")
```

### 4. Integration with Other Systems
```python
# Export to share with other systems
mapper.export_to_turtle("building_for_bms.ttl")
mapper.export_to_json_ld("building_for_web.jsonld")
```

## Files Created

```
core/infrastructure/brick/
├── __init__.py                    # Package initialization
├── namespace_manager.py           # RDF namespace management
└── mapper.py                      # Main Brick mapper (460 lines)

examples/
└── brick_schema_example.py        # Comprehensive example (250 lines)

docs/
└── BRICK_INTEGRATION.md           # Full documentation (400 lines)

test_brick_integration.py          # Integration test
BRICK_SCHEMA_INTEGRATION.md        # This summary
```

## Next Steps

1. **Load Real Data**: Map actual building data from your Excel files
2. **Custom Queries**: Create domain-specific SPARQL queries
3. **Visualization**: Connect with graph visualization tools
4. **Export**: Share models with building management systems
5. **Extend**: Add more Brick classes (air terminals, dampers, etc.)
6. **Validation**: Use Brick's SHACL validation for data quality

## Resources

- **BrickSchema Website**: https://brickschema.org/
- **Python Library**: https://github.com/BrickSchema/py-brickschema
- **Documentation**: `docs/BRICK_INTEGRATION.md`
- **Example**: `examples/brick_schema_example.py`
- **Brick Viewer**: https://viewer.brickschema.org/

## Notes

- The integration uses **brickschema 0.7.8** with Allegro support
- Brick Schema TTL loaded: **53,816 triples** (base ontology)
- All domain enums properly mapped to Brick classes
- SPARQL queries tested and working
- Multiple export formats supported

## Status: ✅ Complete and Tested

The BrickSchema integration is fully functional and ready for use!
