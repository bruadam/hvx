# Domain Model Organization

## Overview

The domain models are now organized by their conceptual type, making the codebase more intuitive and maintainable. This document describes the new structure and how to use it.

## Directory Structure

```
core/domain/models/
├── base/                        # Abstract base classes
│   ├── __init__.py
│   ├── base_entity.py          # BaseEntity, HierarchicalEntity
│   ├── base_measurement.py     # BaseMeasurement, UtilityConsumption
│   ├── base_validation.py      # BaseValidation, ComplianceValidation
│   ├── base_analysis.py        # BaseAnalysis, MetricsAnalysis
│   └── base_dataset.py         # SensorDataset
│
├── entities/                    # Physical & logical entities
│   ├── __init__.py
│   ├── room.py                 # Room entity
│   ├── level.py                # Level/floor entity
│   └── building.py             # Building entity
│
├── measurements/                # Consumption & resource tracking
│   ├── __init__.py
│   ├── energy_consumption.py   # Energy (electricity, gas, heating, cooling)
│   ├── water_consumption.py    # Water (municipal, well, rainwater)
│   └── fuel_consumption.py     # Fuel (gas, oil, wood, hydrogen, co-gen)
│
├── validation/                  # Compliance & rule checking
│   ├── __init__.py
│   ├── violation.py            # Single point violation
│   └── compliance_result.py    # Aggregated compliance test result
│
├── analysis/                    # Analysis results & aggregations
│   ├── __init__.py
│   ├── room_analysis.py        # Room-level analysis
│   ├── building_analysis.py    # Building-level analysis
│   └── portfolio_analysis.py   # Portfolio-level analysis
│
└── datasets/                    # Sensor & time-series data
    ├── __init__.py
    └── dataset.py              # Dataset collection entity
```

## Model Categories

### 1. Base Models (`base/`)

**Purpose**: Abstract base classes providing common functionality

**Contains**:
- `BaseEntity[TChild]` - Core identity and metadata
- `HierarchicalEntity[TChild]` - Parent-child hierarchy management
- `BaseMeasurement[TValue]` - Time-bounded measurements
- `UtilityConsumption` - Utility consumption tracking (energy, water, fuel)
- `BaseValidation[TEntity]` - Validation and deviation logic
- `ComplianceValidation[TEntity]` - Standards compliance testing
- `BaseAnalysis[TEntity, TChildAnalysis]` - Analysis results structure
- `MetricsAnalysis[TEntity, TChildAnalysis]` - Compliance metrics and rankings
- `SensorDataset` - Sensor and metering data management

**Import Example**:
```python
from core.domain.models.base import (
    BaseEntity,
    HierarchicalEntity,
    UtilityConsumption,
    MetricsAnalysis,
)
```

### 2. Entity Models (`entities/`)

**Purpose**: Physical and logical entities representing spatial hierarchy

**Contains**:
- `Room` - Individual space with environmental measurements
- `Level` - Floor/level containing multiple rooms
- `Building` - Building containing levels and rooms

**Relationships**:
```
Building
├── Level 1
│   ├── Room 101
│   ├── Room 102
│   └── Room 103
└── Level 2
    ├── Room 201
    └── Room 202
```

**Import Example**:
```python
from core.domain.models.entities import Room, Level, Building

room = Room(id="R101", name="Conference Room A")
level = Level(id="L1", name="Ground Floor")
building = Building(id="B1", name="Main Office")
```

**Will Extend To**:
- Portfolio - Collection of buildings
- Zone - Logical grouping of rooms (e.g., HVAC zones)
- Campus - Collection of buildings on a campus

### 3. Measurement Models (`measurements/`)

**Purpose**: Track resource consumption and production over time

**Contains**:
- `EnergyConsumption` - Electricity, gas, heating, cooling, renewables
- `WaterConsumption` - Municipal, well, rainwater, greywater
- `FuelConsumption` - Gas, oil, propane, wood, biogas, hydrogen, co-gen

**Common Features** (inherited from `UtilityConsumption`):
- Measurement period tracking
- Source-based consumption breakdown
- Production tracking (PV, co-gen, etc.)
- Net consumption calculation
- Annualization
- Unit conversion

