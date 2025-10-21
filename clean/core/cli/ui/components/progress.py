"""Progress indicators for CLI UI."""

from typing import List
from dataclasses import dataclass
from rich.panel import Panel
from rich import box


@dataclass
class WorkflowStep:
    """Represents a workflow step."""
    number: int
    title: str
    status: str  # 'pending', 'active', 'completed'
    summary: str = ""
    details: List[str] = None

    def __post_init__(self):
        if self.details is None:
            self.details = []


class ProgressTracker:
    """Track and display workflow progress."""

    def __init__(self):
        self.steps: List[WorkflowStep] = []

    def add_step(self, number: int, title: str, status: str = 'pending') -> None:
        """Add a workflow step."""
        self.steps.append(WorkflowStep(
            number=number,
            title=title,
            status=status
        ))

    def start_step(self, number: int) -> None:
        """Mark a step as active."""
        # Mark all previous steps as completed
        for step in self.steps:
            if step.number < number and step.status == 'active':
                step.status = 'completed'

        # Mark current step as active
        for step in self.steps:
            if step.number == number:
                step.status = 'active'
                break

    def complete_step(self, number: int, summary: str = "", details: List[str] = None) -> None:
        """Mark a step as completed with summary."""
        for step in self.steps:
            if step.number == number:
                step.status = 'completed'
                step.summary = summary
                if details:
                    step.details = details
                break

    def render(self) -> Panel:
        """Render progress panel."""
        lines = []

        for step in self.steps:
            if step.status == "completed":
                # Collapsed: show checkmark and summary
                summary_text = f" - {step.summary}" if step.summary else ""
                lines.append(
                    f"[green]✓[/green] [dim]{step.number}. {step.title}{summary_text}[/dim]"
                )
            elif step.status == "active":
                # Active step
                lines.append(f"[bold cyan]▶ {step.number}. {step.title}[/bold cyan]")
            else:
                # Pending
                lines.append(f"[dim]  {step.number}. {step.title}[/dim]")

        content = "\n".join(lines) if lines else "[dim]No steps yet[/dim]"

        return Panel(
            content,
            title="[bold]Workflow Progress[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2)
        )


def create_spinner_text(message: str) -> str:
    """Create text for spinner/progress indicator."""
    return f"[cyan]{message}...[/cyan]"


def create_progress_message(current: int, total: int, item_name: str = "item") -> str:
    """Create progress message."""
    percentage = (current / total * 100) if total > 0 else 0
    return f"[cyan]Processing {item_name} {current} of {total}[/cyan] [dim]({percentage:.0f}%)[/dim]"
