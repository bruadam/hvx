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

# Optional: Install additional packages for enhanced functionality
pip install json-logic holidays matplotlib seaborn
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
analytics = IEQAnalytics(rules_config_path="config/analytics_rules.yaml")

# Analyze with rules
results = analytics.analyze_room_data(ieq_data)
rule_results = results['rule_based_analysis']
```

### 3. CLI Usage

```bash
# Interactive column mapping
python -m ieq_analytics.cli mapping --input-file data.csv --interactive

# Analyze a room
python -m ieq_analytics.cli analyze --input-file processed_data.csv --room-id classroom1

# Run complete pipeline
python -m ieq_analytics.cli run --input-dir data/ --output-dir results/

# Generate visualizations
python -m ieq_analytics.cli analyze --input-file data.csv --visualizations --output-dir plots/
```

## Demo

Run the comprehensive demo to see all features:

```bash
python3 demo.py
```

This will demonstrate:
- Sample data generation
- Complete analytics pipeline
- Rule-based evaluation
- CLI usage examples

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
    ├── analytics_rules.yaml    # Rule definitions
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

```bash
# Run the demo
python3 demo.py

# Test CLI commands
python -m ieq_analytics.cli --help

# Test with sample data
python -c "from ieq_analytics import IEQAnalytics; print('✅ Import successful')"
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