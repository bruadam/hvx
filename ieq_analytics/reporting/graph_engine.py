"""
Graph Engine for IEQ Analytics Reports

Provides a comprehensive graph generation system with multiple chart types,
consistent styling, and data-driven visualization capabilities.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GraphType(Enum):
    """Available graph types for report generation."""
    BAR_CHART = "bar_chart"
    HORIZONTAL_BAR = "horizontal_bar"
    TIME_SERIES = "time_series"
    HEATMAP = "heatmap"
    SCATTER_PLOT = "scatter_plot"
    BOX_PLOT = "box_plot"
    HISTOGRAM = "histogram"
    VIOLIN_PLOT = "violin_plot"
    STACKED_BAR = "stacked_bar"
    GROUPED_BAR = "grouped_bar"
    LINE_PLOT = "line_plot"
    AREA_PLOT = "area_plot"
    CORRELATION_MATRIX = "correlation_matrix"
    RADAR_CHART = "radar_chart"


class GraphStyle:
    """Graph styling configuration."""
    
    def __init__(
        self,
        style_name: str = "professional",
        figsize: Tuple[int, int] = (12, 8),
        dpi: int = 300,
        color_palette: str = "Set2",
        font_size: int = 12,
        title_size: int = 16,
        grid: bool = True,
        grid_alpha: float = 0.3
    ):
        self.style_name = style_name
        self.figsize = figsize
        self.dpi = dpi
        self.color_palette = color_palette
        self.font_size = font_size
        self.title_size = title_size
        self.grid = grid
        self.grid_alpha = grid_alpha
        
        # Color schemes for different purposes
        self.color_schemes = {
            "performance": ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"],  # Red to Green
            "compliance": ["#ff4444", "#ffaa44", "#44ff44"],  # Traffic light
            "parameters": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],  # Standard
            "buildings": ["#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"],  # Distinct
            "severity": ["#2ca02c", "#ffaa00", "#ff6600", "#cc0000"]  # Green to Red
        }


class GraphEngine:
    """Main graph generation engine with AI-powered analysis."""
    
    def __init__(self, style: Optional[GraphStyle] = None, enable_ai_analysis: bool = False):
        self.style = style or GraphStyle()
        self.enable_ai_analysis = enable_ai_analysis
        self._setup_matplotlib()
        
        # Initialize AI analyzer if enabled
        if self.enable_ai_analysis:
            try:
                from .ai_graph_analyzer import AIGraphAnalyzer
                self.ai_analyzer = AIGraphAnalyzer()
                logger.info("AI graph analysis enabled")
            except ImportError as e:
                logger.warning(f"AI analysis not available: {e}")
                self.ai_analyzer = None
                self.enable_ai_analysis = False
        else:
            self.ai_analyzer = None
    
    def _setup_matplotlib(self):
        """Configure matplotlib with professional styling."""
        plt.style.use('default')
        sns.set_palette(self.style.color_palette)
        
        # Set global font sizes
        plt.rcParams.update({
            'font.size': self.style.font_size,
            'axes.titlesize': self.style.title_size,
            'axes.labelsize': self.style.font_size,
            'xtick.labelsize': self.style.font_size - 2,
            'ytick.labelsize': self.style.font_size - 2,
            'legend.fontsize': self.style.font_size - 2,
            'figure.titlesize': self.style.title_size + 2
        })
    
    def create_worst_performers_chart(
        self,
        worst_performers_data: Dict[str, Any],
        chart_type: GraphType = GraphType.HORIZONTAL_BAR,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Create chart showing worst performing rooms.
        
        Args:
            worst_performers_data: Data from ReportDataProcessor.identify_worst_performers
            chart_type: Type of chart to create
            top_n: Number of worst performers to show
            
        Returns:
            Chart generation results with file path and metadata
        """
        logger.info(f"Creating worst performers chart (type: {chart_type.value})")
        
        worst_rooms = worst_performers_data.get('overall_worst', [])[:top_n]
        if not worst_rooms:
            return {'error': 'No worst performers data available'}
        
        # Prepare data
        room_names = [room['room_id'] for room in worst_rooms]
        scores = [room['performance_score'] for room in worst_rooms]
        colors = self._get_performance_colors(scores)
        
        fig, ax = plt.subplots(figsize=self.style.figsize, dpi=self.style.dpi)
        
        if chart_type == GraphType.HORIZONTAL_BAR:
            bars = ax.barh(room_names, scores, color=colors)
            ax.set_xlabel('Performance Score (0-100, higher is better)')
            ax.set_ylabel('Room ID')
            ax.set_title(f'Top {top_n} Worst Performing Rooms')
            
            # Add score labels on bars
            for i, (bar, score) in enumerate(zip(bars, scores)):
                ax.text(score + 1, bar.get_y() + bar.get_height()/2, 
                       f'{score:.1f}', ha='left', va='center')
        
        elif chart_type == GraphType.BAR_CHART:
            bars = ax.bar(range(len(room_names)), scores, color=colors)
            ax.set_xticks(range(len(room_names)))
            ax.set_xticklabels(room_names, rotation=45, ha='right')
            ax.set_ylabel('Performance Score (0-100, higher is better)')
            ax.set_title(f'Top {top_n} Worst Performing Rooms')
            
            # Add score labels on bars
            for bar, score in zip(bars, scores):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                       f'{score:.1f}', ha='center', va='bottom')
        
        if self.style.grid:
            ax.grid(True, alpha=self.style.grid_alpha)
        
        plt.tight_layout()
        
        return {
            'figure': fig,
            'chart_type': chart_type.value,
            'data_points': len(worst_rooms),
            'title': f'Top {top_n} Worst Performing Rooms'
        }
    
    def create_compliance_comparison_chart(
        self,
        comparison_data: Dict[str, Any],
        chart_type: GraphType = GraphType.GROUPED_BAR
    ) -> Dict[str, Any]:
        """
        Create chart comparing compliance across rooms or buildings.
        
        Args:
            comparison_data: Data from ReportDataProcessor.prepare_comparison_data
            chart_type: Type of chart to create
            
        Returns:
            Chart generation results
        """
        logger.info(f"Creating compliance comparison chart (type: {chart_type.value})")
        
        data_points = comparison_data.get('data', [])
        if not data_points:
            return {'error': 'No comparison data available'}
        
        metric = comparison_data.get('metric', 'unknown')
        group_by = comparison_data.get('group_by', 'none')
        
        fig, ax = plt.subplots(figsize=self.style.figsize, dpi=self.style.dpi)
        
        if group_by == 'building' and 'grouped' in comparison_data:
            # Grouped bar chart by building
            self._create_grouped_bar_chart(ax, comparison_data['grouped'], metric)
        else:
            # Simple bar chart
            labels = [item['label'] for item in data_points]
            values = [item['value'] for item in data_points]
            colors = self._get_compliance_colors(values, metric)
            
            if chart_type == GraphType.BAR_CHART:
                bars = ax.bar(range(len(labels)), values, color=colors)
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=45, ha='right')
            elif chart_type == GraphType.HORIZONTAL_BAR:
                bars = ax.barh(range(len(labels)), values, color=colors)
                ax.set_yticks(range(len(labels)))
                ax.set_yticklabels(labels)
        
        # Set labels and title
        ylabel = self._get_metric_label(metric)
        ax.set_ylabel(ylabel)
        ax.set_title(f'{ylabel} Comparison')
        
        if self.style.grid:
            ax.grid(True, alpha=self.style.grid_alpha)
        
        plt.tight_layout()
        
        return {
            'figure': fig,
            'chart_type': chart_type.value,
            'metric': metric,
            'data_points': len(data_points),
            'title': f'{ylabel} Comparison'
        }
    
    def create_time_series_chart(
        self,
        time_series_data: Dict[str, Any],
        parameters: Optional[List[str]] = None,
        room_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create time series chart for IEQ parameters.
        
        Args:
            time_series_data: Time series data from ReportDataProcessor
            parameters: Parameters to plot (if None, plot all available)
            room_ids: Room IDs to include (if None, include all)
            
        Returns:
            Chart generation results
        """
        logger.info("Creating time series chart")
        
        data = time_series_data.get('data', {})
        if not data:
            return {'error': 'No time series data available'}
        
        available_params = time_series_data.get('parameters', [])
        parameters = parameters or available_params
        room_ids = room_ids or list(data.keys())
        
        # Determine subplot layout
        n_params = len(parameters) if parameters else 0
        if n_params == 0:
            return {'error': 'No parameters specified for time series chart'}
        
        if n_params == 1:
            fig, axes = plt.subplots(1, 1, figsize=self.style.figsize, dpi=self.style.dpi)
            axes = [axes]
        else:
            fig, axes = plt.subplots(n_params, 1, figsize=(self.style.figsize[0], self.style.figsize[1] * n_params // 2), 
                                   dpi=self.style.dpi, sharex=True)
        
        colors = sns.color_palette(self.style.color_palette, len(room_ids))
        
        for i, param in enumerate(parameters or []):
            ax = axes[i]
            
            for j, room_id in enumerate(room_ids):
                if room_id in data and param in data[room_id]:
                    series = data[room_id][param]
                    if not series.empty:
                        ax.plot(series.index, series.values, 
                               label=room_id, color=colors[j], alpha=0.7, linewidth=1.5)
            
            ax.set_ylabel(self._get_parameter_unit(param))
            ax.set_title(f'{param.title()} Over Time')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            if self.style.grid:
                ax.grid(True, alpha=self.style.grid_alpha)
        
        # Format x-axis for dates
        if axes:
            axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            axes[-1].xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        return {
            'figure': fig,
            'chart_type': GraphType.TIME_SERIES.value,
            'parameters': parameters,
            'room_count': len(room_ids),
            'title': 'Time Series Analysis'
        }
    
    def create_heatmap_chart(
        self,
        heatmap_data: Dict[str, Any],
        colormap: str = 'RdYlBu_r'
    ) -> Dict[str, Any]:
        """
        Create heatmap visualization.
        
        Args:
            heatmap_data: Heatmap data from ReportDataProcessor
            colormap: Matplotlib colormap to use
            
        Returns:
            Chart generation results
        """
        logger.info("Creating heatmap chart")
        
        pivot_data = heatmap_data.get('data')
        if pivot_data is None or pivot_data.empty:
            return {'error': 'No heatmap data available'}
        
        labels = heatmap_data.get('labels', {})
        parameter = heatmap_data.get('parameter', 'Unknown')
        
        fig, ax = plt.subplots(figsize=self.style.figsize, dpi=self.style.dpi)
        
        # Create heatmap
        sns.heatmap(
            pivot_data,
            cmap=colormap,
            center=None,
            annot=False,
            fmt='.1f',
            cbar_kws={'label': self._get_parameter_unit(parameter)},
            ax=ax
        )
        
        # Set labels
        ax.set_xlabel(labels.get('x', 'X'))
        ax.set_ylabel(labels.get('y', 'Y'))
        ax.set_title(labels.get('title', f'{parameter.title()} Heatmap'))
        
        plt.tight_layout()
        
        return {
            'figure': fig,
            'chart_type': GraphType.HEATMAP.value,
            'parameter': parameter,
            'title': labels.get('title', f'{parameter.title()} Heatmap')
        }
    
    def create_distribution_chart(
        self,
        data: Dict[str, Any],
        chart_type: GraphType = GraphType.BOX_PLOT,
        parameter: str = 'temperature'
    ) -> Dict[str, Any]:
        """
        Create distribution chart (box plot, violin plot, histogram).
        
        Args:
            data: Data dictionary with room_id -> parameter values
            chart_type: Type of distribution chart
            parameter: Parameter name for labeling
            
        Returns:
            Chart generation results
        """
        logger.info(f"Creating distribution chart (type: {chart_type.value})")
        
        if not data:
            return {'error': 'No distribution data available'}
        
        fig, ax = plt.subplots(figsize=self.style.figsize, dpi=self.style.dpi)
        
        if chart_type == GraphType.BOX_PLOT:
            # Prepare data for box plot
            values = []
            labels = []
            for room_id, room_values in data.items():
                if isinstance(room_values, (list, np.ndarray, pd.Series)) and len(room_values) > 0:
                    values.append(room_values)
                    labels.append(room_id)
            
            if values:
                box_plot = ax.boxplot(values)
                ax.set_xticklabels(labels, rotation=45, ha='right')
        
        elif chart_type == GraphType.VIOLIN_PLOT:
            # Prepare data for violin plot
            plot_data = []
            room_ids = []
            for room_id, room_values in data.items():
                if isinstance(room_values, (list, np.ndarray, pd.Series)) and len(room_values) > 0:
                    plot_data.extend(room_values)
                    room_ids.extend([room_id] * len(room_values))
            
            if plot_data:
                df = pd.DataFrame({'values': plot_data, 'room': room_ids})
                sns.violinplot(data=df, x='room', y='values', ax=ax)
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        
        elif chart_type == GraphType.HISTOGRAM:
            # Combined histogram
            colors = sns.color_palette(self.style.color_palette, len(data))
            for i, (room_id, room_values) in enumerate(data.items()):
                if isinstance(room_values, (list, np.ndarray, pd.Series)) and len(room_values) > 0:
                    ax.hist(room_values, alpha=0.6, label=room_id, color=colors[i], bins=30)
            ax.legend()
        
        # Set labels
        ax.set_ylabel(self._get_parameter_unit(parameter))
        ax.set_title(f'{parameter.title()} Distribution Across Rooms')
        
        if self.style.grid:
            ax.grid(True, alpha=self.style.grid_alpha)
        
        plt.tight_layout()
        
        return {
            'figure': fig,
            'chart_type': chart_type.value,
            'parameter': parameter,
            'room_count': len(data),
            'title': f'{parameter.title()} Distribution'
        }
    
    def _get_performance_colors(self, scores: List[float]) -> List[str]:
        """Get colors based on performance scores."""
        colors = []
        for score in scores:
            if score >= 80:
                colors.append(self.style.color_schemes["performance"][3])  # Good - Blue
            elif score >= 60:
                colors.append(self.style.color_schemes["performance"][2])  # OK - Green
            elif score >= 40:
                colors.append(self.style.color_schemes["performance"][1])  # Poor - Orange
            else:
                colors.append(self.style.color_schemes["performance"][0])  # Very Poor - Red
        return colors
    
    def _get_compliance_colors(self, values: List[float], metric: str) -> List[str]:
        """Get colors based on compliance values."""
        colors = []
        for value in values:
            if 'compliance' in metric:
                # Compliance percentage (0-100)
                if value >= 90:
                    colors.append(self.style.color_schemes["compliance"][2])  # Green
                elif value >= 70:
                    colors.append(self.style.color_schemes["compliance"][1])  # Yellow
                else:
                    colors.append(self.style.color_schemes["compliance"][0])  # Red
            else:
                # Use default color scheme
                colors.append(self.style.color_schemes["parameters"][0])
        return colors
    
    def _get_metric_label(self, metric: str) -> str:
        """Get human-readable label for metric."""
        metric_labels = {
            'performance_score': 'Performance Score (0-100)',
            'data_quality_score': 'Data Quality Score (0-1)',
            'temperature_compliance': 'Temperature Compliance (%)',
            'co2_compliance': 'CO2 Compliance (%)',
            'humidity_compliance': 'Humidity Compliance (%)',
            'temperature_mean': 'Average Temperature (°C)',
            'co2_mean': 'Average CO2 (ppm)',
            'humidity_mean': 'Average Humidity (%)',
            'total_records': 'Total Data Records',
            'ach_mean': 'Average Air Changes per Hour'
        }
        return metric_labels.get(metric, metric.replace('_', ' ').title())
    
    def _get_parameter_unit(self, parameter: str) -> str:
        """Get unit string for parameter."""
        units = {
            'temperature': 'Temperature (°C)',
            'co2': 'CO2 (ppm)',
            'humidity': 'Humidity (%)',
            'light': 'Light (lux)',
            'pressure': 'Pressure (Pa)',
            'ach': 'Air Changes per Hour'
        }
        return units.get(parameter.lower(), parameter.title())
    
    def _create_grouped_bar_chart(self, ax, grouped_data: Dict[str, List], metric: str):
        """Create grouped bar chart for building comparisons."""
        buildings = list(grouped_data.keys())
        
        # Prepare data for grouped bars
        room_data = {}
        for building, rooms in grouped_data.items():
            for room in rooms:
                room_id = room['room_id']
                if room_id not in room_data:
                    room_data[room_id] = {}
                room_data[room_id][building] = room['value']
        
        # Create grouped bars
        x_pos = np.arange(len(room_data))
        width = 0.8 / len(buildings)
        colors = sns.color_palette(self.style.color_palette, len(buildings))
        
        for i, building in enumerate(buildings):
            values = [room_data[room].get(building, 0) for room in room_data.keys()]
            ax.bar(x_pos + i * width, values, width, label=building, color=colors[i])
        
        ax.set_xticks(x_pos + width * (len(buildings) - 1) / 2)
        ax.set_xticklabels(list(room_data.keys()), rotation=45, ha='right')
        ax.legend()
    
    def save_figure(self, fig, output_path: Path, filename: str) -> str:
        """Save figure to file."""
        output_path.mkdir(parents=True, exist_ok=True)
        full_path = output_path / f"{filename}.png"
        
        fig.savefig(full_path, dpi=self.style.dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        
        logger.info(f"Chart saved to: {full_path}")
        return str(full_path)
    
    def generate_chart_with_ai_analysis(
        self,
        chart_method: str,
        data: Dict[str, Any],
        output_path: Path,
        filename: str,
        chart_context: Optional[Dict[str, Any]] = None,
        **chart_kwargs
    ) -> Tuple[str, Optional[Any]]:
        """
        Generate a chart and optionally analyze it with AI.
        
        Args:
            chart_method: Name of the chart method to call (e.g., 'create_worst_performers_chart')
            data: Data for chart generation
            output_path: Output directory
            filename: Output filename
            chart_context: Context for AI analysis
            **chart_kwargs: Additional arguments for chart method
            
        Returns:
            Tuple of (chart_path, ai_analysis)
        """
        # Get the chart method
        if not hasattr(self, chart_method):
            raise ValueError(f"Chart method '{chart_method}' not found")
        
        method = getattr(self, chart_method)
        
        # Generate the chart
        chart_result = method(data, **chart_kwargs)
        
        # Save the chart
        if 'fig' in chart_result:
            chart_path = self.save_figure(chart_result['fig'], output_path, filename)
        else:
            raise ValueError("Chart method must return a dictionary with 'fig' key")
        
        # Perform AI analysis if enabled
        ai_analysis = None
        if self.enable_ai_analysis and self.ai_analyzer:
            try:
                chart_type = chart_kwargs.get('chart_type', GraphType.BAR_CHART).value
                context = chart_context or {}
                
                # Add chart generation context
                context.update({
                    'chart_method': chart_method,
                    'data_summary': f"Generated using {chart_method}",
                    'chart_type': chart_type
                })
                
                ai_analysis = self.ai_analyzer.analyze_chart(
                    Path(chart_path), 
                    context, 
                    chart_type
                )
                logger.info(f"AI analysis completed for {filename}")
                
            except Exception as e:
                logger.error(f"AI analysis failed for {filename}: {e}")
        
        return chart_path, ai_analysis
    
    def batch_generate_with_ai_analysis(
        self,
        chart_configs: List[Dict[str, Any]],
        output_path: Path,
        enable_review: bool = False
    ) -> Dict[str, Tuple[str, Optional[Any]]]:
        """
        Generate multiple charts with AI analysis and optional interactive review.
        
        Args:
            chart_configs: List of chart configuration dictionaries
            output_path: Output directory for charts
            enable_review: Whether to enable interactive review of AI analyses
            
        Returns:
            Dictionary mapping filenames to (chart_path, ai_analysis) tuples
        """
        results = {}
        ai_analyses = []
        chart_paths = []
        
        # Generate all charts and AI analyses
        for config in chart_configs:
            try:
                chart_path, ai_analysis = self.generate_chart_with_ai_analysis(
                    chart_method=config['method'],
                    data=config['data'],
                    output_path=output_path,
                    filename=config['filename'],
                    chart_context=config.get('context', {}),
                    **config.get('kwargs', {})
                )
                
                results[config['filename']] = (chart_path, ai_analysis)
                
                if ai_analysis:
                    ai_analyses.append(ai_analysis)
                    chart_paths.append(Path(chart_path))
                    
            except Exception as e:
                logger.error(f"Failed to generate chart {config['filename']}: {e}")
                results[config['filename']] = (None, None)
        
        # Interactive review if enabled and AI analyses available
        if enable_review and ai_analyses and self.enable_ai_analysis:
            try:
                from .ai_graph_analyzer import InteractiveReviewSystem
                review_system = InteractiveReviewSystem()
                
                print(f"\n🎯 Starting interactive review of {len(ai_analyses)} AI-generated chart analyses...")
                reviewed_analyses = []
                
                # Review each analysis individually
                for i, (analysis, chart_path) in enumerate(zip(ai_analyses, chart_paths)):
                    try:
                        if hasattr(review_system, 'review_analysis'):
                            reviewed_analysis = review_system.review_analysis(analysis, chart_path)
                        else:
                            logger.warning("InteractiveReviewSystem doesn't have expected review_analysis method, using original analysis")
                            reviewed_analysis = analysis
                    except AttributeError:
                        logger.warning("InteractiveReviewSystem doesn't have expected review_analysis method, using original analysis")
                        reviewed_analysis = analysis
                    reviewed_analyses.append(reviewed_analysis)
                
                # Update results with reviewed analyses
                for i, (filename, (chart_path, _)) in enumerate(results.items()):
                    if i < len(reviewed_analyses):
                        results[filename] = (chart_path, reviewed_analyses[i])
                
            except Exception as e:
                logger.error(f"Interactive review failed: {e}")
        
        return results
