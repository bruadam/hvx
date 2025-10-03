"""
Start command - Complete end-to-end pipeline for HVX analytics.
"""

import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

console = Console()


@click.group(name='start')
def start():
    """Complete end-to-end analysis pipeline from data loading to report generation."""
    pass


@start.command(name='interactive')
@click.option('--dataset', '-d', type=click.Path(exists=True, path_type=Path),
              help='Path to existing dataset pickle file (skip loading step)')
@click.option('--analysis', '-a', type=click.Path(exists=True, path_type=Path),
              help='Path to existing analysis directory (skip analysis step)')
def interactive(dataset: Optional[Path], analysis: Optional[Path]):
    """
    Interactive end-to-end pipeline with guided workflow.

    The pipeline walks you through:
    1. Loading building data (or use existing dataset)
    2. Running hierarchical analysis (or use existing analysis)
    3. Exploring results interactively
    4. Generating custom reports

    Examples:

    \b
        # Start from beginning (load data)
        hvx start interactive

        # Start with existing dataset
        hvx start interactive --dataset output/dataset.pkl

        # Start with existing analysis
        hvx start interactive --analysis output/analysis
    """
    from src.utils.interactive_workflow import launch_interactive_workflow
    from src.models.building_data import BuildingDataset

    console.print(Panel.fit(
        "[bold cyan]HVX Complete Pipeline[/bold cyan]\n"
        "End-to-end building performance analysis",
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


@start.command(name='pipeline')
@click.argument('source_dir', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--output-dir', '-o', type=click.Path(path_type=Path),
              default='output',
              help='Base output directory for all results')
@click.option('--portfolio-name', default='Portfolio',
              help='Name for the portfolio')
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              default='config/tests.yaml',
              help='Path to tests configuration')
@click.option('--test-set', help='Specific test set to use')
@click.option('--report-template', help='Report template to use for generation')
@click.option('--explore/--no-explore', default=False,
              help='Launch interactive explorer after analysis')
@click.option('--generate-report/--no-generate-report', default=True,
              help='Generate report after analysis')
@click.option('--verbose', is_flag=True, help='Show detailed output')
def pipeline(
    source_dir: Path,
    output_dir: Path,
    portfolio_name: str,
    config: Path,
    test_set: Optional[str],
    report_template: Optional[str],
    explore: bool,
    generate_report: bool,
    verbose: bool
):
    """
    Complete automated pipeline: load → analyze → explore → report.

    This command runs the entire analysis pipeline automatically:
    1. Load data from source directory
    2. Run hierarchical analysis with tests
    3. Optionally explore results interactively
    4. Optionally generate report

    Examples:

    \b
        # Basic pipeline
        hvx start pipeline data/samples/sample-extensive-data

        # With custom test set and template
        hvx start pipeline data/ --test-set summer_analysis --report-template exec_summary

        # Custom output directory
        hvx start pipeline data/ --output-dir results/2024-q4

        # Skip report generation, explore instead
        hvx start pipeline data/ --no-generate-report --explore

        # Full automation (no interaction)
        hvx start pipeline data/ --no-explore --report-template standard_building
    """
    from src.services.data_loader_service import create_data_loader
    from src.services.hierarchical_analysis_service import HierarchicalAnalysisService
    from src.services.test_management_service import TestManagementService
    from src.services.report_template_service import ReportTemplateService
    import tempfile
    import os

    # Setup output paths
    dataset_file = output_dir / "dataset.pkl"
    analysis_dir = output_dir / "analysis"
    report_file = output_dir / "report.pdf"

    console.print(Panel.fit(
        "[bold cyan]HVX Complete Pipeline[/bold cyan]\n"
        f"Source: {source_dir}\n"
        f"Output: {output_dir}\n"
        f"Portfolio: {portfolio_name}",
        border_style="cyan"
    ))

    try:
        # ==========================================
        # STEP 1: Load Data
        # ==========================================
        console.print("\n[bold blue]═══ Step 1: Loading Data ═══[/bold blue]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Loading building data...", total=None)

            loader = create_data_loader(
                auto_infer_levels=True,
                auto_infer_room_types=True
            )
            dataset = loader.load_from_directory(source_dir, validate=True)

            # Save dataset
            output_dir.mkdir(parents=True, exist_ok=True)
            dataset.save_to_pickle(dataset_file)

            progress.update(task, completed=True)

        # Display load summary
        console.print(f"[green]✓[/green] Loaded {dataset.get_building_count()} buildings, "
                     f"{dataset.get_total_room_count()} rooms")
        console.print(f"[green]✓[/green] Dataset saved to: [cyan]{dataset_file}[/cyan]")

        if verbose:
            _display_dataset_summary(dataset)

        # ==========================================
        # STEP 2: Run Analysis
        # ==========================================
        console.print("\n[bold blue]═══ Step 2: Running Analysis ═══[/bold blue]\n")

        # Handle test set if specified
        config_to_use = config
        if test_set:
            test_service = TestManagementService(config)
            if not test_service.get_test_set(test_set):
                console.print(f"[red]✗ Test set '{test_set}' not found.[/red]")
                console.print(f"[yellow]Available test sets:[/yellow]")
                for ts in test_service.list_test_sets():
                    console.print(f"  • {ts.name}")
                raise click.Abort()

            # Export test set to temporary file
            fd, temp_path = tempfile.mkstemp(suffix='.yaml')
            os.close(fd)
            temp_config = Path(temp_path)
            test_service.export_test_set_config(test_set, temp_config)
            config_to_use = temp_config

            console.print(f"[cyan]Using test set:[/cyan] {test_set}")

        console.print(f"[cyan]Config:[/cyan] {config_to_use}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Running hierarchical analysis...", total=None)

            analysis_service = HierarchicalAnalysisService(config_path=config_to_use)
            results = analysis_service.analyze_dataset(
                dataset=dataset,
                output_dir=analysis_dir,
                portfolio_name=portfolio_name,
                save_individual_files=True
            )

            progress.update(task, completed=True)

        console.print(f"[green]✓[/green] Analysis complete")
        console.print(f"[green]✓[/green] Results saved to: [cyan]{analysis_dir}[/cyan]")

        # Display analysis summary
        if results.portfolio and verbose:
            _display_analysis_summary(results)
        elif results.portfolio:
            console.print(f"\n[bold]Portfolio Results:[/bold]")
            console.print(f"  Buildings: {results.portfolio.building_count}")
            console.print(f"  Rooms: {results.portfolio.total_room_count}")
            console.print(f"  Avg Compliance: {results.portfolio.avg_compliance_rate:.1f}%")
            console.print(f"  Avg Quality: {results.portfolio.avg_quality_score:.1f}%")

        # ==========================================
        # STEP 3: Explore Results (Optional)
        # ==========================================
        if explore:
            console.print("\n[bold blue]═══ Step 3: Exploring Results ═══[/bold blue]\n")
            console.print("[cyan]Launching interactive analysis explorer...[/cyan]\n")

            try:
                from src.utils.analysis_explorer import launch_analysis_explorer
                launch_analysis_explorer(analysis_dir)
            except KeyboardInterrupt:
                console.print("\n[yellow]Explorer closed[/yellow]")

        # ==========================================
        # STEP 4: Generate Report (Optional)
        # ==========================================
        if generate_report:
            console.print("\n[bold blue]═══ Step 4: Generating Report ═══[/bold blue]\n")

            # Determine template to use
            template_to_use = report_template
            if not template_to_use:
                # Check if standard template exists, create if not
                template_service = ReportTemplateService()
                if not template_service.load_template('standard_building'):
                    console.print("[yellow]Creating standard building template...[/yellow]")
                    template = template_service.create_standard_building_template()
                    template_service.save_template(template)
                template_to_use = 'standard_building'

            console.print(f"[cyan]Using template:[/cyan] {template_to_use}")
            console.print(f"[cyan]Output file:[/cyan] {report_file}")

            # Note: Actual report generation would be implemented here
            # For now, provide guidance
            console.print("\n[yellow]Note: Report generation integration pending[/yellow]")
            console.print("[dim]Use the following command to generate report:[/dim]")
            console.print(f"[dim]  hvx reports generate --analysis-dir {analysis_dir} "
                        f"--template {template_to_use} --output {report_file}[/dim]")

        # ==========================================
        # Pipeline Complete
        # ==========================================
        console.print("\n" + "─" * 60)
        console.print("[bold green]✓ Pipeline Complete![/bold green]")
        console.print("─" * 60)

        # Summary table
        summary_table = Table(box=box.SIMPLE, show_header=False)
        summary_table.add_column("", style="cyan", width=20)
        summary_table.add_column("", style="white")

        summary_table.add_row("Dataset", str(dataset_file))
        summary_table.add_row("Analysis", str(analysis_dir))
        if generate_report:
            summary_table.add_row("Report", str(report_file))
        summary_table.add_row("Buildings", str(results.portfolio.building_count if results.portfolio else "N/A"))
        summary_table.add_row("Rooms", str(results.portfolio.total_room_count if results.portfolio else "N/A"))
        if results.portfolio:
            summary_table.add_row("Avg Compliance", f"{results.portfolio.avg_compliance_rate:.1f}%")

        console.print()
        console.print(summary_table)

        # Next steps
        console.print("\n[bold]Next Steps:[/bold]")
        console.print(f"  • Explore results: [cyan]hvx analyze explore {analysis_dir}[/cyan]")
        console.print(f"  • View summary: [cyan]hvx analyze summary {analysis_dir}[/cyan]")
        console.print(f"  • Generate report: [cyan]hvx reports generate --analysis-dir {analysis_dir} "
                     f"--template {template_to_use or 'standard_building'}[/cyan]")
        console.print()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Pipeline cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]✗ Pipeline Error:[/bold red] {str(e)}\n")
        if verbose:
            console.print_exception()
        raise click.Abort()


