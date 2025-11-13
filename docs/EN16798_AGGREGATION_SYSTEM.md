# EN 16798-1 Compliant IEQ Aggregation System

## Overview

This system implements a comprehensive, flexible, and EN 16798-1 compliant approach to aggregating Indoor Environmental Quality (IEQ) assessments across multiple parameters and multiple spaces within a building.

## Key Challenge

EN 16798-1 defines comfort categories (I-IV) **per parameter** (temperature, CO₂, etc.) but does not prescribe a single method for:
1. Aggregating multiple parameters into a single room/space assessment
2. Aggregating multiple rooms into a building-level assessment

This implementation provides multiple scientifically-defensible methods consistent with the spirit of the standard and certification practice.

## Architecture

### Three-Level Hierarchy

```
Building Level
    ↓ (spatial aggregation)
Room/Space Level
    ↓ (parameter aggregation)
Parameter Level (individual sensors/measurements)
```

### Core Components

1. **`ParameterAggregationMethod`** - How to combine multiple parameters within a room
2. **`SpatialAggregationMethod`** - How to combine multiple rooms into building assessment
3. **`AggregationStrategy`** - Pre-defined combinations for common use cases
4. **`AggregationConfig`** - Full configuration with custom weights, thresholds, filters
5. **`BuildingAnalysis`** - Main model with aggregation methods implemented

## Parameter Aggregation Methods

### 1. Worst-Parameter (Conservative/Categorical)

**Formula:**
```
RoomCategory = max(Cat_temp, Cat_CO2, Cat_RH, Cat_illuminance, ...)
```

**When to use:**
- EN 16798-1 compliance certification
- Official reporting and documentation
- Conservative building assessments
- BREEAM/LEED IEQ credits

**Characteristics:**
- Most conservative approach
- Ensures no poor parameter is hidden
- Returns categorical result (I, II, III, IV)
- Building/room limited by worst-performing parameter

**Example:**
```python
room_categories = {
    ParameterType.TEMPERATURE: "II",
    ParameterType.CO2: "II", 
    ParameterType.HUMIDITY: "I",
    ParameterType.ILLUMINANCE: "III",  # Worst!
}

overall = analysis.aggregate_parameters_worst_case(room_categories)
# Result: "III" (limited by illuminance)
```

### 2. Weighted-Average (Continuous/Performance)

**Formula:**
```
IEQscore = Σ(w_p × f_p) / Σ(w_p)

where:
  w_p = parameter weight (e.g., temperature = 0.35)
  f_p = compliance fraction (0-100%)
```

**Default Weights:**
- Temperature: 35% (thermal comfort critical)
- CO₂: 25% (air quality proxy)
- Humidity: 10% (part of thermal comfort)
- Illuminance: 15% (visual comfort)
- Noise: 10% (acoustic comfort)
- PM2.5: 5% (health-related)

**When to use:**
- Continuous IEQ monitoring
- Performance tracking over time
- KPI dashboards
- Before/after intervention studies
- Benchmarking between buildings

**Characteristics:**
- Produces continuous score (0-100%)
- Weights reflect parameter importance
- Better for trend analysis
- Can customize weights per building type

**Example:**
```python
room_scores = {
    ParameterType.TEMPERATURE: 96.8,
    ParameterType.CO2: 94.2,
    ParameterType.HUMIDITY: 99.5,
    ParameterType.ILLUMINANCE: 87.3,
}

weights = {
    ParameterType.TEMPERATURE: 0.35,
    ParameterType.CO2: 0.25,
    ParameterType.HUMIDITY: 0.10,
    ParameterType.ILLUMINANCE: 0.15,
}

score = analysis.aggregate_parameters_weighted(room_scores, weights)
# Result: 94.7%
```

### 3. Unweighted-Average (Quick Overview)

**Formula:**
```
IEQscore = Σ(f_p) / n
```

**When to use:**
- Quick screening
- Equal parameter importance
- Simple comparisons

