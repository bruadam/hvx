# Data Commands

The `hvx data` command group provides tools for loading and inspecting building sensor data.

## Overview

Data commands help you:
- Load building data from structured directories
- Validate data quality during loading
- Inspect loaded datasets
- Save datasets in multiple formats (JSON, Pickle)

## Commands

### `hvx data load`

Load building data from a directory structure into a unified dataset.

#### Syntax

```bash
hvx data load SOURCE_DIR [OPTIONS]
```

#### Arguments

- `SOURCE_DIR` - Path to directory containing building data (required)

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--output` | `-o` | PATH | - | Output file path for saving the dataset |
| `--format` | `-f` | CHOICE | `json` | Output format: `json`, `pickle`, or `both` |
| `--validate` | - | FLAG | `true` | Validate data quality during loading |
| `--no-validate` | - | FLAG | - | Skip data validation |
| `--infer-levels` | - | FLAG | `true` | Automatically infer building levels from room names |
| `--no-infer-levels` | - | FLAG | - | Skip level inference |
| `--infer-room-types` | - | FLAG | `true` | Automatically infer room types from names |
| `--no-infer-room-types` | - | FLAG | - | Skip room type inference |
| `--verbose` | `-v` | FLAG | - | Show detailed loading information |

#### Expected Directory Structure

The loader expects a specific directory structure:

```
source_dir/
├── building-1/
│   ├── climate/
│   │   └── climate-data.csv       # Optional: outdoor climate data
│   └── sensors/
│       ├── room1.csv               # Room sensor data
│       ├── room2.csv
│       └── room3.csv
├── building-2/
│   └── sensors/
│       ├── room1.csv
│       └── room2.csv
└── building-3/
    ├── climate/
    │   └── climate-data.csv
    └── sensors/
        └── room1.csv
```

**Key Points:**
- Each building has its own directory
- Building directories must contain a `sensors/` subdirectory with room data
- Optional `climate/` subdirectory for outdoor/building-level climate data
- All CSV files must contain a `timestamp` column
- Room CSV files should contain sensor columns: `temperature`, `co2`, `humidity`, `occupancy`, etc.

#### Output Formats

**JSON Format (`--format json`)**
- Human-readable summary of the dataset
- Contains metadata, building structure, and statistics
- Does not include full timeseries data
- Useful for inspection and sharing structure

**Pickle Format (`--format pickle`)**
- Binary format with complete data
- Includes all timeseries data
- Required for analysis (`hvx analyze run`)
- Preserves Python objects and data types

**Both (`--format both`)**
- Saves both JSON summary and Pickle data
- Recommended for archival and analysis workflows

#### Examples

**Basic loading with summary display:**
```bash
hvx data load data/samples/sample-extensive-data
```

**Load and save to JSON:**
```bash
hvx data load data/my-buildings -o output/dataset.json
```

**Load and save to Pickle for analysis:**
```bash
hvx data load data/my-buildings -o output/dataset.pkl -f pickle
```

**Load and save both formats:**
```bash
hvx data load data/my-buildings -o output/dataset -f both
```

**Load without validation (faster, for known good data):**
```bash
hvx data load data/my-buildings -o output/dataset.pkl --no-validate
```

**Load with detailed output:**
```bash
hvx data load data/my-buildings -o output/dataset.pkl -v
```

**Load without automatic inference:**
```bash
hvx data load data/my-buildings -o output/dataset.pkl \
  --no-infer-levels \
  --no-infer-room-types
```

#### Output

The command displays:
- Loading progress
- Dataset summary (building count, room count)
- Building-level details (rooms, levels, climate data availability)
- Data quality metrics (if validation enabled)
- Output file paths

Example output:
```
Loading building data from: data/samples/sample-extensive-data

✓ Loaded 3 buildings with 45 rooms

╭─────────────── Dataset Overview ───────────────╮
│ Source: data/samples/sample-extensive-data     │
│ Loaded: 2024-10-02 14:30:45                   │
│ Buildings: 3                                   │
│ Total Rooms: 45                                │
╰────────────────────────────────────────────────╯

