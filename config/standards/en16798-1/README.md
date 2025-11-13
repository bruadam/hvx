# EN 16798-1 Standard Configuration

## Overview
Energy performance of buildings - Ventilation for buildings - Part 1: Indoor environmental input parameters for design and assessment of energy performance of buildings addressing indoor air quality, thermal environment, lighting and acoustics.

**Status:** ✅ Fully Implemented (Dynamic Adaptive Comfort Model)

**Implementation:** All EN 16798-1 calculations are performed programmatically by `EN16798StandardCalculator` 
with support for both fixed thresholds (mechanical conditioning) and adaptive thermal comfort (natural/mixed-mode ventilation).

**Note:** YAML configuration files have been removed as thresholds are now calculated dynamically based on:
- Ventilation type (mechanical, natural, mixed-mode)
- Outdoor running mean temperature (for adaptive comfort)
- Category level (I, II, III, IV)
- Seasonal conditions

## Standard Description

EN 16798-1 defines four categories of indoor environmental quality:

- **Category I**: High level of expectation (sensitive/fragile occupants like children, elderly, disabled)
- **Category II**: Normal level of expectation (new buildings and renovations - default)
- **Category III**: Moderate level of expectation (existing buildings)
- **Category IV**: Values outside categories I-III (acceptable for limited periods only)

## Parameters Covered

### 1. Thermal Environment

**Mechanically Conditioned Buildings (Fixed Thresholds):**
- Temperature ranges for heating season (based on design values)
- Temperature ranges for cooling season (based on design values)
- Category-specific comfort bands

**Naturally Ventilated / Mixed-Mode Buildings (Adaptive Comfort):**
- Dynamic temperature thresholds based on outdoor running mean temperature
- Comfort temperature: T_comf = 0.33 × T_rm + 18.8
- Acceptable ranges vary by category:
  - Category I: ±2°C from comfort temperature
  - Category II: ±3°C from comfort temperature
  - Category III: ±4°C from comfort temperature
  - Category IV: ±5°C from comfort temperature
- Valid for: 10°C ≤ T_rm ≤ 30°C

**Running Mean Outdoor Temperature Calculation:**
- Exponentially weighted: T_rm = (1-α) × [T_ed-1 + α×T_ed-2 + α²×T_ed-3 + ...]
- Default α = 0.8 (recommended by standard)
- Requires minimum 7 days of daily mean outdoor temperatures

### 2. Indoor Air Quality
- CO2 concentration limits (above outdoor)
- Ventilation rates based on:
  - Number of occupants
  - Floor area
  - Building pollution level (very low, low, non-low)
  - Activity level (metabolic rate)

### 3. Humidity
- Relative humidity ranges per category
- Prevention of mold growth and comfort issues

### 4. Ventilation Requirements
- Occupant-based ventilation (L/(s·person))
- Building emission-based ventilation (L/(s·m²))
- Total ventilation = n × q_p + A × q_B

## Room Metadata Required

To properly evaluate EN 16798-1 compliance, rooms need:

1. **Room Type**: office, classroom, hotel_room, etc.
2. **Floor Area**: m²
3. **Volume**: m³ (optional, for ACH calculation)
4. **Occupancy Count**: number of typical occupants
5. **Ventilation Type**: natural, mechanical, mixed_mode (determines if adaptive comfort applies)
6. **Pollution Level**: very_low, low, non_low
7. **Activity Level**: sedentary, light_activity, medium_activity, high_activity
8. **Target Category**: cat_i, cat_ii, cat_iii, cat_iv
9. **Outdoor Temperature Data**: Required for adaptive comfort (daily mean temps)

## Implementation Details

### Programmatic Calculation
All thresholds are calculated by `core.analytics.calculators.en16798_calculator.EN16798StandardCalculator`:

