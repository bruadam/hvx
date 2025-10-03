# IEQ Analysis Rule Selection Guide

## Overview

The IEQ analytics system now supports flexible, interactive rule selection. Instead of running all tests from a static configuration file, you can now:

- **Select specific standards** (EN16798-1, BR18, Danish Guidelines)
- **Choose individual rules** from any standard
- **Apply custom filters** (opening hours, with/without holidays, time periods)
- **Configure periods** (seasons, heating/non-heating, all year)

## Quick Start

### Auto Mode (All Standards)

```bash
hvx ieq start
```

This runs all available rules from all standards with default settings.

### Interactive Mode

When you run `hvx ieq start` interactively, you'll see configuration options:

```
Configuration Options:
  1. Interactive rule selection (recommended)
  2. Use all standards with defaults
  3. Load from existing config file
```

## Configuration Options Explained

### Option 1: Interactive Rule Selection

This is the most flexible option, allowing you to:

1. **Select Standards or Individual Rules**
   - Choose entire standards (e.g., all EN16798-1 rules)
   - Select specific rules across any standards
   - Mix both approaches

2. **Configure Filters**
   - Apply one filter to ALL rules
   - Keep each rule's default filter
   - Skip filter configuration

3. **Configure Periods**
   - Apply one period to ALL rules
   - Keep each rule's default period
   - Skip period configuration

### Option 2: Use All Standards

Quickly runs all available rules with their default filters and periods.

### Option 3: Load from Config File

Load a previously saved configuration from a YAML file.

## Available Standards

### EN16798-1
European standard for indoor environmental input parameters. Contains rules for:
- Temperature (Categories I, II, III for heating and non-heating seasons)
- CO2 levels (Categories I, II, III)
- Humidity (Categories I, II, III)

**Rules:** 12 total
- `cat_i_temp_heating_season` - Category I temperature during heating season
- `cat_i_temp_non_heating_season` - Category I temperature during non-heating season
- `cat_ii_temp_heating_season` - Category II temperature during heating season
- `cat_ii_temp_non_heating_season` - Category II temperature during non-heating season
- `cat_iii_temp_heating_season` - Category III temperature during heating season
- `cat_iii_temp_non_heating_season` - Category III temperature during non-heating season
- `cat_i_co2` - Category I CO2 levels
- `cat_ii_co2` - Category II CO2 levels
- `cat_iii_co2` - Category III CO2 levels
- `cat_i_humidity` - Category I humidity
- `cat_ii_humidity` - Category II humidity
- `cat_iii_humidity` - Category III humidity

### BR18
Danish Building Regulations 2018. Contains overheating rules for:
- Office spaces (26°C and 27°C limits)
- Residential spaces (27°C and 28°C limits)

**Rules:** 4 total
- `office_temp_above_26_max_100h` - Office temperature above 26°C (max 100 hours)
- `office_temp_above_27_max_25h` - Office temperature above 27°C (max 25 hours)
- `residential_temp_above_27_max_100h` - Residential temperature above 27°C (max 100 hours)
- `residential_temp_above_28_max_25h` - Residential temperature above 28°C (max 25 hours)

### Danish Guidelines
Danish guidelines for indoor climate in schools and other buildings.

**Rules:** 2 total
- `temp_comfort_danish_schools` - Temperature comfort for Danish schools
- `co2_danish_guidelines` - CO2 levels according to Danish guidelines

## Available Filters

Filters define **when** to apply the rules (time periods and exclusions).

- **`opening_hours`** - Standard business hours (8-15), weekdays
- **`opening_hours_no_holidays`** - Opening hours excluding all school holidays
- **`non_opening_hours`** - Outside business hours
- **`morning_no_holidays`** - Morning period (8-11), weekdays, no holidays
- **`afternoon_no_holidays`** - Afternoon period (12-15), weekdays, no holidays
- **`evening_no_holidays`** - Evening period (16-21), weekdays, no holidays
- **`all_hours`** - All time periods (24/7)

### Filter Use Cases

- **`opening_hours`** - Standard office/school compliance
- **`opening_hours_no_holidays`** - More accurate compliance (excludes vacations)
- **`all_hours`** - Residential or 24/7 facilities
- **Time-specific filters** - Detailed analysis of specific periods

## Available Periods

Periods define **which calendar period** to analyze.

- **`all_year`** - Entire year
- **`heating_season`** - Heating season (typically Oct-Apr in Northern Europe)
- **`non_heating_season`** - Non-heating season (May-Sep)
- **`winter`** - Winter months (Dec-Feb)
- **`spring`** - Spring months (Mar-May)
- **`summer`** - Summer months (Jun-Aug)
- **`autumn`** - Autumn months (Sep-Nov)

### Period Use Cases

- **`heating_season` / `non_heating_season`** - Different temperature limits
- **`summer`** - Overheating analysis
- **`winter`** - Undercooling analysis
- **`all_year`** - General compliance

