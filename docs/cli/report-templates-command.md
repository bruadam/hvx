# Report Template Management CLI

The `hvx report-templates` command group provides comprehensive control over report generation through customizable templates. Build reports with exactly the sections, data, and layout you need.

## Overview

Report templates allow you to:
- **Define report structure** with sections for metadata, graphs, tables, summaries, etc.
- **Control data selection** - choose which parameters, tests, and analysis levels to include
- **Configure loops** - iterate over buildings or rooms to create detailed reports
- **Sort and filter** - show best/worst performing entities
- **Customize output** - PDF, HTML, Markdown, or DOCX formats
- **Save and reuse** - create template libraries for different scenarios

## Template Structure

A report template consists of:
1. **Metadata** - Basic template information (ID, name, description, author)
2. **Output settings** - Format (PDF/HTML), page size, orientation
3. **Sections** - Ordered list of content sections to include
4. **Global configuration** - Filters and settings applied across the template

## Available Commands

### List Templates

```bash
hvx report-templates list
```

Shows all available report templates with their basic information.

### Show Template Details

```bash
hvx report-templates show <template_id>
```

Display detailed information about a specific template, including all sections.

### Create New Template

Interactive template creation:

```bash
hvx report-templates create
```

Create from existing template:

```bash
hvx report-templates create --from-template standard_building
```

### Edit Template

```bash
hvx report-templates edit <template_id>

# Save with new ID
hvx report-templates edit <template_id> --save-as <new_id>
```

### Delete Template

```bash
hvx report-templates delete <template_id>

# Skip confirmation
hvx report-templates delete <template_id> --yes
```

### Copy Template

```bash
hvx report-templates copy <source_id> <new_id>

# With custom name
hvx report-templates copy source_id new_id --name "Custom Report"
```

### Validate Template

```bash
hvx report-templates validate <template_id>
```

Checks template configuration for errors and missing required fields.

## Quick Create Commands

### Standard Building Report

```bash
hvx report-templates quick-standard
```

Creates a comprehensive building analysis template with:
- Metadata section
- Executive summary
- Critical issues list
- Recommendations

### Detailed Room Analysis

```bash
hvx report-templates quick-room-detail
```

Creates a template that loops over worst-performing rooms with:
- Portfolio overview
- Individual room summaries
- Issues and recommendations for each room

## Section Types

### 1. Metadata Section

Contains report header information:
- **Title** - Report title (can be auto-generated)
- **Author** - Report author name
- **Date** - Generation date (auto)
- **Description** - Report description
- **Notes** - Additional notes
- **Custom fields** - Any additional metadata

**Example:**
```bash
Section type: metadata
Include title: Yes
Include author: Yes
Include date: Yes
Include description: Yes
Include notes: No
```

### 2. Text Section

Free-form text content with optional heading:
- **Heading** - Section title
- **Content** - Markdown or plain text
- **Heading level** - H1-H6

**Example:**
```bash
Section type: text
Heading: Executive Summary
Content: [Markdown text...]
```

### 3. Summary Section

Aggregated statistics and metrics:
- **Analysis level** - Portfolio/Building/Level/Room
- **General metrics** - Count, totals, averages
- **Test summary** - Overview of test results
- **Compliance rates** - Pass/fail percentages
- **Quality scores** - Overall quality metrics
- **Best/worst performing** - Top N entities
- **Custom metrics** - Additional calculations

**Example:**
```bash
Section type: summary
Level: building
Include metrics: Yes
Include test summary: Yes
Include compliance rates: Yes
Include best performing: Yes
Include worst performing: Yes
Top N: 5
```

### 4. Table Section

Tabular data display:
- **Table type** - test_results, compliance_summary, room_ranking, etc.
- **Columns** - Which columns to include
- **Tests** - Specific tests to show
- **Parameters** - Specific parameters to show
- **Sort by** - Column to sort on
- **Sort order** - Best first, worst first, alphabetical, none
- **Max rows** - Limit number of rows
- **Filters** - Additional data filtering

**Available table types:**
- `test_results` - Test outcomes and compliance
- `compliance_summary` - Compliance rates by parameter
- `room_ranking` - Ranked list of rooms
- `parameter_statistics` - Statistical summary by parameter
- `seasonal_comparison` - Compare across seasons
- `issues_list` - List of identified issues
- `recommendations_list` - List of recommendations

**Example:**
```bash
Section type: table
Table type: room_ranking
Level: building
Sort by: compliance_rate
Sort order: worst_first
Max rows: 20
```

### 5. Graph Section

