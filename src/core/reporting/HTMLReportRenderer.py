"""
HTML Report Renderer

Generates HTML reports from YAML templates and analysis data.
Supports charts, tables, recommendations, and custom sections.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template

from src.core.graphs.GraphService import GraphService
from src.core.analytics.ieq.SmartRecommendationService import SmartRecommendationService


class HTMLReportRenderer:
    """Renders HTML reports from YAML configuration and analysis data."""

    def __init__(self, templates_dir: Path = None):
        """
        Initialize HTML report renderer.

        Args:
            templates_dir: Directory containing HTML Jinja2 templates
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "html_templates"

        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )

        # Services
        self.graph_service = GraphService()
        self.rec_service = SmartRecommendationService()

        # Output directories
        self.output_dir = Path("output/reports")
        self.charts_dir = Path("output/reports/charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def render_report(
        self,
        config_path: Path,
        analysis_results: Any,
        dataset: Any = None,
        weather_data: Any = None,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Render HTML report from YAML configuration.

        Args:
            config_path: Path to YAML report configuration
            analysis_results: HierarchicalAnalysisResult object
            dataset: BuildingDataset object (optional)
            weather_data: Weather DataFrame (optional)
            output_filename: Custom output filename (optional)

        Returns:
            Dictionary with report metadata
        """
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Set output filename
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            template_id = config.get('template_id', 'report')
            output_filename = f"{template_id}_{timestamp}.html"

        output_path = self.output_dir / output_filename

        # Generate charts
        chart_paths = self._generate_charts(config, analysis_results)

        # Generate recommendations if needed
        recommendations = None
        if self._has_recommendation_section(config):
            recommendations = self._generate_recommendations(
                config,
                dataset,
                analysis_results,
                weather_data
            )

        # Prepare data for template
        template_data = {
            'config': config,
            'analysis_results': analysis_results,
            'chart_paths': chart_paths,
            'recommendations': recommendations,
            'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'dataset': dataset
        }

        # Render HTML
        html_content = self._render_html(config, template_data)

        # Save HTML
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return {
            'template_id': config.get('template_id'),
            'output_path': str(output_path),
            'format': 'html',
            'charts_generated': len(chart_paths),
            'file_size': output_path.stat().st_size,
            'status': 'success'
        }

    def _generate_charts(
        self,
        config: Dict[str, Any],
        analysis_results: Any
    ) -> Dict[str, Path]:
        """Generate all charts required by the template."""
        chart_paths = {}

        sections = config.get('sections', [])

        for section in sections:
            if section.get('type') == 'charts':
                charts = section.get('charts', [])

                for chart_config in charts:
                    chart_id = chart_config['id']

                    # Prepare chart data from analysis
                    chart_data = self._prepare_chart_data(chart_id, analysis_results)

                    # Generate chart
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = self.charts_dir / f"{chart_id}_{timestamp}.png"

                    try:
                        result = self.graph_service.render_chart(
                            chart_id=chart_id,
                            data=chart_data,
                            config=chart_config.get('config', {}),
                            output_path=output_path
                        )
                        chart_paths[chart_id] = output_path
                    except Exception as e:
                        print(f"Warning: Could not generate chart {chart_id}: {e}")
                        # Use dummy data
                        try:
                            result = self.graph_service.preview_with_dummy_data(
                                chart_id=chart_id,
                                output_path=output_path
                            )
                            chart_paths[chart_id] = output_path
                        except:
                            pass

        return chart_paths

    def _prepare_chart_data(
        self,
        chart_id: str,
        analysis_results: Any
    ) -> Dict[str, Any]:
        """Prepare chart data from analysis results."""
        # This would extract relevant data from analysis_results
        # For now, use dummy data as fallback
        try:
            return self.graph_service._load_dummy_data(chart_id)
        except:
            return {}

    def _has_recommendation_section(self, config: Dict[str, Any]) -> bool:
        """Check if config has a recommendations section."""
        sections = config.get('sections', [])
        return any(s.get('type') == 'recommendations' for s in sections)

    def _generate_recommendations(
        self,
        config: Dict[str, Any],
        dataset: Any,
        analysis_results: Any,
        weather_data: Any
    ) -> Optional[Any]:
        """Generate recommendations if dataset is available."""
        if dataset is None or analysis_results is None:
            return None

        try:
            portfolio_recs = self.rec_service.generate_portfolio_recommendations(
                dataset=dataset,
                analysis_results=analysis_results,
                weather_data=weather_data,
                auto_run_prerequisites=True,
                top_n=20
            )
            return portfolio_recs
        except Exception as e:
            print(f"Warning: Could not generate recommendations: {e}")
            return None

    def _render_html(
        self,
        config: Dict[str, Any],
        template_data: Dict[str, Any]
    ) -> str:
        """Render HTML from configuration and data."""
        # Build HTML manually if Jinja2 template doesn't exist
        theme = config.get('report', {}).get('theme', 'modern')
        style_config = config.get('style', {})

        html = self._build_html_structure(config, template_data, style_config)

        return html

    def _build_html_structure(
        self,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        style_config: Dict[str, Any]
    ) -> str:
        """Build HTML structure from configuration."""
        report_config = config.get('report', {})
        title = report_config.get('title', 'IEQ Report')
        subtitle = report_config.get('subtitle', '')

        # Start HTML
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>{title}</title>',
            self._generate_css(style_config),
            '</head>',
            '<body>',
        ]

        # Header
        html_parts.append('<div class="container">')
        html_parts.append(f'<header class="report-header">')
        html_parts.append(f'    <h1>{title}</h1>')
        if subtitle:
            html_parts.append(f'    <p class="subtitle">{subtitle}</p>')
        html_parts.append(f'    <p class="meta">Generated: {template_data["generated_date"]}</p>')
        html_parts.append('</header>')

        # Process sections
        sections = config.get('sections', [])
        for section in sections:
            html_parts.append(self._render_section(section, template_data))

        # Footer
        html_parts.append('<footer class="report-footer">')
        html_parts.append(f'    <p>Generated by HVX Analytics | {template_data["generated_date"]}</p>')
        html_parts.append('</footer>')

        html_parts.extend([
            '</div>',
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)

    def _generate_css(self, style_config: Dict[str, Any]) -> str:
        """Generate CSS styles."""
        primary = style_config.get('primary_color', '#2196F3')
        secondary = style_config.get('secondary_color', '#4CAF50')
        warning = style_config.get('warning_color', '#FF9800')
        critical = style_config.get('critical_color', '#F44336')
        text = style_config.get('text_color', '#333333')
        bg = style_config.get('background_color', '#FFFFFF')
        font_family = style_config.get('font_family', 'Helvetica, Arial, sans-serif')

        return f'''
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: {font_family};
            color: {text};
            background-color: {bg};
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        .report-header {{
            text-align: center;
            margin-bottom: 50px;
            padding-bottom: 30px;
            border-bottom: 2px solid {primary};
        }}

        .report-header h1 {{
            font-size: 2.5em;
            color: {primary};
            margin-bottom: 10px;
        }}

        .report-header .subtitle {{
            font-size: 1.3em;
            color: #666;
            margin-bottom: 10px;
        }}

        .report-header .meta {{
            color: #999;
            font-size: 0.9em;
        }}

        .section {{
            margin-bottom: 50px;
            page-break-inside: avoid;
        }}

        .section-title {{
            font-size: 2em;
            color: {primary};
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }}

        .section-content {{
            padding: 20px 0;
        }}

        .chart-container {{
            margin: 30px 0;
            text-align: center;
        }}

        .chart-container img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .chart-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #555;
        }}

        .summary-box {{
            background: #f5f5f5;
            border-left: 4px solid {primary};
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .recommendation {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .recommendation.critical {{
            border-left: 4px solid {critical};
        }}

        .recommendation.high {{
            border-left: 4px solid {warning};
        }}

        .recommendation.medium {{
            border-left: 4px solid {secondary};
        }}

        .recommendation.low {{
            border-left: 4px solid #999;
        }}

        .recommendation-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .recommendation-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }}

        .priority-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            color: white;
            text-transform: uppercase;
        }}

        .priority-badge.critical {{ background: {critical}; }}
        .priority-badge.high {{ background: {warning}; }}
        .priority-badge.medium {{ background: {secondary}; }}
        .priority-badge.low {{ background: #999; }}

        .recommendation-description {{
            color: #666;
            margin-bottom: 15px;
            line-height: 1.6;
        }}

        .recommendation-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }}

        .recommendation-detail {{
            font-size: 0.9em;
        }}

        .recommendation-detail strong {{
            color: #555;
            display: block;
            margin-bottom: 5px;
        }}

        .rationale-list {{
            list-style: none;
            padding-left: 0;
            margin-top: 10px;
        }}

        .rationale-list li {{
            padding: 8px 0 8px 25px;
            position: relative;
            color: #666;
            font-size: 0.95em;
        }}

        .rationale-list li:before {{
            content: "•";
            position: absolute;
            left: 10px;
            color: {primary};
            font-weight: bold;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            background: {primary};
            color: white;
            font-weight: bold;
        }}

        tr:hover {{
            background: #f5f5f5;
        }}

        .text-content {{
            color: #555;
            line-height: 1.8;
            margin: 20px 0;
        }}

        .text-content p {{
            margin-bottom: 15px;
        }}

        .report-footer {{
            text-align: center;
            padding: 30px 0;
            margin-top: 50px;
            border-top: 1px solid #ddd;
            color: #999;
            font-size: 0.9em;
        }}

        @media print {{
            .section {{
                page-break-inside: avoid;
            }}

            .chart-container {{
                page-break-inside: avoid;
            }}

            .recommendation {{
                page-break-inside: avoid;
            }}
        }}
    </style>
        '''

    def _render_section(
        self,
        section: Dict[str, Any],
        template_data: Dict[str, Any]
    ) -> str:
        """Render a single section."""
        section_type = section.get('type')
        section_html = []

        # Skip cover page for HTML (used in PDF)
        if section_type == 'cover':
            return ''

        section_html.append('<div class="section">')

        # Section title
        title = section.get('title')
        if title:
            section_html.append(f'<h2 class="section-title">{title}</h2>')

        section_html.append('<div class="section-content">')

        if section_type == 'summary':
            section_html.append(self._render_summary_section(section, template_data))
        elif section_type == 'text':
            section_html.append(self._render_text_section(section, template_data))
        elif section_type == 'charts':
            section_html.append(self._render_charts_section(section, template_data))
        elif section_type == 'recommendations':
            section_html.append(self._render_recommendations_section(section, template_data))
        elif section_type == 'issues':
            section_html.append(self._render_issues_section(section, template_data))
        elif section_type == 'table':
            section_html.append(self._render_table_section(section, template_data))

        section_html.append('</div>')  # section-content
        section_html.append('</div>')  # section

        return '\n'.join(section_html)

    def _render_summary_section(
        self,
        section: Dict[str, Any],
        template_data: Dict[str, Any]
    ) -> str:
        """Render summary section."""
        html = []
        html.append('<div class="summary-box">')
        html.append('<h3>Portfolio Performance</h3>')

        if template_data['analysis_results'] and template_data['analysis_results'].portfolio:
            portfolio = template_data['analysis_results'].portfolio
            html.append(f'<p><strong>Total Buildings:</strong> {portfolio.building_count}</p>')
            html.append(f'<p><strong>Total Rooms:</strong> {portfolio.total_room_count}</p>')
            html.append(f'<p><strong>Average Compliance:</strong> {portfolio.avg_compliance_rate:.1f}%</p>')
            html.append(f'<p><strong>Data Quality:</strong> {portfolio.avg_quality_score:.1f}%</p>')

        html.append('</div>')
        return '\n'.join(html)

    def _render_text_section(
        self,
        section: Dict[str, Any],
        template_data: Dict[str, Any]
    ) -> str:
        """Render text section."""
        content = section.get('content', '')
        return f'<div class="text-content"><p>{content}</p></div>'

    def _render_charts_section(
        self,
        section: Dict[str, Any],
        template_data: Dict[str, Any]
    ) -> str:
        """Render charts section."""
        html = []
        charts = section.get('charts', [])
        chart_paths = template_data.get('chart_paths', {})

        for chart_config in charts:
            chart_id = chart_config['id']
            chart_title = chart_config.get('title', chart_id)

            if chart_id in chart_paths:
                chart_path = chart_paths[chart_id]
                # Make path relative to output
                rel_path = f"charts/{chart_path.name}"

                html.append('<div class="chart-container">')
                html.append(f'<div class="chart-title">{chart_title}</div>')
                html.append(f'<img src="{rel_path}" alt="{chart_title}">')
                html.append('</div>')

        return '\n'.join(html)

    def _render_recommendations_section(
        self,
        section: Dict[str, Any],
        template_data: Dict[str, Any]
    ) -> str:
        """Render recommendations section."""
        html = []
        recommendations = template_data.get('recommendations')

        if not recommendations or not recommendations.top_recommendations:
            html.append('<p>No recommendations available.</p>')
            return '\n'.join(html)

        max_recs = section.get('max_recommendations', 10)
        priority_filter = section.get('priority_filter', ['critical', 'high', 'medium', 'low'])

        recs_to_show = [
            rec for rec in recommendations.top_recommendations[:max_recs]
            if rec.priority in priority_filter
        ]

        for rec in recs_to_show:
            html.append(f'<div class="recommendation {rec.priority}">')
            html.append('<div class="recommendation-header">')
            html.append(f'<div class="recommendation-title">{rec.title}</div>')
            html.append(f'<span class="priority-badge {rec.priority}">{rec.priority}</span>')
            html.append('</div>')
            html.append(f'<div class="recommendation-description">{rec.description}</div>')

            if rec.rationale:
                html.append('<ul class="rationale-list">')
                for rationale_item in rec.rationale[:3]:
                    html.append(f'<li>{rationale_item}</li>')
                html.append('</ul>')

            html.append('<div class="recommendation-details">')
            html.append(f'<div class="recommendation-detail"><strong>Estimated Impact:</strong> {rec.estimated_impact}</div>')
            html.append(f'<div class="recommendation-detail"><strong>Implementation Cost:</strong> {rec.implementation_cost}</div>')
            html.append('</div>')
            html.append('</div>')

        return '\n'.join(html)

    def _render_issues_section(
        self,
        section: Dict[str, Any],
        template_data: Dict[str, Any]
    ) -> str:
        """Render issues section."""
        return '<p>Issues section not yet implemented.</p>'

    def _render_table_section(
        self,
        section: Dict[str, Any],
        template_data: Dict[str, Any]
    ) -> str:
        """Render table section."""
        return '<p>Table section not yet implemented.</p>'
