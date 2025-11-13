"""Heatmap chart generator for temporal patterns."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from core.analytics.filters.seasonal_filter import SeasonalFilter
from core.domain.enums.parameter_type import ParameterType
from core.domain.models.room import Room


class HeatmapChart:
    """
    Generate heatmap visualizations showing temporal patterns.

    Supports multiple aggregation modes:
    - Hour x Day of Week
    - Hour x Day of Month
    - Day x Month
    - Hour x Month
    """

    @staticmethod
    def create_hourly_daily_heatmap(
        room: Room,
        parameter: ParameterType,
        season: str | None = None,
        title: str | None = None,
        show_compliance: bool = False,
        compliance_threshold: dict[str, float] | None = None,
    ) -> go.Figure:
        """
        Create heatmap with hours on Y-axis and days on X-axis.

        Args:
            room: Room with time series data
            parameter: Parameter to visualize
            season: Optional season filter ('winter', 'summer', etc.)
            title: Chart title
            show_compliance: Whether to color by compliance
            compliance_threshold: Threshold for compliance coloring

        Returns:
            Plotly figure
        """
        if not room.has_data:
            return HeatmapChart._create_empty_figure("No data available")

        # Get parameter data
        data = room.get_parameter_data(parameter)
        if data is None:
            return HeatmapChart._create_empty_figure(f"No {parameter.value} data")

        # Create DataFrame
        df = pd.DataFrame({parameter.value: data})

        # Apply seasonal filter if specified
        if season:
            seasonal_filter = SeasonalFilter(season)
            df = seasonal_filter.apply(df)

        if df is not None and df.empty:
            return HeatmapChart._create_empty_figure("No data in selected season")

        # Ensure datetime index
        df.index = pd.to_datetime(df.index)
        # Create pivot table: Hour (rows) x Day of Week (columns)
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.day_name()
        df['day_num'] = df.index.weekday

        # Aggregate by hour and day of week
        pivot = df.groupby(['hour', 'day_num', 'day_of_week'])[parameter.value].mean().reset_index()
        pivot_table = pivot.pivot(index='hour', columns='day_of_week', values=parameter.value)

        # Reorder columns to start with Monday
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_table = pivot_table.reindex(columns=[d for d in day_order if d in pivot_table.columns])

        # Determine color scale
        if show_compliance and compliance_threshold:
            # Color based on compliance
            colorscale = 'RdYlGn'  # Red (bad) to Green (good)
        else:
            # Color based on value
            colorscale = 'Viridis'

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale=colorscale,
            hovertemplate='<b>%{x}</b><br>Hour: %{y}<br>Value: %{z:.2f}<extra></extra>',
            colorbar={"title": parameter.default_unit},
        ))

        # Update layout
        title_text = title or f"{parameter.display_name} - Hourly Pattern by Day of Week"
        if season:
            title_text += f" ({season.title()})"

        fig.update_layout(
            title=title_text,
            xaxis_title="Day of Week",
            yaxis_title="Hour of Day",
            yaxis={"autorange": 'reversed'},  # Hour 0 at top
            height=600,
            template='plotly_white',
        )

        return fig

    @staticmethod
    def create_daily_monthly_heatmap(
        room: Room,
        parameter: ParameterType,
        year: int | None = None,
        title: str | None = None,
    ) -> go.Figure:
        """
        Create heatmap with days on Y-axis and months on X-axis.

        Args:
            room: Room with time series data
            parameter: Parameter to visualize
            year: Optional year to filter
            title: Chart title

        Returns:
            Plotly figure
        """
        if not room.has_data:
            return HeatmapChart._create_empty_figure("No data available")

        # Get parameter data
        data = room.get_parameter_data(parameter)
        if data is None:
            return HeatmapChart._create_empty_figure(f"No {parameter.value} data")

        # Create DataFrame
        df = pd.DataFrame({parameter.value: data})
        # Ensure datetime index
        df.index = pd.to_datetime(df.index)
        # Filter by year if specified
        if year:
            df = df[df.index.year == year]

        if df is not None and df.empty:
            return HeatmapChart._create_empty_figure("No data in selected year")

        # Ensure datetime index
        df.index = pd.to_datetime(df.index)
        # Create pivot table: Day (rows) x Month (columns)
        df['day'] = df.index.day
        df['month'] = df.index.month
        df['month_name'] = df.index.strftime('%b')

        # Aggregate by day and month
        pivot = df.groupby(['day', 'month', 'month_name'])[parameter.value].mean().reset_index()
        pivot_table = pivot.pivot(index='day', columns='month_name', values=parameter.value)

        # Reorder columns by month
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        pivot_table = pivot_table.reindex(columns=[m for m in month_order if m in pivot_table.columns])

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='Viridis',
            hovertemplate='<b>%{x}</b><br>Day: %{y}<br>Value: %{z:.2f}<extra></extra>',
            colorbar={"title": parameter.default_unit},
        ))

        # Update layout
        title_text = title or f"{parameter.display_name} - Daily Pattern by Month"
        if year:
            title_text += f" ({year})"

        fig.update_layout(
            title=title_text,
            xaxis_title="Month",
            yaxis_title="Day of Month",
            height=600,
            template='plotly_white',
        )

        return fig

    @staticmethod
    def create_compliance_heatmap(
        room: Room,
        parameter: ParameterType,
        compliance_data: pd.Series,
        season: str | None = None,
        title: str | None = None,
    ) -> go.Figure:
        """
        Create heatmap showing compliance rate by hour and day.

        Args:
            room: Room entity
            parameter: Parameter being analyzed
            compliance_data: Boolean series indicating compliance
            season: Optional season filter
            title: Chart title

        Returns:
            Plotly figure
        """
        # Create DataFrame with compliance
        df = pd.DataFrame({
            'compliant': compliance_data.astype(int)
        })

        # Apply seasonal filter if specified
        if season:
            seasonal_filter = SeasonalFilter(season)
            df = seasonal_filter.apply(df)

        if df is not None and df.empty:
            return HeatmapChart._create_empty_figure("No data in selected season")

        # Ensure datetime index
        df.index = pd.to_datetime(df.index)
        # Create pivot table
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.day_name()
        df['day_num'] = df.index.weekday

        # Calculate compliance rate for each hour/day combination
        pivot = df.groupby(['hour', 'day_num', 'day_of_week'])['compliant'].mean().reset_index()
        pivot['compliance_pct'] = pivot['compliant'] * 100
        pivot_table = pivot.pivot(index='hour', columns='day_of_week', values='compliance_pct')

        # Reorder columns
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_table = pivot_table.reindex(columns=[d for d in day_order if d in pivot_table.columns])

        # Create heatmap with red-green scale (red = low compliance, green = high)
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='RdYlGn',  # Red-Yellow-Green
            zmin=0,
            zmax=100,
            hovertemplate='<b>%{x}</b><br>Hour: %{y}<br>Compliance: %{z:.1f}%<extra></extra>',
            colorbar={"title": 'Compliance %'},
        ))

        # Update layout
        title_text = title or f"{parameter.display_name} - Compliance Rate by Time"
        if season:
            title_text += f" ({season.title()})"

        fig.update_layout(
            title=title_text,
            xaxis_title="Day of Week",
            yaxis_title="Hour of Day",
            yaxis={"autorange": 'reversed'},
            height=600,
            template='plotly_white',
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
