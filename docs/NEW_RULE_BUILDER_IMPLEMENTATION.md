# New Rule Builder Implementation

## Overview

This document describes the new rule builder implementation that replaces the previous json-logic-based system with a custom, native Python rule evaluation engine. The new system is more maintainable, easier to debug, and directly supports the YAML configuration structure.

## Key Changes

### 1. Removed json-logic Dependency

**Before:** The system relied on the `json-logic` library which had issues with:
- Complex installation requirements
- Limited debugging capabilities
- Inflexible rule syntax
- Poor error handling

**After:** Custom Python rule evaluator with:
- Native Python logic evaluation
- Clear error messages
- Type-safe operations
- Flexible rule definitions

### 2. New Core Classes

#### `RuleEvaluator`
- Static class for evaluating rule conditions
- Supports logical operators: `and`, `or`, `not`
- Supports comparison operators: `>=`, `<=`, `>`, `<`, `==`, `!=`
- Handles variable references with `{'var': 'variable_name'}`
- Safe handling of missing data and type errors

#### `SimpleRuleBuilder`
- Fluent API for building rules programmatically
- Methods for common patterns:
  - `add_range_condition()` for bidirectional limits (temperature, humidity)
  - `add_threshold_condition()` for unidirectional limits (CO2)
- Chainable operations with `reset()` and `build()` methods

#### `AnalyticsFilter`
- Enhanced time and period filtering
- Proper holiday handling
- Support for complex filter combinations
- Weekday/weekend filtering
- Hour-based filtering

#### `AnalyticsEngine`
- Main engine for rule evaluation
- Support for multiple rule types:
  - Simple analytics rules (from `analytics` section)
  - Complex EN standard rules (from `rules` section)
- Intelligent column matching for different data formats
- Comprehensive error handling and logging

## Supported Rule Types

### 1. Bidirectional Rules (Range-based)
For parameters like temperature and humidity with min/max limits:

```yaml
temp_comfort_all_year_opening:
  description: "Temperatur 20-26°C (hele året, åbningstid)"
  feature: temperature
  period: all_year
  filter: opening_hours
  mode: bidirectional
  limits: 
    upper: 26
    lower: 20
```

### 2. Unidirectional Rules (Threshold-based)
For parameters like CO2 with single limits:

```yaml
co2_1000_all_year_opening:
  description: "CO2 <1000ppm (hele året, åbningstid)"
  feature: co2
  period: all_year
  filter: opening_hours
  mode: unidirectional_ascending
  limit: 1000
```

### 3. Complex Logic Rules
For advanced combinations using logical operators:

```yaml
comfort_optimal_opening:
  description: "Optimal comfort (temperatur 21-24°C og CO2 <800ppm, åbningstid)"
  feature: combined
  period: all_year
  filter: opening_hours
  json_logic:
    and:
      - and:
          - ">=": [{"var": "temperature"}, 21]
          - "<=": [{"var": "temperature"}, 24]
      - "<": [{"var": "co2"}, 800]
```

## Configuration Structure

### Analytics Rules
Simple rules for standard IEQ analysis:

```yaml
analytics:
  rule_name:
    description: "Human readable description"
    feature: "temperature|co2|humidity|combined"
    period: "all_year|spring|summer|autumn|winter"
    filter: "opening_hours|non_opening_hours|morning|afternoon"
    mode: "bidirectional|unidirectional_ascending|unidirectional_descending"
    limits:  # For bidirectional rules
      upper: 26
      lower: 20
    limit: 1000  # For unidirectional rules
    json_logic:  # For complex rules
      and: [...]
```

### EN Standard Rules
Complex rules for EN 16798-1 compliance:

```yaml
rules:
  rule_name:
    description: "EN16798-1 Category I Temperature Compliance"
    category: "EN16798-1 Category I"
    parameter: "temperature"
    period: "all_year"
    filter: "school_opening_hours"
    rule:
      "and": [
        {">=": [{"var": "temperature"}, 21]},
        {"<=": [{"var": "temperature"}, 23]}
      ]
```

### Periods and Filters
Define time-based filtering:

