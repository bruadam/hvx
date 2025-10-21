"""Chart generation modules."""

# Plotly interactive charts
from core.reporting.charts.heatmap_chart import HeatmapChart
from core.reporting.charts.timeseries_chart import TimeseriesChart
from core.reporting.charts.bar_chart import BarChart
from core.reporting.charts.compliance_chart import ComplianceChart

# Matplotlib static charts
from core.reporting.charts.matplotlib_bar_chart import (
    render_bar_chart,
    render_grouped_bar_chart,
)
from core.reporting.charts.matplotlib_line_chart import (
    render_line_chart,
    render_multi_line_chart,
)
from core.reporting.charts.matplotlib_heatmap import (
    render_heatmap,
    render_correlation_matrix,
)
from core.reporting.charts.matplotlib_compliance_chart import (
    render_compliance_chart,
    render_performance_matrix,
)

__all__ = [
    # Plotly charts
    "HeatmapChart",
    "TimeseriesChart",
    "BarChart",
    "ComplianceChart",
    # Matplotlib charts
    "render_bar_chart",
    "render_grouped_bar_chart",
    "render_line_chart",
    "render_multi_line_chart",
    "render_heatmap",
    "render_correlation_matrix",
    "render_compliance_chart",
    "render_performance_matrix",
]
