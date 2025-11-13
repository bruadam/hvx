# TAIL Rating Scheme Standard

## Overview
The TAIL (Thermal, Acoustics, Indoor Air Quality, Lighting) Rating Scheme is a comprehensive method for evaluating indoor environmental quality in buildings.

## Standard Information
- **Name**: TAIL Rating Scheme
- **Version**: 1.0
- **Based on**: ALDREN Project research and European standards
- **Reference**: [TAIL Rating Scheme Publication](https://www.sciencedirect.com/science/article/pii/S0378778821003133)
- **Applicable Building Types**: Office, Hotel (extensible to others)
- **Assessment Categories**: 4 main categories (Thermal, Acoustics, Indoor Air Quality, Lighting)

## Configuration Files Structure

```
config/standards/tail/
├── tail_schema.yaml                    # Main TAIL configuration with defaults
├── overrides/
│   ├── building_types/
│   │   ├── office.yaml                 # Office building specific overrides
│   │   └── hotel.yaml                  # Hotel building specific overrides
│   └── room_types/
│       ├── small_office.yaml           # Small office room specific overrides
│       ├── open_office.yaml            # Open office room specific overrides
│       └── hotel_room.yaml             # Hotel room specific overrides
└── README.md                           # This file
```

## Configuration Priority
The system uses hierarchical configuration with the following priority:
1. **Room Type** (Highest priority) - Specific to room function
2. **Building Type** (Medium priority) - Specific to building use
3. **Default** (Lowest priority) - Base TAIL standard values

## Parameters Covered

### Thermal (T)
- **Temperature**: Seasonal frequency-based analysis with heating/non-heating season thresholds

### Acoustics (A)  
- **Noise**: 5th percentile analysis with room-type specific thresholds

### Indoor Air Quality (I)
- **CO2**: 95th percentile analysis based on EN16798-1
- **Relative Humidity**: Frequency-based analysis
- **PM2.5**: Direct thresholds based on WHO guidelines
- **Formaldehyde**: Direct thresholds based on WHO guidelines
- **Benzene**: Direct thresholds based on WHO guidelines
- **Radon**: Direct thresholds based on WHO guidelines
- **Ventilation**: Occupancy and floor area based calculations
- **Mold**: Categorical visual inspection assessment

### Lighting (L)
- **Illuminance**: Frequency-based analysis (different criteria for office vs hotel)
- **Daylight Factor**: Direct value assessment from simulation

## Rating Categories
Each parameter is categorized into one of four levels:
- **Green (I)**: Excellent quality
- **Yellow (II)**: Good quality
- **Orange (III)**: Acceptable quality  
- **Red (IV)**: Poor quality

The overall TAIL rating takes the worst-performing category (conservative approach).

## Usage Notes
- Building types must match the `BuildingType` enum values
- Room types must match the `RoomType` enum values
- Parameter names must match the `ParameterType` enum values
- All configurations are validated against these enums to prevent errors

## Extension Guidelines
To add support for new building or room types:
1. Add the new type to the appropriate enum
2. Create an override file in the corresponding directory
3. Define only the parameters that differ from defaults
4. Test the configuration using the validation system