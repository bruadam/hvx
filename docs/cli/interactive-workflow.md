# Interactive Workflow Guide - HVX IEQ Analysis

This guide provides a detailed walkthrough of the interactive IEQ analysis workflow available through `hvx ieq start`.

## Overview

The interactive workflow is designed to guide users through the complete IEQ analysis process, from raw sensor data to professional reports and actionable recommendations. It's suitable for both first-time users and experienced analysts.

## Starting the Workflow

```bash
# Start with prompts
hvx ieq start

# Start with data directory pre-selected
hvx ieq start --directory data/my-buildings

# Run automated (no interaction)
hvx ieq start --directory data/my-buildings --auto
```

## Workflow Steps in Detail

### Step 1: Load Building Data

#### What You'll See

```
HVX - IEQ Analytics Workflow

Interactive workflow steps:
  1. Load building data from directory
  2. Select building type
  3. Select standards, tests & guidelines
  4. Process analytics
  5. Explore results interactively
  6. Generate reports
  7. Export analytics data

Type 'help' for assistance or 'quit' to exit at any time

Enter the path to your data directory: _
```

#### What to Provide

Enter the path to your data directory. The system accepts:
- Relative paths: `data/my-buildings`
- Absolute paths: `/Users/username/projects/data`
- Default available: `data/samples/sample-extensive-data`

#### What Happens Next

The system will:
1. Validate the directory exists
2. Analyze directory structure
3. Detect buildings, levels, and rooms
4. Load all sensor data
5. Validate data quality
6. Display summary

#### Example Output

```
✓ Data loaded successfully

📊 Dataset Summary
┌─────────────────┬──────────────────────────────┐
│ Source          │ data/my-buildings            │
│ Buildings       │ 3                            │
│ Total Rooms     │ 45                           │
└─────────────────┴──────────────────────────────┘
```

#### Room Type Assignment (Optional)

If rooms don't have types assigned, you'll see:

```
⚠ Found 12 room(s) without assigned types

Room Type Assignment Options:
  1. Assign all to same type
  2. Assign individually
  3. Use default (OTHER)
  4. Skip assignment

Choose option: _
```

**Option 1: Assign all to same type**
- Select one room type for all untyped rooms
- Quick and simple

**Option 2: Assign individually**
- System suggests types based on room names
- You can accept or override suggestions
- More accurate but takes longer

**Option 3: Use default (OTHER)**
- All untyped rooms become "OTHER"
- Can be changed later

**Option 4: Skip assignment**
- Proceed without assigning types
- May affect standard applicability

#### Troubleshooting

**Error: Directory not found**
```
✗ Directory not found: data/nonexistent

What would you like to do?
  1. Try again
  2. Get help
  3. Exit workflow

Choose option: 1
```

**Error: Invalid structure**
```
⚠ Directory structure not recognized

Issues found:
  • No building folders found
  • Expected structure: data/buildings/building-name/sensors/*.csv

What would you like to do?
  1. Try again
  2. Get help
  3. Exit workflow
```

### Step 2: Select Building Type

#### What You'll See

```
✓ Load Building Data: 3 buildings, 45 rooms loaded

▶ 2. Select Building Type

What type of building are you analyzing?
  1. Office
  2. School / Educational
  3. Residential / Housing
  4. Healthcare / Hospital
  5. Mixed / Other

Choose building type [1]: _
```

#### Building Type Guide

**1. Office**
- Commercial office buildings
- Workspaces, meeting rooms
- Standards: EN16798-1 Cat II, BR18

**2. School / Educational**
- Schools, universities, classrooms
- Training facilities
- Standards: EN16798-1 Cat II, Danish Guidelines

**3. Residential / Housing**
- Apartments, condos
- Residential buildings
- Standards: EN16798-1 Cat III, BR18

**4. Healthcare / Hospital**
- Medical facilities
- Hospitals, clinics
- Standards: EN16798-1 Cat I (highest requirements)

**5. Mixed / Other**
- Mixed-use buildings
- Special purpose facilities
- Standards: All available, Cat II default

