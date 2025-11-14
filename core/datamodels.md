# Core Data Models Architecture

This document captures the target data model architecture for an EU-focused building digital twin that remains compatible with IFC, Brick Schema, and Project Haystack while supporting simulations, time-series telemetry, analytics, standards compliance, and predictive models. The intent is to guide implementations inside `core/models` and downstream services.

## Guiding Principles

- **Spatial first** – a single SpatialEntity hierarchy anchors every data point (telemetry, assets, analytics, predictions).
- **Standards-aligned** – use IFC for geometry & construction metadata, Brick for HVAC/system semantics, Haystack tags for lightweight point typing, and keep proprietary analytics logic separate but linked through IDs.
- **Typed contracts** – Pydantic models (see `core/models/base_entities.py`, `entities.py`, `metering.py`, etc.) define canonical schemas used across connectors, services, and storage.
- **Layered storage** – combine relational/lakehouse stores for tabular + time-series data and graph stores for semantic relationships without duplicating semantics.

## Model Outline

### Documentation Graph

```
                   ┌───────────────────────┐
                   │  StandardDefinition   │
                   └────────────▲──────────┘
                                │
┌───────────────┐        ┌──────┴────────┐        ┌──────────────────────┐
│ SensorSource  │        │ CountryRule   │        │     RuleClause       │
│ (API/CSV/etc) │◄──────►│ Profile       │◄──────►│ + Threshold Sets     │
└──────▲────────┘        └──────▲────────┘        └──────────▲───────────┘
       │                        │                            │
┌──────┴───────────┐    ┌───────┴────────┐         ┌─────────┴───────────┐
│ SensorDefinition │    │ SpatialEntity   │         │   AnalysisContext   │
│ + SensorGroup    │    │ (Portfolio…Room)│         └─────────▲───────────┘
└──────▲───────────┘    └───────▲────────┘                   │
       │                        │                             │
┌──────┴───────────┐    ┌───────┴────────┐         ┌─────────┴───────────┐
│ TimeSeriesRecord │    │ Aggregation    │         │   AnalysisResult     │
│ / SensorSeries   │    │ (child rollup) │         │ / SimulationResult   │
└──────▲───────────┘    └───────▲────────┘         └─────────▲───────────┘
       │                        │                             │
       │                  ┌─────┴────────┐            ┌───────┴─────────┐
       └─────────────────►│ Calculators  │            │ Provenance /    │
                          │ & Simulators │            │ State Archive   │
                          └──────────────┘            └─────────────────┘
                                 ▲
                                 │
                     ┌───────────┴───────────┐
                     │ User / Access Control │
                     └───────────────────────┘
```

Arrows show data flow: sensors feed SpatialEntities, which run calculators via `compute_analysis()`/`compute_simulation()`, producing AnalysisResults validated against standards/rules and aggregated up the hierarchy.

### User & Access Management

Add a user/access layer to guard every object:

- `UserProfile` Pydantic model: `id`, `email`, `roles` (admin, analyst, viewer, tenant), `organization_id`, `permissions`.
- `AccessControlList` entries tie principals (users, groups, service accounts) to resources (`SpatialEntity`, sensors, analyses, standards configs) with scopes (`read`, `write`, `execute`, `share`).
- `ResourceReference` embeds `(resource_type, resource_id)` plus inherited permissions. SpatialEntities can contain an `access_control` list so building owners can restrict floors/rooms; calculators and standards configs reference ACLs so only authorized analysts can run or edit them.
- Computation methods (`compute_analysis`, `load_sensor`, etc.) accept `user_context` kwargs to enforce access checks before mutating state or reading telemetry.
- Aggregations respect the strictest access level: if a user lacks permission for a child room, floor-level metrics either exclude the room or return redacted outputs. Portfolio views only expose entities the user can view.

This model enables multi-tenant deployments where each stakeholder (owners, operators, tenants, service partners) accesses only the relevant parts of the digital twin while sharing the same data structures.

### Spatial Entities
Use `SpatialEntity` as the base class with thin specializations in `entities.py`. Extend attributes (mostly in `metadata`) to ensure IFC/Brick compatibility:

