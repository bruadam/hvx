# Brick Schema Infrastructure

This module provides integration with the [BrickSchema](https://brickschema.org/) ontology for semantic building modeling.

## Components

### `BrickMapper`
Main class for mapping IEQ Analytics domain models to Brick Schema RDF triples.

**Key Methods:**
- `add_building(building)` - Map Building model to Brick
- `add_room(room, building_uri)` - Map Room model to Brick
- `add_energy_consumption(building_uri, energy)` - Map energy meters
- `query(sparql_query)` - Execute SPARQL queries
- `export_to_turtle(path)` - Export to Turtle format
- `export_to_rdf(path)` - Export to RDF/XML
- `export_to_json_ld(path)` - Export to JSON-LD

### `BrickNamespaceManager`
Manages RDF namespaces for Brick Schema and related ontologies.

**Namespaces:**
- BRICK - Main Brick Schema namespace
- RDF/RDFS/OWL - Semantic web standards
- QUDT - Units and quantities
- Custom namespaces for building instances

## Usage

```python
from core.infrastructure.brick.mapper import BrickMapper

# Initialize
mapper = BrickMapper()

# Map domain models
building_uri = mapper.add_building(my_building)
room_uri = mapper.add_room(my_room, building_uri)

# Query with SPARQL
results = mapper.query("""
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    SELECT ?room WHERE { ?room a brick:Room }
""")

# Export
mapper.export_to_turtle("output.ttl")
```

## Documentation

See `docs/BRICK_INTEGRATION.md` for complete documentation and examples.

## Examples

- `examples/brick_schema_example.py` - Comprehensive usage example
- `test_brick_integration.py` - Quick verification test
