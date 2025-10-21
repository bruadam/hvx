"""HTML report renderer."""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import plotly.graph_objects as go

from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.value_objects.recommendation import Recommendation
from core.reporting.template_engine.report_template import (
    ReportTemplate,
    SectionConfig,
    ChartConfig,
)
from core.reporting.chart_helper import ChartHelper


class HTMLRenderer:
    """Render reports to HTML format."""

    def __init__(self, template: ReportTemplate):
        """
        Initialize renderer with template.

        Args:
            template: Report template configuration
        """
        self.template = template
        self.rooms_data = {}

    def render_room_report(
        self,
        room_analyses: List[RoomAnalysis],
        output_path: Path,
    ) -> None:
        """
        Render room-level report.

        Args:
            room_analyses: List of room analyses
            output_path: Output HTML file path
        """
        html_parts = []

        # Header
        html_parts.append(self._render_header())

        # Title section
        html_parts.append(self._render_title_section())

        # Filter rooms based on template config
        filtered_rooms = self._filter_rooms(room_analyses)

        # Render sections
        for section in self.template.sections:
            section_html = self._render_section(section, filtered_rooms)
            if section_html:
                html_parts.append(section_html)

        # Footer
        html_parts.append(self._render_footer())

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))

    def render_building_report(
        self,
        building_analysis: BuildingAnalysis,
        room_analyses: List[RoomAnalysis],
        output_path: Path,
        rooms: Optional[List] = None,
    ) -> None:
        """
        Render building-level report.

        Args:
            building_analysis: Building analysis result
            room_analyses: List of room analyses
            output_path: Output HTML file path
            rooms: Optional list of Room entities with time series data
        """
        self.rooms_data = {room.id: room for room in rooms} if rooms else {}

        html_parts = []

        # Header
        html_parts.append(self._render_header())

        # Title section
        html_parts.append(self._render_title_section())

        # Building KPI summary
        html_parts.append(self._render_building_summary(building_analysis))

        # Filter rooms based on template config
        filtered_rooms = self._filter_rooms(room_analyses)

        # Render sections
        for section in self.template.sections:
            section_html = self._render_section(
                section, filtered_rooms, building_analysis
            )
            if section_html:
                html_parts.append(section_html)

        # Footer
        html_parts.append(self._render_footer())

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))

    def render_portfolio_report(
        self,
        building_analyses: List[BuildingAnalysis],
        output_path: Path,
    ) -> None:
        """
        Render portfolio-level report.

        Args:
            building_analyses: List of building analyses
            output_path: Output HTML file path
        """
        html_parts = []

        # Header
        html_parts.append(self._render_header())

        # Title section
        html_parts.append(self._render_title_section())

        # Portfolio summary
        html_parts.append(self._render_portfolio_summary(building_analyses))

        # Render sections
        for section in self.template.sections:
            section_html = self._render_section(
                section, building_analyses=building_analyses
            )
            if section_html:
                html_parts.append(section_html)

        # Footer
        html_parts.append(self._render_footer())

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))

    def _filter_rooms(self, room_analyses: List[RoomAnalysis]) -> List[RoomAnalysis]:
        """Filter and sort rooms based on template configuration."""
        filter_config = self.template.room_filter
        rooms = list(room_analyses)

        # Apply filtering
        if filter_config.mode == "failing":
            rooms = [
                r
                for r in rooms
                if r.overall_compliance_rate < filter_config.compliance_threshold
            ]
        elif filter_config.mode == "top_n":
            rooms = sorted(
                rooms,
                key=lambda r: self._get_sort_value(r, filter_config.sort_by),
                reverse=not filter_config.ascending,
            )[: filter_config.n]
        elif filter_config.mode == "bottom_n":
            rooms = sorted(
                rooms,
                key=lambda r: self._get_sort_value(r, filter_config.sort_by),
                reverse=filter_config.ascending,
            )[: filter_config.n]
        else:  # all
            rooms = sorted(
                rooms,
                key=lambda r: self._get_sort_value(r, filter_config.sort_by),
                reverse=not filter_config.ascending,
            )

        return rooms

    @staticmethod
    def _get_sort_value(room: RoomAnalysis, sort_by: str) -> float:
        """Get sort value from room analysis."""
        if sort_by == "compliance":
            return room.overall_compliance_rate
        elif sort_by == "quality":
            return room.data_quality_score
        elif sort_by == "violations":
            return room.total_violations
        else:  # name
            return 0  # Name sorting handled separately

    def _render_section(
        self,
        section: SectionConfig,
        room_analyses: Optional[List[RoomAnalysis]] = None,
        building_analysis: Optional[BuildingAnalysis] = None,
        building_analyses: Optional[List[BuildingAnalysis]] = None,
    ) -> str:
        """Render individual section based on type."""
        if section.type == "summary":
            return self._render_summary_section(section, room_analyses)
        elif section.type == "kpi_cards":
            return self._render_kpi_cards(section, room_analyses, building_analysis)
        elif section.type == "chart":
            return self._render_chart_section(
                section, room_analyses, building_analysis, building_analyses
            )
        elif section.type == "table":
            return self._render_table_section(section, room_analyses)
        elif section.type == "recommendations":
            return self._render_recommendations_section(
                section, room_analyses, building_analysis
            )
        elif section.type == "executive_summary":
            return self._render_executive_summary(section, building_analyses)
        elif section.type == "room_details":
            return self._render_room_details_section(section, room_analyses)
        elif section.type == "building_statistics":
            return self._render_building_statistics(section, building_analysis, room_analyses)

        return ""

    def _render_header(self) -> str:
        """Render HTML header with styles."""
        theme_styles = self._get_theme_styles()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.template.title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        {theme_styles}
    </style>
