# Graphs Commands

The `hvx graphs` command group provides discovery and preview capabilities for the chart library.

## Overview

Graphs commands enable you to:
- Browse available chart types
- View detailed chart information
- Generate preview charts with dummy data
- Explore chart categories and parameters

## Commands

### `hvx graphs list`

List all available charts in the library.

#### Syntax

```bash
hvx graphs list [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--category` | `-c` | TEXT | - | Filter by category |

#### Examples

**List all charts:**
```bash
hvx graphs list
```

**Filter by category:**
```bash
hvx graphs list --category compliance
hvx graphs list --category timeseries
hvx graphs list -c heatmap
```

#### Output

Displays a table of available charts:

```
Available Charts
┌─────────────────────────┬──────────────────────────────┬────────────┬──────────┐
│ ID                      │ Name                         │ Category   │ Type     │
├─────────────────────────┼──────────────────────────────┼────────────┼──────────┤
│ co2_compliance_bar      │ CO2 Compliance Bar Chart     │ compliance │ bar      │
│ temperature_timeseries  │ Temperature Time Series      │ timeseries │ line     │
│ occupancy_heatmap       │ Occupancy Heatmap            │ heatmap    │ heatmap  │
│ humidity_distribution   │ Humidity Distribution        │ statistical│ histogram│
│ multi_parameter_line    │ Multi-Parameter Line Chart   │ timeseries │ line     │
└─────────────────────────┴──────────────────────────────┴────────────┴──────────┘

Available categories: compliance, timeseries, heatmap, statistical
```

#### Chart Categories

- **compliance** - Compliance and threshold-based charts
- **timeseries** - Time-based line and area charts
- **heatmap** - Heat maps for pattern visualization
- **statistical** - Distributions, histograms, box plots
- **comparison** - Comparative bar and grouped charts
- **other** - Miscellaneous chart types

---

### `hvx graphs info`

Show detailed information about a specific chart.

#### Syntax

```bash
hvx graphs info CHART_ID
```

#### Arguments

- `CHART_ID` - ID of the chart to display (required)

#### Examples

**Show chart information:**
```bash
hvx graphs info co2_compliance_bar
```

**View timeseries chart details:**
```bash
hvx graphs info temperature_timeseries
```

**Check heatmap configuration:**
```bash
hvx graphs info occupancy_heatmap
```

#### Output

Displays comprehensive chart information:

```
╭────────────────────────────────────────────────╮
│ CO2 Compliance Bar Chart                       │
│                                                │
│ Description:                                   │
│ Bar chart showing CO2 compliance rates across  │
│ different time periods (daily, weekly,         │
│ monthly). Displays percentage of time CO2      │
│ levels were within acceptable thresholds.      │
│                                                │
│ Details:                                       │
│ • ID: co2_compliance_bar                       │
│ • Category: compliance                         │
│ • Type: bar                                    │
│ • Fixture: co2_compliance_fixture.json         │
│                                                │
│ Parameters:                                    │
│ • threshold (float): CO2 threshold in ppm      │
│   Default: 1000                                │
│ • period (string): Aggregation period          │
│   Default: weekly                              │
│ • title (string): Chart title                  │
│   Default: CO2 Compliance Analysis             │
╰────────────────────────────────────────────────╯
```

#### Information Sections

1. **Name and Description**: What the chart visualizes
2. **Details**: Technical information (ID, category, type, fixture)
3. **Parameters**: Configurable options with types and defaults

---

### `hvx graphs preview`

Generate a preview of a chart using dummy data.

#### Syntax

```bash
hvx graphs preview CHART_ID [OPTIONS]
```

#### Arguments

