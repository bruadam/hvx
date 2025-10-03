#!/usr/bin/env python3
"""
Test script for the data structure detector.

This script demonstrates the structure detection capabilities
for various directory layouts.
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box

from src.core.services.data_structure_detector import create_structure_detector

console = Console()


def test_structure_detection():
    """Test the structure detector with various directory structures."""
    
    detector = create_structure_detector()
    
    # Test cases
    test_directories = [
        "data/samples/sample-extensive-data",  # Standard nested structure
        "data",  # Root data directory
        "output",  # Non-data directory
        "/nonexistent/path",  # Non-existent path
    ]
    
    console.print("\n[bold cyan]Testing Directory Structure Detection[/bold cyan]\n")
    
    for test_dir in test_directories:
        console.print(f"\n{'='*60}")
        console.print(f"[bold]Testing:[/bold] {test_dir}")
        console.print('='*60)
        
        path = Path(test_dir)
        analysis = detector.analyze_directory(path)
        
        # Create results table
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        
        table.add_row("Structure Type", analysis.structure_type.value)
        table.add_row("Confidence", f"{analysis.confidence:.0%}")
        table.add_row("Buildings", str(analysis.building_count))
        table.add_row("Sensor Files", str(analysis.total_sensor_files))
        table.add_row("Has Climate", "Yes" if analysis.has_climate_data else "No")
        
        console.print(table)
        
        # Show issues
        if analysis.issues:
            console.print("\n[bold red]Issues:[/bold red]")
            for issue in analysis.issues:
                console.print(f"  • {issue}")
        
        # Show recommendations
        if analysis.recommendations:
            console.print("\n[bold cyan]Recommendations:[/bold cyan]")
            for rec in analysis.recommendations:
                console.print(f"  • {rec}")
        
        # Show details
        if analysis.details:
            console.print("\n[dim]Details:[/dim]")
            for key, value in analysis.details.items():
                console.print(f"  {key}: {value}")


def test_reorganization_guide():
    """Test the reorganization guide generation."""
    
    console.print("\n\n[bold cyan]Testing Reorganization Guide Generation[/bold cyan]\n")
    
    detector = create_structure_detector()
    
    # Test with a non-existent directory to get the guide
    test_path = Path("/test/unknown/structure")
    analysis = detector.analyze_directory(test_path)
    
    if analysis.structure_type.value == "unknown":
        guide = detector.get_reorganization_guide(analysis)
        console.print(guide)


if __name__ == "__main__":
    try:
        test_structure_detection()
        test_reorganization_guide()
        
        console.print("\n[green]✓ Test completed successfully![/green]\n")
        
    except Exception as e:
        console.print(f"\n[red]✗ Error during testing:[/red] {str(e)}")
        import traceback
        traceback.print_exc()
