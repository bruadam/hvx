# YAML Analytics and Interactive Reporting Guide

## Overview

The IEQ Analytics CLI now supports user-defined analytics tests from YAML configuration files and interactive chart selection for custom reports. This enables advanced customization of IEQ analysis workflows.

## New Features

### 🧪 YAML-Based Analytics Tests

Run custom IEQ tests defined in `config/tests.yaml` on mapped room data.

#### Available Commands

1. **List Available Tests**
   ```bash
   ieq-analytics report tests
   ```
   - Shows all configured analytics tests
   - Displays parameters, thresholds, and periods
   - Export options: `--format [table|json|yaml]`

2. **Run YAML Tests**
   ```bash
   ieq-analytics report from-yaml
   ```
   - Executes tests on mapped room data
   - Generates compliance charts
   - Supports multiple output formats

3. **Interactive Test Selection**
   ```bash
   ieq-analytics report from-yaml --interactive
   ```
   - Choose specific tests to run
   - Custom test combinations

### 📊 Enhanced Report Generation

New options for customizing reports with specific analytics and charts.

#### Interactive Chart Selection
```bash
ieq-analytics report generate --interactive
```
- Choose which charts to include
- Select specific analytics tests
- Custom report templates

#### Test-Specific Reports
```bash
ieq-analytics report generate --test-selection temp_comfort_all_year_opening --test-selection co2_1000_all_year_opening
```

#### Chart-Specific Reports
```bash
ieq-analytics report generate --chart-selection overview --chart-selection temperature_compliance
```

## YAML Configuration Structure

### Test Definition Format
```yaml
analytics:
  test_id:
    description: "Human-readable description"
    feature: temperature|co2|humidity|combined
    period: all_year|spring|summer|autumn|winter
    filter: opening_hours|non_opening_hours|morning|afternoon|evening
    mode: bidirectional|unidirectional_ascending
    limits:
      lower: 20    # For bidirectional
      upper: 26
    # OR
    limit: 1000    # For unidirectional
```

### Supported Features

#### Temperature Tests
- **Bidirectional**: 20-26°C comfort range
- **Unidirectional**: < 26°C overheating limits
- **Periods**: Seasonal variations
- **Filters**: Opening hours, time of day

#### CO2 Tests
- **Unidirectional**: < 1000ppm, < 2000ppm limits
- **Periods**: Seasonal and daily variations
- **Filters**: Opening hours, time-based

#### Humidity Tests
- **Bidirectional**: 30-60% comfort range
- **Periods**: All year analysis
- **Filters**: Various time periods

#### Combined Tests
- **Optimal Comfort**: Temperature 21-24°C AND CO2 < 800ppm
- **Multi-parameter**: Complex conditions

### Period Definitions
- `all_year`: Full year analysis
- `spring`: March, April, May
- `summer`: June, July, August
- `autumn`: September, October, November
- `winter`: December, January, February

### Filter Definitions
- `opening_hours`: Weekdays 8:00-16:00
- `non_opening_hours`: Evenings, nights, weekends
- `morning`: 6:00-12:00
- `afternoon`: 12:00-18:00
- `evening`: 18:00-24:00

## Usage Examples

### 1. Quick Test Overview
```bash
# List all available tests
ieq-analytics report tests

# Export test list
ieq-analytics report tests --export-list tests.json --format json
```

### 2. Run Specific Tests
```bash
# Temperature comfort during opening hours
ieq-analytics report from-yaml --test-ids temp_comfort_all_year_opening

# Multiple tests
ieq-analytics report from-yaml --test-ids temp_comfort_summer_opening --test-ids co2_1000_summer_opening

# Interactive selection
ieq-analytics report from-yaml --interactive
```

### 3. Custom Reports
```bash
# Report with specific test results
ieq-analytics report generate --test-selection temp_comfort_all_year_opening --format pdf

# Interactive report customization
ieq-analytics report generate --interactive

# Chart-specific report
ieq-analytics report generate --chart-selection temperature_compliance --chart-selection co2_compliance
```

### 4. Advanced Workflows
```bash
# 1. Run custom tests
ieq-analytics report from-yaml --test-ids comfort_optimal_opening --create-charts

# 2. Generate custom report
ieq-analytics report generate --test-selection comfort_optimal_opening --ai-analysis --format pdf
```