#### Why It Matters

Building type determines:
- Which standards are most applicable
- Default compliance categories
- Recommended test configurations
- Room type requirements

### Step 3: Select Standards & Tests

#### What You'll See

```
✓ Select Building Type: Office

▶ 3. Select Analysis Rules

Building type: office

What would you like to analyze?
  1. Recommended for this building type (auto-select)
  2. All standards, tests & guidelines
  3. Specific standards only
  4. Custom selection (advanced)
  5. None - skip analysis

Choose option [1]: _
```

#### Option Details

**Option 1: Recommended (Auto-select)**

Fastest option. System selects standards based on building type:

- **Office**: EN16798-1 Cat II + BR18
- **School**: EN16798-1 Cat II + Danish Guidelines
- **Residential**: EN16798-1 Cat III + BR18
- **Healthcare**: EN16798-1 Cat I
- **Mixed**: All standards, Cat II

**Option 2: All standards**

Applies all available standards:
- EN16798-1 (all categories)
- BR18
- Danish Guidelines

Most comprehensive but longer processing time.

**Option 3: Specific standards**

```
Available Standards:
┌───┬─────────────────┬────────────────────────────────┐
│ # │ Standard        │ Description                    │
├───┼─────────────────┼────────────────────────────────┤
│ 1 │ en16798-1       │ European indoor environmental  │
│   │                 │ parameters                     │
│ 2 │ br18            │ Danish Building Regulations    │
│ 3 │ danish-guide..  │ Danish indoor climate guide..  │
└───┴─────────────────┴────────────────────────────────┘

Enter standard numbers (comma-separated) or 'all' [all]: 1,2
```

Select specific standards to apply.

**Option 4: Custom selection (Advanced)**

Interactive configuration builder for fine-grained control:
- Choose specific test types
- Set custom thresholds
- Configure filters and periods
- Advanced users only

### Step 4: Process Analytics

#### What You'll See

```
✓ Select Analysis Rules: Auto-selected for office

▶ 4. Process Analytics

Processing analytics...

✓ Analytics processing complete

Analysis Summary
┌─────────────────────────┬─────────────┐
│ Buildings Analyzed      │ 3           │
│ Total Rooms             │ 45          │
│ Data Quality Score      │ 87.3%       │
│                         │             │
│ EN16798-1 Category      │ Cat II      │
│   (>95% time)           │ (96.2%)     │
│                         │             │
│ Hours Above Danish      │ 127h        │
│   Guidelines            │             │
│                         │             │
│ Critical Issues Found   │ 8           │
└─────────────────────────┴─────────────┘

Top Recommendations:
  1. Improve ventilation in Building 1, Level 0
  2. Adjust temperature setpoints in Building 2
  3. Address CO2 accumulation in conference rooms
```

#### What's Happening

The system performs hierarchical analysis:

1. **Room-level** (45 analyses)
   - Individual room compliance
   - Test results per parameter
   - Data quality per room
   - Issues per room

2. **Level-level** (9 analyses)
   - Aggregated compliance per floor
   - Common issues per level

3. **Building-level** (3 analyses)
   - Building-wide performance
   - Investment priorities
   - Building recommendations

4. **Portfolio-level** (1 analysis)
   - Overall metrics
   - Building comparisons
   - Strategic recommendations

#### Output Files Created

```
output/analysis/
├── portfolio.json
├── buildings/
│   ├── building-1.json
│   ├── building-2.json
│   └── building-3.json
├── levels/
│   ├── building-1-level-0.json
│   └── ...
└── rooms/
    ├── building-1-level-0-room-101.json
    └── ...
```

### Step 5: Explore Results

#### What You'll See

```
✓ Process Analytics: 3 buildings analyzed, 73.5% avg compliance

▶ 5. Explore Results

What would you like to do?
  1. View summary and continue
  2. Explore results interactively
  3. Get smart recommendations

Choose option [1]: _
```

#### Option 1: View Summary and Continue

