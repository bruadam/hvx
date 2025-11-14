# Edge Styling Guide

## Overview
The flow editor uses smart edge styling to visually distinguish between different types of connections in your spatial hierarchy.

## Edge Styling Rules

### 1. Spatial Entity → Spatial Entity
**Appearance**: Static grey line
**Animation**: None
**Use Case**: Hierarchical relationships (Portfolio → Building → Floor → Room)

```
Portfolio ──────[grey, static]────── Building
Building  ──────[grey, static]────── Floor
Floor     ──────[grey, static]────── Room
```

### 2. Sensor → Spatial Entity
**Appearance**: Colored line (matches sensor color)
**Animation**: Animated flow moving from sensor to spatial entity
**Use Case**: Sensor installed in/monitoring a spatial entity

```
Temperature Sensor ~~~~[red, animated]~~~> Room
Humidity Sensor    ~~~~[cyan, animated]~~> Room
CO2 Sensor         ~~~~[slate, animated]~> Building
```

### 3. Spatial Entity → Sensor
**Appearance**: Colored line (matches sensor color)
**Animation**: Animated flow from spatial entity to sensor
**Use Case**: Spatial entity has a sensor (reverse direction, same visual effect)

```
Room     <~~~[red, animated]~~~~ Temperature Sensor
Building <~~~[cyan, animated]~~~ Humidity Sensor
```

### 4. Sensor → Sensor
**Appearance**: Static grey line
**Animation**: None
**Use Case**: Sensor relationships (not typical, but supported)

```
Temperature Sensor ──────[grey, static]────── Humidity Sensor
```

## Color Reference

### Sensor Colors:
- **Temperature**: Red (#EF4444)
- **Humidity**: Cyan (#06B6D4)
- **CO2**: Slate (#64748B)
- **Occupancy**: Purple (#8B5CF6)
- **Light**: Yellow (#FBBF24)
- **Energy**: Green (#22C55E)

### Spatial Entity Colors (for node display):
- **Portfolio**: Purple (#8B5CF6)
- **Building**: Blue (#3B82F6)
- **Floor**: Green (#10B981)
- **Room**: Amber (#F59E0B)

## Dynamic Updates

Edge styles automatically update when:
1. A node type is changed via the properties modal
2. A new connection is created between nodes
3. The subtype of a sensor is changed (e.g., Temperature → Humidity)

### Example Scenario:
1. Create a connection: `Node A → Node B` (both default, grey edge)
2. Double-click Node A and change it to "Temperature Sensor"
3. Edge automatically updates to red with animation
4. Double-click Node A again and change it to "Humidity Sensor"
5. Edge automatically updates to cyan with animation

## Implementation Details

The edge styling logic checks:
1. **Source node type**: Is it a sensor or spatial entity?
2. **Target node type**: Is it a sensor or spatial entity?
3. **Sensor subtype**: What specific sensor type for color matching?

### Logic Flow:
```
if (source is sensor AND target is spatial):
    edge = sensor's color + animated
else if (source is spatial AND target is sensor):
    edge = sensor's color + animated
else:
    edge = grey + static
```

## Visual Benefits

1. **Quick Identification**: Instantly see which sensors are connected to which spaces
2. **Color Coding**: Each sensor type has a distinct color for easy recognition
3. **Flow Direction**: Animation shows the conceptual data flow
4. **Hierarchy Clarity**: Grey edges keep spatial hierarchy visually distinct
5. **Type Changes**: Real-time visual feedback when changing node types

## Best Practices

### Recommended Connection Patterns:
1. **Hierarchical Structure**: Use spatial-to-spatial connections
   - Portfolio → Buildings → Floors → Rooms

2. **Sensor Placement**: Connect sensors to their physical location
   - Room → Temperature Sensor
   - Room → Humidity Sensor
   - Building → Energy Sensor

3. **Mixed Hierarchy**: Sensors can connect at any level
   - Building-level sensors (HVAC, Energy)
   - Floor-level sensors (Ambient conditions)
   - Room-level sensors (Local conditions)

### Example Complete Graph:
```
Portfolio
├── Building 1
│   ├── Floor 1
│   │   ├── Room 101
│   │   │   ├── Temperature Sensor (red, animated)
│   │   │   └── CO2 Sensor (slate, animated)
│   │   └── Room 102
│   │       └── Humidity Sensor (cyan, animated)
│   └── Energy Sensor (green, animated) [building-level]
└── Building 2
    └── Floor 1
        └── Room 201
            └── Occupancy Sensor (purple, animated)
```

All spatial connections (vertical lines) are grey and static.
All sensor connections (leaf connections) are colored and animated.

## Export Format

Edge information is exported with styling data:
```json
{
  "edges": [
    {
      "source": "node_1",
      "target": "node_2",
      "animated": false,
      "style": {
        "stroke": "#9CA3AF",
        "strokeWidth": 2
      }
    },
    {
      "source": "sensor_1",
      "target": "room_1",
      "animated": true,
      "style": {
        "stroke": "#EF4444",
        "strokeWidth": 2
      }
    }
  ]
}
```

This allows backend systems to recreate the same visual representation if needed.