Buildings
┌─────────────┬──────────────┬───────┬────────┬──────────────┐
│ Building ID │ Name         │ Rooms │ Levels │ Climate Data │
├─────────────┼──────────────┼───────┼────────┼──────────────┤
│ building-1  │ Building 1   │    20 │      2 │      ✓       │
│ building-2  │ Building 2   │    15 │      1 │      ✗       │
│ building-3  │ Building 3   │    10 │      1 │      ✓       │
└─────────────┴──────────────┴───────┴────────┴──────────────┘

✓ Saved full dataset to: output/dataset.pkl

✓ Data loading completed successfully!
```

#### Common Issues

**Issue: "Directory structure is invalid"**
- **Solution**: Ensure each building directory has a `sensors/` subdirectory with CSV files

**Issue: "CSV file missing 'timestamp' column"**
- **Solution**: Add a `timestamp` column to all CSV files in ISO format: `2024-01-01 00:00:00`

**Issue: "Unable to parse timestamps"**
- **Solution**: Use standard datetime format. Supported formats include:
  - `2024-01-01 00:00:00`
  - `2024-01-01T00:00:00`
  - `2024-01-01 00:00:00+00:00`

**Issue: Loading is slow**
- **Solution**: Use `--no-validate` to skip validation checks (only if data is known to be good)

---

### `hvx data inspect`

Inspect a loaded dataset from a pickle file.

#### Syntax

```bash
hvx data inspect DATA_FILE [OPTIONS]
```

#### Arguments

- `DATA_FILE` - Path to dataset pickle file (`.pkl`) (required)

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--building` | `-b` | TEXT | - | Filter by building ID |
| `--show-rooms` | - | FLAG | `true` | Show room-level details |
| `--no-show-rooms` | - | FLAG | - | Hide room-level details |
| `--show-quality` | - | FLAG | `true` | Show data quality metrics |
| `--no-show-quality` | - | FLAG | - | Hide data quality metrics |

#### Examples

**Inspect full dataset:**
```bash
hvx data inspect output/dataset.pkl
```

**Inspect specific building:**
```bash
hvx data inspect output/dataset.pkl -b building-1
```

**Inspect without room details:**
```bash
hvx data inspect output/dataset.pkl --no-show-rooms
```

**Inspect without quality metrics:**
```bash
hvx data inspect output/dataset.pkl --no-show-quality
```

**Inspect specific building with full details:**
```bash
hvx data inspect output/dataset.pkl -b building-1 --show-rooms --show-quality
```

#### Output

The command displays:
- Dataset overview (source, loaded date, counts)
- Building-level information (rooms, levels, climate data)
- Room-level details (ID, name, level, type, parameters)
- Data quality metrics (completeness, quality scores)

Example output:
```
Inspecting dataset: output/dataset.pkl

╭────────────── Dataset Overview ──────────────╮
│ Source: data/samples/sample-extensive-data   │
│ Loaded: 2024-10-02 14:30:45                 │
│ Buildings: 3                                 │
│ Total Rooms: 45                              │
╰──────────────────────────────────────────────╯

Buildings
┌─────────────┬──────────────┬───────┬────────┬──────────────┐
│ Building ID │ Name         │ Rooms │ Levels │ Climate Data │
├─────────────┼──────────────┼───────┼────────┼──────────────┤
│ building-1  │ Building 1   │    20 │      2 │      ✓       │
│ building-2  │ Building 2   │    15 │      1 │      ✗       │
│ building-3  │ Building 3   │    10 │      1 │      ✓       │
└─────────────┴──────────────┴───────┴────────┴──────────────┘

Building: Building 1 (ID: building-1)

╭─────────────────────────────────────────────╮
│ Rooms: 20                                   │
│ Levels: 2                                   │
│ Climate Data: Available                     │
│ Climate Parameters: temperature, humidity   │
╰─────────────────────────────────────────────╯

Data Quality:
  Overall Quality Score: 85.3%
  Rooms with Data: 18/20

Rooms
┌──────────────┬────────────────┬───────┬──────┬────────────────────────┬─────────┐
│ Room ID      │ Name           │ Level │ Type │ Parameters             │ Quality │
├──────────────┼────────────────┼───────┼──────┼────────────────────────┼─────────┤
│ room-1-0-01  │ Conference 101 │ 0     │ CONF │ temperature, co2, hum  │  92.5%  │
│ room-1-0-02  │ Office 102     │ 0     │ OFF  │ temperature, co2       │  88.2%  │
│ room-1-1-01  │ Meeting 201    │ 1     │ MEET │ temperature, co2, hum  │  91.1%  │
...
└──────────────┴────────────────┴───────┴──────┴────────────────────────┴─────────┘
```

