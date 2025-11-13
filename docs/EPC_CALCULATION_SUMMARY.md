# EPC (Energy Performance Certificate) Calculation System

## Overview

The EPC calculation system provides country-specific energy performance ratings based on official European DataWarehouse GmbH, 2024 data. It supports **18 European countries** with accurate threshold values and energy conversion factors.

## Features

### 1. **Country-Specific Thresholds**
Official EPC rating thresholds (A+ to G) for:
- Austria, Belgium, Bulgaria, Croatia, Czech Republic
- Denmark, Finland, France, Germany, Greece
- Hungary, Ireland, Italy, Luxembourg, Netherlands
- Norway, Poland, Portugal, Romania, Slovakia, Spain

### 2. **Energy Type Support**
Different countries measure energy differently:
- **Primary Energy**: Most countries (Italy, Spain, Netherlands, etc.)
- **Final Energy**: Denmark, Germany
- **Energy Delivered**: Norway
- **Primary Energy + CO2**: France

### 3. **Primary Energy Calculation**
Calculate primary energy from final energy consumption with country-specific conversion factors:
```python
primary_energy = EPCRating.calculate_primary_energy(
    heating_kwh=12000,
    cooling_kwh=3000,
    electricity_kwh=6000,
    hot_water_kwh=3000,
    country=Country.GERMANY,
    floor_area_m2=200,
    renewable_energy_kwh=1000
)
```

### 4. **Rating Calculation**
Automatically determine EPC rating from energy consumption:
```python
rating = EPCRating.calculate_from_energy_consumption(
    energy_kwh_per_m2=65,
    country=Country.SPAIN
)
# Returns: EPCRating.C
```

## API Reference

### Main Methods

#### `EPCRating.get_country_thresholds(country: Country)`
Returns rating thresholds as (min, max) tuples for a country.

**Example:**
```python
thresholds = EPCRating.get_country_thresholds(Country.AUSTRIA)
# Returns: {
#     "A+": (0, 15),
#     "A": (15, 30),
#     "B": (30, 50),
#     ...
# }
```

#### `EPCRating.calculate_from_energy_consumption(energy_kwh_per_m2, country)`
Calculate EPC rating from energy consumption.

**Example:**
```python
rating = EPCRating.calculate_from_energy_consumption(
    energy_kwh_per_m2=65,
    country=Country.SPAIN
)
```

#### `EPCRating.calculate_primary_energy(...)`
Calculate primary energy with country-specific conversion factors.

**Parameters:**
- `heating_kwh`: Annual heating energy
- `cooling_kwh`: Annual cooling energy
- `electricity_kwh`: Annual electricity
- `hot_water_kwh`: Annual hot water energy
- `country`: Country for conversion factors
- `floor_area_m2`: Building floor area
- `renewable_energy_kwh`: Renewable generation (optional)

#### `EPCRating.get_energy_type(country)`
Get the type of energy measurement used in a country.

**Returns:** `"primary"`, `"final"`, `"delivered"`, or `"primary+co2"`

#### `EPCRating.get_rating_info(country)`
Get information about EPC methodology for a country.

### Properties

#### `rating.description`
Human-readable description of the rating.

#### `rating.numeric_score`
Numeric score from 1 (G) to 8 (A+).

#### `rating.get_threshold_range(country)`
Get min/max energy consumption range for this rating in a country.

## Usage Examples

### Example 1: Direct Rating Lookup
```python
from core.domain.enums.epc import EPCRating
from core.domain.enums.countries import Country

# Building consumes 65 kWh/m²/year in Spain
rating = EPCRating.calculate_from_energy_consumption(65, Country.SPAIN)

print(f"Rating: {rating.value}")  # C
print(f"Description: {rating.description}")  # Average energy performance
print(f"Score: {rating.numeric_score}/8")  # 5/8
```

