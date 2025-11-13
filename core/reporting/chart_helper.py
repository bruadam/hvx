"""Helper for generating and embedding charts in HTML reports."""

import base64
from io import BytesIO
from pathlib import Path
from typing import Any

from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.models.room_analysis import RoomAnalysis
from core.reporting.charts import (
    # Plotly charts
    BarChart,
    ComplianceChart,
    render_bar_chart,
    render_compliance_chart,
    render_line_chart,
)
from core.reporting.template_engine.report_template import ChartConfig


class ChartHelper:
    """Helper class for generating charts and embedding them in HTML."""

    @staticmethod
    def generate_chart_html(
        chart_config: ChartConfig,
        room_analyses: list[RoomAnalysis] | None = None,
        building_analysis: BuildingAnalysis | None = None,
        building_analyses: list[BuildingAnalysis] | None = None,
        output_dir: Path | None = None,
        use_matplotlib: bool = False,
    ) -> str:
        """
        Generate chart HTML based on configuration.

        Args:
            chart_config: Chart configuration
            room_analyses: Optional room analyses
            building_analysis: Optional building analysis
            building_analyses: Optional list of building analyses
            output_dir: Optional output directory for saving matplotlib charts
            use_matplotlib: Whether to use matplotlib (static) or plotly (interactive)

        Returns:
            HTML string containing the chart
        """
        if use_matplotlib:
            return ChartHelper._generate_matplotlib_chart(
                chart_config, room_analyses, building_analysis, building_analyses, output_dir
            )
        else:
            return ChartHelper._generate_plotly_chart(
                chart_config, room_analyses, building_analysis, building_analyses
            )

    @staticmethod
    def _generate_plotly_chart(
        chart_config: ChartConfig,
        room_analyses: list[RoomAnalysis] | None = None,
        building_analysis: BuildingAnalysis | None = None,
        building_analyses: list[BuildingAnalysis] | None = None,
    ) -> str:
        """Generate Plotly interactive chart."""
        fig = None

        try:
            if chart_config.type == "bar_room_comparison":
                if room_analyses:
                    fig = BarChart.create_room_comparison_chart(
                        room_analyses,
                        metric=chart_config.metric or "compliance",
                        title=chart_config.title,
                        sort=chart_config.sort,
                        ascending=chart_config.ascending,
                        show_only_failing=chart_config.show_only_failing,
                        failing_threshold=chart_config.failing_threshold,
                    )

            elif chart_config.type == "bar_building_comparison":
                if building_analyses:
                    fig = BarChart.create_building_comparison_chart(
                        building_analyses,
                        title=chart_config.title,
                        sort=chart_config.sort,
                    )

            elif chart_config.type == "compliance_matrix":
                if room_analyses:
                    fig = ComplianceChart.create_compliance_matrix(
                        room_analyses,
                        title=chart_config.title,
                    )

            elif chart_config.type == "compliance_gauge":
                if building_analysis:
                    fig = ComplianceChart.create_compliance_gauge(
                        building_analysis.avg_compliance_rate,
                        title=chart_config.title or "Compliance Gauge",
                    )

            elif chart_config.type == "building_kpi_dashboard":
                if building_analysis:
                    fig = ComplianceChart.create_building_kpi_dashboard(
                        building_analysis,
                        title=chart_config.title,
                    )

            elif chart_config.type == "portfolio_overview":
                if building_analyses:
                    fig = ComplianceChart.create_portfolio_overview(
                        building_analyses,
                        title=chart_config.title,
                    )

        except Exception as e:
            return f'<div class="chart-error">Error generating chart {chart_config.type}: {str(e)}</div>'

        if fig:
            return fig.to_html(include_plotlyjs=False, div_id=f"chart_{id(chart_config)}")
        else:
            return f'<div class="chart-placeholder">Chart type "{chart_config.type}" not yet implemented</div>'

    @staticmethod
    def _generate_matplotlib_chart(
        chart_config: ChartConfig,
        room_analyses: list[RoomAnalysis] | None = None,
        building_analysis: BuildingAnalysis | None = None,
        building_analyses: list[BuildingAnalysis] | None = None,
        output_dir: Path | None = None,
    ) -> str:
        """Generate Matplotlib static chart and embed as base64 image."""
        # Create a BytesIO buffer to save the image
        buffer = BytesIO()

        # Prepare data and config for matplotlib renderers
        data: dict[str, Any] = {}
        config: dict[str, Any] = {}

        try:
            if chart_config.type == "room_comparison_bar" and room_analyses:
                # Prepare data for bar chart
                data = {
                    "title": chart_config.title or "Room Comparison",
                    "data": {
                        "categories": [r.room_name for r in room_analyses],
                        "compliance_percentage": [r.overall_compliance_rate for r in room_analyses],
                    },
                    "styling": {
                        "xlabel": "Room",
                        "ylabel": "Compliance Rate (%)",
                        "threshold_line": 95.0,
                    },
                }
                # Save to buffer
                render_bar_chart(data, config, buffer)

            elif chart_config.type == "building_comparison_bar" and building_analyses:
                data = {
                    "title": chart_config.title or "Building Comparison",
                    "data": {
                        "categories": [b.building_name for b in building_analyses],
                        "compliance_rates": [b.avg_compliance_rate for b in building_analyses],
                    },
                    "styling": {
                        "xlabel": "Building",
                        "ylabel": "Compliance Rate (%)",
                    },
                }
                render_compliance_chart(data, config, buffer)

            elif chart_config.type == "compliance_overview" and room_analyses:
                # Group by parameter or test
                test_compliance = {}
                for room in room_analyses:
                    for test_id, result in room.compliance_results.items():
                        if test_id not in test_compliance:
                            test_compliance[test_id] = []
                        test_compliance[test_id].append(result.compliance_rate)

                categories = list(test_compliance.keys())
                compliance_rates = [
                    sum(rates) / len(rates) for rates in test_compliance.values()
                ]

                data = {
                    "title": chart_config.title or "Compliance Overview",
                    "data": {
                        "categories": categories,
                        "compliance_rates": compliance_rates,
                    },
                    "styling": {
                        "xlabel": "Test",
                        "ylabel": "Compliance Rate (%)",
                    },
                }
                render_compliance_chart(data, config, buffer)

            elif chart_config.type == "timeseries" and room_analyses:
                # Get timeseries data from first room
                room = room_analyses[0]
                parameter = chart_config.options.get("parameter", "temperature")

                if room.room.timeseries_data and parameter in room.room.timeseries_data:
                    ts_data = room.room.timeseries_data[parameter]
                    data = {
                        "title": chart_config.title or f"{parameter.title()} Over Time",
                        "data": {
                            "timestamps": ts_data.timestamps,
                            "values": ts_data.values,
                        },
                        "styling": {
                            "xlabel": "Time",
                            "ylabel": parameter.title(),
                        },
                    }
                    render_line_chart(data, config, buffer)

            # Convert buffer to base64
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            buffer.close()

            # Return HTML img tag with embedded base64 image
            return f'<img src="data:image/png;base64,{img_base64}" alt="{chart_config.title}" class="chart-image" />'

        except Exception as e:
            return f'<div class="chart-error">Error generating chart: {str(e)}</div>'

    @staticmethod
    def save_matplotlib_chart_to_file(
        chart_config: ChartConfig,
        output_path: Path,
        room_analyses: list[RoomAnalysis] | None = None,
        building_analysis: BuildingAnalysis | None = None,
        building_analyses: list[BuildingAnalysis] | None = None,
    ) -> None:
        """
        Save matplotlib chart to file.

        Args:
            chart_config: Chart configuration
            output_path: Output file path
            room_analyses: Optional room analyses
            building_analysis: Optional building analysis
            building_analyses: Optional list of building analyses
        """
        data: dict[str, Any] = {}
        config: dict[str, Any] = {}

        if chart_config.type == "room_comparison_bar" and room_analyses:
            data = {
                "title": chart_config.title or "Room Comparison",
                "data": {
                    "categories": [r.room_name for r in room_analyses],
                    "compliance_percentage": [r.overall_compliance_rate for r in room_analyses],
                },
                "styling": {
                    "xlabel": "Room",
                    "ylabel": "Compliance Rate (%)",
                    "threshold_line": 95.0,
                },
            }
            render_bar_chart(data, config, output_path)

        elif chart_config.type == "building_comparison_bar" and building_analyses:
            data = {
                "title": chart_config.title or "Building Comparison",
                "data": {
                    "categories": [b.building_name for b in building_analyses],
                    "compliance_rates": [b.avg_compliance_rate for b in building_analyses],
                },
                "styling": {
                    "xlabel": "Building",
                    "ylabel": "Compliance Rate (%)",
                },
            }
            render_compliance_chart(data, config, output_path)
