"""Main report generator orchestrating template loading, chart generation, and rendering."""

from pathlib import Path
from typing import List, Optional, Dict, Any
import plotly.graph_objects as go

from core.domain.models.room import Room
from core.domain.models.building import Building
from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.enums.parameter_type import ParameterType
from core.analytics.engine.analysis_engine import AnalysisEngine
from core.analytics.aggregators.building_aggregator import BuildingAggregator
from core.analytics.aggregators.portfolio_aggregator import PortfolioAggregator
from core.reporting.template_engine import (
    TemplateLoader,
    TemplateValidator,
    ReportTemplate,
    ChartConfig,
)
from core.reporting.renderers.html_renderer import HTMLRenderer
from core.reporting.charts import (
    HeatmapChart,
    TimeseriesChart,
    BarChart,
    ComplianceChart,
)


class ReportGenerator:
    """
    Main report generator.

    Orchestrates the complete report generation process:
    1. Load and validate template
    2. Run required analytics
    3. Generate charts
    4. Render to HTML
    """

    def __init__(self, analysis_engine: Optional[AnalysisEngine] = None):
        """
        Initialize report generator.

        Args:
            analysis_engine: Optional analysis engine (creates default if not provided)
        """
        self.analysis_engine = analysis_engine or AnalysisEngine()
        self.building_aggregator = BuildingAggregator()
        self.portfolio_aggregator = PortfolioAggregator()

    def generate_from_template(
        self,
        template_path: Path,
        rooms: List[Room],
        building_name: str,
        output_path: Path,
    ) -> None:
        """
        Generate report from template file.

        Args:
            template_path: Path to YAML template
            rooms: List of room entities with data
            building_name: Name of building
            output_path: Output HTML file path

        Raises:
            ValueError: If template is invalid
        """
        # Load template
        template = TemplateLoader.load_from_file(template_path)

        # Validate template
        is_valid, errors = TemplateValidator.validate(template)
        if not is_valid:
            raise ValueError(f"Invalid template: {', '.join(errors)}")

        # Generate report
        self.generate_report(template, rooms, building_name, output_path)

    def generate_report(
        self,
        template: ReportTemplate,
        rooms: List[Room],
        building_name: str,
        output_path: Path,
    ) -> None:
        """
        Generate report from template object.

        Args:
            template: Report template configuration
            rooms: List of room entities with data
            building_name: Name of building
            output_path: Output HTML file path
        """
        # Step 1: Run analytics on all rooms
        room_analyses = self._analyze_rooms(rooms, template)

        # Step 2: Aggregate to building level if needed
        building_analysis = None
        if template.report_type in ["building", "portfolio"]:
            # Create Building object from rooms and building_name
            building = Building(
                id=building_name.lower().replace(" ", "_"),
                name=building_name,
            )
            # Add rooms directly to building (no need to assign to levels)
            building.add_rooms([room.id for room in rooms])
            building_analysis = self.building_aggregator.aggregate(
                building, room_analyses
            )

        # Step 3: Generate charts and render
        if template.report_type == "room":
            self._generate_room_report(template, room_analyses, output_path)
        elif template.report_type == "building":
            if building_analysis is None:
                raise ValueError("Building analysis is required for building reports")
            self._generate_building_report(
                template, building_analysis, room_analyses, output_path, rooms
            )
        elif template.report_type == "portfolio":
            # For portfolio, expecting multiple buildings
            # This is a simplified version - extend as needed
            building_analyses = [building_analysis] if building_analysis else []
            self._generate_portfolio_report(template, building_analyses, output_path)

    def generate_portfolio_report_multi_building(
        self,
        template: ReportTemplate,
        buildings_data: Dict[str, List[Room]],
        output_path: Path,
    ) -> None:
        """
        Generate portfolio report from multiple buildings.

        Args:
            template: Report template configuration
            buildings_data: Dict mapping building names to lists of rooms
            output_path: Output HTML file path
        """
        # Analyze each building
        building_analyses = []
        for building_name, rooms in buildings_data.items():
            room_analyses = self._analyze_rooms(rooms, template)
            # Create Building object for aggregation
            building = Building(
                id=building_name.lower().replace(" ", "_"),
                name=building_name,
            )
            building.add_rooms([room.id for room in rooms])
            building_analysis = self.building_aggregator.aggregate(
                building, room_analyses
            )
            building_analyses.append(building_analysis)

        # Generate portfolio report
        self._generate_portfolio_report(template, building_analyses, output_path)

    def _analyze_rooms(
        self, rooms: List[Room], template: ReportTemplate
    ) -> List[RoomAnalysis]:
        """Run analytics on all rooms based on template requirements."""
        room_analyses = []

        # Define tests based on template's compliance standard
        tests = self._get_tests_for_standard(
            template.compliance_standard, template.building_class
        )

        for room in rooms:
            analysis = self.analysis_engine.analyze_room(room, tests=tests)
            room_analyses.append(analysis)

        return room_analyses

    def _generate_room_report(
        self,
        template: ReportTemplate,
        room_analyses: List[RoomAnalysis],
        output_path: Path,
    ) -> None:
        """Generate room-level report."""
        renderer = HTMLRenderer(template)
        renderer.render_room_report(room_analyses, output_path)

    def _generate_building_report(
        self,
        template: ReportTemplate,
        building_analysis: BuildingAnalysis,
        room_analyses: List[RoomAnalysis],
        output_path: Path,
        rooms: Optional[List[Room]] = None,
    ) -> None:
        """Generate building-level report."""
        renderer = HTMLRenderer(template)
        renderer.render_building_report(building_analysis, room_analyses, output_path, rooms)

    def _generate_portfolio_report(
        self,
        template: ReportTemplate,
        building_analyses: List[BuildingAnalysis],
        output_path: Path,
    ) -> None:
        """Generate portfolio-level report."""
        renderer = HTMLRenderer(template)
        renderer.render_portfolio_report(building_analyses, output_path)

    def _get_tests_for_standard(
        self, standard: str, building_class: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Get test configurations for compliance standard.

        Args:
            standard: Compliance standard name
            building_class: Building class (e.g., 'II' for EN16798-1)

        Returns:
            List of test configurations
        """
        # Default tests for EN16798-1 Class II
        # This should be loaded from configuration files in production
        # Ensure standard is lowercase to match StandardType enum
        standard_lower = standard.lower()
        default_tests = [
            {
                "test_id": "temp_class_ii",
                "parameter": "temperature",
                "standard": standard_lower,
                "threshold": {
                    "lower": 20.0,
                    "upper": 24.0,
                },
                "config": {
                    "building_class": building_class or "II",
                    "season": "winter",
                },
            },
            {
                "test_id": "co2_class_ii",
                "parameter": "co2",
                "standard": standard_lower,
                "threshold": {
                    "upper": 800.0,
                },
                "config": {
                    "building_class": building_class or "II",
                },
            },
            {
                "test_id": "humidity_class_ii",
                "parameter": "humidity",
                "standard": standard_lower,
                "threshold": {
                    "lower": 30.0,
                    "upper": 60.0,
                },
                "config": {
                    "building_class": building_class or "II",
                },
            },
        ]

        return default_tests

    def generate_chart(
        self,
        chart_config: ChartConfig,
        room_analyses: Optional[List[RoomAnalysis]] = None,
        building_analysis: Optional[BuildingAnalysis] = None,
        building_analyses: Optional[List[BuildingAnalysis]] = None,
        room: Optional[Room] = None,
    ) -> Optional[go.Figure]:
        """
        Generate individual chart based on configuration.

        Args:
            chart_config: Chart configuration
            room_analyses: Optional list of room analyses
            building_analysis: Optional building analysis
            building_analyses: Optional list of building analyses
            room: Optional room entity (for timeseries charts)

        Returns:
            Plotly figure or None
        """
        chart_type = chart_config.type

        try:
            # Heatmap charts
            if chart_type == "heatmap_hourly_daily":
                if not room or not chart_config.parameters:
                    return None
                param = ParameterType(chart_config.parameters[0])
                return HeatmapChart.create_hourly_daily_heatmap(
                    room, param, season=chart_config.season, title=chart_config.title
                )

            elif chart_type == "heatmap_daily_monthly":
                if not room or not chart_config.parameters:
                    return None
                param = ParameterType(chart_config.parameters[0])
                return HeatmapChart.create_daily_monthly_heatmap(
                    room, param, year=chart_config.year, title=chart_config.title
                )

            elif chart_type == "heatmap_compliance":
                if not room or not chart_config.parameters or not room_analyses:
                    return None
                param = ParameterType(chart_config.parameters[0])
                # Get compliance data from room analysis
                room_analysis = next(
                    (ra for ra in room_analyses if ra.room_id == room.id), None
                )
                if not room_analysis:
                    return None
                # This requires compliance data as series - simplified for now
                return None

            # Timeseries charts
            elif chart_type == "timeseries_compliance":
                if not room or not chart_config.parameters or not room_analyses:
                    return None
                param = ParameterType(chart_config.parameters[0])
                room_analysis = next(
                    (ra for ra in room_analyses if ra.room_id == room.id), None
                )
                if not room_analysis or param.value not in room_analysis.compliance_results:
                    return None
                compliance_result = room_analysis.compliance_results[param.value]
                return TimeseriesChart.create_timeseries_with_compliance(
                    room,
                    param,
                    compliance_result,
                    season=chart_config.season,
                    title=chart_config.title,
                    show_threshold=chart_config.show_threshold,
                )

            elif chart_type == "timeseries_multi_parameter":
                if not room or not chart_config.parameters:
                    return None
                params = [ParameterType(p) for p in chart_config.parameters]
                return TimeseriesChart.create_multi_parameter_timeseries(
                    room, params, season=chart_config.season, title=chart_config.title
                )

            elif chart_type == "violation_timeline":
                if not room_analyses or not chart_config.parameters:
                    return None
                # Use first room's first parameter for demo
                room_analysis = room_analyses[0]
                param = ParameterType(chart_config.parameters[0])
                if param.value not in room_analysis.compliance_results:
                    return None
                compliance_result = room_analysis.compliance_results[param.value]
                return TimeseriesChart.create_violation_timeline(
                    compliance_result, room_analysis.room_name, title=chart_config.title
                )

            # Bar charts
            elif chart_type == "bar_room_comparison":
                if not room_analyses:
                    return None
                return BarChart.create_room_comparison_chart(
                    room_analyses,
                    metric=chart_config.metric or "compliance",
                    title=chart_config.title,
                    sort=chart_config.sort,
                    ascending=chart_config.ascending,
                    show_only_failing=chart_config.show_only_failing,
                    failing_threshold=chart_config.failing_threshold,
                )

            elif chart_type == "bar_building_comparison":
                if not building_analyses:
                    return None
                return BarChart.create_building_comparison_chart(
                    building_analyses, title=chart_config.title, sort=chart_config.sort
                )

            elif chart_type == "bar_test_comparison":
                if not room_analyses:
                    return None
                return BarChart.create_test_comparison_chart(
                    room_analyses[0],
                    title=chart_config.title,
                    show_only_failing=chart_config.show_only_failing,
                )

            elif chart_type == "bar_stacked_comparison":
                if not room_analyses:
                    return None
                return BarChart.create_stacked_comparison_chart(
                    room_analyses, title=chart_config.title
                )

            # Compliance charts
            elif chart_type == "compliance_matrix":
                if not room_analyses:
                    return None
                return ComplianceChart.create_compliance_matrix(
                    room_analyses, title=chart_config.title
                )

            elif chart_type == "compliance_gauge":
                if not building_analysis:
                    return None
                return ComplianceChart.create_compliance_gauge(
                    building_analysis.avg_compliance_rate, title=chart_config.title or "Compliance Gauge"
                )

            elif chart_type == "building_kpi_dashboard":
                if not building_analysis:
                    return None
                return ComplianceChart.create_building_kpi_dashboard(
                    building_analysis, title=chart_config.title
                )

            elif chart_type == "portfolio_overview":
                if not building_analyses:
                    return None
                return ComplianceChart.create_portfolio_overview(
                    building_analyses, title=chart_config.title
                )

        except Exception as e:
            print(f"Error generating chart {chart_type}: {e}")
            return None

        return None
