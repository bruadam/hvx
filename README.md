# IEQ Analytics Engine

A comprehensive Python package for Indoor Environmental Quality (IEQ) data analysis with rule-based evaluation and CLI interface.

## Features

### 🏢 Core Analytics
- **Comprehensive IEQ Analysis**: Temperature, humidity, CO2, PM2.5, noise analysis
- **Statistical Analysis**: Mean, median, std dev, percentiles, trends
- **Comfort Assessment**: Multi-category comfort evaluation (thermal, air quality, acoustic)
- **Data Quality Assessment**: Completeness, accuracy, outlier detection
- **Temporal Pattern Analysis**: Hourly, daily, weekly patterns
- **Correlation Analysis**: Cross-parameter relationships with sanitized correlation matrices

### 📋 Rule-Based System
- **JSON-Logic Integration**: Flexible, configurable rule evaluation
- **YAML Configuration**: Easy-to-edit rule definitions
- **EN 16798-1 Compliance**: European standard for IEQ assessment
- **Custom Rules**: Build complex conditions with the RuleBuilder API
- **Time-Based Filtering**: Working hours, weekdays, holiday exclusions

### 🛠️ Data Processing
- **Intelligent Column Mapping**: Interactive and automated CSV column detection
- **Multiple File Formats**: CSV, Excel support with automatic parsing
- **Data Validation**: Pydantic v2 models for robust data validation
- **Missing Data Handling**: Smart interpolation and gap detection

### 💻 CLI Interface
- **Interactive Mapping**: Step-by-step column mapping wizard
- **Batch Processing**: Analyze multiple files and rooms
- **Export Options**: JSON, CSV, HTML reports
- **Visualization Generation**: Automatic plot creation

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd ieq-analytics/analytics

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Basic Analysis

```python
import pandas as pd
from ieq_analytics import IEQAnalytics, IEQData

# Load your data
data = pd.DataFrame({
    'temperature': [22.0, 23.5, 21.0, 25.0],
    'humidity': [45.0, 50.0, 40.0, 65.0],
    'co2': [400.0, 500.0, 600.0, 700.0]
}, index=pd.date_range('2024-01-01 09:00', periods=4, freq='h'))

# Create IEQ data object
ieq_data = IEQData(
    data=data,
    room_id="classroom_1",
    building_id="school_main"
)

# Initialize analytics engine
analytics = IEQAnalytics()

# Perform analysis
results = analytics.analyze_room_data(ieq_data)

# Access results
print(f"Temperature mean: {results['basic_statistics']['temperature']['mean']:.1f}°C")
print(f"Data quality score: {results['data_quality']['overall_score']}")
for rec in results['recommendations']:
    print(f"- {rec}")
```

### 2. Rule-Based Analysis

```python
from ieq_analytics.rule_builder import RuleBuilder, AnalyticsEngine

# Create custom comfort rule
builder = RuleBuilder()
custom_rule = (builder
    .temperature_threshold(min_temp=20, max_temp=25)
    .humidity_threshold(min_humidity=30, max_humidity=60)
    .co2_threshold(max_co2=800)
    .build())

# Or use pre-built standard rules
standard_rule = RuleBuilder.create_comfort_rule(
    temperature_range=(21, 26),
    humidity_range=(40, 70),
    co2_max=1000
)

# Initialize analytics engine with rules
analytics = IEQAnalytics(rules_config_path="config/tests.yaml")

# Analyze with rules
results = analytics.analyze_room_data(ieq_data)
rule_results = results['rule_based_analysis']
```

### 3. CLI Usage

The IEQ Analytics CLI provides a comprehensive command-line interface with project management, data processing, analysis, and reporting capabilities.

#### 🚀 Quick Start with CLI

```bash
# Initialize a new project workspace
python -m ieq_analytics.cli project init --name "my-ieq-study" --template basic

# Check project status and get recommendations
python -m ieq_analytics.cli project status

# Map raw CSV files to standardized format (interactive)
python -m ieq_analytics.cli mapping --interactive

# Run comprehensive analysis
python -m ieq_analytics.cli analyze --generate-plots

# Generate professional reports
python -m ieq_analytics.cli report generate --format pdf --template executive
```

#### 📁 Project Management

```bash
# Initialize different project types
python -m ieq_analytics.cli project init --name "office-study" --template advanced
python -m ieq_analytics.cli project init --name "research-project" --template research

# Monitor project progress
python -m ieq_analytics.cli project status

# Configure project settings interactively
python -m ieq_analytics.cli project config
```

#### 🗂️ Data Processing

```bash
# Interactive column mapping with batch processing
python -m ieq_analytics.cli mapping --data-dir-path data/raw/ --interactive --batch-size 20

# Inspect CSV file structure before mapping
python -m ieq_analytics.cli inspect --data-dir-path data/raw/ --output-format table

# Automated mapping with configuration
python -m ieq_analytics.cli mapping --no-interactive --config-path config/mapping_config.json
```

