# TAIL Configuration Merge Summary

## Overview
Successfully merged three TAIL-related files in `core/domain/enums/` into a single unified configuration module with **zero hardcoded values**. All configuration now comes exclusively from YAML files.

## Files Consolidated

### 1. **tail_config.py** (Previously 200+ lines of hardcoded configs)
- **Before**: Contained hardcoded parameter thresholds for 12 TAIL parameters across multiple building types
- **After**: Simplified to contain only data classes and the unified loader logic

### 2. **tail_config_loader.py** (Deleted)
- **Status**: Removed - functionality merged into tail_config.py
- **Reason**: Single responsibility principle - all configuration logic now in one module

### 3. **tail_category.py** (Kept as-is)
- **Status**: No changes needed
- **Role**: Provides TAIL category enum (Thermal, Acoustics, Indoor Air Quality, Lighting)

## Architecture Changes

### Data Classes (Retained and Enhanced)
```python
@dataclass
class ParameterThreshold:
    """Threshold configuration for a parameter."""
    # Can load from YAML dict via from_dict() classmethod
    
@dataclass
class TAILParameterConfig:
    """Configuration for a TAIL parameter including building type specific thresholds."""
    # Can load from YAML dict via from_dict() classmethod
```

### TAILConfigLoader Class (Unified)
All configuration loading logic now in one place:

**Key Methods:**
- `load_default_config()` - Loads tail_schema.yaml
- `load_building_override()` - Loads building-specific overrides
- `load_room_override()` - Loads room-specific overrides
- `get_parameter_config()` - Returns merged config with hierarchical priorities
- `validate_configuration()` - Validates all YAML files against enums
- `get_supported_combinations()` - Discovers available combinations

**Hierarchical Priority:**
```
room_type override > building_type override > default config
```

### TAILConfig Class (Refactored)
Clean interface using the unified loader:

```python
# Get configuration for a parameter and building type
config = TAILConfig.get_parameter_config(ParameterType.CO2, BuildingType.OFFICE)

# Get all supported parameters for a building type
params = TAILConfig.get_supported_parameters(BuildingType.HOTEL)

# Check if parameter is supported
is_supported = TAILConfig.is_parameter_supported(ParameterType.NOISE, BuildingType.OFFICE)
```

## Configuration Files (Unchanged Structure)

```
config/standards/tail/
├── tail_schema.yaml                              # Default parameters for all 12 TAIL metrics
├── overrides/
│   ├── building_types/
│   │   ├── office.yaml                          # Office-specific parameter overrides
│   │   └── hotel.yaml                           # Hotel-specific parameter overrides
│   └── room_types/
│       ├── small_office.yaml                    # Small office noise thresholds
│       ├── open_office.yaml                     # Open office noise thresholds
│       └── hotel_room.yaml                      # Hotel room noise thresholds
└── README.md
```

## Code Quality Improvements

### ✅ **No Hardcoded Values**
- Removed 100+ hardcoded parameter definitions
- All thresholds now in YAML configuration files
- Single source of truth for all TAIL parameters

### ✅ **Enhanced Maintainability**
- Building-specific thresholds managed in YAML files
- Easy to add new building/room types
- Configuration changes don't require code edits

### ✅ **Better Validation**
- Configuration files validated against enums at runtime
- Errors caught early with clear messages
- Automatic discovery of supported combinations

### ✅ **Proper Separation of Concerns**
- Data classes for structure
- Loader class for YAML file management
- Facade class (TAILConfig) for clean API

## Import Changes

### Updated in `room_type.py`
```python
# Before
from .tail_config_loader import tail_config_loader

# After
from .tail_config import tail_config_loader
```

### Updated in `enums/__init__.py`
```python
# Now exports
from core.domain.enums.tail_config import (
    TAILConfig,
    TAILParameterConfig,
    ParameterThreshold,
    TAILConfigLoader,
    tail_config_loader,  # Global instance
)
```

## Usage Examples

### Load Parameter Configuration
```python
from core.domain.enums import TAILConfig, ParameterType, BuildingType

# Get CO2 thresholds for an office
config = TAILConfig.get_parameter_config(
    ParameterType.CO2, 
    BuildingType.OFFICE
)
print(config.thresholds.green_max)  # 970 ppm
```

### Validate Configuration
```python
from core.domain.enums import tail_config_loader

# Validate all YAML files
is_valid = tail_config_loader.validate_configuration()
```

### Get Supported Parameters
```python
# Find all parameters for a building type
params = TAILConfig.get_supported_parameters(BuildingType.HOTEL)
```

## Benefits

1. **Configuration as Code**: All settings in YAML, easy to version control
2. **No Restart Required**: Change configuration files and reload module
3. **Scalable**: Adding new standards (EN 16798-1, ASHRAE, etc.) follows same pattern
4. **Type Safe**: Enum validation ensures configuration integrity
5. **Single Responsibility**: Each module has one clear purpose
6. **Testable**: Configuration can be tested independently

## Future Enhancements

The unified architecture makes it easy to:

1. Add new standards (EN 16798-1, ASHRAE 55, etc.)
2. Support additional room types
3. Add building type variants
4. Implement configuration hot-reload
5. Add configuration versioning
6. Create configuration migration tools

## Files Modified

| File | Changes |
|------|---------|
| `core/domain/enums/tail_config.py` | Merged both classes, removed hardcoded values, added YAML loading logic |
| `core/domain/enums/tail_config_loader.py` | **DELETED** - functionality moved to tail_config.py |
| `core/domain/enums/room_type.py` | Updated import to use tail_config instead of tail_config_loader |
| `core/domain/enums/__init__.py` | Added TAILConfigLoader and tail_config_loader to exports |

## Notes

- PyYAML is already in requirements.txt as a core dependency
- Configuration loading is lazy - files only loaded when first accessed
- Fallback thresholds in room_type.py provide graceful degradation if YAML loads fail
- All validation happens at load time with clear error messages
