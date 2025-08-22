
"""
Main CLI entry point for IEQ Analytics.

Modular CLI structure with separate command modules for improved ma# Register command groups
cli.add_command(analyze)
cli.add_command(mapping)
cli.add_command(rules)
cli.add_command(report)
cli.add_command(projects)nability.
"""

import click
from pathlib import Path
import sys
from rich.console import Console

# Import command modules
from .commands.analyze import analyze
from .commands.mapping import mapping  
from .commands.rules import rules
from .commands.report import report
from .commands.projects import projects
from .commands.templates import templates
from .commands.charts import charts
from .commands.climate import climate

console = Console()


class PipelineState:
    """Track pipeline state across commands."""
    
    def __init__(self):
        self.mapping_completed = False
        self.analysis_completed = False
        self.files_mapped = 0
        self.buildings_discovered = 0
        self.rooms_mapped = 0
    
    def update_mapping_state(self, files_count: int, buildings_count: int, rooms_count: int):
        """Update mapping pipeline state."""
        self.mapping_completed = True
        self.files_mapped = files_count
        self.buildings_discovered = buildings_count
        self.rooms_mapped = rooms_count
    
    def update_analysis_state(self):
        """Update analysis pipeline state."""
        self.analysis_completed = True


@click.group(invoke_without_command=True)
@click.option('--workspace', type=click.Path(path_type=Path), help='Workspace directory')
@click.option('--debug/--no-debug', default=False, help='Enable debug output')
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def cli(ctx, workspace: Path, debug: bool, version: bool):
    """🏢 IEQ Analytics - Indoor Environmental Quality Analysis Platform
    
    A comprehensive tool for analyzing and reporting on indoor environmental
    quality data including temperature, humidity, and CO2 measurements.
    
    Commands:
        mapping   - Map raw CSV sensor data to standardized format
        analyze   - Analyze mapped data for comfort compliance
        climate   - Analyze climate-indoor correlations for solar sensitivity
        charts    - Manage shared chart library and visualizations
        rules     - Create and manage analytics rules
        report    - Generate comprehensive analysis reports
        projects  - Manage IEQ projects and configurations
        templates - Interactive template-based report creation
    """
    
    if version:
        console.print("🏢 IEQ Analytics v1.0.0")
        console.print("Indoor Environmental Quality Analysis Platform")
        sys.exit(0)
    
    # Initialize context
    ctx.ensure_object(dict)
    
    # Set workspace
    if workspace:
        workspace = workspace.resolve()
    else:
        workspace = Path.cwd()
    
    ctx.obj['workspace'] = workspace
    ctx.obj['debug'] = debug
    ctx.obj['pipeline_state'] = PipelineState()
    
    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        
        # Show workspace info
        console.print(f"\n📁 Workspace: {workspace}")
        
        # Check for existing data
        data_checks = [
            ("Raw data", workspace / "data" / "raw"),
            ("Mapped data", workspace / "output" / "mapped" / "mapped_data"),
            ("Analysis results", workspace / "output" / "analysis"),
            ("Reports", workspace / "output" / "reports")
        ]
        
        console.print("\n📊 Data Status:")
        for name, path in data_checks:
            if path.exists() and path.is_dir():
                try:
                    has_files = any(path.iterdir())
                    status = "✅" if has_files else "📁"
                except PermissionError:
                    status = "🔒"
            else:
                status = "❌"
            console.print(f"  {status} {name}: {path}")
        
        console.print("\n💡 Quick Start:")
        console.print("  1. ieq-analytics mapping     # Map raw CSV files")
        console.print("  2. ieq-analytics analyze     # Analyze mapped data")
        console.print("  3. ieq-analytics climate     # Climate correlation analysis") 
        console.print("  4. ieq-analytics charts list  # Browse available charts")
        console.print("  5. ieq-analytics templates browse  # Interactive template selection")
        console.print("  6. ieq-analytics report from-yaml --interactive  # Generate reports")


# Register command groups
cli.add_command(analyze)
cli.add_command(mapping)
cli.add_command(climate)
cli.add_command(rules)
cli.add_command(report)
cli.add_command(projects)
cli.add_command(templates)
cli.add_command(charts)


def main():
    """Main entry point function for console script."""
    cli()


if __name__ == '__main__':
    main()
