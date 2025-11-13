"""Main CLI application for IEQ Analytics."""

from pathlib import Path

import click
from rich.console import Console

from core.cli.commands.analyze import analyze
from core.cli.commands.data import data
from core.cli.commands.report import report
from core.cli.commands.tail import tail

console = Console()


@click.group()
@click.version_option(version="2.0.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """
    HVX Analytics - Building Performance Analysis Tool

    Supports multiple analysis types:
    - IEQ: Indoor Environmental Quality
    - Energy: Energy Performance (coming soon)
    - Carbon: Carbon Footprint (coming soon)

    Includes TAIL rating visualizations for building environmental quality.
    """
    ctx.ensure_object(dict)
    ctx.obj['console'] = console
    ctx.obj['verbose'] = verbose


# Register command groups
cli.add_command(data)
cli.add_command(analyze)
cli.add_command(report)
cli.add_command(tail)  # NEW: TAIL rating charts


@cli.group()
def ieq():
    """Indoor Environmental Quality (IEQ) analysis commands."""
    pass


@cli.group()
def energy():
    """Energy performance analysis commands (coming soon)."""
    pass


@ieq.command(name='start')
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Path to data directory')
@click.option('--auto', '-a', is_flag=True,
              help='Run in auto mode with default values')
@click.pass_context
def ieq_start(ctx, directory, auto):
    """
    Start interactive IEQ analysis workflow.

    This command launches an interactive step-by-step workflow that guides
    you through the complete IEQ analysis process from data loading to report
    generation.

    Examples:

        hvx ieq start
        hvx ieq start --directory data/my-building
        hvx ieq start --auto
    """
    from core.cli.ui.workflows.ieq_interactive import IEQInteractiveWorkflow

    try:
        workflow = IEQInteractiveWorkflow(
            auto_mode=auto,
            verbose=ctx.obj.get('verbose', False)
        )

        if directory:
            workflow.data_directory = directory

        workflow.run()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ Workflow cancelled by user[/yellow]")
        ctx.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        if ctx.obj.get('verbose'):
            console.print_exception()
        ctx.exit(1)


@energy.command(name='start')
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Path to data directory')
@click.option('--auto', '-a', is_flag=True,
              help='Run in auto mode with default values')
@click.pass_context
def energy_start(ctx, directory, auto):
    """
    Start interactive energy analysis workflow (coming soon).

    This command will launch an interactive workflow for energy performance
    analysis.

    Examples:

        hvx energy start
        hvx energy start --directory data/my-building
    """
    console.print("\n[yellow]⚠ Energy analysis module coming soon[/yellow]")
    console.print("[dim]This feature is planned for a future release[/dim]\n")
    ctx.exit(0)


# Backward compatibility - direct 'start' command defaults to IEQ
@cli.command(name='start')
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Path to data directory')
@click.option('--auto', '-a', is_flag=True,
              help='Run in auto mode with default values')
@click.option('--type', '-t', type=click.Choice(['ieq', 'energy']), default='ieq',
              help='Analysis type (default: ieq)')
@click.pass_context
def start(ctx, directory, auto, type):
    """
    Start interactive analysis workflow (defaults to IEQ).

    Shortcut command that defaults to IEQ analysis.
    For explicit type selection, use 'hvx ieq start' or 'hvx energy start'.

    Examples:

        hvx start                    # IEQ analysis
        hvx start --type energy      # Energy analysis
        hvx start --directory data   # IEQ with specific directory
    """
    if type == 'ieq':
        ctx.invoke(ieq_start, directory=directory, auto=auto)
    elif type == 'energy':
        ctx.invoke(energy_start, directory=directory, auto=auto)


if __name__ == '__main__':
    cli()
