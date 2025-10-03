"""
IEQ Configuration Builder

Provides an interface to dynamically build analysis configurations by selecting:
- Standards (EN16798-1, BR18, Danish Guidelines, etc.)
- Individual rules from any standard
- Filters (opening hours, with/without holidays, custom time periods)
- Periods (seasons, heating/non-heating, all year)
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import yaml

from src.core.analytics.ieq.config_loader import IEQConfigLoader


@dataclass
class RuleDefinition:
    """Represents a single rule definition."""
    name: str
    standard: str
    description: str
    feature: str
    config: Dict[str, Any]


@dataclass
class FilterDefinition:
    """Represents a filter definition."""
    name: str
    description: str
    config: Dict[str, Any]


@dataclass
class PeriodDefinition:
    """Represents a period definition."""
    name: str
    description: str
    config: Dict[str, Any]


class IEQConfigBuilder:
    """
    Builder for creating custom IEQ analysis configurations.

    Allows users to:
    - Select specific standards to include all their rules
    - Select individual rules from any standard
    - Apply custom filters and periods to rules
    - Filter rules by building type and room type
    - Generate analysis-ready configuration
    """

    def __init__(self, config_base_path: Optional[Path] = None, building_type: Optional[str] = None):
        """
        Initialize the config builder.

        Args:
            config_base_path: Path to config directory
            building_type: Building type for filtering rules (office, school, residential, etc.)
        """
        self.loader = IEQConfigLoader(config_base_path)
        self.selected_rules: Dict[str, Dict[str, Any]] = {}
        self.building_type = building_type

        # Load available options
        self._load_available_options()

    def _load_available_options(self):
        """Load all available standards, rules, filters, and periods."""
        # Load all configuration
        all_config = self.loader.load_all()

        # Parse available rules by standard
        self.available_standards = self.loader.get_available_standards()
        self.rules_by_standard: Dict[str, List[RuleDefinition]] = {}

        standards_path = self.loader.config_base_path / "standards"
        for standard in self.available_standards:
            rules = []
            standard_path = standards_path / standard

            for rule_file in standard_path.glob("*.yaml"):
                rule_name = rule_file.stem
                with open(rule_file, 'r') as f:
                    rule_config = yaml.safe_load(f)

                rules.append(RuleDefinition(
                    name=rule_name,
                    standard=standard,
                    description=rule_config.get('description', rule_name),
                    feature=rule_config.get('feature', 'unknown'),
                    config=rule_config
                ))

            self.rules_by_standard[standard] = rules

        # Parse available filters
        self.available_filters: List[FilterDefinition] = []
        filters_path = self.loader.config_base_path / "filters"

        if filters_path.exists():
            for filter_file in filters_path.glob("*.yaml"):
                filter_name = filter_file.stem
                with open(filter_file, 'r') as f:
                    filter_config = yaml.safe_load(f)

                self.available_filters.append(FilterDefinition(
                    name=filter_name,
                    description=filter_config.get('description', filter_name),
                    config=filter_config
                ))

        # Parse available periods
        self.available_periods: List[PeriodDefinition] = []
        periods_path = self.loader.config_base_path / "periods"

        if periods_path.exists():
            for period_file in periods_path.glob("*.yaml"):
                period_name = period_file.stem
                with open(period_file, 'r') as f:
                    period_config = yaml.safe_load(f)

                self.available_periods.append(PeriodDefinition(
                    name=period_name,
                    description=period_config.get('description', period_name),
                    config=period_config
                ))

    def get_available_standards(self) -> List[str]:
        """Get list of available standards."""
        return self.available_standards

    def get_rules_for_standard(self, standard: str) -> List[RuleDefinition]:
        """Get all rules for a specific standard."""
        return self.rules_by_standard.get(standard, [])

    def get_all_rules(self) -> List[RuleDefinition]:
        """Get all available rules across all standards."""
        all_rules = []
        for rules in self.rules_by_standard.values():
            all_rules.extend(rules)
        return all_rules

    def get_available_filters(self) -> List[FilterDefinition]:
        """Get all available filters."""
        return self.available_filters

    def get_available_periods(self) -> List[PeriodDefinition]:
        """Get all available periods."""
        return self.available_periods

    def add_standard(self, standard: str) -> 'IEQConfigBuilder':
        """
        Add all rules from a standard, filtered by building type if set.

        Args:
            standard: Name of the standard (e.g., 'en16798-1')

        Returns:
            Self for chaining
        """
        rules = self.get_rules_for_standard(standard)
        for rule in rules:
            # Filter by building type if specified
            if self.building_type and not self._rule_applies_to_building(rule.config):
                continue

            self.selected_rules[rule.name] = rule.config.copy()

        return self

    def _rule_applies_to_building(self, rule_config: Dict[str, Any]) -> bool:
        """
        Check if a rule applies to the current building type.

        Args:
            rule_config: Rule configuration dictionary

        Returns:
            True if rule applies to building type
        """
        if not self.building_type:
            return True  # No building type filter

        building_types = rule_config.get('building_types', [])

        # Empty list means applies to all building types
        if not building_types:
            return True

        # Check if current building type is in the list
        return self.building_type in building_types

    @staticmethod
    def rule_applies_to_room(rule_config: Dict[str, Any], room_type: str) -> bool:
        """
        Check if a rule applies to a specific room type.

        Args:
            rule_config: Rule configuration dictionary
            room_type: Room type to check (e.g., 'office', 'classroom')

        Returns:
            True if rule applies to room type
        """
        room_types = rule_config.get('room_types', [])

        # Empty list means applies to all room types
        if not room_types:
            return True

        # Check if room type is in the list
        return room_type in room_types

    def add_rule(self, rule_name: str, standard: Optional[str] = None) -> 'IEQConfigBuilder':
        """
        Add a specific rule by name.

        Args:
            rule_name: Name of the rule
            standard: Optional standard to search in (searches all if not provided)

        Returns:
            Self for chaining
        """
        # Find the rule
        if standard:
            rules = self.get_rules_for_standard(standard)
        else:
            rules = self.get_all_rules()

        for rule in rules:
            if rule.name == rule_name:
                self.selected_rules[rule_name] = rule.config.copy()
                break

        return self

    def apply_filter_to_rule(self, rule_name: str, filter_name: str) -> 'IEQConfigBuilder':
        """
        Override the filter for a specific rule.

        Args:
            rule_name: Name of the rule to modify
            filter_name: Name of the filter to apply

        Returns:
            Self for chaining
        """
        if rule_name in self.selected_rules:
            self.selected_rules[rule_name]['filter'] = filter_name

        return self

    def apply_period_to_rule(self, rule_name: str, period_name: str) -> 'IEQConfigBuilder':
        """
        Override the period for a specific rule.

        Args:
            rule_name: Name of the rule to modify
            period_name: Name of the period to apply

        Returns:
            Self for chaining
        """
        if rule_name in self.selected_rules:
            self.selected_rules[rule_name]['period'] = period_name

        return self

    def apply_filter_to_all(self, filter_name: str) -> 'IEQConfigBuilder':
        """
        Apply a filter to all selected rules.

        Args:
            filter_name: Name of the filter to apply

        Returns:
            Self for chaining
        """
        for rule_config in self.selected_rules.values():
            rule_config['filter'] = filter_name

        return self

    def apply_period_to_all(self, period_name: str) -> 'IEQConfigBuilder':
        """
        Apply a period to all selected rules.

        Args:
            period_name: Name of the period to apply

        Returns:
            Self for chaining
        """
        for rule_config in self.selected_rules.values():
            rule_config['period'] = period_name

        return self

    def clear_rules(self) -> 'IEQConfigBuilder':
        """Clear all selected rules."""
        self.selected_rules.clear()
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build the final configuration dictionary.

        Returns:
            Complete configuration ready for HierarchicalAnalysisService
        """
        # Load filters and periods
        filters = self.loader.load_filters()
        periods = self.loader.load_periods()
        holidays = self.loader.load_holidays()

        return {
            'analytics': self.selected_rules.copy(),
            'filters': filters,
            'periods': periods,
            'holidays': holidays
        }

    def save_to_file(self, output_path: Path) -> None:
        """
        Save the built configuration to a YAML file.

        Args:
            output_path: Path to save the configuration
        """
        config = self.build()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def get_summary(self) -> str:
        """Get a summary of the current configuration."""
        lines = []
        lines.append(f"Selected Rules: {len(self.selected_rules)}")

        # Group by standard
        by_standard: Dict[str, List[str]] = {}
        for rule_name in self.selected_rules.keys():
            # Find which standard this rule belongs to
            for standard, rules in self.rules_by_standard.items():
                if any(r.name == rule_name for r in rules):
                    if standard not in by_standard:
                        by_standard[standard] = []
                    by_standard[standard].append(rule_name)
                    break

        for standard, rules in by_standard.items():
            lines.append(f"  {standard}: {len(rules)} rules")

        return "\n".join(lines)
