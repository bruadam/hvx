"""
Start command - Interactive IEQ analysis workflow.
"""

import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.command(name='start')
@click.option('--dataset', '-d', type=click.Path(exists=True, path_type=Path),
              help='Path to existing dataset pickle file (skip loading step)')
@click.option('--analysis', '-a', type=click.Path(exists=True, path_type=Path),
              help='Path to existing analysis directory (skip analysis step)')
def start(dataset: Optional[Path], analysis: Optional[Path]):
    """
    Start a new IEQ analysis project interactively.

    This interactive workflow guides you through the complete analysis pipeline:
    1. Loading building data (or use existing dataset)
    2. Running hierarchical analysis (or use existing analysis)
    3. Exploring results interactively
    4. Generating custom reports

    Examples:

    \b
        # Start from beginning (load data)
        hvx ieq start

        # Start with existing dataset
        hvx ieq start --dataset output/dataset.pkl

        # Start with existing analysis
        hvx ieq start --analysis output/analysis
    """
    from src.core.utils.interactive_workflow import launch_interactive_workflow
    from src.core.models.building_data import BuildingDataset

    console.print(Panel.fit(
        "[bold cyan]HVX - IEQ Analysis[/bold cyan]\n"
        "Interactive end-to-end building performance analysis",
        border_style="cyan"
    ))

    try:
        # Load dataset if provided
        dataset_obj = None
        if dataset:
            console.print(f"\n[bold]Loading dataset from:[/bold] {dataset}")
            dataset_obj = BuildingDataset.load_from_pickle(dataset)
            console.print(f"[green]✓[/green] Loaded {dataset_obj.get_building_count()} buildings\n")

        # Launch workflow
        launch_interactive_workflow(
            auto_mode=True,    
            dataset=dataset_obj,
            dataset_file=dataset,
            analysis_dir=analysis
        )

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Workflow cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        if click.get_current_context().obj and click.get_current_context().obj.get('verbose'):
            console.print_exception()
        raise click.Abort()
