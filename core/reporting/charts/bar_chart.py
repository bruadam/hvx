"""Bar charts for comparing rooms and buildings."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.models.room_analysis import RoomAnalysis


class BarChart:
    """Generate bar charts for comparisons."""

    @staticmethod
    def create_room_comparison_chart(
        room_analyses: list[RoomAnalysis],
        metric: str = 'compliance',
        title: str | None = None,
        sort: bool = True,
        ascending: bool = False,
        show_only_failing: bool = False,
        failing_threshold: float = 95.0,
    ) -> go.Figure:
        """
        Create bar chart comparing rooms.

        Args:
            room_analyses: List of room analysis results
            metric: Metric to compare ('compliance', 'quality', 'violations')
            title: Chart title
            sort: Whether to sort rooms by metric
            ascending: Sort order
            show_only_failing: Show only rooms below threshold
            failing_threshold: Threshold for considering a room failing

        Returns:
            Plotly figure
        """
        if not room_analyses:
            return BarChart._create_empty_figure("No room data available")

        # Extract data
        room_data = []
        for analysis in room_analyses:
            if metric == 'compliance':
                value = analysis.overall_compliance_rate
            elif metric == 'quality':
                value = analysis.data_quality_score
            elif metric == 'violations':
                value = analysis.total_violations
            else:
                value = 0

            # Apply failing filter
            if show_only_failing:
                if metric == 'compliance' and value >= failing_threshold:
                    continue
                elif metric == 'quality' and value >= failing_threshold:
                    continue

            room_data.append({
                'room_name': analysis.room_name,
                'room_id': analysis.room_id,
                'value': value,
            })

        if not room_data:
            return BarChart._create_empty_figure("No rooms match filter criteria")

        df = pd.DataFrame(room_data)

        # Sort if requested
        if sort:
            df = df.sort_values('value', ascending=ascending)

        # Determine color based on value and threshold
        colors = []
        for val in df['value']:
            if metric in ['compliance', 'quality']:
                if val >= 95:
                    colors.append('#2E7D32')  # Green
                elif val >= 80:
                    colors.append('#F57C00')  # Orange
                else:
                    colors.append('#C62828')  # Red
            else:  # violations
                if val == 0:
                    colors.append('#2E7D32')
                elif val <= 10:
                    colors.append('#F57C00')
                else:
                    colors.append('#C62828')

        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=df['room_name'],
                y=df['value'],
                marker_color=colors,
                text=df['value'].round(1),
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Value: %{y:.1f}<extra></extra>',
            )
        ])

        # Update layout
        metric_labels = {
            'compliance': 'Compliance Rate (%)',
            'quality': 'Data Quality Score (%)',
            'violations': 'Number of Violations',
        }

        title_text = title or f"Room Comparison - {metric_labels.get(metric, metric)}"
        if show_only_failing:
            title_text += " (Failing Rooms Only)"

        fig.update_layout(
            title=title_text,
            xaxis_title="Room",
            yaxis_title=metric_labels.get(metric, metric),
            height=500,
            template='plotly_white',
            xaxis={'tickangle': -45},
        )

        # Add threshold line for compliance/quality
        if metric in ['compliance', 'quality']:
            fig.add_hline(
                y=failing_threshold,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Threshold: {failing_threshold}%",
                annotation_position="right",
            )

        return fig

    @staticmethod
    def create_building_comparison_chart(
        building_analyses: list[BuildingAnalysis],
        title: str | None = None,
        sort: bool = True,
    ) -> go.Figure:
        """
        Create bar chart comparing buildings.

        Args:
            building_analyses: List of building analysis results
            title: Chart title
            sort: Whether to sort by compliance

        Returns:
            Plotly figure
        """
        if not building_analyses:
            return BarChart._create_empty_figure("No building data available")

        # Extract data
        building_data = [{
            'building_name': analysis.building_name,
            'compliance': analysis.avg_compliance_rate,
            'quality': analysis.avg_quality_score,
            'grade': analysis.compliance_grade,
            'rooms': analysis.room_count,
        } for analysis in building_analyses]

        df = pd.DataFrame(building_data)

        # Sort if requested
        if sort:
            df = df.sort_values('compliance', ascending=False)

        # Determine colors based on grade
        grade_colors = {
            'A': '#2E7D32',  # Green
            'B': '#66BB6A',  # Light Green
            'C': '#FFA726',  # Orange
            'D': '#EF5350',  # Red
            'F': '#C62828',  # Dark Red
        }
        colors = [grade_colors.get(grade, '#757575') for grade in df['grade']]

        # Create grouped bar chart
        fig = go.Figure(data=[
            go.Bar(
                name='Compliance Rate',
                x=df['building_name'],
                y=df['compliance'],
                marker_color=colors,
                text=[f"{c:.1f}% ({g})" for c, g in zip(df['compliance'], df['grade'], strict=False)],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Compliance: %{y:.1f}%<br>Grade: %{text}<extra></extra>',
            ),
        ])

        # Update layout
        title_text = title or "Building Comparison - Compliance Rates"

        fig.update_layout(
            title=title_text,
            xaxis_title="Building",
            yaxis_title="Compliance Rate (%)",
            height=500,
            template='plotly_white',
            xaxis={'tickangle': -45},
            yaxis={'range': [0, 105]},  # Give space for text
        )

        return fig

    @staticmethod
    def create_test_comparison_chart(
        room_analysis: RoomAnalysis,
        title: str | None = None,
        show_only_failing: bool = False,
    ) -> go.Figure:
        """
        Create bar chart comparing different tests within a room.

        Args:
            room_analysis: Room analysis with multiple test results
            title: Chart title
            show_only_failing: Show only failing tests

        Returns:
            Plotly figure
        """
        if not room_analysis.compliance_results:
            return BarChart._create_empty_figure("No test results available")

        # Extract test data
        test_data = []
        for test_id, result in room_analysis.compliance_results.items():
            if show_only_failing and result.is_compliant:
                continue

            test_data.append({
                'test_id': test_id,
                'compliance': result.compliance_rate,
                'violations': result.violation_count,
                'is_compliant': result.is_compliant,
            })

        if not test_data:
            return BarChart._create_empty_figure("No tests match filter criteria")

        df = pd.DataFrame(test_data)
        df = df.sort_values('compliance')

        # Color by compliance status
        colors = ['#C62828' if not c else '#2E7D32' for c in df['is_compliant']]

        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=df['test_id'],
                y=df['compliance'],
                marker_color=colors,
                text=df['compliance'].round(1),
                textposition='outside',
                customdata=df['violations'],
                hovertemplate=(
                    '<b>%{x}</b><br>'
                    'Compliance: %{y:.1f}%<br>'
                    'Violations: %{customdata}<extra></extra>'
                ),
            )
        ])

        # Update layout
        title_text = title or f"{room_analysis.room_name} - Test Results"
        if show_only_failing:
            title_text += " (Failing Tests Only)"

        fig.update_layout(
            title=title_text,
            xaxis_title="Test",
            yaxis_title="Compliance Rate (%)",
            height=500,
            template='plotly_white',
            xaxis={'tickangle': -45},
        )

        # Add 95% threshold line
        fig.add_hline(
            y=95,
            line_dash="dash",
            line_color="orange",
            annotation_text="95% Target",
            annotation_position="right",
        )

        return fig

    @staticmethod
    def create_stacked_comparison_chart(
        room_analyses: list[RoomAnalysis],
        title: str | None = None,
    ) -> go.Figure:
        """
        Create stacked bar chart showing compliant vs non-compliant breakdown.

        Args:
            room_analyses: List of room analyses
            title: Chart title

        Returns:
            Plotly figure
        """
        if not room_analyses:
            return BarChart._create_empty_figure("No room data available")

        # Extract data
        room_names = []
        compliant_rates = []
        non_compliant_rates = []

        for analysis in room_analyses:
            room_names.append(analysis.room_name)
            compliant_rates.append(analysis.overall_compliance_rate)
            non_compliant_rates.append(100 - analysis.overall_compliance_rate)

        # Create stacked bar chart
        fig = go.Figure(data=[
            go.Bar(
                name='Compliant',
                x=room_names,
                y=compliant_rates,
                marker_color='#2E7D32',
                text=[f"{c:.1f}%" for c in compliant_rates],
                textposition='inside',
            ),
            go.Bar(
                name='Non-Compliant',
                x=room_names,
                y=non_compliant_rates,
                marker_color='#C62828',
                text=[f"{nc:.1f}%" for nc in non_compliant_rates],
                textposition='inside',
            ),
        ])

        # Update layout
        title_text = title or "Room Compliance Breakdown"

        fig.update_layout(
            title=title_text,
            xaxis_title="Room",
            yaxis_title="Percentage",
            barmode='stack',
            height=500,
            template='plotly_white',
            xaxis={'tickangle': -45},
            yaxis={'range': [0, 100]},
        )

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
            font={'size': 16},
        )
        fig.update_layout(
            xaxis={'visible': False},
            yaxis={'visible': False},
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
