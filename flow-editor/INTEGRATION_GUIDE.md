# Flow Editor Integration Guide

## Complete Integration with Analytics Backend

This guide explains how the Flow Editor integrates with the Python analytics backend to use all available **standards** and **simulations**.

## Architecture Overview

```
Flow Editor (TypeScript/React)
    ↓ (HTTP/REST or Python Bridge)
Python Analytics Backend
    ├── Standards (EN16798, BR18, TAIL, WHO)
    ├── Simulations (Real EPC, RC Thermal, Occupancy, Ventilation)
    ├── Energy Metering (new)
    └── Data Aggregation (new)
```

## Available Standards

### 1. EN16798-1 (Indoor Environment)
- **ID**: `en16798_1`
- **Applies to**: Rooms with temperature, CO2, humidity data
- **Categories**: I (High), II (Normal), III (Moderate), IV (Low)
- **Countries**: All EU countries + UK, NO, CH
- **Required data**: Temperature (required), CO2 (optional), Humidity (optional)
- **Output**: Category rating, compliance percentage, violations

### 2. BR18 (Danish Building Regulations)
- **ID**: `br18`
- **Applies to**: Buildings in Denmark
- **Countries**: DK only
- **Building types**: Office, residential, education
- **Output**: Compliance status, specific requirement checks

### 3. TAIL (Indoor Air Quality)
- **ID**: `tail`
- **Applies to**: Rooms with air quality sensors
- **Required data**: CO2, VOC, PM2.5, PM10 (mix)
- **Output**: Air quality rating, pollutant levels

### 4. WHO Guidelines
- **ID**: `who`
- **Applies to**: Global indoor air quality assessment
- **Required data**: PM2.5, PM10, CO2
- **Output**: WHO compliance, health risk assessment

## Available Simulations

### 1. Real EPC (Energy Performance Certificate)
- **ID**: `real_epc`
- **Applies to**: Buildings with energy data
- **Required inputs**:
  - Primary energy (kWh/m²/year) OR
  - Energy meter data (electricity, gas, heating, etc.)
  - Building area (m²)
  - Country code
- **Output**: EPC rating (A-G), primary energy intensity
- **New**: Auto-calculates from energy meters!

### 2. RC Thermal Model
- **ID**: `rc_thermal`
- **Applies to**: Rooms/buildings with thermal data
- **Required inputs**: Outdoor temperature, solar irradiance
- **Optional inputs**: Internal gains
- **Output**: Temperature profile, heating/cooling power, energy demand

### 3. Occupancy Detection
- **ID**: `occupancy`
- **Applies to**: Rooms with CO2 sensors
- **Required inputs**: CO2 time series
- **Output**: Occupancy count, occupancy percentage, patterns

### 4. Ventilation Estimation
- **ID**: `ventilation`
- **Applies to**: Rooms with CO2 sensors
- **Required inputs**: CO2 time series
- **Output**: Air change rate (ACH), ventilation rate, quality score

## Node Types in Flow Editor

### Current Node Types

1. **Spatial Entities**:
   - Portfolio
   - Building
   - Floor
   - Room

2. **Sensors**:
   - Temperature
   - Humidity
   - CO2
   - Occupancy
   - Light
   - Energy

### Proposed Additional Node Types

3. **Standards** (new):
   - EN16798 Standard Node
   - BR18 Standard Node
   - TAIL Standard Node
   - WHO Standard Node

4. **Simulations** (new):
   - Real EPC Simulation Node
   - RC Thermal Simulation Node
   - Occupancy Simulation Node
   - Ventilation Simulation Node

5. **Energy Meters** (new):
   - Electricity Meter
   - Gas Meter
   - District Heating Meter
   - General Energy Meter

## Data Flow with Standards and Simulations

### Example 1: EN16798 Compliance Check

```
Room Node
    ↓ (connected to)
Temperature Sensor (with CSV data)
CO2 Sensor (with CSV data)
Humidity Sensor (with CSV data)
    ↓ (trigger analysis)
EN16798 Standard Node
    ↓ (compute)
Results:
  - Category: II
  - Compliance Rate: 87.5%
  - Violations: 15
  - Time in Cat I: 12%
  - Time in Cat II: 75%
```

