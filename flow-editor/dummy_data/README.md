# Dummy Data for Spatial Entity Flow Editor

This folder contains sample CSV data files and a pre-configured portfolio example to help you get started with the Flow Editor.

## Contents

### Sample CSV Files

All CSV files contain 24 hours of hourly data (one full day):

#### Temperature Sensors
- **temperature_sensor_room_101.csv** - Conference room temperature data (20.7°C - 24.1°C)
- **temperature_sensor_room_102.csv** - Open office temperature data (21.3°C - 24.7°C)

#### Humidity Sensor
- **humidity_sensor_room_101.csv** - Conference room humidity data (45.2% - 55.6%)

#### CO2 Sensor
- **co2_sensor_room_101.csv** - Conference room CO2 levels (402 - 1150 ppm)
  - Shows typical office pattern: low at night, high during workday

#### Occupancy Sensor
- **occupancy_sensor_room_101.csv** - Conference room occupancy (0 - 16 persons)
  - Reflects typical office hours (8 AM - 6 PM)

#### Light Sensor
- **light_sensor_room_101.csv** - Conference room light levels (0 - 485 lux)
  - Follows daylight pattern

#### Energy Sensor
- **energy_sensor_building_a.csv** - Whole building energy consumption (108.9 - 412.8 kWh)
  - Higher during business hours

#### Energy Meters (NEW!)
- **energy_meters_building_a.csv** - Multi-carrier energy consumption data
  - Electricity: 106.8 - 252.3 kWh
  - Gas: 34.5 - 75.9 kWh
  - District Heating: 135.8 - 258.7 kWh
  - Total: 277.1 - 586.9 kWh
  - Enables automatic EPC calculation!

#### Outdoor Climate (NEW!)
- **outdoor_temperature.csv** - Outdoor temperature data for adaptive comfort analysis
  - Range: 0.8°C - 6.8°C
  - Used by EN16798 adaptive comfort model

### Sample Portfolio

- **sample_portfolio.json** - Pre-configured portfolio structure
  - 1 Portfolio: "Corporate Real Estate Portfolio"
  - 2 Buildings: "Building A - Main Office", "Building B - Annex"
  - 2 Floors in Building A
  - 2 Rooms on Floor 1
  - Multiple sensors attached to rooms
  - Energy sensor at building level

## How to Use

### Method 1: Upload Individual CSV Files

1. Start the Flow Editor (`npm run dev`)
2. Create your spatial hierarchy (Portfolio → Building → Floor → Room)
3. Add sensor nodes
4. Click on a sensor node
5. Click "Upload CSV" button
6. Select a CSV file from this `dummy_data/` folder
7. Review the preview and confirm

### Method 2: Import Complete Portfolio (Future Feature)

Currently, you need to manually recreate the structure from `sample_portfolio.json`. A future version will include an import feature.

To recreate the sample portfolio:
1. Open `sample_portfolio.json` in a text editor
2. Follow the node and edge structure
3. Drag nodes from the library matching the types
4. Connect them as shown in the edges array
5. Upload corresponding CSV files to sensors

## Data Characteristics

### Realistic Patterns

All data follows realistic patterns:

- **Temperature**: Gradual changes, cooler at night, warmer during day
- **Humidity**: Inverse relationship with temperature
- **CO2**: Low when unoccupied, rises with occupancy
- **Occupancy**: Zero at night, peaks mid-day
- **Light**: Follows daylight cycle
- **Energy**: Baseline at night, peaks during business hours

### Time Range
- Start: 2024-01-01 00:00:00
- End: 2024-01-01 23:00:00
- Interval: 1 hour
- Total Records: 24 per file

### Units
- Temperature: Celsius
- Humidity: % (percentage)
- CO2: ppm (parts per million)
- Occupancy: persons
- Light: lux
- Energy: kWh (kilowatt-hours)

## Creating Your Own Data

### CSV Format Requirements

```csv
timestamp,<measurement_type>,unit
2024-01-01T00:00:00,<value>,<unit>
2024-01-01T01:00:00,<value>,<unit>
...
```

### Column Guidelines

1. **timestamp**: ISO 8601 format (YYYY-MM-DDTHH:mm:ss)
2. **measurement column**: Name it appropriately (temperature, humidity, co2, etc.)
3. **unit**: Specify the unit of measurement

### Example: Creating a New Temperature File

```csv
timestamp,temperature,unit
2024-01-15T00:00:00,22.0,Celsius
2024-01-15T01:00:00,21.8,Celsius
2024-01-15T02:00:00,21.6,Celsius
```

## Sample Scenarios

### Scenario 1: Simple Office Monitoring
- Use: `temperature_sensor_room_101.csv` + `humidity_sensor_room_101.csv`
- Purpose: Basic climate monitoring

### Scenario 2: Indoor Air Quality Assessment
- Use: `temperature_sensor_room_101.csv` + `co2_sensor_room_101.csv` + `occupancy_sensor_room_101.csv`
- Purpose: Correlate CO2 with occupancy

### Scenario 3: Complete Room Analysis
- Use: All Room 101 sensors
- Purpose: Comprehensive environmental monitoring

### Scenario 4: Building-Wide Energy
- Use: `energy_sensor_building_a.csv`
- Purpose: Track overall building consumption

## Tips

1. **Start Small**: Begin with one temperature sensor to test the upload
2. **Check Preview**: Always review the preview table before confirming upload
3. **Match Names**: Name your nodes to match the CSV filenames (e.g., "Room 101" node with "room_101" CSV files)
4. **Organize Visually**: Arrange nodes on canvas to match your building layout
5. **Export Often**: Save your work by exporting to JSON

## Extending the Data

### Generate More Data

You can generate additional data using:
- Python with pandas: `df.to_csv('filename.csv', index=False)`
- Excel: Save as CSV
- Online tools: CSV generator websites
- The app's built-in sample data generator

### Add More Time Points

To extend beyond 24 hours:
1. Copy existing CSV
2. Continue timestamp sequence
3. Add more data rows
4. Maintain realistic patterns

### Add More Rooms

To scale up:
1. Copy existing sensor CSV files
2. Rename to match new rooms (room_103, room_104, etc.)
3. Optionally modify values slightly for variety
4. Create corresponding nodes in the Flow Editor

## Validation

### Quick Check
- File extension: `.csv`
- Header row present: Yes
- Timestamp format: ISO 8601
- Data rows: At least 1
- Columns: At least 3 (timestamp, measurement, unit)

### Common Issues
- **Missing headers**: First row must be column names
- **Wrong format**: Use comma-separated, not semicolon
- **Bad timestamps**: Must be valid ISO 8601 format
- **Empty values**: Will show as '-' in preview

## File Sizes

Current sample files are very small (~1KB each):
- 24 rows = ~1 KB
- 100 rows = ~3 KB
- 1000 rows = ~30 KB
- 10000 rows = ~300 KB

The browser can handle CSV files up to several MB easily.

---

**Ready to start?** Try uploading `temperature_sensor_room_101.csv` to a temperature sensor node!

**Need help?** Check the main README.md or click the Help button in the app.
