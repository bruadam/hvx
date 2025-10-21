# Standards Configuration Directory

This directory contains configuration files for various indoor environmental quality (IEQ) standards and rating schemes.

## Current Standards

### TAIL Rating Scheme
- **Directory**: `tail/`
- **Description**: Thermal, Acoustics, Indoor Air Quality, and Lighting rating scheme
- **Status**: Implemented
- **Building Types**: Office, Hotel
- **Parameters**: 12 environmental parameters across 4 categories

## Future Standards (Planned)

### BREEAM
- **Directory**: `breeam/` (planned)
- **Description**: Building Research Establishment Environmental Assessment Method
- **Status**: Not implemented
- **Notes**: Could extend the same hierarchical configuration pattern

### LEED
- **Directory**: `leed/` (planned)  
- **Description**: Leadership in Energy and Environmental Design
- **Status**: Not implemented
- **Notes**: Focus on energy and sustainability metrics

### EN 16798-1
- **Directory**: `en16798-1/` (planned)
- **Description**: Energy performance of buildings - Ventilation for buildings
- **Status**: Not implemented
- **Notes**: European standard for indoor environmental input parameters

### ASHRAE 55
- **Directory**: `ashrae55/` (planned)
- **Description**: Thermal Environmental Conditions for Human Occupancy
- **Status**: Not implemented
- **Notes**: Focus on thermal comfort parameters

## Configuration Pattern

Each standard follows the same hierarchical configuration pattern:

```
standard_name/
├── schema.yaml                     # Default configuration
├── overrides/
│   ├── building_types/
│   │   ├── building1.yaml          # Building-specific overrides
│   │   └── building2.yaml
│   └── room_types/
│       ├── room1.yaml              # Room-specific overrides
│       └── room2.yaml
└── README.md                       # Standard documentation
```

## Adding New Standards

1. Create a new directory under `standards/`
2. Follow the established pattern with:
   - Main schema file with defaults
   - Override structure for building/room types
   - README with standard documentation
3. Update enums to include new parameters/categories
4. Create appropriate loader/validator classes
5. Add tests for the new standard

## Validation

All standards must:
- Use enum-validated parameter names
- Use enum-validated building types
- Use enum-validated room types
- Follow the hierarchical override pattern
- Include proper documentation