Quick overview then proceed to reports.

#### Option 2: Explore Results Interactively

Launches interactive explorer (if available):
- Navigate through portfolio → buildings → levels → rooms
- Filter by compliance, parameters, issues
- View detailed metrics
- Export specific data

```
Analysis Explorer
─────────────────────────────────────────
Level: Portfolio
Entities: 3 buildings

Select action:
  1. View entity details
  2. Drill down to buildings
  3. Filter entities
  4. Export data
  5. Back to workflow
```

#### Option 3: Get Smart Recommendations

AI-powered analysis generates recommendations:

```
Smart Recommendations

📊 Recommendation Summary
┌─────────────────────────┬──────┐
│ Total Recommendations   │ 24   │
│   Critical              │ 3    │
│   High                  │ 8    │
│   Medium                │ 10   │
│   Low                   │ 3    │
└─────────────────────────┴──────┘

Common Issues Across Portfolio:
  • High CO2 levels during occupied hours
  • Temperature exceedances in summer
  • Insufficient ventilation in meeting rooms

Top Priority Recommendations:

┌─────────────────────────────────────────┐
│ #1                                      │
├─────────────────────────────────────────┤
│ CRITICAL - Increase Ventilation Rates  │
│                                         │
│ Description:                            │
│ CO2 levels exceed 1000 ppm for 15% of  │
│ occupied hours in 12 rooms across 2     │
│ buildings. Ventilation rates appear     │
│ insufficient.                           │
│                                         │
│ Impact:                                 │
│ Would improve compliance by ~15%        │
│ affecting 27% of portfolio rooms        │
│                                         │
│ Cost:                                   │
│ Medium - HVAC system adjustment         │
│                                         │
│ Rationale:                              │
│ • CO2 >1000ppm in 12 rooms              │
│ • Pattern correlates with occupancy     │
│ • Simple ventilation increase sufficient│
└─────────────────────────────────────────┘

Show all 24 recommendations? [y/N]: _
```

**Recommendation exports:**

```
Export recommendations to file? [Y/n]: y

✓ Recommendations exported to: output/recommendations/smart_recommendations.json
```

### Step 6: Generate Reports

#### What You'll See

```
✓ Explore Results: Exploration completed

Would you like to generate a report? [Y/n]: y

▶ 6. Generate Report

Report options:
  1. Use predefined template
  2. Create custom template
  3. Skip report generation

Choose option [1]: _
```

#### Option 1: Use Predefined Template

```
Available templates:
  1. building_detailed
      Comprehensive building analysis with detailed metrics
  2. portfolio_summary
      High-level portfolio overview for executives

Select template [1]: 1

Output format:
  1. HTML (viewable in browser)
  2. PDF (requires weasyprint or pdfkit)
  3. Both HTML and PDF

Choose format [1]: 3
```

**Report generation:**

```
Generating both report...

✓ Report generated successfully!

Generated 3 building reports:
  • Building-1: output/reports/building-1_detailed.html
  • Building-2: output/reports/building-2_detailed.html
  • Building-3: output/reports/building-3_detailed.html

Open report in browser/viewer? [Y/n]: y
```

#### Option 2: Create Custom Template

Interactive template builder:

```
Create Custom Template

Select sections to include:
  Include summary section? [Y/n]: y
  Include compliance metrics? [Y/n]: y
  Include charts? [Y/n]: y
  Include data tables? [Y/n]: y
  Include recommendations? [Y/n]: y

Save this template for future use? [y/N]: y
Template name [my_custom_template]: office_monthly

✓ Template 'office_monthly' saved
✓ Custom report configuration created
```

#### PDF Backend Options

If PDF backend is not available:

```
⚠ No PDF backend available.
Install weasyprint for best results: pip install weasyprint

Generate HTML only instead? [Y/n]: y
```

Available backends:
- **weasyprint** - Best, full HTML/CSS support (recommended)
- **pdfkit** - Good, requires wkhtmltopdf
- **reportlab** - Basic, limited styling

### Step 7: Export Data

