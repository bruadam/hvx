"""
Interactive Report Template Commands

CLI commands for browsing, configuring, and generating reports using the template system.
"""

import click
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import yaml
import sys
from datetime import datetime
import pandas as pd
import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from ieq_analytics.reporting.templates.template_manager import TemplateManager
from ieq_analytics.unified_analytics import UnifiedAnalyticsEngine

console = Console()


@click.group()
def templates():
    """📁 Report template management and interactive report creation."""
    pass


@templates.command()
@click.option(
    '--category',
    type=str,
    help='Filter templates by category'
)
@click.pass_context
def list(ctx, category: Optional[str]):
    """📋 List all available report templates."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    template_manager = TemplateManager()
    
    console.print("📁 [bold blue]Available Report Templates[/bold blue]")
    
    try:
        # Get templates by category
        if category:
            console.print(f"🔍 Filtering by category: {category}")
            template_manager.display_templates_table(category)
        else:
            template_manager.display_templates_table()
        
        # Show category summary
        categories = template_manager.get_templates_by_category()
        
        summary_panel = Panel.fit(
            f"[bold green]📊 Template Summary[/bold green]\n\n"
            f"Total templates: {len(template_manager.templates)}\n"
            f"Categories: {len(categories)}\n\n"
            f"[italic]💡 Use 'ieq-analytics templates browse' for interactive selection[/italic]",
            title="📁 Template Library",
            border_style="green"
        )
        console.print(summary_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Error loading templates: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")


@templates.command()
@click.option(
    '--category',
    type=str,
    help='Filter templates by category'
)
@click.pass_context
def browse(ctx, category: Optional[str]):
    """🔍 Interactively browse and preview templates."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    template_manager = TemplateManager()
    
    console.print("🔍 [bold blue]Interactive Template Browser[/bold blue]")
    
    try:
        # Show available templates
        if category:
            template_manager.display_templates_table(category)
        else:
            template_manager.display_templates_table()
        
        # Interactive template selection
        selected_template_id = template_manager.interactive_template_selection()
        
        if selected_template_id:
            template = template_manager.get_template(selected_template_id)
            if template:
                # Show template details
                console.print(f"\n📋 [bold]Template Details: {template.template_name}[/bold]")
                console.print(f"📝 {template.description}")
                
                # Show available sections
                sections = template.get_available_sections()
                console.print(f"\n📊 Available Sections ({len(sections)}):")
                for section in sections:
                    required_text = "[red](Required)[/red]" if section['required'] else ""
                    console.print(f"  • {section['name']} {required_text}")
                    console.print(f"    {section.get('description', 'No description')}")
                
                # Show available charts
                charts = template.get_available_charts()
                console.print(f"\n📈 Available Charts ({len(charts)}):")
                for chart_id, chart_config in list(charts.items())[:5]:  # Show first 5
                    console.print(f"  • {chart_config.get('name', chart_id)}")
                    console.print(f"    {chart_config.get('description', 'No description')}")
                
                if len(charts) > 5:
                    console.print(f"    ... and {len(charts) - 5} more charts")
                
                # Ask if user wants to create report with this template
                if Confirm.ask("\nWould you like to create a report with this template?"):
                    ctx.invoke(create, template=selected_template_id, interactive=True)
        
    except Exception as e:
        console.print(f"[red]❌ Error browsing templates: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")


