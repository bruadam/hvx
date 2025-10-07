"""
Reports command - Generate HTML reports from IEQ analysis results.
"""

import click
import json
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.core.reporting.HTMLReportRenderer import HTMLReportRenderer

console = Console()


@click.command(name='reports')
@click.option('--analysis', '-a', type=click.Path(exists=True, path_type=Path),
              help='Path to analysis JSON file')
@click.option('--template', '-t', type=str,
              help='Template name (building_detailed, standard_building, portfolio_summary)')
@click.option('--output', '-o', type=str,
              help='Output filename (default: auto-generated)')
@click.option('--interactive', '-i', is_flag=True,
              help='Run in interactive mode')
@click.option('--all', is_flag=True,
              help='Generate all available templates')
@click.option('--list-templates', is_flag=True,
              help='List available templates')
@click.option('--list-analysis', is_flag=True,
              help='List available analysis files')
def reports(analysis: Optional[Path], template: Optional[str], output: Optional[str],
           interactive: bool, all: bool, list_templates: bool, list_analysis: bool):
    """
    Generate HTML reports from IEQ analysis results.

    This command generates comprehensive HTML reports with detailed room-by-room
    analysis, charts, weather correlations, and actionable recommendations.

    Examples:

    \b
        # Interactive mode - choose everything interactively
        hvx ieq reports --interactive

        # Manual mode - specify all parameters
        hvx ieq reports -a output/analysis/buildings/building_1.json -t building_detailed

        # Generate all templates for a building
        hvx ieq reports -a output/analysis/buildings/building_1.json --all

        # List available options
        hvx ieq reports --list-templates
        hvx ieq reports --list-analysis
    """

    if list_templates:
        _list_templates()
        return

    if list_analysis:
        _list_analysis_files()
        return

    if interactive:
        _interactive_report_generation()
        return

    # Manual mode - validate required parameters
    if not analysis:
        console.print("[red]✗ Error:[/red] Analysis file is required in manual mode")
        console.print("[dim]Use --interactive or provide --analysis option[/dim]")
        raise click.Abort()

    if not template and not all:
        console.print("[red]✗ Error:[/red] Template is required in manual mode")
        console.print("[dim]Use --interactive, --template, or --all option[/dim]")
        raise click.Abort()

    if all:
        _generate_all_templates(analysis, output)
    else:
        if template:  # Ensure template is not None
            _generate_single_report(analysis, template, output)


