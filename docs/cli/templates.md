# Templates Commands

The `hvx templates` command group provides management capabilities for report templates.

## Overview

Templates commands enable you to:
- List available report templates
- View template configurations
- Create new templates interactively
- Delete custom templates
- Manage built-in and user templates

## Commands

### `hvx templates list`

List all available report templates.

#### Syntax

```bash
hvx templates list [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--builtin/--no-builtin` | - | FLAG | `true` | Include/exclude built-in templates |

#### Examples

**List all templates (built-in and custom):**
```bash
hvx templates list
```

**List only custom templates:**
```bash
hvx templates list --no-builtin
```

**List only built-in templates:**
```bash
hvx templates list --builtin
```

#### Output

Displays a table of available templates:

```
Available Templates
┌─────────────────────┬─────────┬────────────────────────────────┬────────────────────┐
│ Name                │ Type    │ Description                    │ Created            │
├─────────────────────┼─────────┼────────────────────────────────┼────────────────────┤
│ simple_report       │ builtin │ Simple single-page report      │ 2024-01-01         │
│ comprehensive       │ builtin │ Multi-page detailed report     │ 2024-01-01         │
│ executive_summary   │ builtin │ Executive summary format       │ 2024-01-01         │
│ my_custom_template  │ user    │ Custom quarterly report        │ 2024-10-02 14:30   │
└─────────────────────┴─────────┴────────────────────────────────┴────────────────────┘
```

If no templates are found:
```
No templates found
Create a new template with: hvx templates create
```

#### Template Types

- **builtin** - System-provided templates (cannot be deleted)
- **user** - User-created custom templates (can be modified/deleted)

#### Template Locations

- **Built-in**: `src/reporting/templates/`
- **User**: `~/.hvx/templates/`

---

### `hvx templates show`

Show detailed template configuration.

#### Syntax

```bash
hvx templates show TEMPLATE_NAME
```

#### Arguments

- `TEMPLATE_NAME` - Name of the template to display (required)

#### Examples

**Show built-in template:**
```bash
hvx templates show simple_report
```

**Show custom template:**
```bash
hvx templates show my_custom_template
```

#### Output

Displays the complete template configuration in YAML format:

```
╭────────── Template: simple_report ──────────╮
│                                             │
│ name: simple_report                         │
│ title: "Building Performance Report"       │
│ description: "Simple single-page report"   │
│                                             │
│ layout:                                     │
│   orientation: portrait                     │
│   pagesize: A4                              │
│   margins:                                  │
│     top: 2.5                                │
│     bottom: 2.5                             │
│     left: 2.0                               │
│     right: 2.0                              │
│                                             │
│ sections:                                   │
│   - type: title                             │
│     title: "${building_name} Report"       │
│     subtitle: "IEQ Analysis"                │
│                                             │
│   - type: summary                           │
│     title: "Executive Summary"              │
│     metrics:                                │
│       - overall_compliance                  │
│       - data_quality_score                  │
│                                             │
│   - type: charts                            │
│     title: "Analysis Results"               │
│     charts:                                 │
│       - id: co2_compliance_bar              │
│         title: "CO2 Compliance"             │
│       - id: temperature_timeseries          │
│         title: "Temperature Trend"          │
│                                             │
│   - type: findings                          │
│     title: "Key Findings"                   │
│     content: key_findings                   │
│                                             │
╰─────────────────────────────────────────────╯
```

#### Use Cases

1. **Template review**: Understand template structure before using
2. **Template copying**: Use as basis for creating new templates
3. **Debugging**: Verify template configuration when reports fail
4. **Documentation**: Share template structure with team

---

### `hvx templates create`

Create a new report template interactively.

#### Syntax

```bash
hvx templates create
```

#### No Arguments or Options

This command runs an interactive wizard to create templates.

#### Interactive Wizard Steps

1. **Template Name**: Enter unique template name (no spaces)
2. **Report Title**: Enter report title (displayed on report)
3. **Description**: Enter optional description
4. **Chart Selection**: Choose up to 3 charts from available library
5. **Confirmation**: Review and confirm template creation

#### Examples

```bash
hvx templates create
```

#### Interactive Session Example

```
Create New Template

Template name: quarterly_review
Report title: Quarterly IEQ Review
Description: Quarterly building performance report

Available charts:
┌────┬─────────────────────────┬──────────────────────────────┐
│  # │ ID                      │ Name                         │
├────┼─────────────────────────┼──────────────────────────────┤
│  1 │ co2_compliance_bar      │ CO2 Compliance Bar Chart     │
│  2 │ temperature_timeseries  │ Temperature Time Series      │
│  3 │ occupancy_heatmap       │ Occupancy Heatmap            │
│  4 │ humidity_distribution   │ Humidity Distribution        │
│  5 │ multi_parameter_line    │ Multi-Parameter Line Chart   │
└────┴─────────────────────────┴──────────────────────────────┘

Select up to 3 charts (comma-separated numbers): 1,2,3

Selected charts: co2_compliance_bar, temperature_timeseries, occupancy_heatmap

Create template? [y/N]: y

✓ Template created: ~/.hvx/templates/quarterly_review.yaml
Use with: hvx reports generate quarterly_review --data <analysis_name>
```

