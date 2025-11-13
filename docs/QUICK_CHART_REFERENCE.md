# Quick Chart Reference Guide

## Available Chart Types

### 1. Bar Charts

#### Simple Bar Chart
```python
from core.reporting.charts import render_bar_chart

data = {
    "title": "Compliance Rates",
    "data": {
        "categories": ["Room 1", "Room 2", "Room 3"],
        "values": [95.5, 87.2, 92.8],
    },
    "styling": {
        "xlabel": "Room",
        "ylabel": "Compliance (%)",
        "threshold_line": 95.0,  # Optional threshold
    }
}

config = {"figsize": (12, 6), "dpi": 300}
render_bar_chart(data, config, "output.png")
```

#### Grouped Bar Chart
```python
from core.reporting.charts import render_grouped_bar_chart

data = {
    "title": "Multi-Metric Comparison",
    "data": {
        "categories": ["Room 1", "Room 2", "Room 3"],
        "series": [
            {"name": "Temp", "values": [95, 87, 92], "color": "#e74c3c"},
            {"name": "CO2", "values": [92, 89, 94], "color": "#3498db"},
        ]
    },
    "styling": {
        "xlabel": "Room",
        "ylabel": "Compliance (%)"
    }
}
```

### 2. Line Charts (Time Series)

```python
from core.reporting.charts import render_line_chart
from datetime import datetime, timedelta

# Generate timestamps
start = datetime(2024, 1, 1)
timestamps = [start + timedelta(hours=i) for i in range(168)]

data = {
    "title": "Temperature Over Time",
    "data": {
        "timestamps": timestamps,
        "values": [20.5, 21.2, ...],  # Your data
        "target_min": 20.0,  # Optional
        "target_max": 24.0,  # Optional
    },
    "styling": {
        "xlabel": "Time",
        "ylabel": "Temperature (°C)",
    }
}

config = {
    "figsize": (14, 6),
    "show_targets": True,
    "moving_average": 24,  # Optional: window size in hours
}
render_line_chart(data, config, "output.png")
```

### 3. Heatmaps

```python
from core.reporting.charts import render_heatmap
import numpy as np

# Create 7x24 matrix (days x hours)
matrix = np.random.rand(7, 24) * 100

data = {
    "title": "Occupancy Pattern",
    "data": {
        "matrix": matrix.tolist(),
        "x_labels": [f"{h:02d}:00" for h in range(24)],
        "y_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    },
    "styling": {
        "xlabel": "Hour of Day",
        "ylabel": "Day of Week",
        "colormap": "YlOrRd",
        "colorbar_label": "Occupancy (%)",
    }
}

config = {"figsize": (14, 6), "show_values": False}
render_heatmap(data, config, "output.png")
```

### 4. Compliance Charts

```python
from core.reporting.charts import render_compliance_chart

data = {
    "title": "Compliance Overview",
    "data": {
        "categories": ["Temp", "CO2", "Humidity"],
        "compliance_rates": [96.5, 88.3, 92.1],
    },
    "styling": {
        "xlabel": "Parameter",
        "ylabel": "Compliance Rate (%)"
    }
}

# Automatically color-codes:
# Green (≥95%), Yellow (85-95%), Orange (70-85%), Red (<70%)
render_compliance_chart(data, config, "output.png")
```

## Using Charts in HTML Reports

### Template YAML Configuration

```yaml
sections:
  - type: chart
    title: "Room Compliance Comparison"
    description: "Compliance rates across all analyzed rooms"
    chart:
      type: room_comparison_bar
      title: "Room Compliance"
      options:
        renderer: matplotlib  # or "plotly" for interactive
        metric: compliance     # or "quality", "violations"
        sort: true
        ascending: false
        show_only_failing: false
        failing_threshold: 95.0
        figsize: [14, 6]
        dpi: 300

  - type: chart
    title: "Temperature Trends"
    chart:
      type: timeseries
      options:
        renderer: matplotlib
        parameter: temperature
        show_targets: true
        moving_average: 24
```

## Customizing Styles

### Edit Global Style (`config/charts/global_style.yaml`)

