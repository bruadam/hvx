"""Analytics commands for HVX CLI."""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from src.services.analytics_service import AnalyticsService

console = Console()
analytics_service = AnalyticsService()


@click.group()
def analytics():
    """Analytics execution commands."""
    pass


@analytics.command()
@click.argument('data_path', type=click.Path(exists=True))
@click.option('--name', '-n', help='Name for this analysis')
@click.option('--config', '-c', type=click.Path(exists=True), help='Analytics configuration file')
def run(data_path, name, config):
    """Run analytics on a dataset.

    DATA_PATH: Path to CSV or parquet file containing sensor data.
    """
    try:
        data_path = Path(data_path)

        # Use config if provided
        if config:
            config_path = Path(config)
            service = AnalyticsService(config_path=config_path)
        else:
            service = analytics_service

        console.print(f"[cyan]Running analytics on:[/cyan] {data_path}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing...", total=None)

            result = service.run_analysis(
                data_path=data_path,
                analysis_name=name
            )

            progress.update(task, completed=True)

        console.print(f"\n[green]✓[/green] Analysis complete")
        console.print(f"[bold]Analysis name:[/bold] {result['analysis_name']}")
        console.print(f"[bold]Output:[/bold] {result['output_path']}")

        # Show summary
        summary = result['results'].get('summary', {})
        if summary:
            console.print("\n[cyan]Summary:[/cyan]")
            console.print(f"• Overall Compliance: {summary.get('overall_compliance', 'N/A')}%")
            console.print(f"• Rules Evaluated: {summary.get('total_rules_evaluated', 'N/A')}")
            console.print(f"• Data Quality: {summary.get('data_quality_score', 'N/A')}%")

        console.print(f"\n[dim]Generate report with: hvx reports generate <template> --data {result['analysis_name']}[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@analytics.command()
def list():
    """List all saved analysis results."""
    try:
        analyses = analytics_service.list_analyses()

        if not analyses:
            console.print("[yellow]No analysis results found[/yellow]")
            console.print("[dim]Run analysis with: hvx analytics run <data_path>[/dim]")
            return

        # Create table
        table = Table(title="Analysis Results", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green")
        table.add_column("Building", style="white")
        table.add_column("Timestamp", style="dim")

        for analysis in analyses:
            table.add_row(
                analysis['name'],
                analysis.get('building', 'Unknown'),
                analysis.get('timestamp', 'Unknown')[:19]  # Trim to datetime
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@analytics.command()
@click.argument('analysis_name')
def show(analysis_name):
    """Show analysis results summary."""
    try:
        analysis = analytics_service.get_analysis(analysis_name)

        if not analysis:
            console.print(f"[red]Analysis '{analysis_name}' not found[/red]")
            return

        # Display summary
        console.print(f"[bold cyan]Analysis: {analysis_name}[/bold cyan]\n")

        metadata = analysis.get('metadata', {})
        console.print(f"[cyan]Metadata:[/cyan]")
        console.print(f"• Building: {metadata.get('building_name', 'N/A')}")
        console.print(f"• Timestamp: {metadata.get('timestamp', 'N/A')}")
        console.print(f"• Data Points: {metadata.get('data_points', 'N/A')}")

        date_range = metadata.get('date_range', {})
        if date_range:
            console.print(f"• Date Range: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}")

        summary = analysis.get('summary', {})
        if summary:
            console.print(f"\n[cyan]Summary:[/cyan]")
            console.print(f"• Overall Compliance: {summary.get('overall_compliance', 'N/A')}%")
            console.print(f"• Rules Evaluated: {summary.get('total_rules_evaluated', 'N/A')}")
            console.print(f"• Data Quality: {summary.get('data_quality_score', 'N/A')}%")

            key_findings = summary.get('key_findings', [])
            if key_findings:
                console.print(f"\n[cyan]Key Findings:[/cyan]")
                for finding in key_findings:
                    console.print(f"• {finding}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
