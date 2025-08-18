# Analytics Engine for Indoor Environmental Quality

This repository provides a comprehensive analytics engine for IEQ (Indoor Environmental Quality) assessment using IoT indoor climate sensors from various sources.

The analytics engine processes CSV files containing sensor data from multiple rooms, maps them to standardized formats, and generates comprehensive reports with visualizations and insights. It supports data mapping, quality assessment, comfort analysis, and building-level aggregation.

This repository was developed by Bruno Adam and used for indoor environmental quality assessments conducted during an internship at the municipality of Høje Taastrup in Denmark.

## Features

- 📊 **Data Mapping**: Intelligent column mapping with interactive and automated options
- 🏢 **Building Management**: Hierarchical building and room structure using Pydantic models
- 🔬 **Analytics Engine**: Comprehensive IEQ analysis including comfort compliance, temporal patterns, and correlations
- 📈 **Visualizations**: Automatic generation of time series plots, heatmaps, and distribution charts
- 📋 **Reporting**: Export results in JSON, CSV, and visualization formats
- 🛠️ **CLI Interface**: User-friendly command-line interface for all operations
- ⚙️ **Configuration**: Flexible configuration system for column mappings and parameters

## Set up your Python environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Quick Start

### Option 1: Complete Pipeline (Recommended)
Run the complete analysis pipeline with a single command:

```bash
python main.py run --data-dir data/raw/concatenated --output-dir output
```

### Option 2: Step-by-Step Process

1. **Inspect your data** (optional but recommended):
   ```bash
   python main.py inspect --data-dir-path data/raw/concatenated
   ```

2. **Map your data**:
   ```bash
   python main.py mapping --data-dir-path data/raw/concatenated --output-dir output
   ```

3. **Analyze the mapped data**:
   ```bash
   python main.py analyze --data-dir output/mapped_data --output-dir output/analysis
   ```

## CLI Commands

### `ieq-analytics run`
Execute the complete analysis pipeline:
```bash
ieq-analytics run [OPTIONS]
```

Options:
- `--data-dir PATH`: Input data directory (default: data/raw/concatenated)
- `--output-dir PATH`: Output directory (default: output)
- `--config-path PATH`: Configuration file path (default: config/mapping_config.json)
- `--interactive/--no-interactive`: Enable/disable interactive mapping (default: interactive)
- `--generate-plots/--no-plots`: Generate visualization plots (default: generate-plots)

### `ieq-analytics mapping`
Map raw CSV files to standardized IEQ format:
```bash
ieq-analytics mapping [OPTIONS]
```

Options:
- `--data-dir-path PATH`: Directory containing CSV files
- `--config-path PATH`: Configuration file for column mappings
- `--output-dir PATH`: Output directory for processed data
- `--interactive/--no-interactive`: Interactive column mapping
- `--room-tag TEXT`: Optional tag to apply to all rooms

### `ieq-analytics analyze`
Perform comprehensive IEQ analysis:
```bash
ieq-analytics analyze [OPTIONS]
```

Options:
- `--data-dir PATH`: Directory with mapped IEQ data
- `--output-dir PATH`: Output directory for analysis results
- `--buildings-metadata PATH`: Buildings metadata JSON file
- `--export-formats [json|csv|pdf]`: Export formats (multiple allowed)
- `--generate-plots/--no-plots`: Generate visualization plots

### `ieq-analytics inspect`
Inspect CSV files and analyze their structure:
```bash
ieq-analytics inspect --data-dir-path PATH [--output-format table|json]
```

### `ieq-analytics init-config`
Create a configuration template:
```bash
ieq-analytics init-config [--config-path PATH]
```

## Data Structure

### Input Data Format
The engine expects CSV files with hourly sensor data. Example structure:

| DateTime            | Temperatur | Fugtighed | CO2   | Lys | Tilstedeværelse |
|---------------------|------------|-----------|-------|-----|-----------------|
| 2024-01-01 08:00:00 | 20.5       | 45.2      | 650   | 150 | 1               |
| 2024-01-01 09:00:00 | 21.0       | 44.8      | 720   | 200 | 1               |

### Output Data Format
After mapping, data is standardized:

