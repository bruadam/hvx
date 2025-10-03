"""
Simplified workflow for end users - focuses on viewing results, not technical details.

This workflow auto-loads data, runs analysis in the background, and immediately
shows portfolio and building results with arrow-key navigation.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from time import sleep

import inquirer
from inquirer.themes import GreenPassion
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich import box

console = Console()


def launch_simplified_workflow(
    dataset: Optional[Path] = None,
    analysis: Optional[Path] = None,
    verbose: bool = False
):
    """
    Launch simplified workflow for end users.
    
    Auto-loads data, runs analysis, and presents results in user-friendly format.
    Uses arrow keys for building/room selection.
    
    Args:
        dataset: Optional path to existing dataset file
        analysis: Optional path to existing analysis directory
        verbose: Show detailed output
    """
    workflow = SimplifiedWorkflow(dataset, analysis, verbose)
    workflow.run()


class SimplifiedWorkflow:
    """Simplified workflow for non-technical users."""
    
    def __init__(
        self,
        dataset_path: Optional[Path] = None,
        analysis_path: Optional[Path] = None,
        verbose: bool = False
    ):
        self.dataset_path = dataset_path
        self.analysis_path = analysis_path
        self.verbose = verbose
        self.dataset = None
        # analysis_dir may be None until analysis is run or an existing path is provided
        self.analysis_dir: Optional[Path] = None
        self.portfolio_data = None
        self.buildings_data = {}
        self.building_type = None  # For BR18 compliance
    
    def run(self):
        """Main workflow execution."""
        try:
            # Step 1: Auto-load data (no prompts, just progress bar)
            self._auto_load_data()
            
            # Step 1.5: Ask about building type for BR18 compliance
            self._ask_building_type()
            
            # Step 2: Auto-run analysis (no prompts, just progress bar)
            self._auto_run_analysis()
            
            # Step 3: Show results with simple navigation
            self._show_results_dashboard()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            if self.verbose:
                console.print_exception()
    
    def _auto_load_data(self):
        """Automatically load data without user prompts."""
        console.print("\n[bold cyan]📂 Loading Building Data...[/bold cyan]\n")
        
        from src.core.services.data_loader_service import create_data_loader
        from src.core.models import BuildingDataset
        
        # Check if dataset file exists
        if self.dataset_path and self.dataset_path.exists():
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}[/cyan]"),
                console=console
            ) as progress:
                task = progress.add_task("Loading saved dataset...", total=None)
                self.dataset = BuildingDataset.load_from_pickle(self.dataset_path)
                progress.update(task, completed=True)
            
            console.print(f"[green]✓[/green] Loaded from: {self.dataset_path.name}")
        
        else:
            # Auto-detect data directory
            data_dirs = [
                Path("data/samples/sample-extensive-data"),
                Path("data"),
                Path(".")
            ]
            
            data_dir = None
            for d in data_dirs:
                if d.exists() and d.is_dir():
                    # Check if it has building data
                    if list(d.glob("building-*")) or list(d.glob("*/sensors")):
                        data_dir = d
                        break
            
            if not data_dir:
                console.print("[yellow]No data directory found. Please specify with --source-dir[/yellow]")
                return
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}[/cyan]"),
                console=console
            ) as progress:
                task = progress.add_task(f"Loading data from {data_dir}...", total=None)
                
                loader = create_data_loader(
                    auto_infer_levels=True,
                    auto_infer_room_types=True
                )
                self.dataset = loader.load_from_directory(data_dir, validate=True)
                
                # Auto-save for future use
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                dataset_file = output_dir / "dataset.pkl"
                self.dataset.save_to_pickle(dataset_file)
                self.dataset_path = dataset_file
                
                progress.update(task, completed=True)
            
            console.print(f"[green]✓[/green] Loaded {self.dataset.get_building_count()} buildings, "
                         f"{self.dataset.get_total_room_count()} rooms")
    
    def _ask_building_type(self):
        """Ask user about building type for BR18 compliance assessment."""
        if not self.dataset:
            return
        
        console.print("\n[bold cyan]🏢 Building Type Classification[/bold cyan]")
        console.print("\n[dim]To apply BR18 Danish Building Regulations correctly,[/dim]")
        console.print("[dim]please specify your building type:[/dim]\n")
        
        # Create info panel
        info_text = """[bold yellow]BR18 Temperature Limits:[/bold yellow]

[bold]Office Buildings & Schools:[/bold]
  • Max 100 hours/year above 26°C during usage time
  • Max 25 hours/year above 27°C during usage time

[bold]Residential (Natural Ventilation):[/bold]
  • Max 100 hours/year above 27°C
  • Max 25 hours/year above 28°C
  • Requires operable windows for cross-ventilation

[bold]Other Buildings:[/bold]
  • Building owner determines limits
  • Standard office limits often apply
