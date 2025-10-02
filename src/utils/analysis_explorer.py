"""
Interactive analysis explorer for browsing hierarchical analysis results.

Provides an interactive CLI interface to navigate analysis results from
portfolio → buildings → levels → rooms.
"""

import sys
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from datetime import timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml
import holidays

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box

from src.models.analysis_models import (
    PortfolioAnalysis, BuildingAnalysis, LevelAnalysis, RoomAnalysis,
    TestResult, AnalysisSeverity
)
from src.models.building_data import BuildingDataset

console = Console()


class AnalysisExplorer:
    """Interactive explorer for browsing analysis results."""
    
    def __init__(self, analysis_dir: Path):
        """
        Initialize the analysis explorer.
        
        Args:
            analysis_dir: Directory containing analysis results
        """
        self.analysis_dir = analysis_dir
        self.portfolio: Optional[PortfolioAnalysis] = None
        self.current_building: Optional[BuildingAnalysis] = None
        self.current_level: Optional[LevelAnalysis] = None
        self.current_room: Optional[RoomAnalysis] = None
        self.history: List[str] = []
        self.dataset: Optional[BuildingDataset] = None
        self.tests_config: Dict[str, Any] = {}
        
        # Load tests configuration for filter definitions
        self._load_tests_config()
        
        # Load portfolio analysis
        self._load_portfolio()
        
        # Try to load dataset for timeseries access
        self._load_dataset()
    
    def _load_portfolio(self):
        """Load portfolio analysis."""
        portfolio_file = self.analysis_dir / "portfolio_analysis.json"
        if not portfolio_file.exists():
            portfolio_file = self.analysis_dir / "portfolio.json"
        
        if portfolio_file.exists():
            self.portfolio = PortfolioAnalysis.load_from_json(portfolio_file)
    
    def _load_tests_config(self):
        """Load tests configuration for filter and period definitions."""
        config_paths = [
            Path("config/tests.yaml"),
            Path("../config/tests.yaml"),
            self.analysis_dir.parent / "config" / "tests.yaml"
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        self.tests_config = yaml.safe_load(f)
                        return
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not load tests config from {config_path}: {e}[/yellow]")
        
        # Set empty config if not found
        self.tests_config = {'filters': {}, 'periods': {}, 'holidays': {}}
    
    def _load_dataset(self):
        """Try to load the dataset for timeseries access."""
        # Look for dataset.pkl in common locations
        dataset_paths = [
            self.analysis_dir.parent / "dataset.pkl",
            Path("output/dataset.pkl"),
            Path("dataset.pkl")
        ]
        
        for dataset_path in dataset_paths:
            if dataset_path.exists():
                try:
                    self.dataset = BuildingDataset.load_from_pickle(dataset_path)
                    break
                except Exception:
                    continue
    
    def start(self):
        """Start the interactive explorer."""
        console.clear()
        self._show_welcome()
        self._main_loop()
    
    def _show_welcome(self):
        """Display welcome message."""
        welcome = """
[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║   Interactive Analysis Explorer                 ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]

Browse hierarchical analysis results: portfolio → buildings → levels → rooms.

[bold]Commands:[/bold]
  • Type number to select an item
  • 'back' or 'b' - Go back to previous view
  • 'home' or 'h' - Return to portfolio view
  • 'quit' or 'q' - Exit explorer
  • 'help' - Show help
        """
        console.print(welcome)
        console.print()
        
        if self.portfolio:
            self._show_portfolio_summary()
    
    def _show_portfolio_summary(self):
        """Display portfolio summary."""
        if not self.portfolio:
            return
        
        info = f"""
[bold]Portfolio:[/bold] {self.portfolio.portfolio_name}
[bold]Buildings:[/bold] {self.portfolio.building_count}
[bold]Total Rooms:[/bold] {self.portfolio.total_room_count}
[bold]Avg Compliance:[/bold] {self.portfolio.avg_compliance_rate:.1f}%
[bold]Avg Quality:[/bold] {self.portfolio.avg_quality_score:.1f}%
[bold]Analyzed:[/bold] {self.portfolio.analysis_timestamp.strftime('%Y-%m-%d %H:%M')}
        """
        console.print(Panel(info.strip(), title="Portfolio Overview", box=box.ROUNDED))
        console.print()
    
    def _main_loop(self):
        """Main interactive loop."""
        while True:
            try:
                if self.current_room:
                    self._room_view()
                elif self.current_level:
                    self._level_view()
                elif self.current_building:
                    self._building_view()
                else:
                    self._portfolio_view()
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' or 'q' to exit[/yellow]")
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
    
    def _portfolio_view(self):
        """Display portfolio view with building list."""
        console.print("\n[bold cyan]═══ Portfolio Buildings ═══[/bold cyan]\n")
        
        if not self.portfolio:
            console.print("[yellow]No portfolio analysis found[/yellow]")
            self._confirm_exit()
            return
        
        # Load building analyses
        buildings_dir = self.analysis_dir / "buildings"
        if not buildings_dir.exists():
            console.print(f"[yellow]Buildings directory not found: {buildings_dir}[/yellow]")
            self._confirm_exit()
            return
        
        building_files = sorted(buildings_dir.glob("*.json"))
        if not building_files:
            console.print("[yellow]No building analyses found[/yellow]")
            self._confirm_exit()
            return
        
        # Create buildings table
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Building", style="cyan bold")
        table.add_column("Rooms", justify="right", style="yellow")
        table.add_column("Levels", justify="right", style="magenta")
        table.add_column("Compliance", justify="right", style="green")
        table.add_column("Quality", justify="right", style="blue")
        table.add_column("Status", style="white")
        
        buildings = []
        for building_file in building_files:
            try:
                building = BuildingAnalysis.load_from_json(building_file)
                buildings.append(building)
            except Exception as e:
                console.print(f"[dim]Warning: Could not load {building_file.name}: {e}[/dim]")
        
        for idx, building in enumerate(buildings, 1):
            status_color = "green" if building.status.value == "completed" else "yellow"
            table.add_row(
                str(idx),
                building.building_name,
                str(building.room_count),
                str(building.level_count),
                f"{building.avg_compliance_rate:.1f}%",
                f"{building.avg_quality_score:.1f}%",
                f"[{status_color}]{building.status.value}[/{status_color}]"
            )
        
        console.print(table)
        console.print()
        
        # Best/worst buildings
        if self.portfolio.best_performing_buildings:
            # Only show buildings with 90% or higher compliance
            top_performers = [b for b in self.portfolio.best_performing_buildings if b['compliance_rate'] >= 90.0]
            if top_performers:
                console.print("[bold green]🏆 Best Performing:[/bold green]")
                for item in top_performers[:3]:
                    console.print(f"   {item['building_name']}: {item['compliance_rate']:.1f}%")
        
        if self.portfolio.worst_performing_buildings:
            console.print("\n[bold red]⚠️  Needs Attention:[/bold red]")
            for item in self.portfolio.worst_performing_buildings[:3]:
                console.print(f"   {item['building_name']}: {item['compliance_rate']:.1f}%")
        
        console.print()
        
        # Get user input
        choice = Prompt.ask(
            "[bold]Select building[/bold] (number or command)",
            default="q"
        ).strip().lower()
        
        if choice in ['q', 'quit', 'exit']:
            self._confirm_exit()
        elif choice in ['h', 'help']:
            self._show_help()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(buildings):
                self.current_building = buildings[idx]
                self.history.append('portfolio')
            else:
                console.print(f"[red]Invalid selection. Please choose 1-{len(buildings)}[/red]")
    
    def _building_view(self):
        if not self.current_building:
            return
        """Display building analysis details."""
        console.print(f"\n[bold cyan]═══ Building: {self.current_building.building_name} ═══[/bold cyan]\n")
        
        # Building metrics
        info = f"""
[bold]ID:[/bold] {self.current_building.building_id}
[bold]Rooms:[/bold] {self.current_building.room_count}
[bold]Levels:[/bold] {self.current_building.level_count}
[bold]Compliance:[/bold] {self.current_building.avg_compliance_rate:.1f}%
[bold]Quality:[/bold] {self.current_building.avg_quality_score:.1f}%
[bold]Status:[/bold] {self.current_building.status.value}
        """
        console.print(Panel(info.strip(), box=box.ROUNDED))
        
        # Critical issues
        if self.current_building.critical_issues:
            console.print("\n[bold red]🚨 Critical Issues:[/bold red]")
            for issue in self.current_building.critical_issues[:5]:
                console.print(f"   • {issue}")
        
        # Recommendations
        if self.current_building.recommendations:
            console.print("\n[bold yellow]💡 Recommendations:[/bold yellow]")
            for rec in self.current_building.recommendations[:5]:
                console.print(f"   • {rec}")
        
        # Best/worst performing
        if self.current_building.best_performing_rooms:
            console.print("\n[bold green]🏆 Best Rooms:[/bold green]")
            for room in self.current_building.best_performing_rooms[:3]:
                console.print(f"   • {room['room_name']}: {room['compliance_rate']:.1f}%")
        
        if self.current_building.worst_performing_rooms:
            console.print("\n[bold red]⚠️  Rooms Needing Attention:[/bold red]")
            for room in self.current_building.worst_performing_rooms[:3]:
                console.print(f"   • {room['room_name']}: {room['compliance_rate']:.1f}%")
        
        # Navigation options
        console.print("\n[bold]Navigate to:[/bold]")
        options = ["1. View by Levels", "2. View all Rooms", "3. View Test Aggregations"]
        for opt in options:
            console.print(f"  {opt}")
        
        console.print("\n  b. Back to portfolio")
        console.print("  q. Quit")
        console.print()
        
        choice = Prompt.ask("[bold]Your choice[/bold]").strip().lower()
        
        if choice == '1':
            self._levels_list_view()
        elif choice == '2':
            self._rooms_list_view()
        elif choice == '3':
            self._show_test_aggregations(self.current_building.test_aggregations)
        elif choice in ['b', 'back']:
            self._go_back()
        elif choice in ['q', 'quit']:
            self._confirm_exit()
        elif choice in ['h', 'home']:
            self._go_home()
        else:
            console.print("[red]Invalid choice[/red]")
    
    def _levels_list_view(self):
        """Display list of levels."""
        if not self.current_building:
            return
        console.print(f"\n[bold cyan]═══ Levels in {self.current_building.building_name} ═══[/bold cyan]\n")
        
        levels_dir = self.analysis_dir / "levels"
        if not levels_dir.exists():
            console.print("[yellow]No levels directory found[/yellow]")
            return
        
        # Load level analyses for this building
        levels = []
        for level_id in self.current_building.level_ids:
            level_file = levels_dir / f"{level_id}.json"
            if level_file.exists():
                try:
                    level = LevelAnalysis.load_from_json(level_file)
                    levels.append(level)
                except Exception as e:
                    console.print(f"[dim]Warning: Could not load {level_file.name}: {e}[/dim]")
        
        if not levels:
            console.print("[yellow]No level analyses found[/yellow]")
            return
        
        # Create levels table
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Level", style="magenta bold")
        table.add_column("Rooms", justify="right", style="yellow")
        table.add_column("Compliance", justify="right", style="green")
        table.add_column("Quality", justify="right", style="blue")
        
        for idx, level in enumerate(levels, 1):
            table.add_row(
                str(idx),
                level.level_name,
                str(level.room_count),
                f"{level.avg_compliance_rate:.1f}%",
                f"{level.avg_quality_score:.1f}%"
            )
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask(
            "[bold]Select level[/bold] (number) or 'back'",
            default="b"
        ).strip().lower()
        
        if choice in ['b', 'back']:
            return
        elif choice in ['q', 'quit']:
            self._confirm_exit()
        elif choice in ['h', 'home']:
            self._go_home()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(levels):
                self.current_level = levels[idx]
                self.history.append('building')
            else:
                console.print(f"[red]Invalid selection[/red]")
    
    def _level_view(self):
        """Display level analysis details."""
        if not self.current_level:
            return
        console.print(f"\n[bold cyan]═══ {self.current_level.level_name} ═══[/bold cyan]\n")
        
        info = f"""
[bold]ID:[/bold] {self.current_level.level_id}
[bold]Building:[/bold] {self.current_building.building_name if self.current_building else "N/A"}
[bold]Rooms:[/bold] {self.current_level.room_count}
[bold]Compliance:[/bold] {self.current_level.avg_compliance_rate:.1f}%
[bold]Quality:[/bold] {self.current_level.avg_quality_score:.1f}%
        """
        console.print(Panel(info.strip(), box=box.ROUNDED))
        
        # Best/worst rooms on this level
        if self.current_level.best_performing_rooms:
            console.print("\n[bold green]🏆 Best Rooms:[/bold green]")
            for room in self.current_level.best_performing_rooms:
                console.print(f"   • {room['room_name']}: {room['compliance_rate']:.1f}%")
        
        if self.current_level.worst_performing_rooms:
            console.print("\n[bold red]⚠️  Rooms Needing Attention:[/bold red]")
            for room in self.current_level.worst_performing_rooms:
                console.print(f"   • {room['room_name']}: {room['compliance_rate']:.1f}%")
        
        # Critical issues
        if self.current_level.critical_issues:
            console.print("\n[bold red]🚨 Critical Issues:[/bold red]")
            for issue in self.current_level.critical_issues[:5]:
                console.print(f"   • {issue}")
        
        console.print("\n[bold]Actions:[/bold]")
        console.print("  1. View rooms on this level")
        console.print("  2. View test aggregations")
        console.print("  b. Back")
        console.print()
        
        choice = Prompt.ask("[bold]Your choice[/bold]").strip().lower()
        
        if choice == '1':
            self._rooms_list_view(level_filter=True)
        elif choice == '2':
            self._show_test_aggregations(self.current_level.test_aggregations)
        elif choice in ['b', 'back']:
            self._go_back()
        elif choice in ['q', 'quit']:
            self._confirm_exit()
        elif choice in ['h', 'home']:
            self._go_home()
    
    def _rooms_list_view(self, level_filter: bool = False):
        """Display list of rooms."""
        if level_filter and self.current_level:
            title = f"Rooms in {self.current_level.level_name}"
            room_ids = self.current_level.room_ids
        else:
            if not self.current_building:
                return
            title = f"All Rooms in {self.current_building.building_name}"
            room_ids = self.current_building.room_ids
        
        console.print(f"\n[bold cyan]═══ {title} ═══[/bold cyan]\n")
        
        rooms_dir = self.analysis_dir / "rooms"
        if not rooms_dir.exists():
            console.print("[yellow]No rooms directory found[/yellow]")
            return
        
        # Load room analyses
        rooms = []
        for room_id in room_ids[:50]:  # Limit to 50 rooms
            room_file = rooms_dir / f"{room_id}.json"
            if room_file.exists():
                try:
                    room = RoomAnalysis.load_from_json(room_file)
                    rooms.append(room)
                except Exception as e:
                    console.print(f"[dim]Warning: Could not load {room_file.name}: {e}[/dim]")
        
        if not rooms:
            console.print("[yellow]No room analyses found[/yellow]")
            return
        
        # Create rooms table
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Room", style="cyan bold", max_width=35)
        table.add_column("Compliance", justify="right", style="green")
        table.add_column("Quality", justify="right", style="blue")
        table.add_column("Tests", justify="right", style="yellow")
        table.add_column("Issues", justify="right", style="red")
        
        for idx, room in enumerate(rooms, 1):
            issues_count = len(room.critical_issues)
            issue_str = str(issues_count) if issues_count > 0 else "-"
            
            table.add_row(
                str(idx),
                room.room_name[:35],
                f"{room.overall_compliance_rate:.1f}%",
                f"{room.overall_quality_score:.1f}%",
                str(len(room.test_results)),
                f"[red]{issue_str}[/red]" if issues_count > 0 else issue_str
            )
        
        if len(room_ids) > 50:
            table.caption = f"Showing 50 of {len(room_ids)} rooms"
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask(
            "[bold]Select room[/bold] (number) or 'back'",
            default="b"
        ).strip().lower()
        
        if choice in ['b', 'back']:
            return
        elif choice in ['q', 'quit']:
            self._confirm_exit()
        elif choice in ['h', 'home']:
            self._go_home()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(rooms):
                self.current_room = rooms[idx]
                if level_filter:
                    self.history.append('level')
                else:
                    self.history.append('building')
            else:
                console.print(f"[red]Invalid selection[/red]")
    
    def _room_view(self):
        """Display room analysis details."""
        if not self.current_room:
            return
        console.print(f"\n[bold cyan]═══ Room: {self.current_room.room_name} ═══[/bold cyan]\n")
        
        # Room metrics
        info = f"""
[bold]ID:[/bold] {self.current_room.room_id}
[bold]Building:[/bold] {self.current_building.building_name if self.current_building else "N/A"}
[bold]Level:[/bold] {self.current_room.level_id or "N/A"}
[bold]Compliance:[/bold] {self.current_room.overall_compliance_rate:.1f}%
[bold]Quality:[/bold] {self.current_room.overall_quality_score:.1f}%
[bold]Data Completeness:[/bold] {self.current_room.data_completeness:.1f}%
[bold]Parameters:[/bold] {', '.join(self.current_room.parameters_analyzed)}
        """
        
        if self.current_room.data_period_start and self.current_room.data_period_end:
            info += f"\n[bold]Period:[/bold] {self.current_room.data_period_start.date()} to {self.current_room.data_period_end.date()}"
        
        console.print(Panel(info.strip(), box=box.ROUNDED))
        
        # Critical issues
        if self.current_room.critical_issues:
            console.print("\n[bold red]🚨 Critical Issues:[/bold red]")
            for issue in self.current_room.critical_issues[:5]:
                console.print(f"   • {issue}")
        
        # Recommendations
        if self.current_room.recommendations:
            console.print("\n[bold yellow]💡 Recommendations:[/bold yellow]")
            for rec in self.current_room.recommendations[:5]:
                console.print(f"   • {rec}")
        
        # Test results summary
        if self.current_room.test_results:
            console.print(f"\n[bold]Test Results:[/bold] ({len(self.current_room.test_results)} tests)")
            
            # Count by severity
            severity_counts = {}
            for test_result in self.current_room.test_results.values():
                sev = test_result.severity.value
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            if severity_counts:
                console.print("  Severity breakdown:")
                for sev in ['critical', 'high', 'medium', 'low', 'info']:
                    if sev in severity_counts:
                        color = {'critical': 'red', 'high': 'yellow', 'medium': 'cyan', 'low': 'green', 'info': 'white'}[sev]
                        console.print(f"    [{color}]● {sev.title()}[/{color}]: {severity_counts[sev]}")
        
        console.print("\n[bold]Actions:[/bold]")
        console.print("  1. View detailed test results")
        console.print("  2. View statistics")
        console.print("  b. Back")
        console.print()
        
        choice = Prompt.ask("[bold]Your choice[/bold]").strip().lower()
        
        if choice == '1':
            self._show_test_results()
        elif choice == '2':
            self._show_room_statistics()
        elif choice in ['b', 'back']:
            self._go_back()
        elif choice in ['q', 'quit']:
            self._confirm_exit()
        elif choice in ['h', 'home']:
            self._go_home()
    
    def _show_test_results(self):
        """Display detailed test results for a room."""
        if not self.current_room:
            return
        console.print(f"\n[bold cyan]═══ Test Results: {self.current_room.room_name} ═══[/bold cyan]\n")
        
        if not self.current_room.test_results:
            console.print("[yellow]No test results available[/yellow]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        # Create test results table with index
        table = Table(box=box.ROUNDED, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Test", style="cyan", max_width=30)
        table.add_column("Parameter", style="blue")
        table.add_column("Compliance", justify="right", style="green")
        table.add_column("Hours", justify="center", style="yellow")
        table.add_column("Severity", style="white")
        
        test_list = []
        for idx, (test_name, result) in enumerate(sorted(self.current_room.test_results.items()), 1):
            test_list.append((test_name, result))
            
            severity_color = {
                'critical': 'red',
                'high': 'yellow',
                'medium': 'cyan',
                'low': 'green',
                'info': 'white'
            }.get(result.severity.value, 'white')
            
            hours_str = f"{result.compliant_hours}/{result.total_hours}"
            
            table.add_row(
                str(idx),
                test_name[:30],
                result.parameter,
                f"{result.compliance_rate:.1f}%",
                hours_str,
                f"[{severity_color}]{result.severity.value.upper()}[/{severity_color}]"
            )
        
        console.print(table)
        
        # Show recommendations from tests
        all_recommendations = []
        for result in self.current_room.test_results.values():
            all_recommendations.extend(result.recommendations)
        
        if all_recommendations:
            console.print("\n[bold yellow]Test-specific Recommendations:[/bold yellow]")
            for rec in all_recommendations[:5]:
                console.print(f"   • {rec}")
        
        # Prompt to plot timeseries
        console.print("\n[bold]Actions:[/bold]")
        console.print("  • Enter a test number to plot its timeseries")
        console.print("  • Press Enter to return")
        
        choice = Prompt.ask("[bold cyan]Select test to plot (or press Enter)[/bold cyan]", default="")
        
        if choice and choice.isdigit():
            test_idx = int(choice)
            if 1 <= test_idx <= len(test_list):
                test_name, test_result = test_list[test_idx - 1]
                self._plot_test_timeseries(test_name, test_result)
            else:
                console.print("[red]Invalid test number[/red]")
                Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
    
    def _plot_test_timeseries(self, test_name: str, test_result: TestResult):
        """Plot timeseries for a specific test with non-compliant periods highlighted."""
        if not self.current_room:
            console.print("[red]No room selected[/red]")
            return
        
        self._create_timeseries_graph(self.current_room, test_name, test_result)
    
    def _show_room_statistics(self):
        """Display room statistics."""
        if not self.current_room:
            return
        console.print(f"\n[bold cyan]═══ Statistics: {self.current_room.room_name} ═══[/bold cyan]\n")
        
        if not self.current_room.statistics:
            console.print("[yellow]No statistics available[/yellow]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        for param, stats in self.current_room.statistics.items():
            console.print(f"[bold cyan]{param}:[/bold cyan]")
            for stat_name, value in stats.items():
                console.print(f"  {stat_name}: {value:.2f}")
            console.print()
        
        Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
    
    def _show_test_aggregations(self, aggregations: dict):
        """Display test aggregations as a table with drill-down capability."""
        console.print("\n[bold cyan]═══ Test Aggregations ═══[/bold cyan]\n")
        
        if not aggregations:
            console.print("[yellow]No aggregations available[/yellow]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        # Create aggregations table
        table = Table(box=box.ROUNDED, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Test Name", style="cyan bold", max_width=40)
        table.add_column("Avg Compliance", justify="right", style="green")
        table.add_column("Total Hours", justify="right", style="yellow")
        table.add_column("Rooms", justify="right", style="magenta")
        
        test_list = []
        for idx, (test_name, agg_data) in enumerate(sorted(aggregations.items()), 1):
            test_list.append((test_name, agg_data))
            
            avg_compliance = agg_data.get('avg_compliance_rate', agg_data.get('average_compliance', 0))
            total_hours = agg_data.get('total_hours', 0)
            room_count = agg_data.get('room_count', agg_data.get('rooms_tested', 0))
            
            table.add_row(
                str(idx),
                test_name[:40],
                f"{avg_compliance:.1f}%" if isinstance(avg_compliance, (int, float)) else str(avg_compliance),
                str(total_hours) if total_hours else "-",
                str(room_count) if room_count else "-"
            )
        
        console.print(table)
        console.print("\n[bold]Options:[/bold]")
        console.print("  • Type a number to view room-level details for that test")
        console.print("  • Press Enter to go back")
        console.print()
        
        choice = Prompt.ask("[bold]Select test or press Enter[/bold]", default="").strip()
        
        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(test_list):
                test_name, agg_data = test_list[idx]
                self._show_test_room_details(test_name, agg_data)
            else:
                console.print(f"[red]Invalid selection[/red]")
                Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
    
    def _show_help(self):
        """Display help information."""
        help_text = """
[bold cyan]═══ Help ═══[/bold cyan]

[bold]Navigation:[/bold]
  • Type a number to select an item from a list
  • 'back' or 'b' - Go back to the previous view
  • 'home' or 'h' - Return to the portfolio view
  • 'quit' or 'q' - Exit the explorer

[bold]Views:[/bold]
  • Portfolio - Overview of all buildings
  • Building - Detailed building analysis with levels and rooms
  • Level - Analysis of a specific floor/level
  • Room - Detailed room analysis with test results

[bold]Understanding Results:[/bold]
  • Compliance Rate - Percentage of time meeting requirements
  • Quality Score - Data completeness and reliability
  • Severity - CRITICAL > HIGH > MEDIUM > LOW > INFO
        """
        console.print()
        console.print(Panel(help_text.strip(), box=box.ROUNDED))
        console.print()
        Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
    
    def _go_back(self):
        """Navigate back to previous view."""
        if not self.history:
            return
        
        previous = self.history.pop()
        
        if previous == 'level':
            self.current_room = None
        elif previous == 'building':
            self.current_level = None
            self.current_room = None
        elif previous == 'portfolio':
            self.current_building = None
            self.current_level = None
            self.current_room = None
    
    def _go_home(self):
        """Return to portfolio view."""
        self.current_building = None
        self.current_level = None
        self.current_room = None
        self.history = []
    
    def _show_test_room_details(self, test_name: str, agg_data: dict):
        """Display room-level details for a specific test."""
        console.print(f"\n[bold cyan]═══ Room Details: {test_name} ═══[/bold cyan]\n")
        
        # Show test summary first
        console.print("[bold]Test Summary:[/bold]")
        summary_table = Table(box=box.SIMPLE, show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", justify="right")
        
        for key, value in agg_data.items():
            if isinstance(value, float):
                summary_table.add_row(key.replace('_', ' ').title(), f"{value:.2f}")
            else:
                summary_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(summary_table)
        console.print()
        
        # Try to load room-level data for this test
        rooms_dir = self.analysis_dir / "rooms"
        if not rooms_dir.exists():
            console.print("[yellow]Cannot load room details - rooms directory not found[/yellow]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        # Determine which rooms to load based on context
        room_ids = []
        if self.current_building:
            room_ids = self.current_building.room_ids[:50]  # Limit to 50 rooms
        elif self.current_level:
            room_ids = self.current_level.room_ids
        else:
            # Load first 50 room files
            room_files = sorted(rooms_dir.glob("*.json"))[:50]
            room_ids = [f.stem for f in room_files]
        
        # Create room details table
        console.print("[bold]Room-Level Results:[/bold]")
        table = Table(box=box.ROUNDED, show_header=True)
        table.add_column("Room", style="cyan", max_width=35)
        table.add_column("Compliance", justify="right", style="green")
        table.add_column("Hours Pass/Total", justify="center", style="yellow")
        table.add_column("Severity", style="white")
        
        rooms_with_test = []
        for room_id in room_ids:
            room_file = rooms_dir / f"{room_id}.json"
            if room_file.exists():
                try:
                    from src.models.analysis_models import RoomAnalysis
                    room = RoomAnalysis.load_from_json(room_file)
                    
                    # Check if this room has results for the selected test
                    if test_name in room.test_results:
                        test_result = room.test_results[test_name]
                        rooms_with_test.append((room, test_result))
                except Exception:
                    continue
        
        if not rooms_with_test:
            console.print("[yellow]No rooms found with results for this test[/yellow]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        # Sort by compliance rate (ascending to show worst first)
        rooms_with_test.sort(key=lambda x: x[1].compliance_rate)
        
        for room, test_result in rooms_with_test[:30]:  # Show top 30
            severity_color = {
                'critical': 'red',
                'high': 'yellow',
                'medium': 'cyan',
                'low': 'green',
                'info': 'white'
            }.get(test_result.severity.value, 'white')
            
            hours_str = f"{test_result.compliant_hours}/{test_result.total_hours}"
            
            table.add_row(
                room.room_name[:35],
                f"{test_result.compliance_rate:.1f}%",
                hours_str,
                f"[{severity_color}]{test_result.severity.value.upper()}[/{severity_color}]"
            )
        
        if len(rooms_with_test) > 30:
            table.caption = f"Showing 30 of {len(rooms_with_test)} rooms"
        
        console.print(table)
        
        # Show statistics
        if rooms_with_test:
            compliance_rates = [r[1].compliance_rate for r in rooms_with_test]
            console.print("\n[bold]Statistics:[/bold]")
            console.print(f"  • Best: {max(compliance_rates):.1f}%")
            console.print(f"  • Worst: {min(compliance_rates):.1f}%")
            console.print(f"  • Average: {sum(compliance_rates)/len(compliance_rates):.1f}%")
            console.print(f"  • Median: {sorted(compliance_rates)[len(compliance_rates)//2]:.1f}%")
        
        console.print()
        
        # Offer to create timeseries visualization
        if self.dataset:
            console.print("[bold]Options:[/bold]")
            console.print("  1. View timeseries graph for a specific room")
            console.print("  2. Go back")
            console.print()
            
            choice = Prompt.ask("[bold]Your choice[/bold]", default="2").strip()
            
            if choice == "1":
                self._select_room_for_timeseries(test_name, rooms_with_test)
        else:
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
    
    def _select_room_for_timeseries(self, test_name: str, rooms_with_test: List[Tuple]):
        """Select a room to visualize timeseries for a specific test."""
        console.print(f"\n[bold cyan]Select Room for Timeseries Visualization[/bold cyan]\n")
        
        # Create selection table
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Room", style="cyan", max_width=35)
        table.add_column("Compliance", justify="right", style="green")
        
        for idx, (room, test_result) in enumerate(rooms_with_test[:20], 1):
            table.add_row(
                str(idx),
                room.room_name[:35],
                f"{test_result.compliance_rate:.1f}%"
            )
        
        if len(rooms_with_test) > 20:
            table.caption = f"Showing 20 of {len(rooms_with_test)} rooms"
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask(
            "[bold]Select room number or press Enter to cancel[/bold]",
            default=""
        ).strip()
        
        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(rooms_with_test):
                room, test_result = rooms_with_test[idx]
                self._create_timeseries_graph(room, test_name, test_result)
            else:
                console.print(f"[red]Invalid selection[/red]")
    
    def _create_timeseries_graph(self, room: RoomAnalysis, test_name: str, test_result: TestResult):
        """Create interactive timeseries graph with filtered data in blue and out-of-scope data in grey."""
        console.print(f"\n[bold cyan]Generating timeseries graph for {room.room_name}...[/bold cyan]")
        
        if not self.dataset:
            console.print("[red]Dataset not available for timeseries visualization[/red]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
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
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        # Get the parameter for this test
        parameter = test_result.parameter
        
        if parameter not in room_obj.timeseries:
            console.print(f"[yellow]Parameter {parameter} not found in room timeseries[/yellow]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        # Get timeseries data
        ts_obj = room_obj.timeseries[parameter]
        
        # Extract the actual pandas Series from TimeSeriesData
        if parameter not in ts_obj.data.columns:
            console.print(f"[yellow]Parameter {parameter} not found in timeseries data columns[/yellow]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        ts_data = ts_obj.data[parameter]
        
        if ts_data.empty:
            console.print(f"[yellow]No timeseries data available for {parameter}[/yellow]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        # Determine which data points are in scope (filtered) vs out of scope
        filter_mask = self._get_filter_mask(ts_data.index, test_result)
        
        # Split data into filtered and out-of-scope (only keep filtered data for heatmap)
        filtered_data = ts_data[filter_mask]
        
        if filtered_data.empty:
            console.print(f"[yellow]No filtered data available for visualization[/yellow]")
            Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
            return
        
        # Determine compliance for filtered data only
        compliant_mask = self._determine_compliance_mask(filtered_data, test_name, test_result)
        
        # Prepare data for heatmap
        # Create a DataFrame with date, hour, and compliance status
        filtered_df = pd.DataFrame({
            'timestamp': filtered_data.index,
            'value': filtered_data.values,
            'compliant': compliant_mask if compliant_mask is not None else True
        })
        
        # Extract week and hour
        filtered_df['week'] = filtered_df['timestamp'].dt.to_period('W').dt.start_time
        filtered_df['hour'] = filtered_df['timestamp'].dt.hour
        
        # Create pivot table for heatmap - average value per week/hour
        heatmap_data = filtered_df.pivot_table(
            values='value',
            index='hour',
            columns='week',
            aggfunc='mean'  # Average value per hour/week
        )
        
        # Create compliance pivot for coloring
        filtered_df['compliance_value'] = filtered_df['compliant'].map({True: 1, False: 0})
        compliance_data = filtered_df.pivot_table(
            values='compliance_value',
            index='hour',
            columns='week',
            aggfunc='mean'  # Average compliance per hour/week
        )
        
        # Remove weeks (columns) that have no data at all (all NaN)
        valid_weeks = heatmap_data.columns[heatmap_data.notna().any(axis=0)]
        heatmap_data = heatmap_data[valid_weeks]
        compliance_data = compliance_data[valid_weeks]
        
        # Ensure all hours (0-23) are shown for valid weeks
        all_hours = list(range(24))
        heatmap_data = heatmap_data.reindex(all_hours)
        compliance_data = compliance_data.reindex(all_hours)
        
        # Sort hours in descending order (so 0 is at bottom, 23 at top for better readability)
        heatmap_data = heatmap_data.sort_index(ascending=False)
        compliance_data = compliance_data.sort_index(ascending=False)
        
        # Create the heatmap
        fig = go.Figure()
        
        # Convert week dates to strings for x-axis labels (show week start date)
        week_labels = [f"{d.date()}" for d in heatmap_data.columns]
        hour_labels = [f"{h:02d}:00" for h in heatmap_data.index]
        
        # Create custom colorscale: red for non-compliant (0), green for compliant (1)
        colorscale = [
            [0.0, '#ff4444'],  # Red for non-compliant
            [0.5, '#ffaa44'],  # Orange for partial compliance
            [1.0, '#44ff44']   # Green for compliant
        ]
        
        # Create text annotations showing average values
        text_annotations = []
        for i, row in enumerate(heatmap_data.values):
            row_text = []
            for val in row:
                if pd.notna(val):
                    # For CO2, divide by 1000 and round to 1 decimal
                    if 'CO2' in parameter.upper():
                        row_text.append(f"{val/1000:.1f}")
                    else:
                        row_text.append(f"{val:.1f}")
                else:
                    row_text.append("")
            text_annotations.append(row_text)
        
        # Create hover text with both value and compliance info
        hover_text = []
        for i in range(len(heatmap_data.index)):
            row_hover = []
            for j in range(len(heatmap_data.columns)):
                val = heatmap_data.iloc[i, j]
                comp = compliance_data.iloc[i, j]
                if pd.notna(val) and pd.notna(comp):
                    status = 'Compliant' if comp >= 0.9 else 'Partial' if comp >= 0.5 else 'Non-compliant'
                    # For CO2, divide by 1000 for display
                    if 'CO2' in parameter.upper():
                        val_display = f"{val/1000:.1f}k"
                    else:
                        val_display = f"{val:.1f}"
                    row_hover.append(f"Week: {week_labels[j]}<br>Hour: {hour_labels[i]}<br>Avg {parameter}: {val_display}<br>Compliance: {comp*100:.0f}%<br>Status: {status}")
                else:
                    row_hover.append(f"Week: {week_labels[j]}<br>Hour: {hour_labels[i]}<br>No data")
            hover_text.append(row_hover)
        
        fig.add_trace(go.Heatmap(
            z=compliance_data.values,  # Color by compliance
            x=week_labels,
            y=hour_labels,
            text=text_annotations,  # Show average values
            texttemplate='%{text}',
            textfont={"size": 10},
            colorscale=colorscale,
            zmin=0,
            zmax=1,
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_text,
            colorbar=dict(
                title="Compliance",
                tickvals=[0, 0.5, 1],
                ticktext=['Non-compliant', 'Partial', 'Compliant'],
                len=0.5
            ),
            showscale=True
        ))
        
        # Update layout for heatmap
        fig.update_layout(
            title=dict(
                text=f"{room.room_name} - {test_name}<br><sub>{parameter} Compliance Heatmap</sub>",
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="Date",
            yaxis_title="Hour of Day",
            xaxis=dict(
                tickangle=-45,
                tickmode='auto',
                nticks=20  # Limit number of date labels for readability
            ),
            yaxis=dict(
                tickmode='linear',
                dtick=1
            ),
            template='plotly_white',
            height=800,
            showlegend=False
        )
        
        # Add compliance information as annotation
        threshold = self._extract_threshold_from_test(test_result)
        threshold_text = f"Threshold: {threshold}" if threshold is not None else ""
        
        compliance_text = (
            f"Compliance Rate: {test_result.compliance_rate:.1f}%<br>"
            f"Compliant Hours: {test_result.compliant_hours}/{test_result.total_hours}<br>"
            f"Severity: {test_result.severity.value.upper()}<br>"
            f"{threshold_text}"
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
        
        # Save and open the graph
        output_file = self.analysis_dir.parent / "graphs" / f"{room.room_id}_{test_name.replace(' ', '_')}.html"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        fig.write_html(str(output_file))
        
        console.print(f"\n[green]✓ Graph saved to:[/green] {output_file}")
        console.print(f"\n[bold cyan]Opening graph in browser...[/bold cyan]")
        
        # Open in browser
        import webbrowser
        webbrowser.open(f"file://{output_file.absolute()}")
        
        Prompt.ask("\n[bold]Press Enter to continue[/bold]", default="")
    
    def _extract_threshold_from_test(self, test_result: TestResult) -> Optional[float]:
        """Extract threshold value from test result if available."""
        # Check if threshold is a simple float
        if test_result.threshold is not None:
            if isinstance(test_result.threshold, (int, float)):
                return float(test_result.threshold)
            elif isinstance(test_result.threshold, dict):
                # If it's a dict, try to get 'max', 'min', or 'value'
                for key in ['max', 'min', 'value', 'limit']:
                    if key in test_result.threshold:
                        try:
                            return float(test_result.threshold[key])
                        except (ValueError, TypeError):
                            continue
        return None
    
    def _get_filter_mask(self, index, test_result: TestResult):
        """
        Determine which data points are in scope (filtered) vs out of scope.
        Returns a boolean mask where True = in scope, False = out of scope.
        Uses test configuration to apply correct filters including holidays and periods.
        """
        # Create a mask that's initially all True (everything in scope)
        mask = pd.Series(True, index=index)
        
        # Get filter information from test result
        filter_applied = test_result.filter_applied
        period = test_result.period
        
        # Get filter configuration from tests config
        filters_config = self.tests_config.get('filters', {})
        filter_config = filters_config.get(filter_applied, {})
        
        # If filter not found in config, fall back to string parsing
        if not filter_config and filter_applied and filter_applied != 'all_hours':
            return self._get_filter_mask_fallback(index, filter_applied, period)
        
        # Apply hour filtering
        hours = filter_config.get('hours', list(range(24)))
        hour_mask = index.hour.isin(hours)
        
        # Apply weekday filtering
        weekday_mask = pd.Series(True, index=index)
        if filter_config.get('weekdays_only', False):
            weekday_mask = index.weekday < 5
        elif filter_config.get('weekends_only', False):
            weekday_mask = index.weekday >= 5
        
        # Apply holiday exclusion
        holiday_mask = pd.Series(False, index=index)
        if filter_config.get('exclude_holidays', False) or filter_config.get('exclude_custom_holidays', False):
            holiday_mask = self._get_holiday_mask(index)
        
        # Apply period (seasonal) filtering
        period_mask = pd.Series(True, index=index)
        if period and period != 'all_year':
            period_mask = self._get_period_mask(index, period)
        
        # Combine all masks (hours AND weekdays AND NOT holidays AND period)
        mask = hour_mask & weekday_mask & ~holiday_mask & period_mask
        
        return mask
    
    def _get_period_mask(self, index, period: str) -> pd.Series:
        """Get boolean mask for period (seasonal) filtering."""
        periods_config = self.tests_config.get('periods', {})
        period_config = periods_config.get(period, {})
        
        if not period_config:
            # Fallback to hardcoded periods
            if period == 'spring':
                months = [3, 4, 5]
            elif period == 'summer':
                months = [6, 7, 8]
            elif period == 'autumn':
                months = [9, 10, 11]
            elif period == 'winter':
                months = [12, 1, 2]
            else:
                return pd.Series(True, index=index)
        else:
            months = period_config.get('months', list(range(1, 13)))
        
        return index.month.isin(months)
    
    def _get_filter_mask_fallback(self, index, filter_applied: str, period: Optional[str] = None):
        """Fallback filter parsing when filter not found in config."""
        # Default opening hours (8:00 - 15:00)
        opening_hours = [8, 9, 10, 11, 12, 13, 14, 15]
        
        # Evening hours (16:00 - 21:00)
        evening_hours = [16, 17, 18, 19, 20, 21]
        
        # Initialize masks
        hour_mask = pd.Series(True, index=index)
        weekday_mask = pd.Series(True, index=index)
        period_mask = pd.Series(True, index=index)
        
        # Handle hour-based filters
        if 'evening' in filter_applied.lower():
            hour_mask = index.hour.isin(evening_hours)
        elif 'opening' in filter_applied.lower() and 'outside' not in filter_applied.lower() and 'non' not in filter_applied.lower():
            hour_mask = index.hour.isin(opening_hours)
        elif 'non_opening' in filter_applied.lower() or 'outside' in filter_applied.lower():
            hour_mask = ~index.hour.isin(opening_hours)
        elif 'afternoon' in filter_applied.lower():
            # Afternoon hours (12:00 - 15:00)
            hour_mask = index.hour.isin([12, 13, 14, 15])
        elif 'morning' in filter_applied.lower():
            # Morning hours (8:00 - 11:00)
            hour_mask = index.hour.isin([8, 9, 10, 11])
        
        # Handle weekday/weekend filters
        if 'weekday' in filter_applied.lower() or 'opening' in filter_applied.lower() or 'morning' in filter_applied.lower() or 'afternoon' in filter_applied.lower() or 'evening' in filter_applied.lower():
            weekday_mask = index.weekday < 5
        elif 'weekend' in filter_applied.lower():
            weekday_mask = index.weekday >= 5
        
        # Handle period filtering
        if period and period != 'all_year':
            period_mask = self._get_period_mask(index, period)
        
        # Combine masks
        mask = hour_mask & weekday_mask & period_mask
        
        return mask
    
    def _get_holiday_mask(self, index) -> pd.Series:
        """Get boolean mask for holiday dates based on config."""
        if not isinstance(index, pd.DatetimeIndex):
            return pd.Series(False, index=index)
        
        # Get years from the index
        data_years = sorted(index.year.unique().tolist())
        
        # Get holiday dates
        holiday_dates = []
        
        holidays_config = self.tests_config.get('holidays', {})
        
        # Get Danish public holidays
        country = holidays_config.get('country', 'DK')
        try:
            dk_holidays = holidays.country_holidays(country, years=data_years)
            holiday_dates.extend(list(dk_holidays.keys()))
        except:
            pass
        
        # Add custom holidays (school holidays)
        custom_holidays = holidays_config.get('custom_holidays', [])
        for holiday in custom_holidays:
            try:
                start_date = pd.to_datetime(holiday['start_date']).date()
                end_date_str = holiday.get('end_date')
                
                if end_date_str:
                    end_date = pd.to_datetime(end_date_str).date()
                    current_date = start_date
                    while current_date <= end_date:
                        if current_date.year in data_years:
                            holiday_dates.append(current_date)
                        current_date += timedelta(days=1)
                else:
                    if start_date.year in data_years:
                        holiday_dates.append(start_date)
            except:
                continue
        
        # Create mask
        mask = pd.Series(False, index=index)
        for holiday_date in holiday_dates:
            if isinstance(holiday_date, str):
                try:
                    holiday_date = pd.to_datetime(holiday_date).date()
                except:
                    continue
            
            daily_mask = index.date == holiday_date
            mask |= daily_mask
        
        return mask
    
    def _determine_compliance_mask(self, ts_data: pd.Series, test_name: str, test_result: TestResult) -> Optional[pd.Series]:
        """
        Determine which timesteps are compliant vs non-compliant.
        Returns a boolean mask where True = compliant, False = non-compliant, NaN = missing data (excluded).
        Missing data (NaN) is NOT considered non-compliant.
        """
        # Try to get threshold from test result
        threshold = self._extract_threshold_from_test(test_result)
        
        if threshold is None:
            # Try to infer from test name patterns
            if 'CO2' in test_name.upper() or 'CO2' in test_result.parameter.upper():
                # Typical CO2 threshold
                threshold = 1000
                # NaN values remain NaN (not counted as non-compliant)
                return ts_data.le(threshold)
            elif 'TEMP' in test_name.upper() or 'TEMPERATURE' in test_result.parameter.upper():
                # Typical temperature range - check both bounds
                if 'HIGH' in test_name.upper() or 'MAX' in test_name.upper():
                    return ts_data.le(26)
                elif 'LOW' in test_name.upper() or 'MIN' in test_name.upper():
                    return ts_data.ge(20)
                else:
                    # Range check
                    return ts_data.ge(20) & ts_data.le(26)
            elif 'HUMID' in test_name.upper() or 'RH' in test_result.parameter.upper():
                # Typical humidity range
                if 'HIGH' in test_name.upper() or 'MAX' in test_name.upper():
                    return ts_data.le(70)
                elif 'LOW' in test_name.upper() or 'MIN' in test_name.upper():
                    return ts_data.ge(30)
                else:
                    return ts_data.ge(30) & ts_data.le(70)
            else:
                # Cannot determine compliance
                return None
        
        # Use threshold from test result
        # Determine if it's max or min threshold based on test name or threshold_type
        if test_result.threshold_type:
            threshold_type = test_result.threshold_type.lower()
            if any(word in threshold_type for word in ['above', 'max', 'upper', 'less']):
                return ts_data.le(threshold)
            elif any(word in threshold_type for word in ['below', 'min', 'lower', 'greater']):
                return ts_data.ge(threshold)
        
        # Fallback to test name analysis
        if any(word in test_name.lower() for word in ['max', 'upper', 'high', 'exceed']):
            return ts_data.le(threshold)
        elif any(word in test_name.lower() for word in ['min', 'lower', 'below']):
            return ts_data.ge(threshold)
        else:
            # Default to max threshold
            return ts_data.le(threshold)
    
    def _get_non_compliant_periods(self, index: pd.DatetimeIndex, compliant_mask: pd.Series, original_values: Optional[pd.Series] = None) -> List[Tuple]:
        """
        Get start and end times of non-compliant periods.
        Returns list of (start_time, end_time) tuples.
        Excludes NaN values (missing data) - only actual non-compliant periods are returned.
        
        Args:
            index: DatetimeIndex of the timeseries
            compliant_mask: Boolean series where True=compliant, False=non-compliant
            original_values: Original values to check for NaN (if not provided, checks mask)
        """
        non_compliant_periods = []
        
        in_non_compliant = False
        start_time = None
        
        for i, timestamp in enumerate(index):
            is_compliant = compliant_mask.iloc[i] if i < len(compliant_mask) else True
            
            # Check for NaN in original values if provided, otherwise check mask
            if original_values is not None:
                is_nan = pd.isna(original_values.iloc[i]) if i < len(original_values) else False
            else:
                is_nan = pd.isna(is_compliant)
            
            # Skip NaN values (missing data) - they are not non-compliant
            if is_nan:
                # If we were in a non-compliant period, end it before the NaN
                if in_non_compliant:
                    non_compliant_periods.append((start_time, timestamp))
                    in_non_compliant = False
                continue
            
            if not is_compliant and not in_non_compliant:
                # Start of non-compliant period
                start_time = timestamp
                in_non_compliant = True
            elif is_compliant and in_non_compliant:
                # End of non-compliant period
                non_compliant_periods.append((start_time, timestamp))
                in_non_compliant = False
        
        # Handle case where data ends during non-compliant period
        if in_non_compliant:
            non_compliant_periods.append((start_time, index[-1]))
        
        return non_compliant_periods
    
    def _confirm_exit(self):
        """Confirm and exit the explorer."""
        if Confirm.ask("\n[bold yellow]Exit explorer?[/bold yellow]", default=True):
            console.print("\n[bold green]Goodbye![/bold green]\n")
            sys.exit(0)


def launch_analysis_explorer(analysis_dir: Path):
    """
    Launch the interactive analysis explorer.
    
    Args:
        analysis_dir: Directory containing analysis results
    """
    if not analysis_dir.exists():
        console.print(f"[red]Analysis directory not found: {analysis_dir}[/red]")
        return
    
    explorer = AnalysisExplorer(analysis_dir)
    explorer.start()
