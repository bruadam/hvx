"""
Interactive Rule Selector

Provides UI components for selecting IEQ analysis rules, filters, and periods.
"""

from typing import List, Set, Dict, Any, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box

from src.core.analytics.ieq.ConfigBuilder import (
    IEQConfigBuilder,
    RuleDefinition,
    FilterDefinition,
    PeriodDefinition
)

console = Console()


class RuleSelector:
    """Interactive selector for IEQ analysis rules."""

    def __init__(self, builder: IEQConfigBuilder):
        """Initialize the rule selector."""
        self.builder = builder
        self.selected_standards: Set[str] = set()
        self.selected_individual_rules: Set[str] = set()
        self.custom_filter_overrides: Dict[str, str] = {}
        self.custom_period_overrides: Dict[str, str] = {}
        self.global_filter: Optional[str] = None
        self.global_period: Optional[str] = None

    def run_interactive_selection(self) -> IEQConfigBuilder:
        """
        Run the interactive rule selection workflow.

        Returns:
            Configured IEQConfigBuilder instance
        """
        console.clear()
        self._show_welcome()

        # Step 1: Select standards or individual rules
        self._select_rules_or_standards()

        # Step 2: Configure filters and periods
        if self.selected_standards or self.selected_individual_rules:
            self._configure_filters_and_periods()

        # Step 3: Show summary and confirm
        self._show_summary()

        return self.builder

    def _show_welcome(self):
        """Display welcome message."""
        welcome = Panel.fit(
            "[bold cyan]IEQ Analysis Configuration[/bold cyan]\n\n"
            "Configure which analysis rules to run and how to apply them.\n\n"
            "[bold]Steps:[/bold]\n"
            "  1. Select standards or individual rules\n"
            "  2. Configure filters (opening hours, holidays, etc.)\n"
            "  3. Configure periods (seasons, heating season, etc.)\n"
            "  4. Review and confirm",
            border_style="cyan"
        )
        console.print(welcome)
        console.print()

    def _select_rules_or_standards(self):
        """Select between standards or individual rules."""
        console.print("[bold cyan]═══ Step 1: Select Rules ═══[/bold cyan]\n")

        console.print("[bold]Options:[/bold]")
        console.print("  1. Select entire standard(s) (all rules from EN16798-1, BR18, etc.)")
        console.print("  2. Select individual rules")
        console.print("  3. Combination (standards + individual rules)")
        console.print()

        choice = Prompt.ask("[bold]Choose option[/bold]", choices=["1", "2", "3"], default="1")

        if choice in ["1", "3"]:
            self._select_standards()

        if choice in ["2", "3"]:
            self._select_individual_rules()

    def _select_standards(self):
        """Select one or more standards."""
        console.print("\n[bold]Available Standards:[/bold]\n")

        standards = self.builder.get_available_standards()

        # Display standards with rule counts
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Standard", style="bold")
        table.add_column("Rules", justify="right")
        table.add_column("Description")

        standard_descriptions = {
            "en16798-1": "European standard for indoor environmental input parameters",
            "br18": "Danish Building Regulations 2018",
            "danish-guidelines": "Danish guidelines for indoor climate"
        }

        for i, standard in enumerate(standards, 1):
            rules = self.builder.get_rules_for_standard(standard)
            desc = standard_descriptions.get(standard, "")
            table.add_row(str(i), standard, str(len(rules)), desc)

        console.print(table)
        console.print()

        # Multi-select standards
        console.print("[dim]Enter standard numbers separated by commas (e.g., 1,2) or 'all' for all standards[/dim]")
        selection = Prompt.ask("[bold]Select standards[/bold]", default="all")

        if selection.lower() == "all":
            self.selected_standards = set(standards)
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                self.selected_standards = {standards[i] for i in indices if 0 <= i < len(standards)}
            except (ValueError, IndexError):
                console.print("[yellow]Invalid selection, no standards selected[/yellow]")

        # Add selected standards to builder
        for standard in self.selected_standards:
            self.builder.add_standard(standard)

        if self.selected_standards:
            console.print(f"\n[green]✓[/green] Selected {len(self.selected_standards)} standard(s)")

    def _select_individual_rules(self):
        """Select individual rules across all standards."""
        console.print("\n[bold]Select Individual Rules:[/bold]\n")

        all_rules = self.builder.get_all_rules()

        # Group rules by feature and standard
        rules_by_feature: Dict[str, List[RuleDefinition]] = {}
        for rule in all_rules:
            if rule.feature not in rules_by_feature:
                rules_by_feature[rule.feature] = []
            rules_by_feature[rule.feature].append(rule)

        # Display rules grouped by feature
        for feature, rules in sorted(rules_by_feature.items()):
            console.print(f"\n[bold cyan]{feature.upper()}[/bold cyan]")

            table = Table(box=box.SIMPLE, show_header=True)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Rule Name", style="bold")
            table.add_column("Standard")
            table.add_column("Description")

            for i, rule in enumerate(rules, 1):
                table.add_row(
                    str(i),
                    rule.name,
                    rule.standard,
                    rule.description[:60] + "..." if len(rule.description) > 60 else rule.description
                )

            console.print(table)

            # Ask if user wants to select from this feature
            if Confirm.ask(f"\n[bold]Select rules for {feature}?[/bold]", default=False):
                console.print("[dim]Enter rule numbers separated by commas (e.g., 1,2,3)[/dim]")
                selection = Prompt.ask(f"[bold]Select {feature} rules[/bold]", default="")

                if selection:
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(",")]
                        for i in indices:
                            if 0 <= i < len(rules):
                                rule = rules[i]
                                self.builder.add_rule(rule.name, rule.standard)
                                self.selected_individual_rules.add(rule.name)
                    except (ValueError, IndexError):
                        console.print("[yellow]Invalid selection for this feature[/yellow]")

        if self.selected_individual_rules:
            console.print(f"\n[green]✓[/green] Selected {len(self.selected_individual_rules)} individual rule(s)")

    def _configure_filters_and_periods(self):
        """Configure filters and periods for selected rules."""
        console.print("\n[bold cyan]═══ Step 2: Configure Filters & Periods ═══[/bold cyan]\n")

        # Configure filters
        if Confirm.ask("[bold]Apply custom filter settings?[/bold]", default=True):
            self._configure_filters()

        # Configure periods
        if Confirm.ask("\n[bold]Apply custom period settings?[/bold]", default=True):
            self._configure_periods()

    def _configure_filters(self):
        """Configure filter settings."""
        console.print("\n[bold]Filter Configuration:[/bold]\n")

        filters = self.builder.get_available_filters()

        # Display available filters
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Filter Name", style="bold")
        table.add_column("Description")

        for i, filter_def in enumerate(filters, 1):
            table.add_row(
                str(i),
                filter_def.name,
                filter_def.description
            )

        console.print(table)
        console.print()

        # Options
        console.print("[bold]Options:[/bold]")
        console.print("  1. Apply one filter to ALL rules")
        console.print("  2. Keep each rule's default filter")
        console.print("  3. Skip filter configuration")
        console.print()

        choice = Prompt.ask("[bold]Choose option[/bold]", choices=["1", "2", "3"], default="2")

        if choice == "1":
            console.print("\n[dim]Enter filter number[/dim]")
            filter_idx = Prompt.ask("[bold]Select filter[/bold]", default="1")

            try:
                idx = int(filter_idx) - 1
                if 0 <= idx < len(filters):
                    self.global_filter = filters[idx].name
                    self.builder.apply_filter_to_all(self.global_filter)
                    console.print(f"\n[green]✓[/green] Applying '{self.global_filter}' to all rules")
            except (ValueError, IndexError):
                console.print("[yellow]Invalid selection[/yellow]")

    def _configure_periods(self):
        """Configure period settings."""
        console.print("\n[bold]Period Configuration:[/bold]\n")

        periods = self.builder.get_available_periods()

        # Display available periods
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Period Name", style="bold")
        table.add_column("Description")

        for i, period_def in enumerate(periods, 1):
            table.add_row(
                str(i),
                period_def.name,
                period_def.description
            )

        console.print(table)
        console.print()

        # Options
        console.print("[bold]Options:[/bold]")
        console.print("  1. Apply one period to ALL rules")
        console.print("  2. Keep each rule's default period")
        console.print("  3. Skip period configuration")
        console.print()

        choice = Prompt.ask("[bold]Choose option[/bold]", choices=["1", "2", "3"], default="2")

        if choice == "1":
            console.print("\n[dim]Enter period number[/dim]")
            period_idx = Prompt.ask("[bold]Select period[/bold]", default="1")

            try:
                idx = int(period_idx) - 1
                if 0 <= idx < len(periods):
                    self.global_period = periods[idx].name
                    self.builder.apply_period_to_all(self.global_period)
                    console.print(f"\n[green]✓[/green] Applying '{self.global_period}' to all rules")
            except (ValueError, IndexError):
                console.print("[yellow]Invalid selection[/yellow]")

    def _show_summary(self):
        """Display configuration summary."""
        console.print("\n[bold cyan]═══ Configuration Summary ═══[/bold cyan]\n")

        summary = self.builder.get_summary()
        console.print(summary)
        console.print()

        # Show filter and period settings
        if self.global_filter:
            console.print(f"[bold]Global Filter:[/bold] {self.global_filter}")
        if self.global_period:
            console.print(f"[bold]Global Period:[/bold] {self.global_period}")

        console.print()


def create_custom_config(auto_mode: bool = False) -> Tuple[Dict[str, Any], str]:
    """
    Create a custom analysis configuration interactively.

    Args:
        auto_mode: If True, use default selections

    Returns:
        Tuple of (config_dict, summary_text)
    """
    builder = IEQConfigBuilder()

    if auto_mode:
        # Auto mode: select all standards with default filters/periods
        for standard in builder.get_available_standards():
            builder.add_standard(standard)

        summary = builder.get_summary()
        config = builder.build()

        return config, summary
    else:
        # Interactive mode
        selector = RuleSelector(builder)
        selector.run_interactive_selection()

        summary = builder.get_summary()
        config = builder.build()

        return config, summary