#### Template Output

Creates a YAML template file at `~/.hvx/templates/<name>.yaml`:

```yaml
name: quarterly_review
title: "Quarterly IEQ Review"
description: "Quarterly building performance report"

layout:
  orientation: portrait
  pagesize: A4
  margins:
    top: 2.5
    bottom: 2.5
    left: 2.0
    right: 2.0

sections:
  - type: title
    title: "${building_name} - Quarterly Review"
    subtitle: "IEQ Performance Analysis"

  - type: summary
    title: "Executive Summary"
    metrics:
      - overall_compliance
      - data_quality_score
      - total_rules_evaluated

  - type: charts
    title: "Performance Charts"
    charts:
      - id: co2_compliance_bar
        title: "CO2 Compliance"
      - id: temperature_timeseries
        title: "Temperature Trends"
      - id: occupancy_heatmap
        title: "Occupancy Patterns"

  - type: findings
    title: "Key Findings"
    content: key_findings

  - type: recommendations
    title: "Recommendations"
    content: recommendations
```

#### Customizing Created Templates

After creation, you can manually edit the template file to:
- Add more sections
- Configure chart parameters
- Adjust layout settings
- Customize titles and labels
- Add custom content

Example customization:
```bash
# Open template for editing
vim ~/.hvx/templates/quarterly_review.yaml

# Or use your preferred editor
code ~/.hvx/templates/quarterly_review.yaml
```

---

### `hvx templates delete`

Delete a user-created template.

#### Syntax

```bash
hvx templates delete TEMPLATE_NAME
```

#### Arguments

- `TEMPLATE_NAME` - Name of the template to delete (required)

#### Examples

**Delete custom template:**
```bash
hvx templates delete my_custom_template
```

**Delete with confirmation prompt:**
```bash
hvx templates delete quarterly_review
```

#### Output

The command prompts for confirmation:

```
Delete template 'quarterly_review'? [y/N]: y
✓ Template 'quarterly_review' deleted
```

If you cancel:
```
Delete template 'quarterly_review'? [y/N]: n
Cancelled
```

If template doesn't exist:
```
Template 'quarterly_review' not found
```

#### Important Notes

- **Cannot delete built-in templates**: Only user templates can be deleted
- **Confirmation required**: Always prompts before deletion
- **Permanent action**: Deleted templates cannot be recovered
- **Backup recommended**: Keep copies of important templates

---

## Workflow Examples

### Basic Template Management

```bash
# 1. List available templates
hvx templates list

# 2. View a template's structure
hvx templates show simple_report

# 3. Create a new template
hvx templates create

# 4. Use the new template
hvx reports generate my_new_template --data analysis_name

# 5. Delete template if not needed
hvx templates delete my_new_template
```

### Custom Template Development

```bash
# 1. Explore available charts
hvx graphs list

# 2. Preview charts to select favorites
hvx graphs preview co2_compliance_bar
hvx graphs preview temperature_timeseries

# 3. Create template with selected charts
hvx templates create

# 4. Review created template
hvx templates show my_template

# 5. Manually refine template
vim ~/.hvx/templates/my_template.yaml

# 6. Test template
hvx reports generate my_template --data test_analysis

# 7. Refine further if needed
vim ~/.hvx/templates/my_template.yaml
```

### Template Backup and Sharing

```bash
# Backup user templates
mkdir -p backups/templates
cp ~/.hvx/templates/*.yaml backups/templates/

# Share template with team
cp ~/.hvx/templates/my_template.yaml /shared/templates/

# Import template from team member
cp /shared/templates/team_template.yaml ~/.hvx/templates/
```

### Template Comparison

```bash
# View multiple templates
hvx templates show simple_report > /tmp/simple.txt
hvx templates show comprehensive > /tmp/comprehensive.txt

# Compare
diff /tmp/simple.txt /tmp/comprehensive.txt

# Or view side by side
hvx templates show simple_report
hvx templates show comprehensive
```

---

## Template Structure

### Complete Template Anatomy

```yaml
# Template metadata
name: template_name           # Unique identifier
title: "Report Title"         # Displayed on report
description: "Description"    # Template description

# Page layout
layout:
  orientation: portrait       # portrait or landscape
  pagesize: A4               # A4, Letter, Legal
  margins:
    top: 2.5                 # cm
    bottom: 2.5
    left: 2.0
    right: 2.0

# Report sections (rendered in order)
sections:
  # Title page
  - type: title
    title: "${building_name} Report"    # Variables: ${building_name}, ${date}
    subtitle: "IEQ Analysis"
    date: "${analysis_date}"
    
  # Executive summary
  - type: summary
    title: "Executive Summary"
    metrics:                            # Metrics to display
      - overall_compliance
      - data_quality_score
      - total_rules_evaluated
    
  # Charts section
  - type: charts
    title: "Analysis Results"
    layout: grid                        # grid or sequential
    charts:
      - id: co2_compliance_bar
        title: "CO2 Compliance"
        config:                         # Chart-specific config
          threshold: 1000
          period: weekly
      - id: temperature_timeseries
        title: "Temperature Trend"
        config:
          show_average: true
    
  # Data table
  - type: table
    title: "Detailed Results"
    data: test_results                  # Data source from analysis
    columns:
      - parameter
      - compliance_rate
      - status
    
  # Text content
  - type: findings
    title: "Key Findings"
    content: key_findings               # From analysis JSON
    
  - type: recommendations
    title: "Recommendations"
    content: recommendations
    
  # Custom content
  - type: text
    title: "Methodology"
    content: |
      This analysis was performed using...
      Standards applied: EN 16798-1
```

