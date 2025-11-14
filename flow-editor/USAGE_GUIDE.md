# Usage Guide - Spatial Entity & Sensor Flow Editor

## Overview

This visual flow editor allows you to create hierarchical relationships between spatial entities (Portfolio → Building → Floor → Room) and attach sensors to any level of the hierarchy.

## Getting Started

### Starting the Application

```bash
cd flow-editor
npm install  # First time only
npm run dev
```

Open your browser to [http://localhost:3000](http://localhost:3000)

## Interface Components

### 1. Main Canvas (Center)
- **Drag and drop** nodes from the library
- **Pan** by clicking and dragging the background
- **Zoom** using mouse wheel or controls
- **Connect nodes** by dragging from the bottom handle (source) to the top handle (target)

### 2. Node Library (Right Panel)
Two categories of components:

#### Spatial Entities
- **Portfolio** (Purple) - Top-level organization
- **Building** (Blue) - Individual buildings
- **Floor** (Green) - Floors within buildings
- **Room** (Amber) - Individual rooms

#### Sensors
- **Temperature** (Red) - Temperature measurements
- **Humidity** (Cyan) - Humidity measurements
- **CO2** (Slate) - CO2 level measurements
- **Occupancy** (Purple) - Occupancy detection
- **Light** (Yellow) - Light level measurements
- **Energy** (Green) - Energy consumption

### 3. Toolbar (Top Left)
- **Export** - Download graph structure as JSON
- **Clear** - Remove all nodes and connections

### 4. Node Details Panel (Top Right)
Appears when a node is selected:
- Shows node type, label, and ID
- For sensor nodes: CSV upload and sample data options
- Delete button to remove the node

## Step-by-Step Tutorial

### Example: Create a Building with Temperature Monitoring

1. **Add a Portfolio Node**
   - Drag "Portfolio" from the library to the canvas
   - This represents your entire property portfolio

2. **Add a Building Node**
   - Drag "Building" from the library below the portfolio
   - Connect portfolio (bottom handle) to building (top handle)

3. **Add Floor Nodes**
   - Drag multiple "Floor" nodes below the building
   - Connect building to each floor

4. **Add Room Nodes**
   - Drag "Room" nodes for each room on a floor
   - Connect floor to each room

5. **Add Temperature Sensors**
   - Drag "Temperature" sensor nodes
   - Connect each sensor to its respective room

6. **Upload CSV Data to Sensors**
   - Click on a temperature sensor node
   - In the details panel, click "Upload CSV"
   - Select a CSV file with columns like:
     ```csv
     timestamp,temperature,unit
     2024-01-01T00:00:00,22.5,Celsius
     2024-01-01T01:00:00,22.3,Celsius
     ```
   - Or use "Quick Sample Data" buttons for testing

7. **Export Your Graph**
   - Click "Export" in the toolbar
   - Save the JSON file containing your structure

## CSV Data Format

### Temperature Sensor
```csv
timestamp,temperature,unit
2024-01-01T00:00:00,22.5,Celsius
2024-01-01T01:00:00,22.3,Celsius
```

### Humidity Sensor
```csv
timestamp,humidity,unit
2024-01-01T00:00:00,45.2,%
2024-01-01T01:00:00,46.1,%
```

### CO2 Sensor
```csv
timestamp,co2,unit
2024-01-01T00:00:00,450,ppm
2024-01-01T01:00:00,460,ppm
```

### Energy Sensor
```csv
timestamp,energy,unit
2024-01-01T00:00:00,125.5,kWh
2024-01-01T01:00:00,130.2,kWh
```

## Sample Data Generator

For quick testing, sensor nodes include a built-in sample data generator:

1. Select a sensor node
2. In the details panel, find "Quick Sample Data"
3. Click one of the sample data buttons:
   - **Temperature Data** - 100 hourly readings (20-25°C)
   - **Humidity Data** - 100 hourly readings (40-70%)
   - **CO2 Data** - 100 hourly readings (400-1200 ppm)

## Exported JSON Structure

```json
{
  "nodes": [
    {
      "id": "node_0",
      "type": "portfolio",
      "label": "Portfolio 1",
      "position": { "x": 100, "y": 50 },
      "recordCount": 0
    },
    {
      "id": "node_1",
      "type": "temperatureSensor",
      "label": "Temperature 1",
      "position": { "x": 300, "y": 400 },
      "csvFile": "temp_data.csv",
      "recordCount": 100
    }
  ],
  "edges": [
    {
      "source": "node_0",
      "target": "node_1"
    }
  ]
}
```

## Best Practices

### 1. Hierarchical Structure
Follow this typical hierarchy:
```
Portfolio
  └── Building(s)
      └── Floor(s)
          └── Room(s)
              └── Sensor(s)
```

### 2. Naming Conventions
- Use descriptive names: "Building A - Main Office"
- Include location info: "Floor 2 - East Wing"
- Specify room function: "Conference Room 201"
- Label sensors by type and location: "Temp Sensor - Room 201"

### 3. Data Organization
- Upload data to the lowest level (sensors)
- Keep CSV files organized by date range
- Use consistent timestamp formats (ISO 8601)
- Include units in your CSV files

### 4. Connection Logic
- Connect spatial entities hierarchically (top-down)
- Attach sensors to the most specific spatial entity
- One sensor can connect to one spatial entity
- One spatial entity can have multiple sensors

## Keyboard Shortcuts

- **Delete** - Delete selected node
- **Cmd/Ctrl + Z** - Undo (via browser)
- **Mouse Wheel** - Zoom in/out
- **Space + Drag** - Pan canvas
- **Click + Drag** - Move selected node

## Troubleshooting

### CSV Upload Issues
- **Problem**: CSV not recognized
  - **Solution**: Ensure file has .csv extension

- **Problem**: Empty preview
  - **Solution**: Check CSV has headers and data rows

### Connection Issues
- **Problem**: Can't connect nodes
  - **Solution**: Drag from bottom handle (source) to top handle (target)

- **Problem**: Connection doesn't appear
  - **Solution**: Check handles are properly aligned

### Performance
- **Problem**: Slow with many nodes
  - **Solution**: Use fewer than 100 nodes per canvas
  - **Solution**: Split large hierarchies into multiple graphs

## Advanced Features

### Custom Node Labels
1. Click on a node
2. The label is shown in the details panel
3. Currently read-only (future enhancement: inline editing)

### Multiple Sensor Types per Room
You can attach multiple different sensor types to a single room:
- Temperature
- Humidity
- CO2
- Light
- Occupancy
- Energy

### Export for Integration
The exported JSON can be used to:
- Import into analytics platforms
- Generate building information models
- Feed into simulation tools
- Create reports

## Future Enhancements

Planned features:
- [ ] Inline node label editing
- [ ] Node search and filter
- [ ] Undo/Redo functionality
- [ ] Import from JSON
- [ ] Custom node types
- [ ] Node grouping
- [ ] Auto-layout algorithms
- [ ] Data validation rules
- [ ] Real-time data streaming
- [ ] Multi-user collaboration

## Support

For issues or questions:
1. Check this guide first
2. Review the README.md
3. Check the browser console for errors
4. Report issues with screenshots

## Tips & Tricks

1. **Quick Duplicates**: Select and copy-paste nodes (browser default)
2. **Alignment**: Use grid snapping for neat layouts
3. **Color Coding**: Use node colors to quickly identify types
4. **Testing**: Use sample data generators before uploading real data
5. **Export Often**: Save your work regularly by exporting JSON
6. **Zoom Out**: Press 'Fit View' in controls to see entire graph
7. **Organization**: Group related nodes visually for clarity

Happy building! 🏗️
