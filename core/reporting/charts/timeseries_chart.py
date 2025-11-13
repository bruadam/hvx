"""Timeseries chart with non-compliant periods highlighted."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from core.analytics.filters.seasonal_filter import SeasonalFilter
from core.domain.enums.parameter_type import ParameterType
from core.domain.models.compliance_result import ComplianceResult
from core.domain.models.room import Room


class TimeseriesChart:
    """
    Generate timeseries charts with compliance violations highlighted.

    Non-compliant periods are shown in red, compliant periods in green/blue.
    """

    @staticmethod
    def create_timeseries_with_compliance(
        room: Room,
        parameter: ParameterType,
        compliance_result: ComplianceResult,
        season: str | None = None,
        title: str | None = None,
        show_threshold: bool = True,
    ) -> go.Figure:
        """
        Create timeseries chart with non-compliant periods highlighted in red.

        Args:
            room: Room with time series data
            parameter: Parameter to visualize
            compliance_result: Compliance result with violations
            season: Optional season filter
            title: Chart title
            show_threshold: Whether to show threshold lines

        Returns:
            Plotly figure
        """
        if not room.has_data:
            return TimeseriesChart._create_empty_figure("No data available")

        # Get parameter data
        data = room.get_parameter_data(parameter)
        if data is None:
            return TimeseriesChart._create_empty_figure(f"No {parameter.value} data")

        # Create DataFrame
        df = pd.DataFrame({parameter.value: data})

        # Apply seasonal filter if specified
        if season:
            seasonal_filter = SeasonalFilter(season)
            df = seasonal_filter.apply(df)

        if df is not None and df.empty:
            return TimeseriesChart._create_empty_figure("No data in selected season")

        # Create figure
        fig = go.Figure()

        # Create compliance mask from violations
        violation_timestamps = {v.timestamp for v in compliance_result.violations}
        df['is_compliant'] = ~df.index.isin(violation_timestamps)

        # Split data into compliant and non-compliant segments
        compliant_df = df[df['is_compliant']]
        non_compliant_df = df[~df['is_compliant']]

        # Add compliant data (blue/green)
        if not compliant_df.empty:
            fig.add_trace(go.Scatter(
                x=compliant_df.index,
                y=compliant_df[parameter.value],
                mode='lines',
                name='Compliant',
                line={"color": '#2E7D32', "width": 1.5},  # Green
                hovertemplate='<b>%{x}</b><br>Value: %{y:.2f}<extra></extra>',
            ))

        # Add non-compliant data (red) - highlighted
        if not non_compliant_df.empty:
            fig.add_trace(go.Scatter(
                x=non_compliant_df.index,
                y=non_compliant_df[parameter.value],
                mode='markers+lines',
                name='Non-Compliant',
                line={"color": '#C62828', "width": 2},  # Red
                marker={"size": 4, "color": '#C62828'},
                hovertemplate='<b>%{x}</b><br>Value: %{y:.2f}<br><b>VIOLATION</b><extra></extra>',
            ))

        # Add threshold lines if requested
        if show_threshold:
            threshold_meta = compliance_result.metadata
            if 'threshold_lower' in threshold_meta and threshold_meta['threshold_lower']:
                fig.add_hline(
                    y=threshold_meta['threshold_lower'],
                    line_dash="dash",
                    line_color="orange",
                    annotation_text=f"Lower: {threshold_meta['threshold_lower']}",
                    annotation_position="right",
                )

            if 'threshold_upper' in threshold_meta and threshold_meta['threshold_upper']:
                fig.add_hline(
                    y=threshold_meta['threshold_upper'],
                    line_dash="dash",
                    line_color="orange",
                    annotation_text=f"Upper: {threshold_meta['threshold_upper']}",
                    annotation_position="right",
                )

        # Update layout
        title_text = title or f"{parameter.display_name} - Timeseries with Compliance"
        if season:
            title_text += f" ({season.title()})"

        fig.update_layout(
            title=title_text,
            xaxis_title="Time",
            yaxis_title=f"{parameter.display_name} ({parameter.default_unit})",
            hovermode='x unified',
            height=500,
            template='plotly_white',
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1
            },
        )

        # Add compliance rate annotation
        fig.add_annotation(
            text=f"Compliance Rate: {compliance_result.compliance_rate:.1f}%",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.98,
            showarrow=False,
            bgcolor="white",
            bordercolor="gray",
            borderwidth=1,
            font={"size": 12},
        )

        return fig

    @staticmethod
    def create_multi_parameter_timeseries(
        room: Room,
        parameters: list[ParameterType],
        season: str | None = None,
        title: str | None = None,
    ) -> go.Figure:
        """
        Create timeseries chart with multiple parameters.

        Args:
            room: Room with time series data
            parameters: List of parameters to show
            season: Optional season filter
            title: Chart title

        Returns:
            Plotly figure with subplots
        """
        from plotly.subplots import make_subplots

        if not room.has_data:
            return TimeseriesChart._create_empty_figure("No data available")

        # Filter parameters that exist in data
        available_params = [p for p in parameters if p in room.available_parameters]

        if not available_params:
            return TimeseriesChart._create_empty_figure("No matching parameters")

        # Create subplots
        fig = make_subplots(
            rows=len(available_params),
            cols=1,
            subplot_titles=[p.display_name for p in available_params],
            shared_xaxes=True,
            vertical_spacing=0.1,
        )

        # Get data
        df = room.time_series_data

        if df is None:
            return TimeseriesChart._create_empty_figure("No data available")

        # Apply seasonal filter if specified
        if season:
            seasonal_filter = SeasonalFilter(season)
            df = seasonal_filter.apply(df)

        if df is not None and df.empty:
            return TimeseriesChart._create_empty_figure("No data in selected season")

        # Add traces for each parameter
        for i, param in enumerate(available_params, 1):
            if param.value in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[param.value],
                        mode='lines',
                        name=param.display_name,
                        line={"width": 1},
                        hovertemplate=f'<b>%{{x}}</b><br>{param.display_name}: %{{y:.2f}}<extra></extra>',
                    ),
                    row=i,
                    col=1,
                )

                # Update y-axis label
                fig.update_yaxes(
                    title_text=param.default_unit,
                    row=i,
                    col=1,
                )

        # Update layout
        title_text = title or f"{room.name} - Multiple Parameters"
        if season:
            title_text += f" ({season.title()})"

        fig.update_layout(
            title=title_text,
            height=250 * len(available_params),
            showlegend=False,
            hovermode='x unified',
            template='plotly_white',
        )

        fig.update_xaxes(title_text="Time", row=len(available_params), col=1)

        return fig

    @staticmethod
    def create_violation_timeline(
        compliance_result: ComplianceResult,
        room_name: str,
        title: str | None = None,
    ) -> go.Figure:
        """
        Create timeline showing only violation periods.

        Args:
            compliance_result: Compliance result with violations
            room_name: Name of room
            title: Chart title

        Returns:
            Plotly figure
        """
        if not compliance_result.violations:
            return TimeseriesChart._create_empty_figure("No violations found")

        # Create DataFrame from violations
        violations_data = [
            {
                'timestamp': v.timestamp,
                'value': v.measured_value,
                'deviation': v.deviation,
                'severity': v.severity,
            }
            for v in compliance_result.violations
        ]

        df = pd.DataFrame(violations_data)

        # Color by severity
        severity_colors = {
            'minor': '#FFA726',  # Orange
            'moderate': '#FF7043',  # Deep Orange
            'major': '#EF5350',  # Red
            'critical': '#C62828',  # Dark Red
        }

        fig = go.Figure()

        # Add scatter plot with colors by severity
        for severity in ['minor', 'moderate', 'major', 'critical']:
            severity_df = df[df['severity'] == severity]
            if not severity_df.empty:
                fig.add_trace(go.Scatter(
                    x=severity_df['timestamp'],
                    y=severity_df['value'],
                    mode='markers',
                    name=severity.title(),
                    marker={
                        "size": 8,
                        "color": severity_colors[severity],
                        "line": {"width": 1, "color": 'white'},
                    },
                    hovertemplate=(
                        '<b>%{x}</b><br>'
                        'Value: %{y:.2f}<br>'
                        f'Severity: {severity}<br>'
                        'Deviation: %{customdata:.2f}<extra></extra>'
                    ),
                    customdata=severity_df['deviation'],
                ))

        # Update layout
        title_text = title or f"{room_name} - Violation Timeline"

        fig.update_layout(
            title=title_text,
            xaxis_title="Time",
            yaxis_title=f"Value ({compliance_result.parameter.default_unit})",
            height=400,
            template='plotly_white',
            hovermode='closest',
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
            font={"size": 16},
        )
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
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
