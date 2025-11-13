"""CLI commands for analysis operations."""

from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from core.application.use_cases.load_data import LoadDataUseCase
from core.application.use_cases.run_analysis import RunAnalysisUseCase
from core.application.use_cases.save_analysis import SaveAnalysisUseCase

console = Console()


@click.group()
def analyze():
    """Run IEQ analysis commands."""
    pass


@analyze.command(name='run')
@click.argument('data_dir', type=click.Path(exists=True, path_type=Path))
@click.option('--standard', '-s', default='en16798-1', help='Compliance standard')
@click.option('--save', '-o', type=click.Path(path_type=Path), help='Save analysis to file')
@click.option('--session-name', help='Session name for batch save')
@click.pass_context
def run_analysis(ctx, data_dir, standard, save, session_name):
    """
    Run analysis on building data.

    Examples:
        ieq analyze run data/building-a
        ieq analyze run data/building-a --standard en16798-1
        ieq analyze run data/building-a --save output/my_analysis.json
    """
    console.print(f"\n[cyan]Running analysis on:[/cyan] {data_dir}\n")

    try:
        # Step 1: Load data
        console.print("[1/3] Loading data...")
        load_use_case = LoadDataUseCase()
        dataset, buildings, levels, rooms = load_use_case.execute(data_dir)
        rooms_list = list(rooms.values())
        buildings_list = list(buildings.values())
        console.print(f"  ✓ Loaded {len(rooms_list)} rooms")

        # Step 2: Load test configurations
        console.print("\n[2/3] Loading test configurations...")
        config_dir = Path("config/standards") / standard
        tests = []

        if config_dir.exists():
            for yaml_file in config_dir.glob("*.yaml"):
                with open(yaml_file) as f:
                    test_config = yaml.safe_load(f)
                    test_config['test_id'] = yaml_file.stem
                    # Map feature to parameter
                    if 'feature' in test_config:
                        test_config['parameter'] = test_config['feature']
                    if 'category' in test_config:
                        test_config['standard'] = standard
                    tests.append(test_config)

        console.print(f"  ✓ Loaded {len(tests)} tests")

        # Step 3: Run analysis
        console.print("\n[3/3] Running analysis...")
        analysis_use_case = RunAnalysisUseCase()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing rooms...", total=len(rooms_list))

            room_analyses = []
            for room in rooms_list:
                try:
                    analysis = analysis_use_case.execute_room_analysis(room, tests)
                    room_analyses.append(analysis)
                except Exception as e:
                    if ctx.obj.get('verbose'):
                        console.print(f"  [yellow]Warning: {room.name} - {e}[/yellow]")
                finally:
                    progress.advance(task)

        # Aggregate building analysis
        building_analysis = None
        if buildings_list and room_analyses:
            building_analysis = analysis_use_case.execute_building_analysis(
                buildings_list[0],
                room_analyses
            )

        console.print("\n[green]✓ Analysis complete![/green]")
        if building_analysis:
            console.print(f"  Compliance: {building_analysis.avg_compliance_rate:.1f}%")
            console.print(f"  Quality: {building_analysis.avg_quality_score:.1f}%")

        # Save if requested
        if save or session_name:
            console.print("\n[cyan]Saving analysis...[/cyan]")
            save_use_case = SaveAnalysisUseCase()

            if session_name:
                saved_paths = save_use_case.execute_save_batch(
                    room_analyses=room_analyses,
                    building_analysis=building_analysis,
                    session_name=session_name,
                )
                console.print(f"[green]✓ Saved session:[/green] {session_name}")
                console.print(f"  Manifest: {saved_paths['manifest']}")
            elif save:
                if building_analysis:
                    path = save_use_case.execute_save_building_analysis(
                        building_analysis,
                        output_path=save
                    )
                    console.print(f"[green]✓ Saved to:[/green] {path}")

        # Store in context for chaining
        ctx.obj['room_analyses'] = room_analyses
        ctx.obj['building_analysis'] = building_analysis

    except Exception as e:
        console.print(f"\n[red]✗ Analysis failed:[/red] {str(e)}")
        if ctx.obj.get('verbose'):
            console.print_exception()
        ctx.exit(1)


@analyze.command(name='list')
@click.pass_context
def list_analyses(ctx):
    """
    List saved analysis sessions.

    Examples:
        ieq analyze list
    """
    from core.application.use_cases.load_analysis import LoadAnalysisUseCase

    console.print("\n[cyan]Saved Analysis Sessions:[/cyan]\n")

    try:
        use_case = LoadAnalysisUseCase()
        sessions = use_case.list_sessions()

        if not sessions:
            console.print("[yellow]No saved sessions found[/yellow]")
            return

        for session in sessions:
            console.print(f"[bold]{session['session_name']}[/bold]")
            console.print(f"  Timestamp: {session['timestamp']}")
            console.print(f"  Rooms: {session['room_analyses_count']}")
            console.print(f"  Building: {'Yes' if session['has_building_analysis'] else 'No'}")
            console.print()

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        ctx.exit(1)
