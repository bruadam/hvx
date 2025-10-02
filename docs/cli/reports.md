# Reports Commands

The `hvx reports` command group provides PDF report generation capabilities from analysis data.

## Overview

Reports commands enable you to:
- Generate professional PDF reports from analysis data
- List all generated reports
- Combine analysis results with chart visualizations
- Create stakeholder-ready documentation

## Commands

### `hvx reports generate`

Generate a PDF report from analysis data using a template.

#### Syntax

```bash
hvx reports generate TEMPLATE_NAME [OPTIONS]
```

#### Arguments

- `TEMPLATE_NAME` - Name of the template to use (required)

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--data` | `-d` | TEXT | - | Analysis name or path to JSON file (required) |
| `--output` | `-o` | PATH | Auto-generated | Output PDF file path |

#### Examples

**Generate report with analysis name:**
```bash
hvx reports generate simple_report --data my_building
```

**Generate report with JSON file:**
```bash
hvx reports generate simple_report --data output/analysis/building_1.json
```

**Generate report with custom output path:**
```bash
hvx reports generate comprehensive --data my_building -o reports/q1_report.pdf
```

**Generate executive summary:**
```bash
hvx reports generate executive_summary --data quarterly_analysis
```

**Short form:**
```bash
hvx reports generate simple_report -d my_building -o reports/summary.pdf
```

#### Data Sources

The `--data` option accepts two formats:

1. **Analysis Name**: Reference a saved analysis by name
   ```bash
   hvx reports generate simple_report --data building_sample_2024-10-02
   ```
   Loads from: `output/analysis/building_sample_2024-10-02.json`

2. **JSON File Path**: Direct path to analysis JSON file
   ```bash
   hvx reports generate simple_report --data output/analysis/custom_analysis.json
   ```

#### Output

The command displays:
- Data loading confirmation
- Template being used
- Processing progress
- Generation summary with statistics
- Output file path

Example output:
```
Loading analysis data: my_building

Generating report with template: simple_report

Generating report... ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✓ Report generated
Template: simple_report
Output: output/reports/my_building_simple_report_2024-10-02.pdf
Charts: 3
```

#### Default Output Path

If `--output` is not specified, reports are saved to:
```
output/reports/<analysis_name>_<template_name>_<timestamp>.pdf
```

Examples:
- `output/reports/my_building_simple_report_2024-10-02.pdf`
- `output/reports/q1_analysis_executive_summary_2024-10-02.pdf`

#### Report Contents

Generated reports typically include:

1. **Title Page**
   - Building/portfolio name
   - Report date
   - Analysis period

2. **Executive Summary**
   - Key metrics (compliance, quality score)
   - Overall performance rating
   - Quick overview

3. **Charts**
   - Visualizations specified in template
   - Parameter-specific charts
   - Trend analyses

4. **Detailed Results**
   - Test results by parameter
   - Compliance rates
   - Data quality metrics

5. **Findings**
   - Key findings from analysis
   - Critical issues
   - Patterns identified

6. **Recommendations**
   - Action items
   - Improvement suggestions
   - Priority areas

---

### `hvx reports list`

List all generated PDF reports.

#### Syntax

```bash
hvx reports list
```

#### No Options

This command takes no arguments or options.

#### Examples

```bash
hvx reports list
```

#### Output

Displays a table of generated reports:

```
Generated Reports
┌──────────────────────────────────────────────┬──────────┬─────────────────────┐
│ Name                                         │ Size     │ Created             │
├──────────────────────────────────────────────┼──────────┼─────────────────────┤
│ my_building_simple_report_2024-10-02.pdf     │ 2.45 MB  │ 2024-10-02 14:30:45 │
│ q1_analysis_comprehensive_2024-10-01.pdf     │ 5.12 MB  │ 2024-10-01 10:15:20 │
│ executive_summary_2024-09-28.pdf             │ 1.23 MB  │ 2024-09-28 16:45:33 │
└──────────────────────────────────────────────┴──────────┴─────────────────────┘
```

If no reports exist:
```
No reports found
Generate report with: hvx reports generate <template> --data <analysis>
```

#### Report Location

All reports are stored in:
```
output/reports/
```

You can open the directory to view reports:
```bash
# macOS
open output/reports/

