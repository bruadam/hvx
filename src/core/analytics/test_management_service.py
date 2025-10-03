"""
Test Management Service for creating, editing, and managing test configurations.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class TestDefinition:
    """Represents a single test definition."""
    name: str
    description: str
    feature: str
    period: str
    filter: str
    mode: str
    limit: Optional[float] = None
    limits: Optional[Dict[str, float]] = None
    json_logic: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for YAML export."""
        result: Dict[str, Any] = {
            'description': self.description,
            'feature': self.feature,
            'period': self.period,
            'filter': self.filter,
            'mode': self.mode
        }

        if self.limit is not None:
            result['limit'] = self.limit
        if self.limits:
            result['limits'] = self.limits
        if self.json_logic:
            result['json_logic'] = self.json_logic

        return result

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'TestDefinition':
        """Create from dictionary."""
        return cls(
            name=name,
            description=data.get('description', ''),
            feature=data.get('feature', ''),
            period=data.get('period', 'all_year'),
            filter=data.get('filter', 'opening_hours'),
            mode=data.get('mode', 'unidirectional_ascending'),
            limit=data.get('limit'),
            limits=data.get('limits'),
            json_logic=data.get('json_logic')
        )


@dataclass
class FilterDefinition:
    """Represents a filter definition."""
    name: str
    description: Optional[str] = None
    hours: List[int] = field(default_factory=list)
    weekdays_only: bool = True
    exclude_holidays: bool = False
    exclude_custom_holidays: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for YAML export."""
        result = {
            'hours': self.hours,
            'weekdays_only': self.weekdays_only,
            'exclude_holidays': self.exclude_holidays
        }

        if self.description:
            result['description'] = self.description
        if self.exclude_custom_holidays:
            result['exclude_custom_holidays'] = self.exclude_custom_holidays

        return result

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'FilterDefinition':
        """Create from dictionary."""
        return cls(
            name=name,
            description=data.get('description'),
            hours=data.get('hours', []),
            weekdays_only=data.get('weekdays_only', True),
            exclude_holidays=data.get('exclude_holidays', False),
            exclude_custom_holidays=data.get('exclude_custom_holidays', False)
        )


@dataclass
class TestSet:
    """A named collection of tests for specific analysis."""
    name: str
    description: str
    test_names: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'description': self.description,
            'tests': self.test_names
        }

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'TestSet':
        """Create from dictionary."""
        return cls(
            name=name,
            description=data.get('description', ''),
            test_names=data.get('tests', [])
        )


class TestManagementService:
    """Service for managing test configurations."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the test management service.
        
        Args:
            config_path: Path to the tests configuration file (uses package config if None)
        """
        from src.core.analytics.config_loader import get_tests_config_path
        if config_path is None:
            config_path = get_tests_config_path()
        """Initialize with config file path."""
        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f) or {}
        else:
            self.config_data = {
                'analytics': {},
                'periods': {},
                'filters': {},
                'test_sets': {}
            }

    def save_config(self, path: Optional[Path] = None) -> None:
        """Save configuration to YAML file."""
        save_path = path or self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config_data, f, default_flow_style=False,
                     allow_unicode=True, sort_keys=False)

    # Test Management

    def get_test(self, test_name: str) -> Optional[TestDefinition]:
        """Get a specific test definition."""
        analytics = self.config_data.get('analytics', {})
        if test_name in analytics:
            return TestDefinition.from_dict(test_name, analytics[test_name])
        return None

    def list_tests(self) -> List[TestDefinition]:
        """List all available tests."""
        analytics = self.config_data.get('analytics', {})
        return [TestDefinition.from_dict(name, data)
                for name, data in analytics.items()]

    def add_test(self, test: TestDefinition, overwrite: bool = False) -> bool:
        """Add a new test definition."""
        if 'analytics' not in self.config_data:
            self.config_data['analytics'] = {}

        if test.name in self.config_data['analytics'] and not overwrite:
            return False

        self.config_data['analytics'][test.name] = test.to_dict()
        return True

    def update_test(self, test_name: str, test: TestDefinition) -> bool:
        """Update an existing test."""
        if 'analytics' not in self.config_data:
            return False

        if test_name not in self.config_data['analytics']:
            return False

        # Remove old entry if name changed
        if test_name != test.name:
            del self.config_data['analytics'][test_name]

        self.config_data['analytics'][test.name] = test.to_dict()
        return True

    def delete_test(self, test_name: str) -> bool:
        """Delete a test definition."""
        if 'analytics' in self.config_data and test_name in self.config_data['analytics']:
            del self.config_data['analytics'][test_name]
            return True
        return False

    def copy_test(self, source_name: str, new_name: str,
                  modifications: Optional[Dict[str, Any]] = None) -> Optional[TestDefinition]:
        """Copy a test with optional modifications."""
        source = self.get_test(source_name)
        if not source:
            return None

        # Create a copy
        test_dict = source.to_dict()
        if modifications:
            test_dict.update(modifications)

        new_test = TestDefinition.from_dict(new_name, test_dict)
        self.add_test(new_test, overwrite=False)
        return new_test

    # Filter Management

    def get_filter(self, filter_name: str) -> Optional[FilterDefinition]:
        """Get a specific filter definition."""
        filters = self.config_data.get('filters', {})
        if filter_name in filters:
            return FilterDefinition.from_dict(filter_name, filters[filter_name])
        return None

    def list_filters(self) -> List[FilterDefinition]:
        """List all available filters."""
        filters = self.config_data.get('filters', {})
        return [FilterDefinition.from_dict(name, data)
                for name, data in filters.items()]

    def add_filter(self, filter_def: FilterDefinition, overwrite: bool = False) -> bool:
        """Add a new filter definition."""
        if 'filters' not in self.config_data:
            self.config_data['filters'] = {}

        if filter_def.name in self.config_data['filters'] and not overwrite:
            return False

        self.config_data['filters'][filter_def.name] = filter_def.to_dict()
        return True

    def update_filter(self, filter_name: str, filter_def: FilterDefinition) -> bool:
        """Update an existing filter."""
        if 'filters' not in self.config_data:
            return False

        if filter_name not in self.config_data['filters']:
            return False

        # Remove old entry if name changed
        if filter_name != filter_def.name:
            del self.config_data['filters'][filter_name]

        self.config_data['filters'][filter_def.name] = filter_def.to_dict()
        return True

    def delete_filter(self, filter_name: str) -> bool:
        """Delete a filter definition."""
        if 'filters' in self.config_data and filter_name in self.config_data['filters']:
            del self.config_data['filters'][filter_name]
            return True
        return False

    # Test Set Management

    def get_test_set(self, set_name: str) -> Optional[TestSet]:
        """Get a specific test set."""
        test_sets = self.config_data.get('test_sets', {})
        if set_name in test_sets:
            return TestSet.from_dict(set_name, test_sets[set_name])
        return None

    def list_test_sets(self) -> List[TestSet]:
        """List all test sets."""
        test_sets = self.config_data.get('test_sets', {})
        return [TestSet.from_dict(name, data)
                for name, data in test_sets.items()]

    def add_test_set(self, test_set: TestSet, overwrite: bool = False) -> bool:
        """Add a new test set."""
        if 'test_sets' not in self.config_data:
            self.config_data['test_sets'] = {}

        if test_set.name in self.config_data['test_sets'] and not overwrite:
            return False

        self.config_data['test_sets'][test_set.name] = test_set.to_dict()
        return True

    def update_test_set(self, set_name: str, test_set: TestSet) -> bool:
        """Update an existing test set."""
        if 'test_sets' not in self.config_data:
            return False

        if set_name not in self.config_data['test_sets']:
            return False

        if set_name != test_set.name:
            del self.config_data['test_sets'][set_name]

        self.config_data['test_sets'][test_set.name] = test_set.to_dict()
        return True

    def delete_test_set(self, set_name: str) -> bool:
        """Delete a test set."""
        if 'test_sets' in self.config_data and set_name in self.config_data['test_sets']:
            del self.config_data['test_sets'][set_name]
            return True
        return False

    # Utility methods

    def get_periods(self) -> Dict[str, Any]:
        """Get all period definitions."""
        return self.config_data.get('periods', {})

    def export_test_set_config(self, set_name: str, output_path: Path) -> bool:
        """Export a specific test set as a standalone config file."""
        test_set = self.get_test_set(set_name)
        if not test_set:
            return False

        # Build new config with only the tests in the set
        export_config = {
            'analytics': {},
            'periods': self.config_data.get('periods', {}),
            'filters': self.config_data.get('filters', {}),
            'holidays': self.config_data.get('holidays', {})
        }

        for test_name in test_set.test_names:
            test = self.get_test(test_name)
            if test:
                export_config['analytics'][test_name] = test.to_dict()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(export_config, f, default_flow_style=False,
                     allow_unicode=True, sort_keys=False)

        return True

    def search_tests(self, feature: Optional[str] = None,
                    period: Optional[str] = None,
                    filter_name: Optional[str] = None) -> List[TestDefinition]:
        """Search tests by criteria."""
        tests = self.list_tests()

        if feature:
            tests = [t for t in tests if t.feature == feature]
        if period:
            tests = [t for t in tests if t.period == period]
        if filter_name:
            tests = [t for t in tests if t.filter == filter_name]

        return tests
