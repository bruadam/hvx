"""
Report command module for IEQ Analytics CLI.

Simplified report generation focused on HTK template.
"""

import click
from pathlib import Path
from typing import Optional, List
import sys
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()


def setup_weasyprint_environment():
    """Setup environment for WeasyPrint on macOS."""
    if sys.platform == 'darwin':  # macOS
        # Add Homebrew library path for WeasyPrint dependencies
        homebrew_lib = '/opt/homebrew/lib'
        if os.path.exists(homebrew_lib):
            current_path = os.environ.get('DYLD_LIBRARY_PATH', '')
            if homebrew_lib not in current_path:
                new_path = f"{homebrew_lib}:{current_path}" if current_path else homebrew_lib
                os.environ['DYLD_LIBRARY_PATH'] = new_path
                console.print(f"[dim]🔧 Set DYLD_LIBRARY_PATH for WeasyPrint support[/dim]")


@click.group()
def report():
    """📊 Report generation commands."""
    pass


@report.command()
@click.option(
    '--data-dir',
    type=click.Path(exists=True, path_type=Path),
    help='Directory containing analyzed data'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
    help='Report output directory'
)
@click.option(
    '--buildings',
    type=str,
    multiple=True,
    help='Specific buildings to include (can be used multiple times)'
)
@click.option(
    '--format',
    'export_formats',
    type=click.Choice(['html', 'pdf']),
    multiple=True,
    default=['html'],
    help='Export formats (can be used multiple times)'
)
@click.pass_context
def htk(
    ctx,
    data_dir: Optional[Path],
    output_dir: Optional[Path],
    buildings: List[str],
    export_formats: List[str]
):
    """🏢 Generate Høje-Taastrup Kommune (HTK) specific report.
    
    Creates a comprehensive report specifically designed for HTK's requirements:
    - Data quality assessment for each location
    - Building-specific analysis with top issue rooms
    - Room-level performance by periods and seasons
    - Non-compliant hours analysis
    - Recommendations based on analysis results
    """
    
    # Setup environment for PDF generation
    setup_weasyprint_environment()
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    
    # Set defaults based on workspace structure
    data_dir = data_dir or workspace / "output" / "analysis"
    output_dir = output_dir or workspace / "output" / "reports" / "htk"
    
    console.print("🏢 [bold blue]Generating HTK Report...[/bold blue]")
    console.print(f"📂 Data directory: {data_dir}")
    console.print(f"📤 Output directory: {output_dir}")
    console.print(f"🏗️ Buildings: {', '.join(buildings) if buildings else 'All'}")
    console.print(f"📄 Formats: {', '.join(export_formats)}")
    
    # Validate inputs
    if not data_dir.exists():
        console.print(f"[red]❌ Data directory not found: {data_dir}[/red]")
        console.print("Run 'ieq-analytics analyze' first to generate analysis data.")
        sys.exit(1)
    
    try:
        from ieq_analytics.reporting.templates.library.htk.htk_template import HTKReportTemplate
        
        # Create HTK template instance
        htk_template = HTKReportTemplate()
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        console.print("🔧 Initializing HTK template...")
        
        # Generate the HTK report
        console.print("📝 Generating HTK report content...")
        
        result = htk_template.generate_report(
            data_dir=data_dir,
            output_dir=output_dir,
            buildings=list(buildings) if buildings else None,
            export_formats=list(export_formats)
        )
        
        if result.get('success'):
            console.print(f"[green]✅ HTK report generated successfully![/green]")
            
            # Display success summary
            generated_files = result.get('files', {})
            buildings_analyzed = result.get('buildings_analyzed', [])
            charts_generated = result.get('charts_generated', 0)
            
            success_panel = Panel.fit(
                f"[bold green]🏢 HTK Report Generated[/bold green]\n\n"
                f"📁 Files generated:\n" +
                '\n'.join([f"  • {fmt.upper()}: {path}" for fmt, path in generated_files.items()]) +
                f"\n\n🏗️ Buildings analyzed: {len(buildings_analyzed)}\n" +
                '\n'.join([f"  • {building}" for building in buildings_analyzed]) +
                f"\n\n📊 Charts generated: {charts_generated}\n"
                f"📅 Generated: {result.get('generation_time', 'Unknown')}\n\n"
                f"[italic]💡 Open the report to view detailed HTK analysis[/italic]",
                title="🎉 HTK Report Complete",
                border_style="green"
            )
            console.print(success_panel)
        else:
            console.print(f"[red]❌ HTK report generation failed[/red]")
            if 'error' in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            
    except ImportError as e:
        console.print(f"[red]❌ HTK template not available: {e}[/red]")
        console.print("Check that the HTK template is properly installed.")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error generating HTK report: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)
