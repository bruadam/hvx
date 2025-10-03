# Start Command Quick Reference

## Three Simple Modes

| Mode | Command | Use Case |
|------|---------|----------|
| **Interactive** | `hvx start` | First-time, guided workflow |
| **Automated** | `hvx start --source-dir <dir>` | Full pipeline with options |
| **Quick** | `hvx start --quick --source-dir <dir>` | Fast analysis with defaults |

## Mode 1: Interactive (Default)

```bash
# Start from beginning
hvx start

# With existing dataset
hvx start --dataset output/dataset.pkl

# With existing analysis
hvx start --analysis output/analysis
```

**What happens:**
- Guided prompts for each step
- Interactive data loading
- Configuration choices
- Exploration offered
- Report generation prompted

## Mode 2: Automated Pipeline

```bash
# Basic
hvx start --source-dir data/

# With test set
hvx start --source-dir data/ --test-set summer_analysis

# With template
hvx start --source-dir data/ --report-template exec_summary

# Explore after analysis
hvx start --source-dir data/ --explore

# Skip report
hvx start --source-dir data/ --no-report

# Full options
hvx start --source-dir data/ \
  --output-dir results/2024-10 \
  --portfolio-name "October Portfolio" \
  --test-set compliance_tests \
  --report-template monthly_report \
  --config config/custom.yaml \
  --verbose
```

**Pipeline steps:**
1. Load data from source-dir
2. Run analysis with tests
3. Explore (if --explore)
4. Generate report (unless --no-report)

## Mode 3: Quick

```bash
# Quick analysis
hvx start --quick --source-dir data/

# Custom output
hvx start --quick --source-dir data/ --output-dir results/
```

**What happens:**
- Fast load with auto-inference
- Analysis with default tests
- Summary display only
- No exploration or reports

## Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dataset PATH` | Use existing dataset | None |
| `--analysis PATH` | Use existing analysis | None |
| `--source-dir DIR` | Source data directory | None |
| `--output-dir DIR` | Output directory | `output/` |
| `--test-set TEXT` | Test set name | All tests |
| `--config PATH` | Tests config file | `config/tests.yaml` |
| `--report-template TEXT` | Template name | `standard_building` |
| `--portfolio-name TEXT` | Portfolio name | `Portfolio` |
| `--explore` | Launch explorer | No |
| `--no-report` | Skip report | No (report generated) |
| `--quick` | Quick mode | No |
| `--verbose` | Detailed output | No |

## Quick Examples

### Example 1: First Analysis
```bash
hvx start
# Interactive guidance through all steps
```

### Example 2: Daily Check
```bash
hvx start --quick --source-dir data/latest/
# Fast analysis, see results
```

### Example 3: Monthly Report
```bash
hvx start --source-dir data/current/ \
  --output-dir reports/2024-10 \
  --test-set compliance_tests \
  --report-template monthly_compliance
```

### Example 4: Investigation
```bash
hvx start --source-dir data/problem-areas/ \
  --test-set detailed_analysis \
  --explore \
  --no-report
```

### Example 5: Custom Analysis
```bash
# First, create custom test set
hvx tests set-create

# Then run with it
hvx start --source-dir data/ --test-set my_tests
```

### Example 6: Re-analyze Dataset
```bash
hvx start --dataset existing.pkl --test-set new_tests
```

## Output Structure

```
output/                      # (or custom --output-dir)
├── dataset.pkl             # Loaded dataset
├── analysis/               # Analysis results
│   ├── portfolio.json
│   ├── buildings/
│   │   └── *.json
│   ├── levels/
│   │   └── *.json
│   └── rooms/
│       └── *.json
└── report.pdf             # Generated report
```

## Pipeline Stages

### Stage 1: Load
```
═══ Step 1: Loading Data ═══
Loading building data... ━━━━━━━━━━━━━━━
✓ Loaded 3 buildings, 45 rooms
✓ Dataset saved to: output/dataset.pkl
```

### Stage 2: Analyze
```
═══ Step 2: Running Analysis ═══
Using test set: summer_analysis
Running hierarchical analysis... ━━━━━━━
✓ Analysis complete
✓ Results saved to: output/analysis

Portfolio Results:
  Buildings: 3
  Rooms: 45
  Avg Compliance: 73.2%
  Avg Quality: 81.5%
```

### Stage 3: Explore (Optional)
```
═══ Step 3: Exploring Results ═══
Launching interactive analysis explorer...
[Interactive explorer opens]
```

### Stage 4: Report (Optional)
```
═══ Step 4: Generating Report ═══
Using template: exec_summary
Output file: output/report.pdf
✓ Report generated
```

## Integration

### With Test Management
```bash
# Create test set
hvx tests set-create

# Use in pipeline
hvx start --source-dir data/ --test-set my_tests
```

### With Templates
```bash
# Create template
hvx report-templates create

# Use in pipeline
hvx start --source-dir data/ --report-template my_template
```

### After Pipeline
```bash
# Explore results
hvx analyze explore output/analysis

# Generate additional reports
hvx reports generate --analysis-dir output/analysis

# View summaries
hvx analyze summary output/analysis
```

## Automation Examples

### Daily Automated Report
```bash
#!/bin/bash
hvx start --source-dir /data/daily/ \
  --output-dir /reports/$(date +%Y-%m-%d) \
  --test-set standard_tests \
  --report-template daily_summary \
  --verbose
```

### Batch Processing
```bash
#!/bin/bash
for building in buildings/*/; do
  name=$(basename "$building")
  hvx start --quick --source-dir "$building" \
    --output-dir "results/$name"
done
```

### Conditional Analysis
```bash
#!/bin/bash
if [ -f dataset.pkl ]; then
  # Re-analyze existing
  hvx start --dataset dataset.pkl
else
  # Fresh analysis
  hvx start --source-dir data/
fi
```

## Tips

1. **Start with interactive** - Learn the workflow
2. **Use quick for testing** - Fast iteration
3. **Automate regular reports** - Use automated mode
4. **Reuse datasets** - Skip loading with --dataset
5. **Combine options** - Mix test sets and templates
6. **Use verbose** - Debug issues
7. **Skip steps** - Use --no-report or --dataset
8. **Explore problems** - Use --explore for investigation

## Troubleshooting

### Issue: Directory not found
```bash
hvx start --source-dir invalid/
# Error: Directory 'invalid/' does not exist
```
**Solution:** Check path

### Issue: Test set not found
```bash
hvx start --source-dir data/ --test-set invalid
# ✗ Test set 'invalid' not found
# Available test sets: ...
```
**Solution:** Use `hvx tests sets` to list available

### Issue: Template not found
```bash
hvx start --source-dir data/ --report-template invalid
# Warning: Template 'invalid' not found
```
**Solution:** Use `hvx report-templates list`

### Cancel Pipeline
Press `Ctrl+C` anytime to cancel:
```
^C
Pipeline cancelled by user
```

## See Also

- [Full Documentation](./start-command.md)
- [Tests Commands](./tests-command.md)
- [Report Templates](./report-templates-command.md)
- [Analysis Commands](./analyze-command.md)
