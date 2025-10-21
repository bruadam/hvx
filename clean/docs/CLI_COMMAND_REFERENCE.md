Move this file to docs/CLI_COMMAND_REFERENCE.md


# HVX Analytics - CLI Command Reference

Quick reference for all HVX CLI commands.

## Installation

```bash
cd clean/
uv pip install -e .  # or: pip install -e .
```

## Main Commands

```bash
hvx --help              # Show all commands
hvx --version           # Show version
hvx -v <command>        # Verbose mode
```

## Interactive Workflows

```bash
# IEQ Analysis
hvx ieq start                     # Interactive IEQ workflow
hvx ieq start -d data/building-a # With specific directory
hvx ieq start --auto             # Auto mode (no prompts)

# Energy Analysis (coming soon)
hvx energy start

# Default workflow (IEQ)
hvx start                         # Same as 'hvx ieq start'
hvx start --type energy          # Energy workflow
```

## Data Management

```bash
# Load and explore data
hvx data load <directory>         # Load building data
hvx data info <directory>         # Show directory info

# Examples
hvx data load data/building-a
hvx data info data/
```

## Analysis Commands

```bash
# Run analysis
hvx analyze run <directory>                      # Basic analysis
hvx analyze run <dir> --session-name <name>     # Save with session name
hvx analyze run <dir> --standard en16798-1      # Specific standard
hvx analyze run <dir> --save output/file.json   # Save to specific file

# Manage sessions
hvx analyze list                                 # List saved sessions

# Examples
hvx analyze run data/building-a --session-name oct_analysis
hvx analyze run data/ --session-name all_buildings
```

## Reporting Commands

```bash
# Generate reports
hvx report generate                              # Basic report (current analysis)
hvx report generate --session <name>            # From saved session
hvx report generate --template <file.yaml>      # With template
hvx report generate --output <file.html>        # Custom output path
hvx report generate --format html               # Output format

# Export data
hvx report export --format json                  # Export to JSON
hvx report export --format csv                   # Export to CSV
hvx report export --format excel                 # Export to Excel
hvx report export --session <name> --format excel   # From saved session

# List templates
hvx report list-templates                        # Show available templates

# Examples
hvx report generate --session oct_analysis --output october_report.html
hvx report export --session oct_analysis --format excel
```

## Command Chaining

```bash
# Chain commands for complete workflows
hvx analyze run data/building-a --session-name my_analysis && \
hvx report generate --session my_analysis --output report.html && \
hvx report export --session my_analysis --format excel

# Quick analysis + report
hvx analyze run data/ --session-name quick && hvx report generate --session quick
```

## Common Workflows

### Workflow 1: Interactive (Beginner-Friendly)

```bash
hvx ieq start
# Follow the prompts
# Analysis auto-saved at step 4
```

### Workflow 2: Quick Analysis (Fast)

```bash
hvx analyze run data/building-a --session-name building_a
# Done! Analysis saved, generate reports later
```

### Workflow 3: Complete Pipeline (Advanced)

```bash
# Step 1: Check data
hvx data info data/building-a

# Step 2: Run analysis with session
hvx analyze run data/building-a --session-name building_a_oct20

# Step 3: Generate multiple reports
hvx report generate --session building_a_oct20 --output executive_summary.html
hvx report generate --session building_a_oct20 --output detailed_report.html

# Step 4: Export in different formats
hvx report export --session building_a_oct20 --format json
hvx report export --session building_a_oct20 --format excel
```

### Workflow 4: Batch Processing

```bash
# Analyze multiple buildings
for building in data/*/; do
    name=$(basename "$building")
    hvx analyze run "$building" --session-name "${name}_analysis"
done

# Generate reports for all
hvx analyze list  # See all sessions
hvx report generate --session building_a_analysis
hvx report generate --session building_b_analysis
```

## Session Management

```bash
# List all saved sessions
hvx analyze list

# Use a session for reporting
hvx report generate --session <session_name>

# Export from a session
hvx report export --session <session_name> --format excel

# Session files are stored in:
# output/analyses/session_<name>.json
# output/analyses/rooms/<name>/*.json
# output/analyses/buildings/building_<name>.json
```

## Options Reference

### Global Options

```bash
-v, --verbose    # Enable verbose output (debugging)
--help           # Show help for any command
```

### Analyze Options

```bash
--session-name <name>    # Save with specific session name
--standard <std>         # Compliance standard (default: en16798-1)
--save <path>            # Save to specific file path
```

### Report Options

```bash
--session <name>         # Use saved session
--template <file>        # Report template file
--output <file>          # Output file path
--format <fmt>           # Format: html, pdf, json, csv, excel
```

### Workflow Options

```bash
-d, --directory <path>   # Data directory
-a, --auto               # Auto mode (no prompts)
--type <type>            # Analysis type: ieq, energy
```

## Output Locations

```bash
output/
├── analyses/            # Saved analysis sessions
├── reports/             # Generated reports
└── exports/             # Exported data files
```

## Help Commands

```bash
# Get help for any command
hvx --help
hvx data --help
hvx analyze --help
hvx report --help
hvx ieq --help
hvx energy --help

# Get help for subcommands
hvx data load --help
hvx analyze run --help
hvx report generate --help
```

## Troubleshooting

### Command not found

```bash
# Reinstall
cd clean/
uv pip install -e .
```

### Verbose mode for debugging

```bash
hvx -v analyze run data/building-a
```

### Check saved sessions

```bash
hvx analyze list
ls -la output/analyses/
```

### Clear cache/start fresh

```bash
rm -rf output/analyses/*
```

## Advanced Tips

### 1. Custom Session Names

Use descriptive session names for easy identification:
```bash
hvx analyze run data/building-a --session-name "building_a_baseline_oct2024"
```

### 2. Reuse Analysis

Analyze once, generate many reports:
```bash
hvx analyze run data/building-a --session-name baseline
hvx report generate --session baseline --output report1.html
hvx report generate --session baseline --output report2.html
```

### 3. Different Formats

Export the same analysis in multiple formats:
```bash
hvx report export --session my_analysis --format json
hvx report export --session my_analysis --format csv
hvx report export --session my_analysis --format excel
```

### 4. Automation

Script complete workflows:
```bash
#!/bin/bash
SESSION="building_analysis_$(date +%Y%m%d)"
hvx analyze run data/ --session-name "$SESSION"
hvx report generate --session "$SESSION" --output "report_$SESSION.html"
hvx report export --session "$SESSION" --format excel
```

## Quick Start

```bash
# 1. Install
cd clean/ && uv pip install -e .

# 2. Try interactive mode
hvx ieq start

# 3. Or try modular commands
hvx analyze run data/ --session-name test
hvx analyze list
hvx report generate --session test
```

---

**Full Documentation**: See `CLI_MODULAR_ARCHITECTURE.md` and `MODULAR_CLI_COMPLETE.md`

**Version**: 2.0.0  
**Date**: 2024-10-20