### Example 2: Automatic EPC Calculation

```
Building Node (area_m2: 2500)
    ↓ (connected to)
Electricity Meter (85,000 kWh/year)
Gas Meter (45,000 kWh/year)
District Heating Meter (120,000 kWh/year)
    ↓ (trigger analysis)
Real EPC Simulation Node
    ↓ (compute)
Results:
  - Primary Energy: 142.3 kWh/m²/year
  - EPC Rating: B
  - Breakdown by carrier
```

### Example 3: Complete Building Analysis

```
Building Node
    ├─ Floor 1
    │   ├─ Room 101
    │   │   ├─ Temperature Sensor
    │   │   ├─ CO2 Sensor
    │   │   └─ Humidity Sensor
    │   └─ Room 102
    │       └─ Temperature Sensor
    ├─ Energy Meters
    │   ├─ Electricity Meter
    │   └─ Heating Meter
    ├─ Standards
    │   └─ EN16798 Standard
    └─ Simulations
        ├─ Real EPC
        └─ Occupancy Detection
```

## Integration Methods

### Method 1: Python Bridge (Recommended)

Use `python-shell` or similar to call Python scripts directly from Node.js:

```typescript
// Example: Call EN16798 analysis
import { PythonShell } from 'python-shell';

async function runEN16798Analysis(roomData: any) {
  const options = {
    mode: 'json',
    pythonPath: 'python3',
    scriptPath: '../',
    args: [JSON.stringify(roomData)]
  };

  return new Promise((resolve, reject) => {
    PythonShell.run('run_en16798.py', options, (err, results) => {
      if (err) reject(err);
      else resolve(results);
    });
  });
}
```

### Method 2: REST API Backend

Create a FastAPI server that exposes analytics endpoints:

```python
# backend/api.py
from fastapi import FastAPI
from core.entities import Room
from standards.en16798.analysis import EN16798Calculator

app = FastAPI()

@app.post("/analyze/en16798")
async def analyze_en16798(room_data: dict):
    room = Room(**room_data)
    result = room.compute_standards(force_recompute=True)
    return result.get('en16798', {})

@app.post("/simulate/real_epc")
async def simulate_real_epc(building_data: dict):
    building = Building(**building_data)
    epc_rating = building.calculate_and_update_epc_from_meters(
        building_data['aggregated_energy_data']
    )
    return {
        'rating': epc_rating,
        'primary_energy': building.computed_metrics.get('epc_primary_energy_kwh_m2')
    }
```

### Method 3: Web Assembly (Future)

Compile Python analytics to WebAssembly using Pyodide for client-side execution.

## Dummy Data Integration

### Current Dummy Data Structure

```
flow-editor/dummy_data/
├── temperature_sensor_room_101.csv
├── temperature_sensor_room_102.csv
├── humidity_sensor_room_101.csv
├── co2_sensor_room_101.csv
├── occupancy_sensor_room_101.csv
├── light_sensor_room_101.csv
├── energy_sensor_building_a.csv
└── sample_portfolio.json

data/samples/dummy_data/
├── building_a/
│   ├── level_1/
│   │   ├── conference_room_1.csv
│   │   ├── office_1.csv
│   │   └── office_2.csv
│   ├── level_2/
│   │   ├── meeting_room.csv
│   │   ├── office_3.csv
│   │   └── problematic_office.csv
│   ├── climate_data.csv  (outdoor temperature)
│   ├── energy_data.csv   (building consumption)
│   └── metadata.json
├── building_b/
└── building_c/
```

### Recommended Enhancements

1. **Add energy meter CSV files**:
   ```csv
   timestamp,electricity,gas,district_heating,unit
   2024-01-01T00:00:00,120.5,45.2,180.3,kWh
   2024-01-01T01:00:00,115.2,42.8,175.1,kWh
   ```

2. **Add building metadata JSON**:
   ```json
   {
     "id": "building_a",
     "name": "Building A - Main Office",
     "area_m2": 2500,
     "country": "DK",
     "building_type": "office",
     "energy_meters": [
       {
         "id": "meter_elec_001",
         "carrier": "electricity",
         "csv_file": "energy_data.csv",
         "column": "electricity"
       }
     ]
   }
   ```

