# Enhanced Report Template System Documentation

## Overview

The Enhanced Report Template System provides a comprehensive solution for generating HTML and PDF reports from YAML-based templates. The system automatically extracts required analytics data, validates availability, generates HTML reports, and converts them to PDF format.

## Features

- ✅ **YAML Template Parsing**: Parse and validate YAML report templates
- ✅ **Analytics Requirements**: Automatically extract and collect required analytics data
- ✅ **Data Validation**: Validate that required data is available before generating reports
- ✅ **HTML Generation**: Generate richly formatted HTML reports
- ✅ **PDF Conversion**: Convert HTML reports to PDF using weasyprint
- ✅ **Comprehensive Testing**: Full test coverage for all components
- ✅ **Flexible Configuration**: Support for multiple template types and layouts

## Architecture

### Components

1. **YAMLTemplateParser**: Parses and validates YAML template files
2. **AnalyticsDataAggregator**: Collects and aggregates required analytics data
3. **HTMLReportRenderer**: Generates HTML from templates and data
4. **PDFGenerator**: Converts HTML to PDF format
5. **EnhancedReportService**: Orchestrates the complete workflow

### Workflow

```
YAML Template → Parse & Validate → Extract Requirements
                                          ↓
                                  Collect Analytics Data
                                          ↓
                                  Validate Data Availability
                                          ↓
                                  Generate HTML Report
                                          ↓
                                  Convert to PDF (optional)
```

## YAML Template Schema

### Required Fields

```yaml
template_id: unique_template_identifier
name: Human-readable Template Name
description: Template description
```

### Optional Fields

```yaml
version: "1.0"  # Template version
author: Author Name

# Report configuration
report:
  title: Report Title
  subtitle: Report Subtitle
  format: html  # html, pdf, markdown, docx
  theme: modern  # modern, classic, minimal
  scope: building  # portfolio, building, level, room

# Page settings (for PDF)
page:
  size: A4
  orientation: portrait  # portrait, landscape
  margins:
    top: 2cm
    bottom: 2cm
    left: 2cm
    right: 2cm
```

### Analytics Requirements

Specify what analytics data is required for the template:

```yaml
analytics_requirements:
  analytics_tags:
    - statistics.basic
    - statistics.trends
    - compliance.overall
    - compliance.temporal
    - temporal.hourly
    - spatial.room_level
    - recommendations.operational
  
  required_parameters:
    - temperature
    - co2
    - humidity
  
  required_level: room  # portfolio, building, level, room
  min_data_quality: 0.6  # Minimum data quality threshold (0-1)
  min_time_range_days: 7  # Minimum time range in days
```

### Valid Analytics Tags

#### Statistics
- `statistics.basic` - Basic statistics (mean, median, std, min, max)
- `statistics.trends` - Trend analysis
- `statistics.distribution` - Distribution analysis

#### Compliance
- `compliance.overall` - Overall compliance rates
- `compliance.temporal` - Time-based compliance
- `compliance.spatial` - Space-based compliance
- `compliance.threshold` - Threshold-based compliance

#### Temporal Analysis
- `temporal.hourly` - Hourly patterns
- `temporal.daily` - Daily patterns
- `temporal.weekly` - Weekly patterns
- `temporal.monthly` - Monthly patterns
- `temporal.seasonal` - Seasonal patterns

#### Spatial Analysis
- `spatial.room_level` - Room-level analysis
- `spatial.level_level` - Level-level analysis
- `spatial.building_level` - Building-level analysis
- `spatial.comparison` - Spatial comparisons
- `spatial.ranking` - Performance rankings

#### Recommendations
- `recommendations.operational` - Operational recommendations
- `recommendations.hvac` - HVAC recommendations
- `recommendations.ventilation` - Ventilation recommendations
- `recommendations.maintenance` - Maintenance recommendations

#### Data Quality
- `data_quality.completeness` - Data completeness metrics
- `data_quality.accuracy` - Data accuracy metrics

#### Performance
- `performance.scoring` - Performance scores
- `performance.ranking` - Performance rankings

#### Weather
- `weather.correlation` - Weather correlations
- `weather.impact` - Weather impact analysis

### Valid Parameters

- `temperature` - Temperature data
- `co2` - CO2 levels
- `humidity` - Humidity levels
- `voc` - Volatile Organic Compounds
- `pm25` - PM2.5 particulate matter
- `pm10` - PM10 particulate matter
- `noise` - Noise levels
- `light` - Light levels
- `occupancy` - Occupancy data

### Sections

Define report sections:

