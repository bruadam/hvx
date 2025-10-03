"""
Start command - Interactive IEQ analysis workflow.
"""

import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.command(name='start')
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Path to existing data directory')
@click.option('--auto', '-a', is_flag=True,
              help='Run in auto mode with default values')

def start(directory: Optional[Path], auto: bool):
    """
    Start a new IEQ analysis project interactively.

    This interactive workflow guides you through the complete analysis pipeline
    following INSTRUCTIONS.md:

    1. Ask for and load building data from directory
    2. Select standards, tests & guidelines to apply
    3. Process analytics
    4. Explore results interactively
    5. Generate reports (with template selection)
    6. Export analytics data in various formats
    7. Exit workflow

    Examples:

    \b
        # Start interactive workflow
        hvx ieq start

        # Start with specific data directory
        hvx ieq start --directory data/myproject

        # Run in auto mode (use defaults)
        hvx ieq start --auto
    """
    from src.cli.ui.workflows.interactive_workflow import launch_interactive_workflow

    try:
        # Launch workflow
        launch_interactive_workflow(
            data_directory=directory if directory else None,
            auto_mode=auto
        )

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Workflow cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        if click.get_current_context().obj and click.get_current_context().obj.get('verbose'):
            console.print_exception()
        raise click.Abort()
