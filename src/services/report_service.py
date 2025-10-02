"""Report Service for generating PDF reports from JSON data."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.services.graph_service import GraphService
from src.services.template_service import TemplateService


class ReportService:
    """Service for generating PDF reports from JSON analysis data."""

    def __init__(self):
        self.graph_service = GraphService()
        self.template_service = TemplateService()
        self.output_dir = Path("output") / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        template_name: str,
        analysis_data: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate a PDF report using a template and analysis data."""
        # Load template
        template = self.template_service.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # Set default output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"report_{template_name}_{timestamp}.pdf"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate charts
        chart_paths = self._generate_charts(template, analysis_data)

        # Create PDF
        self._create_pdf(template, analysis_data, chart_paths, output_path)

        return {
            'template_name': template_name,
            'output_path': str(output_path),
            'charts_generated': len(chart_paths),
            'status': 'success'
        }

    def _generate_charts(
        self,
        template: Dict[str, Any],
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Path]:
        """Generate all charts required by the template."""
        chart_paths = {}
        charts_dir = Path("output") / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        # Extract chart IDs from template
        sections = template.get('sections', [])

        for section in sections:
            if section.get('type') == 'charts':
                charts = section.get('charts', [])

                for chart_config in charts:
                    chart_id = chart_config['id']

                    # Prepare chart data from analysis
                    chart_data = self._prepare_chart_data(chart_id, analysis_data)

                    # Generate chart
                    output_path = charts_dir / f"{chart_id}.png"

                    result = self.graph_service.render_chart(
                        chart_id=chart_id,
                        data=chart_data,
                        config=chart_config.get('config', {}),
                        output_path=output_path
                    )

                    chart_paths[chart_id] = output_path

        return chart_paths

    def _prepare_chart_data(
        self,
        chart_id: str,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare chart data from analysis JSON."""
        charts_data = analysis_data.get('charts_data', {})

        # Map chart IDs to data keys
        if chart_id == 'co2_compliance_bar':
            if 'co2_compliance' in charts_data:
                return {
                    'chart_type': 'bar',
                    'title': 'CO2 Compliance by Period',
                    'data': {
                        'periods': charts_data['co2_compliance']['periods'],
                        'compliance_percentage': charts_data['co2_compliance']['compliance_percentage'],
                        'threshold': 1000
                    },
                    'styling': {
                        'colors': ['#4CAF50'] * len(charts_data['co2_compliance']['periods']),
                        'xlabel': 'Period',
                        'ylabel': 'Compliance (%)',
                        'threshold_line': 85
                    }
                }

        elif chart_id == 'temperature_timeseries':
            if 'temperature_timeseries' in charts_data:
                return {
                    'chart_type': 'line',
                    'title': 'Temperature Time Series',
                    'data': charts_data['temperature_timeseries'],
                    'styling': {
                        'color': '#2196F3',
                        'xlabel': 'Time',
                        'ylabel': 'Temperature (°C)'
                    }
                }

        # Fallback: use dummy data
        return self.graph_service._load_dummy_data(chart_id)

    def _create_pdf(
        self,
        template: Dict[str, Any],
        analysis_data: Dict[str, Any],
        chart_paths: Dict[str, Path],
        output_path: Path
    ):
        """Create PDF document."""
        # Create document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            topMargin=2*cm,
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm
        )

        # Build story
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        )

        # Title page
        report_config = template.get('report', {})
        title = report_config.get('title', 'IEQ Analytics Report')
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 1*cm))

        # Metadata table
        metadata = analysis_data.get('metadata', {})
        meta_data = [
            ['Building:', metadata.get('building_name', 'N/A')],
            ['Analysis Date:', metadata.get('timestamp', 'N/A')[:10]],
            ['Data Points:', str(metadata.get('data_points', 'N/A'))],
            ['Author:', report_config.get('author', 'HVX Analytics')]
        ]

        meta_table = Table(meta_data, colWidths=[5*cm, 10*cm])
        meta_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(meta_table)
        story.append(PageBreak())

        # Process sections
        sections = template.get('sections', [])

        for section in sections:
            section_title = section.get('title', 'Section')
            story.append(Paragraph(section_title, heading_style))
            story.append(Spacer(1, 0.5*cm))

            section_type = section.get('type')

            if section_type == 'summary':
                # Add summary content
                summary = analysis_data.get('summary', {})
                summary_items = []

                summary_items.append(
                    Paragraph(
                        f"<b>Overall Compliance:</b> {summary.get('overall_compliance', 'N/A')}%",
                        styles['Normal']
                    )
                )
                summary_items.append(Spacer(1, 0.3*cm))

                summary_items.append(
                    Paragraph(
                        f"<b>Rules Evaluated:</b> {summary.get('total_rules_evaluated', 'N/A')}",
                        styles['Normal']
                    )
                )
                summary_items.append(Spacer(1, 0.3*cm))

                summary_items.append(
                    Paragraph(
                        f"<b>Data Quality:</b> {summary.get('data_quality_score', 'N/A')}%",
                        styles['Normal']
                    )
                )
                summary_items.append(Spacer(1, 0.5*cm))

                # Key findings
                if summary.get('key_findings'):
                    summary_items.append(Paragraph("<b>Key Findings:</b>", styles['Normal']))
                    summary_items.append(Spacer(1, 0.2*cm))

                    for finding in summary['key_findings']:
                        summary_items.append(
                            Paragraph(f"• {finding}", styles['Normal'])
                        )
                        summary_items.append(Spacer(1, 0.2*cm))

                story.extend(summary_items)

            elif section_type == 'charts':
                # Add charts
                charts = section.get('charts', [])

                for chart_config in charts:
                    chart_id = chart_config['id']

                    if chart_id in chart_paths:
                        chart_path = chart_paths[chart_id]

                        if chart_path.exists():
                            # Add chart image
                            img = Image(str(chart_path), width=15*cm, height=9*cm)
                            story.append(KeepTogether([img]))
                            story.append(Spacer(1, 1*cm))

            story.append(Spacer(1, 1*cm))

        # Build PDF
        doc.build(story)

    def list_reports(self) -> List[Dict[str, Any]]:
        """List all generated reports."""
        reports = []

        if self.output_dir.exists():
            for pdf_file in self.output_dir.glob("*.pdf"):
                reports.append({
                    'name': pdf_file.stem,
                    'path': str(pdf_file),
                    'size': pdf_file.stat().st_size,
                    'created': datetime.fromtimestamp(pdf_file.stat().st_ctime).isoformat()
                })

        return sorted(reports, key=lambda x: x['created'], reverse=True)
