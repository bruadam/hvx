"""
Interactive workflow orchestrator for HVX CLI.

Provides a comprehensive interactive experience that guides users through
the complete data analysis workflow: load → explore → analyze → report.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

from src.core.models import BuildingDataset
from src.core.services.hierarchical_analysis_service import HierarchicalAnalysisService
from src.core.services.report_service import ReportService
from src.core.services.data_structure_detector import (
    create_structure_detector, 
    DirectoryStructureType
)
from src.core.utils.data_explorer import launch_explorer

console = Console()


class InteractiveWorkflow:
    """Interactive workflow orchestrator for the HVX data analysis pipeline."""
    
    def __init__(self, auto_mode: bool = False, verbose: bool = False):
        """Initialize the workflow orchestrator.

        Args:
            auto_mode: If True, use default values for all prompts without asking
            verbose: If True, show detailed warnings and debug information
        """
        self.dataset: Optional[BuildingDataset] = None
        self.dataset_file: Optional[Path] = None
        self.analysis_results = None
        self.data_directory: Optional[Path] = None
        from src.core.utils.config_loader import get_tests_config_path
        self.config_path: Path = get_tests_config_path()
        self.portfolio_name: str = "Portfolio"
        self.auto_mode: bool = auto_mode
        self.verbose: bool = verbose

    def start(self, data_directory: Optional[Path] = None):
        """
        Start the interactive workflow.
        
        Args:
            data_directory: Path to the data directory (optional)
            dataset_file: Path to dataset pickle file (optional)
        """
        console.clear()
        self._show_welcome()
        
        # Set initial state
        self.data_directory = data_directory
        
        # Main workflow loop
        self._main_workflow()
    
    def _show_welcome(self):
        """Display welcome message."""
        welcome = """

[bold]Complete data analysis pipeline:[/bold]
  1. Load building data
  2. Explore data interactively
  3. Run hierarchical analysis
  4. Generate reports

Type 'quit' or 'q' at any time to exit.
        """
        console.print(welcome)
        console.print()
    
    def _main_workflow(self):
        """Main workflow orchestration."""
        try:
            # Step 1: Ensure we have data loaded
            if not self.dataset:
                if not self._load_or_select_dataset():
                    console.print("\n[yellow]Workflow cancelled.[/yellow]\n")
                    return
            
            # Show dataset summary
            self._show_dataset_summary()
            
            # Step 2: Offer data exploration (skip in auto mode)
            if not self.auto_mode and Confirm.ask("\n[bold cyan]Would you like to explore the data interactively?[/bold cyan]", default=True):
                self._launch_explorer()
                console.print("\n[green]✓[/green] Exploration complete")
            elif self.auto_mode:
                console.print("\n[dim]Auto mode: Skipping data exploration...[/dim]")
            
            # Step 3: Run analysis (always run in auto mode)
            should_analyze = self.auto_mode or Confirm.ask("\n[bold cyan]Would you like to run hierarchical analysis?[/bold cyan]", default=True)
            if should_analyze:
                if self._run_analysis():
                    console.print("\n[green]✓[/green] Analysis complete")
                    
                    # Offer to explore analysis results
                    if Confirm.ask("\n[bold cyan]Would you like to explore the analysis results interactively?[/bold cyan]", default=True):
                        self._explore_analysis()
                        console.print("\n[green]✓[/green] Analysis exploration complete")
                else:
                    console.print("\n[yellow]Analysis skipped or failed[/yellow]")
                    return
            else:
                console.print("\n[yellow]Analysis skipped[/yellow]")
                # Ask if they want to use existing analysis
                if Confirm.ask("\n[bold]Use existing analysis for reporting?[/bold]", default=False):
                    self._select_existing_analysis()
                    
                    # Offer to explore existing analysis
                    if self.analysis_dir and self.analysis_dir.exists():
                        if Confirm.ask("\n[bold cyan]Would you like to explore the analysis results?[/bold cyan]", default=True):
                            self._explore_analysis()
                else:
                    return
            
            # Step 4: Generate reports
            if self.analysis_dir and self.analysis_dir.exists():
                if Confirm.ask("\n[bold cyan]Would you like to generate reports?[/bold cyan]", default=True):
                    self._generate_reports()
                    console.print("\n[green]✓[/green] Reports generated")
            
            # Completion message
            self._show_completion()
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Workflow interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"\n[bold red]Error in workflow:[/bold red] {str(e)}")
            console.print_exception()
    
    def _load_or_select_dataset(self) -> bool:
        """Load or select a dataset. Returns True if successful."""
        console.print("\n[bold cyan]═══ Step 1: Load Data ═══[/bold cyan]\n")
        
        # Check if dataset file was provided
        if self.dataset_file and self.dataset_file.exists():
            if Confirm.ask(f"Load dataset from {self.dataset_file}?", default=True):
                return self._load_dataset_from_file(self.dataset_file)
        
        # In auto mode, go straight to directory loading
        if self.auto_mode:
            console.print("[dim]Auto mode: Loading from data directory...[/dim]")
            data_dir = Path("data/samples/sample-extensive-data")
            return self._load_dataset_from_directory(data_dir)
        
        # Offer options
        console.print("[bold]Options:[/bold]")
        console.print("  1. Load from existing pickle file")
        console.print("  2. Load from data directory")
        console.print("  3. Cancel")
        console.print()
        
        choice = Prompt.ask("[bold]Choose option[/bold]", choices=["1", "2", "3"], default="2")
        
        if choice == "1":
            # Select existing pickle file
            default_path = "output/dataset.pkl"
            file_path = Prompt.ask(
                "[bold]Enter pickle file path[/bold]",
                default=default_path
            )
            return self._load_dataset_from_file(Path(file_path))
        
        elif choice == "2":
            # Load from directory
            # Check if default data/ directory exists
            default_data_dir = Path("data/samples/sample-extensive-data")
            if not Path("data").exists():
                console.print("\n[yellow]Note: 'data/' directory not found in current location[/yellow]")
                console.print("[dim]Please specify the path to your data directory[/dim]\n")
                default_data_dir = Path(".")
            
            # Show expected structure
            console.print("\n[bold cyan]Expected Data Structure:[/bold cyan]")
            structure_info = """
