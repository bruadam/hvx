"""
Main Report Engine for IEQ Analytics

Orchestrates the entire report generation process, including data processing,
chart generation, and PDF creation. Provides a unified interface for creating
different types of reports.
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging
import json

from .data_processor import ReportDataProcessor, WorstPerformerCriteria
from .graph_engine import GraphEngine, GraphType, GraphStyle
from .pdf_generator import PDFGenerator, PDFStyle

logger = logging.getLogger(__name__)


class ReportType:
    """Available report types."""
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_REPORT = "technical_report"
    BUILDING_COMPARISON = "building_comparison"
    WORST_PERFORMERS = "worst_performers"


class ReportConfig:
    """Report generation configuration."""
    
    def __init__(
        self,
        include_charts: bool = True,
        include_heatmaps: bool = True,
        include_time_series: bool = True,
        worst_performers_count: int = 10,
        chart_style: str = "professional",
        pdf_style: str = "professional"
    ):
        self.include_charts = include_charts
        self.include_heatmaps = include_heatmaps
        self.include_time_series = include_time_series
        self.worst_performers_count = worst_performers_count
        self.chart_style = chart_style
        self.pdf_style = pdf_style


class ReportEngine:
    """Main report generation engine."""
    
    def __init__(
        self,
        config: Optional[ReportConfig] = None,
        worst_performer_criteria: Optional[WorstPerformerCriteria] = None
    ):
        self.config = config or ReportConfig()
        self.data_processor = ReportDataProcessor(worst_performer_criteria)
        self.graph_engine = GraphEngine(GraphStyle(style_name=self.config.chart_style))
        
        # Initialize PDF generator if ReportLab is available
        try:
            self.pdf_generator = PDFGenerator(PDFStyle())
            self.pdf_available = True
        except ImportError:
            logger.warning("ReportLab not available. PDF generation will be disabled.")
            self.pdf_generator = None
            self.pdf_available = False
    
    def generate_report(
        self,
        report_type: str,
        room_analyses: List[Dict[str, Any]],
        building_analyses: Dict[str, Any],
        ieq_data_list: Optional[List] = None,
        output_dir: Path = Path("output/reports"),
        filename_prefix: str = "ieq_report"
    ) -> Dict[str, Any]:
        """
        Generate a complete report with charts and PDF.
        
        Args:
            report_type: Type of report to generate
            room_analyses: Room-level analysis results
            building_analyses: Building-level analysis results
            ieq_data_list: Optional list of IEQ data objects for time series
            output_dir: Output directory for generated files
            filename_prefix: Prefix for generated filenames
            
        Returns:
            Dictionary with paths to generated files and metadata
        """
        logger.info(f"Generating {report_type} report")
        
        # Create output directories
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        charts_dir = output_dir / "charts"
        charts_dir.mkdir(exist_ok=True)
        
        # Process data for reporting
        report_data = self._prepare_report_data(room_analyses, building_analyses, ieq_data_list)
        
        # Generate charts
        charts = {}
        if self.config.include_charts:
            charts = self._generate_all_charts(report_data, charts_dir, filename_prefix)
        
        # Add charts to report data
        report_data['charts'] = charts
        
        # Generate PDF report
        pdf_path = None
        if self.pdf_available and self.pdf_generator:
            pdf_filename = f"{filename_prefix}_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = output_dir / pdf_filename
            
            try:
                if report_type == ReportType.EXECUTIVE_SUMMARY:
                    self.pdf_generator.create_executive_summary_report(
                        report_data, pdf_path, self.config.include_charts
                    )
                elif report_type == ReportType.TECHNICAL_REPORT:
                    self.pdf_generator.create_technical_report(
                        report_data, pdf_path, self.config.include_charts
                    )
                else:
                    # Use executive summary as default
                    self.pdf_generator.create_executive_summary_report(
                        report_data, pdf_path, self.config.include_charts
                    )
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
                pdf_path = None
        
        # Save report data as JSON
        json_filename = f"{filename_prefix}_{report_type}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_path = output_dir / json_filename
        
        try:
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            json_path = None
        
        return {
            'report_type': report_type,
            'pdf_path': str(pdf_path) if pdf_path else None,
            'json_path': str(json_path) if json_path else None,
            'charts': charts,
            'charts_dir': str(charts_dir),
            'summary': {
                'total_rooms': len(room_analyses),
                'total_buildings': len(building_analyses),
                'charts_generated': len(charts),
                'generation_time': datetime.now().isoformat()
            }
        }
    
    def analyze_worst_performers(
        self,
        room_analyses: List[Dict[str, Any]],
        output_dir: Path = Path("output/reports"),
        top_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate preliminary worst performers analysis.
        
        Args:
            room_analyses: Room analysis results
            output_dir: Output directory
            top_n: Number of worst performers to identify
            
        Returns:
            Worst performers analysis results
        """
        top_n = top_n or self.config.worst_performers_count
        
        logger.info(f"Analyzing worst performers (top {top_n})")
        
        # Identify worst performers
        worst_performers = self.data_processor.identify_worst_performers(
            room_analyses, top_n=top_n, by_building=True
        )
        
        # Generate worst performers chart
        if self.config.include_charts:
            charts_dir = output_dir / "charts"
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            chart_result = self.graph_engine.create_worst_performers_chart(
                worst_performers, GraphType.HORIZONTAL_BAR, top_n
            )
            
            if 'figure' in chart_result:
                chart_path = self.graph_engine.save_figure(
                    chart_result['figure'],
                    charts_dir,
                    "worst_performers"
                )
                worst_performers['chart_path'] = chart_path
        
        # Save results
        output_file = output_dir / f"worst_performers_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(worst_performers, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save worst performers analysis: {e}")
        
        return worst_performers
    
    def generate_interactive_chart_menu(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate interactive chart selection menu.
        
        Args:
            report_data: Processed report data
            
        Returns:
            Dictionary of available chart options and parameters
        """
        menu = {
            'available_charts': {
                'worst_performers': {
                    'description': 'Bar chart showing worst performing rooms',
                    'types': ['horizontal_bar', 'bar_chart'],
                    'parameters': ['top_n (5-20)']
                },
                'compliance_comparison': {
                    'description': 'Compare compliance across rooms or buildings',
                    'types': ['bar_chart', 'horizontal_bar', 'grouped_bar'],
                    'parameters': ['metric', 'group_by']
                },
                'time_series': {
                    'description': 'Time series plots for IEQ parameters',
                    'types': ['line_plot', 'area_plot'],
                    'parameters': ['parameters', 'room_ids', 'date_range']
                },
                'heatmaps': {
                    'description': 'Temporal pattern heatmaps',
                    'types': ['daily_hourly', 'monthly_hourly', 'weekly_hourly'],
                    'parameters': ['parameter', 'aggregation_type']
                },
                'distributions': {
                    'description': 'Parameter distribution analysis',
                    'types': ['box_plot', 'violin_plot', 'histogram'],
                    'parameters': ['parameter', 'rooms']
                }
            },
            'available_metrics': [
                'performance_score',
                'temperature_compliance',
                'co2_compliance', 
                'humidity_compliance',
                'data_quality_score',
                'ach_mean'
            ],
            'available_parameters': [
                'temperature',
                'co2',
                'humidity'
            ],
            'available_buildings': list(report_data.get('building_analyses', {}).keys()),
            'sample_rooms': list(report_data.get('room_analyses', [{}])[:5])  # First 5 rooms as samples
        }
        
        return menu
    
    def generate_custom_chart(
        self,
        report_data: Dict[str, Any],
        chart_type: str,
        chart_config: Dict[str, Any],
        output_dir: Path = Path("output/charts")
    ) -> Dict[str, Any]:
        """
        Generate a custom chart based on user specifications.
        
        Args:
            report_data: Processed report data
            chart_type: Type of chart to generate
            chart_config: Chart configuration parameters
            output_dir: Output directory for chart
            
        Returns:
            Chart generation results
        """
        logger.info(f"Generating custom {chart_type} chart")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if chart_type == 'worst_performers':
                chart_result = self.graph_engine.create_worst_performers_chart(
                    report_data.get('worst_performers', {}),
                    GraphType(chart_config.get('chart_subtype', 'horizontal_bar')),
                    chart_config.get('top_n', 10)
                )
            
            elif chart_type == 'compliance_comparison':
                comparison_data = self.data_processor.prepare_comparison_data(
                    report_data.get('room_analyses', []),
                    chart_config.get('metric', 'performance_score'),
                    chart_config.get('group_by', 'building')
                )
                chart_result = self.graph_engine.create_compliance_comparison_chart(
                    comparison_data,
                    GraphType(chart_config.get('chart_subtype', 'bar_chart'))
                )
            
            elif chart_type == 'time_series':
                if 'ieq_data_list' in report_data:
                    time_series_data = self.data_processor.prepare_time_series_data(
                        report_data['ieq_data_list'],
                        chart_config.get('parameters', ['temperature', 'co2']),
                        chart_config.get('resample_freq', 'h')
                    )
                    chart_result = self.graph_engine.create_time_series_chart(
                        time_series_data,
                        chart_config.get('parameters'),
                        chart_config.get('room_ids')
                    )
                else:
                    return {'error': 'Time series data not available'}
            
            elif chart_type == 'heatmap':
                if 'ieq_data_list' in report_data and report_data['ieq_data_list']:
                    # Use first available IEQ data for heatmap
                    ieq_data = report_data['ieq_data_list'][0]
                    heatmap_data = self.data_processor.prepare_heatmap_data(
                        ieq_data,
                        chart_config.get('parameter', 'temperature'),
                        chart_config.get('aggregation', 'daily_hourly')
                    )
                    chart_result = self.graph_engine.create_heatmap_chart(heatmap_data)
                else:
                    return {'error': 'IEQ data not available for heatmap'}
            
            else:
                return {'error': f'Unknown chart type: {chart_type}'}
            
            # Save chart if generation was successful
            if 'figure' in chart_result:
                chart_filename = f"{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                chart_path = self.graph_engine.save_figure(
                    chart_result['figure'],
                    output_dir,
                    chart_filename
                )
                chart_result['saved_path'] = chart_path
            
            return chart_result
            
        except Exception as e:
            logger.error(f"Custom chart generation failed: {e}")
            return {'error': f'Chart generation failed: {str(e)}'}
    
    def _prepare_report_data(
        self,
        room_analyses: List[Dict[str, Any]],
        building_analyses: Dict[str, Any],
        ieq_data_list: Optional[List] = None
    ) -> Dict[str, Any]:
        """Prepare and consolidate data for report generation."""
        logger.info("Preparing report data")
        
        # Identify worst performers
        worst_performers = self.data_processor.identify_worst_performers(
            room_analyses, 
            top_n=self.config.worst_performers_count,
            by_building=True
        )
        
        # Calculate summary statistics
        total_rooms = len(room_analyses)
        total_buildings = len(building_analyses)
        
        # Calculate average data quality
        quality_scores = [
            analysis.get('data_quality', {}).get('overall_score', 0)
            for analysis in room_analyses
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Count rooms with issues
        quality_issues = sum(1 for score in quality_scores if score < 0.8)
        comfort_issues = self._count_comfort_issues(room_analyses)
        
        report_data = {
            'generation_timestamp': datetime.now().isoformat(),
            'room_analyses': room_analyses,
            'building_analyses': building_analyses,
            'worst_performers': worst_performers,
            'summary_statistics': {
                'total_rooms': total_rooms,
                'total_buildings': total_buildings,
                'average_data_quality': avg_quality,
                'rooms_with_quality_issues': quality_issues,
                'rooms_with_comfort_issues': comfort_issues
            }
        }
        
        # Add IEQ data if provided
        if ieq_data_list:
            report_data['ieq_data_list'] = ieq_data_list
        
        return report_data
    
    def _generate_all_charts(
        self,
        report_data: Dict[str, Any],
        charts_dir: Path,
        filename_prefix: str
    ) -> Dict[str, str]:
        """Generate all standard charts for the report."""
        charts = {}
        
        try:
            # Worst performers chart
            worst_performers = report_data.get('worst_performers', {})
            if worst_performers:
                chart_result = self.graph_engine.create_worst_performers_chart(
                    worst_performers, GraphType.HORIZONTAL_BAR, self.config.worst_performers_count
                )
                
                if 'figure' in chart_result:
                    chart_path = self.graph_engine.save_figure(
                        chart_result['figure'],
                        charts_dir,
                        f"{filename_prefix}_worst_performers"
                    )
                    charts['worst_performers'] = chart_path
            
            # Compliance comparison chart
            room_analyses = report_data.get('room_analyses', [])
            if room_analyses:
                comparison_data = self.data_processor.prepare_comparison_data(
                    room_analyses, 'performance_score', 'building'
                )
                
                chart_result = self.graph_engine.create_compliance_comparison_chart(
                    comparison_data, GraphType.GROUPED_BAR
                )
                
                if 'figure' in chart_result:
                    chart_path = self.graph_engine.save_figure(
                        chart_result['figure'],
                        charts_dir,
                        f"{filename_prefix}_performance_comparison"
                    )
                    charts['performance_comparison'] = chart_path
            
            # Time series chart (if data available)
            if self.config.include_time_series and 'ieq_data_list' in report_data:
                ieq_data_list = report_data['ieq_data_list'][:5]  # Limit to first 5 for clarity
                
                time_series_data = self.data_processor.prepare_time_series_data(
                    ieq_data_list, ['temperature', 'co2'], 'D'  # Daily aggregation
                )
                
                chart_result = self.graph_engine.create_time_series_chart(
                    time_series_data, ['temperature', 'co2']
                )
                
                if 'figure' in chart_result:
                    chart_path = self.graph_engine.save_figure(
                        chart_result['figure'],
                        charts_dir,
                        f"{filename_prefix}_time_series"
                    )
                    charts['time_series'] = chart_path
            
            # Heatmap (if data available and requested)
            if self.config.include_heatmaps and 'ieq_data_list' in report_data and report_data['ieq_data_list']:
                ieq_data = report_data['ieq_data_list'][0]  # Use first dataset
                
                heatmap_data = self.data_processor.prepare_heatmap_data(
                    ieq_data, 'temperature', 'weekly_hourly'
                )
                
                chart_result = self.graph_engine.create_heatmap_chart(heatmap_data)
                
                if 'figure' in chart_result:
                    chart_path = self.graph_engine.save_figure(
                        chart_result['figure'],
                        charts_dir,
                        f"{filename_prefix}_temperature_heatmap"
                    )
                    charts['temperature_heatmap'] = chart_path
            
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
        
        logger.info(f"Generated {len(charts)} charts")
        return charts
    
    def _count_comfort_issues(self, room_analyses: List[Dict[str, Any]]) -> int:
        """Count rooms with comfort compliance issues."""
        issues = 0
        for analysis in room_analyses:
            comfort_analysis = analysis.get('comfort_analysis', {})
            for param, categories in comfort_analysis.items():
                category_ii = categories.get('II', {})
                if category_ii.get('compliance_percentage', 100) < 80:
                    issues += 1
                    break
        return issues
