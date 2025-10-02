# Test Management CLI - Complete Walkthrough

This guide walks through real-world scenarios using the test management CLI.

## Scenario 1: Creating a Custom Winter Analysis

**Goal**: Analyze winter performance with custom temperature threshold of 18°C instead of standard 20°C.

### Step 1: Explore existing tests
```bash
$ hvx tests list --feature temperature --period winter

Filtered Tests (2 found)

Name                          Feature      Period  Filter         Mode
temp_below_20_winter_opening  temperature  winter  opening_hours  unidirectional_descending
temp_comfort_zone_20_26_...   temperature  winter  opening_hours  bidirectional
```

### Step 2: Create custom test from template
```bash
$ hvx tests create --from-test temp_below_20_winter_opening

Create New Test
Follow the prompts to define your test configuration.

Using 'temp_below_20_winter_opening' as template

Test name: temp_below_18_winter_opening
Description: Temperature <18°C - Stricter undercooling threshold (winter, opening hours)

Feature:
  1. temperature ←
  2. co2
  3. humidity
  4. combined
Select feature [1]: 1

Period:
  1. all_year
  2. winter ←
  3. summer
  4. spring
  5. autumn
Select period [2]: 2

Filter:
  1. opening_hours ←
  2. morning_no_holidays
  3. afternoon_no_holidays
Select filter [1]: 1

Mode:
  1. unidirectional_ascending
  2. unidirectional_descending ←
  3. bidirectional
Select mode [2]: 2

Threshold value [20.0]: 18

✓ Test 'temp_below_18_winter_opening' created successfully!
  Config saved to: config/tests.yaml
```

### Step 3: Verify the test
```bash
$ hvx tests show temp_below_18_winter_opening

╭──────────────────────────────────────────────────────────────────╮
│ temp_below_18_winter_opening                                     │
│ Temperature <18°C - Stricter undercooling threshold (winter, ... │
╰──────────────────────────────────────────────────────────────────╯

  Feature    temperature
  Period     winter
  Filter     opening_hours
  Mode       unidirectional_descending
  Limit      18
```

### Step 4: Create test set with custom and standard tests
```bash
$ hvx tests set-create

Create Test Set
Select tests to include in your custom analysis set.

Set name: winter_strict_analysis
Description: Winter analysis with stricter temperature thresholds

Available tests: (65 total)
  ...
  12. temp_below_18_winter_opening          [temperature]
  13. temp_below_20_winter_opening          [temperature]
  14. temp_comfort_zone_20_26_winter_opening [temperature]
  ...
  45. co2_1000_winter_opening               [co2]
  46. co2_2000_winter_opening               [co2]
  ...

Select tests (e.g., 1-5,10,12): 12-14,45-46

✓ Test set 'winter_strict_analysis' created with 5 tests!
  Config saved to: config/tests.yaml
```

### Step 5: Run analysis with custom test set
```bash
$ hvx analyze run output/dataset.pkl --test-set winter_strict_analysis

✓ Using test set: winter_strict_analysis

Hierarchical Analysis
Dataset: output/dataset.pkl
Config: config/tests.yaml
Test Set: winter_strict_analysis
Output: output/analysis

✓ Loaded 3 buildings with 45 rooms

Running hierarchical analysis...

✓ Analysis complete! Results saved to: output/analysis
```

---

## Scenario 2: Creating Time-Specific Analysis for Classrooms

**Goal**: Analyze classroom performance during extended hours (7am-5pm) excluding all holidays.

### Step 1: Create custom filter
```bash
$ hvx tests filter-create

Create New Filter
Define time-based filtering criteria.

Filter name: classroom_extended_hours
Description: Classroom hours 7-17, excluding all holidays

Define hours:
  1. Specific range (e.g., 8-15)
  2. Custom list (e.g., 8,9,10,14,15)
  3. All hours (0-23)
Select option [1]: 1

Start hour (0-23) [8]: 7
End hour (0-23) [15]: 17

Weekdays only? [Y/n]: Y
Exclude public holidays? [Y/n]: Y
Exclude custom holidays (school vacations)? [Y/n]: Y

✓ Filter 'classroom_extended_hours' created successfully!
  Config saved to: config/tests.yaml
```

