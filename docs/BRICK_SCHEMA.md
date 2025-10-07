# Brick Schema Integration

HVX now fully supports [Brick Schema](https://brickschema.org/), a standardized semantic ontology for building systems and sensors. This integration enables semantic interoperability, standardized data modeling, and RDF/Turtle export capabilities.

## Overview

All domain models (Room, Level, Building) and analysis results models (RoomAnalysis, LevelAnalysis, BuildingAnalysis, PortfolioAnalysis) now inherit from Brick Schema base classes, providing:

- **Semantic URIs**: Each entity has a unique Brick Schema URI
- **Type Classification**: Automatic Brick Schema type assignment
- **Relationships**: Semantic relationships (hasPart, isPartOf, feeds)
- **RDF Export**: Export to RDF graphs and Turtle format
- **Metadata**: Rich metadata aligned with Brick Schema

## Features

### 1. Automatic Brick Schema Support

All models automatically generate Brick Schema metadata:

```python
from src.core.models.domain import Room, Level, Building

# Create a room - Brick Schema metadata is auto-generated
room = Room(
    id="room_101",
    name="Office 101",
    building_id="building_1",
    area_m2=25.0
)

# Access Brick Schema properties
print(room.brick_type)  # "brick:Room"
print(room.brick_uri)   # "urn:building:building_1:room:room_101"
print(room.brick_metadata)  # {'area': {'value': 25.0, 'unit': 'squareMeter'}}
```

### 2. Hierarchical Relationships

Brick Schema relationships are automatically created when building hierarchies:

```python
building = Building(id="building_1", name="Main Building")
level = Level(id="floor_1", name="First Floor", building_id="building_1")
room = Room(id="room_101", name="Office 101", building_id="building_1")

# Add to hierarchy - relationships are auto-created
building.add_level(level)
level.add_room(room)

# Brick Schema relationships are populated
print(building.brick_relationships)
# {'hasPart': ['urn:building:building_1:floor:floor_1']}

print(level.brick_relationships)
# {'isPartOf': ['urn:building:building_1'], 
#  'hasPart': ['urn:building:building_1:room:room_101']}
```

### 3. RDF Export

Export entities to RDF graphs and Turtle format:

```python
from brickschema import Graph

# Create a building hierarchy
building = Building(
    id="building_1",
    name="Main Building",
    address="123 Main St",
    city="Copenhagen"
)

# Export to RDF graph
graph = Graph()
graph.bind("brick", "https://brickschema.org/schema/Brick#")
building.to_brick_graph(graph)

# Export to Turtle format
turtle = building.to_brick_turtle()
print(turtle)
```

**Output (Turtle format):**

```turtle
@prefix brick: <https://brickschema.org/schema/Brick#> .

<urn:building:building_1> a brick:Building ;
    brick:address "123 Main St" ;
    brick:city "Copenhagen" ;
    brick:country "Denmark" .
```

### 4. Analysis Results with Brick Schema

Analysis results are also Brick Schema compatible:

```python
from src.core.models.results import RoomAnalysis

analysis = RoomAnalysis(
    room_id="room_101",
    room_name="Office 101",
    building_id="building_1",
    overall_compliance_rate=85.5
)

# Brick Schema metadata includes analysis metrics
print(analysis.brick_type)  # "brick:Analysis_Result"
print(analysis.brick_metadata)
# {'complianceRate': 85.5, 'qualityScore': 0.0}
```

## API Reference

### BrickSchemaEntity

Base class for all Brick Schema compatible entities.

**Properties:**

- `brick_type`: Brick Schema class (e.g., "brick:Room", "brick:Building")
- `brick_uri`: Unique RDF URI for the entity
- `brick_relationships`: Dictionary of Brick Schema relationships
- `brick_metadata`: Additional metadata and properties

**Methods:**

- `get_brick_type_uri()`: Get the full Brick Schema type URI
- `set_brick_type(brick_class)`: Set the Brick Schema type
- `add_brick_relationship(predicate, target_uri)`: Add a relationship
- `get_brick_relationships(predicate)`: Get relationships
- `to_brick_dict()`: Export as Brick Schema dictionary
- `to_brick_graph(graph)`: Export to RDF graph
- `to_brick_turtle()`: Export as Turtle format
- `validate_brick_schema()`: Validate conformance

### Domain Models

#### Room

- **Brick Type**: `brick:Room`
- **URI Pattern**: `urn:building:{building_id}:room:{room_id}`
- **Metadata**: area, volume, capacity, roomType

#### Level

- **Brick Type**: `brick:Floor`
- **URI Pattern**: `urn:building:{building_id}:floor:{level_id}`
- **Metadata**: floorNumber

#### Building

- **Brick Type**: `brick:Building`
- **URI Pattern**: `urn:building:{building_id}`
- **Metadata**: address, city, postalCode, country, constructionYear, totalArea

### Analysis Results Models

All analysis models use:
- **Brick Type**: `brick:Analysis_Result`
- **URI Pattern**: `urn:building:{building_id}:...:analysis:{timestamp}`
- **Metadata**: complianceRate, qualityScore, etc.

## Usage Examples

### Export Building Portfolio to RDF

```python
from src.core.models.domain import Building, Level, Room
from brickschema import Graph

# Create building structure
building = Building(id="htk_1", name="HTK Building")
floor_1 = Level(id="floor_1", name="Floor 1", building_id="htk_1", floor_number=1)
floor_2 = Level(id="floor_2", name="Floor 2", building_id="htk_1", floor_number=2)

room_101 = Room(id="101", name="Room 101", building_id="htk_1", area_m2=25.0)
room_102 = Room(id="102", name="Room 102", building_id="htk_1", area_m2=30.0)
room_201 = Room(id="201", name="Room 201", building_id="htk_1", area_m2=28.0)

# Build hierarchy
building.add_level(floor_1)
building.add_level(floor_2)
floor_1.add_room(room_101)
floor_1.add_room(room_102)
floor_2.add_room(room_201)

# Export entire hierarchy to RDF
graph = Graph()
graph.bind("brick", "https://brickschema.org/schema/Brick#")

building.to_brick_graph(graph)
for level in building.levels:
    level.to_brick_graph(graph)
    for room in level.rooms:
        room.to_brick_graph(graph)

# Save to file
graph.serialize("building_portfolio.ttl", format="turtle")
print(f"Exported {len(graph)} RDF triples")
```

### Query Brick Schema Data

```python
from brickschema import Graph

# Load exported data
graph = Graph()
graph.parse("building_portfolio.ttl", format="turtle")

# SPARQL query example
query = """
PREFIX brick: <https://brickschema.org/schema/Brick#>

SELECT ?room ?area WHERE {
    ?room a brick:Room .
    ?room brick:area ?area .
}
"""

results = graph.query(query)
for row in results:
    print(f"Room: {row.room}, Area: {row.area}")
```

### Integrate with Analysis Results

```python
from src.core.models.results import RoomAnalysis

# Create analysis with Brick Schema
analysis = RoomAnalysis(
    room_id="room_101",
    room_name="Office 101",
    building_id="building_1",
    overall_compliance_rate=85.5,
    overall_quality_score=92.3
)

# Export analysis to RDF
analysis_graph = analysis.to_brick_graph()

# Link analysis to room
room = Room(id="room_101", name="Office 101", building_id="building_1")
room.add_brick_relationship("hasAnalysis", analysis.brick_uri)

# Export linked data
combined_graph = Graph()
room.to_brick_graph(combined_graph)
analysis.to_brick_graph(combined_graph)

print(combined_graph.serialize(format="turtle"))
```

## Backward Compatibility

All existing HVX functionality remains unchanged. Brick Schema support is **additive**:

- ✅ All existing models work exactly as before
- ✅ All existing methods and properties are preserved
- ✅ Brick Schema fields are auto-populated but optional
- ✅ No breaking changes to existing code

## Benefits

1. **Standardization**: Align with industry-standard building ontology
2. **Interoperability**: Exchange data with other Brick Schema tools
3. **Semantic Queries**: Use SPARQL for complex building data queries
4. **Extensibility**: Easy to extend with custom Brick Schema types
5. **Integration**: Compatible with Brick Schema ecosystem tools

## Learn More

- [Brick Schema Official Site](https://brickschema.org/)
- [Brick Schema GitHub](https://github.com/BrickSchema/Brick)
- [Brick Schema Python Library](https://github.com/BrickSchema/py-brickschema)

## Dependencies

Brick Schema integration requires:

```bash
pip install brickschema>=0.2.0
```

This is automatically included in HVX dependencies.