```python
from core.analytics.calculators.en16798_calculator import (
    EN16798StandardCalculator,
    EN16798RoomMetadata,
)
from core.domain.enums.en16798_category import EN16798Category
from core.domain.enums.ventilation import VentilationType

# Create room metadata
room_metadata = EN16798RoomMetadata(
    room_type="office",
    floor_area=25.0,
    volume=75.0,
    occupancy_count=2,
    ventilation_type=VentilationType.NATURAL,
    pollution_level=PollutionLevel.LOW,
)

# Calculate running mean outdoor temperature
daily_temps = [18.5, 17.2, 16.8, 15.5, 14.2, 13.8, 12.5]  # Last 7+ days
t_rm = EN16798StandardCalculator.calculate_running_mean_outdoor_temp(daily_temps)

# Get adaptive temperature thresholds
thresholds = EN16798StandardCalculator.get_temperature_thresholds(
    EN16798Category.CATEGORY_II,
    outdoor_running_mean_temp=t_rm,
    ventilation_type=VentilationType.NATURAL
)
# Returns: {"lower": 21.8, "upper": 27.8, "design": 24.8, "adaptive_model": True}

# Get all thresholds for room
all_thresholds = EN16798StandardCalculator.get_all_thresholds_for_room(
    room_metadata,
    outdoor_running_mean_temp=t_rm
)
```

### Fixed Thresholds (Mechanical Conditioning)

**Category I - Highest Performance:**
- Heating: 21.0-23.0°C (design: 22.0°C)
- Cooling: 23.5-25.5°C (design: 24.5°C)
- CO2: ≤950 ppm (550 ppm above outdoor)
- Humidity: 30-50% RH
- Ventilation: 10 L/(s·person)

**Category II - Normal Performance:**
- Heating: 20.0-24.0°C (design: 22.0°C)
- Cooling: 23.0-26.0°C (design: 24.5°C)
- CO2: ≤1200 ppm (800 ppm above outdoor)
- Humidity: 25-60% RH
- Ventilation: 7 L/(s·person)

**Category III - Moderate Performance:**
- Heating: 19.0-25.0°C (design: 22.0°C)
- Cooling: 22.0-27.0°C (design: 24.5°C)
- CO2: ≤1750 ppm (1350 ppm above outdoor)
- Humidity: 20-70% RH
- Ventilation: 4 L/(s·person)

**Category IV - Outside Standard:**
- Heating: 17.0-27.0°C (design: 22.0°C)
- Cooling: 20.0-29.0°C (design: 24.5°C)
- CO2: ≤1750 ppm (1350 ppm above outdoor)
- Humidity: 15-80% RH
- Ventilation: 4 L/(s·person)

## Configuration Files

**Previous Implementation:** Static YAML files (removed in favor of dynamic calculations)

**Current Implementation:** All thresholds calculated programmatically by `EN16798StandardCalculator`

The calculator provides:
- Dynamic adaptive comfort thresholds for natural/mixed-mode ventilation
- Fixed thresholds for mechanically conditioned buildings
- Automatic fallback when outdoor temperature data is unavailable
- Running mean outdoor temperature calculation
- Ventilation rate calculations based on occupancy and building emissions

## Category Achievement Logic

A room achieves a category if **ALL** tests in that category meet the ≥95% compliance threshold:

1. Room is tested against all 4 categories simultaneously
2. Each category has 4 tests (temp_heating, temp_cooling, co2, humidity)
3. If all Category I tests pass → Category I achieved (highest)
4. If all Category II tests pass → Category II achieved
5. If all Category III tests pass → Category III achieved
6. If all Category IV tests pass → Category IV achieved
7. If none pass → No category achieved

The **highest achieved category** determines the room's overall rating.

## Usage with Different Standards

EN 16798-1 is **independent** from:
- **TAIL**: Rating scheme with different parameters and scoring
- **BR18**: Danish building regulations
- **Danish Guidelines**: Denmark-specific IEQ standards
- **User-Defined**: Custom thresholds

Each standard has its own configuration files and evaluation logic.

## Examples