**Import Example**:
```python
from core.domain.models.measurements import (
    EnergyConsumption,
    WaterConsumption,
    FuelConsumption,
)

from datetime import datetime

# Track energy
energy = EnergyConsumption(
    measurement_start=datetime(2024, 1, 1),
    measurement_end=datetime(2024, 12, 31),
    heating_kwh=10000,
    electricity_kwh=5000,
    solar_pv_kwh=2000,
)
print(f"Net consumption: {energy.net_consumption} kWh")
print(f"Self-consumption rate: {energy.self_consumption_rate}%")

# Track water
water = WaterConsumption(
    measurement_start=datetime(2024, 1, 1),
    measurement_end=datetime(2024, 12, 31),
    municipal_water_m3=500,
    rainwater_m3=100,
)
print(f"Sustainable water: {water.sustainable_water_percentage}%")

# Track fuel
fuel = FuelConsumption(
    measurement_start=datetime(2024, 1, 1),
    measurement_end=datetime(2024, 12, 31),
    natural_gas_m3=1000,
    wood_pellets_kg=500,
)
print(f"Renewable fuel: {fuel.renewable_fuel_percentage}%")
```

**Will Extend To**:
- ElectricityConsumption - Detailed electricity tracking (grid, solar, wind, battery)
- BiomassConsumption - Detailed biomass fuel tracking
- RenewableProduction - Dedicated renewable energy production tracking

### 4. Validation Models (`validation/`)

**Purpose**: Compliance checking, rule validation, and violation tracking

**Contains**:
- `Violation` - Single point-in-time violation
- `ComplianceResult` - Aggregated test results with violations

**Common Features** (inherited from `BaseValidation`/`ComplianceValidation`):
- Measured vs expected values
- Deviation calculation
- Severity classification
- Compliance rate calculation
- Statistical measures

**Import Example**:
```python
from core.domain.models.validation import Violation, ComplianceResult
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.standard_type import StandardType
from datetime import datetime

# Create a violation
violation = Violation(
    timestamp=datetime(2024, 1, 15, 10, 30),
    measured_value=28.5,
    expected_min=20.0,
    expected_max=26.0,
    deviation=2.5,
    severity="moderate",
    is_valid=False,
)

# Create compliance result
result = ComplianceResult(
    test_id="temp_cat_ii",
    standard=StandardType.EN_16798_1,
    parameter=ParameterType.TEMPERATURE,
    compliance_rate=92.5,
    total_points=1000,
    compliant_points=925,
    non_compliant_points=75,
    violations=[violation],
    is_compliant=True,
    measured_value=24.5,
    is_valid=True,
)
```

**Will Extend To**:
- RuleViolation - Custom rule violations
- QualityCheck - Data quality validation
- ThresholdCheck - Simple threshold validation

### 5. Analysis Models (`analysis/`)

**Purpose**: Aggregated results with metrics, rankings, and recommendations

**Contains**:
- `RoomAnalysis` - Single room analysis results
- `BuildingAnalysis` - Building-wide aggregation
- `PortfolioAnalysis` - Portfolio-wide aggregation

**Common Features** (inherited from `MetricsAnalysis`):
- Compliance and quality scores
- Test aggregations
- Parameter statistics
- Rankings (best/worst performers)
- Issues and recommendations
- Severity breakdown
- Grade calculation (A-F)

**Import Example**:
```python
from core.domain.models.analysis import (
    RoomAnalysis,
    BuildingAnalysis,
    PortfolioAnalysis,
)
from core.domain.enums.status import Status

room_analysis = RoomAnalysis(
    entity_id="R101",
    entity_name="Conference Room A",
    status=Status.COMPLETED,
    compliance_rate=95.0,
    quality_score=98.5,
)

print(f"Grade: {room_analysis.compliance_grade}")  # A
print(f"Issues: {room_analysis.has_issues}")  # True/False
```

**Will Extend To**:
- ZoneAnalysis - HVAC zone analysis
- CampusAnalysis - Campus-wide analysis
- CustomAnalysis - User-defined analysis types

### 6. Dataset Models (`datasets/`)

**Purpose**: Sensor data, metering points, and time-series management

**Contains**:
- `Dataset` - Collection of buildings and sensor data

**Common Features** (inherited from `SensorDataset`):
- Time-series data management
- Data completeness tracking
- Parameter availability
- Time range filtering
- Statistical calculations

**Import Example**:
```python
from core.domain.models.datasets import Dataset
from pathlib import Path

dataset = Dataset(
    id="DS001",
    name="2024 Building Survey",
    source_directory=Path("/data/survey_2024"),
)
dataset.add_building("B1")
dataset.add_building("B2")
```

**Will Extend To**:
- EnvironmentalSensor - IEQ sensor data
- MeteringPoint - Utility meter data
- ClimateStation - Weather station data
- OccupancySensor - People counting data

## Import Patterns

### Pattern 1: Import from Category

