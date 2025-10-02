"""Template commands for HVX CLI."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
import yaml

from src.services.template_service import TemplateService
from src.services.graph_service import GraphService

console = Console()
template_service = TemplateService()
graph_service = GraphService()


@click.group()
def templates():
    """Template management commands."""
    pass


@templates.command()
@click.option('--builtin/--no-builtin', default=True, help='Include built-in templates')
def list(builtin):
    """List all available templates."""
    try:
        template_list = template_service.list_templates(include_builtin=builtin)

        if not template_list:
            console.print("[yellow]No templates found[/yellow]")
            console.print("[dim]Create a new template with: hvx templates create[/dim]")
            return

        # Create table
        table = Table(title="Available Templates", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="blue")
        table.add_column("Description", style="white")
        table.add_column("Created", style="dim")

        for template in template_list:
            table.add_row(
                template['name'],
                template['type'],
                template.get('description', 'No description'),
                template.get('created', 'Unknown')
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@templates.command()
@click.argument('template_name')
def show(template_name):
    """Show template details."""
    try:
        template = template_service.get_template(template_name)

        if not template:
            console.print(f"[red]Template '{template_name}' not found[/red]")
            return

        # Display template
        template_yaml = yaml.dump(template, default_flow_style=False, sort_keys=False)

        panel = Panel(
            template_yaml,
            title=f"Template: {template_name}",
            border_style="blue"
        )
        console.print(panel)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@templates.command()
def create():
    """Create a new template interactively."""
    try:
        console.print("[bold cyan]Create New Template[/bold cyan]\n")

        # Get basic information
        name = Prompt.ask("Template name")
        title = Prompt.ask("Report title")
        description = Prompt.ask("Description", default="")

        # Select charts
        console.print("\n[cyan]Available charts:[/cyan]")
        charts = graph_service.list_available_charts()

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim")
        table.add_column("ID", style="green")
        table.add_column("Name", style="white")

        for idx, chart in enumerate(charts, 1):
            table.add_row(str(idx), chart['id'], chart['name'])

        console.print(table)

        # Get chart selection (max 3)
        console.print("\n[yellow]Select up to 3 charts (comma-separated numbers):[/yellow]")
        selection = Prompt.ask("Chart numbers")

        selected_indices = [int(i.strip()) - 1 for i in selection.split(',') if i.strip()]
        selected_charts = [charts[i]['id'] for i in selected_indices if 0 <= i < len(charts)][:3]

        if not selected_charts:
            console.print("[red]No valid charts selected[/red]")
            return

        console.print(f"\n[green]Selected charts:[/green] {', '.join(selected_charts)}")

        # Confirm creation
        if not Confirm.ask("\nCreate template?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

        # Create template
        template_path = template_service.create_simple_template(
            name=name,
            title=title,
            description=description,
            chart_ids=selected_charts
        )

        console.print(f"\n[green]✓[/green] Template created: [bold]{template_path}[/bold]")
        console.print(f"[dim]Use with: hvx reports generate {name} --data <analysis_name>[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@templates.command()
@click.argument('template_name')
def delete(template_name):
    """Delete a user template."""
    try:
        if not Confirm.ask(f"Delete template '{template_name}'?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

        if template_service.delete_template(template_name):
            console.print(f"[green]✓[/green] Template '{template_name}' deleted")
        else:
            console.print(f"[red]Template '{template_name}' not found[/red]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
