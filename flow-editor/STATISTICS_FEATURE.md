# Statistics Feature for SpatialEntity Nodes

## Overview

The Statistics Feature extends the flow-editor to display comprehensive analytics for SpatialEntity nodes (Portfolio, Building, Floor, Room). When CSV sensor data is loaded, you can now compute and visualize:

1. **Sensor Statistics** - Aggregated data from connected sensors
2. **Standards Compliance** - EN16798, BR18, and other building standards
3. **Simulation Results** - Occupancy detection, ventilation analysis, etc.

## How to Use

### 1. Load Sensor Data

First, connect sensor nodes to your spatial entity nodes and upload CSV data to the sensors:

1. Drag a **Spatial Entity** node (e.g., Room) onto the canvas
2. Drag **Sensor** nodes (Temperature, CO2, Humidity, etc.) onto the canvas
3. Connect the spatial entity to the sensors using edges
4. Click on each sensor node and use **Upload CSV** to load time-series data
5. Map the CSV columns to appropriate metric types (temperature, co2, humidity, etc.)

### 2. View Statistics

Once you have sensors connected with data:

1. Click on a **Spatial Entity** node (Portfolio, Building, Floor, or Room)
2. In the Node Details panel on the right, click the **View Statistics** button (purple)
3. A Statistics Panel will slide in from the right side

### 3. Compute Statistics

The Statistics Panel has three collapsible sections:

#### Sensor Statistics (Green)

Shows aggregated information about all connected sensors:
- Number of connected sensors by type
- Total data points across all sensors
- Time range of collected data

**Click "Compute Stats"** to calculate or refresh sensor statistics.

#### Standards Compliance (Blue)

Evaluates compliance with building standards based on sensor data:
- **EN 16798-1** (European indoor environment standard)
  - Shows achieved category (I, II, III, or IV)
  - Compliance rate percentage
  - Number of violations
- **BR-18** (Bygningsreglementet 2018 - Danish standard)
  - Compliance with temperature and CO2 ranges
- Other applicable standards based on country/region

**Click "Compute Standards"** to run standards analysis.

#### Simulation Results (Purple)

Runs predictive simulations based on sensor data:
- **Occupancy Detection**
  - Average and peak occupancy
  - Occupancy rate vs. design capacity
  - Detected peak times
- **Ventilation Analysis**
  - Average ventilation rate
  - Adequate ventilation percentage
  - CO2 levels and under-ventilated hours

**Click "Compute Simulations"** to run simulation analyses.

### 4. Visual Indicators

Nodes that have computed statistics display small badges at the bottom:
- 🟢 Green badge with number = Sensor stats computed
- 🔵 Blue badge with number = Standards analyzed
- 🟣 Purple badge with number = Simulations run

## Data Structure

### Statistics are stored in the node data:

```typescript
{
  statistics: {
    sensorStats: {
      sensorCount: number,
      connectedSensors: string[],
      sensorTypes: { temperature: 2, co2: 1, ... },
      dataPointsTotal: number,
      timeRange: { start: ISO8601, end: ISO8601 }
    },
    standardsResults: [
      {
        standardId: 'en16798',
        standardName: 'EN 16798-1',
        status: 'compliant' | 'non_compliant' | 'warning',
        category: 'I' | 'II' | 'III' | 'IV',
        complianceRate: 85.5,
        violations: 12,
        summary: 'Achieved Category II...',
        details: { ... }
      }
    ],
    simulationResults: [
      {
        simulationId: 'occupancy',
        simulationName: 'Occupancy Detection',
        status: 'completed' | 'failed',
        summary: 'Average occupancy: 12.3 people',
        results: { avgOccupancy: 12.3, ... }
      }
    ],
    lastComputedAt: ISO8601
  }
}
```

## Implementation Details

### Components

1. **StatisticsPanel** (`components/StatisticsPanel.tsx`)
   - Right-side panel displaying statistics
   - Three collapsible sections (sensors, standards, simulations)
   - Compute buttons for each section
   - Real-time loading states

2. **statisticsUtils** (`lib/statisticsUtils.ts`)
   - `computeSensorStatistics()` - Aggregates sensor data
   - `computeStandardsCompliance()` - Runs standards analysis (mock for now)
   - `computeSimulations()` - Runs simulations (mock for now)
   - `computeAllStatistics()` - Runs all three at once

3. **FlowEditor** (`components/FlowEditor.tsx`)
   - Added state for statistics panel visibility
   - Added handlers for computing statistics
   - Integrated StatisticsPanel with overlay
   - Added "View Statistics" button to node details

