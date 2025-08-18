"""
Command Line Interface for IEQ Analytics Engine.
"""

import click
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import json
import sys

from .mapping import DataMapper
from .analytics import IEQAnalytics
from .models import MappingConfig


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """IEQ Analytics Engine - Comprehensive Indoor Environmental Quality Analysis Tool"""
    pass


@cli.command()
@click.option(
    '--data-dir-path', 
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("data/raw/concatenated"),
    help='Path to directory containing CSV files'
)
@click.option(
    '--config-path',
    type=click.Path(path_type=Path),
    default=Path("config/mapping_config.json"),
    help='Path to mapping configuration file'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
    default=Path("output"),
    help='Output directory for processed data and results'
)
@click.option(
    '--interactive/--no-interactive',
    default=True,
    help='Enable interactive column mapping'
)
@click.option(
    '--room-tag',
    type=str,
    help='Optional tag to apply to all rooms'
)
def mapping(
    data_dir_path: Path,
    config_path: Path,
    output_dir: Path,
    interactive: bool,
    room_tag: Optional[str]
):
    """Map raw CSV sensor data to standardized IEQ format."""
    
    click.echo("🚀 Starting IEQ Data Mapping Process...")
    click.echo(f"📂 Data directory: {data_dir_path}")
    click.echo(f"⚙️  Configuration: {config_path}")
    click.echo(f"📤 Output directory: {output_dir}")
    
    try:
        # Initialize mapper
        mapper = DataMapper()
        
        # Load existing configuration if available
        if config_path.exists():
            click.echo(f"📋 Loading existing configuration from {config_path}")
            mapper.load_config(config_path)
        else:
            click.echo("📋 No existing configuration found. Starting fresh.")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process files
        processed_data = mapper.process_directory(
            data_dir=data_dir_path,
            output_dir=output_dir / "mapped_data",
            interactive=interactive
        )
        
        # Apply room tags if specified
        if room_tag:
            click.echo(f"🏷️  Applying room tag: {room_tag}")
            for building in mapper.buildings.values():
                for room in building.rooms:
                    if room_tag not in room.tags:
                        room.tags.append(room_tag)
        
        # Save configuration for future use
        config_path.parent.mkdir(parents=True, exist_ok=True)
        mapper.save_config(config_path)
        
        # Export building and room metadata
        buildings_data = []
        for building in mapper.buildings.values():
            building_dict = building.dict()
            buildings_data.append(building_dict)
        
        metadata_path = output_dir / "buildings_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(buildings_data, f, indent=2, default=str)
        
        click.echo(f"✅ Mapping completed successfully!")
        click.echo(f"📊 Processed {len(processed_data)} files")
        click.echo(f"🏢 Created {len(mapper.buildings)} buildings")
        click.echo(f"🏠 Total rooms: {sum(len(b.rooms) for b in mapper.buildings.values())}")
        click.echo(f"💾 Metadata saved to: {metadata_path}")
        
    except Exception as e:
        click.echo(f"❌ Error during mapping: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--data-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("output/mapped_data"),
    help='Directory containing mapped IEQ data files'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
    default=Path("output/analysis"),
    help='Output directory for analysis results'
)
@click.option(
    '--buildings-metadata',
    type=click.Path(exists=True, path_type=Path),
    default=Path("output/buildings_metadata.json"),
    help='Path to buildings metadata JSON file'
)
@click.option(
    '--export-formats',
    multiple=True,
    type=click.Choice(['json', 'csv', 'pdf']),
    default=['json', 'csv'],
    help='Export formats for analysis results'
)
@click.option(
    '--generate-plots/--no-plots',
    default=True,
    help='Generate visualization plots'
)
def analyze(
    data_dir: Path,
    output_dir: Path,
    buildings_metadata: Path,
    export_formats: List[str],
    generate_plots: bool
):
    """Perform comprehensive IEQ analysis on mapped data."""
    
    click.echo("🔬 Starting IEQ Analysis Engine...")
    click.echo(f"📂 Data directory: {data_dir}")
    click.echo(f"📤 Output directory: {output_dir}")
    
    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize analytics engine
        analytics = IEQAnalytics()
        
        # Load buildings metadata
        if buildings_metadata.exists():
            with open(buildings_metadata, 'r') as f:
                buildings_data = json.load(f)
            click.echo(f"📋 Loaded metadata for {len(buildings_data)} buildings")
        else:
            click.echo("⚠️  No buildings metadata found. Proceeding without building context.")
            buildings_data = []
        
        # Find all mapped data files
        data_files = list(data_dir.glob("*_processed.csv"))
        if not data_files:
            click.echo("❌ No processed data files found!", err=True)
            sys.exit(1)
        
        click.echo(f"📊 Found {len(data_files)} data files to analyze")
        
        # Analyze each room
        room_analyses = []
        building_groups = {}
        
        for data_file in data_files:
            click.echo(f"🔍 Analyzing: {data_file.name}")
            
            try:
                # Load the mapped data
                import pandas as pd
                df = pd.read_csv(data_file, index_col=0, parse_dates=True)
                
                # Extract room and building IDs from filename
                room_id = data_file.stem.replace('_processed', '')
                
                # Try to extract building ID (assuming format: building_room)
                if '_' in room_id:
                    building_id = '_'.join(room_id.split('_')[:-1])
                else:
                    building_id = "unknown_building"
                
                # Create IEQData object
                from .models import IEQData
                ieq_data = IEQData(
                    room_id=room_id,
                    building_id=building_id,
                    data=df,
                    source_files=[str(data_file)],
                    data_period_start=df.index.min() if not df.empty else None,
                    data_period_end=df.index.max() if not df.empty else None,
                    quality_score=None  # Set to None or compute as needed
                )
                
                # Perform analysis
                analysis_result = analytics.analyze_room_data(ieq_data)
                room_analyses.append(analysis_result)
                
                # Group by building
                if building_id not in building_groups:
                    building_groups[building_id] = []
                building_groups[building_id].append(analysis_result)
                
                # Generate plots if requested
                if generate_plots:
                    plots_dir = output_dir / "plots" / room_id
                    generated_plots = analytics.generate_visualizations(ieq_data, plots_dir)
                    analysis_result["generated_plots"] = generated_plots
                
                click.echo(f"✅ Completed analysis for {room_id}")
                
            except Exception as e:
                click.echo(f"❌ Error analyzing {data_file.name}: {e}", err=True)
                continue
        
        # Perform building-level analysis
        building_analyses = {}
        for building_id, room_results in building_groups.items():
            click.echo(f"🏢 Aggregating analysis for building: {building_id}")
            building_analysis = analytics.aggregate_building_analysis(room_results)
            building_analyses[building_id] = building_analysis
        
        # Export results
        click.echo("💾 Exporting analysis results...")
        
        exported_files = analytics.export_analysis_results(
            room_analyses=room_analyses,
            building_analysis=building_analyses,
            output_dir=output_dir,
            formats=list(export_formats)
        )
        
        # Create summary report
        summary = {
            "analysis_summary": {
                "total_rooms_analyzed": len(room_analyses),
                "total_buildings": len(building_analyses),
                "analysis_timestamp": datetime.now().isoformat(),
                "export_formats": list(export_formats),
                "plots_generated": generate_plots
            },
            "building_summaries": {
                building_id: {
                    "room_count": analysis["room_count"],
                    "average_data_quality": analysis["data_quality_summary"]["average_quality_score"],
                    "recommendations_count": len(analysis["building_recommendations"])
                }
                for building_id, analysis in building_analyses.items()
            },
            "exported_files": exported_files
        }
        
        summary_path = output_dir / "analysis_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        click.echo(f"🎉 Analysis completed successfully!")
        click.echo(f"📊 Analyzed {len(room_analyses)} rooms across {len(building_analyses)} buildings")
        click.echo(f"📁 Results exported to: {output_dir}")
        click.echo(f"📋 Summary available at: {summary_path}")
        
        # Display key insights
        total_quality_score = sum(
            analysis.get("data_quality", {}).get("overall_score", 0) 
            for analysis in room_analyses
        ) / len(room_analyses) if room_analyses else 0
        
        click.echo(f"\n📈 Key Insights:")
        click.echo(f"   Average Data Quality Score: {total_quality_score:.3f}")
        
        # Count rooms with issues
        quality_issues = sum(
            1 for analysis in room_analyses 
            if analysis.get("data_quality", {}).get("overall_score", 0) < 0.8
        )
        click.echo(f"   Rooms with Data Quality Issues: {quality_issues}/{len(room_analyses)}")
        
        # Count comfort issues
        comfort_issues = 0
        for analysis in room_analyses:
            for param, categories in analysis.get("comfort_analysis", {}).items():
                category_ii = categories.get("II", {})
                if category_ii.get("compliance_percentage", 100) < 80:
                    comfort_issues += 1
                    break
        
        click.echo(f"   Rooms with Comfort Issues: {comfort_issues}/{len(room_analyses)}")
        
    except Exception as e:
        click.echo(f"❌ Error during analysis: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--data-dir-path',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Path to directory containing CSV files to analyze'
)
@click.option(
    '--output-format',
    type=click.Choice(['table', 'json']),
    default='table',
    help='Output format for the analysis results'
)
def inspect(data_dir_path: Path, output_format: str):
    """Inspect CSV files and analyze their structure."""
    
    click.echo(f"🔍 Inspecting files in: {data_dir_path}")
    
    try:
        # Initialize mapper for analysis
        mapper = DataMapper()
        
        # Analyze files
        analysis = mapper.analyze_files(data_dir_path)
        
        if output_format == 'json':
            click.echo(json.dumps(analysis, indent=2, default=str))
        else:
            # Display in table format
            click.echo(f"\n📊 Analysis Results:")
            click.echo(f"   Total Files: {len(analysis['files'])}")
            click.echo(f"   Unique Columns: {len(analysis['unique_columns'])}")
            click.echo(f"   Building Patterns: {len(analysis['building_patterns'])}")
            click.echo(f"   Room Patterns: {len(analysis['room_patterns'])}")
            
            click.echo(f"\n🏢 Detected Buildings:")
            for building in analysis['building_patterns']:
                click.echo(f"   - {building}")
            
            click.echo(f"\n🏠 Room Pattern Examples:")
            for room in analysis['room_patterns'][:10]:  # Show first 10
                click.echo(f"   - {room}")
            
            click.echo(f"\n📋 Most Common Columns:")
            sorted_columns = sorted(
                analysis['column_frequency'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for col, freq in sorted_columns[:15]:  # Show top 15
                click.echo(f"   - {col}: {freq} files")
            
            click.echo(f"\n💡 Suggested Mappings:")
            for col in analysis['unique_columns'][:10]:  # Show first 10
                suggestions = mapper.suggest_column_mappings([col])
                if col in suggestions:
                    click.echo(f"   - {col} → {suggestions[col]}")
    
    except Exception as e:
        click.echo(f"❌ Error during inspection: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--config-path',
    type=click.Path(path_type=Path),
    default=Path("config/mapping_config.json"),
    help='Path to save the configuration template'
)
def init_config(config_path: Path):
    """Initialize a mapping configuration template."""
    
    click.echo("🛠️  Creating mapping configuration template...")
    
    try:
        # Create config directory
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create template configuration
        from .models import IEQParameter
        template_config = MappingConfig(
            default_building_name="Sample Building",
            timestamp_format="%Y-%m-%d %H:%M:%S",
            required_parameters=[
                IEQParameter.TIMESTAMP,
                IEQParameter.TEMPERATURE,
                IEQParameter.HUMIDITY,
                IEQParameter.CO2
            ]
        )
        
        # Save template
        template_config.save_to_file(config_path)
        
        click.echo(f"✅ Configuration template created at: {config_path}")
        click.echo("📝 Edit this file to customize column mappings for your data")
        
    except Exception as e:
        click.echo(f"❌ Error creating configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--data-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("data/raw/concatenated"),
    help='Input data directory'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
    default=Path("output"),
    help='Output directory'
)
@click.option(
    '--config-path',
    type=click.Path(path_type=Path),
    default=Path("config/mapping_config.json"),
    help='Mapping configuration file'
)
@click.option(
    '--interactive/--no-interactive',
    default=True,
    help='Enable interactive mode'
)
@click.option(
    '--generate-plots/--no-plots',
    default=True,
    help='Generate visualization plots'
)
def run(
    data_dir: Path,
    output_dir: Path,
    config_path: Path,
    interactive: bool,
    generate_plots: bool
):
    """Run the complete IEQ analysis pipeline (mapping + analysis)."""
    
    click.echo("🚀 Starting Complete IEQ Analysis Pipeline...")
    
    try:
        # Step 1: Mapping
        click.echo("\n📋 Step 1: Data Mapping")
        
        from click.testing import CliRunner
        runner = CliRunner()
        
        mapping_result = runner.invoke(mapping, [
            '--data-dir-path', str(data_dir),
            '--config-path', str(config_path),
            '--output-dir', str(output_dir),
            '--interactive' if interactive else '--no-interactive'
        ])
        
        if mapping_result.exit_code != 0:
            click.echo("❌ Mapping step failed!", err=True)
            sys.exit(1)
        
        # Step 2: Analysis
        click.echo("\n🔬 Step 2: Data Analysis")
        
        analysis_result = runner.invoke(analyze, [
            '--data-dir', str(output_dir / "mapped_data"),
            '--output-dir', str(output_dir / "analysis"),
            '--buildings-metadata', str(output_dir / "buildings_metadata.json"),
            '--export-formats', 'json',
            '--export-formats', 'csv',
            '--generate-plots' if generate_plots else '--no-plots'
        ])
        
        if analysis_result.exit_code != 0:
            click.echo("❌ Analysis step failed!", err=True)
            sys.exit(1)
        
        click.echo("\n🎉 Complete pipeline executed successfully!")
        click.echo(f"📁 All results available in: {output_dir}")
        
    except Exception as e:
        click.echo(f"❌ Pipeline error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
