# Test Management CLI Commands

The `hvx tests` command group provides comprehensive test configuration management for building analytics. This allows you to create, edit, and organize custom test configurations for different analysis scenarios.

## Overview

Tests define the criteria for evaluating building performance metrics (temperature, CO2, humidity, etc.) against specific thresholds or ranges. The test management system allows you to:

- **Create custom tests** with interactive prompts
- **Edit existing tests** and save them with new names
- **Organize tests into sets** for specific analysis scenarios
- **Manage filters** for time-based data filtering
- **Export test sets** as standalone configuration files

## Test Management Commands

### List All Tests

```bash
hvx tests list
```

List tests with filtering:

```bash
# Filter by feature
hvx tests list --feature temperature

# Filter by period
hvx tests list --period summer

# Filter by filter name
hvx tests list --filter opening_hours_no_holidays

# Combined filters
hvx tests list --feature co2 --period winter
```

### Show Test Details

```bash
hvx tests show temp_below_20_winter_opening
```

### Create New Test

Create a test interactively:

```bash
hvx tests create
```

Create a test from an existing template:

```bash
hvx tests create --from-test temp_below_20_winter_opening
```

The interactive prompt will guide you through:
1. Test name
2. Description
3. Feature (temperature, co2, humidity, combined)
4. Period (all_year, winter, summer, spring, autumn, etc.)
5. Filter (opening_hours, morning_no_holidays, etc.)
6. Mode (unidirectional_ascending, unidirectional_descending, bidirectional)
7. Threshold values (single limit or upper/lower limits)

**Example workflow:**
```
$ hvx tests create --from-test temp_below_20_winter_opening

Test name: temp_below_18_custom
Description: Temperature below 18°C during custom hours
Feature: 1. temperature
Period: 2. winter
Filter: 3. custom_hours
Mode: 2. unidirectional_descending
Threshold value: 18

✓ Test 'temp_below_18_custom' created successfully!
```

### Edit Existing Test

Edit a test in place:

```bash
hvx tests edit temp_below_20_winter_opening
```

Edit and save with a new name:

```bash
hvx tests edit temp_below_20_winter_opening --save-as temp_below_18_custom
```

The editor will:
- Show current values with indicators
- Allow you to press Enter to keep current values
- Modify only the fields you want to change

### Delete Test

```bash
hvx tests delete temp_custom_test

# Skip confirmation
hvx tests delete temp_custom_test --yes
```

## Filter Management

Filters define time-based criteria for when data should be included in analysis.

### List Filters

```bash
hvx tests filters
```

### Create Custom Filter

```bash
hvx tests filter-create
```

Example workflow:
```
$ hvx tests filter-create

Filter name: morning_extended
Description: Extended morning hours including early arrival
Define hours:
  1. Specific range (e.g., 8-15)
  2. Custom list (e.g., 8,9,10,14,15)
  3. All hours (0-23)
Select option: 1
Start hour (0-23): 7
End hour (0-23): 12
Weekdays only?: Yes
Exclude public holidays?: Yes
Exclude custom holidays (school vacations)?: Yes

✓ Filter 'morning_extended' created successfully!
```

## Test Set Management

Test sets allow you to group tests for specific analysis scenarios.

### List Test Sets

```bash
hvx tests sets
```

### Show Test Set Contents

```bash
hvx tests set-show summer_analysis
```

### Create Test Set

```bash
hvx tests set-create
```

Example workflow:
```
$ hvx tests set-create

Set name: summer_overheating
Description: Tests focused on summer overheating issues

Available tests: (65 total)
    1. temp_below_20_all_year_opening           [temperature]
    2. temp_below_20_winter_opening             [temperature]
    3. temp_above_26_all_year_opening           [temperature]
    4. temp_above_26_summer_opening             [temperature]
    ...

Select tests (e.g., 1-5,10,12): 3,4,20-24,28

✓ Test set 'summer_overheating' created with 9 tests!
```

### Export Test Set

Export a test set as a standalone configuration file:

