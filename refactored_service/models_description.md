# Core Model Description

This document describes the core Pydantic models used by HVX CODEX.

## Spatial Model

- `SpatialEntity`: base class for portfolio, building, floor, room, zone.
- Hierarchy is stored via `parent_id` and `child_ids` and mirrored in Neo4j.

## Data Sources

- `MeteringPoint`: represents a sensor, meter, weather station, or simulated point.
- `TimeSeries`: represents a time series of measurements or simulations.

## Standards

- `TestRule`: a single constraint (e.g. temperature between 20–26°C).
- `RuleSet`: a collection of TestRules plus applicability conditions.
- `StandardDefinition`: high-level definition for EN16798-1, TAIL, BR18, etc.

## Analytics

- `BaseAnalysis`: base type for any analysis run.
- `TestResult`, `ComplianceAnalysis`, `EN16798ComplianceAnalysis`: specialisations.
- `SimulationModel`, `SimulationRun`, `PredictionComparison`: model-based analytics.

## Brick Compatibility

All major models include optional `brick_class` and `brick_uri` for mapping to/from Brick Schema.

## Neo4j

Neo4j stores all core nodes and relationships so that queries can traverse:
spatial → sensors → timeseries → analyses → standards and back.
