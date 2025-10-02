"""HVX CLI - Main entry point."""

from src import __version__
import click
from rich.console import Console
from rich.table import Table
from rich.theme import Theme
from pathlib import Path

custom_theme = Theme({"info": "bold blue"})
console = Console(theme=custom_theme)


class RichHelpGroup(click.Group):
    def format_help(self, ctx, formatter):
        console.print("[bold blue]HVX[/bold blue]")
        console.print(
            "[blue]A Facility Management CLI tool for analyzing building performance.[/blue]\n"
            "- Indoor Environmental Quality\n"
            "- Energy Efficiency\n"
            "[dim]Open Source, Transparent and Extensible.[/dim]\n"
        )

        table = Table(title="Available Commands", style="blue", header_style="bold blue")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")

        for command in self.commands.values():
            help_str = command.get_short_help_str()
            table.add_row(f"[cyan]{command.name}[/cyan]", help_str)

        console.print(table)
        console.print(f"\n[dim]Version: {__version__}[/dim]")

    def get_help(self, ctx):
        from io import StringIO
        with console.capture() as capture:
            self.format_help(ctx, ctx.make_formatter())
        return capture.get()


@click.group(cls=RichHelpGroup)
@click.version_option(version=__version__, prog_name='hvx')
def cli():
    """HVX - HVAC Analytics eXpert

    A Facility Management CLI tool for analyzing building performance.

    - Indoor Environmental Quality (IEQ) Analytics
    - Energy Efficiency Analytics

    Open Source, Transparent and Extensible.
    """
    pass


# Import and register command groups
from src.cli.commands import graphs, templates, analytics, reports, data, analyze

cli.add_command(graphs.graphs)
cli.add_command(templates.templates)
cli.add_command(analytics.analytics)
cli.add_command(reports.reports)
cli.add_command(data.data)
cli.add_command(analyze.analyze_cli)


if __name__ == '__main__':
    cli()
