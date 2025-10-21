"""Compliance-specific chart generators."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.building_analysis import BuildingAnalysis


class ComplianceChart:
    """Generate compliance-focused visualizations."""

    @staticmethod
    def create_compliance_matrix(
        room_analyses: List[RoomAnalysis],
        title: Optional[str] = None,
    ) -> go.Figure:
        """
        Create matrix showing test results for all rooms.

        Args:
            room_analyses: List of room analyses
            title: Chart title

        Returns:
            Plotly figure
        """
        if not room_analyses:
            return ComplianceChart._create_empty_figure("No data available")

        # Collect all test IDs
        all_tests = set()
        for analysis in room_analyses:
            all_tests.update(analysis.compliance_results.keys())

        all_tests = sorted(list(all_tests))

        # Create matrix
        matrix = []
        room_names = []

        for analysis in room_analyses:
            room_names.append(analysis.room_name)
            row = []
            for test_id in all_tests:
                if test_id in analysis.compliance_results:
                    result = analysis.compliance_results[test_id]
                    row.append(result.compliance_rate)
                else:
                    row.append(None)
            matrix.append(row)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=all_tests,
            y=room_names,
            colorscale='RdYlGn',  # Red-Yellow-Green
            zmin=0,
            zmax=100,
            hovertemplate='<b>%{y}</b><br>%{x}<br>Compliance: %{z:.1f}%<extra></extra>',
            colorbar=dict(title='Compliance %'),
        ))

        # Update layout
        title_text = title or "Compliance Matrix - All Rooms x All Tests"

        fig.update_layout(
            title=title_text,
            xaxis_title="Test",
            yaxis_title="Room",
            height=max(400, len(room_names) * 30),
            template='plotly_white',
            xaxis=dict(tickangle=-45),
        )

        return fig

    @staticmethod
    def create_compliance_gauge(
        compliance_rate: float,
        title: str = "Compliance Rate",
        thresholds: Optional[Dict[str, float]] = None,
    ) -> go.Figure:
        """
        Create gauge chart for compliance rate.

        Args:
            compliance_rate: Compliance percentage (0-100)
            title: Gauge title
            thresholds: Dict with 'good', 'warning', 'critical' thresholds

        Returns:
            Plotly figure
        """
        if thresholds is None:
            thresholds = {'critical': 70, 'warning': 85, 'good': 95}

        # Determine color
        if compliance_rate >= thresholds['good']:
            color = "#2E7D32"  # Green
        elif compliance_rate >= thresholds['warning']:
            color = "#F57C00"  # Orange
        else:
            color = "#C62828"  # Red

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=compliance_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': 95, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, thresholds['critical']], 'color': "#FFCDD2"},
                    {'range': [thresholds['critical'], thresholds['warning']], 'color': "#FFE0B2"},
                    {'range': [thresholds['warning'], thresholds['good']], 'color': "#FFF9C4"},
                    {'range': [thresholds['good'], 100], 'color': "#C8E6C9"},
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95,
                }
            }
        ))

        fig.update_layout(
            height=350,
            template='plotly_white',
        )

        return fig

    @staticmethod
    def create_building_kpi_dashboard(
        building_analysis: BuildingAnalysis,
        title: Optional[str] = None,
    ) -> go.Figure:
        """
        Create KPI dashboard for building.

        Args:
            building_analysis: Building analysis result
            title: Dashboard title

        Returns:
            Plotly figure with multiple KPI gauges
        """
        # Create subplots for KPIs
        fig = make_subplots(
            rows=1,
            cols=3,
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]],
            subplot_titles=['Compliance Rate', 'Data Quality', 'Total Violations'],
        )

        # Compliance gauge
        compliance_color = (
            "#2E7D32" if building_analysis.avg_compliance_rate >= 95
            else "#F57C00" if building_analysis.avg_compliance_rate >= 80
            else "#C62828"
        )

        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=building_analysis.avg_compliance_rate,
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': compliance_color},
                'steps': [
                    {'range': [0, 70], 'color': "#FFCDD2"},
                    {'range': [70, 85], 'color': "#FFE0B2"},
                    {'range': [85, 95], 'color': "#FFF9C4"},
                    {'range': [95, 100], 'color': "#C8E6C9"},
                ],
            },
            domain={'x': [0, 1], 'y': [0, 1]},
        ), row=1, col=1)

        # Quality gauge
        quality_color = (
            "#2E7D32" if building_analysis.avg_quality_score >= 90
            else "#F57C00" if building_analysis.avg_quality_score >= 75
            else "#C62828"
        )

        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=building_analysis.avg_quality_score,
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': quality_color},
            },
            domain={'x': [0, 1], 'y': [0, 1]},
        ), row=1, col=2)

        # Violations indicator
        fig.add_trace(go.Indicator(
            mode="number",
            value=building_analysis.total_violations,
            number={'font': {'size': 60}},
            domain={'x': [0, 1], 'y': [0, 1]},
        ), row=1, col=3)

        # Update layout
        title_text = title or f"{building_analysis.building_name} - Key Performance Indicators"

        fig.update_layout(
            title=title_text,
            height=400,
            template='plotly_white',
        )

        return fig

    @staticmethod
    def create_portfolio_overview(
        building_analyses: List[BuildingAnalysis],
        title: Optional[str] = None,
    ) -> go.Figure:
        """
        Create portfolio overview with multiple KPIs.

        Args:
            building_analyses: List of building analyses
            title: Chart title

        Returns:
            Plotly figure
        """
        if not building_analyses:
            return ComplianceChart._create_empty_figure("No building data available")

        # Calculate portfolio metrics
        total_rooms = sum(ba.room_count for ba in building_analyses)
        avg_compliance = sum(ba.avg_compliance_rate * ba.room_count for ba in building_analyses) / total_rooms if total_rooms > 0 else 0
        total_violations = sum(ba.total_violations for ba in building_analyses)

        # Create figure with KPIs
        fig = make_subplots(
            rows=2,
            cols=2,
            specs=[
                [{'type': 'indicator'}, {'type': 'indicator'}],
                [{'type': 'bar', 'colspan': 2}, None]
            ],
            subplot_titles=[
                'Portfolio Compliance',
                'Total Violations',
                'Buildings Performance'
            ],
            vertical_spacing=0.15,
            row_heights=[0.4, 0.6],
        )

        # Portfolio compliance gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=avg_compliance,
            delta={'reference': 95},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#2E7D32" if avg_compliance >= 95 else "#C62828"},
                'steps': [
                    {'range': [0, 70], 'color': "#FFCDD2"},
                    {'range': [70, 85], 'color': "#FFE0B2"},
                    {'range': [85, 95], 'color': "#FFF9C4"},
                    {'range': [95, 100], 'color': "#C8E6C9"},
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 95}
            },
        ), row=1, col=1)

        # Total violations
        fig.add_trace(go.Indicator(
            mode="number",
            value=total_violations,
            number={'font': {'size': 60, 'color': "#C62828"}},
        ), row=1, col=2)

        # Buildings bar chart
        building_names = [ba.building_name for ba in building_analyses]
        compliance_rates = [ba.avg_compliance_rate for ba in building_analyses]
        colors = ['#2E7D32' if c >= 95 else '#F57C00' if c >= 80 else '#C62828' for c in compliance_rates]

        fig.add_trace(go.Bar(
            x=building_names,
            y=compliance_rates,
            marker_color=colors,
            text=[f"{c:.1f}%" for c in compliance_rates],
            textposition='outside',
        ), row=2, col=1)

        # Update layout
        title_text = title or "Portfolio Overview"

        fig.update_layout(
            title=title_text,
            height=800,
            showlegend=False,
            template='plotly_white',
        )

        fig.update_xaxes(title_text="Building", row=2, col=1, tickangle=-45)
        fig.update_yaxes(title_text="Compliance Rate (%)", row=2, col=1)

        return fig

    @staticmethod
    def _create_empty_figure(message: str) -> go.Figure:
        """Create empty figure with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template='plotly_white',
        )
        return fig

    @staticmethod
    def save_chart(fig: go.Figure, output_path: Path, format: str = 'html') -> None:
        """Save chart to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'html':
            fig.write_html(str(output_path))
        elif format == 'png':
            fig.write_image(str(output_path))
        elif format == 'svg':
            fig.write_image(str(output_path))
