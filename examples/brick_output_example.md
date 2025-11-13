# BrickSchema Output Example

This document shows what the generated Brick Schema output looks like.

## Generated Turtle (RDF) Output

The mapper creates semantic RDF triples following the Brick Schema standard.

### Example Building in Turtle Format

```turtle
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix bldg: <https://ieq-analytics.example.org/building/> .
@prefix sensor: <https://ieq-analytics.example.org/sensor/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

# Building Entity
bldg:test_building a brick:Building,
        brick:Office_Building ;
    rdfs:label "Test Office" ;
    brick:area 1000.0 ;
    brick:hasPart bldg:test_building_hvac,
                  bldg:test_building_ventilation,
                  bldg:test_room_101,
                  sensor:test_building_heating_meter,
                  sensor:test_building_cooling_meter,
                  sensor:test_building_electricity_meter .

# HVAC System
bldg:test_building_hvac a brick:Variable_Air_Volume_System ;
    brick:isPartOf bldg:test_building .

# Ventilation System
bldg:test_building_ventilation a brick:Mechanical_Ventilation_System ;
    brick:isPartOf bldg:test_building .

# Room Entity
bldg:test_room_101 a brick:Room ;
    rdfs:label "Conference Room" ;
    brick:area 50.0 ;
    brick:volume 150.0 ;
    brick:isPartOf bldg:test_building .

# Energy Meters
sensor:test_building_heating_meter a brick:Heating_Thermal_Energy_Meter ;
    rdfs:label "heating meter" ;
    brick:isPointOf bldg:test_building .

sensor:test_building_cooling_meter a brick:Cooling_Thermal_Energy_Meter ;
    rdfs:label "cooling meter" ;
    brick:isPointOf bldg:test_building .

sensor:test_building_electricity_meter a brick:Electrical_Energy_Meter ;
    rdfs:label "electricity meter" ;
    brick:isPointOf bldg:test_building .
```

## Graph Structure

```
Building (test_building)
├── Type: Office_Building
├── Properties
│   ├── Label: "Test Office"
│   └── Area: 1000.0 m²
├── HVAC System
│   └── Variable_Air_Volume_System
├── Ventilation System
│   └── Mechanical_Ventilation_System
├── Rooms
│   └── test_room_101 (Conference Room)
│       ├── Area: 50.0 m²
│       └── Volume: 150.0 m³
└── Energy Meters
    ├── Heating Thermal Energy Meter
    ├── Cooling Thermal Energy Meter
    └── Electrical Energy Meter
```

## SPARQL Query Examples

### Query 1: Find All Rooms

```sparql
PREFIX brick: <https://brickschema.org/schema/Brick#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?room ?label ?area WHERE {
    ?room a brick:Room .
    ?room rdfs:label ?label .
    OPTIONAL { ?room brick:area ?area }
}
```

**Results:**
| room | label | area |
|------|-------|------|
| bldg:test_room_101 | Conference Room | 50.0 |

### Query 2: Find All Energy Meters

```sparql
PREFIX brick: <https://brickschema.org/schema/Brick#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?meter ?type ?label WHERE {
    ?meter a ?type .
    ?meter rdfs:label ?label .
    FILTER(CONTAINS(STR(?type), "Meter"))
}
```

**Results:**
| meter | type | label |
|-------|------|-------|
| sensor:test_building_heating_meter | Heating_Thermal_Energy_Meter | heating meter |
| sensor:test_building_cooling_meter | Cooling_Thermal_Energy_Meter | cooling meter |
| sensor:test_building_electricity_meter | Electrical_Energy_Meter | electricity meter |

### Query 3: Find Building Hierarchy

```sparql
PREFIX brick: <https://brickschema.org/schema/Brick#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?building ?part ?partType WHERE {
    ?building a brick:Building .
    ?building brick:hasPart ?part .
    ?part a ?partType .
}
```

**Results:**
| building | part | partType |
|----------|------|----------|
| bldg:test_building | bldg:test_building_hvac | Variable_Air_Volume_System |
| bldg:test_building | bldg:test_building_ventilation | Mechanical_Ventilation_System |
| bldg:test_building | bldg:test_room_101 | Room |
| bldg:test_building | sensor:test_building_heating_meter | Heating_Thermal_Energy_Meter |

## File Statistics

- **File Size**: ~1.7 MB (includes full Brick ontology)
- **Total Triples**: 53,844
  - Base Brick ontology: 53,816 triples
  - Custom building data: 28 triples
- **Format**: Turtle (TTL) - human-readable RDF
- **Alternative Formats**: RDF/XML, JSON-LD also supported

## Integration Benefits

### 1. Standard Vocabulary
Using Brick means your building data uses the same terminology as:
- Building Management Systems (BMS)
- Energy management platforms
- Smart building applications
- Research institutions

### 2. Semantic Queries
SPARQL enables complex queries like:
- "Find all conference rooms with CO2 sensors"
- "List buildings with VAV systems and their energy meters"
- "Show all rooms larger than 100 m² with mechanical ventilation"

### 3. Graph Relationships
The RDF graph captures relationships:
- `hasPart` / `isPartOf` - containment
- `isPointOf` - sensor/meter belongs to equipment
- `feeds` / `feedsAir` - system connections (can be extended)

### 4. Interoperability
Export to standard formats enables:
- Sharing with other systems
- Integration with visualization tools
- Data exchange between organizations
- Compliance with building data standards

## Visualization

The generated Brick model can be visualized using tools like:
- [Brick Viewer](https://viewer.brickschema.org/)
- Graph databases (Neo4j, GraphDB)
- RDF visualization tools
- Custom web interfaces

## Real-World Example

For a full building with 50 rooms, 200 sensors, and complete HVAC systems:

```
Total RDF Triples: ~54,500
├── Base Brick Ontology: 53,816
└── Custom Building Data: ~700
    ├── Buildings: 1
    ├── Rooms: 50
    ├── HVAC Equipment: 15
    ├── Sensors: 200
    ├── Energy Meters: 8
    └── Relationships: ~426
```

Query performance: < 100ms for most queries on consumer hardware.

## Next Steps

1. Load your actual building data
2. Create domain-specific SPARQL queries
3. Export models for integration
4. Visualize building topology
5. Connect with building management systems