@start.command(name='quick')
@click.argument('source_dir', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--output-dir', '-o', type=click.Path(path_type=Path),
              default='output',
              help='Base output directory')
def quick(source_dir: Path, output_dir: Path):
    """
    Quick pipeline with sensible defaults.

    Runs: load → analyze → summary display

    Examples:

    \b
        # Quick analysis
        hvx start quick data/samples/sample-extensive-data

        # Custom output
        hvx start quick data/ --output-dir results/
    """
    from src.services.data_loader_service import create_data_loader
    from src.services.hierarchical_analysis_service import HierarchicalAnalysisService

    console.print("\n[bold cyan]Quick Analysis Pipeline[/bold cyan]\n")

    dataset_file = output_dir / "dataset.pkl"
    analysis_dir = output_dir / "analysis"

    try:
        # Load
        console.print("[bold]Loading data...[/bold]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("", total=None)
            loader = create_data_loader(auto_infer_levels=True, auto_infer_room_types=True)
            dataset = loader.load_from_directory(source_dir, validate=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            dataset.save_to_pickle(dataset_file)
            progress.update(task, completed=True)

        console.print(f"[green]✓[/green] Loaded {dataset.get_building_count()} buildings, "
                     f"{dataset.get_total_room_count()} rooms")

        # Analyze
        console.print("\n[bold]Running analysis...[/bold]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("", total=None)
            service = HierarchicalAnalysisService()
            results = service.analyze_dataset(
                dataset=dataset,
                output_dir=analysis_dir,
                portfolio_name='Portfolio',
                save_individual_files=True
            )
            progress.update(task, completed=True)

        console.print(f"[green]✓[/green] Analysis complete")

        # Summary
        if results.portfolio:
            console.print("\n[bold cyan]Results:[/bold cyan]")
            console.print(f"  Buildings: {results.portfolio.building_count}")
            console.print(f"  Rooms: {results.portfolio.total_room_count}")
            console.print(f"  Avg Compliance: {results.portfolio.avg_compliance_rate:.1f}%")
            console.print(f"  Avg Quality: {results.portfolio.avg_quality_score:.1f}%")

        console.print(f"\n[bold green]✓ Complete![/bold green]")
        console.print(f"Results in: [cyan]{output_dir}[/cyan]")
        console.print(f"\nExplore: [cyan]hvx analyze explore {analysis_dir}[/cyan]\n")

    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {str(e)}\n")
        raise click.Abort()


# ==========================================
# Helper Functions
# ==========================================

def _display_dataset_summary(dataset):
    """Display detailed dataset summary."""
    from src.models.building_data import BuildingDataset

    console.print("\n[bold]Dataset Summary:[/bold]")

    table = Table(box=box.SIMPLE)
    table.add_column("Building", style="cyan")
    table.add_column("Levels", justify="right")
    table.add_column("Rooms", justify="right")
    table.add_column("Parameters", style="yellow")

    for building in dataset.buildings:
        params = set()
        for room in building.rooms:
            if room.sensor_data:
                params.update(room.sensor_data.keys())

        table.add_row(
            building.building_id,
            str(len(set(room.level for room in building.rooms))),
            str(len(building.rooms)),
            ", ".join(sorted(params))
        )

    console.print(table)


def _display_analysis_summary(results):
    """Display detailed analysis summary."""
    console.print("\n[bold]Analysis Summary:[/bold]\n")

    if results.portfolio:
        table = Table(box=box.ROUNDED, title="Portfolio Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Buildings", str(results.portfolio.building_count))
        table.add_row("Total Levels", str(results.portfolio.total_level_count))
        table.add_row("Total Rooms", str(results.portfolio.total_room_count))
        table.add_row("Avg Compliance", f"{results.portfolio.avg_compliance_rate:.1f}%")
        table.add_row("Avg Quality", f"{results.portfolio.avg_quality_score:.1f}%")

        console.print(table)

        # Top issues
        if results.portfolio.common_issues:
            console.print("\n[bold yellow]Common Issues:[/bold yellow]")
            for item in results.portfolio.common_issues[:5]:
                console.print(f"  • {item['issue']} (occurs in {item['occurrence_count']} buildings)")

    # Building summary
    if results.buildings:
        console.print(f"\n[bold]Buildings:[/bold] {len(results.buildings)}")

        building_table = Table(box=box.SIMPLE)
        building_table.add_column("Building", style="cyan")
        building_table.add_column("Rooms", justify="right")
        building_table.add_column("Compliance", justify="right")
        building_table.add_column("Quality", justify="right")

        for building_id, building in sorted(results.buildings.items())[:10]:
            building_table.add_row(
                building.building_name,
                str(building.room_count),
                f"{building.avg_compliance_rate:.1f}%",
                f"{building.avg_quality_score:.1f}%"
            )

        console.print(building_table)

        if len(results.buildings) > 10:
            console.print(f"[dim]... and {len(results.buildings) - 10} more buildings[/dim]")