</head>
<body>
    <div class="container">
"""

    def _render_footer(self) -> str:
        """Render HTML footer."""
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        author = self.template.author or "IEQ Analytics"

        return f"""
    </div>
    <footer class="footer">
        <p>Generated by {author} on {generated_at}</p>
        <p>Standard: {self.template.compliance_standard}</p>
    </footer>
</body>
</html>
"""

    def _render_title_section(self) -> str:
        """Render report title section."""
        description = (
            f'<p class="description">{self.template.description}</p>'
            if self.template.description
            else ""
        )

        return f"""
        <header class="report-header">
            <h1>{self.template.title}</h1>
            {description}
        </header>
"""

    def _render_building_summary(self, building: BuildingAnalysis) -> str:
        """Render building summary section."""
        grade_class = self._get_grade_class(building.compliance_grade)

        return f"""
        <section class="building-summary">
            <h2>{building.building_name} - Overview</h2>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <h3>Compliance Rate</h3>
                    <div class="kpi-value">{building.avg_compliance_rate:.1f}%</div>
                    <div class="kpi-label {grade_class}">Grade: {building.compliance_grade}</div>
                </div>
                <div class="kpi-card">
                    <h3>Data Quality</h3>
                    <div class="kpi-value">{building.avg_quality_score:.1f}%</div>
                </div>
                <div class="kpi-card">
                    <h3>Rooms Analyzed</h3>
                    <div class="kpi-value">{building.room_count}</div>
                </div>
                <div class="kpi-card">
                    <h3>Total Violations</h3>
                    <div class="kpi-value">{building.total_violations}</div>
                </div>
            </div>
        </section>
"""

    def _render_portfolio_summary(
        self, buildings: List[BuildingAnalysis]
    ) -> str:
        """Render portfolio summary section."""
        total_rooms = sum(b.room_count for b in buildings)
        avg_compliance = (
            sum(b.avg_compliance_rate * b.room_count for b in buildings) / total_rooms
            if total_rooms > 0
            else 0
        )
        total_violations = sum(b.total_violations for b in buildings)

        return f"""
        <section class="portfolio-summary">
            <h2>Portfolio Overview</h2>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <h3>Buildings</h3>
                    <div class="kpi-value">{len(buildings)}</div>
                </div>
                <div class="kpi-card">
                    <h3>Total Rooms</h3>
                    <div class="kpi-value">{total_rooms}</div>
                </div>
                <div class="kpi-card">
                    <h3>Avg Compliance</h3>
                    <div class="kpi-value">{avg_compliance:.1f}%</div>
                </div>
                <div class="kpi-card">
                    <h3>Total Violations</h3>
                    <div class="kpi-value">{total_violations}</div>
                </div>
            </div>
        </section>
"""

    def _render_chart_section(
        self,
        section: SectionConfig,
        room_analyses: Optional[List[RoomAnalysis]] = None,
        building_analysis: Optional[BuildingAnalysis] = None,
        building_analyses: Optional[List[BuildingAnalysis]] = None,
    ) -> str:
        """Render chart section."""
        if not section.chart:
            return ""

        title = section.title or section.chart.title or "Chart"
        description = (
            f'<p class="section-description">{section.description}</p>'
            if section.description
            else ""
        )

        # Determine whether to use matplotlib or plotly (default to plotly)
        use_matplotlib = False  # Default to Plotly

        # Generate chart HTML using ChartHelper
        chart_html = ChartHelper.generate_chart_html(
            section.chart,
            room_analyses=room_analyses,
            building_analysis=building_analysis,
            building_analyses=building_analyses,
            use_matplotlib=use_matplotlib,
        )

        return f"""
        <section class="chart-section">
            <h2>{title}</h2>
            {description}
            <div class="chart-container">
                {chart_html}
            </div>
        </section>
