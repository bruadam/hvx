# IEQ Analytics Configuration Refactoring Summary

## Overview

The IEQ analytics system has been completely refactored to support **modular, dynamic rule selection** instead of relying on static configuration files. This provides users with flexible, interactive control over which analysis rules to run and how to apply them.

## What Changed

### Before (Old System)
- ❌ Static `tests.yaml` file with all rules hardcoded
- ❌ No way to select specific rules or standards
- ❌ Limited ability to customize filters and periods
- ❌ Required manual YAML editing for configuration changes

### After (New System)
- ✅ Dynamic rule selection from modular config structure
- ✅ Interactive UI for selecting standards and individual rules
- ✅ Flexible filter and period configuration
- ✅ Programmatic API for custom workflows
- ✅ Support for all standards: EN16798-1, BR18, Danish Guidelines

## New Files Created

### 1. [src/core/analytics/ieq/ConfigBuilder.py](../src/core/analytics/ieq/ConfigBuilder.py)
**Purpose**: Builder pattern for creating custom analysis configurations

**Key Features**:
- `IEQConfigBuilder` class with fluent API
- `RuleDefinition`, `FilterDefinition`, `PeriodDefinition` data classes
- Methods for adding standards, individual rules, and applying filters/periods

**Example Usage**:
```python
builder = IEQConfigBuilder()
builder.add_standard("en16798-1")
builder.apply_filter_to_all("opening_hours_no_holidays")
config = builder.build()
```

### 2. [src/cli/ui/components/rule_selector.py](../src/cli/ui/components/rule_selector.py)
**Purpose**: Interactive UI components for rule selection

**Key Features**:
- `RuleSelector` class with step-by-step workflow
- Multi-select for standards and individual rules
- Filter and period configuration UI
- Summary display
- `create_custom_config()` convenience function

### 3. [docs/RULE_SELECTION_GUIDE.md](RULE_SELECTION_GUIDE.md)
**Purpose**: Comprehensive user documentation

**Contents**:
- Quick start guide
- Available standards, filters, and periods
- Interactive mode walkthrough
- Programmatic usage examples
- Best practices

## Modified Files

### 1. [src/core/analytics/config_loader.py](../src/core/analytics/config_loader.py)

**Changes**:
- Fixed `get_ieq_config_base_path()` to use correct path: `src/core/analytics/ieq/config/`
- Marked `get_tests_config_path()` as deprecated (kept for backward compatibility)
- Updated to load from modular config structure

**Before**:
```python
def get_ieq_config_base_path() -> Path:
    # Looked in wrong path: src/core/analysis/ieq/config/
    config_path = src_core / "analysis" / "ieq" / "config"
```

**After**:
```python
def get_ieq_config_base_path() -> Path:
    # Correct path: src/core/analytics/ieq/config/
    config_path = src_core / "ieq" / "config"
```

### 2. [src/core/analytics/hierarchical_analysis_service.py](../src/core/analytics/hierarchical_analysis_service.py)

**Changes**:
- Added `config_dict` parameter to `__init__()`
- Now accepts either config dictionary or file path
- Config dictionary takes precedence over file path

**Before**:
```python
def __init__(self, config_path: Optional[Path] = None):
    self.config_path = config_path or get_tests_config_path()
    self.config = self._load_config()
```

**After**:
```python
def __init__(
    self,
    config_path: Optional[Path] = None,
    config_dict: Optional[Dict[str, Any]] = None
):
    if config_dict is not None:
        self.config = config_dict
    elif config_path is not None:
        self.config = self._load_config()
    else:
        # Default: load from generated config
        self.config_path = get_tests_config_path()
        self.config = self._load_config()
```

### 3. [src/cli/ui/workflows/interactive_workflow.py](../src/cli/ui/workflows/interactive_workflow.py)

**Major Changes**:

1. **Removed hardcoded config path initialization**
   - Before: Always loaded `config/tests.yaml` at startup
   - After: Only loads config when needed

2. **Added interactive configuration selection**
   ```python
   # New configuration options in _run_analysis()
   console.print("[bold]Configuration Options:[/bold]")
   console.print("  1. Interactive rule selection (recommended)")
   console.print("  2. Use all standards with defaults")
   console.print("  3. Load from existing config file")
   ```

3. **Auto-mode uses all standards**
   ```python
   if self.auto_mode:
       from src.cli.ui.components.rule_selector import create_custom_config
       analysis_config, config_summary = create_custom_config(auto_mode=True)
   ```

4. **Service initialization with config dict**
   ```python
   if analysis_config:
       service = HierarchicalAnalysisService(config_dict=analysis_config)
   else:
       service = HierarchicalAnalysisService(config_path=self.config_path)
   ```

5. **Fixed auto-mode prompts**
   - Added checks to skip interactive prompts in auto mode
   - Proper handling of analysis exploration and report generation

## Configuration Structure

### Modular Config Location
```
src/core/analytics/ieq/config/
├── standards/
│   ├── en16798-1/
│   │   ├── cat_i_temp_heating_season.yaml
│   │   ├── cat_i_temp_non_heating_season.yaml
│   │   ├── cat_i_co2.yaml
│   │   └── ... (12 files total)
│   ├── br18/
│   │   ├── office_temp_above_26_max_100h.yaml
│   │   └── ... (4 files total)
│   └── danish-guidelines/
│       ├── temp_comfort_danish_schools.yaml
│       └── co2_danish_guidelines.yaml
├── filters/
│   ├── opening_hours.yaml
│   ├── opening_hours_no_holidays.yaml
│   ├── all_hours.yaml
│   └── ... (7 files total)
├── periods/
│   ├── all_year.yaml
│   ├── heating_season.yaml
│   ├── summer.yaml
│   └── ... (7 files total)
└── holidays/
    └── denmark.yaml
```

