"""CLI commands for data operations."""

from pathlib import Path

import click
from rich.console import Console

from core.application.use_cases.load_data import LoadDataUseCase

console = Console()


@click.group()
def data():
    """Data loading and management commands."""
    pass


@data.command(name='load')
@click.argument('data_dir', type=click.Path(exists=True, path_type=Path))
@click.option('--dataset-id', default='dataset', help='Dataset identifier')
@click.option('--dataset-name', default='IEQ Dataset', help='Dataset name')
@click.pass_context
def load_data(ctx, data_dir, dataset_id, dataset_name):
    """
    Load building data from directory.

    Examples:
        ieq data load data/building-a
        ieq data load data --dataset-id my_dataset
    """
    console.print(f"\n[cyan]Loading data from:[/cyan] {data_dir}")

    try:
        use_case = LoadDataUseCase()
        dataset, buildings, levels, rooms = use_case.execute(
            data_directory=data_dir,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
        )

        rooms_list = list(rooms.values())
        buildings_list = list(buildings.values())

        console.print("[green]✓ Successfully loaded:[/green]")
        console.print(f"  • {len(buildings_list)} building(s)")
        console.print(f"  • {len(rooms_list)} room(s)")

        # Store in context for potential chaining
        ctx.obj['rooms'] = rooms_list
        ctx.obj['buildings'] = buildings_list
        ctx.obj['dataset'] = dataset

    except Exception as e:
        console.print(f"[red]✗ Error loading data:[/red] {str(e)}")
        if ctx.obj.get('verbose'):
            console.print_exception()
        ctx.exit(1)


@data.command(name='info')
@click.argument('data_dir', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def data_info(ctx, data_dir):
    """
    Show information about data directory.

    Examples:
        ieq data info data/building-a
    """
    console.print(f"\n[cyan]Data Directory Info:[/cyan] {data_dir}\n")

    try:
        # Quick scan without full loading
        buildings = [d for d in data_dir.iterdir() if d.is_dir()]
        console.print(f"Buildings found: {len(buildings)}")

        for building_dir in buildings:
            console.print(f"\n[bold]{building_dir.name}[/bold]")

            # Check for metadata
            metadata_file = building_dir / "metadata.json"
            if metadata_file.exists():
                import json
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    console.print(f"  Name: {metadata.get('name', 'N/A')}")
                    console.print(f"  Type: {metadata.get('type', 'N/A')}")

            # Count levels and rooms
            levels = [d for d in building_dir.iterdir() if d.is_dir()]
            csv_files = list(building_dir.glob("**/*.csv"))
            console.print(f"  Levels: {len(levels)}")
            console.print(f"  CSV files: {len(csv_files)}")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        ctx.exit(1)
