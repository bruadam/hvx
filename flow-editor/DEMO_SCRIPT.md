# Demo Script - Quick Walkthrough

This script will help you create a complete spatial hierarchy with sensors in under 5 minutes.

## Prerequisites

Make sure the development server is running:
```bash
cd flow-editor
npm run dev
```

Open http://localhost:3000 in your browser.

## Demo Scenario: Office Building with Climate Monitoring

We'll create a portfolio with one building, two floors, and multiple rooms with temperature sensors.

### Step 1: Create Portfolio (30 seconds)

1. Look at the **right panel** - you'll see the Component Library
2. Under "Spatial Entities", find **Portfolio** (purple with briefcase icon)
3. **Drag** the Portfolio node onto the canvas (center-left area)
4. Release to drop - you now have "Portfolio 1"

✅ **Result**: Purple portfolio node on canvas

### Step 2: Add Building (30 seconds)

1. Drag **Building** (blue with building icon) from the library
2. Drop it **below** the Portfolio node
3. **Connect them**:
   - Click and hold the **bottom handle** (●) of Portfolio
   - Drag to the **top handle** (●) of Building
   - Release - you'll see an animated blue line

✅ **Result**: Building connected to Portfolio

### Step 3: Add Floors (1 minute)

1. Drag **Floor** (green with layers icon) twice
2. Position them below the Building node (side by side)
3. **Connect Building to both Floors**:
   - Building bottom handle → Floor 1 top handle
   - Building bottom handle → Floor 2 top handle

✅ **Result**: Two floors connected to building

### Step 4: Add Rooms (1 minute)

1. Drag **Room** (amber with home icon) four times
2. Position:
   - 2 rooms below Floor 1
   - 2 rooms below Floor 2
3. **Connect each room to its floor**:
   - Floor 1 → Room 1 and Room 2
   - Floor 2 → Room 3 and Room 4

✅ **Result**: Four rooms connected to floors

### Step 5: Add Temperature Sensors (1 minute)

1. Scroll down in the library to "Sensors" section
2. Drag **Temperature** sensor (red with thermometer) four times
3. Position one sensor below each room
4. **Connect each sensor to its room**:
   - Room 1 → Temperature Sensor 1
   - Room 2 → Temperature Sensor 2
   - Room 3 → Temperature Sensor 3
   - Room 4 → Temperature Sensor 4

✅ **Result**: Temperature sensors monitoring each room

### Step 6: Add Sample Data (1 minute)

1. **Click** on Temperature Sensor 1
2. Notice the **Node Details panel** appears (top right)
3. Scroll down to "Quick Sample Data"
4. Click **"Temperature Data"** button
5. Watch the node update to show "100 records"
6. **Repeat** for the other 3 temperature sensors

✅ **Result**: All sensors have sample data attached

### Step 7: View Help Guide (30 seconds)

1. Click the **purple "Help"** button (top left)
2. Browse the interactive help modal
3. See the hierarchy guide and tips
4. Click **"Got it!"** to close

✅ **Result**: You've seen the help system

### Step 8: Explore Canvas Controls (30 seconds)

1. **Zoom**: Scroll your mouse wheel
2. **Pan**: Click and drag the background
3. **Move nodes**: Click and drag individual nodes
4. **Deselect**: Click on empty canvas space

✅ **Result**: You can navigate the canvas

### Step 9: Inspect Node Details (30 seconds)

1. Click on any node to select it
2. View the details panel showing:
   - Node type
   - Label
   - ID
   - CSV file info (if sensor)
   - Record count (if sensor)

✅ **Result**: You can inspect any node

### Step 10: Export Your Work (30 seconds)

1. Click the **blue "Export"** button (top left)
2. A JSON file will download automatically
3. Open it to see the structure:
   - All nodes with positions and data
   - All connections between nodes

✅ **Result**: JSON file with complete graph structure

## Advanced Demo (Optional)

### Add More Sensor Types

1. Add a **Humidity sensor** (cyan with droplets icon)
2. Add a **CO2 sensor** (slate with wind icon)
3. Add an **Energy sensor** (green with zap icon)
4. Connect them to rooms
5. Add sample data to each

### Upload Real CSV Data

1. Create a CSV file:
```csv
timestamp,temperature,unit
2024-01-01T00:00:00,22.5,Celsius
2024-01-01T01:00:00,22.3,Celsius
2024-01-01T02:00:00,22.7,Celsius
```