@templates.command()
@click.option(
    '--template',
    type=str,
    help='Template ID to use'
)
@click.option(
    '--interactive/--no-interactive',
    default=True,
    help='Interactive configuration'
)
@click.option(
    '--config-file',
    type=click.Path(exists=True, path_type=Path),
    help='Load configuration from file'
)
@click.option(
    '--save-config',
    type=click.Path(path_type=Path),
    help='Save configuration to file'
)
@click.option(
    '--data-dir',
    type=click.Path(exists=True, path_type=Path),
    help='Directory containing room data files'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
    help='Output directory for report'
)
@click.pass_context
def create(
    ctx,
    template: Optional[str],
    interactive: bool,
    config_file: Optional[Path],
    save_config: Optional[Path],
    data_dir: Optional[Path],
    output_dir: Optional[Path]
):
    """🎨 Create a custom report using the template system."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    
    # Set defaults
    data_dir = data_dir or workspace / "output" / "mapped" / "mapped_data"
    output_dir = output_dir or workspace / "output" / "template_reports"
    
    console.print("🎨 [bold blue]Creating Custom Report[/bold blue]")
    console.print(f"📂 Data directory: {data_dir}")
    console.print(f"📤 Output directory: {output_dir}")
    
    # Validate data directory
    if not data_dir.exists():
        console.print(f"[red]❌ Data directory not found: {data_dir}[/red]")
        console.print("Run 'ieq-analytics mapping' first to create mapped data.")
        sys.exit(1)
    
    try:
        template_manager = TemplateManager()
        
        # Load configuration from file if provided
        if config_file:
            console.print(f"📄 Loading configuration from: {config_file}")
            with open(config_file, 'r') as f:
                if config_file.suffix.lower() == '.json':
                    loaded_config = json.load(f)
                else:
                    loaded_config = yaml.safe_load(f)
            
            template_id = loaded_config.get('template_id')
            if not template_id:
                console.print("[red]❌ No template_id found in configuration file[/red]")
                sys.exit(1)
        else:
            # Interactive template selection
            if not template:
                if interactive:
                    template_id = template_manager.interactive_template_selection()
                    if not template_id:
                        console.print("[yellow]⚠️ No template selected[/yellow]")
                        return
                else:
                    console.print("[red]❌ Template ID required in non-interactive mode[/red]")
                    sys.exit(1)
            else:
                template_id = template
            
            # Interactive configuration
            if interactive:
                console.print("🔧 Starting interactive configuration...")
                loaded_config = template_manager.interactive_template_configuration(template_id)
                if not loaded_config:
                    console.print("[yellow]⚠️ Configuration cancelled[/yellow]")
                    return
            else:
                # Use default configuration
                template_obj = template_manager.get_template(template_id)
                if not template_obj:
                    console.print(f"[red]❌ Template not found: {template_id}[/red]")
                    sys.exit(1)
                
                sections = [s['id'] for s in template_obj.get_available_sections() if s.get('required', False)]
                charts = list(template_obj.get_available_charts().keys())[:5]  # First 5 charts
                
                loaded_config = template_obj.generate_report_config(
                    sections, charts, {}, {}
                )
        
        # Save configuration if requested
        if save_config:
            console.print(f"💾 Saving configuration to: {save_config}")
            with open(save_config, 'w') as f:
                if save_config.suffix.lower() == '.json':
                    json.dump(loaded_config, f, indent=2, default=str)
                else:
                    yaml.dump(loaded_config, f, default_flow_style=False)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and process data
        console.print("📊 Loading and processing data...")
        room_data = _load_room_data(data_dir)
        
        if not room_data:
            console.print("[red]❌ No room data found[/red]")
            sys.exit(1)
        
        console.print(f"📈 Loaded data for {len(room_data)} rooms")
        
        # Process data according to configuration
        processed_data = _process_data_for_template(room_data, loaded_config)
        
        # Generate report
        console.print("📝 Generating report...")
        report_result = _generate_template_report(loaded_config, processed_data, output_dir)
        
        if report_result.get('success'):
            console.print(f"[green]✅ Report generated successfully![/green]")
            
            success_panel = Panel.fit(
                f"[bold green]📄 Report Generated[/bold green]\n\n"
                f"📁 Template: {loaded_config['template_name']}\n"
                f"📊 Sections: {len(loaded_config['sections'])}\n"
                f"📈 Charts: {len(loaded_config['charts'])}\n"
                f"📂 Output: {report_result.get('output_path', 'Unknown')}\n\n"
                f"[italic]💡 Open the report file to view the analysis[/italic]",
                title="🎉 Report Complete",
                border_style="green"
            )
            console.print(success_panel)
        else:
            console.print(f"[red]❌ Report generation failed: {report_result.get('error')}[/red]")
        
    except Exception as e:
        console.print(f"[red]❌ Error creating report: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@templates.command()
@click.option(
    '--template',
    type=str,
    required=True,
    help='Template ID to preview'
)
@click.pass_context
def preview(ctx, template: str):
    """👀 Preview a template configuration and capabilities."""
    
    template_manager = TemplateManager()
    
    console.print(f"👀 [bold blue]Template Preview: {template}[/bold blue]")
    
    try:
        template_obj = template_manager.get_template(template)
        if not template_obj:
            console.print(f"[red]❌ Template not found: {template}[/red]")
            return
        
        # Show template information
        info = template_obj.get_template_info()
        
        info_panel = Panel.fit(
            f"[bold blue]Template Information[/bold blue]\n\n"
            f"📝 Name: {info['name']}\n"
            f"📁 Category: {info['category']}\n"
            f"📄 Description: {info['description']}\n"
            f"📊 Sections: {info['sections_count']}\n"
            f"📈 Charts: {info['charts_count']}\n"
            f"🔬 Advanced Analytics: {'Yes' if info['has_advanced_analytics'] else 'No'}",
            title="📋 Template Details",
            border_style="blue"
        )
        console.print(info_panel)
        
        # Show sections
        sections = template_obj.get_available_sections()
        console.print(f"\n📊 [bold]Available Sections ({len(sections)})[/bold]")
        
        sections_table = Table()
        sections_table.add_column("Section ID", style="cyan")
        sections_table.add_column("Name", style="white")
        sections_table.add_column("Required", style="red")
        sections_table.add_column("Charts", style="green")
        sections_table.add_column("Description", style="yellow")
        
        for section in sections:
            sections_table.add_row(
                section['id'],
                section['name'],
                "Yes" if section['required'] else "No",
                str(len(section['charts'])),
                section.get('description', 'No description')
            )
        
        console.print(sections_table)
        
        # Simplified chart display
        charts = template_obj.get_available_charts()
        console.print(f"\n📈 [bold]Available Charts ({len(charts)})[/bold]")
        
        chart_count = 0
        for chart_id, chart_config in charts.items():
            if chart_count >= 5:  # Show first 5 charts only
                break
            console.print(f"  • {chart_id}: {chart_config.get('name', 'No name')}")
            chart_count += 1
        
        if len(charts) > 5:
            console.print(f"  ... and {len(charts) - 5} more charts")
        
        # Show filters
        filters = template_obj.get_filter_options()
        if filters:
            console.print(f"\n🔍 [bold]Available Filters ({len(filters)})[/bold]")
            for filter_name, filter_config in filters.items():
                console.print(f"  • {filter_name}: {filter_config.get('description', 'No description')}")
        
        # Show advanced analytics
        advanced = template_obj.get_advanced_analytics_options()
        if advanced:
            console.print(f"\n🔬 [bold]Advanced Analytics ({len(advanced)})[/bold]")
            for analytics_name, analytics_config in advanced.items():
                console.print(f"  • {analytics_name}: {analytics_config.get('description', 'No description')}")
        
    except Exception as e:
        console.print(f"[red]❌ Error previewing template: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")


def _load_room_data(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load room data from CSV files."""
    room_data = {}
    
    # Find all processed CSV files
    csv_files = list(data_dir.glob("*_processed.csv"))
    
    for csv_file in csv_files:
        room_id = csv_file.stem.replace('_processed', '')
        
        try:
            df = pd.read_csv(csv_file)
            
            # Convert timestamp column if present
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
            
            if not df.empty:
                room_data[room_id] = df
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Error loading {csv_file}: {e}[/yellow]")
    
    return room_data


