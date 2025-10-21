"""Interactive workflow orchestrator for IEQ Analytics CLI."""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml
import json

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint

from core.cli.ui.components.panels import (
    create_welcome_panel,
    create_step_panel,
    create_success_panel,
    create_error_panel,
    create_completion_panel,
    create_help_panel,
)
from core.cli.ui.components.tables import (
    create_room_analysis_table,
    create_building_summary_table,
    create_test_results_table,
    create_standards_table,
)
from core.cli.ui.components.progress import ProgressTracker

# Import clean architecture components
from core.infrastructure.data_loaders.dataset_builder import DatasetBuilder
from core.analytics.engine.analysis_engine import AnalysisEngine
from core.analytics.aggregators.building_aggregator import BuildingAggregator
from core.reporting.report_generator import ReportGenerator
from core.domain.models.room import Room
from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.building_analysis import BuildingAnalysis

console = Console()


class InteractiveWorkflow:
    """Interactive workflow orchestrator for IEQ analysis."""

    def __init__(self, auto_mode: bool = False, verbose: bool = False):
        """
        Initialize the workflow orchestrator.

        Args:
            auto_mode: If True, use default values without prompting
            verbose: If True, show detailed output
        """
        self.auto_mode = auto_mode
        self.verbose = verbose
        self.data_directory: Optional[Path] = None
        self.progress = ProgressTracker()

        # Initialize clean architecture components
        self.dataset_builder = DatasetBuilder()
        self.analysis_engine = AnalysisEngine()
        self.building_aggregator = BuildingAggregator()
        self.report_generator = ReportGenerator(self.analysis_engine)

        # Workflow state
        self.dataset: Optional[Any] = None
        self.buildings: Dict[str, Any] = {}
        self.levels: Dict[str, Any] = {}
        self.rooms: List[Room] = []
        self.selected_standards: List[str] = []
        self.selected_tests: List[dict] = []
        self.room_analyses: List[RoomAnalysis] = []
        self.building_analysis: Optional[BuildingAnalysis] = None
        self.report_path: Optional[Path] = None
        self.export_path: Optional[Path] = None

        # Initialize workflow steps
        self._initialize_steps()

    def _initialize_steps(self):
        """Initialize workflow steps."""
        self.progress.add_step(1, "Load Building Data")
        self.progress.add_step(2, "Select Standards")
        self.progress.add_step(3, "Configure Tests")
        self.progress.add_step(4, "Run Analysis")
        self.progress.add_step(5, "Explore Results")
        self.progress.add_step(6, "Generate Reports")
        self.progress.add_step(7, "Export Data")

    def run(self):
        """Run the interactive workflow."""
        console.clear()
        console.print(create_welcome_panel())
        console.print()

        if self.auto_mode:
            console.print("[yellow]Running in auto mode - using defaults[/yellow]\n")

        try:
            # Step 1: Load Data
            if not self._step_load_data():
                self._exit_workflow("data loading")
                return

            # Step 2: Select Standards
            if not self._step_select_standards():
                self._exit_workflow("standard selection")
                return

            # Step 3: Configure Tests
            if not self._step_configure_tests():
                self._exit_workflow("test configuration")
                return

            # Step 4: Run Analysis
            if not self._step_run_analysis():
                self._exit_workflow("analysis")
                return

            # Step 5: Explore Results (skip in auto mode)
            if not self.auto_mode:
                self._step_explore_results()

            # Step 6: Generate Reports
            if not self.auto_mode or Confirm.ask("\n[cyan]Generate report?[/cyan]", default=True):
                self._step_generate_reports()

            # Step 7: Export Data
            if not self.auto_mode:
                if Confirm.ask("\n[cyan]Export analysis data?[/cyan]", default=False):
                    self._step_export_data()

            # Show completion
            self._show_completion()

        except KeyboardInterrupt:
            console.print("\n\n[yellow]⚠ Workflow cancelled by user[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(create_error_panel(
                str(e),
                "Check your input and try again. Use --verbose for more details."
            ))
            if self.verbose:
                console.print_exception()
            sys.exit(1)

    # ========================================================================
    # STEP 1: Load Data
    # ========================================================================

    def _step_load_data(self) -> bool:
        """Step 1: Load building data."""
        self.progress.start_step(1)
        console.clear()
        console.print(self.progress.render())
        console.print()
        console.print(create_step_panel(1, "Load Building Data"))
        console.print()

        # Get data directory
        if not self.data_directory:
            if self.auto_mode:
                self.data_directory = Path("data")
            else:
                data_dir_str = Prompt.ask(
                    "[cyan]Enter path to your data directory[/cyan]",
                    default="data"
                )

                if self._check_exit(data_dir_str):
                    return False

                self.data_directory = Path(data_dir_str)

        # Validate directory exists
        if not self.data_directory.exists():
            console.print(create_error_panel(
                f"Directory not found: {self.data_directory}",
                "Please check the path and try again"
            ))
            return False

        # Load data using DatasetBuilder
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Loading data from directory...", total=None)

                # Build dataset from directory structure
                self.dataset, self.buildings, self.levels, self.rooms = \
                    self.dataset_builder.build_from_directory(
                        self.data_directory,
                        dataset_id="cli_dataset",
                        dataset_name="CLI Analysis Dataset"
                    )

            # Filter to get actual Room objects (not dict)
            self.rooms = [room for room in self.rooms.values() if hasattr(room, 'id')]

        except Exception as e:
            console.print(create_error_panel(
                f"Failed to load data: {str(e)}",
                "Check that the directory contains valid building data"
            ))
            if self.verbose:
                console.print_exception()
            return False

        # Show success
        room_count = len(self.rooms)
        building_count = len(self.buildings)
        summary = f"Loaded {room_count} rooms from {building_count} building(s)"
        self.progress.complete_step(1, summary)
        console.print(create_success_panel(summary))

        return True

    # ========================================================================
    # STEP 2: Select Standards
    # ========================================================================

    def _step_select_standards(self) -> bool:
        """Step 2: Select compliance standards."""
        self.progress.start_step(2)
        console.clear()
        console.print(self.progress.render())
        console.print()
        console.print(create_step_panel(2, "Select Compliance Standards"))
        console.print()

        # Load available standards
        standards = self._get_available_standards()

        if not self.auto_mode:
            # Show available standards
            console.print(create_standards_table(standards))
            console.print()

            # Prompt for selection
            selection = Prompt.ask(
                "[cyan]Select standards (comma-separated numbers or 'all')[/cyan]",
                default="1"
            )

            if self._check_exit(selection):
                return False

            # Parse selection
            if selection.lower() == 'all':
                self.selected_standards = [s['id'] for s in standards]
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    self.selected_standards = [standards[i]['id'] for i in indices if 0 <= i < len(standards)]
                except:
                    console.print("[yellow]Invalid selection, using EN16798-1[/yellow]")
                    self.selected_standards = ['en16798-1']
        else:
            # Auto mode: use EN16798-1
            self.selected_standards = ['en16798-1']

        # Show selection summary
        standard_names = [s['name'] for s in standards if s['id'] in self.selected_standards]
        summary = f"Selected: {', '.join(standard_names)}"
        self.progress.complete_step(2, summary)
        console.print(create_success_panel(summary))

        return True

    # ========================================================================
    # STEP 3: Configure Tests
    # ========================================================================

    def _step_configure_tests(self) -> bool:
        """Step 3: Configure tests to run."""
        self.progress.start_step(3)
        console.clear()
        console.print(self.progress.render())
        console.print()
        console.print(create_step_panel(3, "Configure Tests"))
        console.print()

        # Load available tests for selected standards
        self.selected_tests = self._get_tests_for_standards(self.selected_standards)

        if not self.auto_mode:
            console.print(f"[cyan]Found {len(self.selected_tests)} tests for selected standards[/cyan]")
            console.print()

            # Ask if user wants to customize
            customize = Confirm.ask("Customize test selection?", default=False)

            if customize:
                # TODO: Implement test selection UI
                console.print("[yellow]Test customization not yet implemented - using all tests[/yellow]")

        summary = f"Configured {len(self.selected_tests)} tests"
        self.progress.complete_step(3, summary)
        console.print(create_success_panel(summary))

        return True

    # ========================================================================
    # STEP 4: Run Analysis
    # ========================================================================

    def _step_run_analysis(self) -> bool:
        """Step 4: Run analysis."""
        self.progress.start_step(4)
        console.clear()
        console.print(self.progress.render())
        console.print()
        console.print(create_step_panel(4, "Run Analysis"))
        console.print()

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                # Analyze each room
                task = progress.add_task(
                    f"Analyzing {len(self.rooms)} rooms...",
                    total=len(self.rooms)
                )

                self.room_analyses = []
                for room in self.rooms:
                    try:
                        # Run analysis with selected tests
                        analysis = self.analysis_engine.analyze_room(
                            room=room,
                            tests=self.selected_tests,
                            apply_filters=True
                        )
                        self.room_analyses.append(analysis)
                    except Exception as e:
                        if self.verbose:
                            console.print(f"[yellow]Warning: Failed to analyze {room.name}: {e}[/yellow]")
                    finally:
                        progress.advance(task)

            # Aggregate building results
            if self.room_analyses and self.buildings:
                # Get the first building (or main building)
                building = list(self.buildings.values())[0]
                
                self.building_analysis = self.building_aggregator.aggregate(
                    building=building,
                    room_analyses=self.room_analyses
                )

        except Exception as e:
            console.print(create_error_panel(
                f"Analysis failed: {str(e)}",
                "Check your data and test configuration"
            ))
            if self.verbose:
                console.print_exception()
            return False

        # Calculate summary
        if self.building_analysis:
            compliance_rate = self.building_analysis.avg_compliance_rate
            summary = f"Complete - {compliance_rate:.1f}% compliance"
            self.progress.complete_step(4, summary)
            console.print(create_success_panel(
                f"Analysis complete!",
                f"Overall compliance: {compliance_rate:.1f}%"
            ))
        else:
            summary = f"Analyzed {len(self.room_analyses)} rooms"
            self.progress.complete_step(4, summary)
            console.print(create_success_panel(f"Analysis complete!", summary))

        return True

    # ========================================================================
    # STEP 5: Explore Results
    # ========================================================================

    def _step_explore_results(self):
        """Step 5: Explore results interactively."""
        self.progress.start_step(5)

        while True:
            console.clear()
            console.print(self.progress.render())
            console.print()
            console.print(create_step_panel(5, "Explore Results"))
            console.print()

            # Show menu
            console.print("[bold cyan]What would you like to view?[/bold cyan]\n")
            console.print("1. Building summary")
            console.print("2. All rooms")
            console.print("3. Failing rooms only")
            console.print("4. Specific room details")
            console.print("5. Continue to reports")
            console.print()

            choice = Prompt.ask("[cyan]Select option[/cyan]", choices=["1", "2", "3", "4", "5"], default="5")

            if choice == "5":
                break
            elif choice == "1":
                self._show_building_summary()
            elif choice == "2":
                self._show_all_rooms()
            elif choice == "3":
                self._show_failing_rooms()
            elif choice == "4":
                self._show_room_details()

            if choice != "5":
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

        self.progress.complete_step(5, "Results reviewed")

    def _show_building_summary(self):
        """Show building summary."""
        console.print("\n[bold cyan]Building Summary[/bold cyan]\n")
        
        if self.building_analysis:
            # Show building analysis table
            table = create_building_summary_table(self.building_analysis)
            console.print(table)
        else:
            console.print("[dim]No building analysis available[/dim]\n")

    def _show_all_rooms(self):
        """Show all rooms."""
        console.print("\n[bold cyan]All Rooms[/bold cyan]")
        console.print(f"[dim]Showing {len(self.room_analyses)} rooms[/dim]\n")
        
        if self.room_analyses:
            table = create_room_analysis_table(self.room_analyses)
            console.print(table)
        else:
            console.print("[dim]No room analyses available[/dim]\n")

    def _show_failing_rooms(self):
        """Show failing rooms only."""
        console.print("\n[bold cyan]Failing Rooms (< 95% compliance)[/bold cyan]\n")
        
        if self.room_analyses:
            # Filter failing rooms
            failing = [ra for ra in self.room_analyses if ra.overall_compliance_rate < 95.0]
            if failing:
                table = create_room_analysis_table(failing)
                console.print(table)
            else:
                console.print("[green]No failing rooms! All rooms meet 95% compliance.[/green]\n")
        else:
            console.print("[dim]No room analyses available[/dim]\n")

    def _show_room_details(self):
        """Show specific room details."""
        if not self.room_analyses:
            console.print("[yellow]No room analyses available[/yellow]\n")
            return
            
        # Show available rooms
        room_names = [ra.room_name for ra in self.room_analyses]
        console.print("\n[cyan]Available rooms:[/cyan]")
        for i, name in enumerate(room_names[:10], 1):  # Show first 10
            console.print(f"{i}. {name}")
        if len(room_names) > 10:
            console.print(f"... and {len(room_names) - 10} more")
        console.print()
        
        room_name = Prompt.ask("[cyan]Enter room name[/cyan]")
        
        # Find room analysis
        room_analysis = next((ra for ra in self.room_analyses if ra.room_name == room_name), None)
        
        if room_analysis:
            console.print(f"\n[bold cyan]Room Details: {room_name}[/bold cyan]")
            console.print(f"Compliance Rate: {room_analysis.overall_compliance_rate:.1f}%")
            console.print(f"Quality Score: {room_analysis.overall_quality_rate:.1f}%")
            console.print(f"Tests Passed: {len(room_analysis.passed_tests)}/{room_analysis.test_count}")
            
            if room_analysis.compliance_results:
                console.print("\n[cyan]Test Results:[/cyan]")
                table = create_test_results_table(room_analysis.compliance_results)
                console.print(table)
        else:
            console.print(f"\n[yellow]Room '{room_name}' not found[/yellow]\n")

    # ========================================================================
    # STEP 6: Generate Reports
    # ========================================================================

    def _step_generate_reports(self):
        """Step 6: Generate reports."""
        self.progress.start_step(6)
        console.clear()
        console.print(self.progress.render())
        console.print()
        console.print(create_step_panel(6, "Generate Reports"))
        console.print()

        # Get template
        if not self.auto_mode:
            console.print("[cyan]Available templates:[/cyan]")
            console.print("1. Building Detailed Report")
            console.print("2. Portfolio Summary")
            console.print("3. Room Comparison")
            console.print()

            template_choice = Prompt.ask(
                "[cyan]Select template[/cyan]",
                choices=["1", "2", "3"],
                default="1"
            )
            template = "building_detailed"
        else:
            template = "building_detailed"

        # Ensure output directory exists
        output_dir = Path("output/reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate report filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        building_name = list(self.buildings.values())[0].name if self.buildings else "building"
        self.report_path = output_dir / f"{building_name}_{timestamp}.html"

        # Generate report
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generating report...", total=None)

                # Check if we have a template file
                template_dir = Path("config/report_templates")
                template_file = template_dir / f"{template}.yaml"
                
                if template_file.exists():
                    # Use template-based generation
                    self.report_generator.generate_from_template(
                        template_path=template_file,
                        rooms=self.rooms,
                        building_name=building_name,
                        output_path=self.report_path
                    )
                else:
                    # Fallback: Generate basic HTML report
                    self._generate_basic_report(self.report_path, building_name)

        except Exception as e:
            console.print(create_error_panel(
                f"Report generation failed: {str(e)}",
                "Check template configuration and try again"
            ))
            if self.verbose:
                console.print_exception()
            return

        summary = f"Generated: {self.report_path}"
        self.progress.complete_step(6, summary)
        console.print(create_success_panel(
            "Report generated!",
            f"Saved to: {self.report_path}"
        ))

    def _generate_basic_report(self, output_path: Path, building_name: str):
        """Generate a basic HTML report when no template is available."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>IEQ Analysis Report - {building_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
    </style>
</head>
<body>
    <h1>IEQ Analysis Report</h1>
    <h2>{building_name}</h2>
    
    <h3>Building Summary</h3>
    <p>Total Rooms: {len(self.rooms)}</p>
    <p>Rooms Analyzed: {len(self.room_analyses)}</p>
"""
        
        if self.building_analysis:
            html_content += f"""
    <p>Overall Compliance: {self.building_analysis.avg_compliance_rate:.1f}%</p>
    <p>Overall Quality: {self.building_analysis.avg_quality_score:.1f}%</p>
"""
        
        html_content += """
    <h3>Room Results</h3>
    <table>
        <tr>
            <th>Room Name</th>
            <th>Compliance Rate</th>
            <th>Quality Score</th>
            <th>Tests Passed</th>
        </tr>
"""
        
        for ra in self.room_analyses:
            status_class = "pass" if ra.overall_compliance_rate >= 95 else "fail"
            html_content += f"""
        <tr>
            <td>{ra.room_name}</td>
            <td class="{status_class}">{ra.overall_compliance_rate:.1f}%</td>
            <td>{ra.overall_quality_rate:.1f}%</td>
            <td>{len(ra.passed_tests)}/{ra.test_count}</td>
        </tr>
"""
        
        html_content += """
    </table>
</body>
</html>
"""
        
        output_path.write_text(html_content)

    # ========================================================================
    # STEP 7: Export Data
    # ========================================================================

    def _step_export_data(self):
        """Step 7: Export analysis data."""
        self.progress.start_step(7)
        console.clear()
        console.print(self.progress.render())
        console.print()
        console.print(create_step_panel(7, "Export Data"))
        console.print()

        # Get format
        format_choice = Prompt.ask(
            "[cyan]Export format[/cyan]",
            choices=["json", "csv", "excel"],
            default="json"
        )

        # Ensure output directory exists
        output_dir = Path("output/exports")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate export filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.export_path = output_dir / f"analysis_{timestamp}.{format_choice}"

        # Export
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Exporting data...", total=None)

                if format_choice == "json":
                    self._export_to_json(self.export_path)
                elif format_choice == "csv":
                    self._export_to_csv(self.export_path)
                elif format_choice == "excel":
                    self._export_to_excel(self.export_path)

        except Exception as e:
            console.print(create_error_panel(
                f"Export failed: {str(e)}",
                "Check file permissions and try again"
            ))
            if self.verbose:
                console.print_exception()
            return

        summary = f"Exported to: {self.export_path}"
        self.progress.complete_step(7, summary)
        console.print(create_success_panel(
            "Data exported!",
            f"Saved to: {self.export_path}"
        ))

    def _export_to_json(self, path: Path):
        """Export analysis results to JSON."""
        data = {
            "building_analysis": {
                "compliance_rate": self.building_analysis.avg_compliance_rate if self.building_analysis else 0,
                "quality_rate": self.building_analysis.avg_quality_score if self.building_analysis else 0,
                "total_rooms": len(self.rooms),
                "analyzed_rooms": len(self.room_analyses),
            },
            "room_analyses": [
                {
                    "room_id": ra.room_id,
                    "room_name": ra.room_name,
                    "compliance_rate": ra.overall_compliance_rate,
                    "quality_score": ra.overall_quality_rate,
                    "tests_passed": len(ra.passed_tests),
                    "total_tests": ra.test_count,
                }
                for ra in self.room_analyses
            ]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _export_to_csv(self, path: Path):
        """Export analysis results to CSV."""
        import pandas as pd
        
        data = []
        for ra in self.room_analyses:
            data.append({
                "room_id": ra.room_id,
                "room_name": ra.room_name,
                "building_id": ra.building_id,
                "compliance_rate": ra.overall_compliance_rate,
                "quality_score": ra.overall_quality_rate,
                "tests_passed": len(ra.passed_tests),
                "total_tests": ra.test_count,
            })
        
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)

    def _export_to_excel(self, path: Path):
        """Export analysis results to Excel."""
        import pandas as pd
        
        # Room analyses
        room_data = []
        for ra in self.room_analyses:
            room_data.append({
                "room_id": ra.room_id,
                "room_name": ra.room_name,
                "building_id": ra.building_id,
                "compliance_rate": ra.overall_compliance_rate,
                "quality_score": ra.overall_quality_rate,
                "tests_passed": len(ra.passed_tests),
                "total_tests": ra.test_count,
            })
        
        df_rooms = pd.DataFrame(room_data)
        
        # Building summary
        building_data = [{
            "total_rooms": len(self.rooms),
            "analyzed_rooms": len(self.room_analyses),
            "compliance_rate": self.building_analysis.avg_compliance_rate if self.building_analysis else 0,
            "quality_rate": self.building_analysis.avg_quality_score if self.building_analysis else 0,
        }]
        df_building = pd.DataFrame(building_data)
        
        # Write to Excel with multiple sheets
        with pd.ExcelWriter(path) as writer:
            df_building.to_excel(writer, sheet_name="Building Summary", index=False)
            df_rooms.to_excel(writer, sheet_name="Room Analyses", index=False)

    # ========================================================================
    # Helpers
    # ========================================================================

    def _check_exit(self, value: str) -> bool:
        """Check if user wants to exit."""
        return value.lower() in ['quit', 'exit', 'q']

    def _exit_workflow(self, stage: str):
        """Exit workflow gracefully."""
        console.print(f"\n[yellow]Workflow stopped at {stage}[/yellow]")

    def _show_completion(self):
        """Show workflow completion summary."""
        console.clear()
        console.print(self.progress.render())
        console.print()

        summary = {
            'rooms_analyzed': len(self.room_analyses),
            'compliance_rate': self.building_analysis.avg_compliance_rate if self.building_analysis else 0,
        }

        if self.report_path:
            summary['report_path'] = str(self.report_path)
        
        if self.export_path:
            summary['export_path'] = str(self.export_path)

        console.print(create_completion_panel(summary))

    def _get_available_standards(self) -> List[dict]:
        """Get available compliance standards."""
        # Load from config
        config_dir = Path(__file__).parents[5] / "config" / "standards"

        standards = []

        # EN16798-1
        en16798_dir = config_dir / "en16798-1"
        if en16798_dir.exists():
            test_count = len(list(en16798_dir.glob("*.yaml")))
            standards.append({
                'id': 'en16798-1',
                'name': 'EN 16798-1',
                'description': 'European standard for building environmental design',
                'test_count': test_count
            })

        # Danish Guidelines
        danish_dir = config_dir / "danish-guidelines"
        if danish_dir.exists():
            test_count = len(list(danish_dir.glob("*.yaml")))
            standards.append({
                'id': 'danish',
                'name': 'Danish Guidelines',
                'description': 'Danish building regulations',
                'test_count': test_count
            })

        return standards

    def _get_tests_for_standards(self, standard_ids: List[str]) -> List[dict]:
        """Get tests for selected standards."""
        tests = []
        config_dir = Path(__file__).parents[5] / "config" / "standards"

        for standard_id in standard_ids:
            if standard_id == 'en16798-1':
                test_dir = config_dir / "en16798-1"
                standard_type = "en16798-1"  # Use enum value
            elif standard_id == 'danish':
                test_dir = config_dir / "danish-guidelines"
                standard_type = "danish-guidelines"
            else:
                continue

            if test_dir.exists():
                for yaml_file in test_dir.glob("*.yaml"):
                    with open(yaml_file) as f:
                        test_config = yaml.safe_load(f)
                        test_config['test_id'] = yaml_file.stem
                        
                        # Map 'feature' to 'parameter' if needed
                        if 'feature' in test_config and 'parameter' not in test_config:
                            test_config['parameter'] = test_config['feature']
                        
                        # Add standard if not present
                        if 'standard' not in test_config:
                            test_config['standard'] = standard_type
                        
                        tests.append(test_config)

        return tests
