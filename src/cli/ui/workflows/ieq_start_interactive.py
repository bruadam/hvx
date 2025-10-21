"""
Interactive workflow orchestrator for HVX CLI.

Provides a comprehensive interactive experience that guides users through
the complete data analysis workflow:
  1. Ask for data directory
  2. Validate and load data
  3. Ask for standards/tests/guidelines to apply
  4. Process analytics
  5. Display analytics interactively with filtering options
  6. Generate reports (predefined or custom templates)
  7. Save analytics data to file
  8. Exit workflow
"""

import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import pandas as pd

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box
from rich.live import Live
from rich.text import Text

from src.core.models import BuildingDataset, RoomType
from src.core.models.enums.constants import ROOM_TYPE_PATTERNS
from src.core.analytics.hierarchical_analysis_service import HierarchicalAnalysisService
from src.core.reporting.ReportService import ReportService
from src.core.parsers.DataStructureDetector import (
    create_structure_detector,
    DirectoryStructureType
)

console = Console()


@dataclass
class StepSummary:
    """Summary of a completed workflow step."""
    number: int
    title: str
    status: str  # 'completed', 'active', 'pending'
    summary: str  # One-line summary
    details: List[str]  # Collapsed details


class IEQStartInteractive:
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
        self.analysis_config: Optional[Dict[str, Any]] = None
        self.analysis_dir: Optional[Path] = None
        self.portfolio_name: str = "Portfolio"
        self.building_type: Optional[str] = None  # office, school, residential, etc.
        self.auto_mode: bool = auto_mode
        self.verbose: bool = verbose
        self.workflow_state: str = "init"

        # Track completed steps for collapsible display
        self.steps: List[StepSummary] = []
        self.current_step: int = 0

    def start(self, data_directory: Optional[Path] = None):
        """
        Start the interactive workflow following INSTRUCTIONS.md.

        Args:
            data_directory: Path to the data directory (optional)
        """
        console.clear()
        self._show_welcome()

        # Set initial state
        self.data_directory = data_directory

        # Main workflow loop
        self._main_workflow()

    def _show_welcome(self):
        """Display welcome message."""
        
        left = Text(justify="center")
        left.append("Let's get started with your analysis.\n\n", style="cyan")
        left.append("Type 'help' for assistance or 'quit' to exit at any time.\n", style="dim")
        right = Table.grid(padding=(0, 1))
        right.add_column(justify="left", ratio=1)
        right.add_row("[bold]Tips for getting started:[/bold]")
        right.add_row("- You will be guided through each step.")
        right.add_row("- In auto mode, defaults will be used.")
        right.add_row("- You can exit anytime by typing 'quit'.")

        inner_panel = Table.grid(expand=True)
        inner_panel.add_column(ratio=1)
        inner_panel.add_column(ratio=2)
        inner_panel.add_row(
            Panel(left, padding=(1, 2), border_style="none"),
            Panel(right, padding=(1, 1), border_style="none")
        )
        
        welcome_panel = Panel(inner_panel, box=box.ROUNDED, border_style="cyan", title="[bold]Welcome to HVX IEQ 🌡️[/bold]")

        console.print(welcome_panel)
        console.print()

    def _main_workflow(self):
        """Main workflow orchestration"""
        try:
            # Step 1-2: Ask for data directory and load data
            self.current_step = 1
            if not self._step_load_data():
                self._handle_workflow_exit("data_loading")
                return

            self.workflow_state = "data_loaded"

            # Step 1.5: Assign room types (if needed, interactive only)
            if not self.auto_mode:
                if not self._step_assign_room_types():
                    self._handle_workflow_exit("room_type_assignment")
                    return

            # Step 2: Select building type
            self.current_step = 2
            if not self._step_select_building_type():
                self._handle_workflow_exit("building_type_selection")
                return

            self.workflow_state = "building_type_selected"

            # Step 3: Ask for standards/tests/guidelines to apply
            self.current_step = 3
            if not self._step_select_rules():
                self._handle_workflow_exit("rule_selection")
                return

            self.workflow_state = "rules_selected"

            # Step 4-5: Process analytics and display interactively
            self.current_step = 4
            if not self._step_run_and_explore_analytics():
                self._handle_workflow_exit("analytics")
                return

            self.workflow_state = "analytics_complete"

            # Step 6: Generate reports
            if not self.auto_mode:
                self.current_step = 6
                if self._step_generate_reports():
                    self.workflow_state = "reports_generated"

            # Step 7: Save analytics data to file
            if not self.auto_mode:
                self.current_step = 7
                if self._step_save_analytics_data():
                    self.workflow_state = "data_saved"

            # Step 8: End workflow
            self._show_completion()

        except KeyboardInterrupt:
            self._handle_keyboard_interrupt()
        except Exception as e:
            self._handle_error(e)

    # ========================================================================
    # Collapsible Step Management
    # ========================================================================

    def _render_steps(self) -> Panel:
        """Render all steps with collapsible completed steps."""
        lines = []

        for step in self.steps:
            if step.status == "completed":
                # Collapsed: show checkmark and summary
                lines.append(f"[green]✓[/green] [dim]{step.number}. {step.title}:[/dim] [dim]{step.summary}[/dim]")
            elif step.status == "active":
                # Active step - show header
                lines.append(f"[bold cyan]▶ {step.number}. {step.title}[/bold cyan]")
            else:
                # Pending
                lines.append(f"[dim]  {step.number}. {step.title}[/dim]")

        content = "\n".join(lines) if lines else "[dim]No steps yet[/dim]"
        return Panel(content, title="[bold]Workflow Progress[/bold]", border_style="cyan", box=box.ROUNDED)

    def _clear_and_show_progress(self):
        """Clear screen and show workflow progress."""
        console.clear()
        console.print(self._render_steps())
        console.print()

    def _complete_step(self, number: int, title: str, summary: str, details: List[str] = None):
        """Mark a step as completed and collapse it."""
        # Find and update existing step or create new one
        step_found = False
        for step in self.steps:
            if step.number == number:
                step.status = "completed"
                step.summary = summary
                if details:
                    step.details = details
                step_found = True
                break

        if not step_found:
            self.steps.append(StepSummary(
                number=number,
                title=title,
                status="completed",
                summary=summary,
                details=details or []
            ))

        # Clear and show updated progress
        self._clear_and_show_progress()

    def _start_step(self, number: int, title: str):
        """Start a new step."""
        # Mark previous steps as completed if not already
        for step in self.steps:
            if step.status == "active":
                step.status = "completed"

        # Find and update existing step or create new one
        step_found = False
        for step in self.steps:
            if step.number == number:
                step.status = "active"
                step.title = title
                step_found = True
                break

        if not step_found:
            self.steps.append(StepSummary(
                number=number,
                title=title,
                status="active",
                summary="",
                details=[]
            ))

        # Clear and show updated progress
        self._clear_and_show_progress()

    # ========================================================================
    # STEP 1-2: Load Data
    # ========================================================================

    def _step_load_data(self) -> bool:
        """Step 1-2: Ask for data directory and load data."""
        self._start_step(1, "Load Building Data")

        # If data directory provided, use it
        if self.data_directory:
            result = self._load_from_directory(self.data_directory)
        else:
            # Ask for data directory
            data_dir = self._prompt_with_help(
                "[bold]Enter the path to your data directory[/bold] (type '?' for details)",
                default="data/samples/sample-extensive-data",
                help_text=(
                    "Your data directory should contain building folders with sensor CSV files.\n\n"
                    "Example structure:\n\n"
                    "data/\n"
                    "  └── portfolio/\n"
                    "      ├── building_1/\n"
                    "      │   ├── sensors/\n"
                    "      │   │   ├── level1_room1.csv\n"
                    "      │   │   └── level1_room2.csv\n"
                    "      │   └── climate/\n"
                    "      │       └── weather.csv\n"
                    "      └── building_2/...\n\n"
                )
            )

            if self._check_exit_command(data_dir):
                return False

            result = self._load_from_directory(Path(data_dir))

        if result and self.dataset:
            # Collapse step with summary
            summary = self.dataset.get_summary()
            summary_text = f"{summary['building_count']} buildings, {summary['total_room_count']} rooms loaded"
            self._complete_step(1, "Load Building Data", summary_text)

        return result

    def _load_from_directory(self, data_dir: Path) -> bool:
        """Load and validate data from directory."""
        # Validate directory exists
        if not data_dir.exists():
            console.print(f"\n[red]✗ Directory not found:[/red] {data_dir}\n")
            if self.auto_mode:
                return False

            # Offer to try again or get help
            if self._offer_help_or_retry("directory_not_found"):
                return self._step_load_data()
            return False

        try:
            # Show loading message
            with Live(
                Text("Fetching data...", style="cyan"),
                console=console,
                transient=True
            ) as live:
                # Analyze directory structure
                detector = create_structure_detector()
                analysis = detector.analyze_directory(data_dir)

                # Validate structure
                if analysis.structure_type == DirectoryStructureType.UNKNOWN or analysis.confidence < 0.5:
                    live.stop()
                    console.print("\n[yellow]⚠ Directory structure not recognized[/yellow]\n")

                    if analysis.issues:
                        console.print("[bold]Issues found:[/bold]")
                        for issue in analysis.issues:
                            console.print(f"  • {issue}")
                        console.print()

                    if not self.auto_mode and self._offer_help_or_retry("invalid_structure"):
                        return self._step_load_data()
                    return False

                # Load data
                from src.core.parsers.DataLoaderService import create_data_loader

                loader = create_data_loader(
                    auto_infer_levels=True,
                    auto_infer_room_types=True
                )

                self.dataset = loader.load_from_directory(data_dir, validate=True)
                self.data_directory = data_dir

            # Clear loading message and show success
            console.print(f"[green]✓ Data loaded successfully[/green]\n")

            # Show dataset summary
            self._show_dataset_summary()

            return True

        except Exception as e:
            console.print(f"\n[red]✗ Error loading data:[/red] {str(e)}\n")
            if not self.auto_mode and self._offer_help_or_retry("loading_error"):
                return self._step_load_data()
            return False

    def _show_dataset_summary(self):
        """Display dataset summary."""
        if not self.dataset:
            return

        summary = self.dataset.get_summary()

        building_details = "\n".join(
            f"  {idx}. {b['name']} (ID: {b['id']}): {b['room_count']} rooms, {b['level_count']} levels"
            for idx, b in enumerate(summary['buildings'], 1)
        )

        table = Table(box=box.ROUNDED, show_header=False, title="🔣 Loaded Dataset Summary")
        table.add_column("Property", style="cyan bold")
        table.add_column("Value")

        table.add_row("Source", str(summary['source_directory']))
        table.add_row("Buildings", str(summary['building_count']))
        table.add_row("Total Rooms", str(summary['total_room_count']))
        table.add_row("Buildings Detail", building_details if building_details else "N/A")

        console.print(table)
        console.print()

    # ========================================================================
    # STEP 1.5: Assign Room Types
    # ========================================================================

    def _step_assign_room_types(self) -> bool:
        """Assign room types to rooms, with option for interactive assignment."""
        if not self.dataset:
            return True  # Skip if no dataset

        # Check how many rooms have no type assigned
        rooms_without_type = []
        for building in self.dataset.buildings:
            for room in building.rooms:
                if room.room_type is None:
                    rooms_without_type.append((building, room))

        if not rooms_without_type:
            console.print("[green]✓ All rooms have types assigned[/green]\n")
            return True

        # Show summary
        console.print(f"\n[yellow]⚠️ Found {len(rooms_without_type)} room(s) without assigned types[/yellow]\n")

        console.print("[bold]Room Type Assignment Options:[/bold]\n")
        console.print("  [cyan]1.[/cyan] Assign all to same type")
        console.print("  [cyan]2.[/cyan] Assign individually")
        console.print("  [cyan]3.[/cyan] Use default (OTHER)")
        console.print("  [cyan]4.[/cyan] Skip assignment")
        console.print()

        choice = self._prompt_with_help(
            "[bold]Choose option[/bold]",
            choices=["1", "2", "3", "4"],
            default="1",
            help_text=(
                "Room type assignment helps categorize rooms for accurate analysis.\n\n"
                "[bold]Options:[/bold]\n"
                "  1. Assign all to same type - Quick option for uniform portfolios\n"
                "  2. Assign individually - Precise control for each room\n"
                "  3. Use default (OTHER) - Generic type for mixed-use spaces\n"
                "  4. Skip assignment - Continue without room types\n\n"
                "[bold]Available room types:[/bold]\n"
                "  • Office, Meeting Room, Open Office\n"
                "  • Classroom, Auditorium, Library\n"
                "  • Bedroom, Living Room, Kitchen\n"
                "  • Operating Room, Patient Room, Laboratory\n"
                "  • Corridor, Lobby, Storage, Other\n"
            )
        )

        if self._check_exit_command(choice):
            return True

        if choice == "1":
            return self._assign_all_same_type(rooms_without_type)
        elif choice == "2":
            return self._assign_individually(rooms_without_type)
        elif choice == "3":
            return self._assign_default_type(rooms_without_type)
        else:
            console.print("[yellow]Skipping room type assignment[/yellow]\n")
            return True

    def _assign_all_same_type(self, rooms: List) -> bool:
        """Assign all untyped rooms to the same room type."""
        console.print("\n[bold]Select room type for all rooms:[/bold]\n")

        # Show available room types
        room_types = list(RoomType)
        for i, rt in enumerate(room_types, 1):
            console.print(f"  {i}. {rt.value.replace('_', ' ').title()}")
        console.print()

        choice = Prompt.ask("[bold]Select room type[/bold]", choices=[str(i) for i in range(1, len(room_types) + 1)], default="1")
        selected_type = room_types[int(choice) - 1]

        # Assign to all rooms
        for building, room in rooms:
            room.room_type = selected_type

        console.print(f"\n[green]✓ Assigned {len(rooms)} room(s) to type: {selected_type.value}[/green]\n")
        return True

    def _assign_individually(self, rooms: List) -> bool:
        """Assign room types individually."""
        console.print("\n[bold]Individual Room Type Assignment[/bold]\n")

        room_types = list(RoomType)
        type_choices = {str(i): rt for i, rt in enumerate(room_types, 1)}

        # Show type menu once
        console.print("[dim]Available types:[/dim]")
        for i, rt in enumerate(room_types, 1):
            console.print(f"  {i}. {rt.value.replace('_', ' ').title()}")
        console.print()

        for building, room in rooms:
            # Try to infer first
            inferred_type = self._infer_room_type_from_name(room.name)

            if inferred_type:
                console.print(f"[cyan]{room.name}[/cyan] (Building: {building.name})")
                console.print(f"  [dim]Suggested: {inferred_type.value}[/dim]")

                if Confirm.ask("  Use suggestion?", default=True):
                    room.room_type = inferred_type
                    continue

            # Manual selection
            console.print(f"\n[cyan]{room.name}[/cyan] (Building: {building.name})")
            choice = Prompt.ask("  Select type", choices=list(type_choices.keys()), default="10")  # Default to OTHER
            room.room_type = type_choices[choice]

        console.print(f"\n[green]✓ Room types assigned[/green]\n")
        return True

    def _assign_default_type(self, rooms: List) -> bool:
        """Assign default OTHER type to all rooms."""
        for building, room in rooms:
            room.room_type = RoomType.OTHER

        console.print(f"\n[green]✓ Assigned {len(rooms)} room(s) to default type (OTHER)[/green]\n")
        return True

    def _infer_room_type_from_name(self, room_name: str) -> Optional[RoomType]:
        """Infer room type from room name using pattern matching."""
        room_name_lower = room_name.lower()

        for room_type_str, patterns in ROOM_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern in room_name_lower:
                    # Find matching RoomType enum
                    for rt in RoomType:
                        if rt.value == room_type_str:
                            return rt

        return None

    # ========================================================================
    # STEP 2: Select Building Type
    # ========================================================================

    def _step_select_building_type(self) -> bool:
        """Step 2: Select building type for appropriate rule selection."""
        self._start_step(2, "Select Building Type")

        # Use building types from models
        from src.core.models.enums.constants import BUILDING_TYPE_PATTERNS

        console.print("[bold]What type of building are you analyzing?[/bold]\n")
        console.print("  [cyan]1.[/cyan] Office")
        console.print("  [cyan]2.[/cyan] School / Educational")
        console.print("  [cyan]3.[/cyan] Residential / Housing")
        console.print("  [cyan]4.[/cyan] Healthcare / Hospital")
        console.print("  [cyan]5.[/cyan] Mixed / Other")
        console.print()

        choice = self._prompt_with_help(
            "[bold]Choose building type[/bold]",
            choices=["1", "2", "3", "4", "5"],
            default="1",
            help_text="Building type determines which standards and guidelines are most relevant"
        )

        if self._check_exit_command(choice):
            return False

        building_type_map = {
            "1": ("office", "Office"),
            "2": ("school", "School / Educational"),
            "3": ("residential", "Residential"),
            "4": ("hospital", "Healthcare / Hospital"),
            "5": ("mixed", "Mixed / Other")
        }

        self.building_type, display_name = building_type_map.get(choice, ("office", "Office"))

        console.print(f"\n[green]✓[/green] Building type: {display_name}\n")

        # Collapse step
        self._complete_step(2, "Select Building Type", display_name)
        return True

    # ========================================================================
    # STEP 3: Select Standards/Tests/Guidelines
    # ========================================================================

    def _step_select_rules(self) -> bool:
        """Step 3: Ask for standards/tests/guidelines to apply."""
        self._start_step(3, "Select Analysis Rules")

        # Show building type context
        console.print(f"[dim]Building type: {self.building_type}[/dim]\n")

        console.print("[bold]What would you like to analyze?[/bold]\n")
        console.print("  [cyan]1.[/cyan] Recommended for this building type (auto-select)")
        console.print("  [cyan]2.[/cyan] All standards, tests & guidelines")
        console.print("  [cyan]3.[/cyan] Specific standards only")
        console.print("  [cyan]4.[/cyan] Custom selection (advanced)")
        console.print("  [cyan]5.[/cyan] None - skip analysis")
        console.print()

        choice = self._prompt_with_help(
            "[bold]Choose option[/bold]",
            choices=["1", "2", "3", "4", "5"],
            default="1",
            help_text="Standards define compliance rules for temperature, CO2, humidity, etc."
        )

        if self._check_exit_command(choice) or choice == "5":
            return False

        summary_text = ""
        if choice == "1":
            # Auto-select based on building type
            if not self._auto_select_rules_for_building_type():
                return False
            summary_text = f"Auto-selected for {self.building_type}"

        elif choice == "2":
            # All standards
            from src.cli.ui.components.rule_selector import create_custom_config
            self.analysis_config, config_summary = create_custom_config(auto_mode=True)
            console.print(f"\n[green]✓[/green] Using all standards\n")
            summary_text = "All standards selected"

        elif choice == "3":
            # Specific standards
            if not self._select_specific_standards():
                return False
            summary_text = "Specific standards selected"

        elif choice == "4":
            # Custom selection
            if not self._select_custom_rules():
                return False
            summary_text = "Custom configuration created"

        # Collapse step
        self._complete_step(3, "Select Analysis Rules", summary_text)
        return True

    def _auto_select_rules_for_building_type(self) -> bool:
        """Auto-select appropriate rules based on building type."""
        from src.core.analytics.ieq.ConfigBuilder import IEQConfigBuilder

        # Pass building type to filter rules
        builder = IEQConfigBuilder(building_type=self.building_type)

        # Define building type to standards mapping
        building_type_rules = {
            "office": {
                "standards": ["en16798-1", "br18"],
                "categories": ["cat_ii"],  # Category II for offices
                "description": "EN16798-1 Cat II and BR18 office requirements"
            },
            "school": {
                "standards": ["en16798-1", "danish-guidelines"],
                "categories": ["cat_ii"],
                "description": "EN16798-1 Cat II and Danish school guidelines"
            },
            "residential": {
                "standards": ["en16798-1", "br18"],
                "categories": ["cat_iii"],  # Category III for residential
                "description": "EN16798-1 Cat III and BR18 residential requirements"
            },
            "hospital": {
                "standards": ["en16798-1"],
                "categories": ["cat_i"],  # Category I for healthcare
                "description": "EN16798-1 Cat I (high requirements for healthcare)"
            },
            "mixed": {
                "standards": ["en16798-1", "br18", "danish-guidelines"],
                "categories": ["cat_ii"],
                "description": "All standards with Cat II default"
            }
        }

        rules_config = building_type_rules.get(self.building_type, building_type_rules["office"])

        console.print(f"\n[cyan]Auto-selecting:[/cyan] {rules_config['description']}\n")

        # Add standards
        for standard in rules_config["standards"]:
            builder.add_standard(standard)

        self.analysis_config = builder.build()
        console.print(f"[green]✓[/green] Rules configured for {self.building_type} buildings\n")

        return True

    def _select_specific_standards(self) -> bool:
        """Select specific standards."""
        from src.core.analytics.ieq.ConfigBuilder import IEQConfigBuilder

        # Pass building type to filter rules
        builder = IEQConfigBuilder(building_type=self.building_type)
        standards = builder.get_available_standards()

        console.print("\n[bold]Available Standards:[/bold]\n")

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Standard", style="bold")
        table.add_column("Description")

        standard_descriptions = {
            "en16798-1": "European standard for indoor environmental parameters",
            "br18": "Danish Building Regulations 2018",
            "danish-guidelines": "Danish guidelines for indoor climate"
        }

        for i, standard in enumerate(standards, 1):
            desc = standard_descriptions.get(standard, "")
            table.add_row(str(i), standard, desc)

        console.print(table)
        console.print()

        selection = self._prompt_with_help(
            "[bold]Enter standard numbers (comma-separated) or 'all'[/bold]",
            default="all",
            help_text="Select which standards to apply for compliance checking"
        )

        if self._check_exit_command(selection):
            return False

        # Build config
        selected_standards = set()
        if selection.lower() == "all":
            selected_standards = set(standards)
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                selected_standards = {standards[i] for i in indices if 0 <= i < len(standards)}
            except (ValueError, IndexError):
                console.print("[yellow]Invalid selection, using all standards[/yellow]\n")
                selected_standards = set(standards)

        for standard in selected_standards:
            builder.add_standard(standard)

        self.analysis_config = builder.build()
        console.print(f"\n[green]✓[/green] Selected {len(selected_standards)} standard(s)\n")

        return True

    def _select_custom_rules(self) -> bool:
        """Custom rule selection using interactive selector."""
        from src.cli.ui.components.rule_selector import create_custom_config

        self.analysis_config, config_summary = create_custom_config(auto_mode=False)
        console.print(f"\n[green]✓[/green] Configuration created\n")

        return True

    # ========================================================================
    # STEP 4-5: Process and Explore Analytics
    # ========================================================================

    def _step_run_and_explore_analytics(self) -> bool:
        """Step 4-5: Process analytics and display results interactively."""
        self._start_step(3, "Process Analytics")

        # Set output directory
        self.analysis_dir = Path("output/analysis")
        self.portfolio_name = "Portfolio"

        try:
            # Show processing message
            with Live(
                Text("Processing analytics...", style="cyan"),
                console=console,
                transient=True
            ) as live:
                # Initialize service
                service = HierarchicalAnalysisService(config_dict=self.analysis_config)

                # Run analysis
                self.analysis_results = service.analyze_dataset(
                    dataset=self.dataset,
                    output_dir=self.analysis_dir,
                    portfolio_name=self.portfolio_name,
                    save_individual_files=True,
                    verbose=self.verbose
                )

            # Clear processing message and update progress
            self._clear_and_show_progress()
            console.print("[green]✓ Analytics processing complete[/green]\n")

            # Show summary
            self._show_analysis_summary()

            # Create summary for collapsed view
            if self.analysis_results and self.analysis_results.portfolio:
                portfolio = self.analysis_results.portfolio
                summary_text = f"{portfolio.building_count} buildings analyzed, {portfolio.avg_compliance_rate:.1f}% avg compliance"
            else:
                summary_text = "Analysis completed"

            # Collapse processing step
            self._complete_step(3, "Process Analytics", summary_text)

            # Step 4: Display analytics interactively
            if not self.auto_mode:
                self._start_step(4, "Explore Results")
                result = self._explore_analytics_interactively()
                self._complete_step(4, "Explore Results", "Exploration completed")
                return result

            return True

        except Exception as e:
            console.print(f"\n[red]✗ Error during analytics:[/red] {str(e)}\n")
            if not self.auto_mode and self._offer_help_or_retry("analytics_error"):
                return self._step_run_and_explore_analytics()
            return False

    def _show_analysis_summary(self):
        """Display analysis summary with meaningful metrics."""
        if not self.analysis_results or not self.analysis_results.portfolio:
            return

        portfolio = self.analysis_results.portfolio

        console.print("[bold cyan]Analysis Summary[/bold cyan]\n")

        table = Table(box=box.ROUNDED, show_header=False, title="📊 Portfolio Results")
        table.add_column("Metric", style="cyan bold", width=35)
        table.add_column("Value", justify="right", width=25)

        # Basic metrics
        table.add_row("Buildings Analyzed", str(portfolio.building_count))
        table.add_row("Total Rooms", str(portfolio.total_room_count))
        table.add_row("Data Quality Score", f"{portfolio.avg_quality_score:.1f}%")

        # Add separator
        table.add_row("", "")

        # EN16798-1 Category Analysis
        dominant_category = self._calculate_dominant_en16798_category(portfolio)
        if dominant_category:
            table.add_row("EN16798-1 Category (>95% time)", dominant_category)

        # Danish Guidelines Exceedance
        danish_hours = self._calculate_danish_guideline_hours(portfolio)
        if danish_hours is not None:
            table.add_row("Hours Above Danish Guidelines", f"{danish_hours:.0f}h")

        # Critical issues count
        if portfolio.critical_issues:
            table.add_row("Critical Issues Found", f"{len(portfolio.critical_issues)}")

        console.print(table)
        console.print()

        # Show top recommendations if available
        if portfolio.recommendations and len(portfolio.recommendations) > 0:
            console.print("[bold]Top Recommendations:[/bold]")
            for i, rec in enumerate(portfolio.recommendations[:3], 1):
                console.print(f"  {i}. {rec}")
            console.print()

    def _calculate_dominant_en16798_category(self, portfolio) -> Optional[str]:
        """Calculate which EN16798-1 category buildings spend >95% time in."""
        # First, try to get from room analysis category assignments
        if self.analysis_results and self.analysis_results.rooms:
            category_counts = {"Cat I": 0, "Cat II": 0, "Cat III": 0, "Cat IV": 0}
            category_confidences = {"Cat I": [], "Cat II": [], "Cat III": [], "Cat IV": []}
            total_rooms_with_category = 0

            for room_analysis in self.analysis_results.rooms.values():
                if room_analysis.en16798_category:
                    category_counts[room_analysis.en16798_category] += 1
                    category_confidences[room_analysis.en16798_category].append(
                        room_analysis.en16798_category_confidence or 0
                    )
                    total_rooms_with_category += 1

            # Find most common category
            if total_rooms_with_category > 0:
                most_common_category = max(category_counts.items(), key=lambda x: x[1])
                if most_common_category[1] > 0:
                    category = most_common_category[0]
                    room_count = most_common_category[1]
                    avg_confidence = sum(category_confidences[category]) / len(category_confidences[category])

                    percentage_of_rooms = (room_count / total_rooms_with_category) * 100

                    if avg_confidence >= 95.0:
                        return f"{category} ({avg_confidence:.1f}% compliance, {percentage_of_rooms:.0f}% of rooms)"
                    else:
                        return f"{category} ({avg_confidence:.1f}% compliance) [<95% threshold]"

        # Fallback: Check test aggregations
        if not portfolio.test_aggregations:
            return None

        category_compliance = {"Cat I": 0, "Cat II": 0, "Cat III": 0, "Cat IV": 0}

        for test_name, test_data in portfolio.test_aggregations.items():
            if "en16798" in test_name.lower():
                if "cat_i" in test_name.lower():
                    category_compliance["Cat I"] = test_data.get("avg_compliance_rate", 0)
                elif "cat_ii" in test_name.lower():
                    category_compliance["Cat II"] = test_data.get("avg_compliance_rate", 0)
                elif "cat_iii" in test_name.lower():
                    category_compliance["Cat III"] = test_data.get("avg_compliance_rate", 0)

        # Find category with highest compliance >= 95%
        for category, compliance in sorted(category_compliance.items(), key=lambda x: x[1], reverse=True):
            if compliance >= 95.0:
                return f"{category} ({compliance:.1f}%)"

        # If no category >= 95%, show best fit
        best_cat = max(category_compliance.items(), key=lambda x: x[1])
        if best_cat[1] > 0:
            return f"{best_cat[0]} ({best_cat[1]:.1f}%) [Below 95%]"

        return None

    def _calculate_danish_guideline_hours(self, portfolio) -> Optional[float]:
        """Calculate cumulative hours above Danish guidelines."""
        if not portfolio.test_aggregations:
            return None

        total_exceedance_hours = 0.0
        found_danish_tests = False

        # Look for Danish guideline tests
        for test_name, test_data in portfolio.test_aggregations.items():
            if "danish" in test_name.lower():
                found_danish_tests = True
                # Calculate exceedance hours from non-compliance
                if "total_points" in test_data and "compliant_points" in test_data:
                    total_points = test_data.get("total_points", 0)
                    compliant_points = test_data.get("compliant_points", 0)
                    non_compliant = total_points - compliant_points

                    # Assuming hourly data points
                    total_exceedance_hours += non_compliant / 60.0 if total_points > 0 else 0

        return total_exceedance_hours if found_danish_tests else None

    def _explore_analytics_interactively(self) -> bool:
        """Step 4-5: Process analytics and display results interactively."""
        console.print("[bold]What would you like to do?[/bold]\n")
        console.print("  [cyan]1.[/cyan] View summary and continue")
        console.print("  [cyan]2.[/cyan] Explore results interactively")
        console.print("  [cyan]3.[/cyan] Get smart recommendations")
        console.print()

        choice = self._prompt_with_help(
            "[bold]Choose option[/bold]",
            choices=["1", "2", "3"],
            default="1",
            help_text="Explore allows filtering by standard, building, room, etc."
        )

        if self._check_exit_command(choice):
            return True  # Continue to next step

        if choice == "2":
            # Launch interactive explorer
            try:
                from src.cli.ui.explorers.analysis_explorer import launch_analysis_explorer
                launch_analysis_explorer(self.analysis_dir)
                console.print("\n[green]✓ Exploration complete[/green]\n")
            except Exception as e:
                console.print(f"[yellow]Explorer unavailable: {str(e)}[/yellow]\n")

        elif choice == "3":
            # Show smart recommendations
            self._show_smart_recommendations()

        return True

    def _show_smart_recommendations(self):
        """Display smart recommendations based on analysis."""
        console.print("\n[bold cyan]Smart Recommendations[/bold cyan]\n")

        try:
            with Live(
                Text("Analyzing patterns and generating recommendations...", style="cyan"),
                console=console,
                transient=True
            ) as live:
                # Initialize recommendation service
                from src.core.analytics.ieq.SmartRecommendationService import SmartRecommendationService

                rec_service = SmartRecommendationService(config_dict=self.analysis_config)

                # Load weather data if available
                weather_data = self._load_weather_data_if_available()

                # Generate recommendations
                portfolio_recs = rec_service.generate_portfolio_recommendations(
                    dataset=self.dataset,
                    analysis_results=self.analysis_results,
                    weather_data=weather_data,
                    auto_run_prerequisites=True,
                    top_n=10
                )

            # Display recommendations
            self._display_recommendations(portfolio_recs)

        except Exception as e:
            console.print(f"[yellow]Error generating recommendations: {str(e)}[/yellow]\n")
            if self.verbose:
                console.print_exception()

    def _load_weather_data_if_available(self) -> Optional[pd.DataFrame]:
        """Load weather data if available in the data directory."""
        if not self.data_directory:
            return None

        # Look for weather data files
        weather_file_patterns = ['weather.csv', 'weather_data.csv', 'outdoor.csv', 'outdoor_data.csv']

        for pattern in weather_file_patterns:
            weather_path = self.data_directory / pattern
            if weather_path.exists():
                try:
                    import pandas as pd
                    weather_df = pd.read_csv(weather_path, parse_dates=[0], index_col=0)
                    return weather_df
                except Exception:
                    continue

        return None

    def _display_recommendations(self, portfolio_recs):
        """Display portfolio recommendations in a user-friendly format."""
        # Summary panel
        summary_text = (
            f"[bold]Total Recommendations:[/bold] {portfolio_recs.total_recommendations}\n"
            f"  [red]Critical:[/red] {portfolio_recs.critical_count}\n"
            f"  [yellow]High:[/yellow] {portfolio_recs.high_count}\n"
            f"  [cyan]Medium:[/cyan] {portfolio_recs.medium_count}\n"
            f"  [dim]Low:[/dim] {portfolio_recs.low_count}"
        )

        summary_panel = Panel(
            summary_text,
            title="📊 Recommendation Summary",
            border_style="cyan",
            box=box.ROUNDED
        )
        console.print(summary_panel)
        console.print()

        # Common issues
        if portfolio_recs.common_issues:
            console.print("[bold]Common Issues Across Portfolio:[/bold]")
            for issue in portfolio_recs.common_issues:
                console.print(f"  • {issue}")
            console.print()

        # Top recommendations
        if portfolio_recs.top_recommendations:
            console.print("[bold cyan]Top Priority Recommendations:[/bold cyan]\n")

            for i, rec in enumerate(portfolio_recs.top_recommendations[:5], 1):
                # Priority badge
                priority_styles = {
                    'critical': 'bold red',
                    'high': 'bold yellow',
                    'medium': 'bold cyan',
                    'low': 'dim'
                }
                priority_style = priority_styles.get(rec.priority, 'white')

                # Build recommendation display
                rec_content = [
                    f"[{priority_style}]{rec.priority.upper()}[/{priority_style}] - {rec.title}",
                    "",
                    f"[dim]{rec.description}[/dim]",
                    "",
                    "[bold]Impact:[/bold]",
                    f"  {rec.estimated_impact}",
                    "",
                    "[bold]Cost:[/bold]",
                    f"  {rec.implementation_cost}"
                ]

                # Add rationale if available
                if rec.rationale:
                    rec_content.extend([
                        "",
                        "[bold]Rationale:[/bold]"
                    ])
                    for rationale_item in rec.rationale[:3]:  # Show top 3 rationale items
                        rec_content.append(f"  • {rationale_item}")

                # Add weather correlation if available
                if rec.weather_correlations:
                    rec_content.extend([
                        "",
                        "[bold]Weather Correlation:[/bold]"
                    ])
                    for param, corr_data in list(rec.weather_correlations.items())[:2]:
                        if isinstance(corr_data, dict):
                            corr_value = corr_data.get('correlation', 0)
                            rec_content.append(f"  • {param}: {corr_value:+.2f}")

                rec_panel = Panel(
                    "\n".join(rec_content),
                    title=f"[bold]#{i}[/bold]",
                    border_style=priority_style,
                    box=box.ROUNDED
                )
                console.print(rec_panel)
                console.print()

        # Ask if user wants to see more
        if portfolio_recs.total_recommendations > 5:
            if Confirm.ask(f"\n[bold]Show all {portfolio_recs.total_recommendations} recommendations?[/bold]", default=False):
                self._display_all_recommendations(portfolio_recs)

        # Ask if user wants to export recommendations
        if Confirm.ask("\n[bold]Export recommendations to file?[/bold]", default=False):
            self._export_recommendations(portfolio_recs)

    def _display_all_recommendations(self, portfolio_recs):
        """Display all recommendations grouped by building."""
        console.print("\n[bold cyan]All Recommendations by Building[/bold cyan]\n")

        for building_name, recommendations in portfolio_recs.by_building.items():
            if not recommendations:
                continue

            console.print(f"\n[bold]{building_name}[/bold] ({len(recommendations)} recommendations)")

            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {
                    'critical': '🔴',
                    'high': '🟡',
                    'medium': '🔵',
                    'low': '⚪'
                }
                emoji = priority_emoji.get(rec.priority, '⚪')

                console.print(f"  {emoji} {i}. [{rec.priority.upper()}] {rec.title}")
                console.print(f"     {rec.description[:100]}...")
                console.print()

    def _export_recommendations(self, portfolio_recs):
        """Export recommendations to JSON file."""
        from src.core.analytics.ieq.SmartRecommendationService import SmartRecommendationService
        import json

        try:
            rec_service = SmartRecommendationService()
            rec_dict = rec_service.export_recommendations_to_dict(portfolio_recs)

            # Create output directory
            output_dir = Path("output/recommendations")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save to file
            output_file = output_dir / "smart_recommendations.json"
            with open(output_file, 'w') as f:
                json.dump(rec_dict, f, indent=2)

            console.print(f"\n[green]✓[/green] Recommendations exported to: {output_file}\n")

        except Exception as e:
            console.print(f"[yellow]Error exporting recommendations: {str(e)}[/yellow]\n")

    # ========================================================================
    # STEP 6: Generate Reports
    # ========================================================================

    def _step_generate_reports(self) -> bool:
        """Step 6: Generate reports with template selection."""
        if Confirm.ask("\n[bold]Would you like to generate a report?[/bold]", default=True):
            self._start_step(6, "Generate Report")

            console.print("[bold]Report options:[/bold]\n")
            console.print("  [cyan]1.[/cyan] Use predefined template")
            console.print("  [cyan]2.[/cyan] Create custom template")
            console.print("  [cyan]3.[/cyan] Skip report generation")
            console.print()

            choice = self._prompt_with_help(
                "[bold]Choose option[/bold]",
                choices=["1", "2", "3"],
                default="1",
                help_text="Templates define which sections, charts, and tables to include"
            )

            if self._check_exit_command(choice) or choice == "3":
                return False

            result = False
            summary_text = ""
            if choice == "1":
                result = self._generate_predefined_report()
                summary_text = "Predefined template configured"
            elif choice == "2":
                result = self._generate_custom_report()
                summary_text = "Custom template created"

            if result:
                self._complete_step(6, "Generate Report", summary_text)

            return result

        return False

    def _generate_predefined_report(self) -> bool:
        """Generate report using predefined template."""
        from src.core.reporting.ReportService import ReportService

        # Initialize report service
        report_service = ReportService()

        # List available templates
        templates = report_service.list_templates()

        if not templates:
            console.print("[yellow]No report templates found. Please create templates in config/report_templates/[/yellow]\n")
            return False

        console.print("\n[bold]Available templates:[/bold]\n")

        for i, template in enumerate(templates, 1):
            console.print(f"  [cyan]{i}.[/cyan] {template['name']}")
            console.print(f"      [dim]{template['description']}[/dim]")

        console.print()

        # Get template choice
        choices = [str(i) for i in range(1, len(templates) + 1)]
        template_choice = Prompt.ask("[bold]Select template[/bold]", choices=choices, default="1")

        selected_template = templates[int(template_choice) - 1]
        template_name = selected_template['template_id']

        # Choose format
        console.print("\n[bold]Output format:[/bold]")
        console.print("  1. HTML (viewable in browser)")
        console.print("  2. PDF (requires weasyprint or pdfkit)")
        console.print("  3. Both HTML and PDF")
        console.print()

        format_choice = Prompt.ask("[bold]Choose format[/bold]", choices=["1", "2", "3"], default="1")

        format_map = {
            "1": "html",
            "2": "pdf",
            "3": "both"
        }

        output_format = format_map.get(format_choice, "html")

        # Check PDF backend if PDF is requested
        if output_format in ['pdf', 'both']:
            backend_info = report_service.get_pdf_backend_info()
            current_backend = backend_info['current_backend']

            if current_backend == 'none':
                console.print("\n[yellow]⚠ No PDF backend available.[/yellow]")
                console.print("[dim]Install weasyprint for best results: pip install weasyprint[/dim]\n")

                if not Confirm.ask("Generate HTML only instead?", default=True):
                    return False

                output_format = "html"
            elif current_backend == 'reportlab':
                console.print(f"\n[yellow]⚠ Using basic PDF backend ({current_backend}).[/yellow]")
                console.print("[dim]For better HTML/CSS rendering, install weasyprint: pip install weasyprint[/dim]\n")

        # Load weather data if available
        weather_data = self._load_weather_data_if_available()

        # Generate report
        try:
            with Live(
                Text(f"Generating {output_format} report...", style="cyan"),
                console=console,
                transient=True
            ) as live:
                result = report_service.generate_report(
                    template_name=template_name,
                    analysis_results=self.analysis_results,
                    dataset=self.dataset,
                    weather_data=weather_data,
                    format=output_format
                )

            if result['status'] == 'success':
                console.print(f"\n[green]✓ Report generated successfully![/green]\n")
                
                # Check if multiple building reports were generated
                if 'reports' in result:
                    # Multiple building reports
                    console.print(f"[bold]Generated {result['successful_reports']} building reports:[/bold]\n")
                    for report in result['reports']:
                        if report.get('status') == 'success':
                            console.print(f"  • {report['building_name']}: {report['primary_output']}")
                    
                    if result['failed_reports'] > 0:
                        console.print(f"\n[yellow]⚠ {result['failed_reports']} reports failed to generate[/yellow]")
                    
                    console.print()
                else:
                    # Single report
                    console.print(f"[bold]Output:[/bold] {result['primary_output']}")

                    if output_format == 'both':
                        console.print(f"[bold]HTML:[/bold] {result['html']['output_path']}")
                        if result['pdf']['status'] == 'success':
                            console.print(f"[bold]PDF:[/bold] {result['pdf']['output_path']}")

                    console.print()

                # Offer to open report
                if Confirm.ask("[bold]Open report in browser/viewer?[/bold]", default=True):
                    import webbrowser
                    import platform

                    if 'reports' in result:
                        # Open first successful report
                        first_success = next((r for r in result['reports'] if r.get('status') == 'success'), None)
                        if first_success:
                            output_path = first_success['primary_output']
                        else:
                            console.print("[yellow]No successful reports to open[/yellow]")
                            return True
                    else:
                        output_path = result['primary_output']

                    if result.get('format') == 'html' or (not 'format' in result):
                        webbrowser.open(f'file://{output_path.absolute()}')
                    elif result.get('format') == 'pdf' and platform.system() == 'Darwin':
                        # macOS: use 'open' command
                        import subprocess
                        subprocess.run(['open', str(output_path)])
                    else:
                        console.print(f"[dim]Please open: {output_path}[/dim]")

                return True
            else:
                console.print(f"\n[red]✗ Report generation failed:[/red] {result.get('message', 'Unknown error')}\n")
                return False

        except Exception as e:
            console.print(f"\n[red]✗ Error generating report:[/red] {str(e)}\n")
            if self.verbose:
                console.print_exception()
            return False

    def _generate_custom_report(self) -> bool:
        """Generate custom report with user-defined sections."""
        console.print("\n[bold]Create Custom Template[/bold]\n")

        console.print("[bold]Select sections to include:[/bold]\n")

        sections = {
            "summary": Confirm.ask("  Include summary section?", default=True),
            "compliance": Confirm.ask("  Include compliance metrics?", default=True),
            "charts": Confirm.ask("  Include charts?", default=True),
            "tables": Confirm.ask("  Include data tables?", default=True),
            "recommendations": Confirm.ask("  Include recommendations?", default=True),
        }

        console.print()

        # Ask if they want to save template
        if Confirm.ask("[bold]Save this template for future use?[/bold]", default=False):
            template_name = Prompt.ask("[bold]Template name[/bold]", default="my_custom_template")
            console.print(f"\n[green]✓[/green] Template '{template_name}' would be saved\n")

        console.print(f"[green]✓[/green] Custom report configuration created")
        console.print(f"[dim]Report would be generated with selected sections[/dim]\n")

        return True

    # ========================================================================
    # STEP 7: Save Analytics Data
    # ========================================================================

    def _step_save_analytics_data(self) -> bool:
        """Step 7: Save analytics data to file in various formats."""
        if Confirm.ask("\n[bold]Would you like to save the analytics data?[/bold]", default=True):
            self._start_step(7, "Save Analytics Data")

            console.print("[bold]Export format:[/bold]\n")
            console.print("  [cyan]1.[/cyan] JSON (recommended)")
            console.print("  [cyan]2.[/cyan] Excel (.xlsx)")
            console.print("  [cyan]3.[/cyan] CSV files (multiple)")
            console.print("  [cyan]4.[/cyan] Markdown (.md)")
            console.print("  [cyan]5.[/cyan] Text file (.txt)")
            console.print()

            choice = self._prompt_with_help(
                "[bold]Choose format[/bold]",
                choices=["1", "2", "3", "4", "5"],
                default="1",
                help_text="JSON preserves all data structure, Excel/CSV for spreadsheets"
            )

            if self._check_exit_command(choice):
                return False

            format_map = {
                "1": ("JSON", "output/analytics_data.json"),
                "2": ("Excel", "output/analytics_data.xlsx"),
                "3": ("CSV", "output/analytics_csv/"),
                "4": ("Markdown", "output/analytics_data.md"),
                "5": ("Text", "output/analytics_data.txt")
            }

            format_name, default_path = format_map.get(choice, ("JSON", "output/analytics_data.json"))

            output_path = Prompt.ask(
                f"[bold]Output path for {format_name}[/bold]",
                default=default_path
            )

            # Save data
            self._save_data_in_format(choice, Path(output_path))

            # Collapse step
            self._complete_step(7, "Save Analytics Data", f"Data exported as {format_name}")

            return True

        return False

    def _save_data_in_format(self, format_choice: str, output_path: Path):
        """Save analytics data in specified format."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if format_choice == "1":  # JSON
                # Data is already saved as JSON during analysis
                console.print(f"\n[green]✓[/green] Analytics data available at: {self.analysis_dir}")
                console.print(f"  • Portfolio: {self.analysis_dir}/portfolio_analysis.json")
                console.print(f"  • Buildings: {self.analysis_dir}/buildings/")
                console.print(f"  • Rooms: {self.analysis_dir}/rooms/\n")

            elif format_choice == "2":  # Excel
                console.print(f"\n[yellow]Excel export is under development[/yellow]")
                console.print(f"[dim]Data would be saved to: {output_path}[/dim]\n")

            elif format_choice == "3":  # CSV
                console.print(f"\n[yellow]CSV export is under development[/yellow]")
                console.print(f"[dim]Multiple CSV files would be saved to: {output_path}[/dim]\n")

            elif format_choice == "4":  # Markdown
                console.print(f"\n[yellow]Markdown export is under development[/yellow]")
                console.print(f"[dim]Data would be saved to: {output_path}[/dim]\n")

            elif format_choice == "5":  # Text
                console.print(f"\n[yellow]Text export is under development[/yellow]")
                console.print(f"[dim]Data would be saved to: {output_path}[/dim]\n")

        except Exception as e:
            console.print(f"[red]✗ Error saving data:[/red] {str(e)}\n")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _prompt_with_help(self, message: str, default: str = "", choices: List[str] = None, help_text: str = "") -> str:
        """Prompt with help option."""
        while True:
            if choices:
                response = Prompt.ask(message, choices=choices + ["help", "?"], default=default)
            else:
                response = Prompt.ask(message, default=default)

            if response.lower() == "help" or response == "?" or response.lower() == "h":
                self._show_contextual_help(help_text)
                continue

            return response

    def _show_contextual_help(self, help_text: str):
        """Show contextual help."""
        if help_text:
            console.print(f"\n[cyan]ℹ Help:[/cyan] {help_text}\n")
        else:
            self._show_general_help()

    def _show_general_help(self):
        """Show general help information."""
        help_panel = Panel.fit(
            "[bold cyan]Help - HVX IEQ Analytics[/bold cyan]\n\n"
            "[bold]Navigation:[/bold]\n"
            "  • Type 'help' at any prompt for assistance\n"
            "  • Type 'quit' or 'exit' to leave the workflow\n\n"
            "[bold]Key Concepts:[/bold]\n"
            "  • [cyan]Standards:[/cyan] Compliance rules (EN16798-1, BR18, etc.)\n"
            "  • [cyan]Filters:[/cyan] Time-based filters (opening hours, etc.)\n"
            "  • [cyan]Periods:[/cyan] Seasonal periods (heating season, etc.)\n"
            "  • [cyan]Analytics:[/cyan] Calculated metrics and compliance rates\n\n"
            "[bold]Python Environment:[/bold]\n"
            "  • [green]Recommended:[/green] Use [bold]uv[/bold] for fast, reliable Python package management\n"
            "    [dim]Install uv: pip install uv[/dim]\n"
            "    [dim]Usage: uv venv .venv && source .venv/bin/activate && uv pip install -e .[/dim]\n"
            "  • Alternatively, use [bold]python -m venv[/bold] and pip as usual\n\n"
            "[bold]Support:[/bold]\n"
            "  • Documentation: docs/\n"
            "  • Issues: github.com/hvx/ieq-analytics/issues\n"
            "  • Email: support@hvx.com",
            border_style="cyan"
        )
        console.print()
        console.print(help_panel)
        console.print()

    def _show_error_specific_help(self, error_context: str):
        """Show help specific to error context."""
        help_messages = {
            "directory_not_found": "Make sure the path exists and is accessible. Use absolute paths if needed.",
            "invalid_structure": "Your data should be organized with building folders containing sensor CSV files.",
            "loading_error": (
                "Check that CSV files are properly formatted with timestamp and value columns.\n\n"
                "[bold]If you have trouble installing dependencies, try using [green]uv[/green]:[/bold]\n"
                "  pip install uv\n"
                "  uv venv .venv && source .venv/bin/activate && uv pip install -e .\n"
                "See https://github.com/astral-sh/uv for more info."
            ),
            "analytics_error": "Verify that your data has valid timestamps and numeric values."
        }

        message = help_messages.get(error_context, "Please check the documentation for troubleshooting.")
        console.print(f"\n[cyan]ℹ Help:[/cyan] {message}\n")

    def _check_exit_command(self, response: str) -> bool:
        """Check if user wants to exit."""
        if response.lower() in ["quit", "exit", "q"]:
            return self._confirm_exit()
        return False

    def _confirm_exit(self) -> bool:
        """Confirm exit with user."""
        if Confirm.ask("\n[yellow]Are you sure you want to exit? Unsaved progress will be lost.[/yellow]", default=False):
            console.print("\n[dim]Exiting workflow...[/dim]\n")
            return True
        return False

    def _offer_help_or_retry(self, error_context: str) -> bool:
        """Offer help or retry after an error."""
        console.print("[bold]What would you like to do?[/bold]\n")
        console.print("  1. Try again")
        console.print("  2. Get help")
        console.print("  3. Report issue on GitHub")
        console.print("  4. Contact support")
        console.print("  5. Exit workflow")
        console.print()

        choice = Prompt.ask("[bold]Choose option[/bold]", choices=["1", "2", "3", "4", "5"], default="1")

        if choice == "1":
            return True
        elif choice == "2":
            self._show_error_specific_help(error_context)
            return self._offer_help_or_retry(error_context)
        elif choice == "3":
            self._open_github_issue(error_context)
            return False
        elif choice == "4":
            self._show_support_contact(error_context)
            return False
        else:
            return False

    def _show_error_specific_help(self, error_context: str):
        """Show help specific to error context."""
        help_messages = {
            "directory_not_found": "Make sure the path exists and is accessible. Use absolute paths if needed.",
            "invalid_structure": "Your data should be organized with building folders containing sensor CSV files.",
            "loading_error": (
                "Check that CSV files are properly formatted with timestamp and value columns.\n\n"
                "[bold]If you have trouble installing dependencies, try using [green]uv[/green]:[/bold]\n"
                "  pip install uv\n"
                "  uv venv .venv && source .venv/bin/activate && uv pip install -e .\n"
                "See https://github.com/astral-sh/uv for more info."
            ),
            "analytics_error": "Verify that your data has valid timestamps and numeric values."
        }

        message = help_messages.get(error_context, "Please check the documentation for troubleshooting.")
        console.print(f"\n[cyan]ℹ Help:[/cyan] {message}\n")

    def _open_github_issue(self, error_context: str):
        """Provide GitHub issue template."""
        console.print("\n[bold cyan]Report Issue on GitHub[/bold cyan]\n")
        console.print("Please create an issue at:")
        console.print("[link]https://github.com/bruadam/hvx/issues/new[/link]\n")
        console.print(f"[dim]Error context: {error_context}[/dim]\n")

    def _show_support_contact(self, error_context: str):
        """Show support contact information."""
        console.print("\n[bold cyan]Contact Support[/bold cyan]\n")
        console.print("Email: bruno.adam@pm.me")
        console.print(f"Subject: IEQ Analytics Error - {error_context}\n")
        console.print("[dim]Please include details about what you were trying to do.[/dim]\n")

    def _handle_workflow_exit(self, step: str):
        """Handle workflow exit at specific step."""
        console.print(f"\n[yellow]Workflow exited at: {step}[/yellow]\n")

    def _handle_keyboard_interrupt(self):
        """Handle keyboard interrupt (Ctrl+C)."""
        console.print("\n\n[yellow]Workflow interrupted by user (Ctrl+C)[/yellow]")
        if self.workflow_state != "init":
            console.print(f"[dim]Current state: {self.workflow_state}[/dim]")
            console.print(f"[dim]Partial results may be available at: {self.analysis_dir}[/dim]")
        console.print()

    def _handle_error(self, error: Exception):
        """Handle unexpected errors gracefully."""
        console.print(f"\n[bold red]✗ Unexpected Error:[/bold red] {str(error)}\n")

        if self.verbose:
            console.print_exception()

        console.print("[bold]This is a serious error. What would you like to do?[/bold]\n")
        console.print("  1. Report issue on GitHub")
        console.print("  2. Contact support")
        console.print("  3. Exit")
        console.print()

        choice = Prompt.ask("[bold]Choose option[/bold]", choices=["1", "2", "3"], default="3")

        if choice == "1":
            self._open_github_issue("unexpected_error")
        elif choice == "2":
            self._show_support_contact("unexpected_error")

    def _show_completion(self):
        """Show workflow completion message."""
        # Show final collapsed progress
        self._clear_and_show_progress()

        console.print()
        completion_panel = Panel.fit(
            "[bold green]✓ Workflow Complete![/bold green]\n\n"
            "[bold]Summary:[/bold]\n"
            f"  • Data loaded from: {self.data_directory}\n"
            f"  • Analytics processed and saved to: {self.analysis_dir}\n"
            f"  • Workflow state: {self.workflow_state}\n\n"
            "[bold]Next Steps:[/bold]\n"
            "  • Review results in the output directory\n"
            "  • Run 'hvx ieq start' to start a new analysis\n"
            "  • Check documentation for advanced features\n\n"
            "[dim]Thank you for using HVX IEQ Analytics![/dim]",
            border_style="green"
        )

        console.print(completion_panel)
        console.print()