# Linux
xdg-open output/reports/

# Windows
explorer output\reports
```

---

## Workflow Examples

### Basic Report Generation

```bash
# 1. Run analysis
hvx analytics run data/building.csv --name my_building

# 2. List available templates
hvx templates list

# 3. Generate report
hvx reports generate simple_report --data my_building

# 4. List generated reports
hvx reports list

# 5. Open report
open output/reports/my_building_simple_report_*.pdf
```

### Multiple Reports from Same Analysis

```bash
# Generate different reports from same analysis
hvx reports generate simple_report --data my_building
hvx reports generate executive_summary --data my_building
hvx reports generate technical --data my_building

# List all generated reports
hvx reports list
```

### Batch Report Generation

```bash
# Generate reports for multiple analyses
for analysis in building1 building2 building3; do
  hvx reports generate comprehensive --data "$analysis" \
    -o "reports/${analysis}_report.pdf"
done

# List all reports
hvx reports list
```

### Custom Report with Specific Output

```bash
# Generate with specific naming
hvx reports generate executive_summary \
  --data q1_2024_analysis \
  -o reports/stakeholders/Q1_2024_Executive_Summary.pdf

# Verify generation
ls -lh reports/stakeholders/
```

### Complete Workflow with Custom Template

```bash
# 1. Create custom template
hvx templates create
# (Follow prompts to create "quarterly_review" template)

# 2. Run analysis
hvx analytics run data/q1_data.csv --name q1_2024

# 3. Generate report with custom template
hvx reports generate quarterly_review --data q1_2024

# 4. View result
open output/reports/q1_2024_quarterly_review_*.pdf
```

---

## Report Customization

### Template Selection

Choose templates based on audience and purpose:

**Simple Report** - Quick overview
- Ideal for: Regular monitoring
- Audience: Facility managers
- Content: Key metrics and basic charts
```bash
hvx reports generate simple_report --data analysis
```

**Executive Summary** - High-level overview
- Ideal for: Management briefings
- Audience: Executives, board members
- Content: Summary metrics and key findings
```bash
hvx reports generate executive_summary --data analysis
```

**Comprehensive Report** - Detailed analysis
- Ideal for: Technical reviews
- Audience: Engineers, analysts
- Content: All metrics, charts, and detailed data
```bash
hvx reports generate comprehensive --data analysis
```

**Technical Report** - In-depth technical details
- Ideal for: Compliance documentation
- Audience: Auditors, technical staff
- Content: Complete test results and methodologies
```bash
hvx reports generate technical --data analysis
```

### Creating Custom Templates

For specialized needs, create custom templates:

```bash
# 1. Explore available charts
hvx graphs list

# 2. Create template with selected charts
hvx templates create

# 3. Manually edit template for fine-tuning
vim ~/.hvx/templates/my_template.yaml

# 4. Generate report
hvx reports generate my_template --data analysis
```

---

## Report Quality

### Chart Generation

Reports automatically generate charts specified in the template:
- Charts are rendered as high-quality PNG images
- Images are embedded in PDF
- Chart configuration from template is applied
- Dummy data is replaced with actual analysis data

### PDF Quality

Generated PDFs feature:
- Professional layout and styling
- High-resolution charts
- Consistent branding
- Readable fonts and sizes
- Proper page breaks
- Table of contents (in comprehensive templates)

### Data Validation

Before report generation:
- Analysis data is validated
- Required fields are checked
- Charts verify data availability
- Missing data is handled gracefully

---

## Troubleshooting

### Common Issues

**Issue: "Analysis not found"**
- **Solution**: 
  ```bash
  # List available analyses
  hvx analytics list
  
  # Verify analysis name
  hvx analytics show <name>
  
  # Or use direct path
  hvx reports generate template --data path/to/analysis.json
  ```

**Issue: "Template not found"**
- **Solution**:
  ```bash
  # List available templates
  hvx templates list
  
  # Create template if needed
  hvx templates create
  ```

**Issue: "Chart generation failed"**
- **Solution**:
  - Verify chart ID is valid: `hvx graphs list`
  - Check analysis data contains required parameters
  - Preview chart first: `hvx graphs preview <chart_id>`

**Issue: "Missing required field in analysis data"**
- **Solution**:
  - Check template requirements: `hvx templates show <template>`
  - Verify analysis completeness: `hvx analytics show <analysis>`
  - Re-run analysis if data is incomplete

**Issue: "PDF generation error"**
- **Solution**:
  - Check output directory is writable
  - Ensure sufficient disk space
  - Verify all dependencies are installed
  - Try simpler template first

**Issue: "Report is empty or incomplete"**
- **Solution**:
  - Verify analysis JSON is not empty
  - Check template sections are properly configured
  - Review template syntax: `hvx templates show <template>`

### Debugging Report Generation

Enable verbose output (if available):
```bash
# Run with debugging
python -m src.services.report_service generate \
  --template simple_report \
  --data my_building \
  --debug