2. Click on a sensor node
3. Click **"Upload CSV"** button
4. Select your CSV file
5. Preview the data
6. Click **"Upload"**

### Delete Nodes

1. Select any node
2. Click the **trash icon** in the details panel
3. Watch the node and its connections disappear

### Clear Everything

1. Click the **red "Clear"** button
2. Confirm the action
3. Canvas is now empty - ready to start fresh!

## What You Built

You now have a complete spatial hierarchy:

```
Portfolio: "Portfolio 1"
  └─ Building: "Building 2"
      ├─ Floor: "Floor 3"
      │   ├─ Room: "Room 5"
      │   │   └─ Temperature Sensor: "Temperature 9" [100 records]
      │   └─ Room: "Room 6"
      │       └─ Temperature Sensor: "Temperature 10" [100 records]
      └─ Floor: "Floor 4"
          ├─ Room: "Room 7"
          │   └─ Temperature Sensor: "Temperature 11" [100 records]
          └─ Room: "Room 8"
              └─ Temperature Sensor: "Temperature 12" [100 records]
```

## Exported JSON Structure

```json
{
  "nodes": [
    {
      "id": "node_0",
      "type": "portfolio",
      "label": "Portfolio 1",
      "position": { "x": 250, "y": 50 },
      "recordCount": 0
    },
    {
      "id": "node_1",
      "type": "building",
      "label": "Building 2",
      "position": { "x": 250, "y": 150 },
      "recordCount": 0
    },
    // ... more nodes
  ],
  "edges": [
    {
      "source": "node_0",
      "target": "node_1"
    },
    // ... more connections
  ]
}
```

## Next Steps

### Use Cases

1. **Building Management**: Model your entire property portfolio
2. **IoT Planning**: Design sensor deployment strategies
3. **Data Collection**: Plan which data to collect where
4. **System Documentation**: Visual documentation of building systems
5. **Simulation**: Test different sensor configurations

### Integration Ideas

1. **Backend API**: Send the JSON to a backend service
2. **Database**: Store the structure in a database
3. **Analytics**: Feed the structure to analytics tools
4. **Reporting**: Generate reports based on the hierarchy
5. **Monitoring**: Real-time data streaming to sensor nodes

### Customization

1. **Add Node Types**: Edit `lib/nodeTypes.ts`
2. **Change Colors**: Modify the color palette
3. **Add Properties**: Extend the NodeData interface
4. **Custom Validation**: Add connection rules
5. **Templates**: Create pre-built hierarchies

## Tips for Best Results

1. **Start from the top** - Portfolio first, then work down
2. **Keep it hierarchical** - Follow the natural building structure
3. **Name clearly** - Use descriptive labels for each node
4. **One connection per child** - Don't create multiple parent connections
5. **Export regularly** - Save your work often
6. **Use sample data** - Test before uploading real CSV files
7. **Zoom out** - Use fit view to see the entire graph
8. **Organize visually** - Align nodes for a clean look

## Common Patterns

### Single Building, Multiple Sensors
```
Portfolio → Building → Floor → Room → [Multiple Sensors]
```

### Multi-Building Portfolio
```
Portfolio → [Multiple Buildings] → Floors → Rooms → Sensors
```

### Sensor-Only View
```
Room → [Temperature, Humidity, CO2, Occupancy]
```

### Energy Monitoring
```
Building → [Energy Sensors on each floor]
```

## Troubleshooting Demo

### Can't drag nodes?
- Make sure you're dragging from the library panel (right side)
- Check that you're dropping on the canvas (gray dotted area)

### Can't connect nodes?
- Drag from the **bottom** handle (●) to the **top** handle (●)
- Make sure both nodes are visible on canvas
- Try zooming out to see both nodes

### CSV won't upload?
- Only sensor nodes (not spatial entities) accept CSV
- File must have `.csv` extension
- Click the sensor first to select it

### Lost my nodes?
- Try zooming out (mouse wheel or controls)
- Click "Fit View" in the controls (bottom left)
- If all else fails, refresh and start again

## Time Estimate

- **Quick Demo**: 5 minutes (basic hierarchy)
- **Full Demo**: 10 minutes (with all features)
- **Advanced Demo**: 15 minutes (custom CSV, multiple sensors)

---

**Ready to try?** Start with Step 1 and work your way through!

**Need help?** Click the purple "Help" button in the app or review the USAGE_GUIDE.md

**Questions?** Check the README.md for more details
