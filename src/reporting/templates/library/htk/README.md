# HTK (Høje-Taastrup Kommune) Report Template

This template generates comprehensive building performance analysis reports specifically designed for Høje-Taastrup Kommune's requirements.

## Overview

The HTK report template provides:

- **Data Quality Assessment**: Evaluation of data completeness and quality for each location
- **Building-Specific Analysis**: Performance metrics and top issue identification per building
- **Room-Level Details**: Individual room analysis with period and seasonal breakdowns
- **Compliance Analysis**: Non-compliant hours during opening and non-opening times
- **Recommendations**: Actionable improvement suggestions based on analysis results

## Features

### Report Sections

1. **Executive Summary**
   - Overall performance metrics
   - Building comparison charts
   - High-level insights

2. **Data Quality Assessment**
   - Data completeness tables
   - Missing periods identification
   - Quality scores per building

3. **Building Analysis** (repeated for each building)
   - Top 10 rooms with most issues
   - Building-level performance metrics
   - Non-compliant hours analysis
   - Room-specific analysis with tables and charts

4. **Recommendations**
   - Priority matrix for improvements
   - Cost-benefit analysis
   - Implementation phases

### Charts Generated

- Building performance comparison
- Data completeness heatmap
- Top issues ranking per building
- Non-compliant hours scatter plots (opening vs non-opening hours)
- Room-level trend analysis (yearly, seasonal, daily patterns)
- Priority matrix for recommendations
- Cost-benefit analysis

## Usage

### Via CLI

```bash
# Generate HTK report for all buildings
ieq-analytics report htk --data-dir output/analysis --output-dir output/reports/htk

# Generate for specific buildings
ieq-analytics report htk --buildings "Building A" --buildings "Building B"

# Generate in multiple formats
ieq-analytics report htk --format html --format pdf
```

### Via Python API

```python
from ieq_analytics.reporting.templates.library.htk import create_htk_template

# Create template instance
htk_template = create_htk_template()

# Generate report
result = htk_template.generate_report(
    data_dir=Path("output/analysis"),
    output_dir=Path("output/reports/htk"),
    buildings=["Building A", "Building B"],  # Optional: specific buildings
    export_formats=["pdf", "html"]
)

print(f"Report generated: {result['success']}")
print(f"Files: {result['files']}")
```

## Configuration

The template uses configuration from:

- `config.yaml`: Main template configuration
- `template.html`: Jinja2 HTML template
- `charts.py`: Chart generation functions
- `tests.yaml`: Analysis rules (referenced via data mapping)

## Data Requirements

The template expects analyzed data in the format produced by the IEQ Analytics engine:

### Input Data Structure

```
output/analysis/
├── building_a_analysis.json
├── building_b_analysis.json
└── building_c_analysis.json
```

### Analysis File Format

Each building analysis file should contain:

```json
{
  "building_name": "Building A",
  "rooms": {
    "Room 101": {
      "test_results": {
        "co2_1000_all_year_opening": {
          "compliance_rate": 0.85,
          "violations_count": 120,
          "mean": 950
        },
        "temp_comfort_all_year_opening": {
          "compliance_rate": 0.92,
          "violations_count": 45,
          "mean": 23.2
        }
      },
      "statistics": {
        "co2": {"mean": 950, "std": 200},
        "temperature": {"mean": 23.2, "std": 1.5}
      }
    }
  },
  "data_quality": {
    "completeness": 98.5,
    "missing_periods": "2 days in March"
  }
}
```

## Template Configuration

### Key Configuration Options

```yaml
# config.yaml
template:
  id: "htk_report"
  name: "Høje-Taastrup Kommune Report"
  category: "municipal"

# Chart configurations
charts:
  performance_overview:
    type: "performance_overview"
    config:
      metrics: ["co2_compliance", "temperature_compliance"]
      thresholds:
        co2: 1000
        temperature_min: 20
        temperature_max: 26

# Data mapping to tests.yaml
data_mapping:
  co2_tests:
    opening_hours: "co2_1000_all_year_opening"
    seasonal:
      spring: "co2_1000_spring_opening"
      summer: "co2_1000_summer_opening"
      autumn: "co2_1000_autumn_opening"
      winter: "co2_1000_winter_opening"
```

## Output Files

The template generates:

### HTML Report
- `htk_report.html`: Interactive HTML version with embedded charts

### PDF Report  
- `htk_report.pdf`: Print-ready PDF version (requires HTML to PDF conversion)

### Charts Directory
- Individual chart files as PNG/SVG in the charts subdirectory
- Organized by chart type and building

## Customization

### Adding New Chart Types

1. Define chart configuration in `config.yaml`
2. Implement chart generation in `charts.py`
3. Update HTML template to include the new chart
4. Reference the chart in the appropriate section

### Modifying Analysis Rules

The template references analysis rules from `config/tests.yaml`. To modify:

1. Update test definitions in `tests.yaml`
2. Update `data_mapping` in `config.yaml` to reference new test IDs
3. Regenerate analysis data using the updated rules

### Styling and Layout

- Modify `template.html` for layout changes
- Update CSS styles in the `<style>` section
- Chart styling can be modified in `charts.py`

## Dependencies

- Python 3.8+
- matplotlib, seaborn (for charts)
- jinja2 (for HTML templating)
- pandas, numpy (for data processing)
- pydantic (for data validation)

## Danish Localization

The template includes Danish language support:

- All labels and descriptions in Danish
- Month and season names in Danish
- Number formatting following Danish conventions
- Danish-specific color schemes and styling

## Troubleshooting

### Common Issues

1. **Missing Analysis Data**: Ensure `ieq-analytics analyze` has been run first
2. **Import Errors**: Check that all required packages are installed
3. **Chart Generation Failures**: Verify matplotlib backend configuration
4. **Template Rendering Issues**: Check Jinja2 template syntax

### Debug Mode

Enable debug output by setting the debug flag:

```bash
ieq-analytics --debug report htk
```

This will show detailed error information and stack traces.

## Version History

- **1.0.0**: Initial HTK template implementation
  - Basic report structure
  - Chart generation
  - Danish localization
  - CLI integration

## Contributing

To contribute to the HTK template:

1. Follow the existing code structure
2. Add appropriate Danish translations
3. Include unit tests for new functionality
4. Update this documentation

## License

This template is part of the IEQ Analytics project and follows the same license terms.
