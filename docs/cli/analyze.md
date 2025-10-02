# Analyze Commands

The `hvx analyze` command group provides hierarchical analysis capabilities for building portfolios.

## Overview

Analyze commands enable you to:
- Run comprehensive hierarchical analysis across multiple buildings
- Analyze at room, level, building, and portfolio levels
- Generate JSON results for each hierarchical level
- View analysis summaries with rich formatting

## Commands

### `hvx analyze run`

Run hierarchical analysis on a loaded building dataset.

#### Syntax

```bash
hvx analyze run DATASET_FILE [OPTIONS]
```

#### Arguments

- `DATASET_FILE` - Path to dataset pickle file (`.pkl`) created by `hvx data load` (required)

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--config` | - | PATH | `config/tests.yaml` | Path to tests configuration file |
| `--output` | - | PATH | `output/analysis` | Output directory for analysis results |
| `--portfolio-name` | - | TEXT | `Portfolio` | Name for the portfolio analysis |
| `--no-individual-files` | - | FLAG | - | Skip saving individual JSON files per room/level/building |
| `--verbose` | - | FLAG | - | Show verbose output |

#### Analysis Hierarchy

The command performs analysis at four levels:

1. **Room Level** - Individual room analysis with test results
2. **Level Level** - Floor/level aggregations with room rankings
3. **Building Level** - Building-wide metrics with level summaries
4. **Portfolio Level** - Cross-building analysis with investment priorities

#### Configuration File

The analysis uses a YAML configuration file to define test criteria. Default: `config/tests.yaml`

Example structure:
```yaml
parameters:
  temperature:
    tests:
      - name: thermal_comfort
        description: "Thermal comfort range"
        min: 20
        max: 26
        severity: HIGH
        
  co2:
    tests:
      - name: air_quality
        description: "CO2 levels for good air quality"
        max: 1000
        severity: CRITICAL
        
  humidity:
    tests:
      - name: humidity_range
        description: "Relative humidity comfort range"
        min: 30
        max: 70
        severity: MEDIUM
```

#### Output Structure

Analysis results are saved as JSON files in a hierarchical structure:

```
output/analysis/
├── portfolio_analysis.json     # Portfolio-level analysis
├── buildings/                  # Building-level analyses
│   ├── building_1.json
│   ├── building_2.json
│   └── building_3.json
├── levels/                     # Level-level analyses
│   ├── level_1_0.json
│   ├── level_1_1.json
│   ├── level_2_0.json
│   └── ...
└── rooms/                      # Room-level analyses
    ├── building_1_0_room_101.json
    ├── building_1_0_room_102.json
    ├── building_1_1_room_201.json
    └── ...
```

#### Examples

**Basic analysis with default settings:**
```bash
hvx analyze run output/dataset.pkl
```

**Analysis with custom portfolio name:**
```bash
hvx analyze run output/dataset.pkl --portfolio-name "Q1 2024 Portfolio"
```

**Analysis with custom configuration:**
```bash
hvx analyze run output/dataset.pkl --config config/my_tests.yaml
```

**Analysis with custom output directory:**
```bash
hvx analyze run output/dataset.pkl --output results/q1_analysis
```

**Analysis without individual files (portfolio summary only):**
```bash
hvx analyze run output/dataset.pkl --no-individual-files
```

**Analysis with verbose output:**
```bash
hvx analyze run output/dataset.pkl --verbose
```

**Complete example:**
```bash
hvx analyze run output/dataset.pkl \
  --portfolio-name "HTK Office Buildings" \
  --config config/tests.yaml \
  --output output/analysis \
  --verbose
```

#### Output

The command displays:
- Loading progress
- Dataset summary (building and room counts)
- Analysis progress indicator
- Results summary with key metrics
- Output structure visualization

Example output:
```
╭──────────── Hierarchical Analysis ────────────╮
│ Dataset: output/dataset.pkl                   │
│ Config: config/tests.yaml                     │
│ Output: output/analysis                       │
╰───────────────────────────────────────────────╯

