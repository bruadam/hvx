"""
Workflow CLI commands for HVX.
"""

import click
from pathlib import Path
from typing import Optional
from rich.console import Console

from src.utils.interactive_workflow import launch_interactive_workflow
from src.models.building_data import BuildingDataset

console = Console()


@click.group(name='workflow')
def workflow():
    """Interactive workflow commands for complete data analysis pipeline."""
    pass


@workflow.command(name='start')
@click.option('--dataset', '-d', type=click.Path(exists=True, path_type=Path),
              help='Path to existing dataset pickle file')
def start_workflow(dataset: Optional[Path]):
    """
    Start the interactive workflow for data analysis.
    
    The workflow guides you through:
    1. Loading building data (if not provided)
    2. Exploring data interactively
    3. Running hierarchical analysis
    4. Generating reports
    
    Examples:
    
    \b
        # Start workflow from scratch
        hvx workflow start
        
        # Start workflow with existing dataset
        hvx workflow start --dataset output/dataset.pkl
    """
    
    console.print("\n[bold cyan]Starting HVX Interactive Workflow[/bold cyan]\n")
    
    try:
        # Load dataset if provided
        dataset_obj = None
        if dataset:
            console.print(f"Loading dataset from: {dataset}")
            dataset_obj = BuildingDataset.load_from_pickle(dataset)
        
        # Launch workflow
        launch_interactive_workflow(dataset=dataset_obj, dataset_file=dataset)
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        raise click.Abort()


@workflow.command(name='quick')
@click.argument('source_dir', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path),
              default='output/dataset.pkl',
              help='Output file for dataset')
@click.option('--analysis-output', type=click.Path(path_type=Path),
              default='output/analysis',
              help='Output directory for analysis')
@click.option('--portfolio-name', default='Portfolio',
              help='Name for the portfolio')
def quick_workflow(source_dir: Path, output: Path, analysis_output: Path, portfolio_name: str):
    """
    Quick non-interactive workflow: load → analyze → report.
    
    Runs the complete pipeline automatically without user interaction.
    Useful for scripting and automation.
    
    Examples:
    
    \b
        # Quick analysis of sample data
        hvx workflow quick data/samples/sample-extensive-data
        
        # With custom output paths
        hvx workflow quick data/my-data --output data.pkl --analysis-output results/
    """
    
    from src.services.data_loader_service import create_data_loader
    from src.services.hierarchical_analysis_service import HierarchicalAnalysisService
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    console.print("\n[bold cyan]Running Quick Workflow[/bold cyan]\n")
    
    try:
        # Step 1: Load data
        console.print("[bold]Step 1: Loading data...[/bold]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading...", total=None)
            
            loader = create_data_loader(
                auto_infer_levels=True,
                auto_infer_room_types=True
            )
            dataset = loader.load_from_directory(source_dir, validate=True)
            
            # Save dataset
            output.parent.mkdir(parents=True, exist_ok=True)
            dataset.save_to_pickle(output)
            
            progress.update(task, completed=True)
        
        console.print(f"[green]✓[/green] Loaded {dataset.get_building_count()} buildings, "
                     f"{dataset.get_total_room_count()} rooms")
        console.print(f"[green]✓[/green] Saved to: {output}")
        
        # Step 2: Run analysis
        console.print("\n[bold]Step 2: Running hierarchical analysis...[/bold]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing...", total=None)
            
            service = HierarchicalAnalysisService()
            results = service.analyze_dataset(
                dataset=dataset,
                output_dir=analysis_output,
                portfolio_name=portfolio_name,
                save_individual_files=True
            )
            
            progress.update(task, completed=True)
        
        console.print(f"[green]✓[/green] Analysis complete")
        console.print(f"[green]✓[/green] Results saved to: {analysis_output}")
        
        # Show summary
        if results.portfolio:
            console.print("\n[bold cyan]Portfolio Summary:[/bold cyan]")
            console.print(f"  Buildings: {results.portfolio.building_count}")
            console.print(f"  Rooms: {results.portfolio.total_room_count}")
            console.print(f"  Avg Compliance: {results.portfolio.avg_compliance_rate:.1f}%")
            console.print(f"  Avg Quality: {results.portfolio.avg_quality_score:.1f}%")
        
        console.print("\n[bold green]✓ Quick workflow complete![/bold green]")
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  • View results: hvx analyze summary {analysis_output}")
        console.print(f"  • Explore data: hvx data explore {output}")
        console.print(f"  • Generate reports: hvx reports generate <template> --data {analysis_output}/portfolio.json")
        console.print()
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        console.print_exception()
        raise click.Abort()
