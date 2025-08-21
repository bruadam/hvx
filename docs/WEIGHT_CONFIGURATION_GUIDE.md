# Enhanced IEQ Analytics CLI - Performance Score Weight Configuration

## Overview

The IEQ Analytics CLI now supports customizable performance score weights and thresholds, allowing users to adapt the analysis to their specific priorities and standards.

## Performance Score Formula

```
Performance Score = (Weight_Temperature × Temperature_Compliance) + 
                   (Weight_CO2 × CO2_Compliance) + 
                   (Weight_Humidity × Humidity_Compliance) + 
                   (Weight_Data_Quality × Data_Quality_Score × 100)
```

## New CLI Commands

### 1. View and Configure Weights

```bash
# View current weight configuration
ieq-analytics report weights

# Set custom weights (must sum to 1.0)
ieq-analytics report weights \
  --weight-temperature 0.25 \
  --weight-co2 0.5 \
  --weight-humidity 0.15 \
  --weight-data-quality 0.1 \
  --save-config

# Set custom thresholds
ieq-analytics report weights \
  --min-data-quality 0.85 \
  --min-comfort-compliance 85.0 \
  --save-config
```

### 2. Generate Reports with Custom Weights

```bash
# Generate report with custom weights
ieq-analytics report generate \
  --format pdf \
  --template executive \
  --include-plots \
  --weight-temperature 0.2 \
  --weight-co2 0.6 \
  --weight-humidity 0.1 \
  --weight-data-quality 0.1

# Generate report prioritizing data quality
ieq-analytics report generate \
  --weight-data-quality 0.3 \
  --weight-co2 0.35 \
  --weight-temperature 0.25 \
  --weight-humidity 0.1
```

## Default Configuration

| Parameter | Default Weight | Description |
|-----------|----------------|-------------|
| Temperature | 30% (0.3) | Thermal comfort compliance |
| CO2 | 40% (0.4) | Ventilation effectiveness (highest priority) |
| Humidity | 20% (0.2) | Moisture control |
| Data Quality | 10% (0.1) | Data completeness and reliability |

### Default Thresholds

- **Min Data Quality**: 80% (0.8)
- **Min Comfort Compliance**: 80%

## Weight Configuration Scenarios

### 1. Standard Office Environment (Default)
```bash
ieq-analytics report weights \
  --weight-temperature 0.3 \
  --weight-co2 0.4 \
  --weight-humidity 0.2 \
  --weight-data-quality 0.1
```
**Use case**: General office spaces where CO2 is most critical for productivity.

### 2. High-Precision Laboratory
```bash
ieq-analytics report weights \
  --weight-temperature 0.25 \
  --weight-co2 0.25 \
  --weight-humidity 0.25 \
  --weight-data-quality 0.25
```
**Use case**: Research facilities where all parameters are equally important.

### 3. Healthcare Facility
```bash
ieq-analytics report weights \
  --weight-temperature 0.35 \
  --weight-co2 0.35 \
  --weight-humidity 0.25 \
  --weight-data-quality 0.05
```
**Use case**: Hospitals where temperature and air quality are critical for patient comfort.

### 4. Data Center Monitoring
```bash
ieq-analytics report weights \
  --weight-temperature 0.5 \
  --weight-co2 0.1 \
  --weight-humidity 0.3 \
  --weight-data-quality 0.1
```
**Use case**: Server rooms where temperature control is paramount.

### 5. Pandemic Response Mode
```bash
ieq-analytics report weights \
  --weight-temperature 0.15 \
  --weight-co2 0.7 \
  --weight-humidity 0.1 \
  --weight-data-quality 0.05
```
**Use case**: Emphasizing ventilation effectiveness for infection control.

## Validation Features

### Weight Validation
- Weights must sum to exactly 1.0
- Individual weights must be between 0.0 and 1.0
- Clear error messages for invalid configurations

### Threshold Validation
- Data quality threshold: 0.0 - 1.0
- Comfort compliance threshold: 0.0 - 100.0

### Configuration Persistence
- Save custom configurations to `config/performance_weights.yaml`
- Load saved configurations automatically
- Override saved settings with CLI parameters

## Usage Examples

### Interactive Weight Setup
```bash
# View current weights
ieq-analytics report weights

# Adjust for CO2-priority environment
ieq-analytics report weights --weight-co2 0.6 --weight-temperature 0.2 --save-config

# Generate report with new weights
ieq-analytics report generate --include-plots
```

### One-Time Custom Analysis
```bash
# Generate report with temporary custom weights (not saved)
ieq-analytics report generate \
  --format pdf \
  --template executive \
  --weight-temperature 0.4 \
  --weight-co2 0.3 \
  --weight-humidity 0.2 \
  --weight-data-quality 0.1
```

### Batch Analysis with Different Priorities
```bash
# Generate multiple reports with different weight schemes
ieq-analytics report generate --weight-co2 0.6 --weight-temperature 0.2 --output-dir reports/co2_priority
ieq-analytics report generate --weight-temperature 0.5 --weight-co2 0.3 --output-dir reports/temp_priority
ieq-analytics report generate --weight-data-quality 0.3 --weight-co2 0.4 --output-dir reports/quality_priority
```

## Configuration File Format

The configuration is saved as YAML in `config/performance_weights.yaml`:

```yaml
weight_temperature: 0.3
weight_co2: 0.4
weight_humidity: 0.2
weight_data_quality: 0.1
min_data_quality: 0.8
min_comfort_compliance: 80.0
```

## Impact on Analysis

Changing weights affects:
- **Worst Performers Identification**: Rooms ranked by custom performance scores
- **Building Comparisons**: Comparative analysis uses custom weightings
- **Issue Flagging**: Thresholds determine which rooms are flagged for attention
- **Chart Generation**: Performance-based visualizations reflect custom priorities

## Best Practices

1. **Start with defaults** for general office environments
2. **Adjust gradually** - small weight changes can have significant impacts
3. **Document rationale** for custom weight schemes
4. **Test with different scenarios** to understand impact
5. **Save configurations** for consistency across analyses
6. **Use descriptive output directories** when comparing different weight schemes

This enhanced flexibility allows the IEQ Analytics system to adapt to diverse building types, regulatory requirements, and organizational priorities while maintaining scientific rigor in the analysis process.
