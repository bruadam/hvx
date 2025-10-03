"""
Test script for IEQ configuration loader
"""

from src.core.utils.config_loader import load_ieq_config, load_ieq_standard, get_ieq_config_base_path
from src.core.analysis.ieq.config_loader import IEQConfigLoader
import json


def test_config_loader():
    """Test the IEQ configuration loader."""

    print("=" * 80)
    print("Testing IEQ Configuration Loader")
    print("=" * 80)

    # Test 1: Get config base path
    print("\n1. Testing get_ieq_config_base_path()...")
    try:
        config_path = get_ieq_config_base_path()
        print(f"   ✓ Config base path: {config_path}")
        print(f"   ✓ Path exists: {config_path.exists()}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # Test 2: Create loader instance
    print("\n2. Testing IEQConfigLoader instantiation...")
    try:
        loader = IEQConfigLoader(config_path)
        print(f"   ✓ Loader created successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # Test 3: Get available standards
    print("\n3. Testing get_available_standards()...")
    try:
        standards = loader.get_available_standards()
        print(f"   ✓ Available standards: {standards}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 4: Load periods
    print("\n4. Testing load_periods()...")
    try:
        periods = loader.load_periods()
        print(f"   ✓ Loaded {len(periods)} periods:")
        for period_name in periods.keys():
            print(f"      - {period_name}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 5: Load filters
    print("\n5. Testing load_filters()...")
    try:
        filters = loader.load_filters()
        print(f"   ✓ Loaded {len(filters)} filters:")
        for filter_name in filters.keys():
            print(f"      - {filter_name}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 6: Load holidays
    print("\n6. Testing load_holidays()...")
    try:
        holidays = loader.load_holidays()
        print(f"   ✓ Loaded holidays: {holidays.get('country', 'N/A')}")
        if 'custom_holidays' in holidays:
            print(f"   ✓ Custom holidays: {len(holidays['custom_holidays'])} entries")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 7: Load analytics (all standards)
    print("\n7. Testing load_analytics()...")
    try:
        analytics = loader.load_analytics()
        print(f"   ✓ Loaded {len(analytics)} analytics rules:")

        # Group by standard
        by_standard = {}
        for rule_name, rule_config in analytics.items():
            category = rule_config.get('category') or rule_config.get('regulation') or 'unknown'
            if category not in by_standard:
                by_standard[category] = []
            by_standard[category].append(rule_name)

        for standard, rules in by_standard.items():
            print(f"      {standard}: {len(rules)} rules")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 8: Load specific standard
    print("\n8. Testing load_standard('en16798-1')...")
    try:
        en16798_rules = loader.load_standard('en16798-1')
        print(f"   ✓ Loaded {len(en16798_rules)} EN16798-1 rules:")
        for rule_name in list(en16798_rules.keys())[:5]:  # Show first 5
            print(f"      - {rule_name}")
        if len(en16798_rules) > 5:
            print(f"      ... and {len(en16798_rules) - 5} more")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 9: Load all config using convenience function
    print("\n9. Testing load_ieq_config() convenience function...")
    try:
        full_config = load_ieq_config()
        print(f"   ✓ Loaded full config with keys: {list(full_config.keys())}")
        print(f"      - analytics: {len(full_config.get('analytics', {}))} rules")
        print(f"      - periods: {len(full_config.get('periods', {}))} periods")
        print(f"      - filters: {len(full_config.get('filters', {}))} filters")
        print(f"      - holidays: {'✓' if full_config.get('holidays') else '✗'}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 10: Load specific standard using convenience function
    print("\n10. Testing load_ieq_standard() convenience function...")
    try:
        br18_rules = load_ieq_standard('br18')
        print(f"   ✓ Loaded {len(br18_rules)} BR18 rules:")
        for rule_name in br18_rules.keys():
            print(f"      - {rule_name}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 11: Check a sample rule structure
    print("\n11. Testing sample rule structure...")
    try:
        if analytics:
            sample_rule_name = list(analytics.keys())[0]
            sample_rule = analytics[sample_rule_name]
            print(f"   ✓ Sample rule '{sample_rule_name}':")
            print(f"      {json.dumps(sample_rule, indent=6)}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "=" * 80)
    print("Testing Complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_config_loader()