Charts and visualizations:
- **Graph type** - compliance_bar_chart, temperature_heatmap, etc.
- **Parameters** - Which parameters to visualize
- **Tests** - Specific tests to include
- **Analysis level** - Data aggregation level
- **Configuration** - Graph-specific settings
- **Caption** - Optional figure caption

**Available graph types:**
- `compliance_bar_chart` - Bar chart of compliance rates
- `temperature_heatmap` - Heatmap of temperature patterns
- `co2_time_series` - Time series plot of CO2 levels
- `parameter_distribution` - Distribution histograms
- `seasonal_comparison` - Compare metrics across seasons
- `daily_pattern` - Show daily patterns
- `room_comparison` - Compare multiple rooms

**Example:**
```bash
Section type: graph
Graph type: compliance_bar_chart
Level: building
Parameters: temperature, co2
```

### 6. Issues Section

List of identified issues:
- **Analysis level** - Where to pull issues from
- **Severity filters** - Critical, high, medium, low
- **Max issues** - Limit number shown
- **Grouping** - Group by severity, parameter, or location

**Example:**
```bash
Section type: issues
Level: building
Include critical: Yes
Include high: Yes
Include medium: No
Include low: No
Max issues: 10
```

### 7. Recommendations Section

List of improvement recommendations:
- **Analysis level** - Source of recommendations
- **Max recommendations** - Limit number shown
- **Priority filter** - Filter by priority level
- **Grouping** - Group recommendations

**Example:**
```bash
Section type: recommendations
Level: building
Max recommendations: 10
Priority filter: high
```

### 8. Loop Section

Iterate over multiple entities:
- **Loop over** - Buildings or rooms
- **Sort order** - Best first, worst first, alphabetical, none
- **Max iterations** - Limit number of entities
- **Filters** - Filter which entities to include
- **Sections** - Subsections to repeat for each entity

**Example:**
```bash
Section type: loop
Loop over: rooms
Sort order: worst_first
Max iterations: 10
Sections:
  - Room summary
  - Room issues
  - Room recommendations
```

## Interactive Template Builder

When creating a template interactively, you'll be guided through:

### 1. Basic Information
```
Template ID: summer_overheating_report
Template name: Summer Overheating Analysis
Description: Detailed analysis of summer overheating issues
```

### 2. Output Settings
```
Output format:
  1. pdf ←
  2. html
  3. markdown
  4. docx
Select format: 1

Page size:
  1. A4 ←
  2. Letter
  3. A3
Select size: 1

Orientation:
  1. portrait ←
  2. landscape
Select orientation: 1

Default analysis level:
  1. portfolio
  2. building ←
  3. level
  4. room
Select level: 2
```

### 3. Section Building
```
Building Template Sections
Add sections to your template. Press Ctrl+C when done.

Add metadata section (title, author, date)? Yes
✓ Metadata section added

Add another section? Yes

Select section type:
  1. metadata
  2. text
  3. summary ←
  4. table
  5. graph
  6. issues
  7. recommendations
  8. loop
Select type: 3

Analysis level:
  1. portfolio
  2. building ←
  3. level
  4. room
Select level: 2

Include general metrics? Yes
Include test summary? Yes
Include compliance rates? Yes
Include quality scores? Yes
Include best performing? Yes
Include worst performing? Yes
Number of top/bottom items: 5

✓ Section 'summary_1' added
```

## Example Workflows

### Example 1: Create Custom Summer Analysis Report

```bash
# Start interactive creation
hvx report-templates create

# Interactive prompts:
Template ID: summer_overheating
Template name: Summer Overheating Report
Description: Analysis of summer temperature exceedances

Output format: pdf
Page size: A4
Orientation: portrait
Default level: building

# Add sections:
1. Metadata (title, author, date)
2. Executive Summary (building level)
3. Critical Issues (high temp only)
4. Temperature Heatmap Graph
5. Room Ranking Table (sorted worst first, max 20)
6. Recommendations (max 15)

✓ Template 'summer_overheating' created successfully!
```

### Example 2: Create Report with Room Loop

```bash
hvx report-templates create

Template ID: detailed_room_analysis
Template name: Detailed Room-by-Room Analysis
Description: In-depth analysis of each problematic room

# Add sections:
1. Metadata
2. Portfolio Summary
3. Loop over Rooms (worst first, max 15):
   a. Room Summary
   b. Room Test Results Table
   c. Room Temperature Graph
   d. Room Issues
   e. Room Recommendations

✓ Template created with loop over 15 worst rooms!
```