## Output Formats

### Test Results
- **JSON**: Detailed machine-readable results
- **CSV**: Tabular format for analysis
- **YAML**: Human-readable configuration format

### Charts
- **Compliance Charts**: Bar charts showing % compliance by room
- **Distribution Charts**: Histograms of parameter values
- **Auto-generated**: Created with each test run

### Reports
- **PDF**: Professional documents
- **HTML**: Interactive web reports
- **Markdown**: Documentation format

## Data Sources

### Input Data
- **Mapped Room Data**: `output/mapped/mapped_data/*.csv`
- **Format**: DateTime, temperature, humidity, co2 columns
- **58 Rooms**: Across 3 buildings

### Configuration
- **Analytics Rules**: `config/tests.yaml`
- **21 Predefined Tests**: Temperature, CO2, humidity, combined
- **Customizable**: Add your own test definitions

## Results Structure

### Test Results Format
```json
{
  "test_id": {
    "test_id": "temp_comfort_all_year_opening",
    "description": "Temperature 20-26°C (all year, opening hours)",
    "feature": "temperature",
    "status": "passed",
    "results": {
      "room_name": {
        "compliance_rate": 93.6,
        "total_readings": 2357,
        "in_range_readings": 2207,
        "min_value": 17.9,
        "max_value": 26.9,
        "mean_value": 22.2,
        "threshold_lower": 20,
        "threshold_upper": 26,
        "mode": "bidirectional"
      }
    },
    "summary": {
      "rooms_analyzed": 58,
      "total_readings": 136440,
      "average_compliance": 89.2,
      "min_compliance": 76.5,
      "max_compliance": 97.8
    }
  }
}
```

## Integration with Existing Features

### Performance Score Weights
```bash
# Custom weights in report generation
ieq-analytics report generate --weight-temperature 0.4 --weight-co2 0.3 --weight-humidity 0.2 --weight-data-quality 0.1
```

### AI Analysis
```bash
# Include AI analysis of YAML test results
ieq-analytics report generate --test-selection temp_comfort_all_year_opening --ai-analysis --interactive-review
```

### Weight Configuration
```bash
# View current weights
ieq-analytics report weights

# Update and save weights
ieq-analytics report weights --weight-co2 0.5 --weight-temperature 0.25 --save-config
```

## Best Practices

### 1. Test Selection Strategy
- Start with broad tests (all_year, opening_hours)
- Narrow down to specific periods/conditions
- Combine related tests for comprehensive analysis

### 2. Report Customization
- Use interactive mode for exploratory analysis
- Save test selections for repeated analysis
- Include AI analysis for insights

### 3. Configuration Management
- Keep tests.yaml under version control
- Document custom test definitions
- Use descriptive test IDs and descriptions

### 4. Data Quality
- Verify mapped data exists before running tests
- Check test results for reasonable compliance rates
- Use charts to visualize data distribution

## Troubleshooting

### Common Issues

#### No Data Found
```
❌ No processed room data files found
```
**Solution**: Ensure mapping has been run: `ieq-analytics map`

#### Test Fails
```
⚠️ Test temp_comfort_all_year_opening failed: ...
```
**Solution**: Check YAML syntax and feature names

#### Empty Results
```
⚠️ No tests selected
```
**Solution**: Verify test IDs exist in configuration

### Validation Commands
```bash
# Check available data
ls output/mapped/mapped_data/

# Validate configuration
ieq-analytics report tests --format yaml

# Test with single room
head -5 output/mapped/mapped_data/fl_ng_skole_11_processed.csv
```

## Future Enhancements

### Planned Features
- [ ] Custom threshold definitions in CLI
- [ ] Real-time test monitoring
- [ ] Batch test execution
- [ ] Advanced filtering options
- [ ] Test result comparison tools

### Integration Opportunities
- [ ] Export to external analysis tools
- [ ] API endpoints for test execution
- [ ] Automated reporting schedules
- [ ] Integration with building management systems

This comprehensive YAML analytics system provides powerful tools for customized IEQ analysis while maintaining compatibility with existing workflows.