✓ Loaded 3 buildings with 45 rooms

Running hierarchical analysis... ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

Analysis Summary

Portfolio: HTK Office Buildings
┌───────────────────────┬────────┐
│ Metric                │  Value │
├───────────────────────┼────────┤
│ Buildings             │      3 │
│ Total Levels          │      5 │
│ Total Rooms           │     45 │
│ Avg Compliance        │  78.5% │
│ Avg Quality Score     │  85.3% │
└───────────────────────┴────────┘

Common Issues:
  • High CO2 levels (occurs in 2 buildings)
  • Temperature out of range (occurs in 1 building)

Buildings Analyzed: 3
┌─────────────┬───────┬────────┬────────────┬─────────┐
│ Building    │ Rooms │ Levels │ Compliance │ Quality │
├─────────────┼───────┼────────┼────────────┼─────────┤
│ Building 1  │    20 │      2 │      82.1% │   88.5% │
│ Building 2  │    15 │      2 │      75.3% │   84.2% │
│ Building 3  │    10 │      1 │      78.1% │   83.1% │
└─────────────┴───────┴────────┴────────────┴─────────┘

Output Structure:
  output/analysis/
    ├── portfolio.json
    ├── buildings/
    │   └── building_1.json
    │   └── building_2.json
    │   └── building_3.json
    ├── levels/
    │   └── *.json (5 files)
    └── rooms/
        └── *.json (45 files)

✓ Analysis complete! Results saved to: output/analysis
```

#### Analysis Metrics

Each analysis level includes:

**Room Level:**
- Overall compliance rate
- Parameter-specific test results
- Data completeness and quality scores
- Critical issues and recommendations
- Status (GOOD, WARNING, CRITICAL)

**Level Level:**
- Average compliance across rooms
- Best/worst performing rooms
- Room count and aggregated metrics
- Common issues at level

**Building Level:**
- Average compliance across levels
- Level and room counts
- Best/worst performing rooms
- Building-wide recommendations
- Investment priority ranking

**Portfolio Level:**
- Overall compliance across buildings
- Building count and aggregated statistics
- Best/worst performing buildings
- Common issues across portfolio
- Investment priorities with impact estimates

---

### `hvx analyze summary`

Display analysis summary from saved results.

#### Syntax

```bash
hvx analyze summary ANALYSIS_DIR [OPTIONS]
```

#### Arguments

- `ANALYSIS_DIR` - Path to directory containing analysis results (required)

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--level` | - | CHOICE | `portfolio` | Analysis level to display: `portfolio`, `building`, `level`, or `room` |
| `--entity-id` | - | TEXT | - | Specific entity ID to display |

#### Entity IDs

When using `--entity-id`, use these formats:
- **Building**: `building-1`, `building-2`, etc.
- **Level**: `level-1-0`, `level-1-1` (building-level format)
- **Room**: `building_1_0_room_101`, `building_1_1_room_201` (building_level_room format)

#### Examples

**View portfolio summary:**
```bash
hvx analyze summary output/analysis
```

or explicitly:
```bash
hvx analyze summary output/analysis --level portfolio
```

**List all buildings:**
```bash
hvx analyze summary output/analysis --level building
```

**View specific building:**
```bash
hvx analyze summary output/analysis --level building --entity-id building-1
```

**List all levels:**
```bash
hvx analyze summary output/analysis --level level
```

**View specific level:**
```bash
hvx analyze summary output/analysis --level level --entity-id level-1-0
```

**List sample rooms:**
```bash
hvx analyze summary output/analysis --level room
```

**View specific room:**
```bash
hvx analyze summary output/analysis --level room --entity-id building_1_0_room_101
```

#### Portfolio Summary Output