- `CHART_ID` - ID of the chart to preview (required)

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--output` | `-o` | PATH | Auto-generated | Output file path for the chart |
| `--config` | `-c` | PATH | - | Chart configuration file (YAML) |

#### Examples

**Basic preview with default settings:**
```bash
hvx graphs preview co2_compliance_bar
```

**Preview with custom output path:**
```bash
hvx graphs preview temperature_timeseries -o output/temp_preview.png
```

**Preview with configuration file:**
```bash
hvx graphs preview co2_compliance_bar -c config/chart_config.yaml
```

**Preview multiple charts:**
```bash
hvx graphs preview co2_compliance_bar -o charts/co2.png
hvx graphs preview temperature_timeseries -o charts/temp.png
hvx graphs preview occupancy_heatmap -o charts/occupancy.png
```

#### Configuration File Format

Create a YAML file to customize chart parameters:

```yaml
# config/chart_config.yaml
threshold: 1200        # Custom CO2 threshold
period: monthly        # Different aggregation period
title: "Custom CO2 Analysis"
color: "#FF6B6B"       # Custom color
show_legend: true      # Display legend
```

Then use it:
```bash
hvx graphs preview co2_compliance_bar -c config/chart_config.yaml
```

#### Output

The command displays:
- Generation status
- Output file path
- Success confirmation

Example output:
```
Generating preview for 'co2_compliance_bar' with dummy data...
✓ Chart preview generated: output/charts/co2_compliance_bar_preview.png
```

The generated PNG file can be:
- Viewed directly
- Included in presentations
- Used as template reference
- Shared with stakeholders

#### Default Output Paths

If `--output` is not specified, charts are saved to:
```
output/charts/<chart_id>_preview.png
```

Examples:
- `output/charts/co2_compliance_bar_preview.png`
- `output/charts/temperature_timeseries_preview.png`
- `output/charts/occupancy_heatmap_preview.png`

---

## Workflow Examples

### Explore and Preview Workflow

```bash
# 1. List all available charts
hvx graphs list

# 2. Get info about interesting charts
hvx graphs info co2_compliance_bar
hvx graphs info temperature_timeseries

# 3. Generate previews
hvx graphs preview co2_compliance_bar -o previews/co2.png
hvx graphs preview temperature_timeseries -o previews/temp.png

