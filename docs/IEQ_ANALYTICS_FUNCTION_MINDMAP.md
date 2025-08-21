# 🧠 IEQ Analytics Repository Function Mindmap

## 📁 **Repository Structure & Function Hierarchy**

```
ieq-analytics/
├── 🏗️ **Core Architecture**
│   ├── 📊 **Data Models** (models.py)
│   │   ├── Room(BaseModel)
│   │   │   ├── validate_non_empty_strings()
│   │   │   └── validate_tags()
│   │   ├── Building(BaseModel)
│   │   │   ├── validate_non_empty_strings()
│   │   │   ├── validate_rooms_belong_to_building()
│   │   │   ├── add_room()
│   │   │   └── get_room()
│   │   ├── IEQData(BaseModel)
│   │   │   ├── validate_dataframe()
│   │   │   ├── extract_data_period()
│   │   │   ├── get_measurement_columns()
│   │   │   ├── get_data_completeness()
│   │   │   └── resample_data()
│   │   └── ColumnMapping(BaseModel)
│   │       └── validate_mappings()
│   │
│   ├── 🔧 **Enums & Constants** (enums.py)
│   │   ├── IEQParameter(Enum)
│   │   │   ├── get_measurement_parameters()
│   │   │   └── get_metadata_parameters()
│   │   ├── DataResolution(Enum)
│   │   ├── ComfortCategory(Enum)
│   │   ├── RoomType(Enum)
│   │   └── DEFAULT_COLUMN_MAPPINGS
│   │
│   └── 🛠️ **Utilities** (utils.py)
│       ├── sanitize_correlation_value()
│       ├── sanitize_correlation_matrix()
│       ├── safe_numeric_operation()
│       ├── validate_numeric_series()
│       ├── clean_numeric_data()
│       ├── format_percentage()
│       ├── safe_division()
│       ├── calculate_data_completeness()
│       └── detect_time_gaps()
│
├── 🗂️ **Data Processing Pipeline**
│   ├── 📥 **Data Mapping** (mapping.py)
│   │   └── DataMapper
│   │       ├── 🔍 **Analysis Functions**
│   │       │   ├── analyze_files() → file structure analysis
│   │       │   ├── _extract_building_hint() → building detection
│   │       │   └── _extract_room_hint() → room identification
│   │       ├── 🎯 **Mapping Functions**
│   │       │   ├── suggest_column_mappings() → auto-mapping
│   │       │   ├── interactive_column_mapping() → user interaction
│   │       │   └── map_file() → file transformation
│   │       ├── ✅ **Validation Functions**
│   │       │   ├── _validate_hourly_resolution() → time validation
│   │       │   └── _create_building_id() → ID standardization
│   │       ├── 🏭 **Processing Functions**
│   │       │   └── process_directory() → batch processing
│   │       └── 💾 **Configuration**
│   │           ├── save_config() → persist mappings
│   │           └── load_config() → load mappings
│   │
│   └── 🌬️ **Ventilation Analysis** (ventilation_rate_predictor.py)
│       └── VentilationRatePredictor
│           ├── find_decay_periods() → CO2 decay detection
│           ├── filter_outside_opening_hours() → time filtering
│           ├── calculate_ach() → air change rate calculation
│           └── predict_ventilation_rate() → ventilation assessment
│
├── 🔬 **Analytics Engine**
│   ├── 📈 **Main Analytics** (analytics.py)
│   │   └── IEQAnalytics
│   │       ├── 🏠 **Room-Level Analysis**
│   │       │   ├── analyze_room_data() → comprehensive room analysis
│   │       │   ├── _analyze_data_quality() → quality assessment
│   │       │   ├── _calculate_basic_statistics() → descriptive stats
│   │       │   ├── _analyze_comfort_compliance() → EN 16798-1 compliance
│   │       │   ├── _analyze_temporal_patterns() → time-based patterns
│   │       │   ├── _analyze_correlations() → parameter relationships
│   │       │   ├── _detect_outliers() → anomaly detection
│   │       │   └── _generate_recommendations() → actionable insights
│   │       ├── 🏢 **Building-Level Analysis**
│   │       │   ├── aggregate_building_analysis() → building aggregation
│   │       │   └── _generate_building_recommendations() → building insights
│   │       ├── 🎨 **Visualization**
│   │       │   └── generate_visualizations() → plot generation
│   │       ├── 📊 **Export Functions**
│   │       │   └── export_analysis_results() → multi-format export
│   │       └── 📋 **Standards Compliance**
│   │           ├── _analyze_with_rules() → custom rules
│   │           └── _analyze_en_standard() → EN 16798-1 standard
│   │
│   └── 📏 **Rule-Based Analytics** (rule_builder.py)
│       ├── RuleBuilder
│       │   ├── temperature_threshold() → temp rule builder
│       │   ├── humidity_threshold() → humidity rule builder
│       │   ├── co2_threshold() → CO2 rule builder
│       │   ├── build() → rule compilation
│       │   └── create_comfort_rule() → comfort rule factory
│       ├── AnalyticsFilter
│       │   ├── load_config() → filter configuration
│       │   └── get_holidays() → holiday detection
│       └── AnalyticsEngine
│           ├── 🔍 **Rule Evaluation**
│           │   ├── evaluate_rule() → JSON-logic rule execution
│           │   ├── analyze_comfort_compliance() → custom rule compliance
│           │   ├── analyze_all_rules() → comprehensive rule analysis
│           │   └── analyze_en_standard() → standard compliance
│           ├── 🎛️ **Data Filtering**
│           │   ├── _apply_filters() → temporal/seasonal filtering
│           │   ├── _evaluate_range_rule() → range-based rules
│           │   └── _evaluate_single_limit_rule() → threshold rules
│           └── 🧮 **Rule Processing**
│               ├── _map_features() → feature mapping
│               └── _process_periods() → seasonal processing
│
└── 💻 **Command Line Interface**
    └── **CLI Commands** (cli.py)
        ├── 🗂️ **Data Management**
        │   ├── mapping() → raw data mapping
        │   ├── inspect() → data structure analysis
        │   └── init_config() → configuration initialization
        ├── 🔬 **Analysis Operations**
        │   ├── analyze() → comprehensive analysis
        │   └── run() → complete pipeline execution
        └── 🎛️ **CLI Framework**
            └── cli() → main command group
```