```
╭────────── Portfolio Analysis ──────────╮
│ Name: HTK Office Buildings             │
│ Buildings: 3                           │
╰────────────────────────────────────────╯

Portfolio Metrics
┌────────────────────────┬──────────────────┐
│ Metric                 │            Value │
├────────────────────────┼──────────────────┤
│ Total Buildings        │                3 │
│ Total Levels           │                5 │
│ Total Rooms            │               45 │
│ Avg Compliance Rate    │            78.5% │
│ Avg Quality Score      │            85.3% │
│ Analysis Date          │ 2024-10-02 14:30 │
└────────────────────────┴──────────────────┘

Best Performing Buildings:
  • Building 1: 82.1%
  • Building 3: 78.1%
  • Building 2: 75.3%

Worst Performing Buildings:
  • Building 2: 75.3%

Common Issues:
  • High CO2 levels (occurs 15 times)
  • Temperature out of range (occurs 8 times)

Investment Priorities:
  1. Building 2 - 75.3% compliance (high impact)
  2. Building 3 - 78.1% compliance (medium impact)
```

#### Building Summary Output

```
╭───────── Building Analysis ─────────╮
│ ID: building-1                      │
│ Name: Building 1                    │
╰─────────────────────────────────────╯

Building Metrics
┌─────────────────┬──────────┐
│ Metric          │    Value │
├─────────────────┼──────────┤
│ Levels          │        2 │
│ Rooms           │       20 │
│ Avg Compliance  │    82.1% │
│ Avg Quality     │    88.5% │
│ Status          │     GOOD │
└─────────────────┴──────────┘

Best Performing Rooms:
  • Conference 101: 95.2%
  • Office 105: 92.8%
  • Meeting 201: 91.5%

Worst Performing Rooms:
  • Storage 110: 65.3%
  • Office 108: 72.1%
  • Break Room: 74.5%
```

#### Level Summary Output

```
╭─────── Level Analysis ───────╮
│ ID: level-1-0                │
│ Name: Ground Floor           │
╰──────────────────────────────╯

Level Metrics
┌─────────────────┬──────────┐
│ Metric          │    Value │
├─────────────────┼──────────┤
│ Rooms           │       10 │
│ Avg Compliance  │    83.5% │
│ Avg Quality     │    89.2% │
│ Status          │     GOOD │
└─────────────────┴──────────┘

Best Performing Rooms:
  • Conference 101: 95.2%
  • Office 105: 92.8%

Worst Performing Rooms:
  • Storage 110: 65.3%
  • Office 108: 72.1%
```

#### Room Summary Output

```
╭──────── Room Analysis ────────╮
│ ID: building_1_0_room_101     │
│ Name: Conference 101          │
╰───────────────────────────────╯

Room Metrics
┌────────────────────┬──────────────────────────────┐
│ Metric             │                        Value │
├────────────────────┼──────────────────────────────┤
│ Overall Compliance │                        95.2% │
│ Data Completeness  │                        98.5% │
│ Quality Score      │                        97.1% │
│ Parameters         │ temperature, co2, humidity   │
│ Status             │                         GOOD │
│ Data Period        │ 2024-01-01 to 2024-01-31     │
└────────────────────┴──────────────────────────────┘

Test Results:
┌───────────────────┬─────────────┬────────────┬──────────┐
│ Test              │ Parameter   │ Compliance │ Severity │
├───────────────────┼─────────────┼────────────┼──────────┤
│ thermal_comfort   │ temperature │      98.5% │     HIGH │
│ air_quality       │ co2         │      92.1% │ CRITICAL │
│ humidity_range    │ humidity    │      95.0% │   MEDIUM │
└───────────────────┴─────────────┴────────────┴──────────┘

Recommendations:
  • Monitor CO2 levels during peak occupancy
  • Consider increasing ventilation rate
```

---

## Workflow Examples

### Complete Analysis Workflow