4. **CustomNode** (`components/CustomNode.tsx`)
   - Added visual indicators showing computed statistics
   - Badges display count of sensors, standards, and simulations

### Node Types Extensions

Added to `lib/nodeTypes.ts`:
- `SensorStats` interface
- `StandardResult` interface
- `SimulationResult` interface
- `StatisticsData` interface
- Extended `NodeData` with optional `statistics` field

## Integration with Python Backend

### Current Implementation

The current implementation uses **mock computations** in the frontend:
- Sensor statistics are computed from CSV data in the browser
- Standards and simulations return simulated results

### Future Backend Integration

To connect to the real Python analytics backend:

1. **Replace mock functions** in `statisticsUtils.ts` with API calls:

```typescript
export async function computeStandardsCompliance(
  spatialNode: Node<NodeData>,
  allNodes: Node<NodeData>[],
  allEdges: Edge[]
): Promise<StandardResult[]> {
  // Prepare data for backend
  const request = {
    nodeId: spatialNode.id,
    nodeType: spatialNode.data.subType,
    sensors: extractSensorData(spatialNode, allNodes, allEdges),
    metadata: spatialNode.data.metadata,
  };

  // Call Python backend
  const response = await fetch('/api/standards/compute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  const results = await response.json();
  return results.standards;
}
```

2. **Backend API endpoints** to implement:
   - `POST /api/sensors/aggregate` - Aggregate sensor statistics
   - `POST /api/standards/compute` - Run standards compliance
   - `POST /api/simulations/run` - Run simulations

3. **Data mapping**:
   - Convert CSV data to the format expected by Python entities
   - Map flow-editor node structure to `Room`, `Floor`, `Building`, `Portfolio` entities
   - Pass time-series data for `compute_standards()` and `compute_simulations()`

## Example Workflow

### Complete Analysis for a Room

1. Create a Room node
2. Connect Temperature, CO2, and Humidity sensors
3. Upload CSV files with hourly data for each sensor
4. Click on the Room node
5. Click "View Statistics"
6. Click "Compute Stats" - See 3 sensors, 2,160 data points (24h × 30 days × 3)
7. Click "Compute Standards" - See EN16798 Category II, 82% compliance
8. Click "Compute Simulations" - See average occupancy of 8.5 people

### Portfolio-Level Analysis

1. Import a portfolio ZIP file (creates hierarchy automatically)
2. For each building:
   - Select building node
   - View Statistics → Compute all
3. Select portfolio node at the top
4. View Statistics
5. Compute all statistics to see aggregated portfolio-wide results

## Troubleshooting

### "No sensor data available"

- Make sure sensors are connected via edges to the spatial entity
- Verify CSV data is uploaded and has data rows
- Check that CSV columns are mapped to metric types

### Standards showing "not_computed"

- Requires temperature data at minimum for EN16798
- Some standards require specific combinations (e.g., BR18 needs temp + CO2)

### Simulations not running

- Occupancy detection requires CO2 data
- Ventilation analysis requires CO2 data
- Check that the CSV data has appropriate columns

## Future Enhancements

1. **Export statistics** to PDF/Excel reports
2. **Historical comparison** - Compare statistics over time
3. **Real-time updates** - Live sensor data streaming
4. **Custom thresholds** - Define custom compliance thresholds
5. **Batch computation** - Compute statistics for multiple nodes at once
6. **Visualization** - Add charts and graphs to the statistics panel
7. **Alerts** - Set up notifications for non-compliance
8. **Data validation** - Validate sensor data quality before analysis

## Technical Notes

### Performance

- Sensor statistics are computed synchronously (fast)
- Standards and simulations use `async/await` with loading states
- Large datasets (>10,000 points per sensor) may benefit from Web Workers

### State Management

- Statistics are stored directly in the node's data
- Updates trigger React Flow re-renders efficiently
- Statistics persist in JSON export

### Accessibility

- All buttons have keyboard navigation
- Color-coded badges have text labels
- Panels can be closed with Escape key (future enhancement)

## Related Files

- `/components/StatisticsPanel.tsx` - Main statistics UI
- `/lib/statisticsUtils.ts` - Computation logic
- `/lib/nodeTypes.ts` - TypeScript interfaces
- `/components/FlowEditor.tsx` - Integration
- `/components/CustomNode.tsx` - Visual indicators
- `/core/entities.py` - Python SpatialEntity classes
- `/core/analysis.py` - Python analysis framework
- `/standards/*/analysis.py` - Standards implementations