# 4. View the generated charts
open previews/*.png
```

### Category-Based Exploration

```bash
# Explore compliance charts
hvx graphs list --category compliance

# Preview all compliance charts
for chart in $(hvx graphs list --category compliance | awk 'NR>3 {print $2}'); do
  hvx graphs preview "$chart" -o "previews/compliance_${chart}.png"
done
```

### Custom Configuration Workflow

```bash
# 1. Get chart info to see parameters
hvx graphs info co2_compliance_bar

# 2. Create configuration file
cat > config/my_chart.yaml << 'EOF'
threshold: 1200
period: monthly
title: "Monthly CO2 Compliance Report"
color: "#2E86AB"
EOF

# 3. Generate preview with config
hvx graphs preview co2_compliance_bar -c config/my_chart.yaml -o charts/custom_co2.png

# 4. View result
open charts/custom_co2.png
```

### Preview All Charts

```bash
# Create previews directory
mkdir -p output/all_previews

# Generate preview for every chart
hvx graphs list | tail -n +4 | awk '{print $2}' | while read chart_id; do
  echo "Generating preview for $chart_id..."
  hvx graphs preview "$chart_id" -o "output/all_previews/${chart_id}.png"
done

# View all previews
open output/all_previews/*.png
```

---

## Chart Registry

Charts are defined in the registry file at `src/graphs/registry.yaml`. This file contains:
- Chart IDs and names
- Categories and types
- Fixture data references
- Parameter definitions
- Default values

Example registry entry:
```yaml
- id: co2_compliance_bar
  name: "CO2 Compliance Bar Chart"
  description: "Bar chart showing CO2 compliance by period"
  category: compliance
  type: bar
  fixture: co2_compliance_fixture.json
  renderer: bar_charts.render_co2_compliance
  parameters:
    - name: threshold
      type: float
      default: 1000
      description: "CO2 threshold in ppm"
    - name: period
      type: string
      default: weekly
      description: "Aggregation period (daily/weekly/monthly)"
```

---

## Dummy Data Fixtures

Preview charts use fixture files containing representative dummy data. Fixtures are located in:
```
src/graphs/fixtures/
├── co2_compliance_fixture.json
├── temperature_timeseries_fixture.json
├── occupancy_heatmap_fixture.json
└── ...
```

Fixture files contain:
- Sample timeseries data
- Realistic value ranges
- Complete parameter sets
- Typical patterns

This ensures previews accurately represent how charts will look with real data.

---

## Use Cases

### 1. Chart Selection
Before creating a report template, explore available charts to choose the most appropriate visualizations.

```bash
hvx graphs list
hvx graphs info temperature_timeseries
hvx graphs preview temperature_timeseries
```

### 2. Stakeholder Presentation
Generate chart previews to show stakeholders what analytics visualizations will look like.

```bash
# Generate presentation-ready previews
mkdir -p presentation/charts
hvx graphs preview co2_compliance_bar -o presentation/charts/co2.png
hvx graphs preview temperature_timeseries -o presentation/charts/temp.png
hvx graphs preview occupancy_heatmap -o presentation/charts/occupancy.png
```

### 3. Template Development
When creating custom report templates, preview charts to understand their appearance and data requirements.

```bash
# Check what charts are available
hvx graphs list

# View chart details
hvx graphs info co2_compliance_bar

# Generate preview to see layout
hvx graphs preview co2_compliance_bar
```

### 4. Configuration Testing
Test different chart configurations before using them in reports.

```bash
# Test different thresholds
echo "threshold: 800" > config/strict.yaml
hvx graphs preview co2_compliance_bar -c config/strict.yaml -o charts/strict_800.png

echo "threshold: 1200" > config/lenient.yaml
hvx graphs preview co2_compliance_bar -c config/lenient.yaml -o charts/lenient_1200.png

# Compare visually
open charts/strict_800.png charts/lenient_1200.png
```

---

## Chart Integration

Charts from the library are used in:

1. **Report Templates**: Templates specify which charts to include
   ```yaml
   # template.yaml
   charts:
     - id: co2_compliance_bar
       title: "CO2 Compliance"
       config:
         threshold: 1000
     - id: temperature_timeseries
       title: "Temperature Trend"
   ```

2. **Custom Reports**: Programmatic report generation using the graph service
   ```python
   from src.services.graph_service import GraphService
   
   service = GraphService()
   service.render_chart(
       chart_id='co2_compliance_bar',
       data=analysis_data,
       output_path='output/charts/co2.png'
   )
   ```

3. **Analysis Outputs**: Automatic chart generation during analysis workflows

---

## Best Practices

1. **Preview before using**: Always preview charts before adding to templates
2. **Check parameters**: Use `info` command to understand available options
3. **Use categories**: Filter by category to find relevant charts quickly
4. **Test configurations**: Preview with different configs to find optimal settings
5. **Organize outputs**: Use descriptive output paths for easy identification
6. **Document choices**: Keep notes on why specific charts were selected
7. **Version fixtures**: Update fixture data to reflect current standards

---

## Common Issues

**Issue: "Chart not found"**
- **Solution**: Use `hvx graphs list` to see valid chart IDs
- Check spelling and case sensitivity

**Issue: "Fixture file missing"**
- **Solution**: Ensure fixtures directory exists at `src/graphs/fixtures/`
- Check that the referenced fixture file is present

**Issue: "Invalid configuration"**
- **Solution**: Verify YAML syntax in configuration file
- Use `hvx graphs info <chart_id>` to see valid parameter names and types

**Issue: "Output directory not writable"**
- **Solution**: Ensure output directory exists and has write permissions
- Create directory with `mkdir -p output/charts`

**Issue: "Preview looks wrong"**
- **Solution**: Check fixture data is representative
- Verify chart renderer is correctly implemented
- Review configuration parameters

---

## See Also

- [Templates Commands](./templates.md) - Create templates using charts
- [Reports Commands](./reports.md) - Generate reports with charts
- [CLI Overview](./README.md) - Complete CLI documentation
- Chart renderers in `src/graphs/renderers/`
- Registry file at `src/graphs/registry.yaml`