"""
        console.print(Panel(info_text.strip(), border_style="cyan", box=box.ROUNDED))
        
        choices = [
            "Office building or school (offices, classrooms, commercial spaces)",
            "Residential building with natural ventilation (operable windows)",
            "Other building type (custom requirements)",
            "Skip BR18 classification (standard tests only)"
        ]
        
        questions = [
            inquirer.List(
                'building_type',
                message="Select your building type",
                choices=choices,
                carousel=True
            ),
        ]
        
        try:
            answer = inquirer.prompt(questions, theme=GreenPassion())
            if not answer:
                self.building_type = 'skip'
                return
            
            choice = answer['building_type']
            
            if 'Office' in choice:
                self.building_type = 'office'
                console.print("\n[green]✓[/green] Building type set to: [bold]Office/School[/bold]")
                console.print("[dim]  → Applying BR18 office limits (100h >26°C, 25h >27°C)[/dim]")
            elif 'Residential' in choice:
                self.building_type = 'residential'
                console.print("\n[green]✓[/green] Building type set to: [bold]Residential (Natural Ventilation)[/bold]")
                console.print("[dim]  → Applying BR18 residential limits (100h >27°C, 25h >28°C)[/dim]")
            elif 'Other' in choice:
                self.building_type = 'other'
                console.print("\n[green]✓[/green] Building type set to: [bold]Other[/bold]")
                console.print("[dim]  → Applying office limits as baseline (can be customized)[/dim]")
            else:
                self.building_type = 'skip'
                console.print("\n[yellow]○[/yellow] BR18 classification skipped")
                console.print("[dim]  → Standard temperature tests will be applied[/dim]")
        
        except KeyboardInterrupt:
            self.building_type = 'skip'
            console.print("\n[yellow]○[/yellow] BR18 classification skipped")
    
    def _auto_run_analysis(self):
        """Automatically run analysis without user prompts."""
        
        # Check if analysis already exists
        if self.analysis_path and self.analysis_path.exists():
            console.print(f"\n[green]✓[/green] Using existing analysis: {self.analysis_path.name}")
            self.analysis_dir = self.analysis_path
            self._load_analysis_results()
            return
        
        console.print("\n[bold cyan]📊 Analyzing Building Performance...[/bold cyan]\n")
        
        from src.core.services.hierarchical_analysis_service import HierarchicalAnalysisService
        
        # Auto-determine output directory
        self.analysis_dir = Path("output/analysis")

        if self.dataset is None:
            console.print("[red]Error: No dataset loaded. Cannot run analysis.[/red]")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}[/cyan]"),
            console=console
        ) as progress:
            task = progress.add_task("Running analysis (this may take a minute)...", total=None)
            
            service = HierarchicalAnalysisService()
            results = service.analyze_dataset(
                dataset=self.dataset,
                output_dir=self.analysis_dir,
                portfolio_name='Portfolio',
                verbose=self.verbose
            )
            
            progress.update(task, completed=True)
        
        console.print(f"[green]✓[/green] Analysis complete!")
        
        # Load results
        self._load_analysis_results()
    
    def _load_analysis_results(self):
        """Load analysis results from files."""
        from src.core.models import PortfolioAnalysis, BuildingAnalysis

        if self.analysis_dir is None:
            console.print("[yellow]No analysis directory found. Cannot load analysis results.[/yellow]")
            return

        # Load portfolio
        analysis_dir = self.analysis_dir
        portfolio_file = analysis_dir / "portfolio_analysis.json"
        if portfolio_file.exists():
            self.portfolio_data = PortfolioAnalysis.load_from_json(portfolio_file)

        # Load buildings
        buildings_dir = analysis_dir / "buildings"
        if buildings_dir.exists():
            for building_file in buildings_dir.glob("*.json"):
                try:
                    building = BuildingAnalysis.load_from_json(building_file)
                    self.buildings_data[building.building_id] = building
                except Exception:
                    pass
    
    def _show_results_dashboard(self):
        """Show main results dashboard with simple navigation."""
        while True:
            console.clear()
            
            # Show portfolio summary
            self._display_portfolio_summary()
            
            # Simple menu
            console.print("\n[bold]What would you like to do?[/bold]\n")
            
            choices = [
                "View building details",
                "View portfolio recommendations",
                "Export report (PDF)",
                "Exit"
            ]
            
            questions = [
                inquirer.List(
                    'action',
                    message="Select an option",
                    choices=choices,
                    carousel=True
                ),
            ]
            
            try:
                answer = inquirer.prompt(questions, theme=GreenPassion())
                if not answer:
                    break
                
                action = answer['action']
                
                if action == choices[0]:  # View building details
                    self._navigate_buildings()
                elif action == choices[1]:  # View recommendations
                    self._show_portfolio_recommendations()
                elif action == choices[2]:  # Export report
                    self._export_report()
                elif action == choices[3]:  # Exit
                    break
            
            except KeyboardInterrupt:
                break
        
        console.print("\n[bold green]Thank you for using HVX Building Analytics![/bold green]\n")
    
    def _display_portfolio_summary(self):
        """Display high-level portfolio summary."""
        console.print("\n[bold cyan]📊 Portfolio Overview[/bold cyan]\n")
        
        if not self.portfolio_data:
            console.print("[yellow]No portfolio data available[/yellow]")
            return
        
        # Key metrics in a clean panel
        metrics = f"""
[bold]Buildings:[/bold] {self.portfolio_data.building_count}
[bold]Total Rooms:[/bold] {self.portfolio_data.total_room_count}
[bold]Overall Compliance:[/bold] {self._format_compliance(self.portfolio_data.avg_compliance_rate)}
[bold]Data Quality:[/bold] {self._format_quality(self.portfolio_data.avg_quality_score)}
        """
        
        console.print(Panel(metrics.strip(), border_style="cyan", box=box.ROUNDED))
        
        # Smart Recommendations across portfolio
        self._show_portfolio_smart_recommendations()
    
    def _show_portfolio_smart_recommendations(self):
        """Display smart recommendations across the entire portfolio grouped by type."""
        if self.analysis_dir is None:
            return
        
        from src.core.services.smart_recommendations_service import SmartRecommendationsService
        from src.core.models import RoomAnalysis
        
        # Load all room analyses from all buildings
        if self.analysis_dir is None:
            console.print("[yellow]No analysis directory found. Cannot load recommendations.[/yellow]")
            input("\nPress Enter to continue...")
            return
        analysis_dir = self.analysis_dir
        rooms_dir = analysis_dir / 'rooms'
        if not rooms_dir.exists():
            return
        
        all_room_analyses = {}
        for room_file in rooms_dir.glob("*.json"):
            try:
                room = RoomAnalysis.load_from_json(room_file)
                all_room_analyses[room.room_id] = room
            except Exception:
                continue
        
        if not all_room_analyses:
            return
        
        # Generate recommendations for each room and group by title
        service = SmartRecommendationsService()
        rec_by_title = {}
        
        for room_id, room in all_room_analyses.items():
            recommendations = service.generate_recommendations(room)
            
            for rec in recommendations:
                title = rec.title
                if title not in rec_by_title:
                    rec_by_title[title] = {
                        'type': rec.type.value,
                        'priority': rec.priority.value,
                        'rooms': [],
                        'room_names': []
                    }
                rec_by_title[title]['rooms'].append(room_id)
                rec_by_title[title]['room_names'].append(room.room_name)
        
        if not rec_by_title:
            return
        
        console.print("\n[bold cyan]� Smart Recommendations Across Portfolio[/bold cyan]\n")
        
        # Group recommendations by type
        by_type = {}
        for title, data in rec_by_title.items():
            rec_type = data['type']
            if rec_type not in by_type:
                by_type[rec_type] = []
            by_type[rec_type].append({
                'title': title,
                'rooms': data['room_names'],
                'priority': data['priority']
            })
        
        # Define type metadata
        type_config = {
            'solar_shading': {'emoji': '☀️', 'name': 'Solar Shading', 'color': 'yellow'},
            'insulation': {'emoji': '🏠', 'name': 'Insulation', 'color': 'cyan'},
            'mechanical_ventilation': {'emoji': '💨', 'name': 'Mechanical Ventilation', 'color': 'blue'},
            'natural_ventilation': {'emoji': '🌬️', 'name': 'Natural Ventilation', 'color': 'green'},
            'hvac_control': {'emoji': '🎛️', 'name': 'HVAC Control', 'color': 'magenta'},
            'occupancy_management': {'emoji': '👥', 'name': 'Occupancy Management', 'color': 'white'}
        }
        
        # Display each type with its recommendations
        for rec_type, recs in sorted(by_type.items()):
            config = type_config.get(rec_type, {'emoji': '•', 'name': rec_type.replace('_', ' ').title(), 'color': 'white'})
            
            total_rooms = sum(len(r['rooms']) for r in recs)
            
            console.print(f"[bold {config['color']}]{config['emoji']}  {config['name']} ({total_rooms} rooms)[/bold {config['color']}]")
            console.print("─" * 60)
            console.print()
            
            # Sort recommendations by number of affected rooms (descending)
            recs_sorted = sorted(recs, key=lambda x: len(x['rooms']), reverse=True)
            
            for rec in recs_sorted:
                title = rec['title']
                rooms = rec['rooms']
                
                console.print(f"  [bold]• {title}[/bold]")
                
                # Show first 3 rooms, then count remaining
                display_limit = 3
                for i, room_name in enumerate(rooms[:display_limit]):
                    console.print(f"    → {room_name}")
                
                if len(rooms) > display_limit:
                    console.print(f"    [dim]... and {len(rooms) - display_limit} more rooms[/dim]")
                
                console.print()
            
            console.print()
    
    def _format_compliance(self, rate: float) -> str:
        """Format compliance rate with color."""
        if rate >= 90:
            return f"[green]{rate:.1f}%[/green] ✓ Excellent"
        elif rate >= 75:
            return f"[cyan]{rate:.1f}%[/cyan] ◐ Good"
        elif rate >= 50:
            return f"[yellow]{rate:.1f}%[/yellow] ◔ Fair"
        else:
            return f"[red]{rate:.1f}%[/red] ✗ Needs Attention"
    
    def _format_quality(self, score: float) -> str:
        """Format quality score with color."""
        if score >= 90:
            return f"[green]{score:.1f}%[/green] ✓ High"
        elif score >= 70:
            return f"[cyan]{score:.1f}%[/cyan] ~ Medium"
        else:
            return f"[yellow]{score:.1f}%[/yellow] ⚠ Low"
    
    def _navigate_buildings(self):
        """Navigate through buildings using arrow keys."""
        if not self.buildings_data:
            console.print("\n[yellow]No building data available[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        while True:
            console.clear()
            console.print("\n[bold cyan]🏢 Select a Building[/bold cyan]\n")
            
            # Create building choices with summary info
            building_choices = []
            for building_id, building in sorted(self.buildings_data.items()):
                label = f"{building.building_name} - {building.room_count} rooms - {building.avg_compliance_rate:.1f}% compliance"
                building_choices.append(label)
            
            building_choices.append("← Back to main menu")
            
            questions = [
                inquirer.List(
                    'building',
                    message="Choose a building to explore",
                    choices=building_choices,
                    carousel=True
                ),
            ]
            
            try:
                answer = inquirer.prompt(questions, theme=GreenPassion())
                if not answer or answer['building'] == "← Back to main menu":
                    break
                
                # Find selected building
                selected_label = answer['building']
                for building_id, building in self.buildings_data.items():
                    label = f"{building.building_name} - {building.room_count} rooms - {building.avg_compliance_rate:.1f}% compliance"
                    if label == selected_label:
                        self._show_building_details(building)
                        break
            
            except KeyboardInterrupt:
                break
    
    def _show_building_details(self, building):
        """Show detailed building information with options."""
        while True:
            console.clear()
            console.print(f"\n[bold cyan]🏢 {building.building_name}[/bold cyan]\n")
            
            # Building metrics
            metrics = f"""