"""

    def _render_summary_section(
        self, section: SectionConfig, room_analyses: Optional[List[RoomAnalysis]]
    ) -> str:
        """Render summary section."""
        if not room_analyses:
            return ""

        avg_compliance = sum(r.overall_compliance_rate for r in room_analyses) / len(
            room_analyses
        )
        failing_rooms = [
            r
            for r in room_analyses
            if r.overall_compliance_rate < self.template.room_filter.compliance_threshold
        ]

        return f"""
        <section class="summary-section">
            <h2>{section.title or "Summary"}</h2>
            <div class="summary-content">
                <p><strong>Total Rooms:</strong> {len(room_analyses)}</p>
                <p><strong>Average Compliance:</strong> {avg_compliance:.1f}%</p>
                <p><strong>Failing Rooms:</strong> {len(failing_rooms)}</p>
            </div>
        </section>
"""

    def _render_kpi_cards(
        self,
        section: SectionConfig,
        room_analyses: Optional[List[RoomAnalysis]],
        building_analysis: Optional[BuildingAnalysis],
    ) -> str:
        """Render KPI cards section."""
        # Use building analysis if available, otherwise aggregate from rooms
        if building_analysis:
            return self._render_building_summary(building_analysis)
        elif room_analyses:
            # Aggregate from rooms
            avg_compliance = sum(r.overall_compliance_rate for r in room_analyses) / len(
                room_analyses
            )
            avg_quality = sum(r.data_quality_score for r in room_analyses) / len(
                room_analyses
            )
            total_violations = sum(r.total_violations for r in room_analyses)

            return f"""
        <section class="kpi-section">
            <h2>{section.title or "Key Performance Indicators"}</h2>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <h3>Compliance</h3>
                    <div class="kpi-value">{avg_compliance:.1f}%</div>
                </div>
                <div class="kpi-card">
                    <h3>Data Quality</h3>
                    <div class="kpi-value">{avg_quality:.1f}%</div>
                </div>
                <div class="kpi-card">
                    <h3>Total Violations</h3>
                    <div class="kpi-value">{total_violations}</div>
                </div>
            </div>
        </section>
"""
        return ""

    def _render_table_section(
        self, section: SectionConfig, room_analyses: Optional[List[RoomAnalysis]]
    ) -> str:
        """Render table section with room data."""
        if not room_analyses:
            return ""

        rows = []
        for room in room_analyses:
            grade_class = self._get_grade_class(
                self._compliance_to_grade(room.overall_compliance_rate)
            )
            rows.append(
                f"""
                <tr>
                    <td>{room.room_name}</td>
                    <td class="{grade_class}">{room.overall_compliance_rate:.1f}%</td>
                    <td>{room.data_quality_score:.1f}%</td>
                    <td>{room.total_violations}</td>
                </tr>
            """
            )

        return f"""
        <section class="table-section">
            <h2>{section.title or "Room Details"}</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Room</th>
                        <th>Compliance</th>
                        <th>Quality</th>
                        <th>Violations</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </section>
"""

    def _render_recommendations_section(
        self,
        section: SectionConfig,
        room_analyses: Optional[List[RoomAnalysis]],
        building_analysis: Optional[BuildingAnalysis],
    ) -> str:
        """Render recommendations section."""
        recommendations: List[Recommendation] = []

        if building_analysis and building_analysis.recommendations:
            recommendations = building_analysis.recommendations[
                : section.max_recommendations
            ]
        elif room_analyses:
            # Collect recommendations from rooms
            for room in room_analyses:
                recommendations.extend(room.recommendations)
            recommendations = recommendations[: section.max_recommendations]

        if not recommendations:
            return ""

        rec_items = []
        for rec in recommendations:
            # rec is now a Recommendation object with title, description, and priority
            priority = rec.priority.value if hasattr(rec.priority, 'value') else str(rec.priority)
            title = rec.title
            description = rec.description

            rec_items.append(
                f'<li class="recommendation-item priority-{priority}">'
                f"<strong>{title}</strong>: {description}</li>"
            )

        rec_items_html = "".join(rec_items)

        return f"""
        <section class="recommendations-section">
            <h2>{section.title or "Recommendations"}</h2>
            <ul class="recommendations-list">
                {rec_items_html}
            </ul>
        </section>