| Timestamp           | temperature | humidity | co2 | light | presence |
|---------------------|-------------|----------|-----|-------|----------|
| 2024-01-01 08:00:00 | 20.5        | 45.2     | 650 | 150   | 1        |
| 2024-01-01 09:00:00 | 21.0        | 44.8     | 720 | 200   | 1        |

## Configuration

### Mapping Configuration
Create or modify `config/mapping_config.json` to define column mappings:

```json
{
  "mappings": [
    {
      "file_pattern": "Building_A_.*\\.csv",
      "column_mappings": {
        "DateTime": "timestamp",
        "Temperatur": "temperature",
        "Fugtighed": "humidity",
        "CO2": "co2"
      },
      "building_name": "Building A"
    }
  ],
  "default_building_name": "Unknown Building",
  "timestamp_format": "%Y-%m-%d %H:%M:%S",
  "required_parameters": ["timestamp", "temperature"]
}
```

### Supported IEQ Parameters
- `temperature`: Air temperature (°C)
- `humidity`: Relative humidity (%)
- `co2`: Carbon dioxide concentration (ppm)
- `light`: Light level (lux)
- `presence`: Occupancy/presence detection

## Analytics Features

### Data Quality Assessment
- Completeness analysis
- Missing data detection
- Outlier identification
- Data resolution validation

### Comfort Analysis
Based on EN 16798-1 standard with three comfort categories:
- **Category I**: High level of expectation
- **Category II**: Normal level of expectation
- **Category III**: Acceptable level of expectation

### Temporal Pattern Analysis
- Hourly averages and patterns
- Day-of-week variations
- Monthly trends
- Weekend vs. weekday comparison

### Building-Level Aggregation
- Cross-room statistics
- Building-wide comfort compliance
- System performance indicators
- Actionable recommendations

## Output Files

The analysis generates several output files:

### Mapped Data
- `output/mapped_data/`: Processed CSV files with standardized columns
- `output/buildings_metadata.json`: Building and room structure

### Analysis Results
- `output/analysis/room_analyses.json`: Detailed room-level analysis
- `output/analysis/building_analysis.json`: Building-level aggregation
- `output/analysis/ieq_analysis_summary.csv`: Summary statistics
- `output/analysis/analysis_summary.json`: Process summary

### Visualizations
- `output/analysis/plots/`: Time series, heatmaps, and distribution plots for each room

## Programmatic Usage

You can also use the engine programmatically:

```python
from ieq_analytics import DataMapper, IEQAnalytics
from pathlib import Path

# Initialize components
mapper = DataMapper()
analytics = IEQAnalytics()

# Process data
data_dir = Path("data/raw/concatenated")
processed_data = mapper.process_directory(data_dir, interactive=False)

# Analyze each room
for ieq_data in processed_data:
    analysis = analytics.analyze_room_data(ieq_data)
    print(f"Room {ieq_data.room_id}: Quality score = {analysis['data_quality']['overall_score']}")
```

## Examples

Run the provided example script:
```bash
python example.py
```

This demonstrates:
- File structure analysis
- Column mapping
- Data processing
- Analysis execution
- Visualization generation

## Comfort Standards

The engine implements comfort thresholds based on EN 16798-1:

| Parameter   | Category I    | Category II   | Category III  |
|-------------|---------------|---------------|---------------|
| Temperature | 21-23°C       | 20-24°C       | 19-25°C       |
| Humidity    | 30-50%        | 25-60%        | 20-70%        |
| CO₂         | <550 ppm      | <800 ppm      | <1200 ppm     |

## Troubleshooting

### Common Issues

1. **"No CSV files found"**: Check that CSV files exist in the specified data directory
2. **"Could not parse timestamps"**: Verify timestamp format in configuration
3. **"Data not at hourly resolution"**: Ensure data is aggregated to hourly intervals
4. **Import errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`

### Data Requirements

- Files must be in CSV format
- Data should be at hourly resolution
- At minimum, timestamp and one measurement parameter required
- Timestamps should be parseable by pandas

## Contributing

This project uses:
- **Pydantic** for data validation and models
- **Click** for CLI interface
- **Pandas** for data processing
- **Matplotlib/Seaborn** for visualizations
- **EN 16798-1** for comfort standards

## License

This project is open source and available under the MIT License.