- `id`, `name`, `type`: stable identifiers plus enum for portfolio/building/floor/room/zone/site.
- `parent_ids`, `child_ids`: maintain hierarchy and allow polyhierarchy (e.g., a room belongs to multiple analytical groups).
- `geometry_ref`: pointer to geometry storage (IFC GUID, BIM file, GeoJSON).
- `metadata.ifc_refs`: `{ "space": "<IfcSpaceGUID>", "storey": "<IfcBuildingStoreyGUID>" }`.
- `metadata.brick_zone_uri`: direct URI into Brick zone nodes.
- `metadata.haystack_tags`: list of tokens.
- `metadata.country`, `metadata.country_code`, `metadata.region`, `metadata.epbd_zone`: normalized fields for standards lookup.
- `area_m2`, `volume_m3`, `design_occupancy`: pulled from IFC or manual inputs.

Optional helper models (new Pydantic classes under `core/models/base_entities.py`):

```python
class SpatialLink(BaseModel):
    spatial_entity_id: str
    ifc_guid: Optional[str]
    brick_uri: Optional[str]
    haystack_tags: List[str] = []
```

### Analysis Models
Define structured outputs under `core/models/analysis.py`:

- `AnalysisContext`: `spatial_entity_id`, `sensor_ids`, `brick_uris`, `standard_version`, `season`, `climate_inputs_ref`.
- `AnalysisResult`: base class with `analysis_id`, `analysis_type`, `context`, `results`, `confidence`, `issued_at`, `valid_from`, `valid_to`.
- Specializations:
  - `ComfortAnalysisResult` (EN 16798 categories, violation counts, compliance %).
  - `EnergySignatureResult` (baseline parameters, CVRMSE, MAPE, predictions).
  - `AnomalyDetectionResult` (severity, description, linked sensors/models).

Persist results as documents keyed by `(spatial_entity_id, analysis_type, issued_at)`. Include `provenance` (pipeline version, model version, author).

### Standards & Rules
Represent standards in two layers:

1. **Standard definition** (metadata about the regulation):
   ```python
   class StandardDefinition(BaseModel):
       id: str  # e.g. "en16798_1"
       name: str
       version: str
       jurisdiction: str  # "EU", "DK", etc.
       scope: List[str]  # comfort, ventilation, energy
       references: List[str]  # official docs
   ```
   Store these in `core/models/rules.py` or `standards/*/config.yaml`.

2. **Rule sets** (machine-evaluable clauses):
   ```python
   class RuleClause(BaseModel):
       id: str
       condition: Dict[str, Any]  # e.g. category, season, entity type
       thresholds: Dict[str, Any]
       severity: str
       rationale: str
   ```

3. **Country profiles**:
   ```python
   class CountryRuleProfile(BaseModel):
       country_code: str
       standard_ids: List[str]
       overrides: Dict[str, RuleClause]
   ```

Link `SpatialEntity.metadata.country_code` to `CountryRuleProfile` to resolve applicable standards.

### Sets & Libraries
Create catalog models for reusable enumerations:

- `ClimateSet` (EN ISO 52010 zones, heating/cooling design data).
- `OccupancySet` (default occupancy densities per building type).
- `VentilationSet` (airflow requirements per standard category).
- `SensorSet` (logical groups of sensors needed for analyses).

Each set entry links to the originating standard and version for traceability.

## SpatialEntity Relationship Graph

SpatialEntity nodes are intentionally abstract so they can anchor the entire digital twin without carrying standard-specific fields. Relationships are implemented through typed references:

```
                 ┌────────────────────┐
                 │ StandardDefinition │
                 └─────────▲──────────┘
                           │
┌───────────────┐    ┌─────┴─────┐    ┌─────────────────┐
│ SensorSeries  │◄──►│ Spatial   │◄──►│ AnalysisResult  │
│ (Timeseries)  │    │ Entity    │    │ (comfort, energy│
└──────┬────────┘    │ (Room,    │    │ anomalies, etc.)│
       │             │ Floor…)   │    └─────────▲───────┘
       │             └─────▲─────┘              │
       │                   │                    │
       │             ┌─────┴─────┐        ┌─────┴──────┐
       └────────────►│ Aggregator│◄──────►│ RuleClause │
                     │ (child    │        │ /Sets      │
                     │ rollups)  │        └────────────┘
                     └───────────┘
```