```yaml
font:
  family: sans-serif
  size: 10

colors:
  categorical:
    - '#3498db'  # Blue
    - '#e74c3c'  # Red
    - '#2ecc71'  # Green

figure:
  figsize: [12, 6]
  dpi: 300
```

### Edit Chart-Specific Style (`config/charts/bar_chart_style.yaml`)

```yaml
bars:
  width: 0.6
  alpha: 0.8
  colors:
    default: '#3498db'
    compliant: '#2ecc71'
    non_compliant: '#e74c3c'

threshold:
  enabled: true
  color: '#e74c3c'
  linestyle: '--'
```

## Programmatic Style Override

```python
# Override styles in config parameter
config = {
    "figsize": (16, 8),      # Custom size
    "dpi": 150,              # Lower resolution for web
    "bars": {
        "width": 0.8,
        "alpha": 0.9,
        "colors": {
            "default": "#purple"
        }
    }
}

render_bar_chart(data, config, output_path)
```

## Color Palettes

### Categorical (for discrete data)
- Blue: `#3498db`
- Red: `#e74c3c`
- Green: `#2ecc71`
- Orange: `#f39c12`
- Purple: `#9b59b6`
- Teal: `#1abc9c`

### Compliance Colors
- Excellent (≥95%): `#4CAF50` (Green)
- Good (85-95%): `#FFC107` (Yellow)
- Fair (70-85%): `#FF9800` (Orange)
- Poor (<70%): `#F44336` (Red)

### Heatmap Color Schemes
- `YlOrRd` - Yellow to Orange to Red (occupancy, intensity)
- `RdYlGn` - Red to Yellow to Green (performance)
- `coolwarm` - Blue to Red (correlation)
- `viridis` - Purple to Yellow (general purpose)

## Tips

### 1. High-Quality Exports
```python
config = {
    "figsize": (16, 9),  # Larger size
    "dpi": 300,          # Print quality
}
```

### 2. Web-Friendly Charts
```python
config = {
    "figsize": (12, 6),
    "dpi": 96,  # Screen resolution
}
```

### 3. Consistent Branding
Edit `config/charts/global_style.yaml` once, affects all charts.

### 4. Interactive vs Static
- Use **Plotly** (default) for: dashboards, exploration, hover details
- Use **Matplotlib** for: reports, PDFs, consistent styling, print

### 5. Data Formatting
- Timestamps can be strings (ISO format) or datetime objects
- Values can be lists or numpy arrays
- Missing data: use `np.nan` or filter out before charting

## Common Patterns

### From Room Analysis
```python
from core.domain.models.room_analysis import RoomAnalysis

# Extract data from room analyses
room_names = [r.room_name for r in room_analyses]
compliance_rates = [r.overall_compliance_rate for r in room_analyses]

data = {
    "title": "Room Comparison",
    "data": {
        "categories": room_names,
        "values": compliance_rates,
    },
    "styling": {
        "xlabel": "Room",
        "ylabel": "Compliance (%)",
        "threshold_line": 95.0,
    }
}
```

### From Building Analysis
```python
from core.domain.models.building_analysis import BuildingAnalysis

building_names = [b.building_name for b in building_analyses]
avg_rates = [b.avg_compliance_rate for b in building_analyses]

data = {
    "data": {
        "categories": building_names,
        "compliance_rates": avg_rates,
    }
}
```

## Troubleshooting

### Charts not appearing in HTML
- Check that `renderer: matplotlib` is set in template
- Verify matplotlib is installed: `pip install matplotlib seaborn`
- Check browser console for errors

### Poor quality images
- Increase `dpi` in config (try 300)
- Increase `figsize` for more pixels

### Text overlapping
- Adjust `figsize` to give more room
- Modify rotation in `xaxis` config
- Reduce number of categories or use smaller font

### Memory issues with many charts
- Use lower DPI for draft reports
- Generate charts sequentially, not in parallel
- Clear matplotlib state: `plt.close('all')`

## Examples Directory

Check `clean/test_matplotlib_charts.py` for working examples of all chart types.
