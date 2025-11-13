"""Use case for generating analysis reports."""

from datetime import datetime
from pathlib import Path

from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.models.room import Room
from core.reporting.report_generator import ReportGenerator


class GenerateReportUseCase:
    """Use case for generating IEQ analysis reports."""

    def __init__(self):
        """Initialize use case."""
        self.report_generator = ReportGenerator()

    def execute(
        self,
        rooms: list[Room],
        building_name: str,
        output_path: Path | None = None,
        template_path: Path | None = None,
        building_analysis: BuildingAnalysis | None = None,
    ) -> Path:
        """
        Generate analysis report.

        Args:
            rooms: List of room entities with data
            building_name: Name of the building
            output_path: Optional custom output path
            template_path: Optional path to report template
            building_analysis: Optional building analysis for summary

        Returns:
            Path to generated report

        Raises:
            ValueError: If no rooms provided
        """
        if not rooms:
            raise ValueError("No rooms provided for report generation")

        # Set default output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output/reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{building_name}_{timestamp}.html"

        # Generate report using template or fallback
        if template_path and template_path.exists():
            self.report_generator.generate_from_template(
                template_path=template_path,
                rooms=rooms,
                building_name=building_name,
                output_path=output_path,
            )
        else:
            # Fallback to basic report generation
            self._generate_basic_report(
                rooms=rooms,
                building_name=building_name,
                output_path=output_path,
                building_analysis=building_analysis,
            )

        return output_path

    def _generate_basic_report(
        self,
        rooms: list[Room],
        building_name: str,
        output_path: Path,
        building_analysis: BuildingAnalysis | None = None,
    ) -> None:
        """Generate a basic HTML report."""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>IEQ Analysis Report - {building_name}</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .summary-item {{
            display: inline-block;
            margin: 10px 20px 10px 0;
        }}
        .summary-label {{ font-weight: bold; color: #7f8c8d; }}
        .summary-value {{ font-size: 24px; color: #2c3e50; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #e8f4f8; }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌡️ IEQ Analysis Report</h1>
        <h2>{building_name}</h2>

        <div class="summary">
            <div class="summary-item">
                <div class="summary-label">Total Rooms</div>
                <div class="summary-value">{len(rooms)}</div>
            </div>
"""

        if building_analysis:
            html_content += f"""
            <div class="summary-item">
                <div class="summary-label">Overall Compliance</div>
                <div class="summary-value">{building_analysis.avg_compliance_rate:.1f}%</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Data Quality</div>
                <div class="summary-value">{building_analysis.avg_quality_score:.1f}%</div>
            </div>
"""

        html_content += """
        </div>

        <h2>Room Overview</h2>
        <table>
            <tr>
                <th>Room Name</th>
                <th>Level</th>
                <th>Parameters</th>
                <th>Data Points</th>
            </tr>
"""

        for room in rooms:
            params = ", ".join([p.value for p in room.available_parameters])
            html_content += f"""
            <tr>
                <td>{room.name}</td>
                <td>{room.level_id or 'N/A'}</td>
                <td>{params}</td>
                <td>{len(room.data) if hasattr(room, 'data') else 'N/A'}</td>
            </tr>
"""

        html_content += f"""
        </table>

        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>IEQ Analytics v2.0 - Clean Architecture</p>
        </div>
    </div>
</body>
</html>
"""

        output_path.write_text(html_content)