### Links in Practice (dummy_data portfolio)

The sample portfolio under `data/samples/dummy_data` shows how entities relate:

1. **SpatialEntities**
   - Portfolio `dummy_portfolio`
   - Buildings `building_A`, `building_B`
   - Floors `building_A/level_1`, …
   - Rooms from each `room_<id>.csv`
   - Each entity includes `metadata.ifc_guid`, `metadata.brick_zone_uri`, `metadata.country_code="DK"`.

2. **Sensors & Time Series**
   - Every `room_*.csv` file yields `SensorDefinition` objects (CO₂, temperature, humidity) with `sensor_id` derived from file name.
   - `TimeSeriesRecord` rows link back to the room `SpatialEntity.id`.

3. **Analyses**
   - Calculators (EN16798, TAIL, RC model) consume `SensorSeries` + `SpatialEntity` context and emit `AnalysisResult` documents keyed by the room or floor ID.
   - Portfolio/floor level analyses reference aggregated child results through `parent_ids`.

4. **Aggregations**
   - When `SpatialEntity` has `child_ids`, an `AggregationResult` model captures rolled-up metrics (e.g., room → floor compliance percentages). The `aggregators.py` helpers leverage these to compute portfolio summaries.

5. **Standards & Rules**
   - Because `metadata.country_code="DK"`, the standards service resolves EN16798, BR18, EPBD, etc., attaches applicable `RuleClause` IDs to the `AnalysisContext`, and validates `AnalysisResult.results` against the thresholds.

This pattern generalizes beyond dummy data: once SpatialEntity IDs and metadata are set, every sensor, time series, analytics output, and standard reference simply hangs off the node, keeping the twin graph consistent and auditable.

### Progressive Detail Strategy

The data model must work whether only high-level portfolio statistics exist or the full IFC/Brick/Haystack detail is available. Design choices:

- **Permissive schemas**: every Pydantic model allows optional fields; if only building-level data exists, `SpatialEntity` for rooms simply is absent and aggregations operate at building level. Calculators can fall back to area/volume + macro KPIs (e.g., annual energy) when sensor streams are missing.
- **Detail tiers**:
  1. **Portfolio tier** – minimal attributes: total buildings, aggregate area, annual consumption, average EPC rating. `AnalysisResult` at this tier represents coarse KPIs (e.g., per-building energy intensity) and references sensor placeholders (derived from utility bills).
  2. **Building tier** – additional metadata: construction year, main materials, heating/cooling systems, theoretical EPC, boiler/chiller type, fuel mix. Minimal telemetry: building-level energy meters, indoor/outdoor averages.
  3. **Floor tier** – optional; adds area/volume/perimeter, occupancy density hints, partial sensor coverage (e.g., a few temperature probes).
  4. **Room tier** – full deployment with IFC geometry, Brick zone references, setpoints, and detailed sensor series (temperature, CO₂, humidity, lux, occupancy, design occupancy, air flow, supply/return temperatures, water flow, radiator ΔT, thermostat measurements, etc.).
- **Upgradeable references**: start with `metadata` placeholders (`"ifc_guid": null`, `"brick_zone_uri": null`) and fill them as richer integrations land, without schema changes.
- **Analysis flexibility**: `AnalysisContext` contains `data_granularity` or `spatial_level` so calculators know whether they operate on portfolio, building, floor, or room detail and can select appropriate models/rules (e.g., EN16798 room-level vs EPBD building-level).
- **SensorSeries extensibility**: sensors are referenced by semantic role (temperature, setpoint, airflow, etc.). You can attach simulated or estimated series when real sensors are missing, keeping the pipeline running while marking provenance.

This staged approach lets the same core models serve quick macro analyses during onboarding and gradually enrich to full digital twin fidelity without re-architecting data structures.

### SpatialEntity Behaviors

To keep business logic close to the data contracts, each SpatialEntity (and subclasses) exposes helper methods:

