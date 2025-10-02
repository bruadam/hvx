"""
Data loading CLI commands for HVX.
"""

import click
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box

from src.services.data_loader_service import create_data_loader

console = Console()


@click.group(name='data')
def data():
    """Data loading and management commands."""
    pass


@data.command(name='load')
@click.argument('source_dir', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output file path for saving the dataset')
@click.option('--format', '-f', type=click.Choice(['json', 'pickle', 'both']), default='json',
              help='Output format (json for summary, pickle for full data)')
@click.option('--validate/--no-validate', default=True,
              help='Validate data quality during loading')
@click.option('--infer-levels/--no-infer-levels', default=True,
              help='Automatically infer building levels from room names')
@click.option('--infer-room-types/--no-infer-room-types', default=True,
              help='Automatically infer room types from names')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed loading information')
def load_data(source_dir: Path, output: Optional[Path], format: str, 
              validate: bool, infer_levels: bool, infer_room_types: bool, verbose: bool):
    """
    Load building data from a directory structure.
    
    Expected structure:
    
    \b
    source_dir/
        building-1/
            climate/
                climate-data.csv
            sensors/
                room1.csv
                room2.csv
        building-2/
            ...
    
    Examples:
    
    \b
        # Load data and display summary
        hvx data load data/samples/sample-extensive-data
        
        # Load and save to JSON
        hvx data load data/samples/sample-extensive-data -o output/dataset.json
        
        # Load and save full data to pickle
        hvx data load data/samples/sample-extensive-data -o output/dataset.pkl -f pickle
        
        # Load without validation
        hvx data load data/samples/sample-extensive-data --no-validate
    """
    
    # Set up logging verbosity
    if verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
    
    console.print(f"\n[bold blue]Loading building data from:[/bold blue] {source_dir}\n")
    
    try:
        # Create data loader
        loader = create_data_loader(
            auto_infer_levels=infer_levels,
            auto_infer_room_types=infer_room_types
        )
        
        # Load data with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading data...", total=None)
            dataset = loader.load_from_directory(source_dir, validate=validate)
            progress.update(task, completed=True)
        
        # Display summary
        _display_dataset_summary(dataset)
        
        # Save if output specified
        if output:
            _save_dataset(dataset, output, format)
        
        console.print(f"\n[bold green]✓[/bold green] Data loading completed successfully!\n")
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        raise click.Abort()


@data.command(name='inspect')
@click.argument('data_file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--building', '-b', help='Filter by building ID')
@click.option('--show-rooms/--no-show-rooms', default=True, 
              help='Show room-level details')
@click.option('--show-quality/--no-show-quality', default=True,
              help='Show data quality metrics')
def inspect_data(data_file: Path, building: Optional[str], show_rooms: bool, show_quality: bool):
    """
    Inspect a loaded dataset from a pickle file.
    
    Examples:
    
    \b
        # Inspect full dataset
        hvx data inspect output/dataset.pkl
        
        # Inspect specific building
        hvx data inspect output/dataset.pkl -b building_1
        
        # Show only building-level info
        hvx data inspect output/dataset.pkl --no-show-rooms
    """
    
    try:
        from src.models.building_data import BuildingDataset
        
        console.print(f"\n[bold blue]Inspecting dataset:[/bold blue] {data_file}\n")
        
        # Load dataset
        dataset = BuildingDataset.load_from_pickle(data_file)
        
        # Filter by building if specified
        if building:
            bldg = dataset.get_building(building)
            if not bldg:
                console.print(f"[bold red]✗ Error:[/bold red] Building '{building}' not found\n")
                raise click.Abort()
            
            _display_building_details(bldg, show_rooms=show_rooms, show_quality=show_quality)
        else:
            _display_dataset_summary(dataset)
            
            if show_rooms:
                for bldg in dataset.buildings:
                    console.print()
                    _display_building_details(bldg, show_rooms=True, show_quality=show_quality)
        
        console.print()
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        raise click.Abort()


def _display_dataset_summary(dataset):
    """Display dataset summary in a nice table."""
    summary = dataset.get_summary()
    
    # Overview panel
    overview = f"""
[bold]Source:[/bold] {summary['source_directory']}
[bold]Loaded:[/bold] {summary['loaded_at']}
[bold]Buildings:[/bold] {summary['building_count']}
[bold]Total Rooms:[/bold] {summary['total_room_count']}
    """
    console.print(Panel(overview.strip(), title="Dataset Overview", box=box.ROUNDED))
    
    # Buildings table
    if summary['buildings']:
        table = Table(title="\nBuildings", box=box.SIMPLE)
        table.add_column("Building ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Rooms", justify="right", style="yellow")
        table.add_column("Levels", justify="right", style="magenta")
        table.add_column("Climate Data", justify="center")
        
        for bldg in summary['buildings']:
            table.add_row(
                bldg['id'],
                bldg['name'],
                str(bldg['room_count']),
                str(bldg['level_count']),
                "✓" if bldg['has_climate_data'] else "✗"
            )
        
        console.print(table)


def _display_building_details(building, show_rooms: bool = True, show_quality: bool = True):
    """Display detailed building information."""
    
    # Building header
    console.print(f"\n[bold cyan]Building: {building.name}[/bold cyan] (ID: {building.id})")
    
    # Basic info
    info = f"""
[bold]Rooms:[/bold] {building.get_room_count()}
[bold]Levels:[/bold] {building.get_level_count()}
[bold]Climate Data:[/bold] {"Available" if building.climate_data else "Not available"}
    """
    
    if building.climate_data:
        params = list(building.climate_data.timeseries.keys())
        info += f"[bold]Climate Parameters:[/bold] {', '.join(params)}\n"
    
    console.print(Panel(info.strip(), box=box.ROUNDED))
    
    # Quality summary
    if show_quality:
        quality_summary = building.get_data_quality_summary()
        console.print(f"\n[bold]Data Quality:[/bold]")
        console.print(f"  Overall Quality Score: [yellow]{quality_summary['overall_quality_score']:.1f}%[/yellow]")
        console.print(f"  Rooms with Data: [cyan]{quality_summary['rooms_with_data']}/{quality_summary['total_rooms']}[/cyan]")
    
    # Rooms table
    if show_rooms and building.rooms:
        table = Table(title="\nRooms", box=box.SIMPLE)
        table.add_column("Room ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Level", style="magenta")
        table.add_column("Type", style="blue")
        table.add_column("Parameters", style="green")
        
        if show_quality:
            table.add_column("Quality", justify="right", style="yellow")
        
        for room in building.rooms[:20]:  # Limit to first 20 rooms
            params = ', '.join(room.timeseries.keys())
            level = room.level_id or "N/A"
            room_type = room.room_type.value if room.room_type else "N/A"
            
            row = [
                room.id,
                room.name[:30],  # Truncate long names
                level,
                room_type,
                params
            ]
            
            if show_quality:
                quality_score = room.get_overall_quality_score()
                row.append(f"{quality_score:.1f}%")
            
            table.add_row(*row)
        
        if len(building.rooms) > 20:
            table.caption = f"Showing 20 of {len(building.rooms)} rooms"
        
        console.print(table)


def _save_dataset(dataset, output_path: Path, format: str):
    """Save dataset to file(s)."""
    
    console.print(f"\n[bold blue]Saving dataset...[/bold blue]")
    
    try:
        if format in ['json', 'both']:
            json_path = output_path.with_suffix('.json') if output_path.suffix != '.json' else output_path
            dataset.save_to_json(json_path)
            console.print(f"  [green]✓[/green] Saved summary to: {json_path}")
        
        if format in ['pickle', 'both']:
            pkl_path = output_path.with_suffix('.pkl') if output_path.suffix != '.pkl' else output_path
            dataset.save_to_pickle(pkl_path)
            console.print(f"  [green]✓[/green] Saved full dataset to: {pkl_path}")
        
    except Exception as e:
        console.print(f"  [red]✗[/red] Error saving: {str(e)}")
        raise