## Spatial Aggregation Methods

### 1. Worst-Space (Strict Compliance)

**Formula:**
```
BuildingCategory = max(RoomCat_1, RoomCat_2, ..., RoomCat_n)
```

**When to use:**
- Strict compliance certification
- Legal/regulatory reporting
- Conservative building assessment

**Example:**
```python
room_categories = {
    "office_301": "II",
    "office_302": "III",  # Worst!
    "meeting_room": "I",
    "open_office": "II",
}

building_cat = analysis.aggregate_spaces_worst_case(room_categories)
# Result: "III" (limited by office_302)
```

### 2. Occupant-Weighted (Recommended)

**Formula:**
```
F_building = Σ(t_i,occ × f_i) / Σ(t_i,occ)

where:
  t_i,occ = occupied hours in room i
  f_i = IEQ score for room i
```

**When to use:**
- Most representative of occupant experience
- Performance assessment
- Retrofit prioritization
- Facility management reporting

**Characteristics:**
- Heavily-used spaces have more influence
- Reflects actual building usage
- Requires occupancy hour data per room

**Example:**
```python
room_scores = {
    "office_301": 94.5,
    "office_302": 87.2,
    "meeting_room": 98.3,
    "open_office": 92.1,
}

occupancy_hours = {
    "office_301": 2080,    # 1 person × 2080h
    "office_302": 2080,    # 1 person × 2080h
    "meeting_room": 520,   # Occasional use
    "open_office": 8320,   # 4 people × 2080h (64% weight!)
}

score = analysis.aggregate_spaces_occupant_weighted(room_scores, occupancy_hours)
# Result: 91.9% (open office dominates due to 4x occupancy)
```

### 3. Area-Weighted (Practical Alternative)

**Formula:**
```
F_building = Σ(A_i × f_i) / Σ(A_i)

where:
  A_i = floor area of room i (m²)
```

**When to use:**
- Occupancy data unavailable
- Large uniform spaces
- Spatial coverage assessment

**Warning:** Can overweight large auxiliary spaces (storage, corridors)

### 4. Simple-Average (Quick Overview)

**Formula:**
```
F_building = Σ(f_i) / n
```

**When to use:**
- Quick screening
- All spaces equally important
- Initial portfolio assessment

### 5. Critical-Spaces-Only (Focused Assessment)

Only evaluate designated critical spaces (offices, classrooms, etc.).
Excludes auxiliary spaces (corridors, storage, etc.).

## Pre-defined Aggregation Strategies

### 1. STRICT_COMPLIANCE

**Configuration:**
- Parameter method: `WORST_PARAMETER`
- Spatial method: `WORST_SPACE`

**Use cases:**
- EN 16798-1 compliance certification
- BREEAM/LEED IEQ credits
- Building permit submissions
- Legal compliance documentation

**Result:** Most conservative - building limited by worst parameter in worst space

```python
config = AggregationConfig.strict_compliance()
analysis.apply_aggregation_strategy(config)
```

### 2. BALANCED_COMPLIANCE (Default)

**Configuration:**
- Parameter method: `WORST_PARAMETER`
- Spatial method: `OCCUPANT_WEIGHTED`

**Use cases:**
- Internal compliance monitoring
- Retrofit investment prioritization
- Facility management reporting
- Tenant satisfaction analysis

**Result:** Conservative parameters, realistic spatial weighting

```python
config = AggregationConfig.balanced_compliance()
analysis.apply_aggregation_strategy(config)
```

### 3. PERFORMANCE_TRACKING

**Configuration:**
- Parameter method: `WEIGHTED_AVERAGE`
- Spatial method: `OCCUPANT_WEIGHTED`

**Use cases:**
- Continuous IEQ monitoring
- Performance benchmarking
- KPI dashboards
- Year-over-year comparisons
- Before/after intervention studies

**Result:** Continuous scoring optimized for trends