### Example 2: Calculate Primary Energy
```python
# Calculate primary energy for a building in Germany
primary = EPCRating.calculate_primary_energy(
    heating_kwh=18000,
    cooling_kwh=4000,
    electricity_kwh=7000,
    hot_water_kwh=4000,
    country=Country.GERMANY,
    floor_area_m2=180,
    renewable_energy_kwh=0
)

rating = EPCRating.calculate_from_energy_consumption(primary, Country.GERMANY)
print(f"Primary Energy: {primary:.1f} kWh/m²/year")
print(f"Rating: {rating.value}")
```

### Example 3: Compare Across Countries
```python
# Same building in different countries
building_data = {
    "heating_kwh": 12000,
    "cooling_kwh": 3000,
    "electricity_kwh": 6000,
    "hot_water_kwh": 3000,
    "floor_area_m2": 200,
}

for country in [Country.DENMARK, Country.GERMANY, Country.FRANCE]:
    primary = EPCRating.calculate_primary_energy(**building_data, country=country)
    rating = EPCRating.calculate_from_energy_consumption(primary, country)
    print(f"{country.value}: {rating.value} ({primary:.1f} kWh/m²/year)")
```

### Example 4: Energy Improvement Analysis
```python
# Before and after renovation
scenarios = {
    "Before": {"heating_kwh": 18000, ...},
    "After": {"heating_kwh": 8000, ...},
}

for name, data in scenarios.items():
    primary = EPCRating.calculate_primary_energy(**data, country=Country.GERMANY)
    rating = EPCRating.calculate_from_energy_consumption(primary, Country.GERMANY)
    print(f"{name}: {rating.value}")
```

## Energy Conversion Factors

### Electricity Factors (Final → Primary)
Higher values indicate less efficient grids:
- **Poland**: 3.0 (coal-heavy)
- **Czech Republic, Portugal, Bulgaria**: 2.5
- **France**: 2.3 (nuclear-heavy)
- **Denmark, Spain, Austria**: 1.9-2.0
- **Germany, Italy, Belgium**: 1.8-2.0
- **Sweden, Finland**: 1.6-1.7 (renewable-heavy)
- **Norway**: 1.5 (hydroelectric)

### Heating Factors
- **Most countries**: 1.0-1.1 (efficient district heating/natural gas)
- **Eastern Europe** (Poland, Czech Rep.): 1.2 (less efficient systems)

## Data Source

**European DataWarehouse GmbH, 2024**

The information is based on official European EPBD (Energy Performance of Buildings Directive) country implementations. Thresholds are extracted from official national regulations and documentation.

### Disclaimer
© European DataWarehouse GmbH, 2024

The information is published "as is" without any representation or warranty. Please refer to official national EPC authorities for the most current regulations.

## Demo

Run the comprehensive demo to see all features:
```bash
python examples/demo_epc_calculation.py
```

This demonstrates:
1. Direct rating calculation
2. Primary energy conversion
3. Country threshold comparison
4. Cross-country analysis
5. Energy improvement scenarios

## Integration with Building Model

The `Building` model now supports EPC ratings:

```python
from core.domain.models.building import Building
from core.domain.enums.epc import EPCRating
from core.domain.enums.countries import Country

building = Building(
    id="building-123",
    name="Office Building",
    epc_rating=EPCRating.B,
    country="Germany",
    total_area=1000
)

# Calculate actual rating from energy data
primary_energy = EPCRating.calculate_primary_energy(...)
calculated_rating = EPCRating.calculate_from_energy_consumption(
    primary_energy,
    Country.GERMANY
)
building.epc_rating = calculated_rating
```

## Files Modified/Created

### Created:
- `core/domain/enums/epc.py` - Main EPC rating implementation
- `examples/demo_epc_calculation.py` - Comprehensive demo
- `docs/EPC_CALCULATION_SUMMARY.md` - This documentation

### Modified:
- `core/domain/enums/countries.py` - Added Norway
- `core/domain/models/building.py` - Added EPCRating import

## Future Enhancements

Potential improvements:
1. Add building-type specific thresholds (residential vs. non-residential)
2. Support for regional variations (e.g., Belgium's Flanders vs. Wallonia)
3. Time-series tracking of rating improvements
4. CO2 emissions calculation for French dual-metric system
5. Integration with actual energy consumption data from sensors
