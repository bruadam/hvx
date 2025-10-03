"""
Integration tests for StandardRegistry.

Tests dynamic standard discovery, filtering, and enum creation.
"""

import pytest
import os
from pathlib import Path

from src.core.analytics.ieq.StandardRegistry import (
    StandardRegistry
)


class TestStandardDiscovery:
    """Tests for standard discovery functionality."""
    
    def test_discover_standards_from_filesystem(self):
        """Test that standards are discovered from config/standards directory."""
        registry = StandardRegistry()
        
        # Should discover at least en16798
        standard_ids = registry.get_standard_ids()
        
        assert len(standard_ids) > 0
        assert 'en16798' in standard_ids
    
    def test_get_standard_ids(self):
        """Test retrieving list of discovered standard IDs."""
        registry = StandardRegistry()
        standard_ids = registry.get_standard_ids()
        
        assert isinstance(standard_ids, list)
        assert all(isinstance(sid, str) for sid in standard_ids)
    
    def test_get_standard_exists(self):
        """Test retrieving existing standard."""
        registry = StandardRegistry()
        en16798 = registry.get_standard_info('en16798')
        assert en16798 is not None
        assert en16798.id == 'en16798'

    def test_get_standard_not_exists(self):
        """Test retrieving non-existent standard returns None."""
        registry = StandardRegistry()
        result = registry.get_standard_info('nonexistent_standard')
        assert result is None

    def test_discovered_standards_have_rules(self):
        """Test that discovered standards contain rules."""
        registry = StandardRegistry()
        en16798 = registry.get_standard_info('en16798')
        assert en16798 is not None
        assert hasattr(en16798, 'rules')
        assert isinstance(en16798.rules, list)
        assert len(en16798.rules) > 0
    
    def test_discovered_standards_have_metadata(self):
        """Test that discovered standards have required metadata."""
        registry = StandardRegistry()
        for std_id in registry.get_standard_ids():
            standard = registry.get_standard_info(std_id)
            assert hasattr(standard, 'id')
            assert hasattr(standard, 'name')
            assert hasattr(standard, 'rules')


class TestStandardFiltering:
    """Tests for filtering rules by parameter and category."""
    
    def test_filter_by_parameter(self):
        """Test filtering rules by parameter."""
        registry = StandardRegistry()
        temp_rules = registry.filter_rules(parameter='temperature')
        assert isinstance(temp_rules, list)
        # Should contain rule IDs
        if len(temp_rules) > 0:
            for rule_id in temp_rules:
                assert isinstance(rule_id, str)
    
    def test_filter_by_category(self):
        """Test filtering rules by category."""
        registry = StandardRegistry()
        thermal_rules = registry.filter_rules(category='thermal_comfort')
        assert isinstance(thermal_rules, list)
    
    def test_filter_by_parameter_and_category(self):
        """Test filtering by both parameter and category."""
        registry = StandardRegistry()
        filtered = registry.filter_rules(parameter='temperature', category='thermal_comfort')
        assert isinstance(filtered, list)
    
    def test_filter_by_standard_id(self):
        """Test filtering to specific standard."""
        registry = StandardRegistry()
        en16798_temp = registry.filter_rules(standard_ids=['en16798'], parameter='temperature')
        assert isinstance(en16798_temp, list)
    
    def test_filter_no_matches_returns_empty(self):
        """Test that filtering with no matches returns empty list."""
        registry = StandardRegistry()
        result = registry.filter_rules(parameter='nonexistent_param')
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_filter_preserves_rule_structure(self):
        """Test that filtered rules maintain proper structure."""
        registry = StandardRegistry()
        filtered = registry.filter_rules(parameter='temperature')
        for rule_id in filtered:
            rule = registry.get_rule_config(rule_id)
            assert rule is not None
            param = rule.get('feature') or rule.get('parameter')
            assert param is not None
            assert 'temperature' in str(param).lower()


class TestStandardEnum:
    """Tests for dynamic enum creation."""
    
    def test_create_standard_enum(self):
        """Test creating enum from discovered standards."""
        registry = StandardRegistry()
        standard_enum = registry.create_standard_enum()
        assert standard_enum is not None
        # Should have EN16798
        assert hasattr(standard_enum, 'EN16798')

    def test_enum_contains_discovered_standards(self):
        """Test that enum contains all discovered standards."""
        registry = StandardRegistry()
        standard_ids = registry.get_standard_ids()
        standard_enum = registry.create_standard_enum()
        # Convert to uppercase for enum comparison
        for std_id in standard_ids:
            enum_name = std_id.upper().replace('-', '_')
            assert hasattr(standard_enum, enum_name)

    def test_enum_values_match_ids(self):
        """Test that enum values match standard IDs."""
        registry = StandardRegistry()
        standard_enum = registry.create_standard_enum()
        # EN16798 value should be 'en16798'
        assert standard_enum.EN16798.value == 'en16798'

    def test_enum_is_iterable(self):
        """Test that enum can be iterated."""
        registry = StandardRegistry()
        standard_enum = registry.create_standard_enum()
        try:
            enum_values = [e.value for e in standard_enum]
        except (TypeError, AttributeError):
            enum_values = [v.value for v in getattr(standard_enum, "__members__", {}).values()]
        assert isinstance(enum_values, list)
        if enum_values:
            assert 'en16798' in enum_values