### Step 2: Create tests using the new filter
```bash
# Create temperature test
$ hvx tests create --from-test temp_comfort_zone_20_26_all_year_opening

Test name: temp_comfort_classroom_extended
Description: Temperature 20-26°C - Comfort zone (classroom extended hours)

# Keep most defaults, change filter:
Filter:
  1. opening_hours
  2. classroom_extended_hours ←
Select filter: 2

✓ Test 'temp_comfort_classroom_extended' created successfully!

# Create CO2 test
$ hvx tests create --from-test co2_1000_all_year_opening

Test name: co2_1000_classroom_extended
Description: CO₂ <1000ppm - Standard air quality (classroom extended hours)

Filter: classroom_extended_hours

✓ Test 'co2_1000_classroom_extended' created successfully!
```

### Step 3: Create classroom-specific test set
```bash
$ hvx tests set-create

Set name: classroom_extended_analysis
Description: Comprehensive classroom analysis with extended hours

Select tests: [select the newly created tests and any other relevant ones]

✓ Test set 'classroom_extended_analysis' created with 8 tests!
```

### Step 4: Export for sharing with facilities team
```bash
$ hvx tests set-export classroom_extended_analysis \
    --output config/classroom_analysis.yaml

✓ Test set exported to: config/classroom_analysis.yaml
```

---

## Scenario 3: Comparing Different CO2 Thresholds

**Goal**: Compare compliance at different CO2 thresholds (800, 1000, 1200, 1500 ppm).

### Step 1: Clone and modify existing test for different thresholds
```bash
# 800 ppm test
$ hvx tests edit co2_1000_all_year_opening --save-as co2_800_all_year_opening
# Change limit: 800

# 1200 ppm test
$ hvx tests edit co2_1000_all_year_opening --save-as co2_1200_all_year_opening
# Change limit: 1200

# 1500 ppm test
$ hvx tests edit co2_1000_all_year_opening --save-as co2_1500_all_year_opening
# Change limit: 1500
```

### Step 2: Create test set with all thresholds
```bash
$ hvx tests set-create

Set name: co2_threshold_comparison
Description: Compare CO2 compliance at different thresholds (800-1500 ppm)

Available tests: (search for co2 tests)
Select tests: [select co2_800, co2_1000, co2_1200, co2_1500 and seasonal variants]

✓ Test set 'co2_threshold_comparison' created with 20 tests!
```

### Step 3: Run analysis
```bash
$ hvx analyze run output/dataset.pkl \
    --test-set co2_threshold_comparison \
    --output output/co2_comparison \
    --explore

✓ Using test set: co2_threshold_comparison

# Analysis runs...

Launching analysis explorer...
# Interactive explorer opens to compare thresholds
```

---

## Scenario 4: Seasonal Comparative Analysis

**Goal**: Compare building performance across all seasons with focused test sets.

### Step 1: Create season-specific test sets
```bash
# Winter set
$ hvx tests set-create
Set name: winter_focus
Description: Winter-specific performance tests
Select tests: [all winter tests]

# Spring set
$ hvx tests set-create
Set name: spring_focus
Description: Spring-specific performance tests
Select tests: [all spring tests]

# Summer set
$ hvx tests set-create
Set name: summer_focus
Description: Summer-specific performance tests
Select tests: [all summer tests]

# Autumn set
$ hvx tests set-create
Set name: autumn_focus
Description: Autumn-specific performance tests
Select tests: [all autumn tests]
```

### Step 2: Run seasonal analyses
```bash
# Run each season separately
$ hvx analyze run data.pkl --test-set winter_focus --output output/winter
$ hvx analyze run data.pkl --test-set spring_focus --output output/spring
$ hvx analyze run data.pkl --test-set summer_focus --output output/summer
$ hvx analyze run data.pkl --test-set autumn_focus --output output/autumn
```

### Step 3: Compare results
```bash
$ hvx analyze explore output/winter
$ hvx analyze explore output/spring
$ hvx analyze explore output/summer
$ hvx analyze explore output/autumn
```

---

## Scenario 5: Creating Morning vs. Afternoon Comparison

**Goal**: Understand how building performs in morning vs. afternoon.

### Step 1: Review existing time-based filters
```bash
$ hvx tests filters

Available Filters (11 total)

Name                   Hours   Weekdays Only  Exclude Holidays
morning_no_holidays    8-11    ✓              ✓
afternoon_no_holidays  12-15   ✓              ✓
evening_no_holidays    16-21   ✓              ✓
```

### Step 2: Create morning-specific test set
```bash
$ hvx tests list | grep morning

# Review all morning tests
$ hvx tests set-create

Set name: morning_performance
Description: Morning performance analysis (8-11)
Select tests: [all _morning tests]

✓ Test set 'morning_performance' created with 12 tests!
```

