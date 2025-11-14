# Zip Import - Quick Guide

## Overview
The zip import feature allows you to automatically generate complete building portfolios by uploading a zip file containing CSV sensor data.

## Creating a Zip File

### Method 1: Using the Command Line (Recommended)
This method ensures no hidden files are included:

```bash
# Navigate to your data folder
cd /path/to/your/sensor/data

# Create zip without system files
zip -X -r my_portfolio.zip *.csv

# Or on Windows/Mac GUI, select only CSV files
```

### Method 2: Using File Explorer/Finder
1. Select **only the CSV files** (don't select folders)
2. Right-click → Compress/Send to Compressed folder
3. Rename to `my_portfolio.zip`

## File Naming Convention

Your CSV files should follow this pattern:
```
{sensor_type}_sensor_{location}.csv
```

### Examples:
- ✅ `temperature_sensor_room_101.csv`
- ✅ `humidity_sensor_room_101.csv`
- ✅ `co2_sensor_building_a.csv`
- ✅ `energy_sensor_building_a.csv`
- ✅ `light_sensor_room_102.csv`

### Supported Sensor Types:
- `temperature`, `temp`
- `humidity`, `rh`
- `co2`
- `occupancy`
- `light`, `lux`
- `energy`, `power`

### Location Patterns:
- `building_a`, `building_b` → Detected as buildings
- `floor_1`, `floor_2` → Detected as floors
- `room_101`, `room_102`, `101`, `102` → Detected as rooms

## CSV File Format

Each CSV must have:
1. **Header row** with column names
2. **Timestamp column** (named `timestamp` or `time`)
3. **Data columns** with metric values

### Example CSV:
```csv
timestamp,temperature,unit
2024-01-01T00:00:00,21.5,°C
2024-01-01T01:00:00,21.8,°C
2024-01-01T02:00:00,21.3,°C
```

### Multi-Metric CSV:
```csv
timestamp,temp_supply,temp_return,airflow,unit_temp,unit_flow
2024-01-01T00:00:00,18.5,22.3,450,°C,m³/h
2024-01-01T01:00:00,18.8,22.1,455,°C,m³/h
```

## Using the Test Portfolio

A test zip file is included: `test_portfolio.zip`

### Contents:
```
test_portfolio.zip
├── temperature_sensor_room_101.csv (24 hours)
├── temperature_sensor_room_102.csv (24 hours)
├── humidity_sensor_room_101.csv (24 hours)
├── co2_sensor_room_101.csv (24 hours)
├── occupancy_sensor_room_101.csv (24 hours)
├── light_sensor_room_101.csv (24 hours)
└── energy_sensor_building_a.csv (24 hours)
```

### What Gets Generated:
- 1 Building (Building A)
- 2 Rooms (Room 101, Room 102)
- 7 Sensors (with CSV data loaded)
- All connections and metric mappings

## Import Process

1. **Click "Import Zip"** (orange button in toolbar)
2. **Upload your zip file**
3. **Wait for processing** (usually 1-2 seconds)
4. **Review the generated flow**:
   - Spatial entities (portfolio, buildings, floors, rooms)
   - Sensors with loaded CSV data
   - Metric mappings auto-detected
   - Connections established

## Auto-Detection

The system automatically:
- ✅ Extracts spatial hierarchy from filenames
- ✅ Detects sensor types
- ✅ Creates appropriate nodes
- ✅ Loads CSV data into sensors
- ✅ Maps CSV columns to metric types
- ✅ Connects sensors to spaces
- ✅ Arranges nodes in logical layout

## Troubleshooting

### Error: "No valid CSV or JSON files found in zip"
**Cause**: Zip is empty, contains only folders, or files are corrupted

**Solution**:
- Ensure zip contains CSV files at the root level
- Don't zip a folder containing CSVs, zip the CSVs directly
- Check that CSVs are not corrupted

### Error: "Error processing zip file"
**Cause**: Invalid zip format, hidden system files, or parsing errors

**Solution**:
- Use `-X` flag when creating zip: `zip -X -r portfolio.zip *.csv`
- Remove hidden files like `.DS_Store`
- Ensure all CSVs have valid headers
- Check console for specific file errors

### No Sensors Detected
**Cause**: Filenames don't match expected patterns

**Solution**:
- Ensure filenames contain sensor type keywords:
  - `temperature`, `temp`
  - `humidity`, `rh`
  - `co2`
  - `occupancy`
  - `light`, `lux`
  - `energy`, `power`

### Wrong Spatial Hierarchy
**Cause**: Location parsing issue in filenames

**Solution**:
- Use clear location identifiers: `building_a`, `room_101`, `floor_2`
- Be consistent with naming across all files
- After import, you can manually adjust node properties

### CSV Data Not Loading
**Cause**: CSV format issues

**Solution**:
- Ensure first row is header
- Include `timestamp` or `time` column
- Check for proper UTF-8 encoding
- Verify no empty rows

## Advanced Tips

### Creating Complex Hierarchies
```
# Multiple buildings
temperature_sensor_building_a_room_101.csv
temperature_sensor_building_b_room_201.csv

# Multiple floors
co2_sensor_building_a_floor_1_room_101.csv
co2_sensor_building_a_floor_2_room_201.csv
```

### Batch Operations
```bash
# Create zip from specific building
zip -X building_a.zip *building_a*.csv

# Create portfolio from multiple sources
zip -X portfolio.zip building_a/*.csv building_b/*.csv
```

### Large Portfolios
- The system handles 100+ sensors efficiently
- Large CSV files (10,000+ rows) load instantly
- Layout algorithm positions nodes automatically
- Use sensor toggle to focus on hierarchy

## After Import

### Customize Your Flow
1. **Edit Properties**: Click any node → "Edit Properties"
2. **Verify Metrics**: Select sensor → Check metric mappings
3. **Adjust Layout**: Drag nodes to preferred positions
4. **Add Details**: Update metadata (area, capacity, etc.)
5. **Export**: Save your work as JSON

### Re-editing Metric Mappings
1. Select a sensor node
2. Click "Edit Properties"
3. Adjust metric mappings if auto-detection was incorrect
4. Save changes

## Examples

### Example 1: Single Building
```bash
# Files
temperature_sensor_room_101.csv
humidity_sensor_room_101.csv
co2_sensor_room_101.csv

# Create zip
zip -X single_building.zip *.csv

# Result
- 1 Building (Building A - default)
- 1 Room (Room 101)
- 3 Sensors
```

### Example 2: Multi-Building Portfolio
```bash
# Files
temperature_sensor_building_a_room_101.csv
temperature_sensor_building_b_room_201.csv
energy_sensor_building_a.csv
energy_sensor_building_b.csv

# Create zip
zip -X portfolio.zip *.csv

# Result
- 1 Portfolio
- 2 Buildings (A and B)
- 2 Rooms (101 in A, 201 in B)
- 4 Sensors (2 temp, 2 energy)
```

### Example 3: Complete Building with Floors
```bash
# Files
temp_sensor_building_main_floor_1_room_101.csv
temp_sensor_building_main_floor_1_room_102.csv
temp_sensor_building_main_floor_2_room_201.csv
co2_sensor_building_main_floor_1_room_101.csv

# Create zip
zip -X complete_building.zip *.csv

# Result
- 1 Building (Main)
- 2 Floors (1 and 2)
- 3 Rooms (101, 102, 201)
- 4 Sensors (3 temp, 1 co2)
```

## Performance

- **Processing**: 1-2 seconds for 100 CSV files
- **Layout**: Automatic positioning in <1 second
- **Rendering**: Smooth with 200+ nodes
- **CSV Size**: Handles 100,000+ row files instantly

## Best Practices

1. **Consistent Naming**: Use the same pattern for all files
2. **Clear Locations**: Include building/room identifiers
3. **Valid CSVs**: Always include headers and timestamps
4. **No Hidden Files**: Use `-X` flag when creating zips
5. **Test First**: Use `test_portfolio.zip` to verify workflow
6. **Incremental**: Start with one building, then expand

## Quick Reference

### Create Zip (Mac/Linux)
```bash
zip -X -r portfolio.zip *.csv
```

### Create Zip (Windows PowerShell)
```powershell
Compress-Archive -Path *.csv -DestinationPath portfolio.zip
```

### Import Steps
1. Click "Import Zip" button
2. Select zip file
3. Wait for generation
4. Review and customize

---

**Need Help?**
- Check console for detailed error messages
- Verify CSV format with sample data
- Test with `test_portfolio.zip` first
- Review [NEW_FEATURES.md](NEW_FEATURES.md) for detailed documentation