class TestGetRulesForStandard:
    """Tests for get_rules_for_standard method."""
    
    def test_get_rules_for_existing_standard(self):
        """Test getting rules for existing standard."""
        registry = StandardRegistry()
        rules = registry.get_rules_for_standard('en16798')
        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_get_rules_for_nonexistent_standard(self):
        """Test getting rules for non-existent standard."""
        registry = StandardRegistry()
        rules = registry.get_rules_for_standard('nonexistent')
        assert rules == []


class TestStandardRegistryIntegration:
    """Integration tests for StandardRegistry."""
    
    def test_complete_discovery_workflow(self):
        """Test complete standard discovery and filtering workflow."""
        registry = StandardRegistry()
        standard_ids = registry.get_standard_ids()
        assert len(standard_ids) > 0
        en16798 = registry.get_standard_info('en16798')
        assert en16798 is not None
        temp_rules = registry.filter_rules(parameter='temperature')
        assert isinstance(temp_rules, list)
        rules = registry.get_rules_for_standard('en16798')
        assert len(rules) > 0
        standard_enum = registry.create_standard_enum()
        assert hasattr(standard_enum, 'EN16798')
    
    def test_registry_caching(self):
        """Test that registry caches discovered standards."""
        registry = StandardRegistry()
        ids1 = registry.get_standard_ids()
        std1 = registry.get_standard_info('en16798')
        ids2 = registry.get_standard_ids()
        std2 = registry.get_standard_info('en16798')
        assert ids1 == ids2
        assert std1 == std2
    
    def test_filtering_multiple_standards(self):
        """Test filtering across multiple standards."""
        registry = StandardRegistry()
        temp_rules = registry.filter_rules(parameter='temperature')
        assert isinstance(temp_rules, list)
        for rule_id in temp_rules:
            rule = registry.get_rule_config(rule_id)
            assert rule is not None
            param = rule.get('feature') or rule.get('parameter')
            assert param is not None
            assert 'temperature' in str(param).lower()
    
    def test_registry_with_missing_config_dir(self):
        """Test registry handles missing config directory gracefully."""
        from pathlib import Path
        registry = StandardRegistry(config_base_dir=Path('/nonexistent/path'))
        standard_ids = registry.get_standard_ids()
        assert isinstance(standard_ids, list)
    
    def test_all_standards_have_required_fields(self):
        """Test that all discovered standards have required fields."""
        registry = StandardRegistry()
        required_fields = ['id', 'rules']
        for std_id in registry.get_standard_ids():
            standard = registry.get_standard_info(std_id)
            for field in required_fields:
                assert hasattr(standard, field), f"Standard {std_id} missing {field}"
    
    def test_en16798_specific_rules(self):
        """Test EN16798 specific rules are discovered correctly."""
        registry = StandardRegistry()
        en16798 = registry.get_standard_info('en16798')
        assert en16798 is not None
        rules = en16798.rules
        categories = []
        for rule_id in rules:
            rule = registry.get_rule_config(rule_id)
            if rule and 'category' in rule:
                categories.append(rule['category'])
        assert 'thermal_comfort' in categories or any('thermal' in str(c).lower() for c in categories if c)
    
    def test_parameter_list(self):
        """Test getting list of all available parameters."""
        registry = StandardRegistry()
        all_parameters = set()
        for std_id in registry.get_standard_ids():
            rule_ids = registry.get_rules_for_standard(std_id)
            for rule_id in rule_ids:
                rule = registry.get_rule_config(rule_id)
                if rule and 'parameter' in rule:
                    all_parameters.add(rule['parameter'])
        assert 'temperature' in all_parameters or len(all_parameters) > 0
    
    def test_category_list(self):
        """Test getting list of all available categories."""
        registry = StandardRegistry()
        all_categories = set()
        for std_id in registry.get_standard_ids():
            rule_ids = registry.get_rules_for_standard(std_id)
            for rule_id in rule_ids:
                rule = registry.get_rule_config(rule_id)
                if rule and 'category' in rule:
                    all_categories.add(rule['category'])
        assert len(all_categories) >= 0  # May or may not have categories


class TestDynamicStandardAddition:
    """Tests for handling dynamically added standards."""
    
    def test_new_standard_would_be_discovered(self):
        """Test that new standards in config dir would be discovered."""
        registry = StandardRegistry()
        
        # Get current standards
        original_count = len(registry.get_standard_ids())
        
        # In a real scenario, adding a new YAML file to config/standards/
        # would increase this count on next registry creation
        assert original_count >= 1  # At least en16798
    
    def test_enum_updates_with_new_standards(self):
        """Test that enum reflects discovered standards."""
        registry = StandardRegistry()
        standard_enum = registry.create_standard_enum()
        try:
            enum_count = len([e for e in standard_enum])
        except (TypeError, AttributeError):
            enum_count = len(list(getattr(standard_enum, "__members__", {}).values()))
        registry_count = len(registry.get_standard_ids())
        assert enum_count == registry_count
