Move this file to docs/CLI_QUICK_START.md


# CLI Quick Start Guide

## Installation

```bash
cd clean/
pip install -e .
```

Verify installation:
```bash
ieq --version
ieq --help
```

## Basic Usage

### Start Interactive Workflow

```bash
ieq start
```

This launches the interactive 7-step workflow:
1. Load Building Data
2. Select Standards
3. Configure Tests
4. Run Analysis
5. Explore Results
6. Generate Reports
7. Export Data

### With Options

```bash
# Specify data directory
ieq start --directory data/my-building

# Auto mode (use defaults, no prompts)
ieq start --auto

# Verbose output (for debugging)
ieq start --verbose

# Combine options
ieq start --auto --directory data/my-building --verbose
```

## Workflow Steps

### Step 1: Load Building Data

```
Enter path to your data directory: data/my-building
```

The CLI will:
- Validate the directory exists
- Load building data
- Show summary (rooms loaded)

### Step 2: Select Standards

```
Available Standards
┌──────┬─────────────────┬──────────────────┬───────┐
│  #   │ Standard        │ Description      │ Tests │
├──────┼─────────────────┼──────────────────┼───────┤
│  1   │ EN 16798-1      │ European std...  │  18   │
│  2   │ Danish Guide... │ Danish regs...   │   2   │
└──────┴─────────────────┴──────────────────┴───────┘

Select standards (comma-separated numbers or 'all'): 1
```

### Step 3: Configure Tests

Shows tests available for selected standards.
Option to customize (select specific tests).

### Step 4: Run Analysis

```
Running analysis... ⠋
✓ Analysis complete - 93.5% compliance
```

### Step 5: Explore Results

```
What would you like to view?
1. Building summary
2. All rooms
3. Failing rooms only
4. Room details
5. Continue to reports

Select option [1/2/3/4/5] (5):
```

### Step 6: Generate Reports

```
Available templates:
1. Building Detailed Report
2. Portfolio Summary
3. Room Comparison

Select template [1/2/3] (1): 1

✓ Report generated!
  Saved to: output/reports/report.html
```

### Step 7: Export Data

```
Export analysis data? [y/N]: y

Export format [json/csv/excel] (json): json

✓ Data exported!
  Saved to: output/exports/analysis.json
```

## Tips

### Quick Exit
Type `quit` or `exit` at any prompt, or press `Ctrl+C` to exit gracefully.

### Context Help
Type `?` at any prompt for context-specific help.

### Defaults
Press Enter to accept the default value shown in brackets.

### Auto Mode
Use `--auto` for unattended execution (CI/CD, batch processing):
```bash
ieq start --auto --directory data/building-a
```

## Command Reference

### Main Commands

```bash
ieq                      # Show help
ieq --version           # Show version
ieq start               # Interactive workflow
```

### Analyze Commands (coming soon)

```bash
ieq analyze run <dir>         # Run analysis
ieq analyze list              # List past analyses
ieq analyze show <id>         # Show analysis details
```

### Report Commands (coming soon)

```bash
ieq report generate           # Generate report
ieq report list-templates     # List available templates
ieq report list               # List generated reports
```

## Examples

### Example 1: Complete Workflow

```bash
$ ieq start

Welcome to IEQ Analytics! 🌡️

Step 1: Load Building Data
Enter path to your data directory [data/samples]: data/my-building
✓ Loaded 15 rooms from my-building

Step 2: Select Standards
Available Standards...
Select standards: 1
✓ Selected: EN 16798-1

Step 3: Configure Tests
Found 18 tests for selected standards
✓ Configured 18 tests

Step 4: Run Analysis
Running analysis... ━━━━━━━━━━━━━━━━ 100%
✓ Analysis complete - 93.5% compliance

Step 5: Explore Results
What would you like to view?
1. Building summary
...
Select option: 5

Step 6: Generate Reports
Available templates...
Select template: 1
✓ Report generated!

✓ Workflow Complete!
  Rooms Analyzed: 15
  Overall Compliance: 93.5%
  Report Generated: output/reports/report.html
```

### Example 2: Auto Mode

```bash
$ ieq start --auto --directory data/building-a

Running in auto mode - using defaults

✓ 1. Load Building Data - 15 rooms loaded
✓ 2. Select Standards - EN 16798-1
✓ 3. Configure Tests - 18 tests
✓ 4. Run Analysis - 93.5% compliance
✓ 5. Explore Results - (skipped in auto mode)
✓ 6. Generate Reports - report.html
✓ 7. Export Data - (skipped)

✓ Workflow Complete!
```

### Example 3: Verbose Mode

```bash
$ ieq start --verbose

# Shows detailed progress and debug information
# Useful for troubleshooting
```

## Troubleshooting

### Command Not Found

```bash
$ ieq
command not found: ieq
```

**Solution**: Reinstall with `pip install -e .`

### Directory Not Found

```
✗ Error: Directory not found: /path/to/data
💡 Suggestion: Please check the path and try again
```

**Solution**: Verify the directory exists and path is correct

### Keyboard Interrupt

```
⚠ Workflow cancelled by user
```

This is normal - press Ctrl+C to exit anytime.

## Getting Help

```bash
# General help
ieq --help

# Command-specific help
ieq start --help

# Context help
# Type '?' at any prompt during interactive workflow
```

## What's Next?

The CLI is now **fully integrated** with the clean architecture! 

**Working features:**
✅ Real data loading from directories
✅ Actual IEQ analysis with AnalysisEngine
✅ Building-level aggregation
✅ HTML report generation
✅ Data export (JSON/CSV/Excel)

For detailed integration status, see `CLI_INTEGRATION_COMPLETE.md`.

## Files

- **Implementation Guide**: `core/cli/README.md`
- **Implementation Plan**: `docs/CLI_IMPLEMENTATION_PLAN.md`
- **Implementation Summary**: `docs/CLI_IMPLEMENTATION_SUMMARY.md`
- **This Guide**: `CLI_QUICK_START.md`

---

**Ready to use!** Type `ieq start` to begin.
