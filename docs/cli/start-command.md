# Start Command - Complete Pipeline

The `hvx start` command provides end-to-end analysis pipelines from data loading through report generation. Choose between interactive guided workflows or fully automated pipelines.

## Overview

The start command orchestrates the complete analysis workflow:

1. **Load Data** - Import building data from CSV/Excel files
2. **Run Analysis** - Perform hierarchical analysis with configurable tests
3. **Explore Results** - Interactive exploration of analysis results
4. **Generate Reports** - Create formatted reports from templates

## Available Commands

### Interactive Pipeline

```bash
hvx start interactive
```

Launches an interactive, guided workflow that walks you through each step with prompts and choices.

**Options:**
- `--dataset PATH` - Start with existing dataset (skip loading)
- `--analysis PATH` - Start with existing analysis (skip analysis step)

**Examples:**

```bash
# Start from beginning (interactive data loading)
hvx start interactive

# Start with existing dataset
hvx start interactive --dataset output/dataset.pkl

# Start with completed analysis
hvx start interactive --analysis output/analysis
```

**What it does:**
- Guides you through data loading with interactive prompts
- Asks for test configuration preferences
- Runs analysis with progress display
- Offers to explore results
- Prompts for report generation options

### Complete Pipeline

```bash
hvx start pipeline <source_dir>
```

Automated end-to-end pipeline with configurable options. Runs the complete workflow with minimal user interaction.

**Arguments:**
- `SOURCE_DIR` - Directory containing building data files

**Options:**
- `-o, --output-dir PATH` - Base output directory (default: `output/`)
- `--portfolio-name TEXT` - Portfolio name (default: `Portfolio`)
- `--config PATH` - Tests configuration file (default: `config/tests.yaml`)
- `--test-set TEXT` - Specific test set to use
- `--report-template TEXT` - Report template for generation
- `--explore / --no-explore` - Launch explorer after analysis (default: no)
- `--generate-report / --no-generate-report` - Generate report (default: yes)
- `--verbose` - Show detailed output

**Examples:**

```bash
# Basic pipeline with defaults
hvx start pipeline data/samples/sample-extensive-data

# With custom test set and template
hvx start pipeline data/ \
  --test-set summer_analysis \
  --report-template exec_summary

# Custom output directory
hvx start pipeline data/ --output-dir results/2024-q4

# Skip report generation, explore instead
hvx start pipeline data/ \
  --no-generate-report \
  --explore

# Full automation (no interaction at all)
hvx start pipeline data/ \
  --no-explore \
  --report-template standard_building

# With verbose output
hvx start pipeline data/ --verbose

# Custom portfolio name
hvx start pipeline data/ --portfolio-name "Building Portfolio Q4 2024"
```

**Output Structure:**
```
output/
├── dataset.pkl           # Loaded dataset
├── analysis/             # Analysis results
│   ├── portfolio.json
│   ├── buildings/
│   │   └── *.json
│   ├── levels/
│   │   └── *.json
│   └── rooms/
│       └── *.json
└── report.pdf           # Generated report
```

### Quick Pipeline

```bash
hvx start quick <source_dir>
```

Fastest pipeline with sensible defaults. Minimal configuration, maximum speed.

**Arguments:**
- `SOURCE_DIR` - Directory containing building data

**Options:**
- `-o, --output-dir PATH` - Base output directory (default: `output/`)

**Examples:**

```bash
# Quick analysis with defaults
hvx start quick data/samples/sample-extensive-data

# Custom output directory
hvx start quick data/ --output-dir results/
```

**What it does:**
- Loads data with auto-inference
- Runs analysis with default tests
- Displays summary
- Saves all results
- No interactive steps

## Pipeline Stages

### Stage 1: Data Loading

**What happens:**
- Scans source directory for CSV/Excel files
- Auto-infers building hierarchy (buildings → levels → rooms)
- Auto-infers room types from names
- Validates data structure
- Saves dataset to pickle file

**Progress:**
```
═══ Step 1: Loading Data ═══

Loading building data... ━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Loaded 3 buildings, 45 rooms
✓ Dataset saved to: output/dataset.pkl
```

**Verbose output shows:**
- List of all buildings
- Rooms per building
- Available parameters per building
- Data completeness

### Stage 2: Analysis

