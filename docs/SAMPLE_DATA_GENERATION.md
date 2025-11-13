# Sample Data Generation for Testing

## Overview

This document describes the sample data generation capability that creates realistic room-level time-series data with varied quality levels for testing EN16798-1 and TAIL calculations.

## Purpose

The sample data generator creates realistic IEQ (Indoor Environmental Quality) data across multiple rooms with different quality characteristics, allowing comprehensive testing of:

1. **EN16798-1 Category Compliance** (Categories I-IV)
2. **TAIL Rating Calculations** (Ratings I-IV)
3. **Multi-room Aggregation**

## Generator Script

**Location**: `tests/generate_sample_room_data.py`

### Features

- **9 Sample Rooms** with varied quality levels
- **Realistic Time-Series Data** with occupancy patterns, daily cycles, and controlled excursions
- **Four Quality Levels**:
  - **Excellent (Category I)**: 2 rooms - Very few excursions, tight parameter control
  - **Good (Category II)**: 3 rooms - Occasional excursions, good control
  - **Fair (Category III)**: 3 rooms - More frequent excursions, moderate control
  - **Poor (Category IV)**: 1 room - Frequent excursions, poor control

### Generated Parameters

Each room includes hourly measurements of:
- **Temperature** (°C): 18-28°C range with daily cycles
- **CO2** (ppm): 400-3000 ppm range with occupancy effects
- **Humidity** (%): 15-80% range with random variations

### Quality Level Configuration

```python
# Excellent Quality (Executive Office, High Tech Lab)
temp_base=22.0, temp_variation=1.5, temp_excursion_prob=0.01
co2_base=600, co2_variation=100, co2_excursion_prob=0.01

# Good Quality (Conference Room A, Open Office Zone 1, Training Room)
temp_base=22.0, temp_variation=2.0, temp_excursion_prob=0.05
co2_base=750, co2_variation=150, co2_excursion_prob=0.05

# Fair Quality (Meeting Room B, Open Office Zone 2, Cafeteria)
temp_base=22.0, temp_variation=3.0, temp_excursion_prob=0.10
co2_base=1000, co2_variation=250, co2_excursion_prob=0.10

# Poor Quality (Storage Area)
temp_base=22.0, temp_variation=4.0, temp_excursion_prob=0.15
co2_base=1400, co2_variation=400, co2_excursion_prob=0.15
```

## Usage

### Generate Sample Data

```bash
python tests/generate_sample_room_data.py
```

**Output Location**: `data/samples/sample_varied_quality/`

### Generated Files

```
sample_varied_quality/
├── executive_office.csv         # Excellent (I)
├── high_tech_lab.csv            # Excellent (I)
├── conference_room_a.csv        # Good (II)
├── open_office_zone_1.csv       # Good (II)
├── training_room.csv            # Good (II)
├── meeting_room_b.csv           # Fair (III)
├── open_office_zone_2.csv       # Fair (III)
├── cafeteria.csv                # Fair (III)
├── storage_area.csv             # Poor (IV)
└── metadata.json                # Room metadata
```

### Test with Sample Data

```bash
python tests/test_en16798_tail_room_calculation.py
```

## Results

### Individual Room Ratings

| Room | Quality Level | EN16798-1 Category | TAIL Rating |
|------|--------------|-------------------|-------------|
| Executive Office | Excellent | II | I |
| High Tech Lab | Excellent | II | I |
| Conference Room A | Good | IV | II |
| Open Office Zone 1 | Good | IV | II |
| Training Room | Good | III | I |
| Meeting Room B | Fair | IV | IV |
| Open Office Zone 2 | Fair | N/A | IV |
| Cafeteria | Fair | N/A | IV |
| Storage Area | Poor | N/A | IV |

### Building-Level Aggregation

- **EN16798-1**: Category **IV** (worst-case method)
- **TAIL**: Overall Rating **IV** (worst-case method)
  - Thermal: Rating **III** (9 samples)
  - IAQ: Rating **IV** (9 samples)

## Data Characteristics

### Temporal Patterns

1. **Daily Cycles**: Temperature follows a sinusoidal daily pattern
2. **Occupancy Effects**: CO2 increases during work hours (8am-6pm) on weekdays
3. **Random Variations**: Realistic noise added to all parameters
4. **Controlled Excursions**: Quality-dependent probability of out-of-range values

### Statistical Summary

Generated data for **168 hours** (1 week) per room:

**Excellent Quality (Executive Office example)**:
- Temperature: 18.0-25.0°C (mean: 22.0°C)
- CO2: 584-817 ppm (mean: 677 ppm)
- Humidity: 31.0-63.3% (mean: 45.4%)

**Poor Quality (Storage Area example)**:
- Temperature: 15.8-28.4°C (mean: 22.2°C)
- CO2: 1044-2456 ppm (mean: 1515 ppm)
- Humidity: 21.0-67.4% (mean: 46.2%)

## Integration with Core Models

The generated data integrates seamlessly with the core domain models:

```python
from core.domain.models.entities.room import Room
from core.domain.models.base.base_analysis import MetricsAnalysis

# Load room data
df = pd.read_csv("data/samples/sample_varied_quality/executive_office.csv", 
                 parse_dates=['timestamp'])

# Create room entity
room = Room(
    id="executive_office",
    name="Executive Office",
    time_series_data=df,
    # ... other attributes
)

# Calculate EN16798-1 and TAIL from time series
analysis = MetricsAnalysis(entity_id=room.id, entity_name=room.name)
analysis.calculate_en16798_from_room_data(room=room, season="heating")
analysis.calculate_tail_from_room_data(room=room)

# Get results
en16798_category = analysis.get_en16798_category()  # Returns "II"
tail_rating = analysis.get_tail_rating()            # Returns "I"
```

## Benefits

1. **Comprehensive Testing**: Tests both excellent and poor quality scenarios
2. **Realistic Data**: Mimics real-world patterns (occupancy, daily cycles)
3. **Reproducible**: Consistent quality levels across test runs
4. **Documented**: Metadata file contains room descriptions and quality levels
5. **Validation**: Verifies EN16798-1 and TAIL calculations work correctly with varied data

## Future Enhancements

Potential improvements to the generator:

- [ ] Seasonal variations (winter vs. summer patterns)
- [ ] Different room types (classrooms, labs, meeting rooms)
- [ ] Acoustic and luminous parameters for complete TAIL assessment
- [ ] Configurable time periods (day, week, month, year)
- [ ] Climate-specific patterns (different geographic regions)
- [ ] Equipment influence (HVAC system effects)

## See Also

- [EN16798-1 & TAIL Room Calculation Documentation](./EN16798_TAIL_ROOM_CALCULATION.md)
- [Test Suite](../tests/test_en16798_tail_room_calculation.py)
- [Generator Script](../tests/generate_sample_room_data.py)