#### Use Cases

1. **Verify data loading**: Check that all buildings and rooms were loaded correctly
2. **Pre-analysis inspection**: Review data structure before running analysis
3. **Quality assessment**: Identify rooms with missing or poor quality data
4. **Building focus**: Examine specific buildings in detail
5. **Data debugging**: Troubleshoot data issues before analysis

---

## Workflow Examples

### Complete Data Loading Workflow

```bash
# 1. Load data with both formats
hvx data load data/my-buildings -o output/dataset -f both -v

# 2. Inspect the loaded data
hvx data inspect output/dataset.pkl

# 3. Inspect specific building
hvx data inspect output/dataset.pkl -b building-1

# 4. Ready for analysis
hvx analyze run output/dataset.pkl --portfolio-name "My Portfolio"
```

### Data Quality Check Workflow

```bash
# 1. Load with validation
hvx data load data/my-buildings -o output/dataset.pkl --validate

# 2. Check overall quality
hvx data inspect output/dataset.pkl --show-quality

# 3. Check each building's quality
hvx data inspect output/dataset.pkl -b building-1 --show-quality
hvx data inspect output/dataset.pkl -b building-2 --show-quality

# 4. Review rooms with issues
hvx data inspect output/dataset.pkl -b building-1 --show-rooms
```

### Quick Check Workflow

```bash
# Load and immediately inspect
hvx data load data/my-buildings -o output/dataset.pkl && \
  hvx data inspect output/dataset.pkl --no-show-rooms
```

---

## CSV Data Requirements

### Mandatory Columns

All CSV files **must** contain:
- `timestamp` - ISO 8601 datetime format

### Standard Sensor Columns

Common sensor columns (at least one recommended):
- `temperature` - Temperature in °C
- `co2` - CO2 concentration in ppm
- `humidity` - Relative humidity in %
- `occupancy` - Occupancy count or binary (0/1)
- `pm25` - PM2.5 particulate matter in µg/m³
- `pm10` - PM10 particulate matter in µg/m³
- `tvoc` - Total Volatile Organic Compounds in ppb
- `light` - Light level in lux
- `noise` - Noise level in dB

### Example CSV

```csv
timestamp,temperature,co2,humidity,occupancy
2024-01-01 00:00:00,20.5,450,55,0
2024-01-01 01:00:00,20.3,430,54,0
2024-01-01 02:00:00,20.1,420,53,0
2024-01-01 03:00:00,20.0,410,52,0
2024-01-01 08:00:00,21.2,650,58,5
2024-01-01 09:00:00,22.1,780,60,12
```

---

## Best Practices

1. **Use pickle format for analysis**: Always save as `.pkl` when running `hvx analyze run`
2. **Save both formats**: Use `-f both` to keep both summary and data
3. **Validate on first load**: Keep validation enabled for new data
4. **Use verbose for debugging**: Add `-v` when troubleshooting issues
5. **Inspect before analyzing**: Run `hvx data inspect` to verify data quality
6. **Consistent naming**: Use descriptive building and room names
7. **Complete timestamps**: Ensure all timestamps are present and properly formatted
8. **Regular sampling**: Maintain consistent sampling intervals (e.g., hourly)

---

## See Also

- [Analyze Commands](./analyze.md) - Run analysis on loaded datasets
- [CLI Overview](./README.md) - Complete CLI documentation
