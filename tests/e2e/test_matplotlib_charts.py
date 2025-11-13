"""Test matplotlib chart generation in clean architecture."""

from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

from core.reporting.charts import (
    render_bar_chart,
    render_line_chart,
    render_heatmap,
    render_compliance_chart,
)


def test_bar_chart():
    """Test bar chart generation."""
    print("Testing bar chart generation...")

    data = {
        "title": "Room Compliance Comparison",
        "data": {
            "categories": ["Room A", "Room B", "Room C", "Room D", "Room E"],
            "compliance_percentage": [98.5, 92.3, 87.6, 95.2, 89.1],
        },
        "styling": {
            "xlabel": "Room",
            "ylabel": "Compliance Rate (%)",
            "threshold_line": 95.0,
        },
    }

    config = {"figsize": (12, 6), "dpi": 300}
    output_path = Path("output/charts/test_bar_chart.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    render_bar_chart(data, config, output_path)
    print(f"✓ Bar chart saved to {output_path}")


def test_line_chart():
    """Test line chart generation."""
    print("\nTesting line chart generation...")

    # Generate sample timeseries data
    start_time = datetime(2024, 1, 1, 0, 0)
    timestamps = [start_time + timedelta(hours=i) for i in range(168)]  # 1 week
    temperatures = [20 + 3 * np.sin(i * 2 * np.pi / 24) + np.random.randn() * 0.5
                   for i in range(168)]

    data = {
        "title": "Temperature Over Time - Room A",
        "data": {
            "timestamps": timestamps,
            "values": temperatures,
            "target_min": 20.0,
            "target_max": 24.0,
        },
        "styling": {
            "xlabel": "Time",
            "ylabel": "Temperature (°C)",
            "color": "#e74c3c",
        },
    }

    config = {"figsize": (14, 6), "dpi": 300, "show_targets": True}
    output_path = Path("output/charts/test_line_chart.png")

    render_line_chart(data, config, output_path)
    print(f"✓ Line chart saved to {output_path}")


def test_compliance_chart():
    """Test compliance overview chart."""
    print("\nTesting compliance chart generation...")

    data = {
        "title": "Compliance Overview by Test",
        "data": {
            "categories": ["Temp Test", "CO2 Test", "Humidity Test", "Ventilation Test"],
            "compliance_rates": [96.5, 88.3, 92.1, 85.7],
        },
        "styling": {
            "xlabel": "Test",
            "ylabel": "Compliance Rate (%)",
        },
    }

    config = {"figsize": (10, 6), "dpi": 300}
    output_path = Path("output/charts/test_compliance_chart.png")

    render_compliance_chart(data, config, output_path)
    print(f"✓ Compliance chart saved to {output_path}")


def test_heatmap():
    """Test heatmap generation."""
    print("\nTesting heatmap generation...")

    # Generate sample occupancy matrix (7 days x 24 hours)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = [f"{h:02d}:00" for h in range(24)]

    # Create random occupancy pattern
    matrix = np.random.rand(7, 24) * 100
    # Make weekdays 9-17 have higher occupancy
    for day in range(5):  # Mon-Fri
        matrix[day, 9:17] = 70 + np.random.rand(8) * 30

    data = {
        "title": "Weekly Occupancy Pattern",
        "data": {
            "matrix": matrix.tolist(),
            "y_labels": days,
            "x_labels": hours,
        },
        "styling": {
            "xlabel": "Hour of Day",
            "ylabel": "Day of Week",
            "colormap": "YlOrRd",
            "colorbar_label": "Occupancy (%)",
        },
    }

    config = {"figsize": (14, 6), "dpi": 300, "show_values": False}
    output_path = Path("output/charts/test_heatmap.png")

    render_heatmap(data, config, output_path)
    print(f"✓ Heatmap saved to {output_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Matplotlib Chart Generation")
    print("=" * 60)

    try:
        test_bar_chart()
        test_line_chart()
        test_compliance_chart()
        test_heatmap()

        print("\n" + "=" * 60)
        print("✓ All chart tests completed successfully!")
        print("=" * 60)
        print(f"\nCharts saved to: {Path('output/charts').absolute()}")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