## 🔄 **Function Call Flow & Dependencies**

### **📊 Data Processing Pipeline Flow**
```
Raw CSV Files
    ↓
[inspect()] → analyze_files() → suggest_column_mappings()
    ↓
[mapping()] → interactive_column_mapping() → map_file() → process_directory()
    ↓
Standardized IEQ Data (English columns)
    ↓
[analyze()] → analyze_room_data() → comprehensive analysis
    ↓
Building Aggregation → export_analysis_results()
    ↓
JSON/CSV/PDF Reports + Visualizations
```

### **🔍 Analysis Function Dependencies**
```
analyze_room_data()
├── _analyze_data_quality()
│   ├── detect_time_gaps() [utils]
│   └── calculate_data_completeness() [utils]
├── _calculate_basic_statistics()
│   ├── safe_numeric_operation() [utils]
│   └── validate_numeric_series() [utils]
├── _analyze_comfort_compliance()
│   └── sanitize_correlation_value() [utils]
├── _analyze_temporal_patterns()
├── _analyze_correlations()
│   └── sanitize_correlation_matrix() [utils]
├── _detect_outliers()
├── _analyze_with_rules()
│   └── AnalyticsEngine.analyze_all_rules()
│       ├── analyze_comfort_compliance()
│       │   ├── _apply_filters()
│       │   ├── _evaluate_range_rule()
│       │   └── _evaluate_single_limit_rule()
│       └── analyze_en_standard()
├── VentilationRatePredictor.predict_ventilation_rate()
│   ├── find_decay_periods()
│   ├── filter_outside_opening_hours()
│   └── calculate_ach()
└── _generate_recommendations()
```

## 🎯 **Function Categories & Use Cases**

### **🔧 Core Infrastructure Functions**
- **When to call**: System initialization, data validation
- **Functions**: Model validators, enum getters, utility functions
- **Dependencies**: Base Pydantic models, pandas operations

### **📥 Data Ingestion & Mapping Functions**
- **When to call**: Processing raw CSV files from sensors
- **Functions**: `mapping()`, `inspect()`, `process_directory()`
- **Dependencies**: File system access, user interaction (optional)

### **🔬 Analytics Functions**
- **When to call**: After data mapping, for comprehensive analysis
- **Functions**: `analyze()`, `analyze_room_data()`, rule evaluation
- **Dependencies**: Mapped data, configuration files, rules engine

### **📊 Export & Visualization Functions**
- **When to call**: After analysis completion
- **Functions**: `export_analysis_results()`, `generate_visualizations()`
- **Dependencies**: Analysis results, output directories

### **🎛️ CLI Orchestration Functions**
- **When to call**: User interactions, automation scripts
- **Functions**: `run()` (complete pipeline), individual commands
- **Dependencies**: All above function categories

## 🔗 **Inter-Module Dependencies**

```
CLI ←→ Analytics ←→ Rule Builder
 ↓         ↓           ↓
Models ←→ Mapping ←→ Utils
 ↓         ↓           ↓
Enums ←→ Climate ←→ Ventilation
```

## 📈 **Function Complexity Levels**

### **🟢 Simple Functions** (Direct utility, single purpose)
- Validators, formatters, basic calculations
- Examples: `validate_numeric_series()`, `format_percentage()`

### **🟡 Medium Functions** (Processing with dependencies)
- Data mapping, file processing, basic analysis
- Examples: `map_file()`, `_calculate_basic_statistics()`

### **🔴 Complex Functions** (Orchestration, multiple dependencies)
- Complete analysis, rule evaluation, pipeline execution
- Examples: `analyze_room_data()`, `run()`, `analyze_all_rules()`

## 🎪 **Entry Points for Different Use Cases**

### **📊 Data Scientist / Analyst**
```python
# Quick analysis workflow
from ieq_analytics import IEQAnalytics, DataMapper

mapper = DataMapper()
mapper.process_directory("raw_data/", "mapped_data/")

analytics = IEQAnalytics()
results = analytics.analyze_room_data(ieq_data)
```

### **🤖 Automation / CI/CD**
```bash
# Complete pipeline automation
python -m ieq_analytics.cli run \
  --data-dir raw_data/ \
  --output-dir results/ \
  --no-interactive
```

### **🔧 Configuration Management**
```bash
# Setup and inspection
python -m ieq_analytics.cli init_config
python -m ieq_analytics.cli inspect --data-dir-path raw_data/
```

### **📈 Custom Analysis**
```python
# Advanced rule-based analysis
from ieq_analytics.rule_builder import RuleBuilder, AnalyticsEngine

builder = RuleBuilder()
rule = builder.temperature_threshold(20, 26).build()

engine = AnalyticsEngine("custom_rules.yaml")
results = engine.analyze_all_rules(ieq_data)
```