**What happens:**
- Loads test configuration
- Applies test set (if specified)
- Runs hierarchical analysis:
  - Room-level analysis
  - Level-level aggregation
  - Building-level aggregation
  - Portfolio-level aggregation
- Saves results to JSON files

**Progress:**
```
═══ Step 2: Running Analysis ═══

Using test set: summer_analysis
Config: config/tests.yaml
Running hierarchical analysis... ━━━━━━━━━━━━━━━━━━━
✓ Analysis complete
✓ Results saved to: output/analysis

Portfolio Results:
  Buildings: 3
  Rooms: 45
  Avg Compliance: 73.2%
  Avg Quality: 81.5%
```

**Verbose output shows:**
- Common issues across portfolio
- Best/worst performing buildings
- Detailed compliance metrics

### Stage 3: Exploration (Optional)

**What happens:**
- Launches interactive analysis explorer
- Navigate through portfolio → buildings → levels → rooms
- View test results, issues, recommendations
- Export specific results

**When enabled:**
```
═══ Step 3: Exploring Results ═══

Launching interactive analysis explorer...

[Interactive explorer opens]
```

**Controls:**
- Navigate hierarchy
- Filter by criteria
- View details
- Export data

### Stage 4: Report Generation (Optional)

**What happens:**
- Loads report template
- Renders sections with analysis data
- Generates formatted output (PDF/HTML/etc.)
- Saves report file

**Progress:**
```
═══ Step 4: Generating Report ═══

Using template: exec_summary
Output file: output/report.pdf
Generating report... ━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Report generated: output/report.pdf
```

## Use Cases and Workflows

### Use Case 1: Quick Data Check

**Goal:** Quickly analyze data to check overall status

```bash
hvx start quick data/new-building/
```

**Output:** Summary statistics and saved results for deeper analysis

### Use Case 2: Monthly Compliance Report

**Goal:** Generate standardized monthly compliance report

```bash
hvx start pipeline data/2024-10/ \
  --output-dir reports/2024-10 \
  --portfolio-name "October 2024 Portfolio" \
  --test-set compliance_tests \
  --report-template monthly_compliance \
  --no-explore
```

**Output:** Automated compliance report ready for distribution

### Use Case 3: Investigate Problem Buildings

**Goal:** Analyze specific buildings with exploration

```bash
hvx start pipeline data/problem-buildings/ \
  --test-set detailed_analysis \
  --explore \
  --no-generate-report
```

**Output:** Interactive session to investigate issues

### Use Case 4: Custom Analysis Workflow

**Goal:** Run analysis with custom test set and explore results

```bash
# Create custom test set first
hvx tests set-create
# Name: winter_deep_dive
# Select winter-specific tests

# Run pipeline with custom set
hvx start pipeline data/winter-data/ \
  --test-set winter_deep_dive \
  --output-dir results/winter-2024 \
  --explore
```

### Use Case 5: Automated Reporting Pipeline

**Goal:** Fully automated pipeline for scheduled reports

```bash
#!/bin/bash
# Script for automated reporting

hvx start pipeline /data/latest/ \
  --output-dir /reports/$(date +%Y-%m-%d) \
  --portfolio-name "Daily Portfolio Report" \
  --test-set standard_tests \
  --report-template daily_summary \
  --no-explore \
  --verbose > /logs/pipeline.log 2>&1
```

### Use Case 6: Interactive First-Time Analysis

**Goal:** Guided workflow for new users

```bash
hvx start interactive
```

**Process:**
1. Interactive prompts guide data loading
2. Choose analysis options
3. Review results in explorer
4. Generate custom report

## Pipeline Configuration

### Test Configuration

Control which tests to run:

```bash
# Use all tests in config
hvx start pipeline data/ --config config/tests.yaml

# Use specific test set
hvx start pipeline data/ --test-set summer_analysis
```

### Output Configuration

Control where results are saved:

```bash
# Default output structure
hvx start pipeline data/
# Output to: output/

# Custom base directory
hvx start pipeline data/ --output-dir results/2024-q4/
# Output to: results/2024-q4/
```

### Report Configuration

Control report generation:

```bash
# Generate report with standard template
hvx start pipeline data/ --report-template standard_building

# Skip report generation
hvx start pipeline data/ --no-generate-report

# Specify template
hvx start pipeline data/ --report-template custom_executive
```

