# IEQ Commands - Indoor Environmental Quality Analysis

The `hvx ieq` command group provides comprehensive Indoor Environmental Quality (IEQ) analysis capabilities through an interactive workflow.

## Overview

IEQ analysis in HVX focuses on evaluating building indoor environmental quality based on international standards, identifying compliance issues, and providing actionable recommendations for improvement.

## Available Commands

### hvx ieq start

Launch the interactive IEQ analysis workflow.

```bash
hvx ieq start [OPTIONS]
```

**Options:**
- `-d, --directory PATH` - Start with a specific data directory
- `-a, --auto` - Run in automated mode with default values (no prompts)
- `--help` - Show command help

**Examples:**

```bash
# Start interactive workflow (will prompt for data directory)
hvx ieq start

# Start with specific data directory
hvx ieq start --directory data/samples/sample-extensive-data

# Run automated workflow with defaults
hvx ieq start --directory data/my-buildings --auto
```

**What it does:**

The interactive workflow guides you through 7 key steps:

1. **Load Building Data** - Load and validate multi-building datasets
2. **Select Building Type** - Choose: office, school, residential, healthcare, or mixed
3. **Choose Standards** - Select applicable IEQ standards and guidelines
4. **Process Analytics** - Run hierarchical analysis across portfolio/building/level/room
5. **Explore Results** - Interactive exploration with filtering and navigation
6. **Generate Reports** - Create professional HTML/PDF reports
7. **Export Data** - Save analytics in various formats (JSON, Excel, CSV, Markdown)

### hvx ieq info

Display IEQ terminology, concepts, and standards information.

```bash
hvx ieq info
```

Shows explanations of:
- IEQ parameters (temperature, CO2, humidity, etc.)
- Standards (EN16798-1, BR18, Danish Guidelines)
- Compliance categories
- Data quality metrics
- Terminology definitions

## Interactive Workflow Details

### Step 1: Load Building Data

**What happens:**
- You provide a data directory path
- System analyzes directory structure
- Auto-detects buildings, levels, and rooms
- Auto-infers room types from names
- Validates data quality

**Expected directory structure:**
```
data/
└── buildings/
    ├── building-1/
    │   ├── climate/           # Optional outdoor/climate data
    │   │   └── climate.csv
    │   └── sensors/
    │       ├── room1.csv
    │       ├── room2.csv
    │       └── room3.csv
    └── building-2/
        └── sensors/
            └── room1.csv
```

**CSV format requirements:**
- `timestamp` column (datetime)
- Sensor columns: `temperature`, `co2`, `humidity`, `occupancy`, etc.

**Interactive options:**
- Assign room types if not auto-detected
- Review data summary before proceeding

### Step 2: Select Building Type

Choose the primary building type to determine applicable standards:

1. **Office** - Commercial office buildings
2. **School / Educational** - Schools, universities, training facilities
3. **Residential / Housing** - Apartments, condos, residential buildings
4. **Healthcare / Hospital** - Medical facilities, clinics, hospitals
5. **Mixed / Other** - Mixed-use or other building types

**Why it matters:** Building type determines which standards are most relevant and helps auto-select appropriate compliance categories.

### Step 3: Choose Standards & Tests

Select which standards and guidelines to apply:

**Option 1: Recommended for building type (auto-select)**
- System selects appropriate standards based on building type
- Fastest option with sensible defaults

**Option 2: All standards, tests & guidelines**
- Applies all available standards
- Comprehensive analysis

**Option 3: Specific standards only**
- Choose from available standards:
  - **EN16798-1** - European standard with Categories I-IV
  - **BR18** - Danish Building Regulations 2018
  - **Danish Guidelines** - Danish indoor climate guidelines
- Standards are defined in `src/core/analytics/ieq/config/standards/`

**Option 4: Custom selection (advanced)**
- Fine-tune specific tests and categories
- Advanced filtering options

### Step 4: Process Analytics

**Automated hierarchical analysis:**

1. **Room-level analysis**
   - Individual room compliance
   - Test results for each parameter
   - Data quality scoring
   - Issue identification

2. **Level-level aggregation**
   - Floor/level summaries
   - Aggregated compliance rates
   - Common issues per level

3. **Building-level aggregation**
   - Building-wide performance
   - Investment priority scoring
   - Building-specific recommendations

4. **Portfolio-level aggregation**
   - Portfolio-wide metrics
   - Best/worst performing buildings
   - Strategic recommendations

**Output:**
- JSON files for each entity (room, level, building, portfolio)
- Saved to `output/analysis/`

### Step 5: Explore Results

**Interactive exploration options:**

1. **View summary and continue** - Quick overview
2. **Explore results interactively** - Deep dive with filtering
3. **Get smart recommendations** - AI-powered improvement suggestions

**What you can see:**
- Compliance rates by standard
- EN16798-1 category assignments
- Data quality scores
- Critical issues
- Room rankings
- Top recommendations

### Step 6: Generate Reports

**Report options:**