```yaml
sections:
  - section_id: cover_page
    type: cover
    title: "Building IEQ Analysis"
    include_date: true
    include_building_name: true
  
  - section_id: summary
    type: summary
    title: "Executive Summary"
    analytics_requirements:  # Section-specific requirements
      analytics_tags:
        - statistics.basic
        - compliance.overall
    content:
      - building_metrics
      - compliance_rates
      - room_count
  
  - section_id: charts
    type: charts
    title: "Environmental Analysis"
    layout: grid  # grid, vertical, horizontal
    analytics_requirements:
      analytics_tags:
        - temporal.hourly
        - compliance.overall
    charts:
      - id: compliance_overview
        title: "Overall Compliance"
        width: full
        height: 400px
        analytics_requirements:
          analytics_tags:
            - compliance.overall
      
      - id: temperature_heatmap
        title: "Temperature Patterns"
        width: full
        height: 400px
        analytics_requirements:
          analytics_tags:
            - temporal.hourly
            - temporal.daily
          required_parameters:
            - temperature
  
  - section_id: recommendations
    type: recommendations
    title: "Recommended Actions"
    max_recommendations: 15
    priority_filter: [critical, high]
    include_evidence: true
    analytics_requirements:
      analytics_tags:
        - recommendations.operational
        - recommendations.hvac
  
  - section_id: room_details
    type: loop
    title: "Room-by-Room Analysis"
    loop_over: rooms  # rooms, levels, buildings
    view_type: cards  # cards, table
    max_iterations: 20
    sort_by: compliance_rate
    sort_order: ascending  # ascending, descending
    analytics_requirements:
      analytics_tags:
        - spatial.room_level
        - statistics.basic
```

### Section Types

1. **cover** - Cover page
2. **summary** - Summary section with key metrics
3. **text** - Text content (supports auto-generation)
4. **charts** - Chart visualizations
5. **recommendations** - Recommendations list
6. **issues** - Critical issues list
7. **table** - Data table
8. **loop** - Loop over entities (rooms, levels, buildings)

### Styling

Customize report appearance:

```yaml
style:
  primary_color: "#2196F3"
  secondary_color: "#4CAF50"
  warning_color: "#FF9800"
  critical_color: "#F44336"
  text_color: "#333333"
  background_color: "#FFFFFF"
  font_family: "Helvetica, Arial, sans-serif"
  heading_font: "Helvetica, Arial, sans-serif"
```

## Usage

### Basic Usage

```python
from pathlib import Path
from src.core.reporting.enhanced_report_service import EnhancedReportService

# Initialize service
report_service = EnhancedReportService(
    templates_dir=Path("config/report_templates"),
    output_dir=Path("output/reports"),
    enable_validation=True
)

# Generate HTML report
result = report_service.generate_report(
    template_name="building_detailed",
    analysis_results=building_analysis,
    dataset=dataset,
    weather_data=weather_data,
    output_format='html'
)

# Check result
if result['status'] == 'success':
    print(f"Report generated: {result['html_report']['path']}")
    print(f"File size: {result['html_report']['size']} bytes")
else:
    print(f"Error: {result['error']}")
```

### Generate PDF Report

```python
# Generate both HTML and PDF
result = report_service.generate_report(
    template_name="building_detailed",
    analysis_results=building_analysis,
    output_format='both'  # 'html', 'pdf', or 'both'
)

if result['status'] == 'success':
    print(f"HTML: {result['html_report']['path']}")
    if 'pdf_report' in result:
        print(f"PDF: {result['pdf_report']['output_path']}")
```

### List Available Templates

```python
templates = report_service.list_available_templates()

for template in templates:
    print(f"{template['name']}: {template['description']}")
```

### Validate Template

```python
validation = report_service.validate_template_file("building_detailed")

if validation.is_valid:
    print("Template is valid")
else:
    print("Validation errors:")
    for error in validation.errors:
        print(f"  - {error}")
```

### Get Template Requirements

```python
requirements = report_service.get_template_requirements("building_detailed")

print(f"Required analytics tags: {requirements['all_tags']}")
print(f"Required parameters: {requirements['all_parameters']}")
print(f"Required level: {requirements['required_level']}")
```

### Batch Report Generation

```python
# Generate multiple reports from different templates
results = report_service.generate_batch_reports(
    template_names=['building_detailed', 'portfolio_summary'],
    analysis_results=analysis_results,
    dataset=dataset,
    output_format='both'
)

print(f"Generated {results['successful']}/{results['total']} reports")
```

## Example Templates

### Simple Building Report