### Example 3: Executive Summary Template

```bash
hvx report-templates create

Template ID: executive_summary
Template name: Executive Summary Report
Description: High-level overview for management

# Add sections:
1. Metadata
2. Text: Introduction and Scope
3. Portfolio Summary (key metrics only)
4. Critical Issues (critical only, max 5)
5. Compliance Bar Chart
6. Top 10 Worst Performing Buildings Table
7. Investment Priorities Recommendations

✓ Compact executive template created!
```

### Example 4: Copy and Modify Existing Template

```bash
# Copy standard template
hvx report-templates copy standard_building custom_analysis

# Edit the copy
hvx report-templates edit custom_analysis

# Modifications:
- Change default level to room
- Add loop over worst 20 rooms
- Remove recommendations section
- Add custom text section with project background

✓ Template 'custom_analysis' updated!
```

### Example 5: Seasonal Comparison Template

```bash
hvx report-templates create

Template ID: seasonal_comparison
Template name: Seasonal Performance Comparison
Description: Compare building performance across seasons

# Add sections:
1. Metadata
2. Executive Summary (all seasons)
3. Seasonal Comparison Table
4. Temperature by Season Graph
5. CO2 by Season Graph
6. Winter Issues Section
7. Summer Issues Section
8. Seasonal Recommendations

✓ Seasonal comparison template created!
```

## Sorting and Filtering

### Sort Options

When using loops or tables, control sort order:

- **`best_first`** - Highest compliance/quality first
- **`worst_first`** - Lowest compliance/quality first (useful for prioritization)
- **`alphabetical`** - Alphabetical by name
- **`none`** - Original order

### Filtering Options

Filter which entities to include:

```yaml
filters:
  compliance_threshold: 0.7  # Only include if compliance < 70%
  min_quality: 50            # Only include if quality > 50
  parameters: ["temperature", "co2"]  # Only these parameters
  building_ids: ["bldg_1", "bldg_2"]  # Specific buildings
  room_types: ["office", "classroom"] # Specific room types
```

## Template File Format

Templates are saved as YAML or JSON:

```yaml
template_id: summer_analysis
name: Summer Overheating Analysis
description: Detailed summer temperature analysis
version: "1.0"
author: John Doe
created_date: "2024-01-15T10:30:00"

output_format: pdf
page_size: A4
orientation: portrait
default_level: building

sections:
  - section_type: metadata
    section_id: metadata
    enabled: true
    metadata:
      include_title: true
      include_author: true
      include_date: true

  - section_type: summary
    section_id: exec_summary
    enabled: true
    summary:
      level: building
      include_metrics: true
      include_compliance_rates: true
      top_n: 5

  - section_type: loop
    section_id: room_loop
    enabled: true
    loop:
      loop_over: room
      sort_order: worst_first
      max_iterations: 10
      sections:
        - section_type: summary
          section_id: room_summary
          summary:
            level: room
            include_metrics: true
```

## Using Templates with Reports

Once created, use templates to generate reports:

```bash
# Generate report from template
hvx reports generate \
  --analysis-dir output/analysis \
  --template summer_overheating \
  --output reports/summer_report.pdf

# Use with specific test set
hvx reports generate \
  --analysis-dir output/analysis \
  --template detailed_room_analysis \
  --test-set summer_tests \
  --output reports/detailed.pdf
```

## Best Practices

1. **Start with quick templates** - Use `quick-standard` or `quick-room-detail` as starting points
2. **Name meaningfully** - Use descriptive IDs like `winter_compliance_report`
3. **Use loops for details** - Loop over worst performers to focus on priorities
4. **Limit loop iterations** - Don't overwhelm reports with too many entities
5. **Group related sections** - Organize sections logically
6. **Include metadata** - Always start with metadata section
7. **Test templates** - Generate test reports to verify layout
8. **Version templates** - Keep copies when making major changes
9. **Document purpose** - Use clear descriptions for future reference
10. **Share templates** - Export and share templates across projects

## Tips

- **Sort worst first** - Helps prioritize action items
- **Limit recommendations** - Too many recommendations overwhelm readers
- **Use filters** - Show only relevant severity levels for issues
- **Combine graphs and tables** - Visual + detailed data
- **Add text sections** - Provide context and interpretation
- **Create template library** - Build collection for different audiences
- **Executive vs. detailed** - Different templates for different stakeholders

## See Also

- [Reports Commands](./reports-command.md)
- [Tests Commands](./tests-command.md)
- [Analysis Commands](./analyze-command.md)
