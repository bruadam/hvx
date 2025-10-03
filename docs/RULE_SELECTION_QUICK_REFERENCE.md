# IEQ Rule Selection - Quick Reference

## Command Line Usage

### Run All Standards (Auto Mode)
```bash
hvx ieq start
```
**Result**: Runs all 18 rules from all standards with defaults

### Interactive Selection
```bash
hvx ieq start
# Choose option: 1. Interactive rule selection
```

## Programmatic API

### Basic Setup
```python
from src.core.analytics.ieq.ConfigBuilder import IEQConfigBuilder
from src.core.analytics.hierarchical_analysis_service import HierarchicalAnalysisService

builder = IEQConfigBuilder()
```

### Add Complete Standards
```python
builder.add_standard("en16798-1")        # All EN16798-1 rules (12)
builder.add_standard("br18")              # All BR18 rules (4)
builder.add_standard("danish-guidelines") # All Danish rules (2)
```

### Add Individual Rules
```python
builder.add_rule("cat_i_temp_heating_season", "en16798-1")
builder.add_rule("cat_ii_co2", "en16798-1")
builder.add_rule("office_temp_above_26_max_100h", "br18")
```

### Apply Filters
```python
# To all rules
builder.apply_filter_to_all("opening_hours_no_holidays")

# To specific rule
builder.apply_filter_to_rule("cat_i_temp_heating_season", "all_hours")
```

### Apply Periods
```python
# To all rules
builder.apply_period_to_all("summer")

# To specific rule
builder.apply_period_to_rule("cat_i_temp_heating_season", "winter")
```

### Build and Use
```python
config = builder.build()

service = HierarchicalAnalysisService(config_dict=config)
results = service.analyze_dataset(dataset, output_dir=Path("output"))
```

## Available Options Reference

### Standards (3 total)
| Standard | Rules | Description |
|----------|-------|-------------|
| `en16798-1` | 12 | European indoor environment standard |
| `br18` | 4 | Danish Building Regulations 2018 |
| `danish-guidelines` | 2 | Danish indoor climate guidelines |

### Common Filters
| Filter | Use Case |
|--------|----------|
| `opening_hours` | Standard business hours (8-15) |
| `opening_hours_no_holidays` | Business hours, exclude holidays (most accurate) |
| `all_hours` | 24/7 analysis (residential) |
| `morning_no_holidays` | Morning analysis (8-11) |
| `afternoon_no_holidays` | Afternoon analysis (12-15) |

### Common Periods
| Period | Use Case |
|--------|----------|
| `all_year` | General compliance |
| `summer` | Overheating analysis |
| `winter` | Undercooling analysis |
| `heating_season` | Oct-Apr analysis |
| `non_heating_season` | May-Sep analysis |

## Common Scenarios

### Scenario 1: Office Compliance (EN16798-1)
```python
builder = IEQConfigBuilder()
builder.add_standard("en16798-1")
builder.apply_filter_to_all("opening_hours_no_holidays")
config = builder.build()
```

### Scenario 2: Summer Overheating Analysis
```python
builder = IEQConfigBuilder()
builder.add_standard("br18")  # BR18 overheating rules
builder.apply_period_to_all("summer")
config = builder.build()
```

### Scenario 3: Temperature Only (All Standards)
```python
builder = IEQConfigBuilder()

# EN16798-1 temperature rules
builder.add_rule("cat_i_temp_heating_season", "en16798-1")
builder.add_rule("cat_i_temp_non_heating_season", "en16798-1")

# BR18 overheating rules
builder.add_rule("office_temp_above_26_max_100h", "br18")
builder.add_rule("office_temp_above_27_max_25h", "br18")

config = builder.build()
```

### Scenario 4: Residential 24/7 Analysis
```python
builder = IEQConfigBuilder()
builder.add_standard("br18")  # Residential rules
builder.apply_filter_to_all("all_hours")  # 24/7
builder.apply_period_to_all("all_year")
config = builder.build()
```

### Scenario 5: School Analysis (Danish Guidelines)
```python
builder = IEQConfigBuilder()
builder.add_standard("danish-guidelines")
builder.apply_filter_to_all("opening_hours_no_holidays")  # Exclude holidays
config = builder.build()
```

## Inspection Methods

### Check What's Available
```python
builder = IEQConfigBuilder()

# List standards
print(builder.get_available_standards())

# List rules for a standard
rules = builder.get_rules_for_standard("en16798-1")
for rule in rules:
    print(f"{rule.name}: {rule.description}")

# List filters
filters = builder.get_available_filters()
for f in filters:
    print(f"{f.name}: {f.description}")

# List periods
periods = builder.get_available_periods()
for p in periods:
    print(f"{p.name}: {p.description}")
```

### Check What's Selected
```python
# Get summary
summary = builder.get_summary()
print(summary)

# Get full config
config = builder.build()
print(f"Total rules: {len(config['analytics'])}")
```

## Save and Load

### Save Configuration
```python
builder.save_to_file(Path("my_analysis_config.yaml"))
```

### Load from File
```python
# Use saved config
service = HierarchicalAnalysisService(config_path=Path("my_analysis_config.yaml"))
```

## Tips

1. **Start Simple**: Begin with a full standard, then refine
   ```python
   builder.add_standard("en16798-1")
   ```

2. **Override Defaults**: Add a standard, then customize
   ```python
   builder.add_standard("en16798-1")
   builder.apply_filter_to_all("opening_hours_no_holidays")
   ```

3. **Mix and Match**: Combine multiple approaches
   ```python
   builder.add_standard("br18")  # All BR18 rules
   builder.add_rule("cat_i_co2", "en16798-1")  # Add CO2
   ```

4. **Check Before Running**: Use `get_summary()` to verify
   ```python
   print(builder.get_summary())
   ```

## Rule Categories by Feature

### Temperature Rules (14 total)
- EN16798-1: 6 (Category I, II, III × heating/non-heating)
- BR18: 4 (Office/residential × 2 limits)
- Danish Guidelines: 1 (School comfort)

### CO2 Rules (4 total)
- EN16798-1: 3 (Category I, II, III)
- Danish Guidelines: 1 (General guidelines)

### Humidity Rules (3 total)
- EN16798-1: 3 (Category I, II, III)

## Error Handling

### Rule Not Found
```python
builder.add_rule("nonexistent_rule")  # Silently skips
# Always check the summary to verify rules were added
```

### Invalid Filter
```python
builder.apply_filter_to_all("invalid_filter")
# Apply valid filters only - check available options first
```

## Performance Notes

- **More rules = longer analysis time**
  - 18 rules (all): ~10-15 seconds per room
  - 5 rules (custom): ~3-5 seconds per room

- **Recommendation**: Select only needed rules for faster analysis

## Integration with Workflow

The rule selector is integrated into `hvx ieq start`:

```
Configuration Options:
  1. Interactive rule selection (recommended)  ← Full flexibility
  2. Use all standards with defaults          ← Quick start
  3. Load from existing config file           ← Saved configs
```

Choose option 1 for interactive selection with console-based UI.
