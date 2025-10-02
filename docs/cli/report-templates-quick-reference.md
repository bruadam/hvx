# Report Templates Quick Reference

## Command Summary

| Command | Description |
|---------|-------------|
| `hvx report-templates list` | List all templates |
| `hvx report-templates show <id>` | Show template details |
| `hvx report-templates create` | Create new template interactively |
| `hvx report-templates edit <id>` | Edit existing template |
| `hvx report-templates delete <id>` | Delete template |
| `hvx report-templates copy <src> <dst>` | Copy template |
| `hvx report-templates validate <id>` | Validate template |
| `hvx report-templates quick-standard` | Create standard building template |
| `hvx report-templates quick-room-detail` | Create detailed room template |

## Section Types Quick Guide

| Type | Purpose | Key Options |
|------|---------|-------------|
| **metadata** | Report header | Title, author, date, description, notes |
| **text** | Free-form content | Markdown text with heading |
| **summary** | Statistics | Level, metrics, compliance, best/worst |
| **table** | Tabular data | Type, level, sort order, max rows |
| **graph** | Charts | Type, level, parameters, tests |
| **issues** | Problems list | Level, severity filters, max items |
| **recommendations** | Suggestions | Level, max items, priority filter |
| **loop** | Iterate entities | Loop over buildings/rooms, sort, max iterations |

## Common Use Cases

### 1. Quick Standard Report
```bash
hvx report-templates quick-standard
# Creates: standard_building template
# Includes: metadata, summary, issues, recommendations
```

### 2. Detailed Room Analysis
```bash
hvx report-templates quick-room-detail
# Creates: room_detailed template
# Loops over worst 20 rooms with summaries
```

### 3. Custom Executive Summary
```bash
hvx report-templates create
# Template ID: exec_summary
# Sections:
#   - Metadata
#   - Portfolio summary
#   - Critical issues only (max 5)
#   - Compliance bar chart
#   - Top recommendations (max 10)
```

### 4. Worst Performers Report
```bash
hvx report-templates create
# Template ID: worst_performers
# Sections:
#   - Metadata
#   - Building summary
#   - Loop over rooms (worst_first, max 10):
#     - Room summary
#     - Room issues
#     - Room recommendations
```

### 5. Seasonal Analysis
```bash
hvx report-templates create
# Template ID: seasonal_report
# Sections:
#   - Metadata
#   - Seasonal comparison table
#   - Temperature by season graph
#   - CO2 by season graph
#   - Seasonal recommendations
```

## Sort Orders

- `best_first` - Highest performing first
- `worst_first` - Lowest performing first (prioritization)
- `alphabetical` - A-Z by name
- `none` - Original order

## Analysis Levels

- `portfolio` - Across all buildings
- `building` - Individual building
- `level` - Floor/level within building
- `room` - Individual room

## Loop Configuration

```bash
Loop over: rooms
Sort order: worst_first
Max iterations: 10

# Repeats these sections for each entity:
- Summary
- Issues
- Recommendations
```

## Output Formats

- `pdf` - PDF document (default)
- `html` - HTML webpage
- `markdown` - Markdown file
- `docx` - Word document

## Template File Locations

Templates stored in: `config/report_templates/`
- YAML format: `<template_id>.yaml`
- JSON format: `<template_id>.json`

## Severity Filters (Issues)

- `critical` - Critical issues only
- `high` - High severity
- `medium` - Medium severity
- `low` - Low severity

## Quick Examples

### Executive Summary Template
```bash
hvx report-templates create
Template ID: exec_summary
Sections:
  1. Metadata
  2. Portfolio summary
  3. Critical issues (max 5)
  4. Compliance chart
  5. Recommendations (max 10)
```

### Detailed Analysis Template
```bash
hvx report-templates create
Template ID: detailed_analysis
Sections:
  1. Metadata
  2. Building summary
  3. Test results table
  4. Compliance charts
  5. Issues (critical + high)
  6. Recommendations (max 20)
  7. Loop worst 15 rooms:
     - Room summary
     - Room issues
```

### Compliance Report Template
```bash
hvx report-templates create
Template ID: compliance_report
Sections:
  1. Metadata
  2. Compliance summary table
  3. Non-compliant rooms table (worst first)
  4. Compliance by parameter graph
  5. Critical issues
  6. Remediation recommendations
```

## Tips

1. **Start with quick templates** - Modify existing templates
2. **Use meaningful IDs** - `winter_compliance`, `summer_overheating`
3. **Limit loop iterations** - 10-20 max for readability
4. **Sort worst first** - Prioritize action items
5. **Filter severity** - Don't overwhelm with low-priority issues
6. **Combine graphs + tables** - Visual and detailed views
7. **Add text sections** - Provide context
8. **Version templates** - Copy before major edits
9. **Validate before use** - Run validate command
10. **Document purpose** - Use clear descriptions

## Integration with Reports

```bash
# Generate report from template
hvx reports generate \
  --analysis-dir output/analysis \
  --template exec_summary \
  --output reports/executive.pdf

# With test set
hvx reports generate \
  --analysis-dir output/analysis \
  --template seasonal_report \
  --test-set winter_tests \
  --output reports/winter.pdf
```

## Common Patterns

### Pattern 1: Management Report
```
Metadata → Portfolio Summary → Critical Issues → Recommendations
```

### Pattern 2: Technical Report
```
Metadata → Building Summary → Test Results Table →
Parameter Graphs → All Issues → Detailed Recommendations
```

### Pattern 3: Prioritization Report
```
Metadata → Summary → Loop Worst 20 Rooms:
  (Room Summary + Issues + Recommendations)
```

### Pattern 4: Compliance Report
```
Metadata → Compliance Table → Non-Compliant Rooms Table →
Compliance Graph → Critical Issues → Remediation Steps
```

## See Also

- [Full Documentation](./report-templates-command.md)
- [Reports Commands](./reports-command.md)
- [Tests Commands](./tests-command.md)