```bash
# 1. Load data
hvx data load data/my-buildings -o output/dataset.pkl -f pickle

# 2. Run analysis
hvx analyze run output/dataset.pkl --portfolio-name "Q1 2024"

# 3. View portfolio summary
hvx analyze summary output/analysis

# 4. Identify problematic buildings
hvx analyze summary output/analysis --level building

# 5. Investigate specific building
hvx analyze summary output/analysis --level building --entity-id building-2

# 6. Check specific level
hvx analyze summary output/analysis --level level --entity-id level-2-0

# 7. Review problematic rooms
hvx analyze summary output/analysis --level room --entity-id building_2_0_room_205
```

### Quick Portfolio Review

```bash
# Run analysis and view summary in one go
hvx analyze run output/dataset.pkl --portfolio-name "My Portfolio" && \
  hvx analyze summary output/analysis
```

### Custom Configuration Workflow

```bash
# 1. Edit configuration
vim config/tests.yaml

# 2. Run analysis with custom config
hvx analyze run output/dataset.pkl \
  --config config/tests.yaml \
  --portfolio-name "Custom Analysis"

# 3. View results
hvx analyze summary output/analysis
```

### Building-Specific Analysis

```bash
# Run analysis
hvx analyze run output/dataset.pkl

# Review each building
for building in building-1 building-2 building-3; do
  echo "=== $building ==="
  hvx analyze summary output/analysis --level building --entity-id $building
done
```

---

## Understanding Analysis Results

### Compliance Rate

The compliance rate represents the percentage of time that measurements meet the defined test criteria:
- **90-100%**: Excellent - minimal issues
- **75-89%**: Good - minor issues that should be addressed
- **60-74%**: Fair - significant issues requiring attention
- **Below 60%**: Poor - critical issues needing immediate action

### Quality Score

The quality score reflects data completeness and reliability:
- **90-100%**: Excellent data quality
- **75-89%**: Good data quality with minor gaps
- **60-74%**: Fair quality with notable gaps
- **Below 60%**: Poor quality - results may be unreliable

### Status Values

- **GOOD**: All metrics within acceptable ranges
- **WARNING**: Some metrics outside acceptable ranges
- **CRITICAL**: Multiple or severe issues detected
- **INSUFFICIENT_DATA**: Not enough data for reliable analysis

### Severity Levels

Test failures are categorized by severity:
- **CRITICAL**: Immediate health/safety concern (e.g., very high CO2)
- **HIGH**: Significant comfort/productivity impact
- **MEDIUM**: Moderate impact on comfort
- **LOW**: Minor deviation from ideal conditions
- **INFO**: Informational only

---

## Best Practices

1. **Run analysis after data loading**: Always inspect data first with `hvx data inspect`
2. **Use descriptive portfolio names**: Help identify different analysis runs
3. **Keep configuration files**: Version control your test configurations
4. **Review at all levels**: Start at portfolio, drill down to problems
5. **Compare time periods**: Run separate analyses for different periods
6. **Document thresholds**: Comment your configuration files
7. **Archive results**: Keep JSON files for historical comparison
8. **Use verbose for debugging**: Add `--verbose` when troubleshooting

---

## Common Issues

**Issue: "Dataset file not found"**
- **Solution**: Ensure you've run `hvx data load` first and saved to `.pkl` format

**Issue: "Configuration file not found"**
- **Solution**: Verify `config/tests.yaml` exists or specify path with `--config`

**Issue: "No data for parameter"**
- **Solution**: Check that your CSV files contain the required parameter columns

**Issue: "Insufficient data for analysis"**
- **Solution**: Ensure rooms have enough data points (typically >100 hours)

**Issue: "Analysis shows unexpected results"**
- **Solution**: Verify test thresholds in configuration are appropriate for your use case

---

## See Also

- [Data Commands](./data.md) - Load and inspect data before analysis
- [CLI Overview](./README.md) - Complete CLI documentation
- Configuration files in `config/tests.yaml`
