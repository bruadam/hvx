# Analytics Commands (Legacy)

The `hvx analytics` command group provides single-building analytics capabilities for CSV data files.

> **Note**: This is the legacy analytics workflow for single CSV files. For multi-building portfolio analysis, use the [`hvx analyze`](./analyze.md) commands instead.

## Overview

Analytics commands enable you to:
- Run IEQ analytics on individual CSV files
- List all saved analysis results
- View detailed analysis summaries
- Generate analysis data for reports

## Commands

### `hvx analytics run`

Run analytics on a single dataset (CSV or Parquet file).

#### Syntax

```bash
hvx analytics run DATA_PATH [OPTIONS]
```

#### Arguments

- `DATA_PATH` - Path to CSV or Parquet file containing sensor data (required)

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--name` | `-n` | TEXT | Auto-generated | Name for this analysis |
| `--config` | `-c` | PATH | Default config | Analytics configuration file |

#### CSV Requirements

Your CSV file must contain:
- `timestamp` column (datetime format)
- At least one sensor parameter column:
  - `temperature` (°C)
  - `co2` (ppm)
  - `humidity` (%)
  - `occupancy` (count or binary)
  - Other parameters as needed

Example CSV:
```csv
timestamp,temperature,co2,humidity,occupancy
2024-01-01 00:00:00,20.5,450,55,0
2024-01-01 01:00:00,20.3,430,54,0
2024-01-01 08:00:00,22.1,780,60,12
```

#### Examples

**Basic analysis (auto-generated name):**
```bash
hvx analytics run data/samples/building_sample.csv
```

**Analysis with custom name:**
```bash
hvx analytics run data/samples/building_sample.csv --name main_building
```

**Analysis with custom configuration:**
```bash
hvx analytics run data/samples/building_sample.csv \
  --name main_building \
  --config config/custom_analytics.yaml
```

**Analysis with Parquet file:**
```bash
hvx analytics run data/building_data.parquet --name warehouse_analysis
```

#### Output

The command displays:
- Processing progress with spinner
- Analysis completion status
- Analysis name and output path
- Summary metrics (compliance, rules evaluated, data quality)
- Command hint for report generation

Example output:
```
Running analytics on: data/samples/building_sample.csv

Processing... ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✓ Analysis complete
Analysis name: building_sample_2024-10-02
Output: output/analysis/building_sample_2024-10-02.json

Summary:
• Overall Compliance: 78.5%
• Rules Evaluated: 12
• Data Quality: 85.3%

Generate report with: hvx reports generate <template> --data building_sample_2024-10-02
```

#### Result Storage

Analysis results are saved as JSON files in `output/analysis/`:
```
output/analysis/
└── building_sample_2024-10-02.json
```

The JSON file contains:
- Metadata (building name, timestamp, data range)
- Summary metrics
- Detailed test results per parameter
- Compliance rates
- Data quality scores
- Key findings and recommendations

---

### `hvx analytics list`

List all saved analysis results.

#### Syntax

```bash
hvx analytics list
```

#### No Options

This command takes no options.

#### Examples

```bash
hvx analytics list
```

#### Output

Displays a table of all saved analyses:

```
Analysis Results
┌────────────────────────────────┬──────────────┬─────────────────────┐
│ Name                           │ Building     │ Timestamp           │
├────────────────────────────────┼──────────────┼─────────────────────┤
│ building_sample_2024-10-02     │ Building A   │ 2024-10-02 14:30:45 │
│ main_building                  │ Main Office  │ 2024-10-01 10:15:20 │
│ warehouse_analysis             │ Warehouse 1  │ 2024-09-28 16:45:33 │
└────────────────────────────────┴──────────────┴─────────────────────┘
```

If no analyses exist:
```
No analysis results found
Run analysis with: hvx analytics run <data_path>
```

#### Use Cases

1. **Find analysis names**: Get names for report generation
2. **Check history**: See what analyses have been run
3. **Verify completion**: Confirm analysis was saved successfully

---

### `hvx analytics show`

Show detailed analysis results summary.

#### Syntax

```bash
hvx analytics show ANALYSIS_NAME
```

#### Arguments

- `ANALYSIS_NAME` - Name of the analysis to display (required)

#### Examples

**Show analysis by name:**
```bash
hvx analytics show building_sample_2024-10-02
```

**Show named analysis:**
```bash
hvx analytics show main_building
```

#### Output

Displays comprehensive analysis information:

```
Analysis: building_sample_2024-10-02

Metadata:
• Building: Building A
• Timestamp: 2024-10-02 14:30:45
• Data Points: 8760
• Date Range: 2024-01-01 00:00:00 to 2024-12-31 23:00:00

Summary:
• Overall Compliance: 78.5%
• Rules Evaluated: 12
• Data Quality: 85.3%

Key Findings:
• CO2 levels exceeded threshold in 15% of occupied hours
• Temperature remained within comfort range 92% of the time
• Humidity levels occasionally low during winter months
• Overall indoor air quality acceptable
```

#### Use Cases

1. **Review results**: Check analysis outcomes before generating reports
2. **Verify metrics**: Confirm compliance rates and quality scores
3. **Identify issues**: See key findings and problem areas
4. **Report preparation**: Gather information for stakeholder communication

---

## Workflow Examples

### Basic Analytics Workflow

```bash
# 1. Run analysis
hvx analytics run data/building.csv --name my_building

# 2. List all analyses
hvx analytics list

# 3. Show analysis details
hvx analytics show my_building

