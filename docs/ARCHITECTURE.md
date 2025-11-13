Move this file to docs/ARCHITECTURE.md


# Architecture Documentation

## Design Principles

### 1. Clean Architecture (Hexagonal/Ports & Adapters)

```
┌─────────────────────────────────────────────────────────┐
│                     CLI / API Layer                      │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────┐
│              Application Layer (Use Cases)               │
│  - AnalyzeBuilding                                       │
│  - GenerateReport                                        │
│  - ValidateData                                          │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────┐
│                   Domain Layer                           │
│  - Room, Building, AnalysisResult (entities)             │
│  - Temperature, CO2Level (value objects)                 │
│  - Business rules and logic                              │
└──────────────────────────────────────────────────────────┘
```

### 2. Dependency Rule
Dependencies point **inward** only:
- CLI → Application → Domain
- Infrastructure → Application → Domain
- Domain has **NO** external dependencies

### 3. One Class Per File
Each file contains exactly one class/function for:
- Easy navigation
- Clear responsibility
- Simple testing
- Better git history

## Layer Responsibilities

### Domain Layer (`core/domain/`)

**Purpose**: Core business entities and rules

**Contains**:
- **models/**: Entity classes (Room, Building, Level, etc.)
- **value_objects/**: Immutable values (Temperature, CO2Level, TimeRange, etc.)
- **enums/**: Type-safe enumerations
- **exceptions/**: Domain-specific exceptions

**Rules**:
- NO external dependencies (only stdlib, pydantic)
- All types are immutable where possible
- Rich domain models with behavior
- Validation at construction time

**Example**: `Room` entity contains methods like `add_measurement()`, not just data storage.

### Application Layer (`core/application/`)

**Purpose**: Orchestrate business logic and use cases

**Contains**:
- **use_cases/**: High-level operations (AnalyzeBuildingUseCase, GenerateReportUseCase)
- **services/**: Application services (AnalyticsService, ReportService)
- **interfaces/**: Abstract interfaces for ports (IDataLoader, IReportRenderer)
- **dto/**: Data Transfer Objects for boundaries

**Rules**:
- Orchestrates domain entities
- NO direct I/O operations
- Uses interfaces for external dependencies
- Transaction boundaries

**Example**: `AnalyzeBuildingUseCase` coordinates data loading, analytics, and storage.

### Infrastructure Layer (`core/infrastructure/`)

**Purpose**: External system integrations

**Contains**:
- **data_loaders/**: File parsing (CSV, Excel, JSON)
- **repositories/**: Data persistence
- **external_services/**: API clients (weather data)
- **file_system/**: File operations

**Rules**:
- Implements application interfaces
- Handles all I/O
- Error handling and retries
- Configuration management

**Example**: `CSVDataLoader` implements `IDataLoader` interface.

### Analytics Layer (`core/analytics/`)

**Purpose**: IEQ-specific analytics engine

**Contains**:
- **engine/**: Core analysis engine
- **evaluators/**: Compliance evaluators (one per standard)
  - `en16798_evaluator.py`
  - `br18_evaluator.py`
  - `danish_guidelines_evaluator.py`
- **metrics/**: Calculation functions
  - `statistical_metrics.py`
  - `compliance_metrics.py`
  - `data_quality_metrics.py`
- **filters/**: Time-based data filtering
  - `time_filter.py`
  - `opening_hours_filter.py`
  - `seasonal_filter.py`
- **aggregators/**: Result aggregation
  - `room_aggregator.py`
  - `building_aggregator.py`

**Rules**:
- Domain knowledge about IEQ standards
- Pure functions where possible
- Pluggable evaluators (strategy pattern)
- Comprehensive test coverage

**Example**: `EN16798Evaluator` knows how to check temperature compliance.

### Reporting Layer (`core/reporting/`)

**Purpose**: Report generation from templates

**Contains**:
- **template_engine/**: YAML template processing
  - `template_loader.py`
  - `template_validator.py`
  - `analytics_resolver.py`  # Maps template requirements to analytics
- **renderers/**: Output format rendering
  - `html_renderer.py`
  - `pdf_renderer.py`
- **charts/**: Chart generation
  - `compliance_chart.py`
  - `heatmap_chart.py`
  - `line_chart.py`
  - `bar_chart.py`
- **sections/**: Section renderers
  - `summary_section.py`
  - `charts_section.py`
  - `recommendations_section.py`

**Rules**:
- Reads YAML templates
- Validates analytics requirements
- Auto-executes missing analytics
- Generates HTML/PDF output

**Flow**:
1. Load YAML template
2. Validate requirements → Identify missing analytics
3. Execute missing analytics if data available
4. Render report sections
5. Output HTML/PDF

## Key Design Patterns

### 1. Strategy Pattern (Analytics Evaluators)
```python
class IEvaluator(Protocol):
    def evaluate(self, data: TimeSeriesData) -> EvaluationResult: ...

class EN16798Evaluator(IEvaluator): ...
class BR18Evaluator(IEvaluator): ...
```

### 2. Factory Pattern (Evaluator Creation)
```python
class EvaluatorFactory:
    def create(self, standard_id: str) -> IEvaluator: ...
```

### 3. Repository Pattern (Data Access)
```python
class IAnalysisRepository(Protocol):
    def save(self, result: AnalysisResult) -> None: ...
    def load(self, building_id: str) -> AnalysisResult: ...
```

### 4. Builder Pattern (Report Construction)
```python
builder = ReportBuilder()
report = (builder
    .with_template("building_detailed")
    .with_data(analysis_result)
    .with_format("html")
    .build())
```

### 5. Chain of Responsibility (Data Filters)
```python
filter_chain = (TimeRangeFilter()
    .then(OpeningHoursFilter())
    .then(SeasonalFilter()))
filtered_data = filter_chain.apply(data)
```

## Data Flow

### Analysis Flow
```
CSV/Excel Files
    ↓
[DataLoader] → BuildingDataset
    ↓
[AnalysisEngine] → Apply filters
    ↓
[Evaluators] → Check compliance
    ↓
[Aggregators] → Roll up results
    ↓
AnalysisResult (JSON)
```

### Report Generation Flow
```
YAML Template
    ↓
[TemplateValidator] → Check requirements
    ↓
[AnalyticsResolver] → Map to analytics tags
    ↓
[RequirementChecker] → Identify missing
    ↓
[AnalyticsOrchestrator] → Execute missing
    ↓
[TemplateRenderer] → Generate HTML
    ↓
[PDFGenerator] → Convert to PDF (optional)
    ↓
Report Output
```

## Type System

### Core Types
```python
# Value Objects
class Temperature(BaseModel):
    value: float
    unit: Literal["celsius", "fahrenheit"] = "celsius"

# Entities
class Room(BaseModel):
    id: str
    name: str
    measurements: List[Measurement]

    def add_measurement(self, m: Measurement) -> None: ...

# Results
class ComplianceResult(BaseModel):
    compliant: bool
    compliance_rate: float
    violations: List[Violation]
```

### Enums
```python
class StandardType(str, Enum):
    EN16798_1 = "en16798-1"
    BR18 = "br18"
    DANISH_GUIDELINES = "danish-guidelines"

class ParameterType(str, Enum):
    TEMPERATURE = "temperature"
    CO2 = "co2"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
```

## Testing Strategy

### 1. Unit Tests
- Test each class in isolation
- Mock all external dependencies
- Fast (<1s total)

### 2. Integration Tests
- Test layer interactions
- Use test fixtures
- Moderate speed (<10s total)

### 3. End-to-End Tests
- Full workflow tests
- Real file operations (tmp directories)
- Slower but comprehensive

### Test Structure
```
tests/
├── unit/
│   ├── domain/
│   ├── analytics/
│   └── reporting/
├── integration/
│   ├── test_analysis_flow.py
│   └── test_report_generation.py
├── e2e/
│   └── test_full_workflow.py
└── fixtures/
    ├── sample_data.csv
    └── sample_report_template.yaml
```

## Configuration Management

### Standards Configuration
```yaml
# config/standards/en16798-1/temperature_category_1.yaml
standard_id: en16798-1
test_id: cat_i_temperature
category: I
parameter: temperature
limits:
  lower: 20.0
  upper: 24.0
period: heating_season
filter: opening_hours
```

### Report Templates
```yaml
# config/report_templates/building_detailed.yaml
template_id: building_detailed
name: Building Detailed Report
analytics_requirements:
  analytics_tags:
    - statistics.basic
    - compliance.overall
  required_parameters:
    - temperature
    - co2
sections:
  - section_id: compliance_overview
    type: charts
    charts:
      - id: compliance_chart
        analytics_tags: [compliance.overall]
```

## Extension Points

### Adding New Standards
1. Create YAML files in `config/standards/new_standard/`
2. Create evaluator in `analytics/evaluators/new_standard_evaluator.py`
3. Register in `analytics/evaluators/__init__.py`

### Adding New Charts
1. Create chart class in `reporting/charts/new_chart.py`
2. Implement `IChartRenderer` interface
3. Register in `reporting/charts/__init__.py`

### Adding New Report Sections
1. Create section renderer in `reporting/sections/new_section.py`
2. Implement `ISectionRenderer` interface
3. Register in `reporting/sections/__init__.py`

## Performance Considerations

### Data Loading
- Stream large files (chunked reading)
- Lazy evaluation where possible
- Caching for repeated access

### Analytics
- Vectorized operations (NumPy/Pandas)
- Parallel processing for independent rooms
- Incremental aggregation

### Report Generation
- Template caching
- Chart generation parallelization
- Async I/O for file operations

## Security Considerations

- Input validation at boundaries
- No execution of user-provided code
- Safe YAML loading (no `!!python` tags)
- Path traversal prevention
- Resource limits (memory, CPU time)