### Section Types

1. **title** - Title page with report metadata
2. **summary** - Metric summary with key statistics
3. **charts** - Chart visualizations
4. **table** - Data tables
5. **findings** - Key findings from analysis
6. **recommendations** - Recommendations
7. **text** - Custom text content

### Variables

Templates support variable substitution:
- `${building_name}` - Building name from analysis
- `${analysis_date}` - Analysis timestamp
- `${date}` - Current date
- `${portfolio_name}` - Portfolio name (if applicable)

### Data Sources

Content can reference analysis data:
- `overall_compliance` - Overall compliance percentage
- `data_quality_score` - Data quality score
- `key_findings` - Array of finding strings
- `recommendations` - Array of recommendation strings
- `test_results` - Detailed test results
- `summary` - Summary metrics object

---

## Best Practices

1. **Descriptive names**: Use clear, descriptive template names
2. **Start simple**: Begin with basic templates, add complexity incrementally
3. **Test early**: Generate test reports to verify template layout
4. **Version control**: Keep templates in version control
5. **Document purpose**: Use meaningful descriptions
6. **Limit charts**: Keep to 3-5 charts per template for readability
7. **Consistent naming**: Use naming conventions for team templates
8. **Backup regularly**: Keep backups of custom templates
9. **Share wisely**: Share tested, documented templates with team
10. **Iterate**: Refine templates based on stakeholder feedback

---

## Common Issues

**Issue: "Template not found"**
- **Solution**: Use `hvx templates list` to see available templates
- Check template name spelling
- Ensure custom template is in `~/.hvx/templates/`

**Issue: "Cannot delete built-in template"**
- **Solution**: Built-in templates are read-only
- Create a custom copy instead: copy YAML to user directory

**Issue: "Invalid YAML syntax"**
- **Solution**: Validate YAML syntax using online validator
- Check indentation (use spaces, not tabs)
- Ensure proper quote matching

**Issue: "Chart not found in template"**
- **Solution**: Verify chart ID with `hvx graphs list`
- Check spelling of chart ID in template

**Issue: "Variable not substituted"**
- **Solution**: Ensure variable exists in analysis data
- Check variable syntax: `${variable_name}`
- Verify analysis JSON contains the required field

**Issue: "Report generation fails with template"**
- **Solution**: Use `hvx templates show <name>` to verify structure
- Check that analysis data contains required fields
- Verify chart IDs are valid
- Review error messages for specific issues

---

## Template Gallery

### Minimal Template

```yaml
name: minimal
title: "Simple Report"

sections:
  - type: title
    title: "${building_name}"
  
  - type: summary
    metrics:
      - overall_compliance
  
  - type: charts
    charts:
      - id: co2_compliance_bar
```

### Executive Template

```yaml
name: executive
title: "Executive Summary"
description: "High-level overview for executives"

sections:
  - type: title
    title: "Executive Summary"
    subtitle: "${building_name}"
  
  - type: summary
    title: "Key Metrics"
    metrics:
      - overall_compliance
      - data_quality_score
  
  - type: findings
    title: "Critical Findings"
    content: key_findings
  
  - type: recommendations
    title: "Recommended Actions"
    content: recommendations
```

### Detailed Technical Template

```yaml
name: technical
title: "Technical Analysis Report"
description: "Detailed technical report with all metrics"

sections:
  - type: title
    title: "Technical Analysis"
    subtitle: "${building_name}"
  
  - type: summary
    title: "Overview"
    metrics:
      - overall_compliance
      - data_quality_score
      - total_rules_evaluated
  
  - type: charts
    title: "Parameter Analysis"
    layout: grid
    charts:
      - id: co2_compliance_bar
      - id: temperature_timeseries
      - id: humidity_distribution
      - id: occupancy_heatmap
  
  - type: table
    title: "Detailed Results"
    data: test_results
  
  - type: findings
    title: "Findings"
    content: key_findings
  
  - type: recommendations
    title: "Recommendations"
    content: recommendations
```

---

## See Also

- [Graphs Commands](./graphs.md) - Explore charts for templates
- [Reports Commands](./reports.md) - Generate reports using templates
- [CLI Overview](./README.md) - Complete CLI documentation
- Built-in templates in `src/reporting/templates/`
- User templates in `~/.hvx/templates/`
