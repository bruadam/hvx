"""Report commands for HVX CLI."""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from src.services.report_service import ReportService
from src.services.analytics_service import AnalyticsService

console = Console()
report_service = ReportService()
analytics_service = AnalyticsService()


@click.group()
def reports():
    """Report generation commands."""
    pass


@reports.command()
@click.argument('template_name')
@click.option('--data', '-d', required=True, help='Analysis name or path to JSON file')
@click.option('--output', '-o', type=click.Path(), help='Output PDF file path')
def generate(template_name, data, output):
    """Generate a PDF report from analysis data.

    TEMPLATE_NAME: Name of the template to use.
    """
    try:
        # Load analysis data
        console.print(f"[cyan]Loading analysis data:[/cyan] {data}")

        # Check if data is a file path or analysis name
        data_path = Path(data)
        if data_path.exists() and data_path.suffix == '.json':
            import json
            with open(data_path, 'r') as f:
                analysis_data = json.load(f)
        else:
            # Assume it's an analysis name
            analysis_data = analytics_service.get_analysis(data)
            if not analysis_data:
                console.print(f"[red]Analysis '{data}' not found[/red]")
                console.print("[dim]Run: hvx analytics list[/dim]")
                raise click.Abort()

        # Set output path
        output_path = Path(output) if output else None

        console.print(f"[cyan]Generating report with template:[/cyan] {template_name}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating report...", total=None)

            result = report_service.generate_report(
                template_name=template_name,
                analysis_data=analysis_data,
                output_path=output_path
            )

            progress.update(task, completed=True)

        console.print(f"\n[green]✓[/green] Report generated")
        console.print(f"[bold]Template:[/bold] {result['template_name']}")
        console.print(f"[bold]Output:[/bold] {result['output_path']}")
        console.print(f"[bold]Charts:[/bold] {result['charts_generated']}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@reports.command()
def list():
    """List all generated reports."""
    try:
        report_list = report_service.list_reports()

        if not report_list:
            console.print("[yellow]No reports found[/yellow]")
            console.print("[dim]Generate report with: hvx reports generate <template> --data <analysis>[/dim]")
            return

        # Create table
        table = Table(title="Generated Reports", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green")
        table.add_column("Size", style="white")
        table.add_column("Created", style="dim")

        for report in report_list:
            size_mb = report['size'] / (1024 * 1024)
            table.add_row(
                report['name'],
                f"{size_mb:.2f} MB",
                report.get('created', 'Unknown')[:19]
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