```python
# Import all entities
from core.domain.models.entities import Room, Level, Building

# Import all measurements
from core.domain.models.measurements import (
    EnergyConsumption,
    WaterConsumption,
    FuelConsumption,
)

# Import all validation models
from core.domain.models.validation import Violation, ComplianceResult

# Import all analysis models
from core.domain.models.analysis import (
    RoomAnalysis,
    BuildingAnalysis,
    PortfolioAnalysis,
)
```

### Pattern 2: Import Specific Models

```python
# Import just what you need
from core.domain.models.entities.room import Room
from core.domain.models.measurements.energy_consumption import EnergyConsumption
from core.domain.models.validation.compliance_result import ComplianceResult
from core.domain.models.analysis.room_analysis import RoomAnalysis
```

### Pattern 3: Import Base Classes

```python
# When creating new model types
from core.domain.models.base import (
    HierarchicalEntity,
    UtilityConsumption,
    ComplianceValidation,
    MetricsAnalysis,
)

class ElectricityConsumption(UtilityConsumption):
    """Detailed electricity consumption tracking."""
    pass
```

## Benefits of This Organization

### 1. **Intuitive Structure**
- Clear separation by model type
- Easy to find related models
- Logical grouping of functionality

### 2. **Reduced Cognitive Load**
- Don't need to know all models to find what you need
- Category names explain purpose
- Clear parent-child relationships

### 3. **Better IDE Support**
- Autocomplete shows related models together
- Easy to browse by category
- Import statements are clearer

### 4. **Scalability**
- Easy to add new models to appropriate category
- Clear where new model types belong
- Can add subcategories as needed

### 5. **Team Collaboration**
- New team members understand structure quickly
- Clear ownership boundaries
- Easy to work on different categories in parallel

## Migration Guide

### Old Import Patterns → New Import Patterns

```python
# OLD
from core.domain.models.room import Room
from core.domain.models.energy_consumption import EnergyConsumption
from core.domain.models.compliance_result import ComplianceResult
from core.domain.models.room_analysis import RoomAnalysis

# NEW
from core.domain.models.entities import Room
from core.domain.models.measurements import EnergyConsumption
from core.domain.models.validation import ComplianceResult
from core.domain.models.analysis import RoomAnalysis
```

### Creating New Models

```python
# Creating a new measurement type
from core.domain.models.base import UtilityConsumption

class BiomassConsumption(UtilityConsumption):
    """Track biomass fuel consumption."""
    # Add to: core/domain/models/measurements/biomass_consumption.py
    pass

# Creating a new sensor type
from core.domain.models.base import SensorDataset

class OccupancySensor(SensorDataset):
    """Track occupancy data."""
    # Add to: core/domain/models/datasets/occupancy_sensor.py
    pass

# Creating a new analysis type
from core.domain.models.base import MetricsAnalysis

class ZoneAnalysis(MetricsAnalysis):
    """Analyze HVAC zone performance."""
    # Add to: core/domain/models/analysis/zone_analysis.py
    pass
```

## Quick Reference

| Model Type | Category | Base Class | Purpose |
|------------|----------|------------|---------|
| Room, Building | `entities/` | `HierarchicalEntity` | Spatial hierarchy |
| Energy, Water, Fuel | `measurements/` | `UtilityConsumption` | Resource consumption |
| Violation, ComplianceResult | `validation/` | `BaseValidation`, `ComplianceValidation` | Compliance checking |
| RoomAnalysis, BuildingAnalysis | `analysis/` | `MetricsAnalysis` | Aggregated results |
| Dataset | `datasets/` | `SensorDataset` | Time-series data |

## Future Organization

As the system grows, we may add additional categories:

```
core/domain/models/
├── base/                   # Existing
├── entities/               # Existing
│   ├── spatial/           # Room, Level, Building
│   ├── logical/           # Zone, System
│   └── organizational/    # Portfolio, Campus
├── measurements/           # Existing
│   ├── utilities/         # Energy, Water, Fuel
│   └── environmental/     # Climate, IEQ
├── validation/            # Existing
├── analysis/              # Existing
└── datasets/              # Existing
    ├── sensors/           # Environmental sensors
    ├── meters/            # Utility meters
    └── stations/          # Weather stations
```

## Conclusion

This organization provides:
- ✅ **Clear categorization** by model type
- ✅ **Intuitive navigation** of the codebase
- ✅ **Logical grouping** of related models
- ✅ **Easy extensibility** with new model types
- ✅ **Better team collaboration** through clear boundaries
- ✅ **Maintained backward compatibility** through proper imports

The structure scales from simple projects to complex portfolios while keeping the codebase organized and maintainable.
