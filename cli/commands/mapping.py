"""
Mapping command module for IEQ Analytics CLI.

Handles mapping of raw CSV sensor data to standardized IEQ format including:
- Interactive column mapping
- Auto-detection of column patterns
- Building and room metadata extraction
- Configuration persistence
"""

import click
from pathlib import Path
from typing import Optional
import json
import sys
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

console = Console()


@click.command()
@click.option(
    '--data-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Directory containing raw CSV files to map'
)
@click.option(
    '--config',
    type=click.Path(path_type=Path),
    help='Path to mapping configuration file'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
    help='Output directory for mapped data'
)
@click.option(
    '--interactive/--auto',
    default=False,
    help='Interactive column mapping vs automatic detection'
)
@click.option(
    '--room-tag',
    type=str,
    help='Tag to apply to all processed rooms'
)
@click.option(
    '--batch-size',
    type=int,
    default=10,
    help='Number of files to process in each batch'
)
@click.pass_context
def mapping(
    ctx,
    data_dir: Optional[Path],
    config: Optional[Path],
    output_dir: Optional[Path],
    interactive: bool,
    room_tag: Optional[str],
    batch_size: int
):
    """🗂️ Map raw CSV sensor data to standardized IEQ format.
    
    Transforms raw sensor data files into a standardized format with:
    - Consistent column naming
    - Building and room metadata
    - Data validation and cleaning
    - Configuration persistence for future runs
    """
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    
    # Set defaults based on workspace structure
    data_dir = data_dir or workspace / "data" / "raw"
    config = config or workspace / "config" / "mapping_config.json"
    output_dir = output_dir or workspace / "output" / "mapped"
    
    console.print("🗂️ [bold blue]Starting Data Mapping Process...[/bold blue]")
    console.print(f"📂 Data directory: {data_dir}")
    console.print(f"⚙️ Configuration: {config}")
    console.print(f"📤 Output directory: {output_dir}")
    
    # Validate inputs
    if not data_dir.exists():
        console.print(f"[red]❌ Data directory not found: {data_dir}[/red]")
        console.print("Place raw CSV files in the data directory.")
        sys.exit(1)
    
    try:
        # Import mapping components
        from ieq_analytics.mapping import DataMapper
        
        # Initialize mapper
        mapper = DataMapper()
        
        # Load existing configuration if available
        if config.exists():
            console.print(f"📋 Loading existing configuration from {config}")
            mapper.load_config(config)
        else:
            console.print("📋 No existing configuration found. Starting fresh.")
        
        # Create output directories
        mapped_data_dir = output_dir / "mapped_data"
        mapped_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Get list of files to process
        csv_files = list(data_dir.glob("*.csv"))
        if not csv_files:
            console.print(f"[red]❌ No CSV files found in {data_dir}[/red]")
            console.print("Add CSV files to the data directory and try again.")
            sys.exit(1)
        
        console.print(f"📄 Found {len(csv_files)} CSV files to process")
        
        # Process files in batches with progress tracking
        processed_data = []
        processing_errors = []
        total_files = len(csv_files)
        
        for i in track(range(0, total_files, batch_size), description="Processing batches..."):
            batch_files = csv_files[i:i+batch_size]
            
            for file_path in batch_files:
                try:
                    console.print(f"📊 Processing: [cyan]{file_path.name}[/cyan]")
                    
                    # Load and analyze file
                    import pandas as pd
                    df = pd.read_csv(file_path)
                    
                    if df.empty:
                        console.print(f"[yellow]⚠️ Skipping empty file: {file_path.name}[/yellow]")
                        continue
                    
                    # Try to find existing mapping from loaded config first
                    existing_mapping = mapper.config.get_mapping_for_file(file_path.name)
                    
                    if existing_mapping:
                        # Use the existing mapping from config
                        mapping = existing_mapping.column_mappings
                        console.print(f"✅ Using existing mapping for: {file_path.name}")
                        # Map the file with the full configuration (including room type)
                        ieq_data = mapper.map_file(file_path, mapping, existing_mapping)
                    elif interactive:
                        # Interactive mapping for this file if no existing mapping found
                        mapping = mapper.interactive_column_mapping(file_path.name, df.columns.tolist())
                        ieq_data = mapper.map_file(file_path, mapping)
                    else:
                        # Auto-suggest mapping if no config and non-interactive
                        mapping = mapper.suggest_column_mappings(df.columns.tolist())
                        console.print(f"🤖 Auto-suggested mapping for: {file_path.name}")
                        ieq_data = mapper.map_file(file_path, mapping)
                    
                    if not mapping:
                        console.print(f"[yellow]⚠️ No valid mapping found for: {file_path.name}[/yellow]")
                        continue
                    if ieq_data:
                        # Save mapped file
                        output_file = mapped_data_dir / f"{ieq_data.room_id}_processed.csv"
                        ieq_data.data.to_csv(output_file)
                        processed_data.append(ieq_data)
                        
                        console.print(f"✅ Mapped: {file_path.name} → {output_file.name}")
                    else:
                        console.print(f"[yellow]⚠️ Failed to map: {file_path.name}[/yellow]")
                    
                except Exception as e:
                    error_info = {
                        'file': str(file_path),
                        'error': str(e)
                    }
                    processing_errors.append(error_info)
                    console.print(f"[red]❌ Error processing {file_path.name}: {e}[/red]")
                    continue
        
        # Apply room tags if specified
        if room_tag:
            console.print(f"🏷️ Applying room tag: [cyan]{room_tag}[/cyan]")
            for building in mapper.buildings.values():
                for room in building.rooms:
                    if room_tag not in room.tags:
                        room.tags.append(room_tag)
        
        # Save configuration for future use
        console.print("💾 Saving mapping configuration...")
        config.parent.mkdir(parents=True, exist_ok=True)
        mapper.save_config(config)
        
        # Export building and room metadata
        console.print("📋 Exporting building metadata...")
        buildings_data = {}
        for building_id, building in mapper.buildings.items():
            building_dict = building.model_dump()
            # Convert enum values to their string representations
            for room in building_dict.get('rooms', []):
                if 'room_type' in room and hasattr(room['room_type'], 'value'):
                    room['room_type'] = room['room_type'].value
                elif 'room_type' in room and isinstance(room['room_type'], str) and room['room_type'].startswith('RoomType.'):
                    # Handle case where it's already a string representation
                    from ieq_analytics.enums import RoomType
                    enum_name = room['room_type'].split('.')[1]
                    try:
                        room['room_type'] = getattr(RoomType, enum_name).value
                    except AttributeError:
                        room['room_type'] = 'other'
            buildings_data[building_id] = building_dict
        
        metadata_path = output_dir / "buildings_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(buildings_data, f, indent=2, ensure_ascii=False)
        
        # Save processing summary
        processing_summary = {
            'total_files': len(csv_files),
            'processed_files': len(processed_data),
            'failed_files': len(processing_errors),
            'buildings_created': len(mapper.buildings),
            'total_rooms': sum(len(b.rooms) for b in mapper.buildings.values()),
            'output_directory': str(mapped_data_dir),
            'errors': processing_errors
        }
        
        summary_path = output_dir / "processing_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(processing_summary, f, indent=2, default=str)
        
        # Update pipeline state if available
        pipeline_state = ctx.obj.get('pipeline_state')
        if pipeline_state:
            pipeline_state.update_mapping_state(
                len(processed_data),
                len(mapper.buildings),
                sum(len(b.rooms) for b in mapper.buildings.values())
            )
        
        # Display success summary
        success_rate = (len(processed_data) / len(csv_files)) * 100 if csv_files else 0
        
        success_panel = Panel.fit(
            f"[bold green]✅ Mapping completed successfully![/bold green]\n\n"
            f"📊 Processed: {len(processed_data)}/{len(csv_files)} files ({success_rate:.1f}%)\n"
            f"🏢 Buildings: {len(mapper.buildings)}\n"
            f"🏠 Total rooms: {sum(len(b.rooms) for b in mapper.buildings.values())}\n"
            f"📁 Output: {mapped_data_dir}\n"
            f"💾 Metadata: {metadata_path}\n"
            f"⚙️ Config: {config}\n\n"
            f"[italic]Next step: Run analysis with 'ieq-analytics analyze'[/italic]",
            title="🎉 Mapping Results",
            border_style="green"
        )
        console.print(success_panel)
        
        if processing_errors:
            console.print(f"\n[yellow]⚠️ {len(processing_errors)} files had processing errors. Check {summary_path} for details.[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Mapping failed: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)