# 4. Generate report
hvx reports generate simple_report --data my_building
```

### Batch Analysis Workflow

```bash
# Analyze multiple buildings
for csv in data/*.csv; do
  basename=$(basename "$csv" .csv)
  hvx analytics run "$csv" --name "$basename"
done

# List all results
hvx analytics list

# Review each analysis
hvx analytics show building1
hvx analytics show building2
hvx analytics show building3
```

### Analysis with Custom Configuration

```bash
# 1. Create custom config
cat > config/strict_analysis.yaml << 'EOF'
parameters:
  temperature:
    tests:
      - name: thermal_comfort
        min: 21
        max: 24
        severity: HIGH
  co2:
    tests:
      - name: air_quality
        max: 800
        severity: CRITICAL
EOF

# 2. Run analysis with config
hvx analytics run data/building.csv \
  --name strict_analysis \
  --config config/strict_analysis.yaml

# 3. Review results
hvx analytics show strict_analysis
```

---

## Understanding Results

### Overall Compliance

The overall compliance percentage indicates how much of the time all measured parameters met their respective criteria:
- **90-100%**: Excellent - building performing very well
- **75-89%**: Good - minor issues
- **60-74%**: Fair - notable issues requiring attention
- **Below 60%**: Poor - significant problems

### Rules Evaluated

The number of different test rules that were applied to the data. Each parameter can have multiple tests (e.g., temperature might have both comfort range and variability tests).

### Data Quality

Data quality score reflects:
- Completeness (missing data percentage)
- Consistency (outliers and anomalies)
- Validity (values within expected ranges)

A score below 70% may indicate sensor issues or data collection problems.

### Key Findings

Automatically generated insights highlighting:
- Parameters exceeding thresholds
- Patterns of non-compliance
- Data quality issues
- Recommendations for improvement

---

## Output File Structure

Analysis JSON files contain:

```json
{
  "analysis_name": "building_sample_2024-10-02",
  "timestamp": "2024-10-02T14:30:45",
  "metadata": {
    "building_name": "Building A",
    "data_points": 8760,
    "date_range": {
      "start": "2024-01-01T00:00:00",
      "end": "2024-12-31T23:00:00"
    }
  },
  "summary": {
    "overall_compliance": 78.5,
    "total_rules_evaluated": 12,
    "data_quality_score": 85.3,
    "key_findings": [
      "CO2 levels exceeded threshold in 15% of occupied hours",
      "Temperature within comfort range 92% of the time"
    ]
  },
  "results": {
    "temperature": {
      "compliance_rate": 92.0,
      "tests": {
        "thermal_comfort": {
          "passed": true,
          "compliance": 92.0,
          "details": "..."
        }
      }
    },
    "co2": {
      "compliance_rate": 85.0,
      "tests": {
        "air_quality": {
          "passed": true,
          "compliance": 85.0,
          "details": "..."
        }
      }
    }
  }
}
```

---

## Integration with Reports

Analytics results are designed to feed into the report generation system:

```bash
# 1. Run analytics
hvx analytics run data/building.csv --name q1_analysis

# 2. Generate report from analysis
hvx reports generate simple_report --data q1_analysis

# 3. Find report in output/reports/
```

The report will include:
- All metrics from the analysis
- Generated charts based on the data
- Key findings and recommendations
- Professional PDF formatting

---

## Comparison: Analytics vs Analyze

| Feature | `hvx analytics` (Legacy) | `hvx analyze` (Modern) |
|---------|-------------------------|------------------------|
| Input | Single CSV file | Multi-building dataset (pickle) |
| Scope | Single building/space | Portfolio with hierarchy |
| Output | Single JSON file | Hierarchical JSON structure |
| Levels | N/A | Room, Level, Building, Portfolio |
| Use Case | Quick single-building analysis | Enterprise portfolio analysis |
| Reports | Yes, via templates | No (use JSON for custom reports) |

**When to use `hvx analytics`:**
- Single building or space
- Quick analysis of CSV data
- Need PDF reports
- Simple workflow

**When to use `hvx analyze`:**
- Multiple buildings
- Need hierarchical analysis
- Portfolio-level insights
- Investment prioritization

---

## Best Practices

1. **Use descriptive names**: Name analyses clearly for easy identification
2. **Consistent naming**: Use a naming convention (e.g., `building_date`)
3. **Regular analysis**: Run analysis periodically to track improvements
4. **Keep configurations**: Version control your custom config files
5. **Review before reporting**: Use `show` command before generating reports
6. **Archive results**: Keep JSON files for historical comparison
7. **Document findings**: Export or document key findings from summaries

---

## Common Issues

**Issue: "Error: timestamp column not found"**
- **Solution**: Ensure CSV has a column named `timestamp`

**Issue: "No data for parameter"**
- **Solution**: Check CSV contains the expected sensor columns

**Issue: "Analysis not found"**
- **Solution**: Use `hvx analytics list` to see available analyses
- Ensure you use the exact name shown in the list

**Issue: "Unable to parse timestamps"**
- **Solution**: Use standard datetime format: `YYYY-MM-DD HH:MM:SS`

**Issue: "Configuration file error"**
- **Solution**: Validate YAML syntax in configuration file
- Check parameter and test names match expected values

---

## See Also

- [Analyze Commands](./analyze.md) - Modern hierarchical analysis
- [Reports Commands](./reports.md) - Generate PDF reports from analytics
- [Data Commands](./data.md) - Load multi-building datasets
- [CLI Overview](./README.md) - Complete CLI documentation