#### 🔬 Analysis & Visualization

```bash
# Comprehensive analysis with multiple export formats
python -m ieq_analytics.cli analyze --parallel --export-formats json csv excel

# Analysis with custom rules configuration
python -m ieq_analytics.cli analyze --rules-config config/custom_rules.yaml --generate-plots

# Generate visualizations only
python -m ieq_analytics.cli analyze --generate-plots --no-analysis
```

#### 📊 Report Generation

```bash
# Executive summary report
python -m ieq_analytics.cli report generate --template executive --format pdf

# Technical report with AI-powered chart analysis
python -m ieq_analytics.cli report generate --template technical --ai-analysis --interactive-review

# Quick HTML report
python -m ieq_analytics.cli report generate --format html --include-plots
```

#### 🚀 Complete Pipeline Automation

```bash
# Automated pipeline for production
python -m ieq_analytics.cli pipeline --skip-interactive --parallel-analysis

# Custom pipeline with specific directories
python -m ieq_analytics.cli pipeline --source-dir custom_data/ --output-dir results/
```

#### 🔍 Advanced Usage

```bash
# Detailed project status with metrics
python -m ieq_analytics.cli project status

# Export inspection results
python -m ieq_analytics.cli inspect --export inspection_results.json

# Initialize configuration templates
python -m ieq_analytics.cli init-config --config-path custom_config.json

# Run analysis with custom parameters
python -m ieq_analytics.cli analyze --buildings-metadata metadata.json --parallel
```

## Demo & Getting Started

### Quick Demo

Run the comprehensive demo to see all features:

```bash
python3 demo.py
```

### CLI Demo

Try the CLI with sample commands:

```bash
# Initialize a demo project
python -m ieq_analytics.cli project init --name "demo-project" --template basic

# Check project status
python -m ieq_analytics.cli project status

# Inspect sample data (if available)
python -m ieq_analytics.cli inspect --data-dir-path data/raw/

# Run complete pipeline (if data is available)
python -m ieq_analytics.cli pipeline
```

### Step-by-Step Tutorial

1. **Project Setup**:
   ```bash
   python -m ieq_analytics.cli project init --name "my-ieq-analysis" --template research
   cd my-ieq-analysis
   ```

2. **Add Your Data**:
   ```bash
   # Copy your CSV files to data/raw/
   cp /path/to/your/sensor_data*.csv data/raw/
   ```

3. **Check Status**:
   ```bash
   python -m ieq_analytics.cli project status
   ```

4. **Map Your Data**:
   ```bash
   python -m ieq_analytics.cli mapping --interactive
   ```

5. **Run Analysis**:
   ```bash
   python -m ieq_analytics.cli analyze --generate-plots --parallel
   ```

6. **Generate Report**:
   ```bash
   python -m ieq_analytics.cli report generate --format pdf --template executive
   ```

This will demonstrate:
- Complete project workspace setup
- Interactive data mapping workflow
- Comprehensive analytics pipeline
- Professional report generation
- Advanced CLI features and automation

## CLI Command Reference

### Command Structure

```bash
ieq-analytics [OPTIONS] COMMAND [ARGS]...
```

#### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `project` | Project & workspace management | `project init --name study` |
| `mapping` | Data mapping & processing | `mapping --interactive` |
| `analyze` | Comprehensive IEQ analysis | `analyze --parallel` |
| `inspect` | Data structure inspection | `inspect --export results.json` |
| `report` | Report generation | `report generate --format pdf` |
| `pipeline` | Complete automated pipeline | `pipeline --parallel-analysis` |
| `init-config` | Configuration template creation | `init-config` |

#### Project Commands

```bash
# Project initialization and management
ieq-analytics project init [OPTIONS]
  --name TEXT           Project name [required]
  --description TEXT    Project description
  --template CHOICE     Project template (basic/advanced/research)

# Project status monitoring  
ieq-analytics project status

# Configuration management
ieq-analytics project config [OPTIONS]
  --config-type CHOICE  Configuration type (mapping/analytics/all)
```

#### Data Processing Commands

```bash
# Data mapping
ieq-analytics mapping [OPTIONS]
  --data-dir-path PATH         Input directory
  --config-path PATH           Mapping configuration
  --output-dir PATH            Output directory
  --interactive/--no-interactive  Interactive mapping mode
  --room-tag TEXT              Room tag to apply
  --batch-size INTEGER         Batch processing size

# Analysis
ieq-analytics analyze [OPTIONS]
  --data-dir PATH              Mapped data directory
  --output-dir PATH            Output directory
  --buildings-metadata PATH    Buildings metadata file
  --rules-config PATH          Analytics rules configuration
  --export-formats CHOICE     Export formats (json/csv/excel/pdf)
  --generate-plots/--no-plots  Generate visualizations
  --parallel/--sequential      Processing mode

# Data inspection
ieq-analytics inspect [OPTIONS]
  --data-dir-path PATH         Directory to inspect
  --output-format CHOICE       Output format (table/json/yaml)
  --export PATH                Export results to file
```

