# Data Ingestion Modules

This directory contains data ingestion modules for loading environmental data from various sources into the refactored service architecture.

## Available Modules

### CSV Ingestion (`ingestion/csv/`)

Load building environmental data from CSV files.

**Supported Formats:**

1. **Wide Format** - One row per timestamp:
```csv
timestamp,temperature,co2,humidity
2024-01-01 00:00:00,21.5,450,45
2024-01-01 01:00:00,21.3,440,46
```

2. **Long Format** - One row per measurement:
```csv
timestamp,room_id,metric,value
2024-01-01 00:00:00,room_1,temperature,21.5
2024-01-01 00:00:00,room_1,co2,450
2024-01-01 01:00:00,room_1,temperature,21.3
```

**Usage:**

```python
from ingestion.csv import load_from_csv

# Load wide format
entities, points, timeseries = load_from_csv(
    'room_data.csv',
    format='wide',
    spatial_entity_id='room_101',
    spatial_entity_name='Office 101',
    entity_type=SpatialEntityType.ROOM,
    area_m2=25.0,
    volume_m3=75.0,
)

# Load long format
entities, points, timeseries = load_from_csv(
    'portfolio_data.csv',
    format='long',
    entity_id_column='room_id',
    metric_column='parameter',
    value_column='value',
)

# Load multiple files
from ingestion.csv import load_portfolio_from_csv

entities, points, timeseries = load_portfolio_from_csv(
    ['room1.csv', 'room2.csv', 'room3.csv'],
    format='wide',
)
```

**Output:**

The loader creates:
- **SpatialEntity** objects (Room, Building, Floor)
- **MeteringPoint** objects for each metric
- **TimeSeries** objects with data stored in metadata

**Data Access:**

```python
# Get timeseries data
loader = CSVDataLoader()
entities, points, ts = loader.load_wide_format('data.csv', ...)

# Access time series values
ts_id = list(ts.keys())[0]
timestamps, values = loader.get_timeseries_data(ts_id)
```

**Auto-Detection:**

The loader automatically:
- Maps metric names to MetricType enums
- Assigns appropriate units
- Estimates data granularity
- Creates proper entity hierarchies

**Metric Mapping:**

| CSV Column | MetricType | Unit |
|------------|------------|------|
| temperature, temp | TEMPERATURE | °C |
| co2 | CO2 | ppm |
| humidity, rh | HUMIDITY | % |
| illuminance, light, lux | ILLUMINANCE | lux |
| noise, sound | NOISE | dB(A) |
| energy | ENERGY | kWh |
| power | POWER | kW |

## Future Modules

- **Eloverblik** - Danish energy data API
- **BMS/SCADA** - Building management systems
- **IoT Platforms** - Real-time sensor data
- **Weather APIs** - Climate data ingestion

## Architecture

```
CSV File(s)
    ↓
CSVDataLoader
    ↓
┌─────────────┬──────────────┬──────────────┐
│ SpatialEntity│MeteringPoint │  TimeSeries  │
│  (Room,     │  (Sensors)   │   (Data)     │
│  Building)  │              │              │
└─────────────┴──────────────┴──────────────┘
    ↓
Standards Analysis
(EN16798, TAIL, etc.)
```

## Integration with Standards

Once data is loaded, it can be used with standards modules:

```python
from ingestion.csv import load_from_csv
from standards.en16798_1 import analysis as en16798
from standards.tail import analysis as tail

# Load data
entities, points, ts = load_from_csv('data.csv', format='wide', ...)

# Get entity
entity = list(entities.values())[0]

# Get time series data
loader = CSVDataLoader()
temp_ts_id = [ts_id for ts_id in ts if 'temperature' in ts_id][0]
timestamps, temperature = loader.get_timeseries_data(temp_ts_id)

# Run analysis
timeseries_dict = {'temperature': temperature, ...}
en_result = en16798.run(entity, timeseries_dict, timestamps, season='winter')
tail_result = tail.run(entity, timeseries_dict, timestamps)
```

## Adding New Ingestion Modules

To add a new ingestion module:

1. Create directory: `ingestion/your_source/`
2. Implement `data_loader.py` with:
   - Class that creates SpatialEntity, MeteringPoint, TimeSeries
   - Convenience functions for loading
3. Add `__init__.py` with exports
4. Update this README

**Template:**

```python
class YourDataLoader:
    def load(self, source_config: Dict[str, Any]) -> Tuple[...]:
        # 1. Connect to source
        # 2. Fetch data
        # 3. Create SpatialEntity objects
        # 4. Create MeteringPoint objects
        # 5. Create TimeSeries objects
        # 6. Return organized data
        pass
```