def _list_templates():
    """List available report templates."""
    console.print(Panel.fit("[bold blue]Available Report Templates[/bold blue]"))
    
    templates_dir = Path("config/report_templates")
    if not templates_dir.exists():
        console.print("[red]No templates directory found[/red]")
        return

    table = Table(title="Report Templates", style="blue")
    table.add_column("Template", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Format", style="green")

    templates = [
        ("building_detailed", "Comprehensive building analysis with detailed room cards", "HTML"),
        ("standard_building", "Standard building performance analysis", "HTML"),
        ("portfolio_summary", "Portfolio-wide summary report", "HTML"),
    ]

    for template_name, description, format_type in templates:
        template_path = templates_dir / f"{template_name}.yaml"
        if template_path.exists():
            table.add_row(f"[cyan]{template_name}[/cyan]", description, format_type)

    console.print(table)
    console.print("\n[dim]Use: hvx ieq reports -t <template_name> -a <analysis_file>[/dim]")


def _list_analysis_files():
    """List available analysis files."""
    console.print(Panel.fit("[bold blue]Available Analysis Files[/bold blue]"))
    
    # Check for building analysis files
    buildings_dir = Path("output/analysis/buildings")
    rooms_dir = Path("output/analysis/rooms")
    portfolio_file = Path("output/analysis/portfolio_analysis.json")

    table = Table(title="Analysis Files", style="blue")
    table.add_column("Type", style="green")
    table.add_column("File", style="cyan")
    table.add_column("Building", style="white")
    table.add_column("Rooms", style="yellow")
    table.add_column("Compliance", style="magenta")

    # Building analysis files
    if buildings_dir.exists():
        for file_path in buildings_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                building_name = data.get('building_name', 'Unknown')
                room_count = data.get('room_count', 0)
                compliance = data.get('avg_compliance_rate', 0)
                
                table.add_row(
                    "Building",
                    f"[cyan]{file_path.name}[/cyan]",
                    building_name,
                    str(room_count),
                    f"{compliance:.1f}%"
                )
            except Exception:
                table.add_row("Building", f"[red]{file_path.name}[/red]", "Error loading", "-", "-")

    # Portfolio analysis
    if portfolio_file.exists():
        try:
            with open(portfolio_file, 'r') as f:
                data = json.load(f)
            
            building_count = len(data.get('buildings', []))
            avg_compliance = data.get('avg_compliance_rate', 0)
            
            table.add_row(
                "Portfolio",
                f"[cyan]{portfolio_file.name}[/cyan]",
                f"{building_count} buildings",
                "-",
                f"{avg_compliance:.1f}%"
            )
        except Exception:
            table.add_row("Portfolio", f"[red]{portfolio_file.name}[/red]", "Error loading", "-", "-")

    if table.row_count == 0:
        console.print("[yellow]No analysis files found[/yellow]")
        console.print("[dim]Run analysis first: hvx ieq start[/dim]")
    else:
        console.print(table)
        console.print("\n[dim]Use: hvx ieq reports -a <file_path>[/dim]")


def _interactive_report_generation():
    """Interactive report generation workflow."""
    console.print(Panel.fit("[bold blue]Interactive Report Generation[/bold blue]"))
    
    # Step 1: Select analysis file
    analysis_file = _select_analysis_file()
    if not analysis_file:
        console.print("[yellow]No analysis file selected. Exiting.[/yellow]")
        return

    # Step 2: Select template(s)
    templates = _select_templates()
    if not templates:
        console.print("[yellow]No templates selected. Exiting.[/yellow]")
        return

    # Step 3: Generate reports
    _generate_reports_interactive(analysis_file, templates)


def _select_analysis_file() -> Optional[Path]:
    """Interactively select an analysis file."""
    console.print("\n[bold]Step 1:[/bold] Select Analysis File")
    
    # Find available files
    buildings_dir = Path("output/analysis/buildings")
    portfolio_file = Path("output/analysis/portfolio_analysis.json")
    
    files = []
    
    # Add building files
    if buildings_dir.exists():
        for file_path in buildings_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                building_name = data.get('building_name', 'Unknown')
                room_count = data.get('room_count', 0)
                compliance = data.get('avg_compliance_rate', 0)
                files.append({
                    'path': file_path,
                    'type': 'Building',
                    'name': building_name,
                    'display': f"{building_name} ({room_count} rooms, {compliance:.1f}% compliance)"
                })
            except Exception:
                continue

    # Add portfolio file
    if portfolio_file.exists():
        try:
            with open(portfolio_file, 'r') as f:
                data = json.load(f)
            building_count = len(data.get('buildings', []))
            files.append({
                'path': portfolio_file,
                'type': 'Portfolio',
                'name': 'Portfolio Summary',
                'display': f"Portfolio Summary ({building_count} buildings)"
            })
        except Exception:
            pass

    if not files:
        console.print("[red]No analysis files found![/red]")
        console.print("[dim]Run analysis first: hvx ieq start[/dim]")
        return None

    # Display options
    console.print("\nAvailable analysis files:")
    for i, file_info in enumerate(files, 1):
        console.print(f"  {i}. [{file_info['type']}] {file_info['display']}")

    # Get user choice
    while True:
        try:
            choice = Prompt.ask(
                f"\nSelect file (1-{len(files)})",
                default="1"
            )
            index = int(choice) - 1
            if 0 <= index < len(files):
                selected_file = files[index]['path']
                console.print(f"[green]✓[/green] Selected: {files[index]['display']}")
                return selected_file
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")


def _select_templates() -> List[str]:
    """Interactively select report template(s)."""
    console.print("\n[bold]Step 2:[/bold] Select Report Template(s)")
    
    templates = [
        {
            'name': 'building_detailed',
            'display': 'Building Detailed - Comprehensive analysis with room cards, charts, weather correlations',
            'recommended': True
        },
        {
            'name': 'standard_building',
            'display': 'Standard Building - Standard performance analysis',
            'recommended': False
        },
        {
            'name': 'portfolio_summary',
            'display': 'Portfolio Summary - Portfolio-wide overview (for portfolio analysis)',
            'recommended': False
        }
    ]

    console.print("\nAvailable templates:")
    for i, template in enumerate(templates, 1):
        recommended = " [bold green](Recommended)[/bold green]" if template['recommended'] else ""
        console.print(f"  {i}. {template['display']}{recommended}")

    # Ask for selection method
    use_all = Confirm.ask("\nGenerate all templates?", default=False)
    if use_all:
        return [t['name'] for t in templates]

    # Select individual templates
    selected = []
    console.print("\nSelect templates (enter numbers separated by commas, e.g., '1,3'):")
    
    while True:
        try:
            choices = Prompt.ask("Template numbers", default="1")
            indices = [int(x.strip()) - 1 for x in choices.split(',')]
            
            valid_indices = [i for i in indices if 0 <= i < len(templates)]
            if valid_indices:
                selected = [templates[i]['name'] for i in valid_indices]
                selected_names = [templates[i]['display'].split(' - ')[0] for i in valid_indices]
                console.print(f"[green]✓[/green] Selected: {', '.join(selected_names)}")
                return selected
            else:
                console.print("[red]Invalid choices. Please try again.[/red]")
        except ValueError:
            console.print("[red]Please enter valid numbers separated by commas.[/red]")


def _generate_reports_interactive(analysis_file: Path, templates: List[str]):
    """Generate reports interactively with progress display."""
    console.print(f"\n[bold]Step 3:[/bold] Generating Reports")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        total_task = progress.add_task("Generating reports...", total=len(templates))
        
        for template_name in templates:
            progress.update(total_task, description=f"Generating {template_name}...")
            
            try:
                success = _generate_single_report(analysis_file, template_name, None, quiet=True)
                if success:
                    console.print(f"[green]✓[/green] Generated: {template_name}")
                else:
                    console.print(f"[red]✗[/red] Failed: {template_name}")
            except Exception as e:
                console.print(f"[red]✗[/red] Error generating {template_name}: {str(e)}")
            
            progress.advance(total_task)

    console.print(f"\n[bold green]✓ Report generation complete![/bold green]")
    console.print("[dim]Reports saved to: output/reports/[/dim]")


def _generate_single_report(analysis_file: Path, template_name: str, output_name: Optional[str] = None, quiet: bool = False) -> bool:
    """Generate a single report."""
    try:
        html_renderer = HTMLReportRenderer()
        
        # Load analysis data
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        if not quiet:
            building_name = analysis_data.get('building_name', 'Unknown')
            room_count = analysis_data.get('room_count', 0)
            compliance = analysis_data.get('avg_compliance_rate', 0)
            
            console.print(f"\n[cyan]Generating report:[/cyan]")
            console.print(f"  Building: {building_name}")
            console.print(f"  Rooms: {room_count}")
            console.print(f"  Compliance: {compliance:.1f}%")
            console.print(f"  Template: {template_name}")

        # Generate output filename if not provided
        if not output_name:
            building_id = analysis_data.get('building_id', 'building')
            timestamp = analysis_data.get('analysis_timestamp', '').replace(':', '-').replace('T', '_')[:15]
            output_name = f"{template_name}_{building_id}_{timestamp}.html"

        # Generate report
        result = html_renderer.render_report(
            config_path=Path(f"config/report_templates/{template_name}.yaml"),
            analysis_results=analysis_data,
            output_filename=output_name
        )

        # Check output
        output_path = Path("output/reports") / output_name
        if output_path.exists():
            file_size = output_path.stat().st_size
            if not quiet:
                console.print(f"\n[green]✓ Report generated successfully![/green]")
                console.print(f"  File: {output_path}")
                console.print(f"  Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                
                # Check content
                content = output_path.read_text()
                room_cards = content.count('room-card')
                charts = content.count('data:image/png;base64,')
                weather_sections = content.count('weather-correlations')
                
                if room_cards > 0 or charts > 0:
                    console.print(f"\n[bold]Content Summary:[/bold]")
                    if room_cards > 0:
                        console.print(f"  📋 Room cards: {room_cards}")
                    if charts > 0:
                        console.print(f"  📊 Charts: {charts}")
                    if weather_sections > 0:
                        console.print(f"  ☀️ Weather correlations: {weather_sections}")
            
            return True
        else:
            if not quiet:
                console.print(f"[red]✗ Report file not found: {output_path}[/red]")
            return False

    except Exception as e:
        if not quiet:
            console.print(f"[red]✗ Error generating report: {str(e)}[/red]")
        return False


def _generate_all_templates(analysis_file: Path, output_prefix: Optional[str] = None):
    """Generate reports for all available templates."""
    templates = ['building_detailed', 'standard_building', 'portfolio_summary']
    
    console.print(f"[cyan]Generating all templates for:[/cyan] {analysis_file.name}")
    
    with Progress(console=console) as progress:
        task = progress.add_task("Generating reports...", total=len(templates))
        
        for template_name in templates:
            output_name = f"{output_prefix}_{template_name}.html" if output_prefix else None
            
            try:
                template_path = Path(f"config/report_templates/{template_name}.yaml")
                if template_path.exists():
                    _generate_single_report(analysis_file, template_name, output_name, quiet=True)
                    console.print(f"[green]✓[/green] {template_name}")
                else:
                    console.print(f"[yellow]⚠[/yellow] {template_name} (template not found)")
            except Exception as e:
                console.print(f"[red]✗[/red] {template_name}: {str(e)}")
            
            progress.advance(task)

    console.print(f"\n[bold green]✓ All reports generated![/bold green]")
    console.print("[dim]Reports saved to: output/reports/[/dim]")


if __name__ == '__main__':
    reports()