```yaml
template_id: simple_building
name: Simple Building Report
description: Basic building analysis report

analytics_requirements:
  analytics_tags:
    - statistics.basic
    - compliance.overall
  required_parameters:
    - temperature
    - co2

report:
  title: "Building Analysis Report"
  format: html
  scope: building

sections:
  - section_id: summary
    type: summary
    title: "Summary"
  
  - section_id: compliance
    type: charts
    title: "Compliance Overview"
    charts:
      - id: compliance_overview
        title: "Compliance Rates"
```

### Detailed Room Analysis

```yaml
template_id: room_detailed
name: Detailed Room Analysis
description: Comprehensive room-by-room analysis

analytics_requirements:
  analytics_tags:
    - statistics.basic
    - compliance.overall
    - spatial.room_level
  required_parameters:
    - temperature
    - co2
  required_level: room

report:
  title: "Room-by-Room Analysis"
  format: html
  scope: building

sections:
  - section_id: overview
    type: summary
    title: "Building Overview"
  
  - section_id: rooms
    type: loop
    title: "Detailed Room Analysis"
    loop_over: rooms
    view_type: cards
    max_iterations: 20
    sort_by: compliance_rate
    sort_order: ascending
```

## PDF Generation

### Requirements

For best PDF quality, install weasyprint:

```bash
pip install weasyprint
```

### PDF Features

- Page numbering
- Headers and footers
- Table of contents (coming soon)
- Page breaks between sections
- Print-optimized styling
- Embedded charts and images

### PDF Options

```python
# Generate PDF with custom options
pdf_result = pdf_generator.html_to_pdf(
    html_path=Path("output/reports/report.html"),
    pdf_path=Path("output/reports/report.pdf"),
    options={
        'presentational_hints': True,
        'optimize_size': ('fonts',)
    }
)
```

## Troubleshooting

### Template Validation Errors

**Error: "Missing required keys"**
- Ensure template has `template_id`, `name`, and `description`

**Error: "Invalid section type"**
- Check section type is one of: cover, summary, text, charts, recommendations, issues, table, loop

**Error: "Duplicate section IDs"**
- Ensure all section_id values are unique within the template

### Data Collection Issues

**Warning: "Unknown analytics tags"**
- Check analytics tag is in the list of valid tags
- Verify tag name spelling

**Error: "Insufficient data for report generation"**
- Check that required analytics are available in analysis_results
- Verify data quality meets minimum threshold
- Ensure required parameters are present

### PDF Generation Issues

**Error: "No PDF generation backend available"**
- Install weasyprint: `pip install weasyprint`

**Warning: "Basic PDF generated"**
- Upgrade to weasyprint for better HTML/CSS rendering

## API Reference

### YAMLTemplateParser

```python
parser = YAMLTemplateParser()

# Parse template file
template_data = parser.parse_file(Path("template.yaml"))

# Validate template
validation_result = parser.validate(template_data)

# Parse and validate in one call
template_data, validation = parser.parse_and_validate(Path("template.yaml"))

# Extract analytics requirements
requirements = parser.extract_analytics_requirements(template_data)
```

### AnalyticsDataAggregator

```python
aggregator = AnalyticsDataAggregator()

# Collect required analytics
collected_data = aggregator.collect_required_analytics(
    analysis_results=analysis,
    required_tags={'statistics.basic', 'compliance.overall'},
    required_parameters={'temperature', 'co2'},
    required_level='building'
)

# Validate requirements are met
validation = aggregator.validate_requirements_met(
    collected_data,
    required_tags
)
```

### EnhancedReportService

```python
service = EnhancedReportService(
    templates_dir=Path("config/report_templates"),
    output_dir=Path("output/reports"),
    enable_validation=True
)

# Generate report
result = service.generate_report(
    template_name="building_detailed",
    analysis_results=analysis,
    output_format='both'
)

# List templates
templates = service.list_available_templates()

# Validate template
validation = service.validate_template_file("template_name")

# Get requirements
requirements = service.get_template_requirements("template_name")
```

## Best Practices

1. **Always validate templates** before using them in production
2. **Use analytics_requirements** to ensure necessary data is collected
3. **Test templates** with sample data before deploying
4. **Set appropriate min_data_quality** thresholds
5. **Use descriptive section_ids** for easier debugging
6. **Group related charts** in the same section
7. **Limit loop iterations** to avoid overly long reports
8. **Use PDF format** for formal reports and archiving
9. **Keep templates in version control**
10. **Document custom templates** with clear descriptions

## Version History

- **v1.0.0** - Initial release with YAML parsing, analytics aggregation, HTML generation, and PDF conversion
