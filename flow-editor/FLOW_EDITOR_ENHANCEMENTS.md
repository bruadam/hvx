# Flow Editor Enhancements

## Overview
Enhanced the flow editor with metadata support, simplified node types, and a comprehensive properties modal.

## Key Changes

### 1. Simplified Node Types
- **Before**: Multiple specific node types (temperatureSensor, humiditySensor, portfolio, building, etc.)
- **After**: Two base types with selectable subtypes
  - `spatialEntity`: Can be Portfolio, Building, Floor, or Room
  - `sensor`: Can be Temperature, Humidity, CO2, Occupancy, Light, or Energy

### 2. Enhanced Metadata Support
Added comprehensive metadata fields for both spatial entities and sensors:

#### Spatial Entity Metadata:
- Name & Description
- Area (m²)
- Volume (m³)
- Floor Number
- Address
- Building Type
- Capacity (max occupancy)

#### Sensor Metadata:
- Name & Description
- Unit of measurement
- Min/Max values
- Accuracy
- Measurement interval
- Calibration date
- Manufacturer, Model, Serial number

#### Custom Fields:
- Users can add unlimited custom key-value pairs for additional metadata

### 3. Node Properties Modal
- Opens on **double-click** or via "Edit Properties" button
- Organized sections for different property types
- Type-specific fields (spatial vs sensor)
- Custom fields section for extensibility
- Visual feedback with icons and color-coded sections

### 4. Improved Node Library
- Simplified to show just two base node types
- Expandable reference showing all available subtypes
- Clear instructions for users
- Visual consistency with icons and colors

### 5. Enhanced Node Display
- Nodes show metadata preview (area for spatial entities, unit for sensors)
- Type can be changed after creation via properties modal
- All metadata is preserved and exported

### 6. Smart Edge Styling
- **Spatial to Spatial**: Static grey edges (no animation)
- **Sensor to Spatial**: Animated edges with the sensor's color flowing towards the spatial entity
- **Spatial to Sensor**: Animated edges with the sensor's color flowing from the spatial entity
- **Sensor to Sensor**: Static grey edges (no animation)
- Edge styles automatically update when node types are changed

## User Workflow

1. **Drag** a Spatial Entity or Sensor from the library onto the canvas
2. **Double-click** the node to open the properties modal
3. **Configure** the node:
   - Select specific type (e.g., change from default to "Building")
   - Fill in metadata (area, volume, address, etc.)
   - Add custom fields as needed
4. **Save** changes and continue building the graph
5. **Export** the complete graph with all metadata to JSON

## Export Format

The exported JSON now includes:
```json
{
  "nodes": [
    {
      "id": "node_1",
      "baseType": "spatialEntity",
      "subType": "building",
      "label": "Main Building",
      "metadata": {
        "name": "Main Building",
        "description": "Primary office building",
        "area": 5000,
        "address": "123 Main St",
        "buildingType": "Office",
        "customFields": {
          "constructionYear": "2020",
          "energyRating": "A+"
        }
      },
      "position": { "x": 100, "y": 100 }
    }
  ],
  "edges": [...]
}
```

## Technical Implementation

### Files Modified:
- `lib/nodeTypes.ts` - Enhanced type definitions with metadata
- `components/CustomNode.tsx` - Updated to use new type system
- `components/NodeLibrary.tsx` - Simplified to show base types
- `components/FlowEditor.tsx` - Added double-click handler and modal integration

### Files Created:
- `components/NodePropertiesModal.tsx` - Comprehensive properties editor

## Benefits

1. **Flexibility**: Nodes can be created quickly and configured later
2. **Rich Metadata**: Capture detailed information about each entity
3. **Extensibility**: Custom fields allow for project-specific data
4. **Better UX**: Double-click interaction is intuitive
5. **Type Safety**: TypeScript ensures correct metadata structure
6. **Export Ready**: All data is properly serialized for backend integration
7. **Visual Clarity**: Smart edge coloring helps identify sensor-spatial relationships at a glance
8. **Dynamic Updates**: Edge styles automatically update when node types change

## Future Enhancements

Potential improvements:
- Import functionality to load saved graphs
- Validation rules for metadata fields
- Templates for common configurations
- Bulk edit capabilities
- Search/filter by metadata
- Integration with Python backend for analysis
