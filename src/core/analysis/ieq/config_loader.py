"""
IEQ Configuration Loader

Loads IEQ analytics configuration from the new modular structure:
- One file per rule/filter/period
- Standards organized in subfolders
- Automatically discovers and loads all configuration files
"""

from pathlib import Path
from typing import Dict, Any
import yaml


class IEQConfigLoader:
    """Loader for IEQ configuration files from modular structure."""

    def __init__(self, config_base_path: Path = None):
        """
        Initialize the config loader.

        Args:
            config_base_path: Base path to config directory. If None, uses package location.
        """
        if config_base_path is None:
            # Default to the config directory next to this file
            self.config_base_path = Path(__file__).parent / "config"
        else:
            self.config_base_path = Path(config_base_path)

    def load_all(self) -> Dict[str, Any]:
        """
        Load all configuration files and return a unified config structure.

        Returns:
            Dictionary with keys: analytics, periods, filters, holidays
        """
        config = {
            "analytics": self.load_analytics(),
            "periods": self.load_periods(),
            "filters": self.load_filters(),
            "holidays": self.load_holidays()
        }
        return config

    def load_analytics(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all analytics rules from standards folders.

        Returns:
            Dictionary mapping rule names to rule configurations
        """
        analytics = {}
        standards_path = self.config_base_path / "standards"

        if not standards_path.exists():
            return analytics

        # Iterate through all standard folders (en16798-1, br18, danish-guidelines, etc.)
        for standard_folder in standards_path.iterdir():
            if not standard_folder.is_dir():
                continue

            # Load all YAML files in this standard folder
            for rule_file in standard_folder.glob("*.yaml"):
                rule_name = rule_file.stem
                with open(rule_file, 'r') as f:
                    rule_config = yaml.safe_load(f)
                    # Use filename (without extension) as the rule key
                    analytics[rule_name] = rule_config

        return analytics

    def load_periods(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all period definitions.

        Returns:
            Dictionary mapping period names to period configurations
        """
        periods = {}
        periods_path = self.config_base_path / "periods"

        if not periods_path.exists():
            return periods

        for period_file in periods_path.glob("*.yaml"):
            period_name = period_file.stem
            with open(period_file, 'r') as f:
                period_config = yaml.safe_load(f)
                periods[period_name] = period_config

        return periods

    def load_filters(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all filter definitions.

        Returns:
            Dictionary mapping filter names to filter configurations
        """
        filters = {}
        filters_path = self.config_base_path / "filters"

        if not filters_path.exists():
            return filters

        for filter_file in filters_path.glob("*.yaml"):
            filter_name = filter_file.stem
            with open(filter_file, 'r') as f:
                filter_config = yaml.safe_load(f)
                filters[filter_name] = filter_config

        return filters

    def load_holidays(self) -> Dict[str, Any]:
        """
        Load holiday configuration.

        Returns:
            Holiday configuration (currently loads denmark.yaml by default)
        """
        holidays_path = self.config_base_path / "holidays" / "denmark.yaml"

        if not holidays_path.exists():
            return {}

        with open(holidays_path, 'r') as f:
            return yaml.safe_load(f)

    def load_standard(self, standard_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Load only rules from a specific standard.

        Args:
            standard_name: Name of the standard (e.g., 'en16798-1', 'br18')

        Returns:
            Dictionary mapping rule names to rule configurations for that standard
        """
        analytics = {}
        standard_path = self.config_base_path / "standards" / standard_name

        if not standard_path.exists():
            return analytics

        for rule_file in standard_path.glob("*.yaml"):
            rule_name = rule_file.stem
            with open(rule_file, 'r') as f:
                rule_config = yaml.safe_load(f)
                analytics[rule_name] = rule_config

        return analytics

    def get_available_standards(self) -> list:
        """
        Get list of available standards.

        Returns:
            List of standard names
        """
        standards_path = self.config_base_path / "standards"

        if not standards_path.exists():
            return []

        return [d.name for d in standards_path.iterdir() if d.is_dir()]

    def save_rule(self, rule_name: str, rule_config: Dict[str, Any], standard: str = "custom"):
        """
        Save a new rule or update an existing one.

        Args:
            rule_name: Name of the rule (will be the filename)
            rule_config: Rule configuration dictionary
            standard: Standard folder to save in (default: "custom")
        """
        standard_path = self.config_base_path / "standards" / standard
        standard_path.mkdir(parents=True, exist_ok=True)

        rule_file = standard_path / f"{rule_name}.yaml"
        with open(rule_file, 'w') as f:
            yaml.dump(rule_config, f, default_flow_style=False, sort_keys=False)

    def save_filter(self, filter_name: str, filter_config: Dict[str, Any]):
        """
        Save a new filter or update an existing one.

        Args:
            filter_name: Name of the filter (will be the filename)
            filter_config: Filter configuration dictionary
        """
        filters_path = self.config_base_path / "filters"
        filters_path.mkdir(parents=True, exist_ok=True)

        filter_file = filters_path / f"{filter_name}.yaml"
        with open(filter_file, 'w') as f:
            yaml.dump(filter_config, f, default_flow_style=False, sort_keys=False)

    def save_period(self, period_name: str, period_config: Dict[str, Any]):
        """
        Save a new period or update an existing one.

        Args:
            period_name: Name of the period (will be the filename)
            period_config: Period configuration dictionary
        """
        periods_path = self.config_base_path / "periods"
        periods_path.mkdir(parents=True, exist_ok=True)

        period_file = periods_path / f"{period_name}.yaml"
        with open(period_file, 'w') as f:
            yaml.dump(period_config, f, default_flow_style=False, sort_keys=False)


def load_ieq_config(config_base_path: Path = None) -> Dict[str, Any]:
    """
    Convenience function to load all IEQ configuration.

    Args:
        config_base_path: Base path to config directory. If None, uses package location.

    Returns:
        Complete configuration dictionary
    """
    loader = IEQConfigLoader(config_base_path)
    return loader.load_all()


def load_ieq_standard(standard_name: str, config_base_path: Path = None) -> Dict[str, Dict[str, Any]]:
    """
    Convenience function to load only a specific standard.

    Args:
        standard_name: Name of the standard (e.g., 'en16798-1', 'br18')
        config_base_path: Base path to config directory. If None, uses package location.

    Returns:
        Dictionary of rules for that standard
    """
    loader = IEQConfigLoader(config_base_path)
    return loader.load_standard(standard_name)