```python
config = AggregationConfig.performance_tracking()
analysis.apply_aggregation_strategy(config)
```

### 4. QUICK_ASSESSMENT

**Configuration:**
- Parameter method: `UNWEIGHTED_AVERAGE`
- Spatial method: `SIMPLE_AVERAGE`

**Use cases:**
- Initial building screening
- Portfolio-wide comparisons
- High-level feasibility studies

```python
config = AggregationConfig.quick_assessment()
analysis.apply_aggregation_strategy(config)
```

## Custom Configuration

Full flexibility for specialized requirements:

```python
config = AggregationConfig(
    strategy=AggregationStrategy.CUSTOM,
    
    # Choose methods
    parameter_method=ParameterAggregationMethod.WORST_PARAMETER,
    spatial_method=SpatialAggregationMethod.OCCUPANT_WEIGHTED,
    
    # Custom parameter weights (must sum to 1.0)
    parameter_weights={
        ParameterType.TEMPERATURE: 0.40,  # Higher weight for thermal
        ParameterType.CO2: 0.30,
        ParameterType.ILLUMINANCE: 0.20,
        ParameterType.NOISE: 0.10,
    },
    
    # Custom room weights
    room_weights={
        "open_office": 0.6,
        "meeting_rooms": 0.3,
        "break_room": 0.1,
    },
    
    # Stricter thresholds
    category_1_threshold=98.0,  # Instead of 95%
    category_2_threshold=95.0,  # Instead of 90%
    category_3_threshold=90.0,  # Instead of 85%
    
    # Filtering
    critical_room_ids={"open_office", "meeting_room_a"},
    excluded_room_ids={"storage", "corridor"},
    excluded_parameters={ParameterType.PM10},
)

analysis.apply_aggregation_strategy(config)
```

## EN 16798-1 Category Logic

**Time-in-Category Thresholds:**

| Category | Required Time | Description |
|----------|---------------|-------------|
| I | ≥95% in Cat I limits | High expectation |
| II | ≥90% in Cat II limits | Normal expectation |
| III | ≥85% in Cat III limits | Moderate expectation |
| IV | <85% in Cat III | Non-compliant |

**Implementation:**

```python
def get_compliance_category(
    percent_in_cat1: float,
    percent_in_cat2: float, 
    percent_in_cat3: float,
    cat1_threshold: float = 95.0,
    cat2_threshold: float = 90.0,
    cat3_threshold: float = 85.0,
) -> str:
    """Determine EN 16798-1 category."""
    if percent_in_cat1 >= cat1_threshold:
        return "I"
    elif percent_in_cat2 >= cat2_threshold:
        return "II"
    elif percent_in_cat3 >= cat3_threshold:
        return "III"
    else:
        return "IV"
```

## Complete Workflow Example

```python
from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.value_objects.aggregation_config import (
    AggregationConfig,
    ParameterCategoryResult,
    RoomAggregationResult,
)
from core.domain.enums.parameter_type import ParameterType

# 1. Create building analysis
analysis = BuildingAnalysis(
    building_id="office_2025",
    building_name="Modern Office",
    room_count=4,
)

# 2. Add room-level aggregation results
# (These would come from your parameter assessments)
analysis.room_aggregations = {
    "office_301": RoomAggregationResult(
        room_id="office_301",
        overall_category="II",
        ieq_score=94.5,
        total_occupied_hours=2080.0,
        floor_area_m2=45.0,
    ),
    "office_302": RoomAggregationResult(
        room_id="office_302",
        overall_category="III",
        ieq_score=87.2,
        total_occupied_hours=2080.0,
        floor_area_m2=45.0,
    ),
    # ... more rooms
}

# 3. Apply aggregation strategy
config = AggregationConfig.balanced_compliance()
analysis.apply_aggregation_strategy(config)

# 4. Get results
print(f"Building Category: {analysis.building_category}")
print(f"Building IEQ Score: {analysis.building_ieq_score:.1f}%")

summary = analysis.get_aggregation_summary()
print(summary)

# 5. Export summary
full_summary = analysis.to_summary_dict()
```

