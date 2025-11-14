# CSV Data Ingestion

This module provides flexible CSV data loaders for building environmental data with automatic structure detection.

## Features

- **Auto-detection** of folder structures
- **Multiple format support**: wide format, long format, hierarchical portfolios
- **Proper model objects**: Creates `SpatialEntity`, `MeteringPoint`, and `TimeSeries` objects
- **Time series data embedded** in metadata for easy access

## Supported Data Structures

### 1. Hoeje-Taastrup Structure
```
building-X/
  sensors/
    room_name.csv  # DateTime,Temperatur,Fugtighed,CO2,Lys,Tilstedeværelse
  climate/
    climate.csv
```

### 2. Dummy Data Structure
```
building_X/
  metadata.json
  climate_data.csv
  energy_data.csv
  level_Y/
    room_name.csv  # timestamp,temperature,co2,humidity
```

### 3. Simple CSV Files
```
building_sample.csv  # timestamp,temperature,co2,humidity,occupancy
```

## Quick Start

### Load Portfolio with Auto-Detection

```python
from ingestion.csv import load_portfolio

# Auto-detect and load
entities, points, timeseries = load_portfolio('data/samples/hoeje-taastrup')

print(f"Loaded {len(entities)} entities")
print(f"Loaded {len(points)} metering points")
print(f"Loaded {len(timeseries)} time series")
```

### Load Specific Structure

```python
from ingestion.csv import load_hoeje_taastrup, load_dummy_data

# Load hoeje-taastrup data
entities, points, ts = load_hoeje_taastrup('data/samples/hoeje-taastrup')

# Load dummy_data structure
entities, points, ts = load_dummy_data('data/samples/dummy_data')
```

### Load Single CSV File

```python
from ingestion.csv import load_from_csv

# Wide format
entities, points, ts = load_from_csv(
    'data/samples/building_sample.csv',
    format='wide',
    spatial_entity_id='my_building',
    spatial_entity_name='My Building',
)

# Long format
entities, points, ts = load_from_csv(
    'data.csv',
    format='long',
    timestamp_column='timestamp',
    entity_id_column='room_id',
    metric_column='metric',
    value_column='value',
)
```

## Accessing Time Series Data

```python
from ingestion.csv import load_portfolio

# Load data
entities, points, ts = load_portfolio('data/samples/dummy_data')

# Get a time series
ts_id = list(ts.keys())[0]
timeseries = ts[ts_id]

# Access metadata with timestamps and values
metadata = timeseries.metadata
timestamps = metadata.get('timestamps', [])
values = metadata.get('values', [])

print(f"Time series: {timeseries.metric.value}")
print(f"Data points: {len(values)}")
print(f"Start: {timeseries.start}")
print(f"End: {timeseries.end}")
print(f"Unit: {timeseries.unit}")

# Analyze values
import numpy as np
print(f"Mean: {np.mean(values):.2f} {timeseries.unit}")
print(f"Min: {np.min(values):.2f} {timeseries.unit}")
print(f"Max: {np.max(values):.2f} {timeseries.unit}")
```

## Using the Loader Class

```python
from ingestion.csv import PortfolioLoader

loader = PortfolioLoader()

# Load portfolio
entities, points, ts = loader.load_portfolio('data/samples/hoeje-taastrup')

# Access hierarchy
hierarchy = loader.get_building_hierarchy('building-1')
print(f"Building: {hierarchy['building'].name}")
print(f"Floors: {len(hierarchy['floors'])}")
print(f"Rooms: {len(hierarchy['rooms'])}")

# Access loaded data
print(f"All buildings: {list(loader.buildings.keys())}")
print(f"All floors: {list(loader.floors.keys())}")
print(f"All rooms: {list(loader.rooms.keys())}")
```

## Examples

Run the demo script to see all features in action:

```bash
.venv/bin/python refactored_service/ingestion/csv/demo_portfolio_loader.py
```

Run structure detection test:

```bash
.venv/bin/python refactored_service/ingestion/csv/test_structure_detection.py
```

## Column Name Mapping

The loader automatically maps common column names to metrics:

| CSV Column | Metric Type | Unit |
|------------|-------------|------|
| Temperatur, temperature | temperature | °C |
| Fugtighed, humidity, rh | humidity | % |
| CO2, co2 | co2 | ppm |
| Lys, illuminance, light, lux | illuminance | lux |
| noise, sound | noise | dB(A) |
| energy | energy | kWh |
| power | power | kW |
| outdoor_temperature | climate_temp | °C |

## API Reference

### `load_portfolio(data_path, auto_detect=True)`
Load portfolio with automatic structure detection.

### `load_hoeje_taastrup(data_path)`
Load hoeje-taastrup specific structure.

### `load_dummy_data(data_path)`
Load dummy_data specific structure.

### `load_from_csv(csv_path, format='wide', **kwargs)`
Load single CSV file in wide or long format.

### `PortfolioLoader`
Main loader class with methods:
- `load_portfolio(data_path, auto_detect=True)` - Load portfolio
- `get_building_hierarchy(building_id)` - Get building hierarchy
- `buildings` - Dict of loaded buildings
- `floors` - Dict of loaded floors  
- `rooms` - Dict of loaded rooms

### `CSVDataLoader`
Lower-level CSV loader with methods:
- `load_wide_format(csv_path, ...)` - Load wide format CSV
- `load_long_format(csv_path, ...)` - Load long format CSV
- `get_timeseries_data(ts_id)` - Get timestamps and values

## Notes

- Time series data is stored in the `metadata` field of `TimeSeries` objects
- Use `.venv/bin/python` to run scripts with the correct environment
- The loader creates proper model objects that can be used with the rest of the system
- All timestamps are converted to datetime objects
- Missing values are skipped during loading
