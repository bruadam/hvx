"""
PDF Generator for IEQ Analytics Reports

Professional PDF report generation using WeasyPrint and Jinja2 with support for
HTML templates, charts, tables, and modern CSS styling.
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging
from io import BytesIO
import base64
import json

try:
    # Test import without loading the actual classes
    import importlib.util
    weasyprint_spec = importlib.util.find_spec("weasyprint")
    WEASYPRINT_AVAILABLE = weasyprint_spec is not None
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False
    pisa = None

try:
    import jinja2
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Environment = FileSystemLoader = Template = jinja2 = None

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class PDFStyle:
    """PDF styling configuration for WeasyPrint."""
    
    def __init__(self):
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint is required for PDF generation. Install with: pip install weasyprint")
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 is required for template rendering. Install with: pip install jinja2")
        
        # CSS styling
        self.css_styles = {
            'primary_color': '#2d5aa0',      # Dark blue
            'secondary_color': '#cce0ff',    # Light blue
            'accent_color': '#e67300',       # Orange
            'text_color': '#333333',         # Dark gray
            'background_color': '#ffffff',   # White
            'border_color': '#cccccc',       # Light gray
            'success_color': '#28a745',      # Green
            'warning_color': '#ffc107',      # Yellow
            'danger_color': '#dc3545',       # Red
            
            # Typography
            'font_family': 'Arial, sans-serif',
            'title_size': '28px',
            'subtitle_size': '20px',
            'heading_size': '16px',
            'body_size': '12px',
            'small_size': '10px',
            
            # Layout
            'page_margin': '20mm',
            'section_spacing': '20px',
            'table_spacing': '10px'
        }
    
    def get_simple_css(self) -> str:
        """Get simplified CSS styles compatible with xhtml2pdf."""
        return f"""
        body {{
            font-family: Arial, sans-serif;
            font-size: 11pt;
            color: #2c3e50;
            line-height: 1.6;
            margin: 20px;
        }}
        
        .title {{
            font-size: 24pt;
            font-weight: bold;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            font-size: 16pt;
            color: #34495e;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .generation-info {{
            font-size: 10pt;
            color: #7f8c8d;
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .section-header {{
            font-size: 14pt;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        
        .summary-box {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 3px;
        }}
        
        .key-finding {{
            margin-bottom: 10px;
        }}
        
        .recommendation {{
            margin-bottom: 10px;
            padding: 10px;
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        
        th, td {{
            border: 1px solid #dee2e6;
            padding: 8px;
            text-align: left;
        }}
        
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .room-id {{
            font-weight: bold;
        }}
        
        .building-id {{
            font-weight: bold;
        }}
        """
    
    def get_base_css(self) -> str:
        """Get base CSS styles for the PDF."""
        return f"""
        @page {{
            size: A4;
            margin: {self.css_styles['page_margin']};
            @top-left {{
                content: "IEQ Analytics Report";
                font-family: {self.css_styles['font_family']};
                font-size: {self.css_styles['small_size']};
                color: {self.css_styles['text_color']};
            }}
            @top-right {{
                content: counter(page) " / " counter(pages);
                font-family: {self.css_styles['font_family']};
                font-size: {self.css_styles['small_size']};
                color: {self.css_styles['text_color']};
            }}
        }}
        
        body {{
            font-family: {self.css_styles['font_family']};
            font-size: {self.css_styles['body_size']};
            color: {self.css_styles['text_color']};
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }}
        
        .title {{
            font-size: {self.css_styles['title_size']};
            color: {self.css_styles['primary_color']};
            text-align: center;
            margin-bottom: 30px;
            font-weight: bold;
        }}
        
        .subtitle {{
            font-size: {self.css_styles['subtitle_size']};
            color: {self.css_styles['primary_color']};
            text-align: center;
            margin-bottom: 20px;
            font-weight: bold;
        }}
        
        .section-header {{
            font-size: {self.css_styles['heading_size']};
            color: {self.css_styles['primary_color']};
            border-bottom: 2px solid {self.css_styles['primary_color']};
            padding-bottom: 5px;
            margin-top: {self.css_styles['section_spacing']};
            margin-bottom: 15px;
            font-weight: bold;
        }}
        
        .summary-box {{
            background-color: {self.css_styles['secondary_color']};
            border: 1px solid {self.css_styles['border_color']};
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
            margin: {self.css_styles['table_spacing']} 0;
        }}
        
        .metrics-table th {{
            background-color: {self.css_styles['primary_color']};
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: bold;
        }}
        
        .metrics-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid {self.css_styles['border_color']};
        }}
        
        .metrics-table tbody tr:nth-child(even) {{
            background-color: {self.css_styles['secondary_color']};
        }}
        
        .worst-performers-table {{
            width: 100%;
            border-collapse: collapse;
            margin: {self.css_styles['table_spacing']} 0;
            font-size: {self.css_styles['small_size']};
        }}
        
        .worst-performers-table th {{
            background-color: {self.css_styles['primary_color']};
            color: white;
            padding: 8px;
            text-align: center;
            font-weight: bold;
        }}
        
        .worst-performers-table td {{
            padding: 6px 8px;
            border-bottom: 1px solid {self.css_styles['border_color']};
            text-align: center;
        }}
        
        .worst-performers-table .room-id {{
            text-align: left;
            font-weight: bold;
        }}
        
        .worst-performers-table .issues {{
            text-align: left;
            font-size: 9px;
        }}
        
        .chart-container {{
            text-align: center;
            margin: 20px 0;
            page-break-inside: avoid;
        }}
        
        .chart-title {{
            font-size: {self.css_styles['heading_size']};
            color: {self.css_styles['primary_color']};
            margin-bottom: 10px;
            font-weight: bold;
        }}
        
        .chart-image {{
            max-width: 100%;
            height: auto;
            border: 1px solid {self.css_styles['border_color']};
            border-radius: 3px;
        }}
        
        .chart-commentary {{
            background-color: #f8f9fa;
            border-left: 4px solid {self.css_styles['primary_color']};
            padding: 15px;
            margin: 10px 0;
            border-radius: 0 5px 5px 0;
        }}
        
        .commentary-header {{
            font-weight: bold;
            color: {self.css_styles['primary_color']};
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .confidence-badge {{
            background-color: #e9ecef;
            color: #495057;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: normal;
        }}
        
        .commentary-summary {{
            margin-bottom: 10px;
            font-style: italic;
            color: #495057;
        }}
        
        .commentary-section {{
            margin: 8px 0;
        }}
        
        .commentary-section ul {{
            margin: 5px 0 0 0;
            padding-left: 20px;
        }}
        
        .commentary-section li {{
            margin: 3px 0;
            color: #495057;
        }}
        
        .recommendation {{
            margin: 8px 0;
            padding-left: 20px;
        }}
        
        .recommendation.high {{
            border-left: 4px solid {self.css_styles['danger_color']};
        }}
        
        .recommendation.medium {{
            border-left: 4px solid {self.css_styles['warning_color']};
        }}
        
        .recommendation.low {{
            border-left: 4px solid {self.css_styles['success_color']};
        }}
        
        .key-finding {{
            margin: 6px 0;
            padding: 5px 0;
            font-weight: bold;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        
        .generation-info {{
            font-size: {self.css_styles['small_size']};
            color: #666;
            text-align: center;
            margin-top: 40px;
        }}
        
        .building-overview-table {{
            width: 100%;
            border-collapse: collapse;
            margin: {self.css_styles['table_spacing']} 0;
        }}
        
        .building-overview-table th {{
            background-color: {self.css_styles['primary_color']};
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: bold;
        }}
        
        .building-overview-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid {self.css_styles['border_color']};
            text-align: center;
        }}
        
        .building-overview-table .building-id {{
            text-align: left;
            font-weight: bold;
        }}
        
        .building-overview-table .issues {{
            text-align: left;
        }}
        """


class PDFGenerator:
    """PDF generation engine using WeasyPrint and Jinja2."""
    
    def __init__(self, style: Optional[PDFStyle] = None, templates_dir: Optional[Path] = None):
        if not WEASYPRINT_AVAILABLE and not XHTML2PDF_AVAILABLE:
            raise ImportError("Either WeasyPrint or xhtml2pdf is required for PDF generation. Install with: pip install weasyprint or pip install xhtml2pdf")
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 is required for template rendering. Install with: pip install jinja2")
        
        self.style = style or PDFStyle()
        self.use_weasyprint = WEASYPRINT_AVAILABLE
        
        # Set up Jinja2 environment
        if templates_dir and templates_dir.exists():
            self.jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(templates_dir)))
        else:
            # Use string templates if no templates directory
            self.jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('.'))
        
        # Add custom filters
        self.jinja_env.filters['format_number'] = self._format_number
        self.jinja_env.filters['format_percentage'] = self._format_percentage
        self.jinja_env.filters['format_datetime'] = self._format_datetime
        
        logger.info(f"PDF Generator initialized with {'WeasyPrint' if self.use_weasyprint else 'xhtml2pdf'}")
    
    def create_executive_summary_report(
        self,
        analysis_data: Dict[str, Any],
        output_path: Path,
        include_charts: bool = True
    ) -> str:
        """
        Create executive summary report using HTML template.
        
        Args:
            analysis_data: Complete analysis results
            output_path: Output file path
            include_charts: Whether to include charts
            
        Returns:
            Path to generated PDF file
        """
        logger.info("Generating executive summary report with WeasyPrint")
        
        # Prepare template data
        template_data = self._prepare_template_data(analysis_data, include_charts)
        
        # Render HTML template
        html_content = self._render_executive_summary_template(template_data)
        
        # Generate PDF
        css_content = self.style.get_base_css()
        
        try:
            if self.use_weasyprint and WEASYPRINT_AVAILABLE:
                try:
                    from weasyprint import HTML, CSS
                    html_doc = HTML(string=html_content)
                    css_doc = CSS(string=css_content)
                    html_doc.write_pdf(str(output_path), stylesheets=[css_doc])
                except (ImportError, OSError) as e:
                    logger.warning(f"WeasyPrint failed: {e}. Falling back to xhtml2pdf")
                    self.use_weasyprint = False  # Switch to fallback for future calls
                    self._generate_pdf_with_xhtml2pdf(html_content, css_content, output_path)
            else:
                # Use xhtml2pdf fallback
                self._generate_pdf_with_xhtml2pdf(html_content, css_content, output_path)
            
            logger.info(f"Executive summary report generated: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise
    
    def create_technical_report(
        self,
        analysis_data: Dict[str, Any],
        output_path: Path,
        include_detailed_charts: bool = True
    ) -> str:
        """
        Create detailed technical report using HTML template.
        
        Args:
            analysis_data: Complete analysis results
            output_path: Output file path
            include_detailed_charts: Whether to include detailed charts
            
        Returns:
            Path to generated PDF file
        """
        logger.info("Generating technical report with WeasyPrint")
        
        # Prepare template data
        template_data = self._prepare_template_data(analysis_data, include_detailed_charts)
        template_data['report_type'] = 'technical'
        
        # Render HTML template
        html_content = self._render_technical_report_template(template_data)
        
        # Generate PDF
        css_content = self.style.get_base_css()
        
        try:
            if self.use_weasyprint and WEASYPRINT_AVAILABLE:
                try:
                    from weasyprint import HTML, CSS
                    html_doc = HTML(string=html_content)
                    css_doc = CSS(string=css_content)
                    html_doc.write_pdf(str(output_path), stylesheets=[css_doc])
                except (ImportError, OSError) as e:
                    logger.warning(f"WeasyPrint failed: {e}. Falling back to xhtml2pdf")
                    self.use_weasyprint = False  # Switch to fallback for future calls
                    self._generate_pdf_with_xhtml2pdf(html_content, css_content, output_path)
            else:
                # Use xhtml2pdf fallback
                self._generate_pdf_with_xhtml2pdf(html_content, css_content, output_path)
            
            logger.info(f"Technical report generated: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise
    
    def _prepare_template_data(
        self,
        analysis_data: Dict[str, Any],
        include_charts: bool = True
    ) -> Dict[str, Any]:
        """Prepare data for template rendering."""
        # Convert charts to base64 encoded images if they exist
        charts_b64 = {}
        chart_commentaries = {}
        
        if include_charts and 'charts' in analysis_data:
            charts_b64 = self._encode_charts_to_base64(analysis_data['charts'])
            chart_commentaries = self._extract_chart_commentaries(analysis_data)
        
        template_data = {
            'title': 'IEQ Analytics Report',
            'generation_date': datetime.now(),
            'analysis_data': analysis_data,
            'charts': charts_b64,
            'chart_commentaries': chart_commentaries,
            'include_charts': include_charts,
            'summary_stats': analysis_data.get('summary_statistics', {}),
            'worst_performers': analysis_data.get('worst_performers', {}),
            'building_analyses': analysis_data.get('building_analyses', {}),
            'room_analyses': analysis_data.get('room_analyses', [])
        }
        
        return template_data
    
    def _encode_charts_to_base64(self, charts: Dict[str, str]) -> Dict[str, str]:
        """Convert chart file paths to base64 encoded images."""
        charts_b64 = {}
        
        for chart_name, chart_path in charts.items():
            try:
                chart_file = Path(chart_path)
                if chart_file.exists():
                    with open(chart_file, 'rb') as img_file:
                        img_data = img_file.read()
                        img_b64 = base64.b64encode(img_data).decode('utf-8')
                        charts_b64[chart_name] = f"data:image/png;base64,{img_b64}"
                else:
                    logger.warning(f"Chart file not found: {chart_path}")
            except Exception as e:
                logger.error(f"Failed to encode chart {chart_name}: {e}")
        
        return charts_b64
    
    def _extract_chart_commentaries(self, analysis_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Extract AI-generated chart commentaries from analysis data."""
        commentaries = {}
        
        # Look for AI analysis results in the data
        if 'ai_chart_analyses' in analysis_data:
            ai_analyses = analysis_data['ai_chart_analyses']
            for chart_name, analysis in ai_analyses.items():
                if isinstance(analysis, dict):
                    commentaries[chart_name] = {
                        'summary': analysis.get('final_commentary', analysis.get('ai_commentary', '')),
                        'insights': analysis.get('key_insights', []),
                        'actions': analysis.get('suggested_actions', []),
                        'confidence': analysis.get('confidence_score', 0.0)
                    }
                else:
                    # Handle analysis objects
                    commentaries[chart_name] = {
                        'summary': getattr(analysis, 'final_commentary', None) or getattr(analysis, 'ai_commentary', ''),
                        'insights': getattr(analysis, 'key_insights', []),
                        'actions': getattr(analysis, 'suggested_actions', []),
                        'confidence': getattr(analysis, 'confidence_score', 0.0)
                    }
        
        # Provide default commentary for charts without AI analysis
        if 'charts' in analysis_data:
            for chart_name in analysis_data['charts'].keys():
                if chart_name not in commentaries:
                    commentaries[chart_name] = {
                        'summary': self._generate_default_commentary(chart_name),
                        'insights': [],
                        'actions': [],
                        'confidence': 0.0
                    }
        
        return commentaries
    
    def _generate_default_commentary(self, chart_name: str) -> str:
        """Generate default commentary for charts without AI analysis."""
        chart_type_map = {
            'worst_performers': 'This chart identifies the rooms with the lowest IEQ performance scores, highlighting priority areas for intervention and improvement.',
            'performance_comparison': 'This visualization compares IEQ performance across different buildings, revealing systematic differences in environmental management effectiveness.',
            'time_series': 'This time series analysis shows temporal patterns in environmental conditions, revealing daily, weekly, or seasonal trends in IEQ parameters.',
            'heatmap': 'This heatmap visualizes the spatial distribution of environmental conditions, helping identify hot spots or problem areas that require attention.',
            'temperature': 'This chart displays temperature measurements and compliance with EN 16798-1 standards for thermal comfort.',
            'humidity': 'This visualization shows humidity levels and their relationship to occupant comfort and indoor air quality standards.',
            'co2': 'This chart presents CO2 concentration data, indicating ventilation effectiveness and indoor air quality levels.',
            'compliance': 'This analysis shows compliance rates with IEQ standards across different parameters and spaces.'
        }
        
        # Find matching commentary based on chart name
        for key, commentary in chart_type_map.items():
            if key.lower() in chart_name.lower():
                return commentary
        
        # Default commentary
        return f"This chart presents {chart_name.replace('_', ' ')} data analysis, providing insights into indoor environmental quality performance and compliance."
    
    def _render_executive_summary_template(self, template_data: Dict[str, Any]) -> str:
        """Render executive summary HTML template."""
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{{ title }}</title>
        </head>
        <body>
            <!-- Title Page -->
            <div class="title">{{ title }}</div>
            <div class="subtitle">Executive Summary</div>
            
            {% if summary_stats %}
            <div class="subtitle">Analysis of {{ summary_stats.total_rooms }} rooms across {{ summary_stats.total_buildings }} buildings</div>
            {% endif %}
            
            <div class="generation-info">
                Generated on: {{ generation_date | format_datetime }}
            </div>
            
            <div class="page-break"></div>
            
            <!-- Executive Summary Section -->
            <div class="section-header">Executive Summary</div>
            
            <div class="summary-box">
                {% if summary_stats %}
                <p><strong>Overall Assessment:</strong> This analysis covers {{ summary_stats.total_rooms }} rooms across {{ summary_stats.total_buildings }} buildings, evaluating indoor environmental quality based on temperature, humidity, CO2 levels, and data quality metrics.</p>
                
                <p><strong>Key Results:</strong> The average data quality score is {{ summary_stats.average_data_quality | format_number(3) }}, with {{ summary_stats.rooms_with_quality_issues }} rooms showing data quality issues and {{ summary_stats.rooms_with_comfort_issues }} rooms experiencing comfort compliance problems.</p>
                
                <p><strong>Priority Areas:</strong> Immediate attention should be given to worst-performing spaces and systematic improvements to ventilation and environmental control systems.</p>
                {% else %}
                <p>Analysis completed successfully. Detailed metrics and recommendations are provided in the sections below.</p>
                {% endif %}
            </div>
            
            <!-- Key Metrics Table -->
            {% if summary_stats %}
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Total Rooms Analyzed</td>
                        <td>{{ summary_stats.total_rooms }}</td>
                    </tr>
                    <tr>
                        <td>Total Buildings</td>
                        <td>{{ summary_stats.total_buildings }}</td>
                    </tr>
                    <tr>
                        <td>Average Data Quality</td>
                        <td>{{ summary_stats.average_data_quality | format_number(3) }}</td>
                    </tr>
                    <tr>
                        <td>Rooms with Quality Issues</td>
                        <td>{{ summary_stats.rooms_with_quality_issues }}</td>
                    </tr>
                    <tr>
                        <td>Rooms with Comfort Issues</td>
                        <td>{{ summary_stats.rooms_with_comfort_issues }}</td>
                    </tr>
                </tbody>
            </table>
            {% endif %}
            
            <!-- Key Findings -->
            <div class="section-header">Key Findings</div>
            
            {% set key_findings = [] %}
            {% if summary_stats %}
                {% if summary_stats.rooms_with_quality_issues > 0 %}
                    {% set _ = key_findings.append(summary_stats.rooms_with_quality_issues ~ " rooms (" ~ ((summary_stats.rooms_with_quality_issues / summary_stats.total_rooms) * 100) | format_percentage ~ ") have data quality issues requiring attention") %}
                {% endif %}
                {% if summary_stats.rooms_with_comfort_issues > 0 %}
                    {% set _ = key_findings.append(summary_stats.rooms_with_comfort_issues ~ " rooms (" ~ ((summary_stats.rooms_with_comfort_issues / summary_stats.total_rooms) * 100) | format_percentage ~ ") have comfort compliance issues") %}
                {% endif %}
            {% endif %}
            
            {% if worst_performers and worst_performers.summary_statistics %}
                {% set avg_score = worst_performers.summary_statistics.performance_scores.mean %}
                {% set _ = key_findings.append("Average performance score across all rooms is " ~ avg_score ~ "/100") %}
            {% endif %}
            
            {% if key_findings | length == 0 %}
                {% set _ = key_findings.append("Analysis completed successfully with no major issues identified") %}
                {% set _ = key_findings.append("Continued monitoring recommended to maintain optimal conditions") %}
            {% endif %}
            
            {% for finding in key_findings %}
            <div class="key-finding">{{ loop.index }}. {{ finding }}</div>
            {% endfor %}
            
            <!-- Worst Performers Section -->
            {% if worst_performers and worst_performers.overall_worst %}
            <div class="section-header">Worst Performing Rooms</div>
            
            <table class="worst-performers-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Room ID</th>
                        <th>Building</th>
                        <th>Performance Score</th>
                        <th>Primary Issues</th>
                    </tr>
                </thead>
                <tbody>
                    {% for room in worst_performers.overall_worst[:10] %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td class="room-id">{{ room.room_id }}</td>
                        <td>{{ room.building_id }}</td>
                        <td>{{ room.performance_score | format_number(1) }}</td>
                        <td class="issues">
                            {% if room.issues %}
                                {{ room.issues[:2] | join(', ') }}
                                {% if room.issues | length > 2 %}...{% endif %}
                            {% else %}
                                None identified
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
            
            <!-- Building Overview -->
            {% if building_analyses %}
            <div class="section-header">Building Overview</div>
            
            <table class="building-overview-table">
                <thead>
                    <tr>
                        <th>Building ID</th>
                        <th>Rooms</th>
                        <th>Avg Quality Score</th>
                        <th>Major Issues</th>
                    </tr>
                </thead>
                <tbody>
                    {% for building_id, analysis in building_analyses.items() %}
                    {% set quality_score = analysis.data_quality_summary.average_quality_score %}
                    {% set room_count = analysis.room_count %}
                    {% set recommendations = analysis.building_recommendations %}
                    
                    <tr>
                        <td class="building-id">{{ building_id }}</td>
                        <td>{{ room_count }}</td>
                        <td>{{ quality_score | format_number(3) }}</td>
                        <td class="issues">
                            {% set major_issues = [] %}
                            {% for rec in recommendations[:2] %}
                                {% if 'temperature' in rec.lower() %}
                                    {% set _ = major_issues.append('Temperature') %}
                                {% elif 'humidity' in rec.lower() %}
                                    {% set _ = major_issues.append('Humidity') %}
                                {% elif 'co2' in rec.lower() %}
                                    {% set _ = major_issues.append('CO2') %}
                                {% elif 'data' in rec.lower() %}
                                    {% set _ = major_issues.append('Data Quality') %}
                                {% endif %}
                            {% endfor %}
                            {{ major_issues | join(', ') if major_issues else 'None identified' }}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
            
            <!-- Recommendations -->
            <div class="section-header">Recommendations</div>
            
            {% set recommendations = [] %}
            {% if building_analyses %}
                {% for building_id, analysis in building_analyses.items() %}
                    {% for rec in analysis.building_recommendations[:2] %}
                        {% set clean_rec = rec | replace('🌡️', '') | replace('💧', '') | replace('🫁', '') | replace('📊', '') | trim %}
                        {% set _ = recommendations.append(('High', building_id ~ ': ' ~ clean_rec)) %}
                    {% endfor %}
                {% endfor %}
            {% endif %}
            
            {% if worst_performers and worst_performers.overall_worst %}
                {% set top_issues = {} %}
                {% for room in worst_performers.overall_worst[:5] %}
                    {% for issue in room.issues %}
                        {% if issue not in top_issues %}
                            {% set _ = top_issues.update({issue: 0}) %}
                        {% endif %}
                        {% set _ = top_issues.update({issue: top_issues[issue] + 1}) %}
                    {% endfor %}
                {% endfor %}
                
                {% for issue, count in top_issues.items() | sort(attribute='1', reverse=true) %}
                    {% if loop.index <= 3 %}
                        {% set _ = recommendations.append(('Medium', 'Address ' ~ issue.lower() ~ ' affecting ' ~ count ~ ' rooms')) %}
                    {% endif %}
                {% endfor %}
            {% endif %}
            
            {% if recommendations | length == 0 %}
                {% set _ = recommendations.append(('Low', 'Continue regular monitoring of all IEQ parameters')) %}
                {% set _ = recommendations.append(('Low', 'Review and update sensor calibration schedules')) %}
                {% set _ = recommendations.append(('Low', 'Implement preventive maintenance for HVAC systems')) %}
            {% endif %}
            
            {% for priority, rec in recommendations[:10] %}
            <div class="recommendation {{ priority.lower() }}">
                <strong>Priority {{ priority }}:</strong> {{ rec }}
            </div>
            {% endfor %}
            
            <!-- Charts Section -->
            {% if include_charts and charts %}
            <div class="page-break"></div>
            <div class="section-header">Key Performance Charts</div>
            
            {% for chart_name, chart_data in charts.items() %}
            <div class="chart-container">
                <div class="chart-title">{{ chart_name | replace('_', ' ') | title }}</div>
                <img src="{{ chart_data }}" alt="{{ chart_name }}" class="chart-image">
                
                <!-- AI Commentary Section -->
                {% if chart_commentaries and chart_name in chart_commentaries %}
                {% set commentary = chart_commentaries[chart_name] %}
                <div class="chart-commentary">
                    <div class="commentary-header">
                        📊 Chart Analysis
                        {% if commentary.confidence > 0 %}
                        <span class="confidence-badge">AI Confidence: {{ (commentary.confidence * 100) | round }}%</span>
                        {% endif %}
                    </div>
                    
                    <div class="commentary-summary">
                        {{ commentary.summary }}
                    </div>
                    
                    {% if commentary.insights %}
                    <div class="commentary-section">
                        <strong>Key Insights:</strong>
                        <ul>
                        {% for insight in commentary.insights %}
                            <li>{{ insight }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    
                    {% if commentary.actions %}
                    <div class="commentary-section">
                        <strong>Recommended Actions:</strong>
                        <ul>
                        {% for action in commentary.actions %}
                            <li>{{ action }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
            {% endif %}
            
        </body>
        </html>
        """
        
        template = self.jinja_env.from_string(template_str)
        return template.render(template_data)
    
    def _render_technical_report_template(self, template_data: Dict[str, Any]) -> str:
        """Render technical report HTML template."""
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{{ title }} - Technical Report</title>
        </head>
        <body>
            <!-- Title Page -->
            <div class="title">{{ title }}</div>
            <div class="subtitle">Technical Report</div>
            
            {% if summary_stats %}
            <div class="subtitle">Detailed Analysis of {{ summary_stats.total_rooms }} rooms across {{ summary_stats.total_buildings }} buildings</div>
            {% endif %}
            
            <div class="generation-info">
                Generated on: {{ generation_date | format_datetime }}
            </div>
            
            <div class="page-break"></div>
            
            <!-- Methodology Section -->
            <div class="section-header">Methodology</div>
            
            <div class="summary-box">
                <p>This analysis follows the EN 16798-1:2019 standard for Indoor Environmental Quality assessment. Data quality, comfort compliance, and performance metrics are calculated based on continuous monitoring data from IoT sensors deployed across all analyzed spaces.</p>
                
                <p><strong>Analysis Framework:</strong></p>
                <ul>
                    <li>Data Quality Assessment: Completeness, consistency, and temporal coverage</li>
                    <li>Comfort Compliance: Temperature, humidity, and CO2 levels against EN standards</li>
                    <li>Performance Scoring: Weighted combination of all quality and comfort metrics</li>
                    <li>Statistical Analysis: Temporal patterns, correlations, and outlier detection</li>
                </ul>
            </div>
            
            <!-- Data Quality Assessment -->
            <div class="section-header">Data Quality Assessment</div>
            
            {% if summary_stats %}
            <p>Data quality analysis across {{ summary_stats.total_rooms }} rooms reveals an average quality score of {{ summary_stats.average_data_quality | format_number(3) }}. {{ summary_stats.rooms_with_quality_issues }} rooms show data quality issues requiring attention.</p>
            {% endif %}
            
            <div class="summary-box">
                <p><strong>Quality Criteria:</strong></p>
                <ul>
                    <li>Data Completeness: Percentage of expected data points received</li>
                    <li>Missing Data Periods: Identification of significant data gaps</li>
                    <li>Duplicate Timestamps: Detection of sensor synchronization issues</li>
                    <li>Overall Score: Composite metric incorporating all quality factors</li>
                </ul>
            </div>
            
            <!-- Detailed Room Analysis -->
            {% if room_analyses %}
            <div class="section-header">Room-by-Room Analysis Summary</div>
            
            <p>Detailed analysis of {{ room_analyses | length }} rooms shows varying performance across different spaces and buildings. The following summary provides key insights:</p>
            
            <div class="summary-box">
                <p><strong>Performance Distribution:</strong></p>
                <ul>
                    <li>High Performers (Score ≥ 80): {{ room_analyses | selectattr('performance_score', '>=', 80) | list | length }} rooms</li>
                    <li>Moderate Performers (Score 60-79): {{ room_analyses | selectattr('performance_score', '>=', 60) | selectattr('performance_score', '<', 80) | list | length }} rooms</li>
                    <li>Poor Performers (Score < 60): {{ room_analyses | selectattr('performance_score', '<', 60) | list | length }} rooms</li>
                </ul>
            </div>
            {% endif %}
            
            <!-- Building-Level Analysis -->
            {% if building_analyses %}
            <div class="section-header">Building-Level Analysis</div>
            
            {% for building_id, analysis in building_analyses.items() %}
            <div class="summary-box">
                <h4>{{ building_id }}</h4>
                <p><strong>Rooms:</strong> {{ analysis.room_count }}</p>
                <p><strong>Average Quality Score:</strong> {{ analysis.data_quality_summary.average_quality_score | format_number(3) }}</p>
                <p><strong>Rooms Below Quality Threshold:</strong> {{ analysis.data_quality_summary.rooms_below_threshold }}</p>
                
                {% if analysis.building_recommendations %}
                <p><strong>Key Recommendations:</strong></p>
                <ul>
                    {% for rec in analysis.building_recommendations[:3] %}
                    <li>{{ rec | replace('🌡️', '') | replace('💧', '') | replace('🫁', '') | replace('📊', '') | trim }}</li>
                    {% endfor %}
                </ul>
                {% endif %}
            </div>
            {% endfor %}
            {% endif %}
            
            <!-- Compliance Analysis -->
            <div class="section-header">Compliance Analysis</div>
            
            <div class="summary-box">
                <p>Compliance analysis is based on EN 16798-1:2019 Category II standards for office environments:</p>
                <ul>
                    <li><strong>Temperature:</strong> 20-24°C during heating season, 22-26°C during non-heating season</li>
                    <li><strong>Humidity:</strong> 25-60% relative humidity</li>
                    <li><strong>CO2:</strong> Maximum 800 ppm above outdoor levels</li>
                </ul>
            </div>
            
            <!-- Technical Charts -->
            {% if include_charts and charts %}
            <div class="page-break"></div>
            <div class="section-header">Technical Charts and Visualizations</div>
            
            {% for chart_name, chart_data in charts.items() %}
            <div class="chart-container">
                <div class="chart-title">{{ chart_name | replace('_', ' ') | title }}</div>
                <img src="{{ chart_data }}" alt="{{ chart_name }}" class="chart-image">
                
                <!-- AI Commentary Section -->
                {% if chart_commentaries and chart_name in chart_commentaries %}
                {% set commentary = chart_commentaries[chart_name] %}
                <div class="chart-commentary">
                    <div class="commentary-header">
                        🔬 Technical Analysis
                        {% if commentary.confidence > 0 %}
                        <span class="confidence-badge">AI Confidence: {{ (commentary.confidence * 100) | round }}%</span>
                        {% endif %}
                    </div>
                    
                    <div class="commentary-summary">
                        {{ commentary.summary }}
                    </div>
                    
                    {% if commentary.insights %}
                    <div class="commentary-section">
                        <strong>Technical Insights:</strong>
                        <ul>
                        {% for insight in commentary.insights %}
                            <li>{{ insight }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    
                    {% if commentary.actions %}
                    <div class="commentary-section">
                        <strong>Technical Recommendations:</strong>
                        <ul>
                        {% for action in commentary.actions %}
                            <li>{{ action }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                </div>
                {% else %}
                <!-- Default commentary for technical context -->
                {% if chart_name == 'worst_performers' %}
                <div class="chart-commentary">
                    <div class="commentary-header">📋 Technical Notes</div>
                    <div class="commentary-summary">
                        This chart shows the rooms with the lowest performance scores, indicating priority areas for intervention.
                    </div>
                </div>
                {% elif chart_name == 'performance_comparison' %}
                <div class="chart-commentary">
                    <div class="commentary-header">📋 Technical Notes</div>
                    <div class="commentary-summary">
                        Performance comparison across buildings reveals systematic differences in IEQ management effectiveness.
                    </div>
                </div>
                {% elif chart_name == 'time_series' %}
                <div class="chart-commentary">
                    <div class="commentary-header">📋 Technical Notes</div>
                    <div class="commentary-summary">
                        Time series analysis shows temporal patterns and identifies periods of concern or optimal performance.
                    </div>
                </div>
                {% endif %}
                {% endif %}
            </div>
            {% endfor %}
            {% endif %}
            
            <!-- Appendices -->
            <div class="page-break"></div>
            <div class="section-header">Appendices</div>
            
            <div class="summary-box">
                <h4>A. Standards and References</h4>
                <ul>
                    <li>EN 16798-1:2019 - Energy performance of buildings - Ventilation for buildings</li>
                    <li>ASHRAE Standard 62.1 - Ventilation for Acceptable Indoor Air Quality</li>
                    <li>WHO Guidelines for Indoor Air Quality</li>
                </ul>
                
                <h4>B. Analysis Parameters</h4>
                <ul>
                    <li>Analysis Period: {{ analysis_data.generation_timestamp | format_datetime }}</li>
                    <li>Data Processing: Hourly aggregation with quality filtering</li>
                    <li>Performance Weighting: Temperature (30%), CO2 (40%), Humidity (20%), Data Quality (10%)</li>
                </ul>
            </div>
            
        </body>
        </html>
        """
        
        template = self.jinja_env.from_string(template_str)
        return template.render(template_data)
    
    # Jinja2 filter functions
    def _safe_get(self, d: Dict, key: str, default: str = 'N/A') -> str:
        """Safely get value from dictionary."""
        try:
            value = d.get(key, default) if isinstance(d, dict) else default
            return str(value)
        except Exception:
            return str(default)
    
    def _format_number(self, value: Any, decimals: int = 2) -> str:
        """Format number with specified decimal places."""
        try:
            return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)
    
    def _format_percentage(self, value: Any, decimals: int = 1) -> str:
        """Format percentage with specified decimal places."""
        try:
            return f"{float(value):.{decimals}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    def _format_datetime(self, value: Any, format_str: str = "%B %d, %Y at %I:%M %p") -> str:
        """Format datetime with specified format."""
        try:
            if isinstance(value, str):
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif isinstance(value, datetime):
                pass
            else:
                return str(value)
            
            return value.strftime(format_str)
        except (ValueError, TypeError):
            return str(value)
    
    def _generate_pdf_with_xhtml2pdf(self, html_content: str, css_content: str, output_path: Path):
        """Generate PDF using xhtml2pdf fallback."""
        if not XHTML2PDF_AVAILABLE or pisa is None:
            raise ImportError("xhtml2pdf is required for PDF generation fallback")
        
        # Use simple CSS for xhtml2pdf compatibility
        simple_css = self.style.get_simple_css()
        
        # Combine CSS with HTML
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            {simple_css}
            </style>
        </head>
        <body>
        {html_content.split('<body>')[1].split('</body>')[0] if '<body>' in html_content else html_content}
        </body>
        </html>
        """
        
        # Generate PDF
        with open(output_path, 'wb') as result_file:
            pisa_status = pisa.CreatePDF(full_html, dest=result_file)
            
        # Simple success check
        if not Path(output_path).exists() or Path(output_path).stat().st_size == 0:
            raise Exception(f"xhtml2pdf generation failed - output file not created or empty")
        
        logger.info(f"PDF generated using xhtml2pdf: {output_path}")