### Individual Rule File Format
```yaml
# cat_i_temp_heating_season.yaml
description: "Temperature Category I compliance during heating season (opening hours)"
feature: temperature
filter: opening_hours
period: heating_season
mode: bidirectional
limits:
  lower: 21
  upper: 23
category: EN16798-1
```

## Available Standards

### EN16798-1 (12 rules)
European standard for indoor environmental parameters
- Temperature: Categories I, II, III for heating and non-heating seasons
- CO2: Categories I, II, III
- Humidity: Categories I, II, III

### BR18 (4 rules)
Danish Building Regulations 2018
- Office overheating limits (26°C, 27°C)
- Residential overheating limits (27°C, 28°C)

### Danish Guidelines (2 rules)
Danish guidelines for indoor climate
- Temperature comfort for schools
- CO2 levels

## Available Filters (7 total)

- `opening_hours` - Business hours (8-15), weekdays
- `opening_hours_no_holidays` - Opening hours excluding school holidays
- `non_opening_hours` - Outside business hours
- `morning_no_holidays` - Morning (8-11), weekdays, no holidays
- `afternoon_no_holidays` - Afternoon (12-15), weekdays, no holidays
- `evening_no_holidays` - Evening (16-21), weekdays, no holidays
- `all_hours` - All time periods (24/7)

## Available Periods (7 total)

- `all_year` - Entire year
- `heating_season` - Heating season (Oct-Apr)
- `non_heating_season` - Non-heating season (May-Sep)
- `winter` - Winter months (Dec-Feb)
- `spring` - Spring months (Mar-May)
- `summer` - Summer months (Jun-Aug)
- `autumn` - Autumn months (Sep-Nov)

## Usage Examples

### Command Line

#### Auto Mode (All Standards)
```bash
hvx ieq start
# Uses all 18 rules from all standards
```

#### Interactive Mode
```bash
hvx ieq start
# Then select option 1 for interactive rule selection
# Follow the prompts to choose standards, filters, and periods
```

### Programmatic API

#### Example 1: All EN16798-1 Rules
```python
from src.core.analytics.ieq.ConfigBuilder import IEQConfigBuilder
from src.core.analytics.hierarchical_analysis_service import HierarchicalAnalysisService

builder = IEQConfigBuilder()
builder.add_standard("en16798-1")
config = builder.build()

service = HierarchicalAnalysisService(config_dict=config)
results = service.analyze_dataset(dataset, output_dir=Path("output"))
```

#### Example 2: Specific Rules with Custom Filter
```python
builder = IEQConfigBuilder()
builder.add_rule("cat_i_temp_heating_season", "en16798-1")
builder.add_rule("cat_ii_temp_heating_season", "en16798-1")
builder.apply_filter_to_all("opening_hours_no_holidays")
config = builder.build()

service = HierarchicalAnalysisService(config_dict=config)
```

#### Example 3: Mix Standards with Custom Period
```python
builder = IEQConfigBuilder()
builder.add_standard("br18")  # All BR18 overheating rules
builder.add_rule("cat_i_co2", "en16798-1")  # Add CO2 rule
builder.apply_period_to_all("summer")  # Summer overheating focus
config = builder.build()

service = HierarchicalAnalysisService(config_dict=config)
```

## Benefits

### For Users
1. **Flexibility** - Choose exactly which rules to run
2. **Ease of Use** - Interactive UI guides the selection process
3. **Time Saving** - Run only relevant rules instead of all 18
4. **Customization** - Apply custom filters and periods easily

### For Developers
1. **Clean API** - Builder pattern for programmatic access
2. **Modular** - Easy to add new standards, rules, filters, periods
3. **Testable** - Individual components can be tested independently
4. **Maintainable** - Configuration in separate YAML files

## Backward Compatibility

The system maintains backward compatibility:

1. **File-based config still works**
   ```python
   service = HierarchicalAnalysisService(config_path=Path("config.yaml"))
   ```

2. **`get_tests_config_path()` still exists**
   - Marked as deprecated
   - Generates config with all standards
   - Used as fallback for legacy code

3. **Existing workflows continue to function**
   - Auto mode uses all standards (same as before, but now explicit)
   - Manual config file loading still supported

## Migration Guide

### If you were using file-based config:

**Before**:
```python
service = HierarchicalAnalysisService(config_path=Path("my_config.yaml"))
```

**After (recommended)**:
```python
builder = IEQConfigBuilder()
builder.add_standard("en16798-1")
# ... configure as needed
config = builder.build()

service = HierarchicalAnalysisService(config_dict=config)
```

**Or keep using file-based approach** (still supported):
```python
# No changes needed - still works!
service = HierarchicalAnalysisService(config_path=Path("my_config.yaml"))
```

## Testing

### Auto Mode Test
```bash
hvx ieq start
# Should see: "Selected Rules: 18"
#             "  en16798-1: 12 rules"
#             "  br18: 4 rules"
#             "  danish-guidelines: 2 rules"
```

### Programmatic Test
See [test_rule_selection.py](../test_rule_selection.py) for comprehensive examples.

## Future Enhancements

Potential future improvements:
1. Save custom configurations as named profiles
2. Rule recommendation based on building type
3. Conflict detection between rules
4. Performance optimization for large rule sets
5. Rule dependency management
6. Custom rule creation UI

## Summary

This refactoring provides a **modern, flexible, and user-friendly** approach to IEQ analysis configuration while maintaining full backward compatibility. The modular structure makes it easy to extend with new standards, rules, filters, and periods without modifying core code.

**Key Achievement**: Transformed a static, file-based configuration system into a dynamic, interactive, and programmable rule selection framework.
