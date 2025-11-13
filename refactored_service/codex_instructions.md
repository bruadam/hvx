# CODEX Standard Instruction Specification (Brick-Enabled)

This project uses a folder-based plugin system.

## 1. Standards

Each standard lives in `standards/<standard-id>/` with:

- `config.yaml` — declarative definition (applicability, required inputs, rules, analysis entry)
- `analysis.py` — Python entry with `run(standard_config, spatial_entity, timeseries_dict, ruleset, context)`

CODEX scans `standards/` and dynamically imports each standard.

## 2. Ingestion Connectors

Each connector lives in `ingestion/<connector-id>/` with:

- `config.yaml`
- `connector.py` implementing a `fetch(start, end)` interface that returns TimeSeries.

## 3. Simulation Models

Each simulation model lives in `simulation_models/<model-id>/` with:

- `config.yaml`
- `model.py` implementing a `run(inputs, context)` interface and returning simulated TimeSeries.

## 4. Analytics Modules

Analytics live in `analytics/<analytics-id>/` with:

- `config.yaml`
- `logic.py` implementing `run(spatial_entity, context)` and returning Analysis instances.

## 5. Brick Compatibility

The `brick/` folder contains:

- `mappings/*.yaml` for mapping internal classes to Brick classes/units
- `importer/from_brick.py` to build internal Pydantic models from Brick RDF
- `exporter/to_brick.py` to export internal model to Brick TTL
- `ontology/` optionally containing a Brick TTL file

## 6. Neo4j

The `neo4j/` folder contains CQL files for:

- node labels and relationship types
- seeds for spatial and standards nodes

The graph schema is designed to align with Brick concepts:
`SpatialEntity`, `Sensor`, `Point`, `TimeSeries`, `Standard`, `RuleSet`, `Analysis`.

See `core/models/` for the Pydantic models these components are based on.