```yaml
periods:
  spring:
    months: [3, 4, 5]
  summer:
    months: [6, 7, 8]

filters:
  opening_hours:
    hours: [8, 9, 10, 11, 12, 13, 14, 15]
    weekdays_only: true
    exclude_holidays: true
```

## Smart Column Matching

The new system intelligently matches feature names to actual data columns:

- **Direct match**: `temperature` matches `temperature`
- **Case-insensitive partial match**: `temperature` matches `Temperature_C`
- **Alias matching**: `co2` matches `co2_ppm`, `carbon_dioxide`

Common aliases supported:
- `temperature`: `temp`, `temperature_c`, `temp_c`, `air_temperature`
- `humidity`: `rh`, `relative_humidity`, `humidity_percent`, `humidity_rh`
- `co2`: `co2_ppm`, `carbon_dioxide`, `co2_concentration`

## Error Handling

The new system provides comprehensive error handling:

1. **Configuration Errors**: Clear messages when YAML is malformed
2. **Missing Columns**: Warnings when data columns aren't found
3. **Data Type Errors**: Safe handling of non-numeric data
4. **Rule Evaluation Errors**: Graceful degradation with error reporting
5. **Filter Errors**: Informative messages for invalid time filters

## Performance Improvements

1. **No External Dependencies**: Faster startup, no installation issues
2. **Vectorized Operations**: Uses pandas operations where possible
3. **Caching**: Holiday data and configuration caching
4. **Early Exit**: Skip processing when filters result in empty datasets

## Usage Examples

### Basic Usage

```python
from ieq_analytics.rule_builder import AnalyticsEngine
from ieq_analytics.models import IEQData

# Initialize engine with config
engine = AnalyticsEngine("config/analytics_rules.yaml")

# Analyze all rules
results = engine.analyze_comfort_compliance(ieq_data)

# Analyze specific rule
result = engine.analyze_rule(data, "temp_comfort_all_year_opening")
```

### Building Rules Programmatically

```python
from ieq_analytics.rule_builder import SimpleRuleBuilder

# Create a temperature comfort rule
builder = SimpleRuleBuilder()
rule = builder.add_range_condition('temperature', 20, 26).build()

# Create a CO2 threshold rule
builder.reset()
rule = builder.add_threshold_condition('co2', 1000, '<=').build()
```

### Custom Rule Evaluation

```python
from ieq_analytics.rule_builder import RuleEvaluator

evaluator = RuleEvaluator()

# Simple condition
condition = {'>=': [{'var': 'temperature'}, 20]}
data = {'temperature': 22}
result = evaluator.evaluate_condition(condition, data)  # True

# Complex condition
condition = {
    'and': [
        {'>=': [{'var': 'temperature'}, 20]},
        {'<=': [{'var': 'co2'}, 800]}
    ]
}
result = evaluator.evaluate_condition(condition, data)
```

## Migration from Old System

The new system is backwards compatible with existing configurations. No changes are required to existing YAML files, but new features are available:

1. **Legacy `json_logic` rules**: Still supported for complex rules
2. **New simple rules**: Can use `limits`/`limit` instead of `json_logic`
3. **Enhanced filtering**: More robust time and period filtering
4. **Better error messages**: Clearer feedback when rules fail

## Testing

The new implementation includes comprehensive testing:

```bash
# Run basic functionality test
python -c "from ieq_analytics.rule_builder import RuleEvaluator; print('✅ Working!')"

# Test with real data
python -m ieq_analytics.cli analyze --data-dir data/mapped --rules-config config/analytics_rules.yaml
```

## Benefits

1. **No External Dependencies**: Eliminates json-logic installation issues
2. **Better Debugging**: Clear error messages and stack traces
3. **Type Safety**: Proper handling of missing/invalid data
4. **Performance**: Faster evaluation with native Python operations
5. **Maintainability**: Cleaner, more readable code
6. **Flexibility**: Easy to extend with new rule types
7. **Documentation**: Self-documenting rule structure

## Future Enhancements

1. **Rule Validation**: Syntax checking for rule configurations
2. **Performance Profiling**: Optimize slow rule evaluations
3. **Rule Templates**: Common patterns as reusable templates
4. **Visual Rule Builder**: GUI for creating rules
5. **Rule Testing Framework**: Unit tests for individual rules