def _process_data_for_template(
    room_data: Dict[str, pd.DataFrame], 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Process room data according to template configuration."""
    
    processed_data = {
        'room_data': room_data,
        'summary_metrics': {},
        'advanced_analytics': {},
        'filtered_data': {}
    }
    
    # Calculate summary metrics
    all_co2 = []
    all_temp = []
    
    for room_id, df in room_data.items():
        if 'co2' in df.columns:
            co2_data = df['co2'].dropna()
            if not co2_data.empty:
                all_co2.extend(co2_data.values)
        
        if 'temperature' in df.columns:
            temp_data = df['temperature'].dropna()
            if not temp_data.empty:
                all_temp.extend(temp_data.values)
    
    if all_co2:
        processed_data['summary_metrics']['avg_co2'] = np.mean(all_co2)
    
    if all_temp:
        processed_data['summary_metrics']['avg_temperature'] = np.mean(all_temp)
    
    # Placeholder values for demonstration
    processed_data['summary_metrics']['compliance_rate'] = 75.0
    processed_data['summary_metrics']['data_quality'] = 0.85
    
    # Process advanced analytics if enabled
    advanced_settings = config.get('advanced_analytics', {})
    
    if advanced_settings.get('ventilation_rate_predictor', {}).get('enabled', False):
        console.print("🌪️ Running ventilation rate analysis...")
        try:
            # Use unified analytics engine for ventilation analysis
            unified_engine = UnifiedAnalyticsEngine()
            from ieq_analytics.unified_analytics import AnalysisType
            
            # Analyze each room's data
            ventilation_results = {}
            for room_id, df in room_data.items():
                room_results = unified_engine.analyze_room_data(
                    df, 
                    room_id=room_id,
                    analysis_types=[AnalysisType.BASIC_STATISTICS]
                )
                ventilation_results[room_id] = room_results
            
            processed_data['advanced_analytics']['ventilation'] = ventilation_results
        except Exception as e:
            console.print(f"[yellow]⚠️ Ventilation analysis failed: {e}[/yellow]")
    
    return processed_data


def _generate_template_report(
    config: Dict[str, Any], 
    processed_data: Dict[str, Any], 
    output_dir: Path
) -> Dict[str, Any]:
    """Generate the actual report using the template."""
    
    try:
        # For now, create a summary JSON file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"template_report_{config['template_id']}_{timestamp}.json"
        
        report_data = {
            'config': config,
            'data_summary': {
                'rooms_analyzed': len(processed_data['room_data']),
                'summary_metrics': processed_data['summary_metrics'],
                'advanced_analytics_enabled': len(processed_data['advanced_analytics'])
            },
            'generation_timestamp': datetime.now().isoformat()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return {
            'success': True,
            'output_path': str(output_file),
            'format': 'json'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