### Exploration Configuration

Control interactive exploration:

```bash
# Enable exploration after analysis
hvx start pipeline data/ --explore

# Skip exploration (default)
hvx start pipeline data/ --no-explore
```

## Error Handling

### Common Issues

**Issue: Source directory not found**
```bash
$ hvx start pipeline data/nonexistent/
✗ Error: Invalid value for 'SOURCE_DIR': Directory 'data/nonexistent/' does not exist.
```

**Solution:** Check path and ensure directory exists

**Issue: Test set not found**
```bash
$ hvx start pipeline data/ --test-set invalid_set
✗ Test set 'invalid_set' not found.
Available test sets:
  • summer_analysis
  • winter_compliance
```

**Solution:** Use `hvx tests sets` to list available test sets

**Issue: Invalid test configuration**
```bash
$ hvx start pipeline data/ --config invalid.yaml
✗ Error: Invalid value for '--config': Path 'invalid.yaml' does not exist.
```

**Solution:** Check config path or omit to use default

### Cancelling Pipeline

Press `Ctrl+C` to cancel at any time:

```
^C
Pipeline cancelled by user
```

Partial results are saved up to the cancellation point.

## Performance Tips

1. **Use Quick for Testing** - Fast iteration during development
   ```bash
   hvx start quick data/sample/
   ```

2. **Skip Exploration for Automation** - Faster in scripts
   ```bash
   hvx start pipeline data/ --no-explore
   ```

3. **Use Test Sets** - Only run needed tests
   ```bash
   hvx start pipeline data/ --test-set focused_tests
   ```

4. **Reuse Datasets** - Skip loading if dataset exists
   ```bash
   hvx start interactive --dataset output/dataset.pkl
   ```

5. **Batch Processing** - Process multiple directories
   ```bash
   for dir in data/*/; do
     hvx start quick "$dir" --output-dir "results/$(basename $dir)"
   done
   ```

## Integration with Other Commands

The start command integrates with the entire CLI ecosystem:

### Before Start

Prepare test configurations:
```bash
# Create custom test set
hvx tests set-create

# Create custom template
hvx report-templates create
```

### After Start

Work with results:
```bash
# Explore results
hvx analyze explore output/analysis

# Generate additional reports
hvx reports generate --analysis-dir output/analysis

# View specific summaries
hvx analyze summary output/analysis --level building
```

## Best Practices

1. **Start with Quick** - Use `quick` for initial data validation
2. **Use Test Sets** - Create focused test sets for specific analyses
3. **Name Portfolios** - Use descriptive portfolio names
4. **Organize Output** - Use dated output directories
5. **Version Control** - Keep test configs and templates in version control
6. **Automate Regularly** - Use `pipeline` in cron jobs or CI/CD
7. **Explore Interactively** - Use `--explore` when investigating issues
8. **Save Datasets** - Reuse loaded datasets for multiple analyses
9. **Verbose for Debugging** - Use `--verbose` when troubleshooting
10. **Template Reuse** - Create template library for consistent reporting

## Complete Workflow Examples

### Example 1: First Analysis of New Building

```bash
# Step 1: Quick check
hvx start quick data/new-building/

# Step 2: Review results
hvx analyze explore output/analysis

# Step 3: Full analysis with custom tests
hvx tests set-create
# Create focused test set

hvx start pipeline data/new-building/ \
  --test-set my_tests \
  --report-template detailed_analysis
```

### Example 2: Monthly Compliance Report

```bash
# Automated monthly script
DATE=$(date +%Y-%m)
hvx start pipeline /data/current/ \
  --output-dir /reports/$DATE \
  --portfolio-name "Monthly Report $DATE" \
  --test-set compliance_tests \
  --report-template monthly_compliance \
  --no-explore
```

### Example 3: Investigation Workflow

```bash
# Interactive investigation
hvx start interactive --dataset existing_data.pkl

# Or automated with exploration
hvx start pipeline data/ \
  --test-set detailed_tests \
  --explore \
  --no-generate-report
```

## See Also

- [Analyze Commands](./analyze-command.md) - Analysis operations
- [Tests Commands](./tests-command.md) - Test management
- [Report Templates](./report-templates-command.md) - Template management
- [Data Commands](./data-command.md) - Data operations
