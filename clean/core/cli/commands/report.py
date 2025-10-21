"""CLI commands for report generation."""

import click
from pathlib import Path
from rich.console import Console

from core.application.use_cases.generate_report import GenerateReportUseCase
from core.application.use_cases.load_analysis import LoadAnalysisUseCase
from core.application.use_cases.export_results import ExportResultsUseCase

console = Console()


@click.group()
def report():
    """Generate and export reports."""
    pass


@report.command(name='generate')
@click.option('--session', '-s', help='Load from saved session')
@click.option('--template', '-t', type=click.Path(path_type=Path), help='Report template path')
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output path')
@click.option('--format', '-f', type=click.Choice(['html', 'pdf']), default='html', help='Output format')
@click.pass_context
def generate_report(ctx, session, template, output, format):
    """
    Generate analysis report.

    Examples:
        ieq report generate --session my_session
        ieq report generate --output my_report.html
    """
    console.print("\n[cyan]Generating report...[/cyan]\n")
    
    try:
        # Load analysis data (from session or context)
        room_analyses = ctx.obj.get('room_analyses')
        building_analysis = ctx.obj.get('building_analysis')
        rooms = ctx.obj.get('rooms')
        
        if session:
            console.print(f"Loading session: {session}")
            load_use_case = LoadAnalysisUseCase()
            session_data = load_use_case.execute_load_session(session)
            # TODO: Convert loaded data back to proper objects
            console.print("[yellow]Note: Session loading partially implemented[/yellow]")
        
        if not rooms:
            console.print("[red]✗ No data available for report[/red]")
            console.print("Run analysis first or load a session")
            ctx.exit(1)
        
        # Generate report
        use_case = GenerateReportUseCase()
        building_name = building_analysis.building_name if building_analysis else "Building"
        
        report_path = use_case.execute(
            rooms=rooms,
            building_name=building_name,
            output_path=output,
            template_path=template,
            building_analysis=building_analysis,
        )
        
        console.print(f"[green]✓ Report generated:[/green] {report_path}")
        
    except Exception as e:
        console.print(f"\n[red]✗ Report generation failed:[/red] {str(e)}")
        if ctx.obj.get('verbose'):
            console.print_exception()
        ctx.exit(1)


@report.command(name='export')
@click.option('--session', '-s', help='Load from saved session')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'excel']), default='json', help='Export format')
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output path')
@click.pass_context
def export_results(ctx, session, format, output):
    """
    Export analysis results to file.

    Examples:
        ieq report export --format json
        ieq report export --format excel --output results.xlsx
    """
    console.print(f"\n[cyan]Exporting to {format.upper()}...[/cyan]\n")
    
    try:
        # Get analysis data
        room_analyses = ctx.obj.get('room_analyses')
        building_analysis = ctx.obj.get('building_analysis')
        
        if session:
            console.print(f"Loading session: {session}")
            load_use_case = LoadAnalysisUseCase()
            session_data = load_use_case.execute_load_session(session)
            # TODO: Convert loaded data
        
        if not room_analyses:
            console.print("[red]✗ No analysis data available[/red]")
            console.print("Run analysis first or load a session")
            ctx.exit(1)
        
        # Export based on format
        use_case = ExportResultsUseCase()
        
        if format == 'json':
            export_path = use_case.execute_export_json(
                room_analyses=room_analyses,
                building_analysis=building_analysis,
                output_path=output,
            )
        elif format == 'csv':
            export_path = use_case.execute_export_csv(
                room_analyses=room_analyses,
                output_path=output,
            )
        elif format == 'excel':
            export_path = use_case.execute_export_excel(
                room_analyses=room_analyses,
                building_analysis=building_analysis,
                output_path=output,
            )
        
        console.print(f"[green]✓ Exported to:[/green] {export_path}")
        
    except Exception as e:
        console.print(f"\n[red]✗ Export failed:[/red] {str(e)}")
        if ctx.obj.get('verbose'):
            console.print_exception()
        ctx.exit(1)


@report.command(name='list-templates')
@click.pass_context
def list_templates(ctx):
    """
    List available report templates.

    Examples:
        ieq report list-templates
    """
    console.print("\n[cyan]Available Report Templates:[/cyan]\n")
    
    template_dir = Path("config/report_templates")
    if not template_dir.exists():
        console.print("[yellow]No templates directory found[/yellow]")
        return
    
    templates = list(template_dir.glob("*.yaml"))
    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        return
    
    for template in templates:
        console.print(f"• {template.stem}")