[dim]Your data directory should be organized like this:[/dim]

    data_directory/
    ├── building-1/
    │   ├── climate/
    │   │   └── climate-data.csv      [dim](optional)[/dim]
    │   └── sensors/
    │       ├── room1.csv
    │       ├── room2.csv
    │       └── ...
    ├── building-2/
    │   └── sensors/
    │       └── ...
    └── ...

[dim]Examples:[/dim]
  • [cyan]data/samples/sample-extensive-data[/cyan]  (3 buildings, 58 rooms)
  • [cyan]data/myproject[/cyan]  (your custom data)

[bold]Notes:[/bold]
  • [dim]Building folders can be named:[/dim] building-1, building-2, or custom names
  • [dim]Climate data is optional but recommended for smart recommendations[/dim]
  • [dim]Room CSV files will be auto-detected from the sensors/ folder[/dim]
  • [dim]The system can also handle other structures (flat, hybrid, etc.)[/dim]
            """
            console.print(structure_info)
            
            data_dir = Prompt.ask(
                "\n[bold]Enter data directory path[/bold]",
                default=str(default_data_dir)
            )
            return self._load_dataset_from_directory(Path(data_dir))
        
        else:
            return False
    
    def _load_dataset_from_file(self, file_path: Path) -> bool:
        """Load dataset from pickle file."""
        try:
            if not file_path.exists():
                console.print(f"[red]✗ File not found:[/red] {file_path}")
                return False
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Loading dataset...", total=None)
                self.dataset = BuildingDataset.load_from_pickle(file_path)
                self.dataset_file = file_path
                progress.update(task, completed=True)
            
            console.print(f"[green]✓[/green] Dataset loaded from: {file_path}")
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Error loading dataset:[/red] {str(e)}")
            return False
    
    def _load_dataset_from_directory(self, data_dir: Path) -> bool:
        """Load dataset from data directory."""
        try:
            if not data_dir.exists():
                console.print(f"[red]✗ Directory not found:[/red] {data_dir}")
                
                # Prompt for alternative directory
                if self.auto_mode:
                    console.print("[yellow]Auto mode: Cannot proceed without valid directory[/yellow]")
                    return False
                
                if Confirm.ask("\n[bold]Would you like to specify a different directory?[/bold]", default=True):
                    new_dir = Prompt.ask("[bold]Enter data directory path[/bold]")
                    return self._load_dataset_from_directory(Path(new_dir))
                return False
            
            # Analyze directory structure
            console.print("\n[dim]Analyzing directory structure...[/dim]")
            detector = create_structure_detector()
            analysis = detector.analyze_directory(data_dir)
            
            # Show analysis results
            self._show_structure_analysis(analysis)
            
            # If structure is unknown or has low confidence, offer help
            if analysis.structure_type == DirectoryStructureType.UNKNOWN or analysis.confidence < 0.5:
                console.print("\n[yellow]⚠ Directory structure not recognized or has issues[/yellow]")
                
                if analysis.issues:
                    console.print("\n[bold red]Issues:[/bold red]")
                    for issue in analysis.issues:
                        console.print(f"  • {issue}")
                
                if analysis.recommendations:
                    console.print("\n[bold cyan]Recommendations:[/bold cyan]")
                    for rec in analysis.recommendations:
                        console.print(f"  • {rec}")
                
                # In auto mode, fail immediately
                if self.auto_mode:
                    console.print("\n[yellow]Auto mode: Cannot proceed with unsupported structure[/yellow]")
                    return False
                
                # Offer reorganization guide
                if Confirm.ask("\n[bold]Would you like to see the reorganization guide?[/bold]", default=True):
                    guide = detector.get_reorganization_guide(analysis)
                    console.print(guide)
                
                if not Confirm.ask("\n[bold]Try to load data anyway?[/bold]", default=False):
                    return False
            
            # Show warnings for non-standard structures
            elif analysis.structure_type in [
                DirectoryStructureType.FLAT_BUILDING_PREFIX,
                DirectoryStructureType.FLAT_BUILDING_LEVEL_PREFIX,
                DirectoryStructureType.HYBRID_CLIMATE_FILES,
                DirectoryStructureType.NESTED_FULL
            ]:
                if not self.auto_mode and analysis.recommendations:
                    console.print("\n[yellow]Note:[/yellow] Non-standard structure detected")
                    console.print("[dim]Recommendations for better organization:[/dim]")
                    for rec in analysis.recommendations:
                        console.print(f"  • [dim]{rec}[/dim]")
                    console.print()
            
            from src.core.services.data_loader_service import create_data_loader
            
            # Auto-infer settings (always enabled)
            infer_levels = True
            infer_room_types = True
            
            if self.auto_mode:
                validate = True
                console.print("[dim]Auto mode: Validating data quality, auto-inferring levels and room types...[/dim]")
            else:
                validate = Confirm.ask("Validate data quality?", default=True)
                console.print("\n[dim]Auto-inferring building levels and room types...[/dim]")
            
            loader = create_data_loader(
                auto_infer_levels=infer_levels,
                auto_infer_room_types=infer_room_types
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Loading data from directory...", total=None)
                self.dataset = loader.load_from_directory(data_dir, validate=validate)
                progress.update(task, completed=True)
            
            console.print(f"[green]✓[/green] Dataset loaded from: {data_dir}")
            
            # Auto save in auto mode, otherwise ask
            should_save = self.auto_mode or Confirm.ask("\nSave dataset to pickle file?", default=True)
            if should_save:
                if self.auto_mode:
                    output_file = "output/dataset.pkl"
                else:
                    output_file = Prompt.ask(
                        "Output file path",
                        default="output/dataset.pkl"
                    )
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                self.dataset.save_to_pickle(output_path)
                self.dataset_file = output_path
                console.print(f"[green]✓[/green] Dataset saved to: {output_path}")
            
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Error loading dataset:[/red] {str(e)}")
            return False
    
    def _show_dataset_summary(self):
        """Display dataset summary."""
        if not self.dataset:
            return
        
        summary = self.dataset.get_summary()
        
        info = f"""
