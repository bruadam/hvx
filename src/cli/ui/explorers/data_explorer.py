"""
Interactive data explorer for browsing building datasets.

Provides an interactive CLI interface to navigate building hierarchies,
inspect room data, and preview timeseries data.
"""

import sys
from typing import Optional, List, Any
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.text import Text
from rich import box
import pandas as pd
import matplotlib.pyplot as plt

from src.core.models import BuildingDataset, Building, Level, Room, TimeSeriesData

console = Console()


class DataExplorer:
    """Interactive data explorer for building datasets."""
    
    def __init__(self, dataset: BuildingDataset):
        """
        Initialize the data explorer.
        
        Args:
            dataset: BuildingDataset to explore
        """
        self.dataset = dataset
        self.current_building: Optional[Building] = None
        self.current_level: Optional[Level] = None
        self.current_room: Optional[Room] = None
        self.history: List[str] = []
    
    def start(self):
        """Start the interactive explorer."""
        console.clear()
        self._show_welcome()
        self._main_loop()
    
    def _show_welcome(self):
        """Display welcome message and dataset overview."""
        welcome = """
[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║   Interactive Building Data Explorer            ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]

Navigate through buildings, levels, rooms, and timeseries data.

[bold]Commands:[/bold]
  • Type number to select an item
  • 'back' or 'b' - Go back to previous view
  • 'home' or 'h' - Return to main menu
  • 'quit' or 'q' - Exit explorer
  • 'help' - Show help
        """
        console.print(welcome)
        console.print()
        self._show_dataset_overview()
    
    def _show_dataset_overview(self):
        """Display dataset overview."""
        summary = self.dataset.get_summary()
        
        info = f"""
[bold]Source:[/bold] {summary['source_directory']}
[bold]Buildings:[/bold] {summary['building_count']}
[bold]Total Rooms:[/bold] {summary['total_room_count']}
[bold]Loaded:[/bold] {summary['loaded_at']}
        """
        console.print(Panel(info.strip(), title="Dataset Overview", box=box.ROUNDED))
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
                    self._buildings_list_view()
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' or 'q' to exit[/yellow]")
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
    
    def _buildings_list_view(self):
        """Display list of buildings and handle selection."""
        console.print("\n[bold cyan]═══ Buildings ═══[/bold cyan]\n")
        
        if not self.dataset.buildings:
            console.print("[yellow]No buildings found in dataset[/yellow]")
            return
        
        # Create buildings table
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Building Name", style="cyan bold")
        table.add_column("Rooms", justify="right", style="yellow")
        table.add_column("Levels", justify="right", style="magenta")
        table.add_column("Climate", justify="center", style="green")
        
        for idx, building in enumerate(self.dataset.buildings, 1):
            table.add_row(
                str(idx),
                building.name,
                str(building.get_room_count()),
                str(building.get_level_count()),
                "✓" if building.climate_data else "✗"
            )
        
        console.print(table)
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
            if 0 <= idx < len(self.dataset.buildings):
                self.current_building = self.dataset.buildings[idx]
                self.history.append('buildings')
            else:
                console.print(f"[red]Invalid selection. Please choose 1-{len(self.dataset.buildings)}[/red]")
    
    def _building_view(self):
        """Display building details and navigation options."""
        console.print(f"\n[bold cyan]═══ Building: {self.current_building.name} ═══[/bold cyan]\n")
        
        # Building info
        info = f"""
[bold]ID:[/bold] {self.current_building.id}
[bold]Rooms:[/bold] {self.current_building.get_room_count()}
[bold]Levels:[/bold] {self.current_building.get_level_count()}
        """
        
        if self.current_building.address:
            info += f"[bold]Address:[/bold] {self.current_building.address}\n"
        
        console.print(Panel(info.strip(), box=box.ROUNDED))
        
        # Climate data summary
        if self.current_building.climate_data:
            console.print("\n[bold green]✓ Climate Data Available[/bold green]")
            params = list(self.current_building.climate_data.timeseries.keys())
            console.print(f"  Parameters: {', '.join(params)}")
        else:
            console.print("\n[bold red]✗ No Climate Data[/bold red]")
        
        # Quality summary
        quality = self.current_building.get_data_quality_summary()
        console.print(f"\n[bold]Data Quality:[/bold] {quality['overall_quality_score']:.1f}%")
        console.print(f"  Rooms with data: {quality['rooms_with_data']}/{quality['total_rooms']}")
        
        # Navigation options
        console.print("\n[bold]Navigate to:[/bold]")
        options = []
        
        if self.current_building.levels:
            options.append("1. View by Levels")
        if self.current_building.rooms:
            options.append("2. View all Rooms")
        if self.current_building.climate_data:
            options.append("3. View Climate Data")
        
        for opt in options:
            console.print(f"  {opt}")
        
        console.print("\n  b. Back to buildings list")
        console.print("  q. Quit")
        console.print()
        
        choice = Prompt.ask("[bold]Your choice[/bold]").strip().lower()
        
        if choice == '1' and self.current_building.levels:
            self._levels_list_view()
        elif choice == '2' and self.current_building.rooms:
            self._rooms_list_view()
        elif choice == '3' and self.current_building.climate_data:
            self._climate_data_view()
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
        console.print(f"\n[bold cyan]═══ Levels in {self.current_building.name} ═══[/bold cyan]\n")
        
        # Sort levels by floor number
        sorted_levels = sorted(
            self.current_building.levels,
            key=lambda l: l.floor_number if l.floor_number is not None else 0
        )
        
        # Create levels table
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Level Name", style="magenta bold")
        table.add_column("Floor", justify="center", style="cyan")
        table.add_column("Rooms", justify="right", style="yellow")
        
        for idx, level in enumerate(sorted_levels, 1):
            floor_str = str(level.floor_number) if level.floor_number is not None else "N/A"
            table.add_row(
                str(idx),
                level.name,
                floor_str,
                str(level.get_room_count())
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
            if 0 <= idx < len(sorted_levels):
                self.current_level = sorted_levels[idx]
                self.history.append('building')
            else:
                console.print(f"[red]Invalid selection[/red]")
    
    def _level_view(self):
        """Display level details and rooms."""
        console.print(f"\n[bold cyan]═══ {self.current_level.name} ═══[/bold cyan]\n")
        
        info = f"""
[bold]Building:[/bold] {self.current_building.name}
[bold]Floor Number:[/bold] {self.current_level.floor_number if self.current_level.floor_number is not None else "N/A"}
[bold]Rooms:[/bold] {self.current_level.get_room_count()}
        """
        console.print(Panel(info.strip(), box=box.ROUNDED))
        console.print()
        
        if not self.current_level.rooms:
            console.print("[yellow]No rooms on this level[/yellow]")
            choice = Prompt.ask("[bold]Press Enter to go back[/bold]", default="b")
            self._go_back()
            return
        
        # Create rooms table
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Room Name", style="cyan bold")
        table.add_column("Type", style="blue")
        table.add_column("Parameters", style="green")
        table.add_column("Quality", justify="right", style="yellow")
        
        for idx, room in enumerate(self.current_level.rooms, 1):
            params = ', '.join(room.timeseries.keys()) if room.timeseries else "No data"
            quality = f"{room.get_overall_quality_score():.1f}%"
            room_type = room.room_type.value if room.room_type else "N/A"
            
            table.add_row(
                str(idx),
                room.name[:40],
                room_type,
                params[:30],
                quality
            )
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask(
            "[bold]Select room[/bold] (number) or 'back'",
            default="b"
        ).strip().lower()
        
        if choice in ['b', 'back']:
            self._go_back()
        elif choice in ['q', 'quit']:
            self._confirm_exit()
        elif choice in ['h', 'home']:
            self._go_home()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(self.current_level.rooms):
                self.current_room = self.current_level.rooms[idx]
                self.history.append('level')
            else:
                console.print(f"[red]Invalid selection[/red]")
    
    def _rooms_list_view(self):
        """Display all rooms in building."""
        console.print(f"\n[bold cyan]═══ All Rooms in {self.current_building.name} ═══[/bold cyan]\n")
        
        if not self.current_building.rooms:
            console.print("[yellow]No rooms in this building[/yellow]")
            choice = Prompt.ask("[bold]Press Enter to go back[/bold]", default="b")
            return
        
        # Create rooms table
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Room Name", style="cyan bold", max_width=30)
        table.add_column("Level", style="magenta")
        table.add_column("Type", style="blue")
        table.add_column("Parameters", style="green")
        table.add_column("Quality", justify="right", style="yellow")
        
        # Display first 50 rooms
        display_rooms = self.current_building.rooms[:50]
        
        for idx, room in enumerate(display_rooms, 1):
            params = ', '.join(room.timeseries.keys()) if room.timeseries else "No data"
            quality = f"{room.get_overall_quality_score():.1f}%"
            room_type = room.room_type.value if room.room_type else "N/A"
            level = room.level_id or "N/A"
            
            table.add_row(
                str(idx),
                room.name[:30],
                level,
                room_type,
                params[:30],
                quality
            )
        
        if len(self.current_building.rooms) > 50:
            table.caption = f"Showing 50 of {len(self.current_building.rooms)} rooms"
        
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
            if 0 <= idx < len(display_rooms):
                self.current_room = display_rooms[idx]
                self.history.append('building')
            else:
                console.print(f"[red]Invalid selection[/red]")
    
    def _room_view(self):
        """Display room details and timeseries data."""
        console.print(f"\n[bold cyan]═══ Room: {self.current_room.name} ═══[/bold cyan]\n")
        
        # Room info
        info = f"""
[bold]ID:[/bold] {self.current_room.id}
[bold]Building:[/bold] {self.current_building.name}
[bold]Level:[/bold] {self.current_room.level_id or "N/A"}
[bold]Type:[/bold] {self.current_room.room_type.value if self.current_room.room_type else "N/A"}
[bold]Data Quality:[/bold] {self.current_room.get_overall_quality_score():.1f}%
        """
        
        if self.current_room.area_m2:
            info += f"[bold]Area:[/bold] {self.current_room.area_m2} m²\n"
        if self.current_room.capacity_people:
            info += f"[bold]Capacity:[/bold] {self.current_room.capacity_people} people\n"
        
        console.print(Panel(info.strip(), box=box.ROUNDED))
        
        # Timeseries data
        if not self.current_room.timeseries:
            console.print("\n[yellow]No timeseries data available[/yellow]")
            choice = Prompt.ask("[bold]Press Enter to go back[/bold]", default="b")
            self._go_back()
            return
        
        console.print("\n[bold]Available Parameters:[/bold]")
        
        # Create parameters table
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Parameter", style="cyan bold")
        table.add_column("Unit", style="green")
        table.add_column("Data Points", justify="right", style="yellow")
        table.add_column("Period", style="magenta")
        table.add_column("Quality", justify="right", style="blue")
        
        params_list = list(self.current_room.timeseries.items())
        for idx, (param_name, ts) in enumerate(params_list, 1):
            period = f"{ts.period_start.strftime('%Y-%m-%d')} to {ts.period_end.strftime('%Y-%m-%d')}"
            quality = f"{ts.data_quality.completeness:.1f}%"
            
            table.add_row(
                str(idx),
                param_name,
                ts.unit or "N/A",
                str(ts.data_quality.total_count),
                period,
                quality
            )
        
        console.print()
        console.print(table)
        console.print()
        
        console.print("[bold]Actions:[/bold]")
        console.print("  1-9. View parameter details")
        console.print("  s. Show statistics for all parameters")
        console.print("  p. Plot timeseries (opens matplotlib)")
        console.print("  b. Back")
        console.print()
        
        choice = Prompt.ask("[bold]Your choice[/bold]").strip().lower()
        
        if choice in ['b', 'back']:
            self._go_back()
        elif choice in ['q', 'quit']:
            self._confirm_exit()
        elif choice in ['h', 'home']:
            self._go_home()
        elif choice == 's':
            self._show_room_statistics()
        elif choice == 'p':
            self._plot_timeseries()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(params_list):
                param_name, ts = params_list[idx]
                self._show_timeseries_details(param_name, ts)
            else:
                console.print(f"[red]Invalid selection[/red]")
    
    def _show_timeseries_details(self, param_name: str, ts: TimeSeriesData):
        """Display detailed information about a timeseries."""
        console.print(f"\n[bold cyan]═══ Parameter: {param_name} ═══[/bold cyan]\n")
        
        # Basic info
        info = f"""
[bold]Unit:[/bold] {ts.unit or "N/A"}
[bold]Period:[/bold] {ts.period_start.strftime('%Y-%m-%d %H:%M')} to {ts.period_end.strftime('%Y-%m-%d %H:%M')}
[bold]Data Points:[/bold] {ts.data_quality.total_count}
[bold]Missing:[/bold] {ts.data_quality.missing_count}
[bold]Completeness:[/bold] {ts.data_quality.completeness:.2f}%
[bold]Quality:[/bold] {ts.data_quality.quality_score}
        """
        console.print(Panel(info.strip(), box=box.ROUNDED))
        
        # Statistics
        stats = ts.get_statistics()
        if stats:
            console.print("\n[bold]Statistics:[/bold]")
            stats_table = Table(box=box.SIMPLE, show_header=False)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="yellow", justify="right")
            
            stats_table.add_row("Mean", f"{stats['mean']:.2f}")
            stats_table.add_row("Std Dev", f"{stats['std']:.2f}")
            stats_table.add_row("Min", f"{stats['min']:.2f}")
            stats_table.add_row("Max", f"{stats['max']:.2f}")
            stats_table.add_row("Median", f"{stats['median']:.2f}")
            
            console.print(stats_table)
        
        # Sample data preview
        console.print("\n[bold]Sample Data (first 10 rows):[/bold]")
        sample_df = ts.data.head(10)
        console.print(sample_df.to_string())
        
        console.print()
        choice = Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
    
    def _show_room_statistics(self):
        """Show statistics for all parameters in the room."""
        console.print(f"\n[bold cyan]═══ Statistics for {self.current_room.name} ═══[/bold cyan]\n")
        
        for param_name, ts in self.current_room.timeseries.items():
            stats = ts.get_statistics()
            if stats:
                console.print(f"[bold cyan]{param_name}[/bold cyan] ({ts.unit or 'N/A'})")
                console.print(f"  Mean: {stats['mean']:.2f}, "
                            f"Std: {stats['std']:.2f}, "
                            f"Min: {stats['min']:.2f}, "
                            f"Max: {stats['max']:.2f}")
        
        console.print()
        choice = Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
    
    def _plot_timeseries(self):
        """Plot timeseries data using matplotlib."""
        console.print("\n[bold]Plotting timeseries data...[/bold]")
        
        try:
            # Create figure with subplots for each parameter
            n_params = len(self.current_room.timeseries)
            fig, axes = plt.subplots(n_params, 1, figsize=(12, 3 * n_params))
            
            if n_params == 1:
                axes = [axes]
            
            for idx, (param_name, ts) in enumerate(self.current_room.timeseries.items()):
                ax = axes[idx]
                df = ts.data
                
                # Plot the data
                if param_name in df.columns:
                    df[param_name].plot(ax=ax, title=f"{param_name} ({ts.unit or ''})")
                    ax.set_xlabel("Time")
                    ax.set_ylabel(ts.unit or param_name)
                    ax.grid(True, alpha=0.3)
            
            plt.suptitle(f"Room: {self.current_room.name}", fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.show()
            
            console.print("[green]✓ Plot displayed[/green]")
        
        except Exception as e:
            console.print(f"[red]Error plotting data: {str(e)}[/red]")
        
        console.print()
        choice = Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
    
    def _climate_data_view(self):
        """Display climate data for the building."""
        console.print(f"\n[bold cyan]═══ Climate Data for {self.current_building.name} ═══[/bold cyan]\n")
        
        climate = self.current_building.climate_data
        
        # Climate info
        info = f"""
[bold]Period:[/bold] {climate.period_start.strftime('%Y-%m-%d')} to {climate.period_end.strftime('%Y-%m-%d')}
[bold]Parameters:[/bold] {len(climate.timeseries)}
[bold]Source:[/bold] {Path(climate.source_file).name if climate.source_file else "N/A"}
        """
        console.print(Panel(info.strip(), box=box.ROUNDED))
        
        # Parameters table
        console.print("\n[bold]Available Parameters:[/bold]")
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Parameter", style="cyan bold")
        table.add_column("Unit", style="green")
        table.add_column("Data Points", justify="right", style="yellow")
        table.add_column("Mean", justify="right", style="blue")
        table.add_column("Min / Max", style="magenta")
        
        for param_name, ts in climate.timeseries.items():
            stats = ts.get_statistics()
            if stats:
                min_max = f"{stats['min']:.1f} / {stats['max']:.1f}"
                table.add_row(
                    param_name,
                    ts.unit or "N/A",
                    str(stats['count']),
                    f"{stats['mean']:.2f}",
                    min_max
                )
        
        console.print()
        console.print(table)
        console.print()
        
        choice = Prompt.ask("[bold]Press Enter to go back[/bold]", default="b")
    
    def _show_help(self):
        """Display help information."""
        help_text = """
[bold cyan]═══ Help ═══[/bold cyan]

[bold]Navigation:[/bold]
  • Type a number to select an item from a list
  • 'back' or 'b' - Go back to the previous view
  • 'home' or 'h' - Return to the main buildings list
  • 'quit' or 'q' - Exit the explorer

[bold]Room View:[/bold]
  • View detailed timeseries information
  • Display statistics for all parameters
  • Plot timeseries data (opens matplotlib window)

[bold]Tips:[/bold]
  • Data quality scores indicate completeness (High: >90%, Medium: 75-90%, Low: <75%)
  • Use levels view for organized navigation by floor
  • Use all rooms view to see all rooms at once
        """
        console.print()
        console.print(Panel(help_text.strip(), box=box.ROUNDED))
        console.print()
        choice = Prompt.ask("[bold]Press Enter to continue[/bold]", default="")
    
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
        elif previous == 'buildings':
            self.current_building = None
            self.current_level = None
            self.current_room = None
    
    def _go_home(self):
        """Return to main buildings list."""
        self.current_building = None
        self.current_level = None
        self.current_room = None
        self.history = []
    
    def _confirm_exit(self):
        """Confirm and exit the explorer."""
        if Confirm.ask("\n[bold yellow]Exit explorer?[/bold yellow]", default=True):
            console.print("\n[bold green]Goodbye![/bold green]\n")
            sys.exit(0)


def launch_explorer(dataset: BuildingDataset):
    """
    Launch the interactive data explorer.
    
    Args:
        dataset: BuildingDataset to explore
    """
    explorer = DataExplorer(dataset)
    explorer.start()