```

Check intermediate files:
```bash
# Charts should be generated
ls -la output/charts/

# Analysis JSON should exist
cat output/analysis/my_building.json | jq .
```

---

## Performance Considerations

### Report Size

- **Simple reports**: ~1-3 MB
- **Comprehensive reports**: ~3-10 MB
- **Size factors**: Number of charts, data density, page count

### Generation Time

- **Typical**: 5-15 seconds per report
- **Factors**: Chart complexity, data volume, system performance

### Optimization Tips

1. **Limit charts**: Use 3-5 charts for faster generation
2. **Reduce data**: Pre-filter data if possible
3. **Use appropriate templates**: Don't use comprehensive when simple suffices
4. **Batch wisely**: Generate reports sequentially for large batches

---

## Integration Examples

### Automated Reporting

```bash
#!/bin/bash
# automated_report.sh

# Run analysis
hvx analytics run data/daily_data.csv --name daily_$(date +%Y%m%d)

# Generate report
hvx reports generate simple_report \
  --data daily_$(date +%Y%m%d) \
  -o reports/daily/report_$(date +%Y%m%d).pdf

# Email report (example)
# mail -s "Daily Report" -a "reports/daily/report_$(date +%Y%m%d).pdf" \
#   manager@example.com < report_email.txt
```

### Scheduled Reports

```bash
# Add to crontab for weekly reports
# 0 9 * * 1 /path/to/generate_weekly_report.sh

#!/bin/bash
# generate_weekly_report.sh

cd /path/to/hvx
source venv/bin/activate

# Run analysis on weekly data
hvx analytics run data/weekly_data.csv --name weekly_$(date +%Y%W)

# Generate report
hvx reports generate comprehensive \
  --data weekly_$(date +%Y%W) \
  -o reports/weekly/Week_$(date +%Y%W).pdf

# Archive old reports
find reports/weekly -name "*.pdf" -mtime +90 -delete
```

### Multi-Building Reports

```bash
#!/bin/bash
# multi_building_reports.sh

buildings=("building_a" "building_b" "building_c")

for building in "${buildings[@]}"; do
  echo "Generating report for $building..."
  
  hvx reports generate executive_summary \
    --data "$building" \
    -o "reports/monthly/${building}_$(date +%Y%m).pdf"
done

echo "All reports generated!"
hvx reports list
```

---

## Best Practices

1. **Choose appropriate templates**: Match template to audience and purpose
2. **Consistent naming**: Use clear, consistent naming for analyses and reports
3. **Regular generation**: Generate reports on a schedule for consistency
4. **Archive reports**: Keep historical reports for trend analysis
5. **Verify before sharing**: Review generated reports before distribution
6. **Custom templates**: Create custom templates for recurring needs
7. **Document workflows**: Keep scripts for automated report generation
8. **Test templates**: Test new templates with sample data first
9. **Backup reports**: Archive important reports separately
10. **Track versions**: Use timestamps or version numbers in filenames

---

## See Also

- [Analytics Commands](./analytics.md) - Generate analysis data for reports
- [Templates Commands](./templates.md) - Manage report templates
- [Graphs Commands](./graphs.md) - Explore available charts
- [CLI Overview](./README.md) - Complete CLI documentation
- Built-in templates in `src/reporting/templates/`
