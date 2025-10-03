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
        from src.core.services.graph_service import GraphService

        service = GraphService()
        graph_configs = service.list_graph_configs()

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
        from src.core.services.graph_service import GraphService

        service = GraphService()
        config = service.get_graph_config(config_name)

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
        from src.core.services.report_template_service import ReportTemplateService

        service = ReportTemplateService()
        template_list = service.list_templates()

        if not template_list:
            console.print("[yellow]No templates found[/yellow]")
            console.print("[dim]Create a template with: hvx settings templates create[/dim]")
            return

        console.print("\n[bold cyan]Available Report Templates:[/bold cyan]\n")
        for template in template_list:
            console.print(f"  • [green]{template.name}[/green]")
            if template.description:
                console.print(f"    [dim]{template.description}[/dim]")
            console.print(f"    [dim]Sections: {len(template.sections)}[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@templates.command(name='show')
@click.argument('template_name')
def show_template(template_name: str):
    """Show details of a report template."""
    try:
        from src.core.services.report_template_service import ReportTemplateService

        service = ReportTemplateService()
        template = service.load_template(template_name)

        if not template:
            console.print(f"[red]Template '{template_name}' not found[/red]")
            raise click.Abort()

        console.print(f"\n[bold cyan]Template: {template.name}[/bold cyan]\n")
        console.print(f"[bold]Description:[/bold] {template.description}")
        console.print(f"[bold]Scope:[/bold] {template.scope}")
        console.print(f"\n[bold]Sections ({len(template.sections)}):[/bold]")

        for i, section in enumerate(template.sections, 1):
            console.print(f"  {i}. [green]{section.title}[/green]")
            console.print(f"     Type: {section.section_type}")
            if section.content_config:
                console.print(f"     Config keys: {', '.join(section.content_config.keys())}")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@templates.command(name='create')
@click.argument('template_name')
@click.option('--scope', type=click.Choice(['building', 'level', 'room', 'portfolio']),
              default='building', help='Template scope')
@click.option('--description', help='Template description')
def create_template(template_name: str, scope: str, description: str):
    """Create a new report template interactively."""
    try:
        from src.core.services.report_template_service import ReportTemplateService

        console.print(f"\n[bold cyan]Creating template: {template_name}[/bold cyan]\n")

        service = ReportTemplateService()

        # Check if template already exists
        if service.load_template(template_name):
            console.print(f"[red]Template '{template_name}' already exists[/red]")
            raise click.Abort()

        # Create basic template structure
        from src.core.models.report_template import ReportTemplate, TemplateSection

        template = ReportTemplate(
            name=template_name,
            scope=scope,
            description=description or f"{template_name} report template",
            sections=[]
        )

        # Add default sections based on scope
        if scope == 'building':
            template.sections = [
                TemplateSection(
                    title="Executive Summary",
                    section_type="summary",
                    content_config={"include_metrics": True}
                ),
                TemplateSection(
                    title="Compliance Overview",
                    section_type="compliance",
                    content_config={}
                ),
                TemplateSection(
                    title="Recommendations",
                    section_type="recommendations",
                    content_config={}
                )
            ]
        elif scope == 'portfolio':
            template.sections = [
                TemplateSection(
                    title="Portfolio Overview",
                    section_type="summary",
                    content_config={"include_metrics": True}
                ),
                TemplateSection(
                    title="Building Rankings",
                    section_type="rankings",
                    content_config={}
                ),
                TemplateSection(
                    title="Investment Priorities",
                    section_type="priorities",
                    content_config={}
                )
            ]

        # Save template
        service.save_template(template)

        console.print(f"[green]✓[/green] Template created: [cyan]{template_name}[/cyan]")
        console.print(f"  Scope: {scope}")
        console.print(f"  Sections: {len(template.sections)}")
        console.print(f"\nView with: [dim]hvx settings templates show {template_name}[/dim]\n")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@templates.command(name='delete')
@click.argument('template_name')
@click.confirmation_option(prompt='Are you sure you want to delete this template?')
def delete_template(template_name: str):
    """Delete a report template."""
    try:
        from src.core.services.report_template_service import ReportTemplateService

        service = ReportTemplateService()

        if not service.load_template(template_name):
            console.print(f"[red]Template '{template_name}' not found[/red]")
            raise click.Abort()

        service.delete_template(template_name)
        console.print(f"[green]✓[/green] Template deleted: {template_name}\n")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()
