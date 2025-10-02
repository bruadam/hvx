"""
CLI commands for running hierarchical analysis.
"""

import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from src.models.building_data import BuildingDataset
from src.services.hierarchical_analysis_service import HierarchicalAnalysisService

console = Console()
logger = logging.getLogger(__name__)


@click.group(name='analyze')
def analyze_cli():
    """Run hierarchical analysis on building data."""
    pass


@analyze_cli.command(name='run')
@click.argument('dataset_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--config',
    type=click.Path(exists=True, path_type=Path),
    default='config/tests.yaml',
    help='Path to tests configuration file'
)
@click.option(
    '--test-set',
    help='Name of test set to use (instead of all tests in config)'
)
@click.option(
    '--output',
    type=click.Path(path_type=Path),
    default='output/analysis',
    help='Output directory for analysis results'
)
@click.option(
    '--portfolio-name',
    default='Portfolio',
    help='Name for the portfolio analysis'
)
@click.option(
    '--no-individual-files',
    is_flag=True,
    help='Skip saving individual JSON files per room/level/building'
)
@click.option(
    '--explore',
    is_flag=True,
    help='Launch interactive analysis explorer after completion'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Show verbose output'
)
def run_analysis(
    dataset_file: Path,
    config: Path,
    test_set: Optional[str],
    output: Path,
    portfolio_name: str,
    no_individual_files: bool,
    explore: bool,
    verbose: bool
):
    """
    Run hierarchical analysis on a loaded dataset.

    Performs analysis at room, level, building, and portfolio levels.
    Results are saved as JSON files in a hierarchical structure.

    Example:
        hvx analyze run output/dataset.pkl --config config/tests.yaml
        hvx analyze run output/dataset.pkl --test-set summer_analysis
        hvx analyze run output/dataset.pkl --explore
    """
    if verbose:
        logging.basicConfig(level=logging.INFO)

    try:
        # Handle test set if specified
        config_to_use = config
        if test_set:
            from src.services.test_management_service import TestManagementService
            import tempfile

            # Create temporary config with only the test set
            service = TestManagementService(config)
            if not service.get_test_set(test_set):
                console.print(f"[red]✗ Test set '{test_set}' not found in config.[/red]")
                console.print(f"[yellow]Available test sets:[/yellow]")
                for ts in service.list_test_sets():
                    console.print(f"  • {ts.name}")
                raise click.Abort()

            # Export test set to temporary file
            import os
            fd, temp_path = tempfile.mkstemp(suffix='.yaml')
            os.close(fd)
            temp_config = Path(temp_path)
            service.export_test_set_config(test_set, temp_config)
            config_to_use = temp_config

            console.print(f"[green]✓ Using test set: {test_set}[/green]\n")

        console.print(Panel.fit(
            f"[bold blue]Hierarchical Analysis[/bold blue]\n"
            f"Dataset: {dataset_file}\n"
            f"Config: {config}\n"
            + (f"Test Set: {test_set}\n" if test_set else "")
            + f"Output: {output}",
            border_style="blue"
        ))

        # Load dataset
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading dataset...", total=None)
            dataset = BuildingDataset.load_from_pickle(dataset_file)
            progress.update(task, completed=True)

        console.print(f"✓ Loaded {dataset.get_building_count()} buildings "
                     f"with {dataset.get_total_room_count()} rooms\n")

        # Initialize analysis service
        service = HierarchicalAnalysisService(config_path=config_to_use)
        
        # Run analysis
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running hierarchical analysis...", total=None)
            
            results = service.analyze_dataset(
                dataset=dataset,
                output_dir=output,
                portfolio_name=portfolio_name,
                save_individual_files=not no_individual_files
            )
            
            progress.update(task, completed=True)
        
        # Display summary
        _display_analysis_summary(results, output)
        
        console.print(f"\n✓ Analysis complete! Results saved to: [cyan]{output}[/cyan]")
        
        # Launch explorer if requested
        if explore:
            console.print("\n[bold cyan]Launching analysis explorer...[/bold cyan]")
            from src.utils.analysis_explorer import launch_analysis_explorer
            launch_analysis_explorer(output)
        
    except FileNotFoundError as e:
        console.print(f"[red]✗ Error:[/red] {e}", style="red")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error during analysis:[/red] {e}", style="red")
        if verbose:
            console.print_exception()
        raise click.Abort()


