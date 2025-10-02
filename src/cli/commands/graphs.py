"""Graph commands for HVX CLI."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path

from src.services.graph_service import GraphService

console = Console()
graph_service = GraphService()


@click.group()
def graphs():
    """Graph discovery and preview commands."""
    pass


@graphs.command()
@click.option('--category', '-c', help='Filter by category')
def list(category):
    """List available charts."""
    try:
        charts = graph_service.list_available_charts(category=category)

        if not charts:
            console.print("[yellow]No charts found[/yellow]")
            return

        # Create table
        table = Table(title="Available Charts", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="green")
        table.add_column("Name", style="white")
        table.add_column("Category", style="blue")
        table.add_column("Type", style="magenta")

        for chart in charts:
            table.add_row(
                chart['id'],
                chart['name'],
                chart.get('category', 'other'),
                chart.get('type', 'unknown')
            )

        console.print(table)

        # Show categories
        categories = graph_service.get_categories()
        console.print(f"\n[dim]Available categories: {', '.join(categories)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@graphs.command()
@click.argument('chart_id')
def info(chart_id):
    """Show detailed information about a chart."""
    try:
        chart_info = graph_service.get_chart_info(chart_id)

        if not chart_info:
            console.print(f"[red]Chart '{chart_id}' not found[/red]")
            return

        # Display chart information
        info_text = f"""[bold]{chart_info['name']}[/bold]

[cyan]Description:[/cyan]
{chart_info.get('description', 'No description available')}

[cyan]Details:[/cyan]
• ID: {chart_info['id']}
• Category: {chart_info.get('category', 'other')}
• Type: {chart_info.get('type', 'unknown')}
• Fixture: {chart_info.get('fixture', 'N/A')}
"""

        # Add parameters if available
        if 'parameters' in chart_info and chart_info['parameters']:
            info_text += "\n[cyan]Parameters:[/cyan]\n"
            for param in chart_info['parameters']:
                info_text += f"• {param['name']} ({param['type']}): {param.get('description', 'No description')}\n"
                info_text += f"  Default: {param.get('default', 'None')}\n"

        panel = Panel(info_text, border_style="blue")
        console.print(panel)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@graphs.command()
@click.argument('chart_id')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--config', '-c', type=click.Path(exists=True), help='Chart configuration file')
def preview(chart_id, output, config):
    """Generate a preview of a chart using dummy data."""
    try:
        # Load config if provided
        chart_config = {}
        if config:
            import yaml
            with open(config, 'r') as f:
                chart_config = yaml.safe_load(f)

        # Set output path
        output_path = Path(output) if output else None

        # Generate preview
        console.print(f"[cyan]Generating preview for '{chart_id}' with dummy data...[/cyan]")

        result = graph_service.preview_with_dummy_data(
            chart_id=chart_id,
            config=chart_config,
            output_path=output_path
        )

        console.print(f"[green]✓[/green] Chart preview generated: [bold]{result['output_path']}[/bold]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()