### Step 3: Create afternoon-specific test set
```bash
$ hvx tests set-create

Set name: afternoon_performance
Description: Afternoon performance analysis (12-15)
Select tests: [all _afternoon tests]

✓ Test set 'afternoon_performance' created with 12 tests!
```

### Step 4: Run comparative analysis
```bash
# Morning analysis
$ hvx analyze run data.pkl \
    --test-set morning_performance \
    --output output/morning_analysis \
    --portfolio-name "Morning Performance"

# Afternoon analysis
$ hvx analyze run data.pkl \
    --test-set afternoon_performance \
    --output output/afternoon_analysis \
    --portfolio-name "Afternoon Performance"

# Compare in explorer
$ hvx analyze explore output/morning_analysis
$ hvx analyze explore output/afternoon_analysis
```

---

## Scenario 6: Building Type-Specific Analysis

**Goal**: Create different test configurations for offices vs. classrooms.

### Step 1: Create type-specific filters
```bash
# Office hours filter
$ hvx tests filter-create
Filter name: office_hours
Hours: 8-17
Weekdays only: Yes
Exclude holidays: Yes (public only)

# Classroom hours filter
$ hvx tests filter-create
Filter name: classroom_hours
Hours: 7-15
Weekdays only: Yes
Exclude holidays: Yes (all holidays including school breaks)
```

### Step 2: Create tests for each type
```bash
# Office tests
$ hvx tests create --from-test temp_comfort_zone_20_26_all_year_opening
Test name: temp_comfort_office
Filter: office_hours

$ hvx tests create --from-test co2_1000_all_year_opening
Test name: co2_1000_office
Filter: office_hours

# Classroom tests
$ hvx tests create --from-test temp_comfort_zone_20_26_all_year_opening
Test name: temp_comfort_classroom
Filter: classroom_hours

$ hvx tests create --from-test co2_1000_all_year_opening
Test name: co2_1000_classroom
Filter: classroom_hours
```

### Step 3: Create building-type test sets
```bash
$ hvx tests set-create
Set name: office_buildings
Description: Tests configured for office building analysis
Select tests: [all office tests]

$ hvx tests set-create
Set name: classroom_buildings
Description: Tests configured for classroom/school building analysis
Select tests: [all classroom tests]
```

### Step 4: Export for different teams
```bash
# Export for office facilities team
$ hvx tests set-export office_buildings \
    --output config/office_analysis.yaml

# Export for school facilities team
$ hvx tests set-export classroom_buildings \
    --output config/classroom_analysis.yaml

# Each team now has their own configuration file!
```

---

## Tips from the Walkthroughs

1. **Start with templates**: Always use `--from-test` to inherit settings
2. **Test incrementally**: Create one test, verify, then create set
3. **Use descriptive names**: Include feature, threshold, and context in names
4. **Organize by purpose**: Group tests by analysis goal, not just by feature
5. **Export for sharing**: Share test sets as standalone configs
6. **Compare iteratively**: Run multiple analyses with different test sets

## Common Patterns

### Pattern 1: Threshold Sensitivity Analysis
```bash
# Create multiple tests with different thresholds
hvx tests edit original_test --save-as test_strict
hvx tests edit original_test --save-as test_moderate
hvx tests edit original_test --save-as test_lenient

# Group into comparison set
hvx tests set-create  # name: threshold_comparison
```

### Pattern 2: Time-of-Day Analysis
```bash
# Create time-specific filter
hvx tests filter-create  # custom hours

# Clone tests for specific time
hvx tests create --from-test base_test
# Apply custom filter

# Group by time period
hvx tests set-create  # name: specific_time_analysis
```

### Pattern 3: Seasonal Deep-Dive
```bash
# Filter by season
hvx tests list --period winter

# Create focused set
hvx tests set-create  # select all winter tests

# Run isolated analysis
hvx analyze run data.pkl --test-set winter_focus
```

## Troubleshooting

### Test set not found
```bash
$ hvx analyze run data.pkl --test-set my_set
✗ Test set 'my_set' not found in config.
Available test sets:
  • summer_analysis
  • winter_focus

# Solution: Check name spelling or create the set
$ hvx tests sets
```

### Filter doesn't exist
```bash
# When creating test, if filter not in list:
$ hvx tests filters  # View all available filters
$ hvx tests filter-create  # Create the missing filter
```

### Want to modify existing test
```bash
# Don't delete and recreate - use edit!
$ hvx tests edit existing_test --save-as modified_test
# Preserves all settings, modify only what you need
```

## See Also

- [Command Reference](./tests-command.md)
- [Quick Reference](./tests-quick-reference.md)
- [Analysis Commands](./analyze-command.md)