3. **Add outdoor climate data** for adaptive comfort analysis

4. **Add pre-computed results** for testing

## Implementation Steps

### Step 1: Update Node Types

Add standard and simulation node types to `nodeTypes.ts`:

```typescript
export type BaseNodeType = 'spatialEntity' | 'sensor' | 'standard' | 'simulation' | 'energyMeter';

export type StandardType = 'en16798' | 'br18' | 'tail' | 'who';
export type SimulationType = 'real_epc' | 'rc_thermal' | 'occupancy' | 'ventilation';
export type EnergyMeterType = 'electricity' | 'gas' | 'district_heating' | 'general';
```

### Step 2: Update Node Library

Add new node categories to `NodeLibrary.tsx`:

```tsx
{/* Standards Section */}
<div>
  <h3>Standards</h3>
  {renderNodeItem('standard', 'EN16798', '#8B5CF6', 'ClipboardCheck')}
  {renderNodeItem('standard', 'BR18', '#EC4899', 'FileText')}
</div>

{/* Simulations Section */}
<div>
  <h3>Simulations</h3>
  {renderNodeItem('simulation', 'Real EPC', '#F59E0B', 'Zap')}
  {renderNodeItem('simulation', 'RC Thermal', '#EF4444', 'Flame')}
</div>

{/* Energy Meters Section */}
<div>
  <h3>Energy Meters</h3>
  {renderNodeItem('energyMeter', 'Energy Meter', '#10B981', 'Gauge')}
</div>
```

### Step 3: Update Statistics Panel

Enhance `StatisticsPanel.tsx` to display standards and simulation results:

```tsx
{/* Standards Results */}
{statistics.standardsResults && (
  <div>
    <h4>Standards Compliance</h4>
    {statistics.standardsResults.map(result => (
      <div key={result.standardId}>
        <span>{result.standardName}</span>
        <Badge color={result.status === 'compliant' ? 'green' : 'red'}>
          {result.category || result.status}
        </Badge>
        {result.complianceRate && (
          <span>{result.complianceRate}%</span>
        )}
      </div>
    ))}
  </div>
)}

{/* Simulation Results */}
{statistics.simulationResults && (
  <div>
    <h4>Simulation Results</h4>
    {statistics.simulationResults.map(result => (
      <div key={result.simulationId}>
        <span>{result.simulationName}</span>
        <span>{result.summary}</span>
      </div>
    ))}
  </div>
)}
```

### Step 4: Create API Integration

Create `lib/analyticsAPI.ts`:

```typescript
export async function analyzeWithEN16798(roomData: any) {
  // Option 1: Call Python backend
  const response = await fetch('http://localhost:8000/analyze/en16798', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(roomData)
  });
  return response.json();
}

export async function simulateRealEPC(buildingData: any) {
  const response = await fetch('http://localhost:8000/simulate/real_epc', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildingData)
  });
  return response.json();
}
```

### Step 5: Update Statistics Computation

Modify `statisticsUtils.ts` to call real backend:

```typescript
export async function computeStandardsCompliance(
  spatialNode: Node<NodeData>,
  connectedSensors: Node<NodeData>[]
): Promise<StandardResult[]> {
  // Prepare room data from node and sensors
  const roomData = {
    id: spatialNode.id,
    name: spatialNode.data.metadata.name,
    area_m2: spatialNode.data.metadata.area,
    timeseries_data: {},
    timestamps: []
  };

  // Extract sensor data
  connectedSensors.forEach(sensor => {
    if (sensor.data.csvData) {
      const sensorType = sensor.data.subType;
      roomData.timeseries_data[sensorType] = sensor.data.csvData.map(
        row => row[sensorType] || row.value
      );
      if (!roomData.timestamps.length && sensor.data.csvData.length) {
        roomData.timestamps = sensor.data.csvData.map(
          row => row.timestamp
        );
      }
    }
  });

  // Call Python backend
  try {
    const en16798Result = await analyzeWithEN16798(roomData);

    return [{
      standardId: 'en16798_1',
      standardName: 'EN 16798-1',
      status: en16798Result.achieved_category ? 'compliant' : 'non_compliant',
      category: en16798Result.achieved_category,
      complianceRate: en16798Result.overall_compliance_rate,
      violations: en16798Result.total_violations,
      details: en16798Result
    }];
  } catch (error) {
    console.error('Failed to compute standards:', error);
    return [];
  }
}
```