"""

    def _render_executive_summary(
        self, section: SectionConfig, building_analyses: Optional[List[BuildingAnalysis]]
    ) -> str:
        """Render executive summary for portfolio."""
        if not building_analyses:
            return ""

        best_building = max(building_analyses, key=lambda b: b.avg_compliance_rate)
        worst_building = min(building_analyses, key=lambda b: b.avg_compliance_rate)

        return f"""
        <section class="executive-summary">
            <h2>{section.title or "Executive Summary"}</h2>
            <div class="summary-content">
                <p><strong>Best Performing:</strong> {best_building.building_name}
                ({best_building.avg_compliance_rate:.1f}%)</p>
                <p><strong>Needs Attention:</strong> {worst_building.building_name}
                ({worst_building.avg_compliance_rate:.1f}%)</p>
            </div>
        </section>
"""

    def _render_room_details_section(
        self, section: SectionConfig, room_analyses: Optional[List[RoomAnalysis]]
    ) -> str:
        """Render detailed section for each room with individual charts and metrics."""
        if not room_analyses:
            return ""

        html_parts = []
        html_parts.append(f"""
        <section class="room-details-section">
            <h2>{section.title or "Individual Room Analysis"}</h2>
            <p class="section-description">{section.description or "Detailed analysis for each room"}</p>
        """)

        # Loop through each room
        for room_analysis in room_analyses:
            grade_class = self._get_grade_class(
                self._compliance_to_grade(room_analysis.overall_compliance_rate)
            )

            html_parts.append(f"""
            <div class="room-detail-card">
                <h3 class="room-name">{room_analysis.room_name}</h3>

                <div class="room-kpi-grid">
                    <div class="room-kpi-item">
                        <span class="room-kpi-label">Compliance Rate</span>
                        <span class="room-kpi-value {grade_class}">{room_analysis.overall_compliance_rate:.1f}%</span>
                    </div>
                    <div class="room-kpi-item">
                        <span class="room-kpi-label">Data Quality</span>
                        <span class="room-kpi-value">{room_analysis.data_quality_score:.1f}%</span>
                    </div>
                    <div class="room-kpi-item">
                        <span class="room-kpi-label">Total Violations</span>
                        <span class="room-kpi-value">{room_analysis.total_violations}</span>
                    </div>
                </div>

                <div class="room-compliance-details">
                    <h4>Compliance Results by Parameter</h4>
                    <table class="room-compliance-table">
                        <thead>
                            <tr>
                                <th>Parameter</th>
                                <th>Compliance Rate</th>
                                <th>Violations</th>
                            </tr>
                        </thead>
                        <tbody>
            """)

            # Add compliance details for each parameter
            for param, result in room_analysis.compliance_results.items():
                param_grade_class = self._get_grade_class(
                    self._compliance_to_grade(result.compliance_rate)
                )
                html_parts.append(f"""
                            <tr>
                                <td>{param.replace('_', ' ').title()}</td>
                                <td class="{param_grade_class}">{result.compliance_rate:.1f}%</td>
                                <td>{result.violation_count}</td>
                            </tr>
                """)

            html_parts.append("""
                        </tbody>
                    </table>
                </div>
            """)

            # Add EN16798-1 Category Distribution Table
            category_tables = self._render_category_distribution_table(room_analysis)
            if category_tables:
                html_parts.append(category_tables)

            # Add Parameter Statistics Table
            param_stats_table = self._render_parameter_statistics_table(room_analysis)
            if param_stats_table:
                html_parts.append(param_stats_table)

            html_parts.append("""
                <!-- Room-specific charts will be added here by chart sections -->
            </div>
            """)

        html_parts.append("</section>")
        return "\n".join(html_parts)

    def _render_category_distribution_table(
        self, room_analysis: RoomAnalysis
    ) -> str:
        """Render EN16798-1 category distribution table for a room."""
        html_parts = []

        html_parts.append("""
                <div class="category-distribution">
                    <h4>EN16798-1 Category Distribution</h4>
                    <table class="category-table">
                        <thead>
                            <tr>
                                <th>Parameter</th>
                                <th>Cat I (%)</th>
                                <th>Cat II (%)</th>
                                <th>Cat III (%)</th>
                                <th>Cat IV (%)</th>
                                <th>Outside (%)</th>
                            </tr>
                        </thead>
                        <tbody>
        """)

        # Get category distribution from room analysis
        # Get unique parameters from compliance results
        parameters_seen = set()

        for test_id, result in room_analysis.compliance_results.items():
            # Extract parameter from test result
            # The result should have parameter info
            param = result.parameter if hasattr(result, 'parameter') else None

            if not param or param in parameters_seen:
                continue

            parameters_seen.add(param)
            param_name = param.replace('_', ' ').title()

            # Get category counts if available
            category_dist = self._calculate_category_distribution(room_analysis, param)

            if category_dist:
                html_parts.append(f"""
                            <tr>
                                <td><strong>{param_name}</strong></td>
                                <td class="cat-i">{category_dist.get('I', 0):.1f}%</td>
                                <td class="cat-ii">{category_dist.get('II', 0):.1f}%</td>
                                <td class="cat-iii">{category_dist.get('III', 0):.1f}%</td>
                                <td class="cat-iv">{category_dist.get('IV', 0):.1f}%</td>
                                <td class="cat-outside">{category_dist.get('Outside', 0):.1f}%</td>
                            </tr>
                """)

        html_parts.append("""
                        </tbody>
                    </table>
                </div>
        """)

        return "\n".join(html_parts)

    def _render_parameter_statistics_table(
        self, room_analysis: RoomAnalysis
    ) -> str:
        """Render parameter statistics table showing min, max, avg values."""
        # Get parameter statistics
        param_stats = self._calculate_parameter_statistics(room_analysis)

        if not param_stats:
            return ""

        html_parts = []

        html_parts.append("""
                <div class="parameter-statistics">
                    <h4>Parameter Statistics</h4>
                    <table class="stats-table">
                        <thead>
                            <tr>
                                <th>Parameter</th>
                                <th>Minimum</th>
                                <th>Maximum</th>
                                <th>Average</th>
                                <th>Unit</th>
                            </tr>
                        </thead>
                        <tbody>
        """)

        # Render statistics rows
        for param_name, stats in param_stats.items():
            display_name = param_name.replace('_', ' ').title()
            html_parts.append(f"""
                            <tr>
                                <td><strong>{display_name}</strong></td>
                                <td>{stats['min']:.2f}</td>
                                <td>{stats['max']:.2f}</td>
                                <td>{stats['avg']:.2f}</td>
                                <td>{stats['unit']}</td>
                            </tr>
            """)

        html_parts.append("""
                        </tbody>
                    </table>
                </div>
        """)

        return "\n".join(html_parts)

    def _calculate_category_distribution(
        self, room_analysis: RoomAnalysis, parameter: str
    ) -> Dict[str, float]:
        """Calculate EN16798-1 category distribution percentages for a parameter."""
        # Get room from rooms_data using room_id
        if not hasattr(self, 'rooms_data') or not self.rooms_data:
            return {}

        room = self.rooms_data.get(room_analysis.room_id)
        if not room:
            return {}

        # Check if time_series_data exists and is not None
        if not hasattr(room, 'time_series_data') or room.time_series_data is None:
            return {}

        import pandas as pd

        # Handle DataFrame time series data
        if isinstance(room.time_series_data, pd.DataFrame):
            if parameter not in room.time_series_data.columns:
                return {}

            values = room.time_series_data[parameter].dropna().values
        else:
            # Handle dict of TimeSeriesData objects
            if parameter not in room.time_series_data:
                return {}

            ts_data = room.time_series_data[parameter]
            if ts_data is None or len(ts_data.values) == 0:
                return {}
            values = ts_data.values

        if len(values) == 0:
            return {}

        # Get EN16798-1 thresholds for this parameter
        thresholds = self._get_en16798_thresholds(parameter)

        if not thresholds:
            return {}

        # Count values in each category
        total_count = len(values)
        category_counts = {'I': 0, 'II': 0, 'III': 0, 'IV': 0, 'Outside': 0}

        for value in values:
            if value is None:
                continue

            category = self._classify_value_to_category(value, thresholds, parameter)
            if category in category_counts:
                category_counts[category] += 1

        # Convert to percentages
        category_percentages = {
            cat: (count / total_count * 100) if total_count > 0 else 0
            for cat, count in category_counts.items()
        }

        return category_percentages

    def _get_en16798_thresholds(self, parameter: str) -> Dict[str, Any]:
        """Get EN16798-1 thresholds for a parameter."""
        # Simplified thresholds - in production, load from standards config
        thresholds = {
            'temperature': {
                'I': {'lower': 21.0, 'upper': 23.0},
                'II': {'lower': 20.0, 'upper': 24.0},
                'III': {'lower': 19.0, 'upper': 25.0},
                'IV': {'lower': 18.0, 'upper': 26.0},
            },
            'co2': {
                'I': {'upper': 550},
                'II': {'upper': 800},
                'III': {'upper': 1350},
                'IV': {'upper': 1350},
            },
            'humidity': {
                'I': {'lower': 30, 'upper': 50},
                'II': {'lower': 25, 'upper': 60},
                'III': {'lower': 20, 'upper': 70},
                'IV': {'lower': 20, 'upper': 70},
            },
        }

        return thresholds.get(parameter, {})

    def _classify_value_to_category(
        self, value: float, thresholds: Dict[str, Any], parameter: str
    ) -> str:
        """Classify a value into EN16798-1 category."""
        # Check Category I (most strict)
        if 'I' in thresholds:
            cat_i = thresholds['I']
            if parameter in ['temperature', 'humidity']:
                if cat_i.get('lower', float('-inf')) <= value <= cat_i.get('upper', float('inf')):
                    return 'I'
            elif parameter == 'co2':
                if value <= cat_i.get('upper', float('inf')):
                    return 'I'

        # Check Category II
        if 'II' in thresholds:
            cat_ii = thresholds['II']
            if parameter in ['temperature', 'humidity']:
                if cat_ii.get('lower', float('-inf')) <= value <= cat_ii.get('upper', float('inf')):
                    return 'II'
            elif parameter == 'co2':
                if value <= cat_ii.get('upper', float('inf')):
                    return 'II'

        # Check Category III
        if 'III' in thresholds:
            cat_iii = thresholds['III']
            if parameter in ['temperature', 'humidity']:
                if cat_iii.get('lower', float('-inf')) <= value <= cat_iii.get('upper', float('inf')):
                    return 'III'
            elif parameter == 'co2':
                if value <= cat_iii.get('upper', float('inf')):
                    return 'III'

        # Check Category IV
        if 'IV' in thresholds:
            cat_iv = thresholds['IV']
            if parameter in ['temperature', 'humidity']:
                if cat_iv.get('lower', float('-inf')) <= value <= cat_iv.get('upper', float('inf')):
                    return 'IV'
            elif parameter == 'co2':
                if value <= cat_iv.get('upper', float('inf')):
                    return 'IV'

        # If not in any category, it's outside
        return 'Outside'

    def _calculate_parameter_statistics(
        self, room_analysis: RoomAnalysis
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate min, max, avg statistics for each parameter."""
        stats = {}

        # Get room from rooms_data using room_id
        if not hasattr(self, 'rooms_data') or not self.rooms_data:
            return stats

        room = self.rooms_data.get(room_analysis.room_id)
        if not room:
            return stats

        if not hasattr(room, 'time_series_data') or room.time_series_data is None:
            return stats

        import pandas as pd

        # Define units for each parameter
        units = {
            'temperature': '°C',
            'co2': 'ppm',
            'humidity': '%RH',
            'pm25': 'µg/m³',
            'pm10': 'µg/m³',
            'voc': 'ppb',
        }

        # Handle DataFrame time series data
        if isinstance(room.time_series_data, pd.DataFrame):
            for param_name in room.time_series_data.columns:
                series = room.time_series_data[param_name].dropna()

                if len(series) == 0:
                    continue

                stats[param_name] = {
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'avg': float(series.mean()),
                    'unit': units.get(param_name, ''),
                }
        else:
            # Handle dict of TimeSeriesData objects
            for param_name, ts_data in room.time_series_data.items():
                if ts_data is None or len(ts_data.values) == 0:
                    continue

                # Filter out None values
                valid_values = [v for v in ts_data.values if v is not None]

                if not valid_values:
                    continue

                stats[param_name] = {
                    'min': min(valid_values),
                    'max': max(valid_values),
                    'avg': sum(valid_values) / len(valid_values),
                    'unit': units.get(param_name, ''),
                }

        return stats

    def _render_building_statistics(
        self,
        section: SectionConfig,
        building_analysis: Optional[BuildingAnalysis],
        room_analyses: Optional[List[RoomAnalysis]],
    ) -> str:
        """Render comprehensive building-level statistics."""
        if not building_analysis and not room_analyses:
            return ""

        # Calculate statistics
        if building_analysis:
            avg_compliance = building_analysis.avg_compliance_rate
            avg_quality = building_analysis.avg_quality_score
            total_violations = building_analysis.total_violations
            room_count = building_analysis.room_count
            grade = building_analysis.compliance_grade
            grade_class = self._get_grade_class(grade)
        elif room_analyses:
            avg_compliance = sum(r.overall_compliance_rate for r in room_analyses) / len(room_analyses)
            avg_quality = sum(r.data_quality_score for r in room_analyses) / len(room_analyses)
            total_violations = sum(r.total_violations for r in room_analyses)
            room_count = len(room_analyses)
            grade = self._compliance_to_grade(avg_compliance)
            grade_class = self._get_grade_class(grade)
        else:
            return ""

        # Calculate additional statistics
        passing_rooms = len([r for r in room_analyses if r.overall_compliance_rate >= 95]) if room_analyses else 0
        failing_rooms = room_count - passing_rooms

        # Calculate parameter-specific statistics
        param_stats = {}
        if room_analyses:
            for room in room_analyses:
                for param, result in room.compliance_results.items():
                    if param not in param_stats:
                        param_stats[param] = {
                            'total_compliance': 0,
                            'total_violations': 0,
                            'count': 0
                        }
                    param_stats[param]['total_compliance'] += result.compliance_rate
                    param_stats[param]['total_violations'] += result.violation_count
                    param_stats[param]['count'] += 1

        html_parts = []
        html_parts.append(f"""
        <section class="building-statistics-section">
            <h2>{section.title or "Building Statistics"}</h2>
            <p class="section-description">{section.description or "Comprehensive statistics for the entire building"}</p>

            <div class="statistics-grid">
                <div class="stat-category">
                    <h3>Overall Performance</h3>
                    <div class="stat-items">
                        <div class="stat-item">
                            <span class="stat-label">Overall Compliance Grade</span>
                            <span class="stat-value {grade_class}">{grade}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Average Compliance Rate</span>
                            <span class="stat-value">{avg_compliance:.2f}%</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Average Data Quality</span>
                            <span class="stat-value">{avg_quality:.2f}%</span>
                        </div>
                    </div>
                </div>

                <div class="stat-category">
                    <h3>Room Summary</h3>
                    <div class="stat-items">
                        <div class="stat-item">
                            <span class="stat-label">Total Rooms</span>
                            <span class="stat-value">{room_count}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Passing Rooms (≥95%)</span>
                            <span class="stat-value grade-a">{passing_rooms}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Failing Rooms (&lt;95%)</span>
                            <span class="stat-value grade-d">{failing_rooms}</span>
                        </div>
                    </div>
                </div>

                <div class="stat-category">
                    <h3>Violations</h3>
                    <div class="stat-items">
                        <div class="stat-item">
                            <span class="stat-label">Total Violations</span>
                            <span class="stat-value">{total_violations}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Avg Violations per Room</span>
                            <span class="stat-value">{total_violations / room_count:.1f}</span>
                        </div>
                    </div>
                </div>
        """)

        # Add parameter-specific statistics
        if param_stats:
            html_parts.append("""
                <div class="stat-category full-width">
                    <h3>Parameter-Specific Performance</h3>
                    <table class="parameter-stats-table">
                        <thead>
                            <tr>
                                <th>Parameter</th>
                                <th>Avg Compliance</th>
                                <th>Total Violations</th>
                                <th>Rooms Tested</th>
                            </tr>
                        </thead>
                        <tbody>
            """)

            for param, stats in param_stats.items():
                avg_param_compliance = stats['total_compliance'] / stats['count']
                param_grade = self._compliance_to_grade(avg_param_compliance)
                param_grade_class = self._get_grade_class(param_grade)

                html_parts.append(f"""
                            <tr>
                                <td>{param.replace('_', ' ').title()}</td>
                                <td class="{param_grade_class}">{avg_param_compliance:.1f}%</td>
                                <td>{stats['total_violations']}</td>
                                <td>{stats['count']}</td>
                            </tr>
                """)

            html_parts.append("""
                        </tbody>
                    </table>
                </div>
            """)

        html_parts.append("""
            </div>
        </section>
        """)

        return "\n".join(html_parts)

    def _get_theme_styles(self) -> str:
        """Get CSS styles based on theme."""
        base_styles = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .report-header {
            background: white;
            padding: 40px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .report-header h1 {
            font-size: 2.5em;
            color: #1a1a1a;
            margin-bottom: 10px;
        }

        .description {
            font-size: 1.1em;
            color: #666;
        }

        section {
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        h2 {
            font-size: 1.8em;
            color: #1a1a1a;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .kpi-card {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            border: 1px solid #e0e0e0;
        }

        .kpi-card h3 {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .kpi-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #1a1a1a;
            margin: 10px 0;
        }

        .kpi-label {
            font-size: 1.1em;
            font-weight: 600;
            padding: 5px 10px;
            border-radius: 4px;
            display: inline-block;
        }

        .grade-a { background: #C8E6C9; color: #2E7D32; }
        .grade-b { background: #FFF9C4; color: #F57C00; }
        .grade-c { background: #FFE0B2; color: #E65100; }
        .grade-d { background: #FFCDD2; color: #C62828; }
        .grade-f { background: #FFCDD2; color: #C62828; }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        .data-table th {
            background: #f5f5f5;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            font-size: 0.9em;
        }

        .data-table tr:hover {
            background: #f9f9f9;
        }

        .recommendations-list {
            list-style: none;
            margin-top: 20px;
        }

        .recommendation-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
            border-left: 4px solid #2E7D32;
        }

        .recommendation-item.priority-high {
            border-left-color: #C62828;
            background: #FFEBEE;
        }

        .recommendation-item.priority-medium {
            border-left-color: #F57C00;
            background: #FFF3E0;
        }

        .recommendation-item.priority-low {
            border-left-color: #2E7D32;
            background: #E8F5E9;
        }

        .chart-container {
            margin-top: 20px;
            min-height: 400px;
        }

        .chart-image {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
        }

        .chart-placeholder {
            background: #f5f5f5;
            padding: 40px;
            text-align: center;
            border: 2px dashed #ddd;
            border-radius: 4px;
            color: #999;
        }

        .chart-error {
            background: #ffebee;
            color: #c62828;
            padding: 20px;
            border-radius: 4px;
            border: 1px solid #ef5350;
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }

        .footer p {
            margin: 5px 0;
        }

        /* Room Details Section Styles */
        .room-details-section {
            padding: 30px;
        }

        .room-detail-card {
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
        }

        .room-name {
            font-size: 1.5em;
            color: #1a1a1a;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #4CAF50;
        }

        .room-kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .room-kpi-item {
            display: flex;
            flex-direction: column;
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }

        .room-kpi-label {
            font-size: 0.85em;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .room-kpi-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #1a1a1a;
        }

        .room-compliance-details {
            margin-top: 20px;
        }

        .room-compliance-details h4 {
            font-size: 1.1em;
            color: #333;
            margin-bottom: 15px;
        }

        .room-compliance-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        .room-compliance-table th,
        .room-compliance-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        .room-compliance-table th {
            background: #f5f5f5;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            font-size: 0.85em;
        }

        /* Building Statistics Styles */
        .building-statistics-section {
            padding: 30px;
        }

        .statistics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .stat-category {
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
        }

        .stat-category.full-width {
            grid-column: 1 / -1;
        }

        .stat-category h3 {
            font-size: 1.2em;
            color: #1a1a1a;
            margin-bottom: 15px;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 8px;
        }

        .stat-items {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: white;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }

        .stat-label {
            font-size: 0.95em;
            color: #666;
        }

        .stat-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #1a1a1a;
            padding: 3px 8px;
            border-radius: 4px;
        }

        .parameter-stats-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
        }

        .parameter-stats-table th,
        .parameter-stats-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        .parameter-stats-table th {
            background: #f5f5f5;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            font-size: 0.9em;
        }

        .parameter-stats-table tr:hover {
            background: #f9f9f9;
        }

        /* Category Distribution Table Styles */
        .category-distribution,
        .parameter-statistics {
            margin-top: 25px;
        }

        .category-distribution h4,
        .parameter-statistics h4 {
            font-size: 1.1em;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 1px solid #e0e0e0;
        }

        .category-table,
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin-top: 10px;
        }

        .category-table th,
        .category-table td,
        .stats-table th,
        .stats-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        .category-table th,
        .stats-table th {
            background: #f5f5f5;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            font-size: 0.85em;
        }

        .category-table td {
            text-align: center;
        }

        .category-table td:first-child {
            text-align: left;
        }

        /* Category color coding */
        .cat-i {
            background: #E8F5E9;
            color: #2E7D32;
            font-weight: 600;
        }

        .cat-ii {
            background: #FFF9C4;
            color: #F57C00;
            font-weight: 600;
        }

        .cat-iii {
            background: #FFE0B2;
            color: #E65100;
            font-weight: 600;
        }

        .cat-iv {
            background: #FFCDD2;
            color: #C62828;
            font-weight: 600;
        }

        .cat-outside {
            background: #FFEBEE;
            color: #B71C1C;
            font-weight: 700;
        }

        .stats-table td {
            text-align: right;
        }

        .stats-table td:first-child {
            text-align: left;
        }

        .stats-table tr:hover {
            background: #f9f9f9;
        }
        """

        return base_styles

    @staticmethod
    def _get_grade_class(grade: str) -> str:
        """Get CSS class for grade."""
        return f"grade-{grade.lower()}"

    @staticmethod
    def _compliance_to_grade(compliance_rate: float) -> str:
        """Convert compliance rate to grade."""
        if compliance_rate >= 95:
            return "A"
        elif compliance_rate >= 85:
            return "B"
        elif compliance_rate >= 70:
            return "C"
        elif compliance_rate >= 50:
            return "D"
        else:
            return "F"