[bold]Rooms:[/bold] {building.room_count}
[bold]Levels:[/bold] {building.level_count}
[bold]Compliance:[/bold] {self._format_compliance(building.avg_compliance_rate)}
[bold]Quality:[/bold] {self._format_quality(building.avg_quality_score)}
            """
            console.print(Panel(metrics.strip(), border_style="cyan", box=box.ROUNDED))
            
            # Key performance indicators
            if building.test_aggregations:
                self._show_building_kpis(building)
            
            # Critical issues - consolidated view
            if building.test_aggregations:
                self._show_consolidated_critical_issues(building)
            
            # Menu options
            console.print("\n[bold]Options:[/bold]\n")
            
            choices = [
                "View rooms in this building",
                "View smart recommendations",
                "View test results",
                "← Back to building list"
            ]
            
            questions = [
                inquirer.List(
                    'action',
                    message="What would you like to do?",
                    choices=choices,
                    carousel=True
                ),
            ]
            
            try:
                answer = inquirer.prompt(questions, theme=GreenPassion())
                if not answer or answer['action'] == choices[3]:  # Back
                    break
                
                action = answer['action']
                
                if action == choices[0]:  # View rooms
                    self._navigate_rooms(building)
                elif action == choices[1]:  # Smart recommendations
                    self._show_building_recommendations(building)
                elif action == choices[2]:  # Test results
                    self._show_building_tests(building)
            
            except KeyboardInterrupt:
                break
    
    def _show_building_kpis(self, building):
        """Show key performance indicators for building."""
        console.print("\n[bold cyan]📊 Key Performance Indicators:[/bold cyan]\n")
        
        # Pinned tests - base tests always shown
        pinned_tests = {
            'co2_1000_all_year_opening': 'CO₂ < 1000 ppm',
            'co2_2000_all_year_opening': 'CO₂ < 2000 ppm',
            'temp_below_20_all_year_opening': 'Temperature ≥ 20°C',
            'temp_above_26_all_year_opening': 'Temperature ≤ 26°C',
            'temp_above_27_all_year_opening': 'Temperature ≤ 27°C'
        }
        
        # Add BR18 tests based on building type selection
        if self.building_type == 'office' or self.building_type == 'other':
            pinned_tests['br18_office_temp_above_26_max_100h'] = 'BR18 Office: ≤100h >26°C'
            pinned_tests['br18_office_temp_above_27_max_25h'] = 'BR18 Office: ≤25h >27°C'
        elif self.building_type == 'residential':
            pinned_tests['br18_residential_temp_above_27_max_100h'] = 'BR18 Residential: ≤100h >27°C'
            pinned_tests['br18_residential_temp_above_28_max_25h'] = 'BR18 Residential: ≤25h >28°C'
        
        table = Table(box=box.SIMPLE, show_header=False, show_edge=False)
        table.add_column("Test", style="white", width=35)
        table.add_column("Result", style="white", width=30)
        
        for test_id, test_name in pinned_tests.items():
            if test_id in building.test_aggregations:
                test_data = building.test_aggregations[test_id]
                compliance = test_data.get('avg_compliance_rate', test_data.get('average_compliance', 0))
                
                # Check if this is a BR18 test with hour tolerance
                is_br18 = 'br18' in test_id.lower()
                if is_br18:
                    # BR18 tests: show binary PASS/FAIL with actual exceedance hours
                    avg_exceedance_hours = test_data.get('avg_non_compliant_hours', 0)
                    # Extract max allowed hours from test name
                    max_hours = 100 if '100h' in test_id else 25 if '25h' in test_id else 0
                    
                    # Check actual hours vs limit (more reliable than compliance % which might be from old analysis)
                    is_passing = avg_exceedance_hours <= max_hours
                    
                    if is_passing:
                        status = f"[green]PASS[/green] ({avg_exceedance_hours:.0f}/{max_hours}h)"
                    else:
                        status = f"[red]FAIL[/red] ({avg_exceedance_hours:.0f}/{max_hours}h)"
                else:
                    # Standard tests: show percentage
                    if compliance >= 90:
                        status = f"[green]{compliance:.1f}%[/green] ✓"
                    elif compliance >= 75:
                        status = f"[cyan]{compliance:.1f}%[/cyan] ◐"
                    elif compliance >= 50:
                        status = f"[yellow]{compliance:.1f}%[/yellow] ◔"
                    else:
                        status = f"[red]{compliance:.1f}%[/red] ✗"
                
                table.add_row(test_name, status)
        
        console.print(table)
    
    def _show_consolidated_critical_issues(self, building):
        """Show critical issues grouped by parameter type (CO2, Temperature, BR18 Regulations)."""
        # Group tests by parameter and threshold
        co2_tests = {}
        temp_tests = {}
        br18_tests = {}
        
        for test_id, test_data in building.test_aggregations.items():
            compliance = test_data.get('avg_compliance_rate', test_data.get('average_compliance', 0))
            
            # Check for BR18 tests (show even if not critical, as they have specific hour limits)
            if 'br18' in test_id.lower():
                br18_tests[test_id] = {
                    'compliance': compliance,
                    'data': test_data
                }
                continue
            
            # Only show critical issues (< 50% compliance) for other tests
            if compliance >= 50:
                continue
            
            # Parse test information
            if 'co2' in test_id.lower():
                # Extract threshold (1000 or 2000)
                threshold = '1000' if '1000' in test_id else '2000' if '2000' in test_id else 'unknown'
                
                # Extract period (season and/or time of day)
                period_parts = []
                if 'spring' in test_id:
                    period_parts.append('Spring')
                elif 'summer' in test_id:
                    period_parts.append('Summer')
                elif 'autumn' in test_id:
                    period_parts.append('Autumn')
                elif 'winter' in test_id:
                    period_parts.append('Winter')
                elif 'all_year' in test_id:
                    period_parts.append('All year')
                else:
                    # If no season, assume all year
                    period_parts.append('All year')
                
                # Add time of day if present
                if 'morning' in test_id:
                    period_parts.append('morning')
                elif 'afternoon' in test_id:
                    period_parts.append('afternoon')
                elif 'evening' in test_id:
                    period_parts.append('evening')
                
                period = ' '.join(period_parts) if period_parts else None
                
                if threshold not in co2_tests:
                    co2_tests[threshold] = {}
                if period:
                    co2_tests[threshold][period] = compliance
            
            elif 'temp' in test_id.lower():
                # Extract threshold and type (above/below)
                threshold = None
                direction = None
                
                if 'above_26' in test_id or 'max_26' in test_id:
                    threshold = '26'
                    direction = 'above'
                elif 'above_27' in test_id or 'max_27' in test_id:
                    threshold = '27'
                    direction = 'above'
                elif 'below_20' in test_id or 'min_20' in test_id:
                    threshold = '20'
                    direction = 'below'
                elif 'below_18' in test_id or 'min_18' in test_id:
                    threshold = '18'
                    direction = 'below'
                
                # Extract period (season and/or time of day)
                period_parts = []
                if 'spring' in test_id:
                    period_parts.append('Spring')
                elif 'summer' in test_id:
                    period_parts.append('Summer')
                elif 'autumn' in test_id:
                    period_parts.append('Autumn')
                elif 'winter' in test_id:
                    period_parts.append('Winter')
                elif 'all_year' in test_id:
                    period_parts.append('All year')
                else:
                    # If no season, assume all year
                    period_parts.append('All year')
                
                # Add time of day if present
                if 'morning' in test_id:
                    period_parts.append('morning')
                elif 'afternoon' in test_id:
                    period_parts.append('afternoon')
                elif 'evening' in test_id:
                    period_parts.append('evening')
                
                period = ' '.join(period_parts) if period_parts else None
                
                if threshold and direction:
                    key = f"{direction}_{threshold}"
                    if key not in temp_tests:
                        temp_tests[key] = {}
                    if period:
                        temp_tests[key][period] = compliance
        
        # Display consolidated issues
        if not co2_tests and not temp_tests:
            return
        
        console.print("\n[bold red]🚨 Critical Issues:[/bold red]\n")
        
        # CO2 Issues
        if co2_tests:
            console.print("[bold yellow]💨 CO₂ Levels:[/bold yellow]")
            for threshold in sorted(co2_tests.keys()):
                periods_data = co2_tests[threshold]
                
                # Check if all periods are present
                all_periods = {'All year', 'Spring', 'Summer', 'Autumn', 'Winter'}
                has_all_year = 'All year' in periods_data
                has_all_seasons = {'Spring', 'Summer', 'Autumn', 'Winter'}.issubset(periods_data.keys())
                
                if has_all_year or has_all_seasons:
                    # Show average across all periods
                    avg_compliance = sum(periods_data.values()) / len(periods_data)
                    console.print(f"  • <{threshold} ppm: [red]All periods affected[/red] ([red]{avg_compliance:.1f}% avg[/red])")
                else:
                    # Show specific periods
                    period_strs = [f"{period} ({comp:.1f}%)" for period, comp in sorted(periods_data.items())]
                    console.print(f"  • <{threshold} ppm: [red]{', '.join(period_strs)}[/red]")
                
                # Add recommendation
                if threshold == '1000':
                    console.print("    [dim]→ Recommendation: Increase ventilation rates or reduce occupancy[/dim]")
            
            console.print()
        
        # Temperature Issues
        if temp_tests:
            console.print("[bold yellow]🌡️  Temperature:[/bold yellow]")
            for key in sorted(temp_tests.keys()):
                direction, threshold = key.split('_')
                periods_data = temp_tests[key]
                
                # Check if all periods are present
                has_all_year = 'All year' in periods_data
                has_all_seasons = {'Spring', 'Summer', 'Autumn', 'Winter'}.issubset(periods_data.keys())
                
                symbol = '>' if direction == 'above' else '<'
                
                if has_all_year or has_all_seasons:
                    avg_compliance = sum(periods_data.values()) / len(periods_data)
                    console.print(f"  • {symbol}{threshold}°C: [red]All periods affected[/red] ([red]{avg_compliance:.1f}% avg[/red])")
                else:
                    period_strs = [f"{period} ({comp:.1f}%)" for period, comp in sorted(periods_data.items())]
                    console.print(f"  • {symbol}{threshold}°C: [red]{', '.join(period_strs)}[/red]")
                
                # Add recommendations based on issue type
                if direction == 'above' and threshold in ['26', '27']:
                    console.print("    [dim]→ Recommendation: Install solar shading or improve cooling[/dim]")
                elif direction == 'below' and threshold in ['18', '20']:
                    console.print("    [dim]→ Recommendation: Improve insulation or heating system[/dim]")
            
            console.print()
        
        # BR18 Danish Building Regulations (filter by selected building type)
        if br18_tests and self.building_type and self.building_type != 'skip':
            console.print("[bold yellow]📋 BR18 Danish Building Regulations:[/bold yellow]")
            
            # Filter by building type selection
            office_tests = {k: v for k, v in br18_tests.items() if 'office' in k}
            residential_tests = {k: v for k, v in br18_tests.items() if 'residential' in k}
            
            # Only show relevant tests based on building type
            show_office = self.building_type in ['office', 'other']
            show_residential = self.building_type == 'residential'
            
            if office_tests and show_office:
                console.print("\n  [bold]Office Buildings:[/bold]")
                for test_id, test_info in sorted(office_tests.items()):
                    compliance = test_info['compliance']
                    test_data = test_info['data']
                    avg_exceedance_hours = test_data.get('avg_non_compliant_hours', 0)
                    
                    # Extract info
                    if '26_max_100h' in test_id:
                        limit_desc = ">26°C (max 100h/year)"
                        max_hours = 100
                        is_passing = avg_exceedance_hours <= max_hours
                        status = f"[green]✓ PASS ({avg_exceedance_hours:.0f}/{max_hours}h)[/green]" if is_passing else f"[red]✗ FAIL ({avg_exceedance_hours:.0f}/{max_hours}h)[/red]"
                    elif '27_max_25h' in test_id:
                        limit_desc = ">27°C (max 25h/year)"
                        max_hours = 25
                        is_passing = avg_exceedance_hours <= max_hours
                        status = f"[green]✓ PASS ({avg_exceedance_hours:.0f}/{max_hours}h)[/green]" if is_passing else f"[red]✗ FAIL ({avg_exceedance_hours:.0f}/{max_hours}h)[/red]"
                    else:
                        continue
                    
                    console.print(f"    • {limit_desc}: {status}")
                
                # Check if any tests are failing based on actual hours
                any_failing = any(
                    test_data.get('avg_non_compliant_hours', 0) > (100 if '100h' in test_id else 25)
                    for test_id, test_info in office_tests.items()
                    for test_data in [test_info['data']]
                )
                if any_failing:
                    console.print("      [dim]→ Recommendation: Install solar shading or improve HVAC controls[/dim]")
            
            if residential_tests and show_residential:
                console.print("\n  [bold]Residential (Natural Ventilation):[/bold]")
                for test_id, test_info in sorted(residential_tests.items()):
                    compliance = test_info['compliance']
                    test_data = test_info['data']
                    avg_exceedance_hours = test_data.get('avg_non_compliant_hours', 0)
                    
                    # Extract info
                    if '27_max_100h' in test_id:
                        limit_desc = ">27°C (max 100h/year)"
                        max_hours = 100
                        is_passing = avg_exceedance_hours <= max_hours
                        status = f"[green]✓ PASS ({avg_exceedance_hours:.0f}/{max_hours}h)[/green]" if is_passing else f"[red]✗ FAIL ({avg_exceedance_hours:.0f}/{max_hours}h)[/red]"
                    elif '28_max_25h' in test_id:
                        limit_desc = ">28°C (max 25h/year)"
                        max_hours = 25
                        is_passing = avg_exceedance_hours <= max_hours
                        status = f"[green]✓ PASS ({avg_exceedance_hours:.0f}/{max_hours}h)[/green]" if is_passing else f"[red]✗ FAIL ({avg_exceedance_hours:.0f}/{max_hours}h)[/red]"
                    else:
                        continue
                    
                    console.print(f"    • {limit_desc}: {status}")
                
                # Check if any tests are failing based on actual hours
                any_failing = any(
                    test_data.get('avg_non_compliant_hours', 0) > (100 if '100h' in test_id else 25)
                    for test_id, test_info in residential_tests.items()
                    for test_data in [test_info['data']]
                )
                if any_failing:
                    console.print("      [dim]→ Recommendation: Ensure operable windows for cross-ventilation, consider night cooling[/dim]")
            
            console.print()
    
    def _show_building_recommendations(self, building):
        """Show smart recommendations for the building."""
        console.clear()
        console.print(f"\n[bold cyan]💡 Smart Recommendations: {building.building_name}[/bold cyan]\n")
        
        from src.core.services.smart_recommendations_service import generate_building_recommendations_report
        from src.core.models import RoomAnalysis
        
        # Load room analyses
        room_analyses = {}
        if self.analysis_dir is None:
            console.print("[yellow]No analysis directory found. Cannot load recommendations.[/yellow]")
            input("\nPress Enter to continue...")
            return
        analysis_dir = self.analysis_dir
        rooms_dir = analysis_dir / 'rooms'
        
        if rooms_dir.exists():
            for room_id in building.room_ids:
                room_file = rooms_dir / f"{room_id}.json"
                if room_file.exists():
                    try:
                        room = RoomAnalysis.load_from_json(room_file)
                        room_analyses[room_id] = room
                    except Exception:
                        pass
        
        if not room_analyses:
            console.print("[yellow]No recommendations available[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        # Generate report
        report = generate_building_recommendations_report(room_analyses)
        
        # Group by type
        from collections import defaultdict
        recs_by_type = defaultdict(list)
        
        for room_id, recs in report.get('room_recommendations', {}).items():
            for rec in recs:
                recs_by_type[rec.type.value].append({
                    'room_id': room_id,
                    'room_name': room_analyses[room_id].room_name,
                    'rec': rec
                })
        
        # Display recommendations by type
        type_names = {
            'solar_shading': '🌞 Solar Shading',
            'insulation': '🏠 Insulation',
            'mechanical_ventilation': '💨 Mechanical Ventilation',
            'natural_ventilation': '🌬️  Natural Ventilation'
        }
        
        for type_key, type_name in type_names.items():
            if type_key in recs_by_type:
                items = recs_by_type[type_key]
                console.print(f"\n[bold]{type_name}[/bold] ({len(items)} rooms)")
                console.print("─" * 60)
                
                # Group by title
                by_title = defaultdict(list)
                for item in items:
                    by_title[item['rec'].title].append(item['room_name'])
                
                for title, rooms in list(by_title.items())[:3]:  # Show top 3
                    console.print(f"\n  • {title}")
                    if len(rooms) <= 3:
                        for room in rooms:
                            console.print(f"    → {room}")
                    else:
                        for room in rooms[:3]:
                            console.print(f"    → {room}")
                        console.print(f"    ... and {len(rooms)-3} more rooms")
        
        input("\n\nPress Enter to continue...")
    
    def _show_building_tests(self, building):
        """Show test results for building with interactive selection."""
        while True:
            console.clear()
            console.print(f"\n[bold cyan]📋 Test Results: {building.building_name}[/bold cyan]\n")
            
            if not building.test_aggregations:
                console.print("[yellow]No test results available[/yellow]")
                input("\nPress Enter to continue...")
                return
            
            # Display all tests with index
            table = Table(box=box.ROUNDED, show_header=True)
            table.add_column("#", style="dim", width=4, justify="right")
            table.add_column("Test", style="cyan", width=40)
            table.add_column("Compliance", justify="right", style="white")
            table.add_column("Rooms", justify="right", style="yellow")
            
            test_list = []
            for idx, (test_name, test_data) in enumerate(sorted(building.test_aggregations.items()), 1):
                test_list.append((test_name, test_data))
                
                compliance = test_data.get('avg_compliance_rate', test_data.get('average_compliance', 0))
                room_count = test_data.get('room_count', test_data.get('rooms_tested', 0))
                
                # Format compliance
                if compliance >= 90:
                    comp_str = f"[green]{compliance:.1f}%[/green]"
                elif compliance >= 75:
                    comp_str = f"[cyan]{compliance:.1f}%[/cyan]"
                elif compliance >= 50:
                    comp_str = f"[yellow]{compliance:.1f}%[/yellow]"
                else:
                    comp_str = f"[red]{compliance:.1f}%[/red]"
                
                # Friendly name
                friendly = test_name.replace('_all_year_opening', '').replace('_', ' ').title()
                
                table.add_row(str(idx), friendly, comp_str, str(room_count))
            
            console.print(table)
            
            # Interactive options
            console.print("\n[bold]Options:[/bold]")
            console.print("  • Enter test number to view details and graph")
            console.print("  • Press [bold]Enter[/bold] to go back\n")
            
            try:
                choice = Prompt.ask("[cyan]Select test number[/cyan]", default="")
                
                if not choice:
                    break
                
                try:
                    test_idx = int(choice) - 1
                    if 0 <= test_idx < len(test_list):
                        test_name, test_data = test_list[test_idx]
                        self._show_test_detail_and_graph(building, test_name, test_data)
                    else:
                        console.print(f"[red]Invalid selection. Please enter 1-{len(test_list)}[/red]")
                        sleep(1)
                except ValueError:
                    console.print("[red]Invalid input. Please enter a number.[/red]")
                    sleep(1)
                    
            except KeyboardInterrupt:
                break
    
    def _show_test_detail_and_graph(self, building, test_name: str, test_data: dict):
        """Show test details and generate graph for specific test."""
        console.clear()
        
        # Friendly name
        friendly_name = test_name.replace('_all_year_opening', '').replace('_', ' ').title()
        
        console.print(f"\n[bold cyan]📊 Test Details: {friendly_name}[/bold cyan]\n")
        console.print(f"[bold]Building:[/bold] {building.building_name}\n")
        
        # Test metadata
        compliance = test_data.get('avg_compliance_rate', test_data.get('average_compliance', 0))
        room_count = test_data.get('room_count', test_data.get('rooms_tested', 0))
        min_comp = test_data.get('min_compliance_rate', 0)
        max_comp = test_data.get('max_compliance_rate', 0)
        
        info = f"""