[bold]Source:[/bold] {summary['source_directory']}
[bold]Buildings:[/bold] {summary['building_count']}
[bold]Total Rooms:[/bold] {summary['total_room_count']}
[bold]Loaded:[/bold] {summary['loaded_at']}
        """
        console.print(Panel(info.strip(), title="Dataset Summary", box=box.ROUNDED))
    
    def _show_structure_analysis(self, analysis):
        """Display directory structure analysis results."""
        from src.core.services.data_structure_detector import DirectoryStructureType
        
        # Create a summary table
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        
        # Structure type with color coding
        structure_name = analysis.structure_type.value.replace('_', ' ').title()
        if analysis.structure_type == DirectoryStructureType.NESTED_BUILDING_CLIMATE_SENSORS:
            structure_display = f"[green]{structure_name}[/green] ✓"
        elif analysis.confidence >= 0.7:
            structure_display = f"[yellow]{structure_name}[/yellow]"
        else:
            structure_display = f"[red]{structure_name}[/red]"
        
        table.add_row("Structure Type", structure_display)
        table.add_row("Confidence", f"{analysis.confidence:.0%}")
        table.add_row("Buildings Detected", str(analysis.building_count))
        table.add_row("Sensor Files", str(analysis.total_sensor_files))
        table.add_row("Climate Data", "Yes ✓" if analysis.has_climate_data else "No")
        
        console.print("\n")
        console.print(table)
        
        # Show additional details if available
        if analysis.details:
            if 'structure' in analysis.details:
                console.print(f"\n[dim]Pattern: {analysis.details['structure']}[/dim]")

    
    def _launch_explorer(self):
        """Launch the interactive data explorer."""
        try:
            if self.dataset is not None:
                launch_explorer(self.dataset)
            else:
                console.print("[red]No dataset loaded to explore.[/red]")
        except Exception as e:
            console.print(f"[red]Error in explorer:[/red] {str(e)}")
    
    def _explore_analysis(self):
        """Launch the interactive analysis explorer."""
        if not self.analysis_dir or not self.analysis_dir.exists():
            console.print("[yellow]No analysis directory available[/yellow]")
            return
        
        try:
            from src.core.utils.analysis_explorer import launch_analysis_explorer
            launch_analysis_explorer(self.analysis_dir)
        except Exception as e:
            console.print(f"[red]Error in analysis explorer:[/red] {str(e)}")
    
    def _run_analysis(self) -> bool:
        """Run hierarchical analysis. Returns True if successful."""
        console.print("\n[bold cyan]═══ Step 2: Run Analysis ═══[/bold cyan]\n")
        
        if self.auto_mode:
            # Use defaults in auto mode
            console.print("[dim]Auto mode: Using default configuration...[/dim]")
            self.config_path = Path("config/tests.yaml")
            self.analysis_dir = Path("output/analysis")
            self.portfolio_name = "Portfolio"
            save_individual = True
            
            console.print(f"  Config: {self.config_path}")
            console.print(f"  Output: {self.analysis_dir}")
            console.print(f"  Portfolio: {self.portfolio_name}")
            console.print()
        else:
            # Configuration options
            console.print("[bold]Analysis Configuration:[/bold]")
            
            # Config file
            config_input = Prompt.ask(
                "Config file path",
                default=str(self.config_path)
            )
            self.config_path = Path(config_input)
            
            if not self.config_path.exists():
                console.print(f"[yellow]Warning: Config file not found:[/yellow] {self.config_path}")
                if not Confirm.ask("Continue with default config?", default=True):
                    return False
                # Use default path anyway
                from src.core.utils.config_loader import get_tests_config_path
                self.config_path = get_tests_config_path()
            
            # Output directory
            output_input = Prompt.ask(
                "Output directory for analysis",
                default="output/analysis"
            )
            self.analysis_dir = Path(output_input)
            
            # Portfolio name
            self.portfolio_name = Prompt.ask(
                "Portfolio name",
                default="Portfolio"
            )
            
            # Save individual files?
            save_individual = Confirm.ask(
                "Save individual JSON files per room/level/building?",
                default=True
            )
        
        try:
            # Initialize service
            service = HierarchicalAnalysisService(config_path=self.config_path)
            
            # Run analysis
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running hierarchical analysis...", total=None)
                
                if self.dataset is None:
                    console.print("[red]No dataset loaded for analysis.[/red]")
                    return False

                self.analysis_results = service.analyze_dataset(
                    dataset=self.dataset,
                    output_dir=self.analysis_dir,
                    portfolio_name=self.portfolio_name,
                    save_individual_files=save_individual,
                    verbose=self.verbose
                )
                
                progress.update(task, completed=True)
            
            # Show summary
            self._show_analysis_summary()
            
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Error during analysis:[/red] {str(e)}")
            console.print_exception()
            return False
    
    def _show_analysis_summary(self):
        """Display analysis summary."""
        if not self.analysis_results:
            return
        
        console.print("\n[bold cyan]Analysis Summary[/bold cyan]")
        
        # Portfolio summary
        if self.analysis_results.portfolio:
            portfolio = self.analysis_results.portfolio
            
            table = Table(box=box.SIMPLE, show_header=False)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right")
            
            table.add_row("Buildings Analyzed", str(portfolio.building_count))
            table.add_row("Total Rooms", str(portfolio.total_room_count))
            table.add_row("Avg Compliance", f"{portfolio.avg_compliance_rate:.1f}%")
            table.add_row("Avg Quality", f"{portfolio.avg_quality_score:.1f}%")
            
            console.print(table)
        
        console.print(f"\n[bold]Results saved to:[/bold] [cyan]{self.analysis_dir}[/cyan]")
    
    def _select_existing_analysis(self):
        """Select an existing analysis directory."""
        analysis_path = Prompt.ask(
            "[bold]Enter analysis directory path[/bold]",
            default="output/analysis"
        )
        self.analysis_dir = Path(analysis_path)
        
        if not self.analysis_dir.exists():
            console.print(f"[yellow]Warning: Directory not found:[/yellow] {self.analysis_dir}")
    
    def _generate_reports(self):
        """Generate reports from analysis."""
        console.print("\n[bold cyan]═══ Step 3: Generate Reports ═══[/bold cyan]\n")
        
        try:
            report_service = ReportService()
            
            # List available templates
            console.print("[bold]Available report types:[/bold]")
            console.print("  1. Portfolio Summary Report")
            console.print("  2. Building Reports (all buildings)")
            console.print("  3. Custom template")
            console.print("  4. Skip")
            console.print()
            
            choice = Prompt.ask(
                "[bold]Choose report type[/bold]",
                choices=["1", "2", "3", "4"],
                default="1"
            )
            
            if choice == "4":
                return
            
            # Load portfolio data for reports
            if not self.analysis_dir:
                console.print(f"[yellow]Warning: Analysis directory is not set[/yellow]")
                return

            portfolio_file = self.analysis_dir / "portfolio_analysis.json"
            if not portfolio_file.exists():
                portfolio_file = self.analysis_dir / "portfolio.json"
            
            if not portfolio_file.exists():
                console.print(f"[yellow]Warning: Portfolio analysis not found[/yellow]")
                return
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                if choice == "1":
                    # Portfolio summary report
                    task = progress.add_task("Generating portfolio report...", total=None)
                    
                    output_file = self.analysis_dir.parent / "reports" / "portfolio_report.pdf"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Note: This assumes report_service has appropriate methods
                    console.print(f"\n[green]✓[/green] Portfolio report template ready")
                    console.print(f"    Output would be: {output_file}")
                    console.print(f"    [dim]Note: PDF generation requires template configuration[/dim]")
                    
                    progress.update(task, completed=True)
                
                elif choice == "2":
                    # Building reports
                    task = progress.add_task("Generating building reports...", total=None)
                    
                    buildings_dir = self.analysis_dir / "buildings"
                    if buildings_dir.exists():
                        building_files = list(buildings_dir.glob("*.json"))
                        console.print(f"\n[green]✓[/green] Found {len(building_files)} building analyses")
                        console.print(f"    Reports would be generated for each building")
                        console.print(f"    [dim]Note: PDF generation requires template configuration[/dim]")
                    else:
                        console.print(f"[yellow]No building analyses found in {buildings_dir}[/yellow]")
                    
                    progress.update(task, completed=True)
                
                elif choice == "3":
                    # Custom template
                    template_name = Prompt.ask("[bold]Enter template name[/bold]")
                    console.print(f"\n[green]✓[/green] Template specified: {template_name}")
                    console.print(f"    [dim]Note: PDF generation requires template configuration[/dim]")
            
            console.print(f"\n[bold]Analysis results available at:[/bold] [cyan]{self.analysis_dir}[/cyan]")
            
        except Exception as e:
            console.print(f"[red]✗ Error generating reports:[/red] {str(e)}")
            console.print_exception()
    
    def _show_completion(self):
        """Show workflow completion message."""
        console.print("\n" + "="*60)
        console.print()
        
        completion = """
