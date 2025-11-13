# BrickSchema Integration Guide

This guide explains how to use BrickSchema ontology with the IEQ Analytics platform to create semantic building models.

## Overview

[BrickSchema](https://brickschema.org/) is a standardized semantic ontology for buildings that provides:

- **Standardized vocabulary** for building components, systems, and sensors
- **Semantic relationships** between building entities
- **Interoperability** with other building management systems
- **SPARQL queries** for complex building data analysis
- **RDF export** for integration with semantic web technologies

## Installation

The BrickSchema dependencies are included in the standard requirements:

```bash
pip install -r requirements.txt
# or
pip install brickschema>=0.6.0 rdflib>=7.0.0
```

## Quick Start

```python
from core.domain.models.building import Building
from core.domain.models.room import Room
from core.infrastructure.brick.mapper import BrickMapper

# Initialize mapper
mapper = BrickMapper()

# Create and map a building
building = Building(
    id="building_001",
    name="Office Building",
    building_type=BuildingType.OFFICE,
    total_area=1000.0
)
building_uri = mapper.add_building(building)

# Create and map rooms
room = Room(id="room_101", name="Conference Room", area=50.0)
room_uri = mapper.add_room(room, building_uri)

# Export to Turtle format
mapper.export_to_turtle("building_model.ttl")
```

## Features

### 1. Building Mapping

Maps your domain `Building` model to Brick entities:

```python
building_uri = mapper.add_building(building)
```

**Mapped properties:**
- Building type (Office, Residential, School, etc.)
- Location (address, coordinates)
- Area
- HVAC system
- Ventilation system
- Heating system

### 2. Room/Space Mapping

Maps `Room` entities with automatic sensor detection:

```python
room_uri = mapper.add_room(room, building_uri)
```

**Automatically creates Brick sensors for:**
- Temperature sensors
- Humidity sensors
- CO2 sensors
- PM2.5 and PM10 sensors
- TVOC sensors
- Illuminance sensors

### 3. Energy System Mapping

Maps `EnergyConsumption` data to Brick energy meters:

```python
meters = mapper.add_energy_consumption(building_uri, energy_data)
```

**Creates meters for:**
- Heating energy
- Cooling energy
- Electricity consumption
- Hot water
- Ventilation
- Renewable generation (solar PV, etc.)

### 4. SPARQL Queries

Query your building model using SPARQL:

```python
# Find all temperature sensors
query = """
PREFIX brick: <https://brickschema.org/schema/Brick#>

SELECT ?sensor ?room WHERE {
    ?sensor a brick:Temperature_Sensor .
    ?sensor brick:isPointOf ?room .
}
"""
results = mapper.query(query)
```

### 5. Export Formats

Export your building model to multiple RDF formats:

```python
# Turtle (human-readable)
mapper.export_to_turtle("building.ttl")

# RDF/XML
mapper.export_to_rdf("building.rdf")

# JSON-LD (JSON-based)
mapper.export_to_json_ld("building.jsonld")
```

## Usage Examples

### Example 1: Create Complete Building Model

```python
from datetime import datetime, timedelta
from core.infrastructure.brick.mapper import BrickMapper

# Initialize
mapper = BrickMapper(base_namespace="https://mycompany.com/buildings/")

# Create building
building = Building(
    id="hq_001",
    name="Headquarters",
    building_type=BuildingType.OFFICE,
    total_area=5000.0,
    hvac_system=HVACType.VAV,
    ventilation_type=VentilationType.BALANCED,
    latitude=50.8503,
    longitude=4.3517
)
building_uri = mapper.add_building(building)

# Add rooms
rooms = [
    Room(id="room_101", name="Conference A", area=50.0),
    Room(id="room_102", name="Office Floor 1", area=200.0),
]

for room in rooms:
    mapper.add_room(room, building_uri)

# Add energy data
energy = EnergyConsumption(
    measurement_start=datetime.now() - timedelta(days=365),
    measurement_end=datetime.now(),
    heating_kwh=150000.0,
    electricity_kwh=200000.0
)
mapper.add_energy_consumption(building_uri, energy)

# Export
mapper.export_to_turtle("output/hq_model.ttl")
```

### Example 2: Query Building Hierarchy

```python
# Get complete building hierarchy
hierarchy = mapper.get_building_hierarchy("building_001")

print(f"Building: {hierarchy['building_id']}")
print(f"Components: {len(hierarchy['parts'])}")

for part in hierarchy['parts']:
    print(f"  - {part['label']}: {part['type']}")
```

### Example 3: Find Sensors by Type

```python
# Find all CO2 sensors in the building
co2_sensors = mapper.find_sensors_by_type("CO2_Level_Sensor")

print(f"Found {len(co2_sensors)} CO2 sensors:")
for sensor_uri in co2_sensors:
    print(f"  - {sensor_uri}")
```

### Example 4: Complex SPARQL Query

```python
# Find rooms with high occupancy and their sensors
query = """
PREFIX brick: <https://brickschema.org/schema/Brick#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?room ?label ?sensor ?sensor_type WHERE {
    ?room a brick:Room .
    ?room rdfs:label ?label .
    ?room brick:hasPart ?sensor .
    ?sensor a ?sensor_type .
    FILTER(CONTAINS(STR(?sensor_type), "Sensor"))
}
ORDER BY ?label
"""

results = mapper.query(query)
for row in results:
    print(f"{row['label']}: {row['sensor_type']}")
```

## Brick Classes Used

### Spaces
- `brick:Building` - Building entity
- `brick:Room` - Room/space entity
- `brick:Office_Building`, `brick:Residential_Building`, etc. - Building types

### Equipment
- `brick:HVAC_System` - HVAC equipment
- `brick:Variable_Air_Volume_System` - VAV systems
- `brick:Heating_System` - Heating equipment
- `brick:Ventilation_System` - Ventilation equipment

### Sensors (Points)
- `brick:Temperature_Sensor`
- `brick:Humidity_Sensor`
- `brick:CO2_Level_Sensor`
- `brick:PM2_dot_5_Sensor`
- `brick:PM10_Sensor`
- `brick:TVOC_Sensor`
- `brick:Illuminance_Sensor`

### Meters
- `brick:Heating_Thermal_Energy_Meter`
- `brick:Cooling_Thermal_Energy_Meter`
- `brick:Electrical_Energy_Meter`
- `brick:Solar_Panel_Energy_Meter`

### Relationships
- `brick:hasPart` - Containment relationship
- `brick:isPartOf` - Inverse of hasPart
- `brick:isPointOf` - Sensor belongs to equipment/space
- `brick:hasLocation` - Location information

## Advanced Features

### Custom Namespaces

```python
# Use custom namespace for your buildings
mapper = BrickMapper(base_namespace="https://mycompany.com/")
```

### Graph Statistics

```python
stats = mapper.get_stats()
print(f"Total triples: {stats['total_triples']}")
print(f"Buildings: {stats['buildings']}")
print(f"Rooms: {stats['rooms']}")
print(f"Sensors: {stats['sensors']}")
```

### Graph Validation

```python
is_valid, errors = mapper.validate_graph()
if not is_valid:
    for error in errors:
        print(f"Validation error: {error}")
```

## Integration with Existing Workflow

### 1. During Data Loading

```python
from core.infrastructure.data_loaders.excel_loader import ExcelDataLoader
from core.infrastructure.brick.mapper import BrickMapper

# Load building data
loader = ExcelDataLoader(excel_path)
dataset = loader.load_dataset()

# Create Brick model
mapper = BrickMapper()
for building in dataset.buildings:
    building_uri = mapper.add_building(building)

    for room in dataset.get_rooms_for_building(building.id):
        mapper.add_room(room, building_uri)

# Export semantic model
mapper.export_to_turtle("output/building_model.ttl")
```

### 2. After Analysis

```python
from core.analytics.engine.analysis_engine import AnalysisEngine

# Run analysis
engine = AnalysisEngine()
analysis_result = engine.analyze_dataset(dataset)

# Export to Brick with results
mapper = BrickMapper()
# ... add building and rooms ...

# Results could be added as properties or separate entities
```

## Benefits

1. **Standardization**: Use industry-standard vocabulary
2. **Interoperability**: Exchange data with other BMS systems
3. **Querying**: Use powerful SPARQL queries
4. **Visualization**: Many tools can visualize Brick models
5. **Integration**: Connect with semantic web technologies
6. **Documentation**: Self-documenting building structure

## Resources

- [BrickSchema Website](https://brickschema.org/)
- [Brick Documentation](https://docs.brickschema.org/)
- [Brick Python Library](https://github.com/BrickSchema/py-brickschema)
- [SPARQL Tutorial](https://www.w3.org/TR/sparql11-query/)

## Example Output

Running the example script generates RDF models that can be:

1. **Queried** using SPARQL endpoints
2. **Visualized** using graph visualization tools
3. **Integrated** with building management systems
4. **Shared** with other researchers/systems
5. **Validated** against Brick Schema standards

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError: No module named 'brickschema'`:

```bash
pip install brickschema rdflib
```

### Graph is Empty

Ensure you're adding entities before exporting:

```python
building_uri = mapper.add_building(building)  # Must add entities
mapper.export_to_turtle("output.ttl")
```

### Query Returns No Results

Check your SPARQL syntax and namespaces:

```python
# Correct namespace prefix
PREFIX brick: <https://brickschema.org/schema/Brick#>
```

## Next Steps

1. Run the example: `python examples/brick_schema_example.py`
2. Load your own building data
3. Create custom SPARQL queries
4. Export and share your building models
5. Integrate with visualization tools