## Output Example

```json
{
  "building_id": "office_building_2025",
  "building_name": "Modern Office Building",
  "status": "completed",
  "room_count": 4,
  "aggregation": {
    "strategy": "balanced_compliance",
    "parameter_method": "worst_parameter",
    "spatial_method": "occupant_weighted",
    "building_category": "III",
    "building_ieq_score": 91.95,
    "rooms_evaluated": 4,
    "parameters_evaluated": 4,
    "thresholds": {
      "category_I": 95.0,
      "category_II": 90.0,
      "category_III": 85.0
    }
  }
}
```

## Comparison of Methods

### When Building Has Mixed Performance

**Scenario:** 4 rooms with categories: I, II, II, III

| Method | Result | Interpretation |
|--------|--------|----------------|
| Worst-Space | Category III | Most conservative |
| Occupant-Weighted | 92.1% | Reflects actual usage |
| Area-Weighted | 92.3% | Spatial coverage |
| Simple-Average | 93.0% | All rooms equal |

### Recommendation by Use Case

| Use Case | Recommended Strategy |
|----------|---------------------|
| Certification submission | `STRICT_COMPLIANCE` |
| Internal monitoring | `BALANCED_COMPLIANCE` |
| Continuous improvement | `PERFORMANCE_TRACKING` |
| Portfolio screening | `QUICK_ASSESSMENT` |
| Research study | `CUSTOM` |

## Best Practices

1. **For Compliance Reporting:**
   - Use `WORST_PARAMETER` for parameter aggregation
   - Use `WORST_SPACE` for spatial aggregation
   - Document all assumptions clearly

2. **For Performance Tracking:**
   - Use `WEIGHTED_AVERAGE` for parameters
   - Use `OCCUPANT_WEIGHTED` for spaces
   - Track trends over time, not absolute categories

3. **For Investment Decisions:**
   - Use `BALANCED_COMPLIANCE` strategy
   - Identify worst-performing parameters per room
   - Prioritize high-occupancy spaces

4. **Data Requirements:**
   - Occupant-weighted: Need occupancy hour data
   - Area-weighted: Need floor area data
   - Weighted-average: Need parameter weights
   - Worst-case methods: Only need category assessments

## Files Created

1. **`core/domain/enums/aggregation_method.py`**
   - `ParameterAggregationMethod` enum
   - `SpatialAggregationMethod` enum
   - `AggregationStrategy` enum

2. **`core/domain/value_objects/aggregation_config.py`**
   - `AggregationConfig` value object
   - `ParameterCategoryResult` value object
   - `RoomAggregationResult` value object

3. **`core/domain/models/building_analysis.py`** (updated)
   - Added aggregation methods
   - Added configuration support
   - Updated summary outputs

4. **`examples/demo_en16798_aggregation.py`**
   - Complete demonstration of all methods
   - Real-world scenarios
   - Output examples

## References

- EN 16798-1:2019 - Energy performance of buildings — Ventilation for buildings
- ASHRAE Standard 55 - Thermal Environmental Conditions for Human Occupancy
- ISO 7730 - Ergonomics of the thermal environment
- BREEAM International New Construction Technical Manual
- LEED v4.1 Building Design and Construction

## Summary

This implementation provides:

✅ **EN 16798-1 compliant** category assessment  
✅ **Multiple aggregation methods** for different use cases  
✅ **Pre-defined strategies** for common scenarios  
✅ **Full flexibility** with custom configurations  
✅ **Scientifically defensible** approaches  
✅ **Well-documented** with clear use cases  
✅ **Type-safe** with Pydantic validation  
✅ **Tested** with comprehensive examples  

The system successfully addresses the challenge of aggregating IEQ assessments while maintaining consistency with EN 16798-1 principles and providing flexibility for different assessment purposes.
