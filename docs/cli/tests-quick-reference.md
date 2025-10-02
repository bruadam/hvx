# Test Management Quick Reference

## Command Summary

| Command | Description |
|---------|-------------|
| `hvx tests list` | List all tests |
| `hvx tests show <name>` | Show test details |
| `hvx tests create` | Create new test interactively |
| `hvx tests edit <name>` | Edit existing test |
| `hvx tests delete <name>` | Delete a test |
| `hvx tests filters` | List all filters |
| `hvx tests filter-create` | Create new filter |
| `hvx tests sets` | List test sets |
| `hvx tests set-show <name>` | Show test set contents |
| `hvx tests set-create` | Create test set |
| `hvx tests set-export <name>` | Export test set to file |

## Common Use Cases

### 1. List tests by feature
```bash
hvx tests list --feature temperature
hvx tests list --feature co2
hvx tests list --period winter
```

### 2. Create a custom test
```bash
# From scratch
hvx tests create

# From existing template
hvx tests create --from-test temp_below_20_winter_opening
```

### 3. Edit and save with new name
```bash
hvx tests edit temp_above_26_summer_opening --save-as temp_above_25_summer_opening
```

### 4. Create a test set for focused analysis
```bash
# Create set
hvx tests set-create
# Name: summer_overheating
# Select tests: 3,4,20-24

# Use in analysis
hvx analyze run dataset.pkl --test-set summer_overheating
```

### 5. Create custom time filter
```bash
hvx tests filter-create
# Name: extended_hours
# Hours: 7-17
# Weekdays: Yes
# Exclude holidays: Yes
```

### 6. Export test set for sharing
```bash
hvx tests set-export summer_overheating --output config/summer.yaml
```

## Test Configuration Options

### Features
- `temperature` - Temperature measurements
- `co2` - CO2 concentration
- `humidity` - Relative humidity
- `combined` - Multi-parameter tests using JSON logic

### Periods
- `all_year` - Full year (Jan-Dec)
- `winter` - Dec, Jan, Feb
- `spring` - Mar, Apr, May
- `summer` - Jun, Jul, Aug
- `autumn` - Sep, Oct, Nov
- `heating_season` - Nov-Mar
- `non_heating_season` - Apr-Oct

### Modes
- `unidirectional_ascending` - Below threshold (e.g., CO2 < 1000)
- `unidirectional_descending` - Above threshold (e.g., Temp > 20)
- `bidirectional` - Within range (e.g., 20 < Temp < 26)

### Filter Components
- `hours` - Hour list (e.g., [8,9,10,11,12,13,14,15])
- `weekdays_only` - Include only Mon-Fri
- `exclude_holidays` - Exclude public holidays
- `exclude_custom_holidays` - Exclude school vacations

## Example Workflows

### Winter Analysis Set
```bash
# 1. Create morning winter tests
hvx tests create --from-test temp_below_20_winter_opening
# Modify to use morning_no_holidays filter

# 2. Create test set
hvx tests set-create
# Name: winter_morning_analysis
# Select winter + morning tests

# 3. Run analysis
hvx analyze run data.pkl --test-set winter_morning_analysis
```

### Custom Threshold Analysis
```bash
# Clone and modify for different thresholds
hvx tests edit co2_1000_all_year_opening --save-as co2_800_all_year_opening
# Change limit: 800

hvx tests edit co2_1000_all_year_opening --save-as co2_1200_all_year_opening
# Change limit: 1200

# Create comparative test set
hvx tests set-create
# Name: co2_threshold_comparison
# Select: co2_800, co2_1000, co2_1200 tests
```

### Room Type Specific Analysis
```bash
# Create custom filters
hvx tests filter-create
# Name: classroom_hours (7-15)

hvx tests filter-create
# Name: office_hours (8-17)

# Create tests with specific filters
hvx tests create --from-test temp_comfort_zone_20_26_all_year_opening
# Change filter to classroom_hours
# Name: temp_comfort_classroom

# Create test sets
hvx tests set-create
# Name: classroom_analysis
# Select classroom-specific tests

hvx tests set-create
# Name: office_analysis
# Select office-specific tests
```

## Tips

1. **Naming convention**: Use pattern `{feature}_{condition}_{period}_{filter}`
   - Example: `temp_below_18_winter_morning`

2. **Test templates**: Always start with `--from-test` to inherit settings

3. **Filter reuse**: Create filters once, use across multiple tests

4. **Test sets for scenarios**: Group related tests by purpose
   - `compliance_check` - Regulatory compliance
   - `summer_overheating` - Seasonal issues
   - `morning_analysis` - Time-of-day focus

5. **Export for documentation**: Export test sets to share configurations

6. **Selection ranges**: Use ranges for efficiency
   - `1-10` selects tests 1 through 10
   - `1,5,7-9,12` selects 1, 5, 7, 8, 9, 12

## See Also

- [Full Documentation](./tests-command.md)
- [Analysis Commands](./analyze-command.md)
- [Configuration Guide](../configuration.md)
