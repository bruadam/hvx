# Flow Editor Quick Start Guide

## Running the Application

The flow editor is now running at:
- **Local**: http://localhost:3002
- **Network**: http://192.168.1.2:3002

## How to Use

### 1. Add Nodes to Canvas
- Drag **Spatial Entity** or **Sensor** from the right sidebar onto the canvas
- Nodes are created with default types (Room for spatial, Temperature for sensor)

### 2. Configure Node Properties
**Double-click** any node to open the properties modal where you can:
- Change the node type (e.g., Room → Building, Temperature → Humidity)
- Set metadata:
  - **Spatial entities**: Area, volume, floor number, address, building type, capacity
  - **Sensors**: Unit, min/max values, accuracy, calibration info, manufacturer details
- Add custom fields for any additional data

Alternatively, click a node and use the **Edit Properties** button in the right panel.

### 3. Create Connections
- Drag from a node's bottom handle to another node's top handle
- **Smart Edge Styling**:
  - Spatial → Spatial: Grey static line (hierarchy)
  - Sensor → Spatial: Animated colored line (sensor's color)
  - Spatial → Sensor: Animated colored line (sensor's color)

### 4. Export Your Work
- Click **Export** button in the top toolbar
- Downloads a JSON file with all nodes, metadata, and connections

## Features at a Glance

### Node Library (Right Sidebar)
- **Spatial Entity**: Can be Portfolio, Building, Floor, or Room
- **Sensor**: Can be Temperature, Humidity, CO2, Occupancy, Light, or Energy
- Expand the details sections to see all available types

### Node Properties Modal
- **Basic Info**: Label, type, name, description
- **Spatial Properties**: Area, volume, floor number, address, building type, capacity
- **Sensor Properties**: Unit, accuracy, min/max values, measurement interval, calibration date, manufacturer info
- **Custom Fields**: Add unlimited key-value pairs

### Smart Edge Colors
- **Temperature**: Red
- **Humidity**: Cyan
- **CO2**: Slate grey
- **Occupancy**: Purple
- **Light**: Yellow
- **Energy**: Green

### Keyboard Shortcuts
- **Double-click**: Open node properties
- **Delete**: Remove selected node (via trash icon)
- **Drag**: Move nodes around
- **Mouse wheel**: Zoom in/out
- **Click + drag canvas**: Pan view

## Example Workflow

1. **Build Hierarchy**:
   ```
   Drag Spatial Entity → Double-click → Change to "Building"
   Drag Spatial Entity → Double-click → Change to "Floor"
   Connect Building → Floor (grey line)
   Drag Spatial Entity → Double-click → Change to "Room"
   Connect Floor → Room (grey line)
   ```

2. **Add Sensors**:
   ```
   Drag Sensor → Double-click → Change to "Temperature"
   Set unit: "°C", min: 15, max: 30
   Connect Room → Temperature Sensor (red animated line)

   Drag Sensor → Double-click → Change to "Humidity"
   Set unit: "%", min: 30, max: 70
   Connect Room → Humidity Sensor (cyan animated line)
   ```

3. **Add Metadata**:
   ```
   Double-click Room node
   Set area: 45, volume: 135, floor number: 1
   Add custom field: "purpose" = "Office"
   Save
   ```

4. **Export**:
   ```
   Click Export button
   File downloads: spatial-entity-graph.json
   ```

## Troubleshooting

### Build Cache Issues
If you see errors about missing files in `.next/`:
```bash
cd flow-editor
rm -rf .next
npm run dev
```

### Port Already in Use
The dev server automatically finds an available port. Check the terminal output for the correct URL.

### TypeScript Errors
Run type checking:
```bash
cd flow-editor
npx tsc --noEmit
```

## Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Type check
npx tsc --noEmit
```

## Tips

1. **Start with hierarchy**: Build your spatial structure first (Portfolio → Buildings → Floors → Rooms)
2. **Then add sensors**: Connect sensors to their physical locations
3. **Use metadata**: Fill in area, volume, etc. for better analytics later
4. **Custom fields**: Add any project-specific data you need
5. **Export often**: Save your work regularly by exporting to JSON
6. **Visual feedback**: Watch edge colors change as you modify sensor types

## Next Steps

- Import functionality (coming soon)
- Validation rules for metadata
- Templates for common building configurations
- Bulk edit capabilities
- Python backend integration for analysis

Enjoy building your spatial hierarchy! 🏢📊
