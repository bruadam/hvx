"""
CLI commands for managing test configurations.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich import box
from typing import Optional, List

from src.services.test_management_service import (
    TestManagementService,
    TestDefinition,
    FilterDefinition,
    TestSet
)

console = Console()


@click.group(name='tests')
def tests():
    """Manage test configurations for analysis."""
    pass


# =====================
# Test Management
# =====================

@tests.command(name='list')
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
@click.option('--feature', help='Filter by feature (temperature, co2, combined)')
@click.option('--period', help='Filter by period (all_year, winter, summer, etc.)')
@click.option('--filter', 'filter_name', help='Filter by filter name')
def list_tests(config: Path, feature: Optional[str], period: Optional[str],
               filter_name: Optional[str]):
    """List all available tests."""
    service = TestManagementService(config)

    if feature or period or filter_name:
        tests_list = service.search_tests(feature=feature, period=period, filter_name=filter_name)
        console.print(f"\n[bold cyan]Filtered Tests[/bold cyan] ({len(tests_list)} found)\n")
    else:
        tests_list = service.list_tests()
        console.print(f"\n[bold cyan]All Tests[/bold cyan] ({len(tests_list)} total)\n")

    if not tests_list:
        console.print("[yellow]No tests found matching criteria.[/yellow]")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Feature", style="green")
    table.add_column("Period", style="yellow")
    table.add_column("Filter", style="magenta")
    table.add_column("Mode", style="blue")
    table.add_column("Limit(s)")

    for test in tests_list:
        if test.limit is not None:
            limit_str = str(test.limit)
        elif test.limits:
            limit_str = f"{test.limits.get('lower', '')} - {test.limits.get('upper', '')}"
        else:
            limit_str = "N/A"

        table.add_row(
            test.name,
            test.feature,
            test.period,
            test.filter,
            test.mode,
            limit_str
        )

    console.print(table)


@tests.command(name='show')
@click.argument('test_name')
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
def show_test(test_name: str, config: Path):
    """Show detailed information about a specific test."""
    service = TestManagementService(config)
    test = service.get_test(test_name)

    if not test:
        console.print(f"[red]✗ Test '{test_name}' not found.[/red]")
        raise click.Abort()

    console.print(Panel.fit(
        f"[bold blue]{test.name}[/bold blue]\n"
        f"{test.description}",
        border_style="blue"
    ))

    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value")

    table.add_row("Feature", test.feature)
    table.add_row("Period", test.period)
    table.add_row("Filter", test.filter)
    table.add_row("Mode", test.mode)

    if test.limit is not None:
        table.add_row("Limit", str(test.limit))
    if test.limits:
        table.add_row("Upper Limit", str(test.limits.get('upper', 'N/A')))
        table.add_row("Lower Limit", str(test.limits.get('lower', 'N/A')))
    if test.json_logic:
        table.add_row("JSON Logic", str(test.json_logic))

    console.print(table)


@tests.command(name='create')
@click.option('--config', type=click.Path(path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
@click.option('--from-test', help='Create from existing test as template')
def create_test(config: Path, from_test: Optional[str]):
    """Create a new test interactively."""
    service = TestManagementService(config)

    console.print(Panel.fit(
        "[bold blue]Create New Test[/bold blue]\n"
        "Follow the prompts to define your test configuration.",
        border_style="blue"
    ))

    # Start from existing test if specified
    if from_test:
        template = service.get_test(from_test)
        if not template:
            console.print(f"[red]✗ Template test '{from_test}' not found.[/red]")
            raise click.Abort()
        console.print(f"\n[green]Using '{from_test}' as template[/green]")
    else:
        template = None

    # Collect test details
    name = Prompt.ask("\n[cyan]Test name[/cyan] (e.g., temp_below_20_custom)")
    if service.get_test(name):
        if not Confirm.ask(f"[yellow]Test '{name}' exists. Overwrite?[/yellow]"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    description = Prompt.ask(
        "[cyan]Description[/cyan]",
        default=template.description if template else "Custom test"
    )

    # Feature
    features = ["temperature", "co2", "humidity", "combined"]
    console.print("\n[cyan]Feature:[/cyan]")
    for i, feat in enumerate(features, 1):
        console.print(f"  {i}. {feat}")
    feature_idx = IntPrompt.ask(
        "Select feature",
        default=features.index(template.feature) + 1 if template else 1
    ) - 1
    feature = features[feature_idx]

    # Period
    periods = list(service.get_periods().keys())
    console.print("\n[cyan]Period:[/cyan]")
    for i, per in enumerate(periods, 1):
        console.print(f"  {i}. {per}")
    period_idx = IntPrompt.ask(
        "Select period",
        default=periods.index(template.period) + 1 if template and template.period in periods else 1
    ) - 1
    period = periods[period_idx]

    # Filter
    filters = [f.name for f in service.list_filters()]
    console.print("\n[cyan]Filter:[/cyan]")
    for i, filt in enumerate(filters, 1):
        console.print(f"  {i}. {filt}")
    filter_idx = IntPrompt.ask(
        "Select filter",
        default=filters.index(template.filter) + 1 if template and template.filter in filters else 1
    ) - 1
    filter_name = filters[filter_idx]

    # Mode
    modes = ["unidirectional_ascending", "unidirectional_descending", "bidirectional"]
    console.print("\n[cyan]Mode:[/cyan]")
    for i, mode in enumerate(modes, 1):
        console.print(f"  {i}. {mode}")
    mode_idx = IntPrompt.ask(
        "Select mode",
        default=modes.index(template.mode) + 1 if template else 1
    ) - 1
    mode = modes[mode_idx]

    # Limits
    limit = None
    limits = None

    if mode in ["unidirectional_ascending", "unidirectional_descending"]:
        limit = FloatPrompt.ask(
            "[cyan]Threshold value[/cyan]",
            default=template.limit if template and template.limit else 20.0
        )
    elif mode == "bidirectional":
        upper = FloatPrompt.ask(
            "[cyan]Upper limit[/cyan]",
            default=template.limits.get('upper') if template and template.limits else 26.0
        )
        lower = FloatPrompt.ask(
            "[cyan]Lower limit[/cyan]",
            default=template.limits.get('lower') if template and template.limits else 20.0
        )
        limits = {'upper': upper, 'lower': lower}

    # Create test
    test = TestDefinition(
        name=name,
        description=description,
        feature=feature,
        period=period,
        filter=filter_name,
        mode=mode,
        limit=limit,
        limits=limits
    )

    service.add_test(test, overwrite=True)
    service.save_config()

    console.print(f"\n[green]✓ Test '{name}' created successfully![/green]")
    console.print(f"  Config saved to: [cyan]{config}[/cyan]")


@tests.command(name='edit')
@click.argument('test_name')
@click.option('--config', type=click.Path(path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
@click.option('--save-as', help='Save edited test with a new name')
def edit_test(test_name: str, config: Path, save_as: Optional[str]):
    """Edit an existing test interactively."""
    service = TestManagementService(config)
    test = service.get_test(test_name)

    if not test:
        console.print(f"[red]✗ Test '{test_name}' not found.[/red]")
        raise click.Abort()

    console.print(Panel.fit(
        f"[bold blue]Edit Test: {test_name}[/bold blue]\n"
        "Press Enter to keep current value.",
        border_style="blue"
    ))

    # Show current test
    _show_test_summary(test)

    # Edit fields
    new_name = save_as or Prompt.ask(
        "\n[cyan]Test name[/cyan]",
        default=test.name
    )

    description = Prompt.ask(
        "[cyan]Description[/cyan]",
        default=test.description
    )

    # Feature
    features = ["temperature", "co2", "humidity", "combined"]
    console.print("\n[cyan]Feature:[/cyan] (current: [yellow]" + test.feature + "[/yellow])")
    for i, feat in enumerate(features, 1):
        marker = " ←" if feat == test.feature else ""
        console.print(f"  {i}. {feat}{marker}")
    feature_idx = IntPrompt.ask(
        "Select feature",
        default=features.index(test.feature) + 1
    ) - 1
    feature = features[feature_idx]

    # Period
    periods = list(service.get_periods().keys())
    console.print("\n[cyan]Period:[/cyan] (current: [yellow]" + test.period + "[/yellow])")
    current_period_idx = periods.index(test.period) + 1 if test.period in periods else 1
    for i, per in enumerate(periods, 1):
        marker = " ←" if per == test.period else ""
        console.print(f"  {i}. {per}{marker}")
    period_idx = IntPrompt.ask("Select period", default=current_period_idx) - 1
    period = periods[period_idx]

    # Filter
    filters = [f.name for f in service.list_filters()]
    console.print("\n[cyan]Filter:[/cyan] (current: [yellow]" + test.filter + "[/yellow])")
    current_filter_idx = filters.index(test.filter) + 1 if test.filter in filters else 1
    for i, filt in enumerate(filters, 1):
        marker = " ←" if filt == test.filter else ""
        console.print(f"  {i}. {filt}{marker}")
    filter_idx = IntPrompt.ask("Select filter", default=current_filter_idx) - 1
    filter_name = filters[filter_idx]

    # Mode
    modes = ["unidirectional_ascending", "unidirectional_descending", "bidirectional"]
    console.print("\n[cyan]Mode:[/cyan] (current: [yellow]" + test.mode + "[/yellow])")
    for i, mode in enumerate(modes, 1):
        marker = " ←" if mode == test.mode else ""
        console.print(f"  {i}. {mode}{marker}")
    mode_idx = IntPrompt.ask("Select mode", default=modes.index(test.mode) + 1) - 1
    mode = modes[mode_idx]

    # Limits
    limit = None
    limits = None

    if mode in ["unidirectional_ascending", "unidirectional_descending"]:
        default_limit = test.limit if test.limit is not None else 20.0
        limit = FloatPrompt.ask("[cyan]Threshold value[/cyan]", default=default_limit)
    elif mode == "bidirectional":
        default_upper = test.limits.get('upper') if test.limits else 26.0
        default_lower = test.limits.get('lower') if test.limits else 20.0
        upper = FloatPrompt.ask("[cyan]Upper limit[/cyan]", default=default_upper)
        lower = FloatPrompt.ask("[cyan]Lower limit[/cyan]", default=default_lower)
        limits = {'upper': upper, 'lower': lower}

    # Create updated test
    updated_test = TestDefinition(
        name=new_name,
        description=description,
        feature=feature,
        period=period,
        filter=filter_name,
        mode=mode,
        limit=limit,
        limits=limits
    )

    if save_as or new_name != test_name:
        # Save as new test
        service.add_test(updated_test, overwrite=False)
        console.print(f"\n[green]✓ Test saved as '{new_name}'![/green]")
    else:
        # Update existing
        service.update_test(test_name, updated_test)
        console.print(f"\n[green]✓ Test '{test_name}' updated![/green]")

    service.save_config()
    console.print(f"  Config saved to: [cyan]{config}[/cyan]")


@tests.command(name='delete')
@click.argument('test_name')
@click.option('--config', type=click.Path(path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
@click.option('--yes', is_flag=True, help='Skip confirmation')
def delete_test(test_name: str, config: Path, yes: bool):
    """Delete a test."""
    service = TestManagementService(config)

    if not service.get_test(test_name):
        console.print(f"[red]✗ Test '{test_name}' not found.[/red]")
        raise click.Abort()

    if not yes:
        if not Confirm.ask(f"[yellow]Delete test '{test_name}'?[/yellow]"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    service.delete_test(test_name)
    service.save_config()
    console.print(f"[green]✓ Test '{test_name}' deleted.[/green]")


# =====================
# Filter Management
# =====================

@tests.command(name='filters')
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
def list_filters(config: Path):
    """List all available filters."""
    service = TestManagementService(config)
    filters = service.list_filters()

    console.print(f"\n[bold cyan]Available Filters[/bold cyan] ({len(filters)} total)\n")

    table = Table(box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Hours", style="yellow")
    table.add_column("Weekdays Only", style="green")
    table.add_column("Exclude Holidays", style="magenta")

    for f in filters:
        hours_str = f"{min(f.hours)}-{max(f.hours)}" if f.hours else "All"
        table.add_row(
            f.name,
            hours_str,
            "✓" if f.weekdays_only else "✗",
            "✓" if f.exclude_holidays or f.exclude_custom_holidays else "✗"
        )

    console.print(table)


@tests.command(name='filter-create')
@click.option('--config', type=click.Path(path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
def create_filter(config: Path):
    """Create a new filter interactively."""
    service = TestManagementService(config)

    console.print(Panel.fit(
        "[bold blue]Create New Filter[/bold blue]\n"
        "Define time-based filtering criteria.",
        border_style="blue"
    ))

    name = Prompt.ask("\n[cyan]Filter name[/cyan] (e.g., custom_hours)")
    if service.get_filter(name):
        if not Confirm.ask(f"[yellow]Filter '{name}' exists. Overwrite?[/yellow]"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    description = Prompt.ask("[cyan]Description[/cyan]", default="")

    # Hours
    console.print("\n[cyan]Define hours:[/cyan]")
    console.print("  1. Specific range (e.g., 8-15)")
    console.print("  2. Custom list (e.g., 8,9,10,14,15)")
    console.print("  3. All hours (0-23)")

    choice = IntPrompt.ask("Select option", default=1)

    if choice == 1:
        start_hour = IntPrompt.ask("Start hour (0-23)", default=8)
        end_hour = IntPrompt.ask("End hour (0-23)", default=15)
        hours = list(range(start_hour, end_hour + 1))
    elif choice == 2:
        hours_str = Prompt.ask("Enter hours (comma-separated)", default="8,9,10,11,12,13,14,15")
        hours = [int(h.strip()) for h in hours_str.split(',')]
    else:
        hours = list(range(24))

    weekdays_only = Confirm.ask("\n[cyan]Weekdays only?[/cyan]", default=True)
    exclude_holidays = Confirm.ask("[cyan]Exclude public holidays?[/cyan]", default=False)
    exclude_custom = Confirm.ask("[cyan]Exclude custom holidays (school vacations)?[/cyan]", default=False)

    # Create filter
    filter_def = FilterDefinition(
        name=name,
        description=description,
        hours=hours,
        weekdays_only=weekdays_only,
        exclude_holidays=exclude_holidays,
        exclude_custom_holidays=exclude_custom
    )

    service.add_filter(filter_def, overwrite=True)
    service.save_config()

    console.print(f"\n[green]✓ Filter '{name}' created successfully![/green]")
    console.print(f"  Config saved to: [cyan]{config}[/cyan]")


# =====================
# Test Set Management
# =====================

@tests.command(name='sets')
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
def list_test_sets(config: Path):
    """List all test sets."""
    service = TestManagementService(config)
    sets = service.list_test_sets()

    console.print(f"\n[bold cyan]Test Sets[/bold cyan] ({len(sets)} total)\n")

    if not sets:
        console.print("[yellow]No test sets defined yet. Create one with 'hvx tests set-create'.[/yellow]")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Tests", justify="right", style="yellow")

    for test_set in sets:
        table.add_row(
            test_set.name,
            test_set.description,
            str(len(test_set.test_names))
        )

    console.print(table)


@tests.command(name='set-show')
@click.argument('set_name')
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
def show_test_set(set_name: str, config: Path):
    """Show tests in a set."""
    service = TestManagementService(config)
    test_set = service.get_test_set(set_name)

    if not test_set:
        console.print(f"[red]✗ Test set '{set_name}' not found.[/red]")
        raise click.Abort()

    console.print(Panel.fit(
        f"[bold blue]{test_set.name}[/bold blue]\n"
        f"{test_set.description}",
        border_style="blue"
    ))

    console.print(f"\n[bold cyan]Tests in set:[/bold cyan] ({len(test_set.test_names)} tests)\n")

    for i, test_name in enumerate(test_set.test_names, 1):
        test = service.get_test(test_name)
        if test:
            console.print(f"  {i}. [cyan]{test_name}[/cyan] - {test.description}")
        else:
            console.print(f"  {i}. [red]{test_name}[/red] [dim](not found)[/dim]")


@tests.command(name='set-create')
@click.option('--config', type=click.Path(path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
def create_test_set(config: Path):
    """Create a new test set interactively."""
    service = TestManagementService(config)

    console.print(Panel.fit(
        "[bold blue]Create Test Set[/bold blue]\n"
        "Select tests to include in your custom analysis set.",
        border_style="blue"
    ))

    name = Prompt.ask("\n[cyan]Set name[/cyan] (e.g., summer_analysis)")
    if service.get_test_set(name):
        if not Confirm.ask(f"[yellow]Set '{name}' exists. Overwrite?[/yellow]"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    description = Prompt.ask("[cyan]Description[/cyan]", default="Custom test set")

    # Get all tests
    all_tests = service.list_tests()

    console.print(f"\n[cyan]Available tests:[/cyan] ({len(all_tests)} total)")
    console.print("[dim]Select tests by entering numbers separated by commas, or ranges (e.g., 1,3,5-8)[/dim]\n")

    # Display tests
    for i, test in enumerate(all_tests, 1):
        console.print(f"  {i:3d}. {test.name:50s} [{test.feature}]")

    selection = Prompt.ask("\n[cyan]Select tests[/cyan] (e.g., 1-5,10,12)")

    # Parse selection
    selected_indices = _parse_selection(selection, len(all_tests))
    selected_tests = [all_tests[i].name for i in selected_indices]

    if not selected_tests:
        console.print("[red]✗ No tests selected.[/red]")
        return

    # Create test set
    test_set = TestSet(
        name=name,
        description=description,
        test_names=selected_tests
    )

    service.add_test_set(test_set, overwrite=True)
    service.save_config()

    console.print(f"\n[green]✓ Test set '{name}' created with {len(selected_tests)} tests![/green]")
    console.print(f"  Config saved to: [cyan]{config}[/cyan]")


@tests.command(name='set-export')
@click.argument('set_name')
@click.option('--output', type=click.Path(path_type=Path),
              help='Output path for exported config')
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              default='config/tests.yaml', help='Path to tests config file')
def export_test_set(set_name: str, output: Optional[Path], config: Path):
    """Export a test set as a standalone config file."""
    service = TestManagementService(config)

    if not service.get_test_set(set_name):
        console.print(f"[red]✗ Test set '{set_name}' not found.[/red]")
        raise click.Abort()

    output_path = output or Path(f"config/test_sets/{set_name}.yaml")

    if service.export_test_set_config(set_name, output_path):
        console.print(f"[green]✓ Test set exported to: [cyan]{output_path}[/cyan][/green]")
    else:
        console.print("[red]✗ Export failed.[/red]")


# =====================
# Helper Functions
# =====================

def _show_test_summary(test: TestDefinition):
    """Display a summary of a test."""
    console.print(f"\n[bold]Current configuration:[/bold]")
    console.print(f"  Name: [cyan]{test.name}[/cyan]")
    console.print(f"  Feature: [yellow]{test.feature}[/yellow]")
    console.print(f"  Period: [yellow]{test.period}[/yellow]")
    console.print(f"  Filter: [yellow]{test.filter}[/yellow]")
    console.print(f"  Mode: [yellow]{test.mode}[/yellow]")
    if test.limit:
        console.print(f"  Limit: [yellow]{test.limit}[/yellow]")
    if test.limits:
        console.print(f"  Limits: [yellow]{test.limits}[/yellow]")


def _parse_selection(selection: str, max_value: int) -> List[int]:
    """Parse selection string like '1,3,5-8' into list of indices."""
    indices = []
    parts = selection.split(',')

    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            indices.extend(range(int(start) - 1, int(end)))
        else:
            indices.append(int(part) - 1)

    # Filter valid indices
    return [i for i in indices if 0 <= i < max_value]