@analyze_cli.command(name='explore')
@click.argument('analysis_dir', type=click.Path(exists=True, path_type=Path), default='output/analysis')
def explore_analysis(analysis_dir: Path):
    """
    Launch interactive explorer for browsing analysis results.
    
    Navigate through the hierarchical analysis results from portfolio → buildings → levels → rooms.
    View test results, compliance rates, issues, and recommendations at each level.
    
    Example:
        hvx analyze explore output/analysis
        hvx analyze explore  # Uses default output/analysis directory
    """
    try:
        from src.utils.analysis_explorer import launch_analysis_explorer
        
        console.print(f"[bold cyan]Loading analysis from:[/bold cyan] {analysis_dir}\n")
        launch_analysis_explorer(analysis_dir)
        
    except FileNotFoundError as e:
        console.print(f"[red]✗ Error:[/red] {e}", style="red")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error launching explorer:[/red] {e}", style="red")
        console.print_exception()
        raise click.Abort()


@analyze_cli.command(name='summary')
@click.argument('analysis_dir', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--level',
    type=click.Choice(['portfolio', 'building', 'level', 'room']),
    default='portfolio',
    help='Analysis level to display'
)
@click.option(
    '--entity-id',
    help='Specific entity ID to display (e.g., building-1, level-1-1, room-1-1-01)'
)
def show_summary(analysis_dir: Path, level: str, entity_id: Optional[str]):
    """
    Display analysis summary from saved results.
    
    Example:
        hvx analyze summary output/analysis --level portfolio
        hvx analyze summary output/analysis --level building --entity-id building-1
    """
    try:
        if level == 'portfolio':
            _display_portfolio_summary(analysis_dir)
        elif level == 'building':
            _display_building_summary(analysis_dir, entity_id)
        elif level == 'level':
            _display_level_summary(analysis_dir, entity_id)
        elif level == 'room':
            _display_room_summary(analysis_dir, entity_id)
            
    except FileNotFoundError as e:
        console.print(f"[red]✗ Error:[/red] {e}", style="red")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error displaying summary:[/red] {e}", style="red")
        console.print_exception()
        raise click.Abort()


