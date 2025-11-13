"""Panel components for CLI UI."""

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def create_welcome_panel() -> Panel:
    """Create welcome panel for CLI."""
    left = Text(justify="center")
    left.append("Welcome to IEQ Analytics!\n\n", style="bold cyan")
    left.append("Let's analyze your building's indoor environmental quality.\n\n", style="cyan")
    left.append("Type 'help' for assistance or 'quit' to exit at any time.\n", style="dim")

    right = Table.grid(padding=(0, 1))
    right.add_column(justify="left", ratio=1)
    right.add_row("[bold]Tips for getting started:[/bold]")
    right.add_row("• You will be guided through each step")
    right.add_row("• Press Enter to accept defaults")
    right.add_row("• Type '?' for context-specific help")
    right.add_row("• Type 'quit' to exit anytime")

    inner_panel = Table.grid(expand=True)
    inner_panel.add_column(ratio=1)
    inner_panel.add_column(ratio=2)
    inner_panel.add_row(
        Panel(left, padding=(1, 2), border_style="none"),
        Panel(right, padding=(1, 1), border_style="none")
    )

    return Panel(
        inner_panel,
        box=box.ROUNDED,
        border_style="cyan",
        title="[bold]🌡️  IEQ Analytics[/bold]"
    )


def create_step_panel(step_number: int, title: str, description: str = "") -> Panel:
    """Create panel for a workflow step."""
    content = f"[bold cyan]Step {step_number}: {title}[/bold cyan]"
    if description:
        content += f"\n[dim]{description}[/dim]"

    return Panel(
        content,
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1)
    )


def create_success_panel(message: str, details: str = "") -> Panel:
    """Create success message panel."""
    content = f"[bold green]✓ {message}[/bold green]"
    if details:
        content += f"\n[dim]{details}[/dim]"

    return Panel(
        content,
        box=box.ROUNDED,
        border_style="green",
        padding=(0, 1)
    )


def create_error_panel(message: str, suggestion: str = "") -> Panel:
    """Create error message panel."""
    content = f"[bold red]✗ Error: {message}[/bold red]"
    if suggestion:
        content += f"\n\n[yellow]💡 Suggestion:[/yellow] {suggestion}"

    return Panel(
        content,
        box=box.ROUNDED,
        border_style="red",
        padding=(1, 2)
    )


def create_completion_panel(summary: dict) -> Panel:
    """Create workflow completion summary panel."""
    content = "[bold green]✓ Workflow Complete![/bold green]\n\n"

    if 'rooms_analyzed' in summary:
        content += f"[cyan]Rooms Analyzed:[/cyan] {summary['rooms_analyzed']}\n"
    if 'compliance_rate' in summary:
        content += f"[cyan]Overall Compliance:[/cyan] {summary['compliance_rate']:.1f}%\n"
    if 'report_path' in summary:
        content += f"[cyan]Report Generated:[/cyan] {summary['report_path']}\n"
    if 'data_exported' in summary:
        content += f"[cyan]Data Exported:[/cyan] {summary['data_exported']}\n"

    content += "\n[dim]Thank you for using IEQ Analytics![/dim]"

    return Panel(
        content,
        box=box.ROUNDED,
        border_style="green",
        title="[bold]Summary[/bold]",
        padding=(1, 2)
    )


def create_help_panel(help_text: str) -> Panel:
    """Create context help panel."""
    return Panel(
        help_text,
        box=box.ROUNDED,
        border_style="yellow",
        title="[bold]Help[/bold]",
        padding=(1, 2)
    )