#### Report Generation Commands

```bash
# Generate reports
ieq-analytics report generate [OPTIONS]
  --analysis-dir PATH          Analysis results directory
  --output-dir PATH            Report output directory
  --format CHOICE              Report format (html/pdf/markdown)
  --template CHOICE            Report template (executive/technical/research)
  --include-plots/--no-plots   Include visualization plots
  --ai-analysis/--no-ai-analysis        AI-powered chart analysis
  --interactive-review/--no-interactive-review  Interactive AI review
```

#### Pipeline Commands

```bash
# Complete automation
ieq-analytics pipeline [OPTIONS]
  --source-dir PATH            Source directory with raw data
  --output-dir PATH            Output directory
  --skip-interactive           Skip interactive steps
  --parallel-analysis          Enable parallel processing
```

#### Global Options

```bash
--workspace PATH    Workspace directory (default: current directory)
--version          Show version information
--help             Show help message
```

## Project Workspace Structure

When you initialize a project with `ieq-analytics project init`, the following workspace structure is created:

```
ieq-analytics-project/
├── 📁 config/                    # Configuration files
│   ├── project.json             # Project metadata
│   ├── mapping_config.json      # Data mapping configuration
│   ├── tests.yaml     # Custom analytics rules
│   └── en16798_thresholds.yaml  # EN standard thresholds
├── 📁 data/                     # Data directories
│   ├── raw/                     # Original CSV files (place your data here)
│   ├── mapped/                  # Standardized data (auto-generated)
│   ├── climate/                 # External climate data (optional)
│   └── buildings_metadata.json  # Building/room metadata (auto-generated)
├── 📁 output/                   # Analysis results
│   ├── analysis/                # Analysis results (JSON/CSV)
│   ├── reports/                 # Generated reports (PDF/HTML)
│   └── visualizations/          # Plots and charts
├── 📁 scripts/                  # Custom analysis scripts (optional)
├── 📁 docs/                     # Project documentation (optional)
└── .ieq_pipeline_state.json     # Pipeline state tracking (auto-generated)
```

### Recommended Workflow

1. **📁 Initialize Project**: `ieq-analytics project init --name "my-study"`
2. **📥 Add Data**: Copy your CSV files to `data/raw/`
3. **🗂️ Map Data**: `ieq-analytics mapping --interactive`
4. **🔬 Analyze**: `ieq-analytics analyze --generate-plots`
5. **📊 Generate Reports**: `ieq-analytics report generate --format pdf`

Or run the complete pipeline: `ieq-analytics pipeline`

### Project Templates

- **Basic**: Standard IEQ analysis with common parameters
- **Advanced**: Extended analysis with custom rules and thresholds
- **Research**: Full EN 16798-1 compliance with detailed documentation

## Configuration

### Rule Configuration (YAML)

The system uses YAML files to define analysis rules. Example:

```yaml
comfort_rules:
  basic_comfort:
    description: "Basic thermal and air quality comfort"
    category: "comfort"
    filters:
      hours: [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
      weekdays_only: true
      exclude_holidays: true
    rule:
      and:
        - ">=": [{"var": "temperature"}, 20]
        - "<=": [{"var": "temperature"}, 26]
        - ">=": [{"var": "humidity"}, 30]
        - "<=": [{"var": "humidity"}, 70]
        - "<=": [{"var": "co2"}, 800]

en_16798_rules:
  thermal_comfort:
    category_II:
      description: "EN 16798-1 Category II thermal comfort"
      standard_level: "Category II"
      parameter: "temperature"
      rule:
        and:
          - ">=": [{"var": "temperature"}, 20]
          - "<=": [{"var": "temperature"}, 26]
```

## Package Structure

```
ieq_analytics/
├── __init__.py          # Package initialization
├── models.py            # Pydantic v2 data models
├── enums.py             # IEQ parameters and comfort categories
├── analytics.py         # Main analytics engine
├── rule_builder.py      # JSON-logic rule system
├── mapping.py           # Data mapping and processing
├── utils.py             # Utility functions (correlation sanitization)
├── cli.py               # Command-line interface
└── config/
    ├── tests.yaml    # Rule definitions
    └── mapping_config.json     # Column mapping configuration
```

## API Reference

### Core Classes

#### `IEQAnalytics`
Main analytics engine with comprehensive analysis capabilities.

