# Quick Reference: Enhanced Report Template System

## Quick Start

```python
from src.core.reporting.enhanced_report_service import EnhancedReportService

# Initialize
service = EnhancedReportService()

# Generate report
result = service.generate_report(
    template_name="building_detailed",
    analysis_results=your_analysis_data,
    output_format='both'  # 'html', 'pdf', or 'both'
)

# Check result
if result['status'] == 'success':
    print(f"HTML: {result['html_report']['path']}")
    if 'pdf_report' in result:
        print(f"PDF: {result['pdf_report']['output_path']}")
```

## Template YAML Structure

### Minimal Template

```yaml
template_id: my_template
name: My Template
description: A simple template

sections:
  - section_id: summary
    type: summary
    title: Summary
```

### With Analytics Requirements

```yaml
template_id: advanced_template
name: Advanced Template
description: Template with analytics requirements

analytics_requirements:
  analytics_tags:
    - statistics.basic
    - compliance.overall
  required_parameters:
    - temperature
    - co2
  min_data_quality: 0.7

report:
  title: "Building Report"
  format: html
  scope: building

sections:
  - section_id: charts
    type: charts
    title: "Analysis"
    charts:
      - id: compliance_overview
        title: "Compliance"
        analytics_requirements:
          analytics_tags:
            - compliance.overall
```

## Analytics Tags Cheat Sheet

### Statistics
- `statistics.basic` - mean, median, std, min, max
- `statistics.trends` - trend analysis
- `statistics.distribution` - distribution data

### Compliance
- `compliance.overall` - overall compliance rates
- `compliance.temporal` - time-based compliance
- `compliance.spatial` - space-based compliance
- `compliance.threshold` - threshold compliance

### Temporal
- `temporal.hourly` - hourly patterns
- `temporal.daily` - daily patterns
- `temporal.seasonal` - seasonal patterns

### Spatial
- `spatial.room_level` - room analysis
- `spatial.comparison` - comparisons
- `spatial.ranking` - rankings

### Recommendations
- `recommendations.operational` - operational advice
- `recommendations.hvac` - HVAC improvements
- `recommendations.ventilation` - ventilation fixes

### Data Quality
- `data_quality.completeness` - completeness metrics
- `data_quality.accuracy` - accuracy metrics

### Performance
- `performance.scoring` - performance scores
- `performance.ranking` - performance rankings

### Weather
- `weather.correlation` - weather correlations
- `weather.impact` - weather impact

## Section Types

1. **cover** - Cover page
   ```yaml
   - section_id: cover
     type: cover
     title: "Report Title"
     include_date: true
   ```

2. **summary** - Key metrics summary
   ```yaml
   - section_id: summary
     type: summary
     title: "Summary"
   ```

3. **text** - Text content
   ```yaml
   - section_id: intro
     type: text
     title: "Introduction"
     content: "Text here..."
   ```

4. **charts** - Visualizations
   ```yaml
   - section_id: charts
     type: charts
     title: "Charts"
     charts:
       - id: chart_name
         title: "Chart Title"
   ```

5. **recommendations** - Recommendations list
   ```yaml
   - section_id: recs
     type: recommendations
     title: "Recommendations"
     max_recommendations: 10
     priority_filter: [critical, high]
   ```

6. **loop** - Loop over rooms/levels
   ```yaml
   - section_id: rooms
     type: loop
     title: "Room Analysis"
     loop_over: rooms
     view_type: cards
     max_iterations: 20
     sort_by: compliance_rate
   ```

## Common Tasks

### List Templates
```python
templates = service.list_available_templates()
for t in templates:
    print(f"{t['name']}: {t['description']}")
```

### Validate Template
```python
validation = service.validate_template_file("my_template")
if not validation.is_valid:
    for error in validation.errors:
        print(f"Error: {error}")
```

### Check Requirements
```python
reqs = service.get_template_requirements("my_template")
print(f"Tags: {reqs['all_tags']}")
print(f"Parameters: {reqs['all_parameters']}")
print(f"Level: {reqs['required_level']}")
```

### Generate Batch Reports
```python
results = service.generate_batch_reports(
    template_names=['template1', 'template2'],
    analysis_results=data,
    output_format='html'
)
print(f"Success: {results['successful']}/{results['total']}")
```

## Error Handling

```python
result = service.generate_report(...)

if result['status'] == 'error':
    if 'validation_errors' in result:
        print("Template validation failed:")
        for error in result['validation_errors']:
            print(f"  - {error}")
    elif 'data_validation' in result:
        print("Insufficient data:")
        print(f"  Coverage: {result['data_validation']['coverage_percentage']}%")
        print(f"  Missing: {result['data_validation']['missing_categories']}")
    else:
        print(f"Error: {result['error']}")
```

## Tips

1. **Always validate templates** before using in production
2. **Use analytics_requirements** to ensure data availability
3. **Test with sample data** first
4. **Set appropriate min_data_quality** (0.6-0.8 recommended)
5. **Limit loop iterations** (10-20 recommended)
6. **Use 'both' format** for archiving (HTML + PDF)
7. **Check validation warnings** - they indicate potential issues

## File Locations

- **Templates**: `config/report_templates/*.yaml`
- **Output HTML**: `output/reports/*.html`
- **Output PDF**: `output/reports/*.pdf`
- **Documentation**: `docs/REPORTING_SYSTEM.md`
- **Examples**: `examples/enhanced_reporting_examples.py`

## Testing

```bash
# Run all tests
python -m pytest tests/test_enhanced_reporting.py -v

# Run specific test
python -m pytest tests/test_enhanced_reporting.py::TestYAMLTemplateParser -v

# Run examples
python examples/enhanced_reporting_examples.py
```

## Troubleshooting

### "Template validation failed"
→ Check YAML syntax, ensure required keys present

### "Insufficient data for report generation"
→ Check that required analytics are in analysis_results

### "PDF generation failed"
→ Install weasyprint: `pip install weasyprint`

### "Unknown analytics tags"
→ Check tag name against valid tags list

### Charts not appearing
→ Ensure chart IDs match available charts
→ Check analytics requirements are met