[bold]Average Compliance:[/bold] {self._format_compliance(compliance)}
[bold]Room Count:[/bold] {room_count}
[bold]Range:[/bold] {min_comp:.1f}% - {max_comp:.1f}%
[bold]Test ID:[/bold] {test_name}
        """
        console.print(Panel(info.strip(), border_style="cyan", box=box.ROUNDED))
        
        # Check if BR18 test
        is_br18 = 'br18' in test_name.lower()
        if is_br18:
            avg_exceedance_hours = test_data.get('avg_non_compliant_hours', 0)
            max_hours = 100 if '100h' in test_name else 25 if '25h' in test_name else 0
            
            console.print("\n[bold yellow]📋 BR18 Compliance:[/bold yellow]")
            if max_hours:
                is_passing = avg_exceedance_hours <= max_hours
                status = f"[green]PASS ({avg_exceedance_hours:.0f}/{max_hours}h)[/green]" if is_passing else f"[red]FAIL ({avg_exceedance_hours:.0f}/{max_hours}h)[/red]"
                console.print(f"  Status: {status}")
                console.print(f"  Average Exceedance: {avg_exceedance_hours:.0f} hours/year")
                console.print(f"  Limit: {max_hours} hours/year")
        
        # Options
        console.print("\n[bold]Options:[/bold]")
        console.print("  [bold]1.[/bold] Generate graph for this test")
        console.print("  [bold]2.[/bold] View room-by-room breakdown")
        console.print("  [bold]Enter.[/bold] Go back\n")
        
        try:
            choice = Prompt.ask("[cyan]Select option[/cyan]", default="")
            
            if choice == "1":
                self._generate_test_graph(building, test_name, friendly_name)
            elif choice == "2":
                self._show_test_room_breakdown(building, test_name, friendly_name, test_data)
                
        except KeyboardInterrupt:
            pass
    
    def _generate_test_graph(self, building, test_name: str, friendly_name: str):
        """Generate graph for a specific test across rooms."""
        console.clear()
        console.print(f"\n[bold cyan]📈 Generating Graph: {friendly_name}[/bold cyan]\n")
        
        try:
            from src.core.models import RoomAnalysis
            import pandas as pd
            import plotly.graph_objects as go
            import webbrowser
            
            # Load room analyses
            if self.analysis_dir is None:
                console.print("[yellow]No analysis directory found. Cannot generate graph.[/yellow]")
                input("\nPress Enter to continue...")
                return
            analysis_dir = self.analysis_dir
            rooms_dir = analysis_dir / 'rooms'
            room_analyses = []
            
            if rooms_dir.exists():
                for room_id in building.room_ids:
                    room_file = rooms_dir / f"{room_id}.json"
                    if room_file.exists():
                        try:
                            room = RoomAnalysis.load_from_json(room_file)
                            room_analyses.append(room)
                        except Exception:
                            pass
            
            if not room_analyses:
                console.print("[yellow]No room data available for graphing[/yellow]")
                input("\nPress Enter to continue...")
                return
            
            # Find rooms with this test that are failing
            rooms_with_test = []
            for room in room_analyses:
                if test_name in room.test_results:
                    test_result = room.test_results[test_name]
                    # Prioritize rooms with low compliance
                    if test_result.compliance_rate < 70:
                        rooms_with_test.append((room, test_result))
            
            if not rooms_with_test:
                # If no failing rooms, just take first few rooms with this test
                for room in room_analyses[:5]:
                    if test_name in room.test_results:
                        rooms_with_test.append((room, room.test_results[test_name]))
            
            if not rooms_with_test:
                console.print(f"[yellow]No rooms found with test '{test_name}'[/yellow]")
                input("\nPress Enter to continue...")
                return
            
            # Generate graph for first failing room (or first room)
            room, test_result = rooms_with_test[0]
            
            console.print(f"[cyan]Generating graph for:[/cyan] {room.room_name}")
            console.print(f"[cyan]Test:[/cyan] {friendly_name}")
            console.print(f"[cyan]Compliance:[/cyan] {test_result.compliance_rate:.1f}%\n")
            
            # Generate the graph using the same approach as analysis_explorer
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task("Generating graph...", total=None)
                
                graph_path = self._create_timeseries_graph(room, test_name, test_result)
            
            if graph_path and graph_path.exists():
                console.print(f"\n[green]✓ Graph generated successfully![/green]")
                console.print(f"[dim]Saved to: {graph_path}[/dim]")
                
                # Try to open in browser
                try:
                    webbrowser.open(f"file://{graph_path.absolute()}")
                    console.print("\n[green]Graph opened in your browser[/green]")
                except Exception:
                    console.print("\n[yellow]Please open the file manually to view the graph[/yellow]")
            else:
                console.print("\n[red]Failed to generate graph[/red]")
            
        except ImportError as e:
            console.print(f"[red]Error: Required library not available ({str(e)})[/red]")
            console.print(f"[dim]Please install plotly and pandas: pip install plotly pandas[/dim]")
        except Exception as e:
            console.print(f"[red]Error generating graph: {str(e)}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
        input("\n\nPress Enter to continue...")
    
    def _create_timeseries_graph(self, room, test_name: str, test_result):
        """Create interactive timeseries graph for a room's test result."""
        import pandas as pd
        import plotly.graph_objects as go
        
        if not self.dataset:
            console.print("[red]Dataset not available for timeseries visualization[/red]")
            return None
        
        # Find the room in the dataset
        room_obj = None
        for building in self.dataset.buildings:
            for level in building.levels:
                for r in level.rooms:
                    if r.id == room.room_id:
                        room_obj = r
                        break
                if room_obj:
                    break
            if room_obj:
                break
        
        if not room_obj:
            console.print(f"[yellow]Room {room.room_id} not found in dataset[/yellow]")
            return None
        
        # Get the parameter for this test
        parameter = test_result.parameter
        
        if parameter not in room_obj.timeseries:
            console.print(f"[yellow]Parameter {parameter} not found in room timeseries[/yellow]")
            return None
        
        # Get timeseries data
        ts_obj = room_obj.timeseries[parameter]
        
        # Extract the actual pandas Series from TimeSeriesData
        if parameter not in ts_obj.data.columns:
            console.print(f"[yellow]Parameter {parameter} not found in timeseries data columns[/yellow]")
            return None
        
        ts_data = ts_obj.data[parameter]
        
        if ts_data.empty:
            console.print(f"[yellow]No timeseries data available for {parameter}[/yellow]")
            return None
        
        # Create a simple time series plot (instead of complex heatmap)
        # This is a simplified version for the workflow
        
        # Determine threshold
        threshold = None
        if test_result.threshold is not None:
            if isinstance(test_result.threshold, (int, float)):
                threshold = float(test_result.threshold)
            elif isinstance(test_result.threshold, dict):
                for key in ['max', 'min', 'value', 'limit']:
                    if key in test_result.threshold:
                        try:
                            threshold = float(test_result.threshold[key])
                            break
                        except (ValueError, TypeError):
                            continue
        
        # Create figure
        fig = go.Figure()
        
        # Add actual data trace
        fig.add_trace(go.Scatter(
            x=ts_data.index,
            y=ts_data.values,
            mode='lines',
            name=parameter,
            line=dict(color='blue', width=1)
        ))
        
        # Add threshold line if available
        if threshold is not None:
            fig.add_trace(go.Scatter(
                x=[ts_data.index[0], ts_data.index[-1]],
                y=[threshold, threshold],
                mode='lines',
                name=f'Threshold: {threshold}',
                line=dict(color='red', width=2, dash='dash')
            ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f"{room.room_name} - {test_name}<br><sub>{parameter} Time Series</sub>",
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="Date",
            yaxis_title=parameter,
            template='plotly_white',
            height=600,
            hovermode='x unified'
        )
        
        # Add compliance annotation
        compliance_text = (
            f"Compliance: {test_result.compliance_rate:.1f}%<br>"
            f"Hours: {test_result.compliant_hours}/{test_result.total_hours}"
        )
        
        fig.add_annotation(
            text=compliance_text,
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.98,
            showarrow=False,
            bgcolor="white",
            bordercolor="gray",
            borderwidth=1,
            borderpad=10,
            align="left",
            xanchor="left",
            yanchor="top"
        )
        
        # Save the graph
        output_dir = Path("output/graphs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{room.room_id}_{test_name.replace(' ', '_')}.html"
        
        fig.write_html(str(output_file))
        
        return output_file
    
    def _show_test_room_breakdown(self, building, test_name: str, friendly_name: str, test_data: dict):
        """Show room-by-room breakdown for a test."""
        console.clear()
        console.print(f"\n[bold cyan]📋 Room Breakdown: {friendly_name}[/bold cyan]\n")
        
        try:
            from src.core.models import RoomAnalysis
            
            # Load room analyses
            if self.analysis_dir is None:
                console.print("[yellow]No analysis directory found. Cannot load room breakdown.[/yellow]")
                input("\nPress Enter to continue...")
                return
            analysis_dir = self.analysis_dir
            rooms_dir = analysis_dir / 'rooms'
            rooms_with_test = []
            
            if rooms_dir.exists():
                for room_id in building.room_ids:
                    room_file = rooms_dir / f"{room_id}.json"
                    if room_file.exists():
                        try:
                            room = RoomAnalysis.load_from_json(room_file)
                            if test_name in room.test_results:
                                test_result = room.test_results[test_name]
                                rooms_with_test.append((room, test_result))
                        except Exception:
                            pass
            
            if not rooms_with_test:
                console.print("[yellow]No rooms found with this test[/yellow]")
                input("\nPress Enter to continue...")
                return
            
            # Sort by compliance (worst first)
            rooms_with_test.sort(key=lambda x: x[1].compliance_rate)
            
            # Display table
            table = Table(box=box.ROUNDED, show_header=True)
            table.add_column("Room", style="cyan", width=30)
            table.add_column("Compliance", justify="right", style="white")
            table.add_column("Hours", justify="right", style="yellow")
            
            is_br18 = 'br18' in test_name.lower()
            if is_br18:
                table.add_column("BR18 Status", justify="center", style="white")
            
            for room, test_result in rooms_with_test[:30]:  # Show top 30
                # Format compliance
                if test_result.compliance_rate >= 90:
                    comp_str = f"[green]{test_result.compliance_rate:.1f}%[/green]"
                elif test_result.compliance_rate >= 75:
                    comp_str = f"[cyan]{test_result.compliance_rate:.1f}%[/cyan]"
                elif test_result.compliance_rate >= 50:
                    comp_str = f"[yellow]{test_result.compliance_rate:.1f}%[/yellow]"
                else:
                    comp_str = f"[red]{test_result.compliance_rate:.1f}%[/red]"
                
                hours_str = f"{test_result.non_compliant_hours}/{test_result.total_hours}"
                
                if is_br18:
                    max_hours = 100 if '100h' in test_name else 25 if '25h' in test_name else 0
                    is_passing = test_result.non_compliant_hours <= max_hours
                    br18_status = f"[green]PASS[/green]" if is_passing else f"[red]FAIL[/red]"
                    table.add_row(room.room_name[:30], comp_str, hours_str, br18_status)
                else:
                    table.add_row(room.room_name[:30], comp_str, hours_str)
            
            console.print(table)
            
            if len(rooms_with_test) > 30:
                console.print(f"\n[dim]... and {len(rooms_with_test) - 30} more rooms[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error loading room data: {str(e)}[/red]")
        
        input("\n\nPress Enter to continue...")
    
    def _navigate_rooms(self, building):
        """Navigate through rooms in a building."""
        from src.core.models import RoomAnalysis
        
        # Load room data
        if self.analysis_dir is None:
            console.print("\n[yellow]No analysis directory found. Cannot navigate rooms.[/yellow]")
            input("\nPress Enter to continue...")
            return
        analysis_dir = self.analysis_dir
        rooms_dir = analysis_dir / 'rooms'
        room_analyses = {}
        
        if rooms_dir.exists():
            for room_id in building.room_ids:
                room_file = rooms_dir / f"{room_id}.json"
                if room_file.exists():
                    try:
                        room = RoomAnalysis.load_from_json(room_file)
                        room_analyses[room_id] = room
                    except Exception:
                        pass
        
        if not room_analyses:
            console.clear()
            console.print("\n[yellow]No room data available[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        while True:
            console.clear()
            console.print(f"\n[bold cyan]🚪 Rooms in {building.building_name}[/bold cyan]\n")
            
            # Create room choices
            room_choices = []
            for room_id, room in sorted(room_analyses.items(), key=lambda x: x[1].room_name):
                # Base label with compliance
                label = f"{room.room_name} - {room.overall_compliance_rate:.1f}% compliance"
                
                # Add BR18 indicator if applicable
                if self.building_type and self.building_type != 'skip' and room.test_results:
                    br18_tests = {k: v for k, v in room.test_results.items() if 'br18' in k.lower()}
                    
                    # Filter by building type
                    if self.building_type in ['office', 'other']:
                        relevant_br18 = {k: v for k, v in br18_tests.items() if 'office' in k}
                    elif self.building_type == 'residential':
                        relevant_br18 = {k: v for k, v in br18_tests.items() if 'residential' in k}
                    else:
                        relevant_br18 = {}
                    
                    if relevant_br18:
                        # Check if any BR18 tests are failing
                        any_br18_fail = False
                        for test_id, test_result in relevant_br18.items():
                            max_hours = 100 if '100h' in test_id else 25
                            if test_result.non_compliant_hours > max_hours:
                                any_br18_fail = True
                                break
                        
                        if any_br18_fail:
                            label += " [BR18: FAIL]"
                        else:
                            label += " [BR18: PASS]"
                
                room_choices.append(label)
            
            room_choices.append("← Back to building")
            
            questions = [
                inquirer.List(
                    'room',
                    message="Choose a room to view details",
                    choices=room_choices,
                    carousel=True
                ),
            ]
            
            try:
                answer = inquirer.prompt(questions, theme=GreenPassion())
                if not answer or answer['room'] == "← Back to building":
                    break
                
                # Find selected room
                selected_label = answer['room']
                for room_id, room in room_analyses.items():
                    label = f"{room.room_name} - {room.overall_compliance_rate:.1f}% compliance"
                    if label == selected_label:
                        self._show_room_details(room)
                        break
            
            except KeyboardInterrupt:
                break
    
    def _show_room_details(self, room):
        """Show detailed room information."""
        console.clear()
        console.print(f"\n[bold cyan]🚪 {room.room_name}[/bold cyan]\n")
        
        # Room metrics
        metrics = f"""
[bold]Level:[/bold] {room.level_id or 'N/A'}
[bold]Compliance:[/bold] {self._format_compliance(room.overall_compliance_rate)}
[bold]Quality:[/bold] {self._format_quality(room.overall_quality_score)}
[bold]Data Completeness:[/bold] {room.data_completeness:.1f}%
[bold]Parameters:[/bold] {', '.join(room.parameters_analyzed)}
        """
        console.print(Panel(metrics.strip(), border_style="cyan", box=box.ROUNDED))
        
        # Critical issues
        if room.critical_issues and len(room.critical_issues) > 0:
            console.print("\n[bold red]🚨 Critical Issues:[/bold red]")
            for issue in room.critical_issues[:5]:
                console.print(f"  • {issue}")
        
        # Recommendations
        if room.recommendations and len(room.recommendations) > 0:
            console.print("\n[bold yellow]💡 Recommendations:[/bold yellow]")
            for rec in room.recommendations[:5]:
                console.print(f"  • {rec}")
        
        # BR18 Compliance (if applicable)
        if room.test_results and self.building_type and self.building_type != 'skip':
            br18_tests = {k: v for k, v in room.test_results.items() if 'br18' in k.lower()}
            
            # Filter by building type
            office_br18 = {k: v for k, v in br18_tests.items() if 'office' in k}
            residential_br18 = {k: v for k, v in br18_tests.items() if 'residential' in k}
            
            show_office = self.building_type in ['office', 'other']
            show_residential = self.building_type == 'residential'
            
            tests_to_show = {}
            if show_office:
                tests_to_show.update(office_br18)
            if show_residential:
                tests_to_show.update(residential_br18)
            
            if tests_to_show:
                console.print("\n[bold yellow]📋 BR18 Danish Building Regulations:[/bold yellow]")
                
                for test_id, test_result in sorted(tests_to_show.items()):
                    exceedance_hours = test_result.non_compliant_hours
                    
                    # Extract max hours from test ID
                    if '100h' in test_id:
                        max_hours = 100
                        temp_limit = '26°C' if '26' in test_id else '27°C'
                    elif '25h' in test_id:
                        max_hours = 25
                        temp_limit = '27°C' if '27' in test_id else '28°C'
                    else:
                        continue
                    
                    # Determine pass/fail
                    is_passing = exceedance_hours <= max_hours
                    
                    if is_passing:
                        status = f"[green]✓ PASS ({exceedance_hours}/{max_hours}h)[/green]"
                    else:
                        status = f"[red]✗ FAIL ({exceedance_hours}/{max_hours}h)[/red]"
                    
                    building_type_label = "Office" if 'office' in test_id else "Residential"
                    console.print(f"  • {building_type_label} >{temp_limit} (max {max_hours}h/year): {status}")
        
        # Test summary
        if room.test_results:
            console.print(f"\n[bold]All Tests Run:[/bold] {len(room.test_results)}")
            
            # Count by severity
            severity_counts = {}
            for test in room.test_results.values():
                sev = test.severity.value
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            for sev in ['critical', 'high', 'medium', 'low']:
                if sev in severity_counts:
                    color = {'critical': 'red', 'high': 'yellow', 'medium': 'cyan', 'low': 'green'}[sev]
                    console.print(f"  [{color}]● {sev.title()}[/{color}]: {severity_counts[sev]}")
        
        input("\n\nPress Enter to continue...")
    
    def _show_portfolio_recommendations(self):
        """Show portfolio-level recommendations."""
        console.clear()
        console.print("\n[bold cyan]💡 Portfolio Recommendations[/bold cyan]\n")
        
        if not self.portfolio_data or not self.portfolio_data.recommendations:
            console.print("[yellow]No portfolio recommendations available[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        console.print("[bold]Top Recommendations for Your Portfolio:[/bold]\n")
        
        for i, rec in enumerate(self.portfolio_data.recommendations[:10], 1):
            console.print(f"{i}. {rec}")
        
        input("\n\nPress Enter to continue...")
    
    def _export_report(self):
        """Export PDF report."""
        console.clear()
        console.print("\n[bold cyan]📄 Export Report[/bold cyan]\n")
        
        console.print("[yellow]PDF report generation will be available in the next version.[/yellow]")
        console.print("\nFor now, you can:")
        console.print("  • Take screenshots of the results")
        console.print(f"  • Access JSON data in: {self.analysis_dir}")
        console.print("  • Use the web dashboard for presentations")
        
        input("\n\nPress Enter to continue...")