## Testing with Dummy Data

### Test Scenario 1: Room EN16798 Analysis

1. Create a Room node ("Conference Room 1")
2. Add Temperature sensor, upload `temperature_sensor_room_101.csv`
3. Add CO2 sensor, upload `co2_sensor_room_101.csv`
4. Add Humidity sensor, upload `humidity_sensor_room_101.csv`
5. Connect sensors to room
6. Add EN16798 Standard node, connect to room
7. Click "Compute Statistics" on EN16798 node
8. View results in Statistics Panel

**Expected Output**:
```
EN 16798-1: Category II
Compliance Rate: 87.5%
Temperature: Compliant
CO2: 15 violations
```

### Test Scenario 2: Building EPC Calculation

1. Create a Building node ("Building A")
   - Set area: 2500 m²
   - Set country: DK
2. Add Energy Meter nodes:
   - Electricity: upload `energy_sensor_building_a.csv`
   - Gas: create dummy data
   - District Heating: create dummy data
3. Connect meters to building
4. Add Real EPC Simulation node, connect to building
5. Click "Compute" on EPC node
6. View EPC rating

**Expected Output**:
```
Primary Energy: 142.3 kWh/m²/year
EPC Rating: B
Denmark 2020 Standard
```

### Test Scenario 3: Complete Portfolio

1. Import the enhanced `sample_portfolio.json`
2. Load all CSV files from `dummy_data/building_a/`
3. Compute statistics for all rooms
4. Aggregate to building level
5. Compute building EPC
6. Aggregate to portfolio level

**Expected Output**:
- Portfolio with 3 buildings
- 15+ rooms analyzed
- EN16798 compliance per room
- Building EPC ratings
- Portfolio-wide metrics

## Error Handling

### Common Issues and Solutions

1. **Python not found**:
   - Ensure Python 3.8+ is installed
   - Set `pythonPath` in configuration
   - Use virtual environment

2. **Missing dependencies**:
   ```bash
   cd analytics
   pip install -r requirements.txt
   ```

3. **Port conflicts**:
   - Check if port 8000 is available
   - Change port in FastAPI config

4. **CSV format errors**:
   - Ensure headers match expected format
   - Check timestamp format (ISO 8601)
   - Verify data types

5. **Missing metadata**:
   - Spatial entities need area_m2 for EPC
   - Buildings need country code
   - Sensors need unit information

## Configuration Files

### `.env.local` for Flow Editor

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_PYTHON_PATH=/usr/bin/python3
NEXT_PUBLIC_ANALYTICS_PATH=../
```

### Backend Configuration

Create `backend/config.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8000
  cors_origins:
    - http://localhost:3000
    - http://localhost:3001

analytics:
  standards:
    - en16798
    - br18
    - tail
    - who

  simulations:
    - real_epc
    - rc_thermal
    - occupancy
    - ventilation

  default_country: DK
  default_currency: EUR
```

## Next Steps

1. ✅ Update flow-editor node types
2. ✅ Create API integration layer
3. ⬜ Set up FastAPI backend server
4. ⬜ Update statisticsUtils with real implementations
5. ⬜ Add energy meter CSV examples to dummy data
6. ⬜ Create comprehensive test portfolio
7. ⬜ Add result visualization components
8. ⬜ Implement export to Python entities
9. ⬜ Add import from Python entities
10. ⬜ Create deployment documentation

## Resources

- [EN16798 Documentation](../standards/en16798/README.md)
- [Real EPC Configuration](../simulations/models/real_epc/config.yaml)
- [Energy Meter Integration](../docs/ENERGY_METER_INTEGRATION.md)
- [Flow Editor README](./README.md)
- [Python Analytics README](../README.md)

---

**Ready to integrate?** Start with Test Scenario 1 to validate the basic workflow!