**Methods:**
- `analyze_room_data(ieq_data: IEQData) -> Dict[str, Any]`: Complete room analysis
- `aggregate_building_analysis(room_analyses: List[Dict]) -> Dict[str, Any]`: Building-level aggregation
- `generate_visualizations(ieq_data: IEQData, output_dir: Path) -> Dict[str, str]`: Create plots
- `export_analysis_results(results: Dict, output_path: Path, format: str)`: Export results

#### `IEQData`
Pydantic v2 model for IEQ data validation.

**Fields:**
- `room_id: str`: Room identifier
- `building_id: str`: Building identifier
- `data: pd.DataFrame`: Time-series data with datetime index
- `source_files: List[str]`: Original file paths (optional)
- `processing_timestamp: datetime`: Processing time (auto-generated)

#### `RuleBuilder`
Fluent API for creating JSON-logic rules.

**Methods:**
- `temperature_threshold(min_temp, max_temp)`: Add temperature conditions
- `humidity_threshold(min_humidity, max_humidity)`: Add humidity conditions
- `co2_threshold(max_co2)`: Add CO2 conditions
- `build()`: Return the constructed rule

#### `DataMapper`
Intelligent column mapping for CSV files.

**Methods:**
- `analyze_file(file_path: Path) -> Dict`: Analyze file structure
- `map_columns_interactive(file_path: Path) -> ColumnMapping`: Interactive mapping
- `map_columns_automatic(file_path: Path) -> ColumnMapping`: Automatic mapping
- `process_file(file_path: Path, mapping: ColumnMapping) -> IEQData`: Process with mapping

## Analysis Results Structure

```python
{
    "room_id": "classroom_1",
    "building_id": "school_main",
    "data_period": {
        "start": "2024-01-01T08:00:00",
        "end": "2024-01-01T18:00:00",
        "duration_hours": 10
    },
    "data_quality": {
        "overall_score": 0.95,
        "completeness": {...},
        "accuracy_score": 0.98
    },
    "basic_statistics": {
        "temperature": {"mean": 22.5, "std": 1.2, ...},
        "humidity": {"mean": 45.0, "std": 5.0, ...},
        "co2": {"mean": 650, "max": 1200, ...}
    },
    "comfort_analysis": {...},
    "temporal_patterns": {...},
    "correlation_analysis": {...},
    "outlier_detection": {...},
    "recommendations": ["List of recommendations"],
    "rule_based_analysis": {
        "comfort_compliance": {...},
        "en_standard_compliance": {...}
    }
}
```

## Requirements

### Core Dependencies
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **pydantic**: Data validation (v2)
- **click**: CLI framework
- **pyyaml**: YAML configuration parsing

### Optional Dependencies
- **json-logic**: Rule evaluation engine
- **holidays**: Holiday calendar support
- **matplotlib**: Plotting and visualization
- **seaborn**: Statistical visualization
- **openpyxl**: Excel file support

## Testing

### Basic Testing

```bash
# Run the demo
python3 demo.py

# Test CLI installation
python -m ieq_analytics.cli --help

# Test package import
python -c "from ieq_analytics import IEQAnalytics; print('✅ Import successful')"
```

### CLI Testing

```bash
# Test project initialization
python -m ieq_analytics.cli project init --name "test-project" --template basic

# Test project status
python -m ieq_analytics.cli project status

# Test data inspection (with sample data)
python -m ieq_analytics.cli inspect --data-dir-path data/raw/ --output-format table

# Test configuration creation
python -m ieq_analytics.cli init-config

# Test complete pipeline (if data available)
python -m ieq_analytics.cli pipeline --skip-interactive
```

### Validation Commands

```bash
# Check CLI version
python -m ieq_analytics.cli --version

# Validate workspace structure
python -m ieq_analytics.cli project status

# Test report generation capabilities
python -m ieq_analytics.cli report generate --help
```

## Advanced Features

### Custom Rule Development

```python
from ieq_analytics.rule_builder import RuleBuilder

# Complex rule with multiple conditions
builder = RuleBuilder()
complex_rule = (builder
    .temperature_threshold(min_temp=20, max_temp=26)
    .humidity_threshold(max_humidity=70)
    .co2_threshold(max_co2=800)
    .build())
```

### Building-Level Analysis

```python
# Analyze multiple rooms
room_results = []
for room_data in building_rooms:
    result = analytics.analyze_room_data(room_data)
    room_results.append(result)

# Aggregate building-level metrics
building_analysis = analytics.aggregate_building_analysis(room_results)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For questions, issues, or contributions:
- Create an issue on GitHub
- Check the documentation
- Run `python demo.py` for a complete system demonstration

## Changelog

### v1.0.0 (Latest)
- ✅ Complete Pydantic v2 migration
- ✅ JSON-logic based rule system
- ✅ Correlation sanitization utilities
- ✅ YAML configuration support
- ✅ Enhanced CLI interface
- ✅ EN 16798-1 standard compliance
- ✅ Comprehensive documentation