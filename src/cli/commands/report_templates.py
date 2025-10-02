"""
CLI commands for managing report templates.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import box
from typing import Optional, List
from datetime import datetime

from src.services.report_template_service import ReportTemplateService
from src.models.report_template_models import (
    ReportTemplate, ReportSection, SectionType, AnalysisLevel, SortOrder,
    MetadataSection, TextSection, GraphSection, TableSection,
    SummarySection, RecommendationsSection, IssuesSection, LoopSection
)

console = Console()


@click.group(name='report-templates')
def report_templates():
    """Manage report templates for generating custom reports."""
    pass


# =====================
# Template Management
# =====================

@report_templates.command(name='list')
@click.option('--templates-dir', type=click.Path(path_type=Path),
              default='config/report_templates', help='Templates directory')
def list_templates(templates_dir: Path):
    """List all available report templates."""
    service = ReportTemplateService(templates_dir)
    templates = service.list_templates()

    console.print(f"\n[bold cyan]Report Templates[/bold cyan] ({len(templates)} total)\n")

    if not templates:
        console.print("[yellow]No templates found. Create one with 'hvx report-templates create'.[/yellow]")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Sections", justify="right", style="yellow")
    table.add_column("Format", style="green")
    table.add_column("Level", style="magenta")

    for template in templates:
        table.add_row(
            template.template_id,
            template.name,
            str(len(template.sections)),
            template.output_format,
            template.default_level.value
        )

    console.print(table)


@report_templates.command(name='show')
@click.argument('template_id')
@click.option('--templates-dir', type=click.Path(path_type=Path),
              default='config/report_templates', help='Templates directory')
def show_template(template_id: str, templates_dir: Path):
    """Show detailed information about a template."""
    service = ReportTemplateService(templates_dir)
    template = service.load_template(template_id)

    if not template:
        console.print(f"[red]✗ Template '{template_id}' not found.[/red]")
        raise click.Abort()

    console.print(Panel.fit(
        f"[bold blue]{template.name}[/bold blue]\n"
        f"{template.description}\n\n"
        f"ID: {template.template_id}\n"
        f"Format: {template.output_format}\n"
        f"Level: {template.default_level.value}\n"
        f"Sections: {len(template.sections)}",
        border_style="blue"
    ))

    # Show sections
    console.print("\n[bold cyan]Sections:[/bold cyan]\n")

    table = Table(box=box.SIMPLE)
    table.add_column("#", style="dim", width=4)
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Details", style="white")
    table.add_column("Enabled", justify="center")

    for i, section in enumerate(template.sections, 1):
        details = _get_section_details(section)
        enabled = "✓" if section.enabled else "✗"

        table.add_row(
            str(i),
            section.section_id,
            section.section_type.value,
            details,
            enabled
        )

    console.print(table)


@report_templates.command(name='create')
@click.option('--templates-dir', type=click.Path(path_type=Path),
              default='config/report_templates', help='Templates directory')
@click.option('--from-template', help='Create from existing template')
@click.option('--interactive/--no-interactive', default=True,
              help='Use interactive mode to build template')
def create_template(templates_dir: Path, from_template: Optional[str], interactive: bool):
    """Create a new report template."""
    service = ReportTemplateService(templates_dir)

    console.print(Panel.fit(
        "[bold blue]Create Report Template[/bold blue]\n"
        "Build a custom report template with sections for your analysis.",
        border_style="blue"
    ))

    # Basic template info
    template_id = Prompt.ask("\n[cyan]Template ID[/cyan] (e.g., summer_analysis)")
    if service.load_template(template_id):
        if not Confirm.ask(f"[yellow]Template '{template_id}' exists. Overwrite?[/yellow]"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    # Start from existing template or scratch
    if from_template:
        source = service.load_template(from_template)
        if not source:
            console.print(f"[red]✗ Source template '{from_template}' not found.[/red]")
            raise click.Abort()

        console.print(f"\n[green]Using '{from_template}' as template base[/green]")
        template = service.copy_template(from_template, template_id)
        template.name = Prompt.ask("[cyan]Template name[/cyan]", default=template.name)
        template.description = Prompt.ask("[cyan]Description[/cyan]", default=template.description)
    else:
        name = Prompt.ask("[cyan]Template name[/cyan]")
        description = Prompt.ask("[cyan]Description[/cyan]")

        template = ReportTemplate(
            template_id=template_id,
            name=name,
            description=description,
            created_date=datetime.now().isoformat()
        )

    # Configure template settings
    _configure_template_settings(template)

    # Interactive section builder
    if interactive:
        console.print("\n[bold cyan]Building Template Sections[/bold cyan]")
        _interactive_section_builder(template, service)

    # Validate
    issues = service.validate_template(template)
    if issues:
        console.print("\n[yellow]⚠ Template validation warnings:[/yellow]")
        for issue in issues:
            console.print(f"  • {issue}")

        if not Confirm.ask("\n[cyan]Save template anyway?[/cyan]", default=True):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    # Save
    file_path = service.save_template(template)
    console.print(f"\n[green]✓ Template '{template_id}' created successfully![/green]")
    console.print(f"  Saved to: [cyan]{file_path}[/cyan]")


@report_templates.command(name='edit')
@click.argument('template_id')
@click.option('--templates-dir', type=click.Path(path_type=Path),
              default='config/report_templates', help='Templates directory')
@click.option('--save-as', help='Save edited template with new ID')
def edit_template(template_id: str, templates_dir: Path, save_as: Optional[str]):
    """Edit an existing template."""
    service = ReportTemplateService(templates_dir)
    template = service.load_template(template_id)

    if not template:
        console.print(f"[red]✗ Template '{template_id}' not found.[/red]")
        raise click.Abort()

    console.print(Panel.fit(
        f"[bold blue]Edit Template: {template_id}[/bold blue]",
        border_style="blue"
    ))

    # Edit basic info
    template.name = Prompt.ask("[cyan]Template name[/cyan]", default=template.name)
    template.description = Prompt.ask("[cyan]Description[/cyan]", default=template.description)

    # Edit settings
    _configure_template_settings(template)

    # Section management menu
    while True:
        console.print("\n[bold cyan]Section Management:[/bold cyan]")
        console.print("  1. Add section")
        console.print("  2. Remove section")
        console.print("  3. Edit section")
        console.print("  4. Reorder sections")
        console.print("  5. View sections")
        console.print("  6. Done")

        choice = IntPrompt.ask("Select option", default=6)

        if choice == 1:
            _add_section_interactive(template, service)
        elif choice == 2:
            _remove_section_interactive(template)
        elif choice == 3:
            _edit_section_interactive(template, service)
        elif choice == 4:
            _reorder_sections_interactive(template)
        elif choice == 5:
            _display_sections(template)
        elif choice == 6:
            break

    # Save
    new_id = save_as or template_id
    if new_id != template_id:
        template.template_id = new_id

    file_path = service.save_template(template)
    console.print(f"\n[green]✓ Template saved to: [cyan]{file_path}[/cyan][/green]")


@report_templates.command(name='delete')
@click.argument('template_id')
@click.option('--templates-dir', type=click.Path(path_type=Path),
              default='config/report_templates', help='Templates directory')
@click.option('--yes', is_flag=True, help='Skip confirmation')
def delete_template(template_id: str, templates_dir: Path, yes: bool):
    """Delete a template."""
    service = ReportTemplateService(templates_dir)

    if not service.load_template(template_id):
        console.print(f"[red]✗ Template '{template_id}' not found.[/red]")
        raise click.Abort()

    if not yes:
        if not Confirm.ask(f"[yellow]Delete template '{template_id}'?[/yellow]"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    if service.delete_template(template_id):
        console.print(f"[green]✓ Template '{template_id}' deleted.[/green]")
    else:
        console.print(f"[red]✗ Failed to delete template.[/red]")


@report_templates.command(name='copy')
@click.argument('source_id')
@click.argument('new_id')
@click.option('--templates-dir', type=click.Path(path_type=Path),
              default='config/report_templates', help='Templates directory')
@click.option('--name', help='Name for new template')
def copy_template_cmd(source_id: str, new_id: str, templates_dir: Path, name: Optional[str]):
    """Copy an existing template."""
    service = ReportTemplateService(templates_dir)

    template = service.copy_template(source_id, new_id, name)

    if template:
        service.save_template(template)
        console.print(f"[green]✓ Template copied to '{new_id}'[/green]")
    else:
        console.print(f"[red]✗ Source template '{source_id}' not found.[/red]")


@report_templates.command(name='validate')
@click.argument('template_id')
@click.option('--templates-dir', type=click.Path(path_type=Path),
              default='config/report_templates', help='Templates directory')
def validate_template_cmd(template_id: str, templates_dir: Path):
    """Validate a template configuration."""
    service = ReportTemplateService(templates_dir)
    template = service.load_template(template_id)

    if not template:
        console.print(f"[red]✗ Template '{template_id}' not found.[/red]")
        raise click.Abort()

    issues = service.validate_template(template)

    if not issues:
        console.print(f"[green]✓ Template '{template_id}' is valid![/green]")
    else:
        console.print(f"[yellow]⚠ Template has {len(issues)} validation issues:[/yellow]\n")
        for i, issue in enumerate(issues, 1):
            console.print(f"  {i}. {issue}")


# =====================
# Quick Create Commands
# =====================

@report_templates.command(name='quick-standard')
@click.option('--templates-dir', type=click.Path(path_type=Path),
              default='config/report_templates', help='Templates directory')
def quick_standard(templates_dir: Path):
    """Quickly create a standard building analysis template."""
    service = ReportTemplateService(templates_dir)
    template = service.create_standard_building_template()

    file_path = service.save_template(template)
    console.print(f"[green]✓ Standard building template created![/green]")
    console.print(f"  Template ID: [cyan]{template.template_id}[/cyan]")
    console.print(f"  Saved to: [cyan]{file_path}[/cyan]")


@report_templates.command(name='quick-room-detail')
@click.option('--templates-dir', type=click.Path(path_type=Path),
              default='config/report_templates', help='Templates directory')
def quick_room_detail(templates_dir: Path):
    """Quickly create a detailed room analysis template with loops."""
    service = ReportTemplateService(templates_dir)
    template = service.create_room_loop_template()

    file_path = service.save_template(template)
    console.print(f"[green]✓ Detailed room analysis template created![/green]")
    console.print(f"  Template ID: [cyan]{template.template_id}[/cyan]")
    console.print(f"  Saved to: [cyan]{file_path}[/cyan]")


# =====================
# Helper Functions
# =====================

def _configure_template_settings(template: ReportTemplate):
    """Interactively configure template settings."""
    console.print("\n[bold cyan]Template Settings:[/bold cyan]")

    # Output format
    formats = ["pdf", "html", "markdown", "docx"]
    console.print("\nOutput format:")
    for i, fmt in enumerate(formats, 1):
        marker = " ←" if fmt == template.output_format else ""
        console.print(f"  {i}. {fmt}{marker}")
    fmt_idx = IntPrompt.ask("Select format",
                            default=formats.index(template.output_format) + 1) - 1
    template.output_format = formats[fmt_idx]

    # Page settings
    if template.output_format == "pdf":
        # Page size
        sizes = ["A4", "Letter", "A3"]
        console.print("\nPage size:")
        for i, size in enumerate(sizes, 1):
            marker = " ←" if size == template.page_size else ""
            console.print(f"  {i}. {size}{marker}")
        size_idx = IntPrompt.ask("Select size",
                                default=sizes.index(template.page_size) + 1) - 1
        template.page_size = sizes[size_idx]

        # Orientation
        orientations = ["portrait", "landscape"]
        console.print("\nOrientation:")
        for i, orient in enumerate(orientations, 1):
            marker = " ←" if orient == template.orientation else ""
            console.print(f"  {i}. {orient}{marker}")
        orient_idx = IntPrompt.ask("Select orientation",
                                   default=orientations.index(template.orientation) + 1) - 1
        template.orientation = orientations[orient_idx]

    # Default analysis level
    levels = [level.value for level in AnalysisLevel]
    console.print("\nDefault analysis level:")
    for i, level in enumerate(levels, 1):
        marker = " ←" if level == template.default_level.value else ""
        console.print(f"  {i}. {level}{marker}")
    level_idx = IntPrompt.ask("Select level",
                             default=levels.index(template.default_level.value) + 1) - 1
    template.default_level = AnalysisLevel(levels[level_idx])


def _interactive_section_builder(template: ReportTemplate, service: ReportTemplateService):
    """Interactive section builder."""
    console.print("\n[dim]Add sections to your template. Press Ctrl+C when done.[/dim]")

    # Always add metadata first if not present
    if not any(s.section_type == SectionType.METADATA for s in template.sections):
        if Confirm.ask("\n[cyan]Add metadata section (title, author, date)?[/cyan]", default=True):
            section = _create_metadata_section()
            template.add_section(section)
            console.print("[green]✓ Metadata section added[/green]")

    try:
        while True:
            console.print(f"\n[bold]Current sections: {len(template.sections)}[/bold]")

            if not Confirm.ask("\n[cyan]Add another section?[/cyan]", default=True):
                break

            _add_section_interactive(template, service)

    except KeyboardInterrupt:
        console.print("\n[dim]Finished building template[/dim]")


def _add_section_interactive(template: ReportTemplate, service: ReportTemplateService):
    """Add a section interactively."""
    console.print("\n[bold cyan]Select section type:[/bold cyan]")
    section_types = [
        ("metadata", "Metadata (title, author, date, etc.)"),
        ("text", "Text/Markdown content"),
        ("summary", "Summary statistics"),
        ("table", "Data table"),
        ("graph", "Chart/visualization"),
        ("issues", "Issues list"),
        ("recommendations", "Recommendations list"),
        ("loop", "Loop over buildings/rooms")
    ]

    for i, (typ, desc) in enumerate(section_types, 1):
        console.print(f"  {i}. {typ:20s} - {desc}")

    choice = IntPrompt.ask("Select type", default=1)
    section_type = section_types[choice - 1][0]

    section_id = Prompt.ask("[cyan]Section ID[/cyan]",
                           default=f"{section_type}_{len(template.sections) + 1}")

    # Create the appropriate section
    if section_type == "metadata":
        section = _create_metadata_section(section_id)
    elif section_type == "text":
        section = _create_text_section(section_id)
    elif section_type == "summary":
        section = _create_summary_section(section_id)
    elif section_type == "table":
        section = _create_table_section(section_id, service)
    elif section_type == "graph":
        section = _create_graph_section(section_id, service)
    elif section_type == "issues":
        section = _create_issues_section(section_id)
    elif section_type == "recommendations":
        section = _create_recommendations_section(section_id)
    elif section_type == "loop":
        section = _create_loop_section(section_id, service)
    else:
        console.print("[red]Invalid section type[/red]")
        return

    template.add_section(section)
    console.print(f"[green]✓ Section '{section_id}' added[/green]")


def _create_metadata_section(section_id: str = "metadata") -> ReportSection:
    """Create metadata section interactively."""
    include_title = Confirm.ask("[cyan]Include title?[/cyan]", default=True)
    title = None
    if include_title:
        title = Prompt.ask("[cyan]Title[/cyan] (leave empty for auto-generate)", default="")
        title = title if title else None

    include_author = Confirm.ask("[cyan]Include author?[/cyan]", default=True)
    author = None
    if include_author:
        author = Prompt.ask("[cyan]Author name[/cyan]", default="")
        author = author if author else None

    include_description = Confirm.ask("[cyan]Include description?[/cyan]", default=True)
    description = None
    if include_description:
        description = Prompt.ask("[cyan]Description[/cyan]", default="")
        description = description if description else None

    include_notes = Confirm.ask("[cyan]Include notes section?[/cyan]", default=False)
    notes = None
    if include_notes:
        notes = Prompt.ask("[cyan]Notes[/cyan]", default="")

    return ReportSection(
        section_type=SectionType.METADATA,
        section_id=section_id,
        metadata=MetadataSection(
            include_title=include_title,
            title=title,
            include_author=include_author,
            author=author,
            include_date=True,
            include_description=include_description,
            description=description,
            include_notes=include_notes,
            notes=notes
        )
    )


def _create_text_section(section_id: str) -> ReportSection:
    """Create text section interactively."""
    heading = Prompt.ask("[cyan]Section heading[/cyan]", default="")
    heading = heading if heading else None

    console.print("[cyan]Enter text content (press Ctrl+D when done):[/cyan]")
    content_lines = []
    try:
        while True:
            line = input()
            content_lines.append(line)
    except EOFError:
        pass

    content = "\n".join(content_lines)

    return ReportSection(
        section_type=SectionType.TEXT,
        section_id=section_id,
        text=TextSection(
            content=content,
            heading=heading,
            markdown=True
        )
    )


def _create_summary_section(section_id: str) -> ReportSection:
    """Create summary section interactively."""
    levels = [level.value for level in AnalysisLevel]
    console.print("\n[cyan]Analysis level:[/cyan]")
    for i, level in enumerate(levels, 1):
        console.print(f"  {i}. {level}")
    level_idx = IntPrompt.ask("Select level", default=1) - 1
    level = AnalysisLevel(levels[level_idx])

    include_metrics = Confirm.ask("[cyan]Include general metrics?[/cyan]", default=True)
    include_test_summary = Confirm.ask("[cyan]Include test summary?[/cyan]", default=True)
    include_compliance = Confirm.ask("[cyan]Include compliance rates?[/cyan]", default=True)
    include_quality = Confirm.ask("[cyan]Include quality scores?[/cyan]", default=True)
    include_best = Confirm.ask("[cyan]Include best performing?[/cyan]", default=True)
    include_worst = Confirm.ask("[cyan]Include worst performing?[/cyan]", default=True)
    top_n = IntPrompt.ask("[cyan]Number of top/bottom items[/cyan]", default=5)

    return ReportSection(
        section_type=SectionType.SUMMARY,
        section_id=section_id,
        summary=SummarySection(
            level=level,
            include_metrics=include_metrics,
            include_test_summary=include_test_summary,
            include_compliance_rates=include_compliance,
            include_quality_scores=include_quality,
            include_best_performing=include_best,
            include_worst_performing=include_worst,
            top_n=top_n
        )
    )


def _create_table_section(section_id: str, service: ReportTemplateService) -> ReportSection:
    """Create table section interactively."""
    table_types = service.get_available_table_types()
    console.print("\n[cyan]Table type:[/cyan]")
    for i, ttype in enumerate(table_types, 1):
        console.print(f"  {i}. {ttype}")
    type_idx = IntPrompt.ask("Select type", default=1) - 1
    table_type = table_types[type_idx]

    title = Prompt.ask("[cyan]Table title[/cyan]", default="")
    title = title if title else None

    levels = [level.value for level in AnalysisLevel]
    console.print("\n[cyan]Analysis level:[/cyan]")
    for i, level in enumerate(levels, 1):
        console.print(f"  {i}. {level}")
    level_idx = IntPrompt.ask("Select level", default=1) - 1
    level = AnalysisLevel(levels[level_idx])

    # Sort options
    sort_orders = [order.value for order in SortOrder]
    console.print("\n[cyan]Sort order:[/cyan]")
    for i, order in enumerate(sort_orders, 1):
        console.print(f"  {i}. {order}")
    sort_idx = IntPrompt.ask("Select sort order", default=4) - 1
    sort_order = SortOrder(sort_orders[sort_idx])

    max_rows = None
    if Confirm.ask("[cyan]Limit number of rows?[/cyan]", default=False):
        max_rows = IntPrompt.ask("[cyan]Maximum rows[/cyan]", default=20)

    return ReportSection(
        section_type=SectionType.TABLE,
        section_id=section_id,
        table=TableSection(
            table_type=table_type,
            title=title,
            level=level,
            sort_order=sort_order,
            max_rows=max_rows
        )
    )


def _create_graph_section(section_id: str, service: ReportTemplateService) -> ReportSection:
    """Create graph section interactively."""
    graph_types = service.get_available_graph_types()
    console.print("\n[cyan]Graph type:[/cyan]")
    for i, gtype in enumerate(graph_types, 1):
        console.print(f"  {i}. {gtype}")
    type_idx = IntPrompt.ask("Select type", default=1) - 1
    graph_type = graph_types[type_idx]

    title = Prompt.ask("[cyan]Graph title[/cyan]", default="")
    title = title if title else None

    levels = [level.value for level in AnalysisLevel]
    console.print("\n[cyan]Analysis level:[/cyan]")
    for i, level in enumerate(levels, 1):
        console.print(f"  {i}. {level}")
    level_idx = IntPrompt.ask("Select level", default=1) - 1
    level = AnalysisLevel(levels[level_idx])

    # Parameters
    parameters = []
    if Confirm.ask("[cyan]Specify parameters?[/cyan]", default=True):
        available = service.get_available_parameters()
        console.print("\nAvailable parameters:")
        for i, param in enumerate(available, 1):
            console.print(f"  {i}. {param}")
        param_selection = Prompt.ask("[cyan]Select parameters[/cyan] (e.g., 1,2,4)", default="1")
        param_indices = [int(i.strip()) - 1 for i in param_selection.split(',')]
        parameters = [available[i] for i in param_indices if 0 <= i < len(available)]

    return ReportSection(
        section_type=SectionType.GRAPH,
        section_id=section_id,
        graph=GraphSection(
            graph_type=graph_type,
            title=title,
            level=level,
            parameters=parameters
        )
    )


def _create_issues_section(section_id: str) -> ReportSection:
    """Create issues section interactively."""
    levels = [level.value for level in AnalysisLevel]
    console.print("\n[cyan]Analysis level:[/cyan]")
    for i, level in enumerate(levels, 1):
        console.print(f"  {i}. {level}")
    level_idx = IntPrompt.ask("Select level", default=1) - 1
    level = AnalysisLevel(levels[level_idx])

    include_critical = Confirm.ask("[cyan]Include critical issues?[/cyan]", default=True)
    include_high = Confirm.ask("[cyan]Include high severity issues?[/cyan]", default=True)
    include_medium = Confirm.ask("[cyan]Include medium severity issues?[/cyan]", default=False)
    include_low = Confirm.ask("[cyan]Include low severity issues?[/cyan]", default=False)

    max_issues = None
    if Confirm.ask("[cyan]Limit number of issues?[/cyan]", default=True):
        max_issues = IntPrompt.ask("[cyan]Maximum issues[/cyan]", default=10)

    return ReportSection(
        section_type=SectionType.ISSUES,
        section_id=section_id,
        issues=IssuesSection(
            level=level,
            include_critical=include_critical,
            include_high=include_high,
            include_medium=include_medium,
            include_low=include_low,
            max_issues=max_issues
        )
    )


def _create_recommendations_section(section_id: str) -> ReportSection:
    """Create recommendations section interactively."""
    levels = [level.value for level in AnalysisLevel]
    console.print("\n[cyan]Analysis level:[/cyan]")
    for i, level in enumerate(levels, 1):
        console.print(f"  {i}. {level}")
    level_idx = IntPrompt.ask("Select level", default=1) - 1
    level = AnalysisLevel(levels[level_idx])

    max_recommendations = None
    if Confirm.ask("[cyan]Limit number of recommendations?[/cyan]", default=True):
        max_recommendations = IntPrompt.ask("[cyan]Maximum recommendations[/cyan]", default=10)

    return ReportSection(
        section_type=SectionType.RECOMMENDATIONS,
        section_id=section_id,
        recommendations=RecommendationsSection(
            level=level,
            max_recommendations=max_recommendations
        )
    )


def _create_loop_section(section_id: str, service: ReportTemplateService) -> ReportSection:
    """Create loop section interactively."""
    console.print("\n[cyan]Loop over:[/cyan]")
    console.print("  1. Buildings")
    console.print("  2. Rooms")
    loop_choice = IntPrompt.ask("Select", default=1)
    loop_over = AnalysisLevel.BUILDING if loop_choice == 1 else AnalysisLevel.ROOM

    # Sort options
    sort_orders = [order.value for order in SortOrder]
    console.print("\n[cyan]Sort order:[/cyan]")
    for i, order in enumerate(sort_orders, 1):
        console.print(f"  {i}. {order}")
    sort_idx = IntPrompt.ask("Select sort order", default=1) - 1
    sort_order = SortOrder(sort_orders[sort_idx])

    max_iterations = None
    if Confirm.ask("[cyan]Limit number of iterations?[/cyan]", default=True):
        max_iterations = IntPrompt.ask("[cyan]Maximum iterations[/cyan]", default=10)

    console.print("\n[yellow]Loop sections (sections to repeat for each entity):[/yellow]")
    console.print("[dim]You'll add sections that will be repeated for each building/room[/dim]")

    loop_sections = []
    # Add a few default sections for the loop
    if Confirm.ask("\n[cyan]Add summary for each entity?[/cyan]", default=True):
        loop_sections.append(_create_summary_section(f"{loop_over.value}_summary"))

    if Confirm.ask("[cyan]Add issues for each entity?[/cyan]", default=True):
        loop_sections.append(_create_issues_section(f"{loop_over.value}_issues"))

    if Confirm.ask("[cyan]Add recommendations for each entity?[/cyan]", default=True):
        loop_sections.append(_create_recommendations_section(f"{loop_over.value}_recommendations"))

    return ReportSection(
        section_type=SectionType.LOOP,
        section_id=section_id,
        loop=LoopSection(
            loop_over=loop_over,
            sort_order=sort_order,
            max_iterations=max_iterations,
            sections=loop_sections
        )
    )


def _remove_section_interactive(template: ReportTemplate):
    """Remove a section interactively."""
    if not template.sections:
        console.print("[yellow]No sections to remove.[/yellow]")
        return

    _display_sections(template)

    section_id = Prompt.ask("\n[cyan]Section ID to remove[/cyan]")
    if template.remove_section(section_id):
        console.print(f"[green]✓ Section '{section_id}' removed[/green]")
    else:
        console.print(f"[red]✗ Section '{section_id}' not found[/red]")


def _edit_section_interactive(template: ReportTemplate, service: ReportTemplateService):
    """Edit a section interactively."""
    if not template.sections:
        console.print("[yellow]No sections to edit.[/yellow]")
        return

    _display_sections(template)

    section_id = Prompt.ask("\n[cyan]Section ID to edit[/cyan]")
    section = template.get_section(section_id)

    if not section:
        console.print(f"[red]✗ Section '{section_id}' not found[/red]")
        return

    console.print(f"\n[cyan]Editing section: {section_id} ({section.section_type.value})[/cyan]")
    console.print("[yellow]Note: Full section editing not yet implemented.[/yellow]")
    console.print("[yellow]Use 'remove' then 'add' to replace a section.[/yellow]")


def _reorder_sections_interactive(template: ReportTemplate):
    """Reorder sections interactively."""
    if len(template.sections) < 2:
        console.print("[yellow]Need at least 2 sections to reorder.[/yellow]")
        return

    _display_sections(template)

    section_id = Prompt.ask("\n[cyan]Section ID to move[/cyan]")
    new_position = IntPrompt.ask("[cyan]New position (1-based)[/cyan]", default=1)

    if template.reorder_section(section_id, new_position - 1):
        console.print(f"[green]✓ Section '{section_id}' moved to position {new_position}[/green]")
    else:
        console.print(f"[red]✗ Failed to reorder section[/red]")


def _display_sections(template: ReportTemplate):
    """Display template sections."""
    console.print("\n[bold cyan]Template Sections:[/bold cyan]")

    table = Table(box=box.SIMPLE)
    table.add_column("#", style="dim", width=4)
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Enabled", justify="center")

    for i, section in enumerate(template.sections, 1):
        enabled = "✓" if section.enabled else "✗"
        table.add_row(str(i), section.section_id, section.section_type.value, enabled)

    console.print(table)


def _get_section_details(section: ReportSection) -> str:
    """Get a summary of section details."""
    if section.section_type == SectionType.METADATA:
        return "Title, author, date, description"
    elif section.section_type == SectionType.TEXT and section.text:
        return f"Text content ({len(section.text.content)} chars)"
    elif section.section_type == SectionType.GRAPH and section.graph:
        return f"{section.graph.graph_type} at {section.graph.level.value}"
    elif section.section_type == SectionType.TABLE and section.table:
        return f"{section.table.table_type} at {section.table.level.value}"
    elif section.section_type == SectionType.SUMMARY and section.summary:
        return f"Summary at {section.summary.level.value}"
    elif section.section_type == SectionType.RECOMMENDATIONS and section.recommendations:
        return f"Recommendations at {section.recommendations.level.value}"
    elif section.section_type == SectionType.ISSUES and section.issues:
        return f"Issues at {section.issues.level.value}"
    elif section.section_type == SectionType.LOOP and section.loop:
        return f"Loop over {section.loop.loop_over.value} ({len(section.loop.sections)} sections)"
    return ""