- `load_sensor(sensor: SensorDefinition, source: Literal["api","csv","stream"], **kwargs)` adds or updates a sensor reference for the entity. Multiple sensors with the same semantic parameter (e.g., temperature) are allowed; metadata can specify weighting (area, quality score, priority) which is then used during aggregation.
- `compute_analysis(**kwargs)` orchestrates all applicable calculators. At runtime it:
  1. Resolves standards based on `metadata.country_code`, `building_type`, and `available_sensors`.
  2. Selects calculators (EN16798, TAIL, ventilation, occupancy, etc.) from a registry and calls them with the entity context + sensor streams.
  3. Stores `AnalysisResult` instances in the entity’s `computed_metrics` cache.
  4. Supports overrides via kwargs—for example `compute_analysis(analyses=["en16798","tail"], force=True)`.
- `compute_simulation(**kwargs)` triggers simulations such as RC thermal models, energy signatures, or ML predictors. Kwargs carry simulation-specific inputs (e.g., `weather_series`, `hvac_schedule`). Results are added to the analysis cache as simulation outputs.

Aggregation flows:

- When an entity has child entities (e.g., floor with rooms), `compute_analysis()` also calls the aggregators in `core/models/aggregators.py` to roll up child results. Default behavior is “worst-case” aggregation for comfort categories; kwargs allow switching to average or weighted average (by area, volume, or sensor quality).
- Sensor aggregation relies on declared weights: if multiple sensors measure the same parameter, `load_sensor()` stores them in a `SensorGroup` object with methods like `average()`, `weighted_average()`, `median()`. Buildings/floors can thus aggregate room sensors before running building-level analyses.
- `compute_analysis()` first ensures required sensor groups exist; if not, it can derive proxies (e.g., average of rooms) before invoking calculators.

This pattern lets analytics run directly from the Pydantic models, ensuring every SpatialEntity can self-evaluate using the metadata, standards, and calculators that apply at its level of detail.

### Energy Conversion Layer

- `core/energy.py` hosts canonical energy data (fuel calorific values, primary energy factors, technology helpers) built on enums `EnergyCarrier`, `FuelUnit`, and `PrimaryEnergyScope`.
- `EnergyConversionService` converts physical fuel quantities (e.g., m³ of natural gas, liters of oil, kg of biomass) to delivered kWh using default or country-specific efficiencies, and then to primary energy via per-country factors. Scopes (total, non-renewable, renewable) follow EPBD/EED conventions so outputs feed EPC and portfolio KPIs consistently.
- Helper methods cover electrified and hybrid technologies: `heat_pump_input_from_output()` computes power draw using COP, `heat_pump_output_from_input()` estimates thermal delivery, `cogeneration_outputs()` splits CHP fuel inputs into electric vs thermal portions, and `convert_energy_mix_to_primary()` aggregates all carriers into a single KPI.
- Default factor tables include EU + DK references; deployments override factors using `PrimaryEnergyFactor` records tied to `SpatialEntity.metadata.country_code`, ensuring conversions stay auditable.

### Occupancy & Opening Hours

- `OpeningHoursProfile` enum plus `core/schedules.py` define reusable opening-hour templates for major building types (office, retail, education, hospitality, industrial, 24/7).
- `generate_occupancy_mask()` combines the profile with national holidays (via the `holidays` package) to build boolean series identifying occupied timestamps. Profiles inherit from parent spatial entities by traversing `parent_ids` until a building-level type is found.
- Analyses (e.g., EN 16798) can now pre-filter time series to occupied hours by retrieving the building’s profile and country code before calling calculators.

### EPC Rating

- `simulations/models/real_epc.py` provides EU member state threshold tables (DK, FR, DE, default EU) and a helper that maps primary energy intensity to EPC labels (A…G), while theoretical EPC remains a `Building` metadata property.
- `Building.get_energy_summary()` automatically computes the EPC rating after primary energy is calculated, ensuring dashboards and compliance modules have consistent EPC snapshots across countries.

## Canonical Spatial Layer

`SpatialEntity` (and the Portfolio/Building/Floor/Room/Zone implementations in `core/models/entities.py`) form the geometry-driven backbone:

