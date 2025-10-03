"""Settings commands for HVX CLI."""

import click
from rich.console import Console
from pathlib import Path

console = Console()


@click.group(name='settings')
def settings():
    """Manage hvx settings and configurations."""
    pass


# ==========================================
# Graph Settings
# ==========================================
@settings.group(name='graphs')
def graphs():
    """Configure graph settings."""
    pass


@graphs.command(name='list')
def list_graphs():
    """List available graph configurations."""
    try:
        from src.core.graphs.GraphService import GraphService

        service = GraphService()
        graph_configs = service.list_available_charts()

        if not graph_configs:
            console.print("[yellow]No graph configurations found[/yellow]")
            return

        console.print("\n[bold cyan]Available Graph Configurations:[/bold cyan]\n")
        for config in graph_configs:
            console.print(f"  • [green]{config['name']}[/green]")
            if config.get('description'):
                console.print(f"    [dim]{config['description']}[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@graphs.command(name='show')
@click.argument('config_name')
def show_graph(config_name: str):
    """Show details of a graph configuration."""
    try:
        from src.core.graphs.GraphService import GraphService

        service = GraphService()
        config = service.get_chart_info(config_name)

        if not config:
            console.print(f"[red]Graph configuration '{config_name}' not found[/red]")
            raise click.Abort()

        console.print(f"\n[bold cyan]Graph Configuration: {config_name}[/bold cyan]\n")
        console.print(f"[bold]Description:[/bold] {config.get('description', 'N/A')}")
        console.print(f"[bold]Type:[/bold] {config.get('type', 'N/A')}")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


# ==========================================
# Templates Settings
# ==========================================
@settings.group(name='templates')
def templates():
    """Manage report templates."""
    pass


@templates.command(name='list')
def list_templates():
    """List available report templates."""
    try:
        from src.core.reporting.report_template_service import ReportTemplateService

        service = ReportTemplateService()
        template_list = service.list_templates()

        if not template_list:
            console.print("[yellow]No templates found[/yellow]")
            console.print("[dim]Create a template with: hvx settings templates create[/dim]")
            return

        console.print("\n[bold cyan]Available Report Templates:[/bold cyan]\n")
        for template in template_list:
            console.print(f"  • [green]{template.name}[/green] ({template.template_id})")
            if template.description:
                console.print(f"    [dim]{template.description}[/dim]")
            console.print(f"    [dim]Level: {template.default_level.value} | Sections: {len(template.sections)}[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@templates.command(name='show')
@click.argument('template_id')
def show_template(template_id: str):
    """Show details of a report template."""
    try:
        from src.core.reporting.report_template_service import ReportTemplateService

        service = ReportTemplateService()
        template = service.load_template(template_id)

        if not template:
            console.print(f"[red]Template '{template_id}' not found[/red]")
            raise click.Abort()

        console.print(f"\n[bold cyan]Template: {template.name}[/bold cyan] ({template.template_id})\n")
        console.print(f"[bold]Description:[/bold] {template.description}")
        console.print(f"[bold]Default Level:[/bold] {template.default_level.value}")
        console.print(f"[bold]Output Format:[/bold] {template.output_format}")
        console.print(f"[bold]Page Size:[/bold] {template.page_size} ({template.orientation})")

        if template.author:
            console.print(f"[bold]Author:[/bold] {template.author}")
        if template.created_date:
            console.print(f"[bold]Created:[/bold] {template.created_date}")

        console.print(f"\n[bold]Sections ({len(template.sections)}):[/bold]")

        for i, section in enumerate(template.sections, 1):
            console.print(f"  {i}. [green]{section.section_id}[/green]")
            console.print(f"     Type: {section.section_type.value}")
            console.print(f"     Enabled: {section.enabled}")

            # Show specific section details
            if section.summary:
                console.print(f"     Level: {section.summary.level.value}")
            elif section.graph:
                console.print(f"     Graph: {section.graph.graph_type}")
            elif section.table:
                console.print(f"     Table: {section.table.table_type}")
            elif section.text:
                console.print(f"     Heading: {section.text.heading or 'N/A'}")
            elif section.loop:
                console.print(f"     Loop over: {section.loop.loop_over.value} ({len(section.loop.sections)} subsections)")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@templates.command(name='create')
@click.argument('template_id')
@click.option('--name', help='Template display name')
@click.option('--level', type=click.Choice(['building', 'level', 'room', 'portfolio']),
              default='building', help='Default analysis level')
@click.option('--description', help='Template description')
@click.option('--standard', is_flag=True, help='Create standard building template')
def create_template(template_id: str, name: str, level: str, description: str, standard: bool):
    """Create a new report template."""
    try:
        from src.core.reporting.report_template_service import ReportTemplateService
        from src.core.models import AnalysisLevel
        from datetime import datetime

        service = ReportTemplateService()

        # Check if template already exists
        if service.load_template(template_id):
            console.print(f"[red]Template '{template_id}' already exists[/red]")
            raise click.Abort()

        console.print(f"\n[bold cyan]Creating template: {template_id}[/bold cyan]\n")

        # Create standard template or basic template
        if standard:
            template = service.create_standard_building_template()
            template.template_id = template_id
            template.name = name or template_id.replace('_', ' ').title()
            if description:
                template.description = description
        else:
            template = service.create_basic_template(
                template_id=template_id,
                name=name or template_id.replace('_', ' ').title(),
                description=description or f"{template_id} report template"
            )
            template.default_level = AnalysisLevel(level)

        # Save template
        service.save_template(template)

        console.print(f"[green]✓[/green] Template created: [cyan]{template.name}[/cyan]")
        console.print(f"  ID: {template.template_id}")
        console.print(f"  Level: {template.default_level.value}")
        console.print(f"  Sections: {len(template.sections)}")
        console.print(f"\nView with: [dim]hvx settings templates show {template_id}[/dim]\n")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@templates.command(name='delete')
@click.argument('template_id')
@click.confirmation_option(prompt='Are you sure you want to delete this template?')
def delete_template(template_id: str):
    """Delete a report template."""
    try:
        from src.core.reporting.report_template_service import ReportTemplateService

        service = ReportTemplateService()

        if not service.load_template(template_id):
            console.print(f"[red]Template '{template_id}' not found[/red]")
            raise click.Abort()

        service.delete_template(template_id)
        console.print(f"[green]✓[/green] Template deleted: {template_id}\n")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()