```bash
hvx tests set-export summer_overheating
```

Export to specific location:

```bash
hvx tests set-export summer_overheating --output config/custom/summer.yaml
```

This creates a complete YAML configuration with:
- Only the tests in the set
- All required period definitions
- All required filter definitions
- Holiday configurations

## Using Test Sets in Analysis

Once you've created a test set, use it in analysis:

```bash
hvx analyze run dataset.pkl --test-set summer_overheating
```

This will run the analysis using only the tests defined in the set, rather than all tests in the config file.

## Configuration Files

By default, commands use `config/tests.yaml`. You can specify a different config:

```bash
hvx tests list --config config/custom/my_tests.yaml
hvx tests create --config config/custom/my_tests.yaml
```

## Test Structure

A test definition includes:

```yaml
temp_below_20_winter_opening:
  description: "Temperature <20°C - Undercooling (winter, opening hours)"
  feature: temperature          # temperature, co2, humidity, combined
  period: winter               # all_year, winter, summer, spring, autumn
  filter: opening_hours        # opening_hours, morning, afternoon, etc.
  mode: unidirectional_descending  # how to evaluate
  limit: 20                    # single threshold (for unidirectional)
```

For bidirectional tests (range checks):

```yaml
temp_comfort_zone_20_26_winter:
  description: "Temperature 20-26°C - Comfort zone (winter)"
  feature: temperature
  period: winter
  filter: opening_hours_no_holidays
  mode: bidirectional
  limits:
    upper: 26
    lower: 20
```

## Common Workflows

### Create a Winter-Specific Analysis Set

```bash
# 1. Create custom filter for winter extended hours
hvx tests filter-create
# Name: winter_extended_hours
# Hours: 7-17

# 2. Create custom temperature test
hvx tests create --from-test temp_below_20_winter_opening
# Modify filter to winter_extended_hours

# 3. Create test set
hvx tests set-create
# Name: winter_deep_analysis
# Select all winter-related tests

# 4. Run analysis
hvx analyze run dataset.pkl --test-set winter_deep_analysis
```

### Clone and Modify Tests for Different Thresholds

```bash
# Edit existing test and save with new name
hvx tests edit temp_above_26_summer_opening --save-as temp_above_25_summer_opening
# Change limit from 26 to 25

# Verify
hvx tests show temp_above_25_summer_opening
```

### Create Custom Morning/Afternoon Analysis

```bash
# 1. Create morning test set
hvx tests set-create
# Name: morning_focus
# Select: all _morning tests

# 2. Create afternoon test set
hvx tests set-create
# Name: afternoon_focus
# Select: all _afternoon tests

# 3. Run comparative analysis
hvx analyze run dataset.pkl --test-set morning_focus --output output/morning_analysis
hvx analyze run dataset.pkl --test-set afternoon_focus --output output/afternoon_analysis
```

## Tips

1. **Start with templates**: Use `--from-test` to create variations of existing tests
2. **Use descriptive names**: Include feature, threshold, and period in the name (e.g., `temp_below_18_winter_custom`)
3. **Test sets for scenarios**: Create sets like `compliance_check`, `summer_overheating`, `winter_undercooling`
4. **Export for sharing**: Export test sets to share configurations across projects
5. **Filter reuse**: Create filters once and reuse them across multiple tests

## Available Periods

- `all_year`: All 12 months
- `spring`: March, April, May
- `summer`: June, July, August
- `autumn`: September, October, November
- `winter`: December, January, February
- `heating_season`: November-March
- `non_heating_season`: April-October

## Available Modes

- `unidirectional_ascending`: Values must be below threshold (e.g., CO2 < 1000ppm)
- `unidirectional_descending`: Values must be above threshold (e.g., Temp > 20°C)
- `bidirectional`: Values must be within range (e.g., 20°C < Temp < 26°C)

## See Also

- [Analysis Commands](./analyze-command.md)
- [Data Commands](./data-command.md)
- [Configuration Guide](../configuration.md)
