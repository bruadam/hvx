"""
Enhanced Command Line Interface for IEQ Analytics Engine.
Complete pipeline automation with improved structure and workflow management.
"""

import click
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import sys
import logging
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel

from .mapping import DataMapper
from .analytics import IEQAnalytics
from .models import MappingConfig
from .rule_builder import AnalyticsEngine
from .ventilation_rate_predictor import VentilationRatePredictor

# Rich console for better output formatting
console = Console()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PipelineState:
    """Manages pipeline state and workflow coordination."""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.state_file = workspace_dir / ".ieq_pipeline_state.json"
        self.config_dir = workspace_dir / "config"
        self.data_dir = workspace_dir / "data"
        self.output_dir = workspace_dir / "output"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load pipeline state from file."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "initialized": False,
            "mapped": False,
            "analyzed": False,
            "last_run": None,
            "data_files_count": 0,
            "buildings_count": 0,
            "rooms_count": 0
        }
    
    def save_state(self):
        """Save current pipeline state."""
        self.state["last_run"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def update_mapping_state(self, files_count: int, buildings_count: int, rooms_count: int):
        """Update state after mapping completion."""
        self.state.update({
            "mapped": True,
            "data_files_count": files_count,
            "buildings_count": buildings_count,
            "rooms_count": rooms_count
        })
        self.save_state()
    
    def update_analysis_state(self):
        """Update state after analysis completion."""
        self.state["analyzed"] = True
        self.save_state()


@click.group()
@click.version_option(version="1.0.0")
@click.option('--workspace', type=click.Path(path_type=Path), default=Path.cwd(), 
              help='Workspace directory for IEQ analytics project')
@click.pass_context
def cli(ctx, workspace: Path):
    """🔬 IEQ Analytics Engine - Comprehensive Indoor Environmental Quality Analysis Tool
    
    A complete pipeline for processing, analyzing, and reporting on indoor environmental quality data
    from IoT sensors across multiple buildings and rooms.
    """
    ctx.ensure_object(dict)
    ctx.obj['workspace'] = workspace
    ctx.obj['pipeline_state'] = PipelineState(workspace)


@cli.group()
@click.pass_context
def project(ctx):
    """📁 Project management commands for IEQ analytics workspace."""
    pass


@project.command()
@click.option('--name', type=str, required=True, help='Project name')
@click.option('--description', type=str, help='Project description')
@click.option('--template', type=click.Choice(['basic', 'advanced', 'research']), 
              default='basic', help='Project template')
@click.pass_context
def init(ctx, name: str, description: Optional[str], template: str):
    """🚀 Initialize a new IEQ analytics project workspace."""
    workspace = ctx.obj['workspace']
    
    console.print(f"[bold green]🚀 Initializing IEQ Analytics Project: {name}[/bold green]")
    
    # Create directory structure
    directories = [
        "config",
        "data/raw",
        "data/mapped", 
        "data/climate",
        "output/analysis",
        "output/reports",
        "output/visualizations",
        "scripts",
        "docs"
    ]
    
    for dir_path in directories:
        (workspace / dir_path).mkdir(parents=True, exist_ok=True)
        console.print(f"📁 Created: {dir_path}")
    
    # Create configuration files based on template
    if template == 'basic':
        _create_basic_config(workspace, name, description or f"IEQ Analytics project: {name}")
    elif template == 'advanced':
        _create_advanced_config(workspace, name, description or f"IEQ Analytics project: {name}")
    elif template == 'research':
        _create_research_config(workspace, name, description or f"IEQ Analytics project: {name}")
    
    # Initialize pipeline state
    pipeline_state = ctx.obj['pipeline_state']
    pipeline_state.state["initialized"] = True
    pipeline_state.save_state()
    
    console.print(f"[bold green]✅ Project '{name}' initialized successfully![/bold green]")
    console.print(f"📍 Workspace: {workspace}")
    
    # Display next steps
    next_steps = Panel(
        """
[bold]Next Steps:[/bold]

1. 📥 Place your raw CSV files in: data/raw/
2. 🔧 Configure mappings: ieq-analytics project config
3. 🗂️ Map your data: ieq-analytics mapping
4. 🔬 Run analysis: ieq-analytics analyze
5. 📊 Generate reports: ieq-analytics report generate

[italic]Use 'ieq-analytics --help' to see all available commands.[/italic]
        """,
        title="🎯 Getting Started",
        border_style="green"
    )
    console.print(next_steps)


@project.command()
@click.pass_context
def status(ctx):
    """📊 Show current project status and pipeline state."""
    workspace = ctx.obj['workspace']
    pipeline_state = ctx.obj['pipeline_state']
    
    # Create status table
    table = Table(title="🔬 IEQ Analytics Project Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta") 
    table.add_column("Details", style="white")
    
    # Check workspace structure
    workspace_ok = all((workspace / d).exists() for d in ["config", "data", "output"])
    table.add_row(
        "Workspace",
        "✅ Ready" if workspace_ok else "❌ Not initialized",
        str(workspace)
    )
    
    # Check data files
    raw_files = list((workspace / "data/raw").glob("*.csv")) if (workspace / "data/raw").exists() else []
    mapped_files = list((workspace / "data/mapped").glob("*.csv")) if (workspace / "data/mapped").exists() else []
    
    table.add_row(
        "Raw Data Files",
        f"📄 {len(raw_files)} files" if raw_files else "❌ No files found",
        f"Location: data/raw/"
    )
    
    table.add_row(
        "Mapped Data",
        f"✅ {len(mapped_files)} files" if mapped_files else "❌ Not mapped",
        f"Location: data/mapped/"
    )
    
    # Check configuration
    config_files = {
        "Mapping Config": workspace / "config/mapping_config.json",
        "Analytics Rules": workspace / "config/analytics_rules.yaml",
        "EN Standards": workspace / "config/en16798_thresholds.yaml"
    }
    
    for config_name, config_path in config_files.items():
        table.add_row(
            config_name,
            "✅ Configured" if config_path.exists() else "❌ Missing",
            str(config_path.relative_to(workspace))
        )
    
    # Pipeline state
    state = pipeline_state.state
    table.add_row(
        "Pipeline State",
        f"Mapped: {'✅' if state['mapped'] else '❌'} | Analyzed: {'✅' if state['analyzed'] else '❌'}",
        f"Last run: {state.get('last_run', 'Never')}"
    )
    
    # Analysis results
    analysis_files = list((workspace / "output/analysis").glob("*")) if (workspace / "output/analysis").exists() else []
    table.add_row(
        "Analysis Results",
        f"📊 {len(analysis_files)} files" if analysis_files else "❌ No results",
        f"Location: output/analysis/"
    )
    
    console.print(table)
    
    # Show recommendations
    recommendations = []
    if not raw_files:
        recommendations.append("📥 Add CSV files to data/raw/ directory")
    if not mapped_files and raw_files:
        recommendations.append("🗂️ Run data mapping: ieq-analytics mapping")
    if mapped_files and not state['analyzed']:
        recommendations.append("🔬 Run analysis: ieq-analytics analyze")
    
    if recommendations:
        rec_panel = Panel(
            "\n".join(f"• {rec}" for rec in recommendations),
            title="💡 Recommendations",
            border_style="yellow"
        )
        console.print(rec_panel)


@project.command()
@click.option('--config-type', type=click.Choice(['mapping', 'analytics', 'all']), 
              default='all', help='Configuration type to manage')
@click.pass_context
def config(ctx, config_type: str):
    """⚙️ Manage project configuration files."""
    workspace = ctx.obj['workspace']
    config_dir = workspace / "config"
    
    if config_type in ['mapping', 'all']:
        _configure_mapping(config_dir)
    
    if config_type in ['analytics', 'all']:
        _configure_analytics(config_dir)
    
    console.print("[bold green]✅ Configuration updated successfully![/bold green]")


@cli.command()
@click.option(
    '--data-dir-path', 
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Path to directory containing CSV files'
)
@click.option(
    '--config-path',
    type=click.Path(path_type=Path),
    help='Path to mapping configuration file'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
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
@click.option(
    '--batch-size', type=int, default=10, 
    help='Number of files to process in each batch'
)
@click.pass_context
def mapping(
    ctx,
    data_dir_path: Optional[Path],
    config_path: Optional[Path],
    output_dir: Optional[Path],
    interactive: bool,
    room_tag: Optional[str],
    batch_size: int
):
    """🗂️ Map raw CSV sensor data to standardized IEQ format."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    pipeline_state = ctx.obj.get('pipeline_state')
    
    # Set defaults based on workspace structure
    data_dir_path = data_dir_path or workspace / "data/raw"
    config_path = config_path or workspace / "config/mapping_config.json"
    output_dir = output_dir or workspace / "output"
    
    console.print("[bold blue]�️ Starting Data Mapping Process...[/bold blue]")
    console.print(f"📂 Data directory: {data_dir_path}")
    console.print(f"⚙️  Configuration: {config_path}")
    console.print(f"📤 Output directory: {output_dir}")
    
    try:
        # Initialize mapper
        mapper = DataMapper()
        
        # Load existing configuration if available
        if config_path.exists():
            console.print(f"📋 Loading existing configuration from {config_path}")
            mapper.load_config(config_path)
        else:
            console.print("📋 No existing configuration found. Starting fresh.")
        
        # Create output directory
        mapped_data_dir = output_dir / "mapped_data"
        mapped_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Get list of files to process
        csv_files = list(data_dir_path.glob("*.csv"))
        if not csv_files:
            console.print("[red]❌ No CSV files found in source directory![/red]")
            return
        
        console.print(f"📄 Found {len(csv_files)} CSV files to process")
        
        # Process files in batches with progress tracking
        processed_data = []
        total_files = len(csv_files)
        
        for i in track(range(0, total_files, batch_size), description="Processing batches..."):
            batch_files = csv_files[i:i+batch_size]
            
            for file_path in batch_files:
                try:
                    console.print(f"📊 Processing: {file_path.name}")
                    
                    # Load and analyze file
                    import pandas as pd
                    df = pd.read_csv(file_path)
                    
                    # Try to find existing mapping from loaded config first
                    existing_mapping = mapper.config.get_mapping_for_file(file_path.name)
                    
                    if existing_mapping:
                        # Use the existing mapping from config
                        mapping = existing_mapping.column_mappings
                        console.print(f"✅ Using existing mapping for: {file_path.name}")
                    elif interactive:
                        # Interactive mapping for this file if no existing mapping found
                        mapping = mapper.interactive_column_mapping(file_path.name, df.columns.tolist())
                    else:
                        # Auto-suggest mapping if no config and non-interactive
                        mapping = mapper.suggest_column_mappings(df.columns.tolist())
                        console.print(f"🤖 Auto-suggested mapping for: {file_path.name}")
                    
                    # Map the file
                    ieq_data = mapper.map_file(file_path, mapping)
                    if ieq_data:
                        # Save mapped file
                        output_file = mapped_data_dir / f"{ieq_data.room_id}_processed.csv"
                        ieq_data.data.to_csv(output_file)
                        processed_data.append(ieq_data)
                        
                        console.print(f"✅ Mapped: {file_path.name} → {output_file.name}")
                    
                except Exception as e:
                    console.print(f"[red]❌ Error processing {file_path.name}: {e}[/red]")
                    continue
        
        # Apply room tags if specified
        if room_tag:
            console.print(f"🏷️  Applying room tag: {room_tag}")
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
        
        # Update pipeline state if available
        if pipeline_state:
            pipeline_state.update_mapping_state(
                len(processed_data),
                len(mapper.buildings),
                sum(len(b.rooms) for b in mapper.buildings.values())
            )
        
        # Success summary with rich formatting
        success_panel = Panel(
            f"""
[bold green]✅ Mapping completed successfully![/bold green]

📊 Processed: {len(processed_data)}/{len(csv_files)} files
🏢 Buildings: {len(mapper.buildings)}
🏠 Total rooms: {sum(len(b.rooms) for b in mapper.buildings.values())}
📁 Output: {mapped_data_dir}
💾 Metadata: {metadata_path}

[italic]Next step: Run analysis with 'ieq-analytics analyze'[/italic]
            """,
            title="🎉 Mapping Results",
            border_style="green"
        )
        console.print(success_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Error during mapping: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    '--data-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Directory containing mapped IEQ data files'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
    help='Output directory for analysis results'
)
@click.option(
    '--buildings-metadata',
    type=click.Path(path_type=Path),
    help='Path to buildings metadata JSON file'
)
@click.option(
    '--rules-config', 
    type=click.Path(path_type=Path),
    help='Analytics rules configuration'
)
@click.option(
    '--export-formats',
    multiple=True,
    type=click.Choice(['json', 'csv', 'excel', 'pdf']),
    default=['json', 'csv'],
    help='Export formats for analysis results'
)
@click.option(
    '--generate-plots/--no-plots',
    default=True,
    help='Generate visualization plots'
)
@click.option(
    '--parallel/--sequential', default=True,
    help='Parallel processing of rooms'
)
@click.pass_context
def analyze(
    ctx,
    data_dir: Optional[Path],
    output_dir: Optional[Path],
    buildings_metadata: Optional[Path],
    rules_config: Optional[Path],
    export_formats: List[str],
    generate_plots: bool,
    parallel: bool
):
    """🔬 Perform comprehensive IEQ analysis on mapped data."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    pipeline_state = ctx.obj.get('pipeline_state')
    
    # Set defaults based on workspace structure
    data_dir = data_dir or workspace / "output/mapped_data"
    output_dir = output_dir or workspace / "output/analysis"
    buildings_metadata = buildings_metadata or workspace / "output/buildings_metadata.json"
    rules_config = rules_config or workspace / "config/analytics_rules.yaml"
    
    console.print("[bold blue]🔬 Starting Comprehensive IEQ Analysis...[/bold blue]")
    console.print(f"📂 Data directory: {data_dir}")
    console.print(f"📤 Output directory: {output_dir}")
    
    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        if generate_plots:
            (output_dir / "plots").mkdir(exist_ok=True)
        
        # Initialize analytics engine
        analytics = IEQAnalytics(rules_config if rules_config.exists() else None)
        
        # Load buildings metadata
        buildings_data = []
        if buildings_metadata.exists():
            with open(buildings_metadata, 'r') as f:
                buildings_data = json.load(f)
            console.print(f"📋 Loaded metadata for {len(buildings_data)} buildings")
        else:
            console.print("⚠️  No buildings metadata found. Proceeding without building context.")
        
        # Find all mapped data files
        data_files = list(data_dir.glob("*_processed.csv"))
        if not data_files:
            console.print("[red]❌ No mapped data files found! Run mapping first.[/red]")
            return
        
        console.print(f"📊 Found {len(data_files)} data files to analyze")
        
        # Analyze each room with progress tracking
        room_analyses = []
        building_groups = {}
        
        for data_file in track(data_files, description="Analyzing rooms..."):
            console.print(f"🔍 Analyzing: {data_file.name}")
            
            try:
                # Load the mapped data
                import pandas as pd
                df = pd.read_csv(data_file, index_col=0, parse_dates=True)
                
                # Extract room and building IDs from filename
                room_id = data_file.stem.replace('_processed', '')
                building_id = _get_building_id_from_metadata(room_id, buildings_data)
                
                # Create IEQData object
                from .models import IEQData
                ieq_data = IEQData(
                    room_id=room_id,
                    building_id=building_id,
                    data=df,
                    source_files=[str(data_file)],
                    data_period_start=df.index.min() if not df.empty else None,
                    data_period_end=df.index.max() if not df.empty else None,
                    quality_score=None
                )
                
                # Perform comprehensive analysis
                analysis_result = analytics.analyze_room_data(ieq_data)
                room_analyses.append(analysis_result)
                
                # Group by building for aggregation
                if building_id not in building_groups:
                    building_groups[building_id] = []
                building_groups[building_id].append(analysis_result)
                
                # Generate plots if requested
                if generate_plots:
                    plots_dir = output_dir / "plots" / room_id
                    try:
                        generated_plots = analytics.generate_visualizations(ieq_data, plots_dir)
                        analysis_result["generated_plots"] = generated_plots
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Visualization error for {room_id}: {e}[/yellow]")
                
                console.print(f"✅ Completed analysis for {room_id}")
                
            except Exception as e:
                console.print(f"[red]❌ Error analyzing {data_file.name}: {e}[/red]")
                continue
        
        # Perform building-level analysis
        building_analyses = {}
        for building_id, room_results in building_groups.items():
            console.print(f"🏢 Aggregating analysis for building: {building_id}")
            building_analysis = analytics.aggregate_building_analysis(room_results)
            building_analyses[building_id] = building_analysis
        
        # Export results
        console.print("💾 Exporting analysis results...")
        exported_files = analytics.export_analysis_results(
            room_analyses=room_analyses,
            building_analysis=building_analyses,
            output_dir=output_dir,
            formats=list(export_formats)
        )
        
        # Update pipeline state if available
        if pipeline_state:
            pipeline_state.update_analysis_state()
        
        # Generate comprehensive summary
        _generate_analysis_summary(room_analyses, building_analyses, output_dir)
        
        # Display key insights
        total_quality_score = sum(
            analysis.get("data_quality", {}).get("overall_score", 0) 
            for analysis in room_analyses
        ) / len(room_analyses) if room_analyses else 0
        
        # Count rooms with issues
        quality_issues = sum(
            1 for analysis in room_analyses 
            if analysis.get("data_quality", {}).get("overall_score", 0) < 0.8
        )
        
        comfort_issues = _count_comfort_issues(room_analyses)
        
        # Success summary with rich formatting
        success_panel = Panel(
            f"""
[bold green]✅ Analysis completed successfully![/bold green]

📊 Analyzed rooms: {len(room_analyses)}
🏢 Buildings: {len(building_analyses)}
📁 Results: {output_dir}
📊 Export formats: {', '.join(export_formats)}
🎨 Visualizations: {'✅ Generated' if generate_plots else '❌ Skipped'}

[bold]📈 Key Insights:[/bold]
   Average Data Quality: {total_quality_score:.3f}
   Rooms with Quality Issues: {quality_issues}/{len(room_analyses)}
   Rooms with Comfort Issues: {comfort_issues}/{len(room_analyses)}

[italic]Next step: Generate reports with 'ieq-analytics report generate'[/italic]
            """,
            title="🎉 Analysis Results",
            border_style="green"
        )
        console.print(success_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Error during analysis: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    '--data-dir-path',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Path to directory containing CSV files to analyze'
)
@click.option(
    '--output-format',
    type=click.Choice(['table', 'json', 'yaml']),
    default='table',
    help='Output format for the analysis results'
)
@click.option(
    '--export', 
    type=click.Path(path_type=Path),
    help='Export inspection results to file'
)
@click.pass_context
def inspect(ctx, data_dir_path: Optional[Path], output_format: str, export: Optional[Path]):
    """🔍 Inspect CSV files and analyze their structure."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    data_dir_path = data_dir_path or workspace / "data/raw"
    
    console.print(f"[bold blue]🔍 Inspecting data files in: {data_dir_path}[/bold blue]")
    
    try:
        # Initialize mapper for analysis
        mapper = DataMapper()
        
        # Analyze files
        analysis = mapper.analyze_files(data_dir_path)
        
        if output_format == 'json':
            result = json.dumps(analysis, indent=2, default=str)
            console.print(result)
        elif output_format == 'yaml':
            result = yaml.dump(analysis, default_flow_style=False)
            console.print(result)
        else:
            _display_inspection_table(analysis)
        
        if export:
            export.parent.mkdir(parents=True, exist_ok=True)
            if export.suffix == '.json':
                with open(export, 'w') as f:
                    json.dump(analysis, f, indent=2, default=str)
            elif export.suffix in ['.yaml', '.yml']:
                with open(export, 'w') as f:
                    yaml.dump(analysis, f, default_flow_style=False)
            console.print(f"📁 Inspection results exported to: {export}")
    
    except Exception as e:
        console.print(f"[red]❌ Inspection failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    '--config-path',
    type=click.Path(path_type=Path),
    help='Path to save the configuration template'
)
@click.pass_context
def init_config(ctx, config_path: Optional[Path]):
    """🛠️ Initialize a mapping configuration template."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    config_path = config_path or workspace / "config/mapping_config.json"
    
    console.print("🛠️  Creating mapping configuration template...")
    
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
        
        console.print(f"[bold green]✅ Configuration template created at: {config_path}[/bold green]")
        console.print("📝 Edit this file to customize column mappings for your data")
        
    except Exception as e:
        console.print(f"[red]❌ Error creating configuration: {e}[/red]")
        sys.exit(1)


@cli.group()
@click.pass_context
def report(ctx):
    """� Report generation and analysis summary commands."""
    pass


@report.command()
@click.option('--analysis-dir', type=click.Path(exists=True, path_type=Path),
              help='Analysis results directory (default: output/analysis)')
@click.option('--output-dir', type=click.Path(path_type=Path),
              help='Report output directory (default: output/reports)')
@click.option('--format', 'report_format', type=click.Choice(['html', 'pdf', 'markdown']),
              default='pdf', help='Report format')
@click.option('--template', type=click.Choice(['executive', 'technical', 'research']),
              default='executive', help='Report template')
@click.option('--include-plots/--no-plots', default=True,
              help='Include visualization plots in report')
@click.option('--ai-analysis/--no-ai-analysis', default=False,
              help='Include AI-powered chart analysis (requires MISTRAL_API_KEY)')
@click.option('--interactive-review/--no-interactive-review', default=False,
              help='Enable interactive review of AI analysis')
@click.pass_context
def generate(ctx, analysis_dir: Optional[Path], output_dir: Optional[Path],
             report_format: str, template: str, include_plots: bool,
             ai_analysis: bool, interactive_review: bool):
    """📊 Generate comprehensive analysis reports."""
    workspace = ctx.obj.get('workspace', Path.cwd())
    analysis_dir = analysis_dir or workspace / "output/analysis"
    output_dir = output_dir or workspace / "output/reports"
    
    console.print("[bold blue]📊 Generating Analysis Report...[/bold blue]")
    console.print(f"📂 Analysis directory: {analysis_dir}")
    console.print(f"📤 Output directory: {output_dir}")
    console.print(f"📋 Template: {template}")
    console.print(f"📄 Format: {report_format}")
    
    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Import required reporting modules
        from .reporting.report_engine import ReportEngine
        from .reporting.pdf_generator import PDFGenerator
        from .reporting.graph_engine import GraphEngine
        
        # Initialize report engine
        console.print("🔧 Initializing report engine...")
        report_engine = ReportEngine()
        
        # Check for analysis results
        if not analysis_dir.exists():
            console.print(f"[red]❌ Analysis directory not found: {analysis_dir}[/red]")
            console.print("Run 'ieq-analytics analyze' first to generate analysis data.")
            return
        
        # Load analysis results
        console.print("📊 Loading analysis results...")
        
        # Look for analysis result files
        json_files = list(analysis_dir.glob("*.json"))
        if not json_files:
            console.print(f"[red]❌ No analysis results found in {analysis_dir}[/red]")
            console.print("Make sure analysis has been completed successfully.")
            return
        
        # Load room and building analyses
        room_analyses = []
        building_analysis = {}
        buildings_metadata = None
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                if json_file.name == "room_analyses.json":
                    room_analyses = data
                elif json_file.name == "building_analysis.json":
                    building_analysis = data
                elif json_file.name == "comprehensive_summary.json":
                    summary_data = data
                
            except Exception as e:
                console.print(f"[yellow]⚠️ Error loading {json_file.name}: {e}[/yellow]")
        
        # Load buildings metadata if available
        metadata_path = workspace / "output/buildings_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                buildings_metadata = json.load(f)
        
        console.print(f"✅ Loaded analysis for {len(room_analyses)} rooms and {len(building_analysis)} buildings")
        
        # Generate charts with optional AI analysis
        chart_paths = []
        ai_commentaries = {}
        
        if include_plots:
            console.print("� Generating visualization charts...")
            
            # Initialize graph engine
            graph_engine = GraphEngine()
            
            # Enable AI analysis if requested
            if ai_analysis:
                console.print("🤖 AI analysis enabled - checking setup...")
                
                # Validate AI setup
                from .reporting.ai_graph_analyzer import validate_ai_setup, AIGraphAnalyzer, InteractiveReviewSystem
                is_valid, message = validate_ai_setup()
                
                if is_valid:
                    console.print("✅ AI analysis ready")
                    ai_analyzer = AIGraphAnalyzer()
                    
                    if interactive_review:
                        review_system = InteractiveReviewSystem()
                    
                else:
                    console.print(f"[yellow]⚠️ AI analysis unavailable: {message}[/yellow]")
                    ai_analysis = False
            
            # Process each room's data for chart generation
            plots_dir = analysis_dir / "plots"
            if plots_dir.exists():
                console.print(f"📁 Found existing plots directory: {plots_dir}")
                
                # Collect chart paths and generate AI analysis if requested
                for room_dir in plots_dir.iterdir():
                    if room_dir.is_dir():
                        room_charts = list(room_dir.glob("*.png"))
                        chart_paths.extend(room_charts)
                        
                        # Generate AI analysis for charts
                        if ai_analysis and room_charts:
                            console.print(f"🤖 Analyzing charts for room: {room_dir.name}")
                            
                            room_commentaries = {}
                            for chart_path in room_charts:
                                try:
                                    # Create context for the chart
                                    chart_context = {
                                        'room_id': room_dir.name,
                                        'building_id': _get_building_id_from_room(room_dir.name, buildings_metadata),
                                        'parameter': _extract_parameter_from_filename(chart_path.name),
                                        'description': f"Time series analysis for {room_dir.name}"
                                    }
                                    
                                    # Analyze chart
                                    analysis = ai_analyzer.analyze_chart(chart_path, chart_context)
                                    
                                    # Interactive review if enabled
                                    if interactive_review and analysis.confidence_score > 0:
                                        analysis = review_system.review_analysis(analysis, chart_path)
                                    
                                    room_commentaries[chart_path.stem] = analysis
                                    
                                except Exception as e:
                                    console.print(f"[yellow]⚠️ AI analysis failed for {chart_path.name}: {e}[/yellow]")
                            
                            if room_commentaries:
                                ai_commentaries[room_dir.name] = room_commentaries
                
                console.print(f"📊 Found {len(chart_paths)} charts across {len(list(plots_dir.iterdir()))} rooms")
                
                if ai_analysis and ai_commentaries:
                    total_analyses = sum(len(commentaries) for commentaries in ai_commentaries.values())
                    console.print(f"🤖 Generated {total_analyses} AI chart analyses")
                    
                    if interactive_review:
                        review_summary = review_system.get_review_summary()
                        console.print(f"👁️ Review summary: {review_summary}")
            else:
                console.print("[yellow]⚠️ No plots directory found. Generate visualizations first.[/yellow]")
        
        # Generate report based on format
        console.print(f"📝 Generating {report_format.upper()} report...")
        
        output_file = None  # Initialize variable
        
        if report_format == 'pdf':
            # Generate PDF report
            pdf_generator = PDFGenerator()
            
            # Prepare report data
            report_data = {
                'room_analyses': room_analyses,
                'building_analysis': building_analysis,
                'buildings_metadata': buildings_metadata,
                'chart_paths': chart_paths,
                'ai_commentaries': ai_commentaries,
                'template': template,
                'generation_timestamp': datetime.now().isoformat(),
                'workspace': str(workspace)
            }
            
            # Generate PDF
            output_file = output_dir / f"ieq_analysis_report_{template}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            try:
                if template == 'executive':
                    pdf_path = pdf_generator.create_executive_summary_report(
                        analysis_data=report_data,
                        output_path=output_file
                    )
                else:
                    pdf_path = pdf_generator.create_technical_report(
                        analysis_data=report_data,
                        output_path=output_file
                    )
                
                console.print(f"✅ PDF report generated: {pdf_path}")
                
            except Exception as e:
                console.print(f"[red]❌ PDF generation failed: {e}[/red]")
                console.print("Falling back to HTML generation...")
                report_format = 'html'
        
        if report_format == 'html':
            # Generate HTML report using simple template
            output_file = output_dir / f"ieq_analysis_report_{template}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>IEQ Analysis Report - {template.title()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .metric {{ margin: 10px 0; }}
        .ai-analysis {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>IEQ Analysis Report - {template.title()}</h1>
    <div class="summary">
        <h2>Summary</h2>
        <div class="metric">Total Rooms Analyzed: {len(room_analyses)}</div>
        <div class="metric">Buildings: {len(building_analysis)}</div>
        <div class="metric">Charts Generated: {len(chart_paths) if include_plots else 0}</div>
        <div class="metric">AI Analyses: {sum(len(c) for c in ai_commentaries.values()) if ai_analysis else 0}</div>
    </div>
    
    <h2>Room Analysis Results</h2>
    <p>Analysis completed for {len(room_analyses)} rooms across {len(building_analysis)} buildings.</p>
    
    {'<h2>AI Chart Analysis</h2>' if ai_commentaries else ''}
    {''.join(f'<div class="ai-analysis"><h3>{room}</h3><p>Charts analyzed: {len(charts)}</p></div>' 
             for room, charts in ai_commentaries.items()) if ai_commentaries else ''}
</body>
</html>"""
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            console.print(f"✅ HTML report generated: {output_file}")
        
        elif report_format == 'markdown':
            # Generate Markdown report
            output_file = output_dir / f"ieq_analysis_report_{template}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            markdown_content = f"""# IEQ Analysis Report - {template.title()}

## Summary

- **Total Rooms Analyzed**: {len(room_analyses)}
- **Buildings**: {len(building_analysis)}
- **Charts Generated**: {len(chart_paths) if include_plots else 0}
- **AI Analyses**: {sum(len(c) for c in ai_commentaries.values()) if ai_analysis else 0}

## Room Analysis Results

Analysis completed for {len(room_analyses)} rooms across {len(building_analysis)} buildings.

{"## AI Chart Analysis" if ai_commentaries else ""}

{chr(10).join(f"### {room}{chr(10)}Charts analyzed: {len(charts)}{chr(10)}" 
              for room, charts in ai_commentaries.items()) if ai_commentaries else ""}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            console.print(f"✅ Markdown report generated: {output_file}")
        
        # Generate summary metrics
        if room_analyses and output_file:
            total_rooms = len(room_analyses)
            quality_issues = sum(
                1 for analysis in room_analyses 
                if analysis.get("data_quality", {}).get("overall_score", 1.0) < 0.8
            )
            comfort_issues = _count_comfort_issues(room_analyses)
            
            # Success summary
            success_panel = Panel(
                f"""
[bold green]✅ Report generation completed successfully![/bold green]

📊 Report Details:
   Format: {report_format.upper()}
   Template: {template}
   Output: {output_file}

📈 Analysis Summary:
   Rooms analyzed: {total_rooms}
   Buildings: {len(building_analysis)}
   Charts included: {len(chart_paths) if include_plots else 0}
   AI analyses: {sum(len(c) for c in ai_commentaries.values()) if ai_analysis else 0}

🎯 Key Findings:
   Rooms with quality issues: {quality_issues}/{total_rooms}
   Rooms with comfort issues: {comfort_issues}/{total_rooms}

[italic]Report is ready for review and distribution![/italic]
                """,
                title="🎉 Report Generated",
                border_style="green"
            )
            console.print(success_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Report generation failed: {e}[/red]")
        import traceback
        console.print(f"[red]Error details: {traceback.format_exc()}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    '--source-dir', 
    type=click.Path(exists=True, path_type=Path),
    help='Source directory with raw data (default: data/raw)'
)
@click.option(
    '--output-dir', 
    type=click.Path(path_type=Path),
    help='Output directory (default: output)'
)
@click.option(
    '--skip-interactive', 
    is_flag=True,
    help='Skip interactive steps (auto mode)'
)
@click.option(
    '--parallel-analysis', 
    is_flag=True,
    help='Enable parallel analysis processing'
)
@click.pass_context
def pipeline(ctx, source_dir: Optional[Path], output_dir: Optional[Path],
             skip_interactive: bool, parallel_analysis: bool):
    """🚀 Run the complete IEQ analysis pipeline (map → analyze → report)."""
    workspace = ctx.obj.get('workspace', Path.cwd())
    source_dir = source_dir or workspace / "data/raw"
    output_dir = output_dir or workspace / "output"
    
    console.print("[bold green]🚀 Starting Complete IEQ Analysis Pipeline...[/bold green]")
    
    pipeline_panel = Panel(
        """
[bold]Pipeline Steps:[/bold]

1. 🗂️ Data Mapping (Raw CSV → Standardized Format)
2. 🔬 Comprehensive Analysis (Room + Building Level)
3. 📊 Visualization Generation
4. 📋 Report Generation
5. 💾 Export Results

[italic]This may take several minutes depending on data size...[/italic]
        """,
        title="🔄 Pipeline Overview",
        border_style="blue"
    )
    console.print(pipeline_panel)
    
    try:
        # Step 1: Data Mapping
        console.print("\n[bold]Step 1: Data Mapping[/bold]")
        from click.testing import CliRunner
        runner = CliRunner()
        
        mapping_args = [
            '--data-dir-path', str(source_dir),
            '--output-dir', str(output_dir)
        ]
        if skip_interactive:
            mapping_args.append('--no-interactive')
        
        mapping_result = runner.invoke(mapping, mapping_args, obj=ctx.obj)
        if mapping_result.exit_code != 0:
            console.print("[red]❌ Data mapping failed![/red]")
            return
        
        # Step 2: Analysis
        console.print("\n[bold]Step 2: Comprehensive Analysis[/bold]")
        analysis_args = [
            '--data-dir', str(output_dir / "mapped_data"),
            '--output-dir', str(output_dir / "analysis"),
            '--generate-plots'
        ]
        if parallel_analysis:
            analysis_args.append('--parallel')
        
        analysis_result = runner.invoke(analyze, analysis_args, obj=ctx.obj)
        if analysis_result.exit_code != 0:
            console.print("[red]❌ Analysis failed![/red]")
            return
        
        # Step 3: Report Generation
        console.print("\n[bold]Step 3: Report Generation[/bold]")
        report_result = runner.invoke(generate, [
            '--analysis-dir', str(output_dir / "analysis"),
            '--output-dir', str(output_dir / "reports"),
            '--include-plots'
        ], obj=ctx.obj)
        
        # Pipeline completion
        completion_panel = Panel(
            f"""
[bold green]🎉 Pipeline completed successfully![/bold green]

📁 Workspace: {workspace}
📊 Analysis Results: output/analysis/
📋 Reports: output/reports/
🎨 Visualizations: output/analysis/plots/

[italic]All IEQ analysis results are ready for review![/italic]
            """,
            title="✅ Pipeline Complete",
            border_style="green"
        )
        console.print(completion_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Pipeline failed: {e}[/red]")
        sys.exit(1)


# Helper functions
def _create_basic_config(workspace: Path, name: str, description: str):
    """Create basic project configuration files."""
    # Project metadata
    project_config = {
        "name": name,
        "description": description or f"IEQ Analytics project: {name}",
        "created": datetime.now().isoformat(),
        "version": "1.0.0",
        "template": "basic"
    }
    
    with open(workspace / "config/project.json", 'w') as f:
        json.dump(project_config, f, indent=2)
    
    # Basic mapping configuration
    mapping_config = {
        "default_building_name": "Building_1",
        "timestamp_format": "%Y-%m-%d %H:%M:%S",
        "required_parameters": ["timestamp", "temperature", "humidity", "co2"],
        "optional_parameters": ["light", "presence"]
    }
    
    with open(workspace / "config/mapping_config.json", 'w') as f:
        json.dump(mapping_config, f, indent=2)


def _create_advanced_config(workspace: Path, name: str, description: str):
    """Create advanced project configuration with custom rules."""
    _create_basic_config(workspace, name, description)
    
    # Advanced analytics rules
    analytics_rules = {
        "analytics": {
            "temp_comfort_office": {
                "description": "Office temperature comfort (20-26°C)",
                "feature": "temperature",
                "thresholds": {"min": 20.0, "max": 26.0},
                "periods": ["all_year"],
                "filters": ["opening_hours"]
            },
            "humidity_control": {
                "description": "Humidity control (30-70%)",
                "feature": "humidity", 
                "thresholds": {"min": 30.0, "max": 70.0},
                "periods": ["all_year"],
                "filters": ["all_hours"]
            },
            "co2_ventilation": {
                "description": "CO2 ventilation effectiveness (<1000 ppm)",
                "feature": "co2",
                "thresholds": {"max": 1000.0},
                "periods": ["all_year"],
                "filters": ["opening_hours"]
            }
        }
    }
    
    with open(workspace / "config/analytics_rules.yaml", 'w') as f:
        yaml.dump(analytics_rules, f, default_flow_style=False)


def _create_research_config(workspace: Path, name: str, description: str):
    """Create research-grade configuration with detailed analysis."""
    _create_advanced_config(workspace, name, description)
    
    # Add EN 16798-1 thresholds
    en_thresholds = {
        "comfort_thresholds": {
            "temperature": {
                "I": {"min": 21.0, "max": 23.0},
                "II": {"min": 20.0, "max": 24.0},
                "III": {"min": 19.0, "max": 25.0}
            },
            "humidity": {
                "I": {"min": 30.0, "max": 50.0},
                "II": {"min": 25.0, "max": 60.0},
                "III": {"min": 20.0, "max": 70.0}
            },
            "co2": {
                "I": {"max": 550.0},
                "II": {"max": 800.0},
                "III": {"max": 1200.0}
            }
        }
    }
    
    with open(workspace / "config/en16798_thresholds.yaml", 'w') as f:
        yaml.dump(en_thresholds, f, default_flow_style=False)


def _configure_mapping(config_dir: Path):
    """Interactive configuration of data mapping settings."""
    console.print("⚙️ Configuring data mapping settings...")
    # Implementation for interactive configuration


def _configure_analytics(config_dir: Path):
    """Interactive configuration of analytics rules."""
    console.print("⚙️ Configuring analytics rules...")
    # Implementation for interactive rule configuration


def _get_building_id_from_metadata(room_id: str, buildings_data: List[Dict]) -> str:
    """Extract building ID from room ID using metadata."""
    for building in buildings_data:
        for room in building.get("rooms", []):
            if room["id"] == room_id:
                return building["id"]
    
    # Fallback pattern matching
    if room_id.startswith("fl_ng_") or "Fløng" in room_id or "floeng" in room_id.lower():
        return "floeng-skole"
    elif room_id.startswith("ole_") or "Ole" in room_id:
        return "ole-roemer-skolen"
    elif room_id.startswith("reerslev_") or "reerslev" in room_id.lower():
        return "reerslev"
    else:
        return "unknown_building"


def _display_inspection_table(analysis: Dict[str, Any]):
    """Display inspection results in a formatted table."""
    table = Table(title="📊 Data Inspection Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Details", style="white")
    
    table.add_row("Total Files", str(len(analysis['files'])), "CSV files found")
    table.add_row("Unique Columns", str(len(analysis['unique_columns'])), "Distinct column names")
    table.add_row("Building Patterns", str(len(analysis['building_patterns'])), "Detected building types")
    table.add_row("Room Patterns", str(len(analysis['room_patterns'])), "Detected room identifiers")
    
    console.print(table)
    
    # Show column frequency
    console.print("\n[bold]Most Common Columns:[/bold]")
    sorted_columns = sorted(
        analysis['column_frequency'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for col, freq in sorted_columns[:10]:
        console.print(f"  • {col}: [green]{freq}[/green] files")


def _generate_analysis_summary(room_analyses: List[Dict], building_analyses: Dict, output_dir: Path):
    """Generate a comprehensive analysis summary."""
    summary = {
        "analysis_timestamp": datetime.now().isoformat(),
        "summary_statistics": {
            "total_rooms": len(room_analyses),
            "total_buildings": len(building_analyses),
            "average_data_quality": sum(
                analysis.get("data_quality", {}).get("overall_score", 0) 
                for analysis in room_analyses
            ) / len(room_analyses) if room_analyses else 0,
            "rooms_with_quality_issues": sum(
                1 for analysis in room_analyses 
                if analysis.get("data_quality", {}).get("overall_score", 0) < 0.8
            ),
            "rooms_with_comfort_issues": _count_comfort_issues(room_analyses)
        },
        "building_summaries": {
            building_id: {
                "room_count": analysis["room_count"],
                "average_quality": analysis["data_quality_summary"]["average_quality_score"],
                "recommendation_count": len(analysis["building_recommendations"])
            }
            for building_id, analysis in building_analyses.items()
        }
    }
    
    summary_path = output_dir / "comprehensive_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)


def _count_comfort_issues(room_analyses: List[Dict]) -> int:
    """Count rooms with comfort compliance issues."""
    issues = 0
    for analysis in room_analyses:
        for param, categories in analysis.get("comfort_analysis", {}).items():
            category_ii = categories.get("II", {})
            if category_ii.get("compliance_percentage", 100) < 80:
                issues += 1
                break
    return issues


def _get_building_id_from_room(room_id: str, buildings_metadata: Optional[List[Dict]]) -> str:
    """Extract building ID from room ID using metadata."""
    if buildings_metadata:
        for building in buildings_metadata:
            for room in building.get("rooms", []):
                if room.get("id") == room_id:
                    return building.get("id", "unknown_building")
    
    # Fallback pattern matching
    if room_id.startswith("fl_ng_") or "Fløng" in room_id or "floeng" in room_id.lower():
        return "floeng-skole"
    elif room_id.startswith("ole_") or "Ole" in room_id:
        return "ole-roemer-skolen"
    elif room_id.startswith("reerslev_") or "reerslev" in room_id.lower():
        return "reerslev"
    else:
        return "unknown_building"


def _extract_parameter_from_filename(filename: str) -> str:
    """Extract parameter type from chart filename."""
    filename_lower = filename.lower()
    if 'temperature' in filename_lower or 'temp' in filename_lower:
        return 'temperature'
    elif 'humidity' in filename_lower or 'rh' in filename_lower:
        return 'humidity'
    elif 'co2' in filename_lower or 'carbon' in filename_lower:
        return 'co2'
    elif 'light' in filename_lower or 'lux' in filename_lower:
        return 'light'
    elif 'pressure' in filename_lower:
        return 'pressure'
    else:
        return 'environmental_parameter'


if __name__ == "__main__":
    cli()
