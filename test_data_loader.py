#!/usr/bin/env python3
"""
Test script for data loader service.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.data_loader_service import create_data_loader
from rich.console import Console
from rich.table import Table

console = Console()

def main():
    console.print("\n[bold blue]Testing Data Loader Service[/bold blue]\n")
    
    # Create loader
    loader = create_data_loader(
        auto_infer_levels=True,
        auto_infer_room_types=True
    )
    
    # Load sample data
    data_dir = Path("data/samples/sample-extensive-data")
    
    if not data_dir.exists():
        console.print(f"[red]Error:[/red] Data directory not found: {data_dir}")
        return
    
    console.print(f"Loading data from: {data_dir}\n")
    
    try:
        dataset = loader.load_from_directory(data_dir, validate=True)
        
        # Display summary
        console.print(f"\n[green]✓[/green] Successfully loaded dataset!\n")
        console.print(f"[bold]Buildings:[/bold] {dataset.get_building_count()}")
        console.print(f"[bold]Total Rooms:[/bold] {dataset.get_total_room_count()}\n")
        
        # Display building table
        table = Table(title="Buildings")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Rooms", justify="right", style="yellow")
        table.add_column("Levels", justify="right", style="magenta")
        table.add_column("Climate", justify="center")
        
        for building in dataset.buildings:
            table.add_row(
                building.id,
                building.name,
                str(building.get_room_count()),
                str(building.get_level_count()),
                "✓" if building.climate_data else "✗"
            )
        
        console.print(table)
        
        # Display sample room data
        if dataset.buildings and dataset.buildings[0].rooms:
            console.print("\n[bold]Sample Room Details (first room):[/bold]")
            room = dataset.buildings[0].rooms[0]
            console.print(f"  ID: {room.id}")
            console.print(f"  Name: {room.name}")
            console.print(f"  Level: {room.level_id or 'N/A'}")
            console.print(f"  Type: {room.room_type.value if room.room_type else 'N/A'}")
            console.print(f"  Parameters: {', '.join(room.timeseries.keys())}")
            console.print(f"  Quality Score: {room.get_overall_quality_score():.1f}%")
            
            # Show first parameter details
            if room.timeseries:
                param_name = list(room.timeseries.keys())[0]
                ts = room.timeseries[param_name]
                console.print(f"\n  [bold]{param_name.title()} Data:[/bold]")
                console.print(f"    Period: {ts.period_start} to {ts.period_end}")
                console.print(f"    Records: {len(ts.data)}")
                console.print(f"    Completeness: {ts.data_quality.completeness:.1f}%")
        
        # Save dataset
        output_dir = Path("output/data_loader_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_file = output_dir / "dataset_summary.json"
        pkl_file = output_dir / "dataset.pkl"
        
        dataset.save_to_json(json_file)
        dataset.save_to_pickle(pkl_file)
        
        console.print(f"\n[green]✓[/green] Saved dataset to:")
        console.print(f"  Summary: {json_file}")
        console.print(f"  Full data: {pkl_file}\n")
        
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