- Minimal attributes: `id`, `type`, `name`, parent/child IDs, area/volume, occupancy, and contextual metadata (country, climate zone, building use).
- **IFC linkage**: store `metadata.ifc_guid` (or a list) so every `SpatialEntity` is traceable to `IfcSpace` / `IfcBuildingStorey` elements.
- **Brick zone linkage**: store `metadata.brick_uri` (e.g., `brick:Zone_X`) to connect geometry to the Brick semantic graph.
- **Haystack tags**: include `metadata.haystack_tags` for interoperability with systems that expect marker-based typing.

Spatial entities never include HVAC-specific fields—they only reference other systems by ID/URI to keep the spatial core reusable.

## Systems & Assets (Brick/Haystack)

HVAC and other building systems remain fully described via Brick classes (AHU, VAV, Plant, Sensors, Points) stored in a graph DB (e.g., Neo4j) or RDF store. Each Brick node contains:

- `brick_uri` (globally unique URI).
- Haystack tags (e.g., `ahu`, `supply`, `air`).
- Optional pointer to IFC `IfcDistributionElement` GUIDs.
- Optional `spatial_entity_id` where the equipment resides or serves.

The core service references Brick nodes through URIs stored on Pydantic models (e.g., `EquipmentRef`, `PointRef`). This keeps the Brick graph authoritative while letting analytics query via adapters.

## Telemetry & Time Series

Telemetry (raw sensors, standardized feeds, simulated series) is modeled via dedicated Pydantic schemas (extend `core/models/metering.py`):

- `SensorDefinition`: describes physical/virtual sensors, linking `sensor_id` to `brick_point_uri`, `spatial_entity_id`, measurement units, and tags (standard vs simulated vs derived).
- `TimeSeriesRecord`: minimal schema for ingestion (timestamp, value, quality, `sensor_id`, provenance).
- `CalibratedSeries` / `DerivedSeries`: capture standardized or simulated streams with references to the generating model/config.

Storage strategy:

- High-rate data → time-series DB (TimescaleDB) or lakehouse tables partitioned by sensor + time.
- Summaries/features → relational tables keyed by `spatial_entity_id`.

## State & Analytics Layer

Analytical outputs (compliance, anomalies, predictions) share a consistent structure:

- `state_id`: deterministic hash of `spatial_entity_id`, analysis type, and timestamp/version.
- `source_standard` / `model_id`: identifies EN16798, EPBD, RC thermal model, ML model, etc.
- `inputs_ref`: references to sensors/models used (for audit traceability).
- `results`: structured payload (Pydantic model) containing KPIs (comfort category, EPC delta, predicted load) plus confidence intervals.
- `valid_for`: time window when the state applies (supports historical compliance back-testing).

`core/models/analysis.py` and `simulation.py` can host these schemas so the same contracts are reused by calculators, engines, and APIs.

## Data Lineage & Provenance

Every model includes provenance metadata to ensure traceability:

- `created_at`, `updated_at`, `source_system`, `processing_pipeline`, `version`.
- `links`: reference arrays back to SpatialEntity, Brick URIs, IFC GUIDs, and sensor IDs.

This is critical for EU regulations (EPBD, EED) that demand auditable compliance evidence.

## Minimal SpatialEntity Example

```python
from core.models.base_entities import SpatialEntity

room = SpatialEntity(
    id="room-3F-12",
    name="Conf Room 3F-12",
    type="room",
    parent_ids=["floor-3"],
    metadata={
        "ifc_guid": "2m4dX$96PDcONycCu5IfbL",
        "brick_uri": "https://brick.example.com/zone/ConfRoom3F12",
        "haystack_tags": ["space", "conf", "room"],
    }
)
```

Downstream services use the `id` to join with Brick equipment/points, sensor streams, IFC geometry, and analytics outputs without embedding cross-standard logic into the SpatialEntity itself.

## Roadmap

1. Extend existing Pydantic models (`core/models/*`) per the structures above (e.g., add sensor + state schemas).
2. Implement adapters that translate between IFC/Brick/Haystack IDs and SpatialEntity IDs.
3. Ensure ingestion pipelines populate provenance metadata and maintain referential integrity across stores.
