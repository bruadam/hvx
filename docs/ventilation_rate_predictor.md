# VentilationRatePredictor Documentation

## Overview

`VentilationRatePredictor` is a Python class for analyzing indoor air quality data, specifically focusing on CO2 decay periods to estimate ventilation rates (ACH: Air Changes per Hour). It identifies periods of monotonically decreasing CO2, filters them to outside opening hours, and predicts ventilation rates using the gas decay function. The class also provides statistical summaries and confidence estimates for the results.

## Key Methods

### `find_decay_periods(data, min_length=3)`
- **Purpose:** Identifies periods in the CO2 time series where the concentration decreases monotonically.
- **Returns:** List of decay periods, each with start/end timestamps and CO2 values.
- **Parameters:**
  - `data`: Pandas DataFrame with a CO2 column.
  - `min_length`: Minimum number of consecutive decreasing points to qualify as a decay period.

### `filter_outside_opening_hours(periods, data, start_hour=8, end_hour=17)`
- **Purpose:** Filters decay periods to those occurring outside specified opening hours (default: 8-17).
- **Returns:** List of filtered decay periods.

### `predict_ventilation_rate(period, dt_minutes=60.0)`
- **Purpose:** Estimates the ventilation rate (ACH) for a decay period using the gas decay function:
  - Formula: `C(t) = C0 * exp(-ACH * t)` → `ACH = -ln(C(t)/C0)/t`
- **Returns:** ACH value (float) or None if calculation is not possible.
- **Parameters:**
  - `period`: Decay period dictionary with CO2 values.
  - `dt_minutes`: Time interval between measurements (default: 60 min).

### `analyze(data)`
- **Purpose:** Full pipeline: finds decay periods, filters outside opening hours, predicts ACH for each.
- **Returns:** List of results, each with start/end, ACH, and values.

### `summarize_ach_statistics(results, txt_path=None, ask_save=True)`
- **Purpose:** Prints a table of all decay periods and their ACH values, computes weighted statistics, and estimates confidence level. Optionally saves the summary to a text file.
- **Calculations:**
  - **Weighted Mean/Std:** Each ACH value is weighted by the number of data points in its decay period.
  - **Confidence Level:**
    - High: ≥10 periods, std < 0.01, total points > 30
    - Medium: ≥5 periods, std < 0.02, total points > 15
    - Low: Otherwise
- **Parameters:**
  - `results`: Output from `analyze()`
  - `txt_path`: Path to save summary (optional)
  - `ask_save`: If True, prompts user to save summary

## Example Usage

```python
from ieq_analytics.ventilation_rate_predictor import VentilationRatePredictor
import pandas as pd

data = pd.read_csv('your_data.csv', index_col=0, parse_dates=True)
predictor = VentilationRatePredictor(co2_col='CO2')
results = predictor.analyze(data)
predictor.summarize_ach_statistics(results)
```

## Output
- **Table:** Start/end times, ACH, number of data points for each decay period
- **Statistics:** Weighted mean, median, std, min, max, number of periods, total data points
- **Confidence:** Based on number of periods, std deviation, and total data points
- **Optional:** Save summary and table to a text file

## Notes
- The number of data points in each decay period is used for both confidence calculation and as a weight in the average/statistics.
- The method is robust to missing or non-monotonic data, and skips periods with insufficient data.