def _display_analysis_summary(results, output_dir: Path):
    """Display a summary of analysis results."""
    console.print("\n[bold cyan]Analysis Summary[/bold cyan]")
    
    # Portfolio summary
    if results.portfolio:
        console.print(f"\n[bold]Portfolio:[/bold] {results.portfolio.portfolio_name}")
        
        table = Table(box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Buildings", str(results.portfolio.building_count))
        table.add_row("Total Levels", str(results.portfolio.total_level_count))
        table.add_row("Total Rooms", str(results.portfolio.total_room_count))
        table.add_row("Avg Compliance", f"{results.portfolio.avg_compliance_rate:.1f}%")
        table.add_row("Avg Quality Score", f"{results.portfolio.avg_quality_score:.1f}%")
        
        console.print(table)
        
        # Top issues
        if results.portfolio.common_issues:
            console.print("\n[bold yellow]Common Issues:[/bold yellow]")
            for item in results.portfolio.common_issues[:5]:
                console.print(f"  • {item['issue']} (occurs in {item['occurrence_count']} buildings)")
    
    # Building summary
    console.print(f"\n[bold]Buildings Analyzed:[/bold] {len(results.buildings)}")
    
    building_table = Table(box=box.SIMPLE)
    building_table.add_column("Building", style="cyan")
    building_table.add_column("Rooms", justify="right")
    building_table.add_column("Levels", justify="right")
    building_table.add_column("Compliance", justify="right")
    building_table.add_column("Quality", justify="right")
    
    for building_id, building in sorted(results.buildings.items()):
        building_table.add_row(
            building.building_name,
            str(building.room_count),
            str(building.level_count),
            f"{building.avg_compliance_rate:.1f}%",
            f"{building.avg_quality_score:.1f}%"
        )
    
    console.print(building_table)
    
    # Output structure
    console.print(f"\n[bold]Output Structure:[/bold]")
    console.print(f"  {output_dir}/")
    console.print(f"    ├── portfolio.json")
    console.print(f"    ├── buildings/")
    for building_id in results.buildings.keys():
        console.print(f"    │   └── {building_id}.json")
    console.print(f"    ├── levels/")
    console.print(f"    │   └── *.json ({len(results.levels)} files)")
    console.print(f"    └── rooms/")
    console.print(f"        └── *.json ({len(results.rooms)} files)")


def _display_portfolio_summary(analysis_dir: Path):
    """Display portfolio analysis summary."""
    from src.models.analysis_models import PortfolioAnalysis
    
    portfolio_file = analysis_dir / "portfolio.json"
    if not portfolio_file.exists():
        console.print(f"[red]Portfolio analysis not found at: {portfolio_file}[/red]")
        return
    
    portfolio = PortfolioAnalysis.load_from_json(portfolio_file)
    
    console.print(Panel.fit(
        f"[bold blue]Portfolio Analysis[/bold blue]\n"
        f"Name: {portfolio.portfolio_name}\n"
        f"Buildings: {portfolio.building_count}",
        border_style="blue"
    ))
    
    # Metrics table
    table = Table(title="Portfolio Metrics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Buildings", str(portfolio.building_count))
    table.add_row("Total Levels", str(portfolio.total_level_count))
    table.add_row("Total Rooms", str(portfolio.total_room_count))
    table.add_row("Avg Compliance Rate", f"{portfolio.avg_compliance_rate:.1f}%")
    table.add_row("Avg Quality Score", f"{portfolio.avg_quality_score:.1f}%")
    table.add_row("Analysis Date", portfolio.analysis_timestamp.strftime("%Y-%m-%d %H:%M"))
    
    console.print(table)
    
    # Best/worst buildings
    if portfolio.best_performing_buildings:
        console.print("\n[bold green]Best Performing Buildings:[/bold green]")
        for item in portfolio.best_performing_buildings[:5]:
            console.print(f"  • {item['building_name']}: {item['compliance_rate']:.1f}%")
    
    if portfolio.worst_performing_buildings:
        console.print("\n[bold red]Worst Performing Buildings:[/bold red]")
        for item in portfolio.worst_performing_buildings[:5]:
            console.print(f"  • {item['building_name']}: {item['compliance_rate']:.1f}%")
    
    # Common issues
    if portfolio.common_issues:
        console.print("\n[bold yellow]Common Issues:[/bold yellow]")
        for item in portfolio.common_issues[:5]:
            console.print(f"  • {item['issue']} (occurs {item['occurrence_count']} times)")
    
    # Investment priorities
    if portfolio.investment_priorities:
        console.print("\n[bold magenta]Investment Priorities:[/bold magenta]")
        for item in portfolio.investment_priorities[:5]:
            console.print(
                f"  {item['priority_rank']}. {item['building_name']} - "
                f"{item['compliance_rate']:.1f}% compliance ({item['estimated_impact']} impact)"
            )


def _display_building_summary(analysis_dir: Path, building_id: Optional[str]):
    """Display building analysis summary."""
    from src.models.analysis_models import BuildingAnalysis
    
    buildings_dir = analysis_dir / "buildings"
    
    if building_id:
        building_file = buildings_dir / f"{building_id}.json"
        if not building_file.exists():
            console.print(f"[red]Building analysis not found: {building_id}[/red]")
            return
        
        building = BuildingAnalysis.load_from_json(building_file)
        _display_single_building(building)
    else:
        # List all buildings
        if not buildings_dir.exists():
            console.print(f"[red]Buildings directory not found: {buildings_dir}[/red]")
            return
        
        console.print("[bold cyan]Available Buildings:[/bold cyan]\n")
        for building_file in sorted(buildings_dir.glob("*.json")):
            building = BuildingAnalysis.load_from_json(building_file)
            console.print(
                f"  • {building.building_id}: {building.building_name} - "
                f"{building.room_count} rooms, {building.avg_compliance_rate:.1f}% compliance"
            )


def _display_single_building(building):
    """Display detailed building analysis."""
    console.print(Panel.fit(
        f"[bold blue]Building Analysis[/bold blue]\n"
        f"ID: {building.building_id}\n"
        f"Name: {building.building_name}",
        border_style="blue"
    ))
    
    # Metrics
    table = Table(title="Building Metrics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    
    table.add_row("Levels", str(building.level_count))
    table.add_row("Rooms", str(building.room_count))
    table.add_row("Avg Compliance", f"{building.avg_compliance_rate:.1f}%")
    table.add_row("Avg Quality", f"{building.avg_quality_score:.1f}%")
    table.add_row("Status", building.status.value)
    
    console.print(table)
    
    # Best/worst rooms
    if building.best_performing_rooms:
        console.print("\n[bold green]Best Performing Rooms:[/bold green]")
        for room in building.best_performing_rooms[:3]:
            console.print(f"  • {room['room_name']}: {room['compliance_rate']:.1f}%")
    
    if building.worst_performing_rooms:
        console.print("\n[bold red]Worst Performing Rooms:[/bold red]")
        for room in building.worst_performing_rooms[:3]:
            console.print(f"  • {room['room_name']}: {room['compliance_rate']:.1f}%")


def _display_level_summary(analysis_dir: Path, level_id: Optional[str]):
    """Display level analysis summary."""
    from src.models.analysis_models import LevelAnalysis
    
    levels_dir = analysis_dir / "levels"
    
    if level_id:
        level_file = levels_dir / f"{level_id}.json"
        if not level_file.exists():
            console.print(f"[red]Level analysis not found: {level_id}[/red]")
            return
        
        level = LevelAnalysis.load_from_json(level_file)
        _display_single_level(level)
    else:
        # List all levels
        if not levels_dir.exists():
            console.print(f"[red]Levels directory not found: {levels_dir}[/red]")
            return
        
        console.print("[bold cyan]Available Levels:[/bold cyan]\n")
        for level_file in sorted(levels_dir.glob("*.json")):
            level = LevelAnalysis.load_from_json(level_file)
            console.print(
                f"  • {level.level_id}: {level.level_name} - "
                f"{level.room_count} rooms, {level.avg_compliance_rate:.1f}% compliance"
            )


def _display_single_level(level):
    """Display detailed level analysis."""
    console.print(Panel.fit(
        f"[bold blue]Level Analysis[/bold blue]\n"
        f"ID: {level.level_id}\n"
        f"Name: {level.level_name}",
        border_style="blue"
    ))
    
    # Metrics
    table = Table(title="Level Metrics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    
    table.add_row("Rooms", str(level.room_count))
    table.add_row("Avg Compliance", f"{level.avg_compliance_rate:.1f}%")
    table.add_row("Avg Quality", f"{level.avg_quality_score:.1f}%")
    table.add_row("Status", level.status.value)
    
    console.print(table)
    
    # Room rankings
    if level.best_performing_rooms:
        console.print("\n[bold green]Best Performing Rooms:[/bold green]")
        for room in level.best_performing_rooms:
            console.print(f"  • {room['room_name']}: {room['compliance_rate']:.1f}%")
    
    if level.worst_performing_rooms:
        console.print("\n[bold red]Worst Performing Rooms:[/bold red]")
        for room in level.worst_performing_rooms:
            console.print(f"  • {room['room_name']}: {room['compliance_rate']:.1f}%")


def _display_room_summary(analysis_dir: Path, room_id: Optional[str]):
    """Display room analysis summary."""
    from src.models.analysis_models import RoomAnalysis
    
    rooms_dir = analysis_dir / "rooms"
    
    if room_id:
        room_file = rooms_dir / f"{room_id}.json"
        if not room_file.exists():
            console.print(f"[red]Room analysis not found: {room_id}[/red]")
            return
        
        room = RoomAnalysis.load_from_json(room_file)
        _display_single_room(room)
    else:
        # List all rooms (limited)
        if not rooms_dir.exists():
            console.print(f"[red]Rooms directory not found: {rooms_dir}[/red]")
            return
        
        console.print("[bold cyan]Sample Rooms (first 20):[/bold cyan]\n")
        for i, room_file in enumerate(sorted(rooms_dir.glob("*.json"))[:20]):
            room = RoomAnalysis.load_from_json(room_file)
            console.print(
                f"  • {room.room_id}: {room.room_name} - "
                f"{room.overall_compliance_rate:.1f}% compliance"
            )
        
        total_rooms = len(list(rooms_dir.glob("*.json")))
        if total_rooms > 20:
            console.print(f"\n  ... and {total_rooms - 20} more rooms")


def _display_single_room(room):
    """Display detailed room analysis."""
    console.print(Panel.fit(
        f"[bold blue]Room Analysis[/bold blue]\n"
        f"ID: {room.room_id}\n"
        f"Name: {room.room_name}",
        border_style="blue"
    ))
    
    # Metrics
    table = Table(title="Room Metrics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    
    table.add_row("Overall Compliance", f"{room.overall_compliance_rate:.1f}%")
    table.add_row("Data Completeness", f"{room.data_completeness:.1f}%")
    table.add_row("Quality Score", f"{room.overall_quality_score:.1f}%")
    table.add_row("Parameters", ", ".join(room.parameters_analyzed))
    table.add_row("Status", room.status.value)
    
    if room.data_period_start and room.data_period_end:
        table.add_row("Data Period", f"{room.data_period_start.date()} to {room.data_period_end.date()}")
    
    console.print(table)
    
    # Test results
    if room.test_results:
        console.print("\n[bold]Test Results:[/bold]")
        test_table = Table(box=box.SIMPLE)
        test_table.add_column("Test", style="cyan")
        test_table.add_column("Parameter")
        test_table.add_column("Compliance", justify="right")
        test_table.add_column("Severity")
        
        for test_name, result in room.test_results.items():
            severity_color = {
                'CRITICAL': 'red',
                'HIGH': 'yellow',
                'MEDIUM': 'cyan',
                'LOW': 'green',
                'INFO': 'white'
            }.get(result.severity.value, 'white')
            
            test_table.add_row(
                test_name,
                result.parameter,
                f"{result.compliance_rate:.1f}%",
                f"[{severity_color}]{result.severity.value}[/{severity_color}]"
            )
        
        console.print(test_table)
    
    # Critical issues
    if room.critical_issues:
        console.print("\n[bold red]Critical Issues:[/bold red]")
        for issue in room.critical_issues[:5]:
            console.print(f"  • {issue}")
    
    # Recommendations
    if room.recommendations:
        console.print("\n[bold yellow]Recommendations:[/bold yellow]")
        for rec in room.recommendations[:5]:
            console.print(f"  • {rec}")