### Example 1: Mechanically Conditioned Office (Fixed Thresholds)
```python
room_metadata = EN16798RoomMetadata(
    room_type="office",
    floor_area=20.0,  # m²
    volume=60.0,  # m³
    occupancy_count=2,
    ventilation_type=VentilationType.MECHANICAL,
    pollution_level=PollutionLevel.LOW,
    target_category=EN16798Category.CATEGORY_II,
)

# Get fixed thresholds (no outdoor temp needed)
thresholds = EN16798StandardCalculator.get_temperature_thresholds(
    EN16798Category.CATEGORY_II,
    season="heating",
    ventilation_type=VentilationType.MECHANICAL
)
# Returns: {"lower": 20.0, "upper": 24.0, "design": 22.0}

# Calculate ventilation requirements
vent = EN16798StandardCalculator.calculate_required_ventilation_rate(
    room_metadata, EN16798Category.CATEGORY_II
)
# Returns: {
#   "total_ventilation_l_s": 24.0,
#   "occupant_contribution_l_s": 14.0,  # 2 persons × 7 L/s
#   "building_contribution_l_s": 10.0,  # 20 m² × 0.5 L/(s·m²)
#   "air_change_rate_ach": 1.44
# }
```

### Example 2: Naturally Ventilated Office (Adaptive Comfort)
```python
room_metadata = EN16798RoomMetadata(
    room_type="office",
    floor_area=25.0,
    volume=75.0,
    occupancy_count=2,
    ventilation_type=VentilationType.NATURAL,
    pollution_level=PollutionLevel.LOW,
    target_category=EN16798Category.CATEGORY_II,
)

# Calculate running mean outdoor temperature
daily_outdoor_temps = [18.5, 17.2, 16.8, 15.5, 14.2, 13.8, 12.5]
t_rm = EN16798StandardCalculator.calculate_running_mean_outdoor_temp(daily_outdoor_temps)
# Returns: 16.0°C

# Get adaptive thresholds
thresholds = EN16798StandardCalculator.get_temperature_thresholds(
    EN16798Category.CATEGORY_II,
    outdoor_running_mean_temp=t_rm,
    ventilation_type=VentilationType.NATURAL
)
# Returns: {
#   "lower": 21.8,  # T_comf - 3°C
#   "upper": 27.8,  # T_comf + 3°C
#   "design": 24.8,  # T_comf = 0.33 × 16.0 + 18.8
#   "outdoor_running_mean": 16.0,
#   "adaptive_model": True
# }
```

### Example 3: Classroom (Category I Target)
```python
room_metadata = EN16798RoomMetadata(
    room_type="classroom",
    floor_area=60.0,  # m²
    volume=180.0,  # m³
    occupancy_count=25,
    ventilation_type=VentilationType.MECHANICAL,
    pollution_level=PollutionLevel.LOW,
    target_category=EN16798Category.CATEGORY_I,
)

# Calculate ventilation requirements for Category I
vent = EN16798StandardCalculator.calculate_required_ventilation_rate(
    room_metadata, EN16798Category.CATEGORY_I
)
# Returns: {
#   "total_ventilation_l_s": 280.0,
#   "occupant_contribution_l_s": 250.0,  # 25 persons × 10 L/s
#   "building_contribution_l_s": 30.0,   # 60 m² × 0.5 L/(s·m²)
#   "air_change_rate_ach": 5.6
# }

# Get all thresholds
all_thresholds = EN16798StandardCalculator.get_all_thresholds_for_room(room_metadata)
# Returns Category I requirements:
# - Temperature heating: 21.0-23.0°C
# - Temperature cooling: 23.5-25.5°C
# - CO2: ≤950 ppm
# - Humidity: 30-50%
# - Ventilation: 280 L/s
```

## References

- EN 16798-1:2019 - Energy performance of buildings - Ventilation for buildings - Part 1
- CEN/TR 16798-2:2019 - Performance requirements for ventilation and room-conditioning systems