1. **Use predefined template**
   - `building_detailed.yaml` - Comprehensive building report
   - `portfolio_summary.yaml` - High-level overview
   - Choose output format (HTML, PDF, or both)

2. **Create custom template**
   - Select sections to include
   - Configure loops over buildings/rooms
   - Save for future use

**Output formats:**
- **HTML** - Web-viewable reports (always available)
- **PDF** - Printable reports (requires weasyprint or pdfkit)

**Reports saved to:** `output/reports/`

### Step 7: Export Data

Export analysis data in various formats:

1. **JSON** - Full structured data (already saved during analysis)
2. **Excel** - Spreadsheet format (coming soon)
3. **CSV** - Multiple CSV files (coming soon)
4. **Markdown** - Documentation format (coming soon)
5. **Text** - Plain text summaries (coming soon)

## Standards Reference

### EN16798-1 - European Standard

Four categories based on percentage of occupancy hours within ranges:

**Temperature (°C):**
- Category I: 20-24 (heating), 23-26 (cooling)
- Category II: 19-25 (heating), 23-26 (cooling)
- Category III: 18-25 (heating), 22-27 (cooling)
- Category IV: Outside other categories

**CO2 (ppm above outdoor):**
- Category I: <550 ppm
- Category II: <800 ppm
- Category III: <1350 ppm
- Category IV: >1350 ppm

**Compliance threshold:** >95% of time within category limits

### BR18 - Danish Building Regulations

Specific requirements for:
- Thermal comfort
- Air quality (CO2)
- Ventilation rates
- Humidity levels

### Danish Guidelines

Additional guidelines for:
- Temperature exceedances
- CO2 accumulation
- Seasonal considerations
- Room-type specific requirements

## Use Cases

### Use Case 1: Monthly Compliance Report

```bash
# Generate standardized monthly report
hvx ieq start --directory data/2024-10/ --auto

# Results:
# - Compliance metrics
# - Issue identification
# - Auto-generated report
```

### Use Case 2: New Building Assessment

```bash
# Interactive analysis with exploration
hvx ieq start --directory data/new-building/

# Follow prompts to:
# - Select appropriate standards
# - Review detailed results
# - Generate custom report
```

### Use Case 3: Portfolio Overview

```bash
# Analyze entire building portfolio
hvx ieq start --directory data/portfolio-buildings/

# Focus on:
# - Portfolio-level metrics
# - Building comparisons
# - Investment priorities
```

### Use Case 4: Problem Investigation

```bash
# Deep dive into specific issues
hvx ieq start --directory data/problematic-building/

# Use exploration feature to:
# - Identify root causes
# - View detailed timeseries
# - Generate recommendations
```

## Tips & Best Practices

1. **Data Preparation**
   - Ensure consistent timestamp formats
   - Include all relevant parameters
   - Organize data by building/room hierarchy

2. **Standard Selection**
   - Use "recommended" for first-time analysis
   - Apply building-specific standards when known
   - Consider regulatory requirements

3. **Exploration**
   - Start with portfolio view
   - Drill down to worst-performing entities
   - Review recommendations for each level

4. **Reports**
   - Use predefined templates for consistency
   - Create custom templates for specific audiences
   - Export both HTML and PDF when possible

5. **Automation**
   - Use `--auto` mode for scheduled analyses
   - Script recurring reports
   - Integrate with data pipelines

## Troubleshooting

### Data Loading Fails

**Problem:** Directory structure not recognized

**Solution:**
```
Ensure data follows structure:
data/buildings/building-name/sensors/room.csv
```

### Analysis Errors

**Problem:** Missing required columns

**Solution:**
```
Check CSV files contain:
- timestamp (required)
- temperature, co2, humidity (at least one)
```

### PDF Generation Fails

**Problem:** No PDF backend available

**Solution:**
```bash
pip install weasyprint  # Best option
# or
pip install pdfkit
```

### Workflow Interrupted

**Problem:** Accidentally closed workflow

**Solution:**
```
Analysis results are saved incrementally.
Check output/analysis/ for partial results.
Re-run workflow to complete.
```

## Advanced Usage

### Automated Batch Processing

```bash
#!/bin/bash
# Process multiple building portfolios

for dir in data/portfolios/*/; do
  portfolio_name=$(basename "$dir")
  hvx ieq start \
    --directory "$dir" \
    --auto \
    > logs/${portfolio_name}.log 2>&1
done
```

### Integration with CI/CD

```yaml
# GitHub Actions example
- name: Run IEQ Analysis
  run: |
    hvx ieq start --directory data/latest --auto

- name: Archive Reports
  uses: actions/upload-artifact@v2
  with:
    name: ieq-reports
    path: output/reports/
```

## See Also

- [Interactive Workflow Guide](./interactive-workflow.md) - Detailed workflow documentation
- [CLI Overview](./README.md) - Complete CLI reference
- [Chart Library](../CHART_QUICK_REFERENCE.md) - Visualization reference
- [Analytics Executors](../ANALYTICS_EXECUTORS_QUICK_REFERENCE.md) - Engine details