#### What You'll See

```
✓ Generate Report: Predefined template configured

Would you like to save the analytics data? [Y/n]: y

▶ 7. Save Analytics Data

Export format:
  1. JSON (recommended)
  2. Excel (.xlsx)
  3. CSV files (multiple)
  4. Markdown (.md)
  5. Text file (.txt)

Choose format [1]: _
```

#### Format Options

**1. JSON (recommended)**

```
✓ Analytics data available at: output/analysis
  • Portfolio: output/analysis/portfolio_analysis.json
  • Buildings: output/analysis/buildings/
  • Rooms: output/analysis/rooms/
```

Already saved during analysis. Complete data structure preserved.

**2. Excel (.xlsx)**

Tabular export (under development):
- One sheet per building
- Room-level data
- Summary metrics
- Test results

**3. CSV files**

Multiple CSV files (under development):
- `portfolio_summary.csv`
- `building_metrics.csv`
- `room_compliance.csv`
- `test_results.csv`

**4. Markdown (.md)**

Documentation format (under development):
- Human-readable
- Suitable for reports
- Version control friendly

**5. Text (.txt)**

Plain text summaries (under development):
- Simple format
- Easy to read
- Good for logs

### Workflow Completion

```
✓ Workflow Complete!

Summary:
  • Data loaded from: data/my-buildings
  • Analytics processed and saved to: output/analysis
  • Workflow state: data_saved

Next Steps:
  • Review results in the output directory
  • Run 'hvx ieq start' to start a new analysis
  • Check documentation for advanced features

Thank you for using HVX IEQ Analytics!
```

## Navigation Commands

Throughout the workflow:

- **help** - Show context-specific help
- **quit** or **exit** - Exit workflow (with confirmation)
- **Ctrl+C** - Cancel current operation

## Tips for Best Results

### Data Preparation

1. **Organize files properly**
   ```
   data/
   └── buildings/
       └── building-name/
           └── sensors/
               └── room-name.csv
   ```

2. **Ensure data quality**
   - Consistent timestamp format
   - No large gaps in data
   - Valid sensor ranges

3. **Name files descriptively**
   - Room names help auto-detection
   - Use consistent naming conventions

### Standard Selection

1. **First time**: Use "Recommended"
2. **Regulatory compliance**: Choose specific required standards
3. **Comparison**: Use same standards across analyses
4. **Deep investigation**: Use "All standards"

### Report Generation

1. **For management**: Use portfolio_summary template
2. **For technical team**: Use building_detailed template
3. **Monthly reports**: Create custom template, save for reuse
4. **Quick check**: HTML format is fastest

### Automation

For recurring analysis:

```bash
#!/bin/bash
# Monthly analysis script

DATE=$(date +%Y-%m)
hvx ieq start \
  --directory data/monthly/$DATE \
  --auto \
  > logs/analysis_$DATE.log 2>&1
```

## Troubleshooting

### Workflow Interrupted

**Problem**: Workflow interrupted (Ctrl+C or error)

**Solution**: Partial results are saved. Check `output/analysis/` for completed analyses. Re-run workflow to complete.

### Can't Find Data Directory

**Problem**: System can't find data directory

**Solution**:
- Use absolute paths
- Check for typos
- Verify directory permissions
- Ensure directory exists

### Analysis Takes Too Long

**Problem**: Analysis running for extended time

**Solution**:
- Large datasets take longer (normal)
- Check system resources
- Use `--auto` mode to skip interactions
- Consider subset of data first

### Reports Won't Generate

**Problem**: PDF generation fails

**Solution**:
```bash
pip install weasyprint  # Recommended
```

Or use HTML format instead.

## See Also

- [IEQ Commands Reference](./ieq.md) - Command details
- [CLI Overview](./README.md) - Complete CLI guide
- [Chart Library](../CHART_QUICK_REFERENCE.md) - Available charts
- [Analytics Executors](../ANALYTICS_EXECUTORS_QUICK_REFERENCE.md) - Analysis details