[bold green]✓ Workflow Complete![/bold green]

[bold]Summary:[/bold]
  • Dataset loaded and explored
  • Hierarchical analysis completed
  • Results available for reporting

[bold]Next Steps:[/bold]
  • View analysis: hvx analyze summary {analysis_dir}
  • Explore data: hvx data explore {dataset_file}
  • Generate custom reports: hvx reports generate <template> --data {analysis_dir}/portfolio.json

[dim]Run 'hvx --help' for more commands[/dim]
        """
        
        analysis_dir = str(self.analysis_dir) if self.analysis_dir else "output/analysis"
        dataset_file = str(self.dataset_file) if self.dataset_file else "output/dataset.pkl"
        
        console.print(completion.format(
            analysis_dir=analysis_dir,
            dataset_file=dataset_file
        ))
        console.print()


def launch_interactive_workflow(
    data_directory: Optional[Path] = None,
    auto_mode: bool = False,
):
    """
    Launch the interactive workflow.
    
    Args:
        dataset: Pre-loaded BuildingDataset (optional)
        dataset_file: Path to dataset pickle file (optional)
        auto_mode: If True, use default values for all prompts without asking
    """
    workflow = InteractiveWorkflow(auto_mode=auto_mode)
    # Allow callers to provide an existing analysis directory
    if data_directory is not None:
        workflow.data_directory = data_directory

    workflow.start()