## Programmatic Usage

### Example 1: Select All EN16798-1 Rules

```python
from src.core.analytics.ieq.ConfigBuilder import IEQConfigBuilder

builder = IEQConfigBuilder()
builder.add_standard("en16798-1")
config = builder.build()

# Use with HierarchicalAnalysisService
from src.core.analytics.hierarchical_analysis_service import HierarchicalAnalysisService

service = HierarchicalAnalysisService(config_dict=config)
results = service.analyze_dataset(dataset, output_dir=Path("output"))
```

### Example 2: Custom Rules with Filter Override

```python
builder = IEQConfigBuilder()

# Add specific temperature rules
builder.add_rule("cat_i_temp_heating_season", "en16798-1")
builder.add_rule("cat_ii_temp_heating_season", "en16798-1")

# Apply custom filter to all rules
builder.apply_filter_to_all("opening_hours_no_holidays")

config = builder.build()
```

### Example 3: Mix Standards with Custom Period

```python
builder = IEQConfigBuilder()

# Add all BR18 rules
builder.add_standard("br18")

# Add specific CO2 rule from EN16798-1
builder.add_rule("cat_i_co2", "en16798-1")

# Apply summer period to all (for overheating analysis)
builder.apply_period_to_all("summer")

config = builder.build()
```

### Example 4: Individual Rule Customization

```python
builder = IEQConfigBuilder()

builder.add_rule("cat_i_temp_heating_season", "en16798-1")
builder.add_rule("cat_i_co2", "en16798-1")

# Apply different filters to different rules
builder.apply_filter_to_rule("cat_i_temp_heating_season", "opening_hours")
builder.apply_filter_to_rule("cat_i_co2", "all_hours")

# Apply different periods
builder.apply_period_to_rule("cat_i_temp_heating_season", "winter")

config = builder.build()
```

## Saving and Loading Configurations

### Save Configuration to File

```python
builder = IEQConfigBuilder()
builder.add_standard("en16798-1")
builder.apply_filter_to_all("opening_hours_no_holidays")

# Save for later use
builder.save_to_file(Path("my_config.yaml"))
```

### Load Configuration from File

```python
from src.core.analytics.hierarchical_analysis_service import HierarchicalAnalysisService

service = HierarchicalAnalysisService(config_path=Path("my_config.yaml"))
```

## Best Practices

### 1. Start with Standards
For most use cases, selecting an entire standard is the easiest approach:
```python
builder.add_standard("en16798-1")  # All European standard rules
```

### 2. Use Appropriate Filters
- **Schools/Offices**: `opening_hours_no_holidays` (most accurate)
- **Residential**: `all_hours`
- **Detailed Analysis**: Time-specific filters (morning, afternoon, evening)

### 3. Match Periods to Analysis Goals
- **General Compliance**: Use rule's default period
- **Overheating Focus**: `summer` or `non_heating_season`
- **Undercooling Focus**: `winter` or `heating_season`

### 4. Combine Standards for Comprehensive Analysis
```python
builder.add_standard("en16798-1")  # European standard
builder.add_standard("br18")       # Danish regulations
builder.add_standard("danish-guidelines")  # Local guidelines
```

## Configuration File Format

The generated configuration files follow this structure:

```yaml
analytics:
  cat_i_temp_heating_season:
    description: "Temperature Category I compliance during heating season"
    feature: temperature
    filter: opening_hours
    period: heating_season
    mode: bidirectional
    limits:
      lower: 21
      upper: 23
    category: EN16798-1

filters:
  opening_hours:
    description: "Opening hours (8-15), weekdays"
    # ... filter configuration

periods:
  heating_season:
    description: "Heating season"
    # ... period configuration

holidays:
  # Holiday definitions
```

## Troubleshooting

### "No rules selected"
Make sure to add at least one standard or rule before building the configuration.

### "Filter not found"
Check available filters using:
```python
builder.get_available_filters()
```

### "Period not found"
Check available periods using:
```python
builder.get_available_periods()
```

### View Available Options
```python
builder = IEQConfigBuilder()

# Show all standards
print("Standards:", builder.get_available_standards())

# Show rules for a specific standard
rules = builder.get_rules_for_standard("en16798-1")
for rule in rules:
    print(f"- {rule.name}: {rule.description}")

# Show all filters
filters = builder.get_available_filters()
for f in filters:
    print(f"- {f.name}: {f.description}")

# Show all periods
periods = builder.get_available_periods()
for p in periods:
    print(f"- {p.name}: {p.description}")
```

## Summary

The new modular configuration system provides:

✅ **Flexibility** - Select exactly the rules you need
✅ **Interactivity** - Easy-to-use CLI interface
✅ **Programmatic** - Full API for custom workflows
✅ **Standards-based** - Built-in support for major standards
✅ **Customizable** - Override filters and periods as needed

For most users, the interactive mode (`hvx ieq start` → Option 1) provides the best balance of flexibility and ease of use.
