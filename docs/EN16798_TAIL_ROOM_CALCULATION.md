# EN16798-1 and TAIL Room-Level Calculation Implementation

## Overview

Updated the `MetricsAnalysis` class in `core/domain/models/base/base_analysis.py` to support **direct calculation** of EN16798-1 and TAIL ratings from room-level time series data.

## What Was Added

### 1. `calculate_en16798_from_room_data()` Method

Calculates EN 16798-1 indoor environmental quality compliance directly from room time series data.

**Features:**
- Analyzes time series data (temperature, CO2, humidity) against EN 16798-1 thresholds
- Supports all four categories (I, II, III, IV)
- Calculates compliance rate for each category as percentage of time within limits
- Determines achieved category (highest category with ≥95% compliance)
- Computes overall IEQ score as weighted average of parameter compliance
- Supports both fixed thresholds and adaptive comfort model

**Parameters:**
- `room`: Room entity with `time_series_data` (pandas DataFrame)
- `outdoor_running_mean_temp`: Optional running mean outdoor temperature for adaptive comfort
- `season`: "heating" or "cooling" season

**Returns:**
Stores EN 16798-1 compliance data in `standard_compliance` with:
```python
{
    "standard": "en16798-1",
    "achieved_category": "cat_ii",  # or None if not achieved
    "category_compliance": {
        "cat_i": 45.2,   # % of time compliant
        "cat_ii": 92.3,
        "cat_iii": 98.1,
        "cat_iv": 100.0
    },
    "ieq_score": 85.4,  # Overall IEQ score (0-100%)
    "season": "heating",
    "adaptive_comfort": False,
    "outdoor_running_mean_temp": None,
    "calculation_method": "time_series_analysis",
    "total_hours_analyzed": 8760
}
```

### 2. `calculate_tail_from_room_data()` Method

Calculates TAIL (Thermal, Acoustic, Indoor Air Quality, Luminous) ratings directly from room time series data.

**Features:**
- Analyzes each parameter against configurable thresholds
- Categorizes parameters into TAIL categories (T, A, I, L)
- Calculates compliance rate for each parameter
- Determines ratings (I-IV) based on compliance percentages
- Aggregates parameters within categories using worst-case method
- Computes overall TAIL rating as worst category rating

**Parameters:**
- `room`: Room entity with `time_series_data`
- `parameter_thresholds`: Optional custom thresholds for each parameter
  ```python
  {
      'temperature': {'lower': 20.0, 'upper': 26.0},
      'co2': {'lower': 0, 'upper': 1000},
      'humidity': {'lower': 30, 'upper': 60}
  }
  ```

**Returns:**
Stores TAIL rating data in `standard_compliance` with:
```python
{
    "overall_rating": 2,  # I=1 (best) to IV=4 (worst)
    "overall_rating_label": "II",
    "categories": {
        "thermal": {
            "rating": 2,
            "rating_label": "II",
            "average_compliance": 87.5,
            "parameter_count": 2
        },
        "acoustic": {...},
        "iaq": {...},
        "luminous": {...}
    },
    "parameters": {
        "temperature": {
            "compliance_rate": 85.2,
            "rating": 2,
            "rating_label": "II"
        },
        ...
    },
    "calculation_method": "time_series_analysis",
    "total_hours_analyzed": 8760
}
```

## Integration with Existing Methods

The new methods integrate seamlessly with existing aggregation methods:

1. **Child Analysis** → Calculate EN16798/TAIL from room data
2. **Building Analysis** → Aggregate using `aggregate_child_standard_compliance()`
3. **Portfolio Analysis** → Aggregate across buildings

## Usage Example

```python
from core.domain.models.entities.room import Room
from core.domain.models.base.base_analysis import MetricsAnalysis
import pandas as pd

# Load room with time series data
df = pd.read_csv('room_data.csv', parse_dates=['timestamp'])
room = Room(
    id="office_101",
    name="Office 101",
    area=25.0,
    volume=75.0,
    occupancy=2,
    room_type="office",
    time_series_data=df,
    data_start=df['timestamp'].min(),
    data_end=df['timestamp'].max()
)

# Create analysis instance
analysis = MetricsAnalysis(
    entity_id=room.id,
    entity_name=room.name
)

# Calculate EN16798-1 compliance from room data
analysis.calculate_en16798_from_room_data(
    room=room,
    season="heating"
)

# Calculate TAIL ratings from room data
analysis.calculate_tail_from_room_data(
    room=room,
    parameter_thresholds={
        'temperature': {'lower': 20.0, 'upper': 26.0},
        'co2': {'lower': 0, 'upper': 1000},
        'humidity': {'lower': 30, 'upper': 60}
    }
)

# Access results
en16798_category = analysis.get_en16798_category()
tail_rating = analysis.get_tail_rating()

print(f"EN16798-1 Category: {en16798_category}")
print(f"TAIL Rating: {tail_rating}")

# Get detailed data
en16798_data = analysis.get_standard_compliance("en16798-1")
tail_data = analysis.get_standard_compliance("tail")
```

## Multi-Room Aggregation Example

```python
# Analyze multiple rooms
room_analyses = []
for room in rooms:
    analysis = MetricsAnalysis(
        entity_id=room.id,
        entity_name=room.name
    )
    analysis.calculate_en16798_from_room_data(room)
    analysis.calculate_tail_from_room_data(room)
    room_analyses.append(analysis)

# Aggregate at building level
building_analysis = MetricsAnalysis(
    entity_id="building_a",
    entity_name="Building A",
    child_count=len(room_analyses)
)

building_analysis.aggregate_child_standard_compliance(
    child_analyses=room_analyses,
    standard="both"  # Aggregate both EN16798-1 and TAIL
)

# Get building-level results
building_en16798 = building_analysis.get_en16798_category()
building_tail = building_analysis.get_tail_rating()
```

## Test Results

All tests pass successfully:
- ✅ EN16798-1 calculation from room time series data
- ✅ TAIL calculation from room time series data  
- ✅ Multi-room aggregation of both standards

Example output from test:
```
Office 1:
  EN16798-1: Category IV (83.13% IEQ score)
  Category Compliance:
    - Category I: 11.90%
    - Category II: 49.40%
    - Category III: 75.60%
    - Category IV: 99.40%
    
  TAIL: Overall Rating III
  Categories:
    - Thermal: III (80.06% avg compliance)
    - IAQ: I (100.00% avg compliance)
  Parameters:
    - temperature: III (60.12% compliance)
    - co2: I (100.00% compliance)
    - humidity: I (100.00% compliance)
```

## Benefits

1. **Direct Calculation**: No need for pre-aggregated test results
2. **Flexible Thresholds**: Support custom thresholds per parameter
3. **Time-Based Compliance**: Calculates % of time within limits
4. **Comprehensive Details**: Returns category-by-category breakdown
5. **Standard Alignment**: Uses official EN 16798-1 and TAIL methodologies
6. **Seamless Aggregation**: Works with existing aggregation infrastructure

## Files Modified

- `core/domain/models/base/base_analysis.py` - Added two new methods to `MetricsAnalysis` class
- `tests/test_en16798_tail_room_calculation.py` - Comprehensive test suite (new file)

## Dependencies

- Uses existing `EN16798StandardCalculator` for threshold calculations
- Uses existing `TAILRatingCalculator` for rating conversions
- Leverages room entity's `time_series_data` (pandas DataFrame)
- Compatible with existing aggregation methods
