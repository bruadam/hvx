#!/usr/bin/env python3
"""
Test script to verify HTK template improvements.

This script tests the new features added to the HTK template:
1. Relative image paths
2. Friendly names for buildings and rooms  
3. Separated CO2 compliance metrics
4. Room summaries with recommendations
5. Color coding in tables
6. Optimized KPI layout
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import ieq_analytics
sys.path.insert(0, str(Path(__file__).parent))

def test_friendly_names():
    """Test the friendly name mapping functionality."""
    print("🏗️ Testing friendly name mapping...")
    
    try:
        from ieq_analytics.reporting.templates.library.htk.htk_template import HTKReportTemplate
        
        # Create template instance
        template = HTKReportTemplate()
        
        # Test building name mappings
        test_cases = [
            ("floeng-skole", "Fløng Skole"),
            ("ole-roemer-skolen", "Ole Rømer-Skolen"), 
            ("reerslev", "Reerslev Skole"),
            ("Some_Random_Building", "Some Random Building"),
            ("klasserum_01", "Klasserum 01"),
        ]
        
        for original, expected in test_cases:
            result = template._get_friendly_name(original)
            if result == expected:
                print(f"  ✓ {original} → {result}")
            else:
                print(f"  ✗ {original} → {result} (expected: {expected})")
                
    except Exception as e:
        print(f"  ✗ Error testing friendly names: {e}")

def test_compliance_class():
    """Test the compliance class assignment."""
    print("🎨 Testing compliance class assignment...")
    
    try:
        from ieq_analytics.reporting.templates.library.htk.htk_template import HTKReportTemplate
        
        template = HTKReportTemplate()
        
        test_cases = [
            (95, "good"),
            (75, "warning"),
            (45, "danger"),
            (80, "good"),
            (60, "warning")
        ]
        
        for percentage, expected_class in test_cases:
            result = template._get_compliance_class(percentage)
            if result == expected_class:
                print(f"  ✓ {percentage}% → {result}")
            else:
                print(f"  ✗ {percentage}% → {result} (expected: {expected_class})")
                
    except Exception as e:
        print(f"  ✗ Error testing compliance classes: {e}")

def test_relative_paths():
    """Test the relative path conversion."""
    print("🔗 Testing relative path conversion...")
    
    try:
        from ieq_analytics.reporting.templates.library.htk.htk_template import HTKReportTemplate
        
        template = HTKReportTemplate()
        
        # Create sample absolute paths
        test_paths = {
            "chart1": "/path/to/output/charts/building_comparison.png",
            "chart2": "/another/path/charts/room_analysis.png",
            "empty": "",
            "nonexistent": "/does/not/exist.png"
        }
        
        result = template._convert_to_relative_paths(test_paths)
        
        # Check expected results
        expected = {
            "chart1": "./charts/building_comparison.png",
            "chart2": "./charts/room_analysis.png", 
            "empty": "",
            "nonexistent": ""
        }
        
        for key in expected:
            if result.get(key) == expected[key]:
                print(f"  ✓ {key}: {result.get(key)}")
            else:
                print(f"  ✗ {key}: {result.get(key)} (expected: {expected[key]})")
                
    except Exception as e:
        print(f"  ✗ Error testing relative paths: {e}")

def test_template_syntax():
    """Test that the template HTML syntax is valid."""
    print("📄 Testing template HTML syntax...")
    
    try:
        from ieq_analytics.reporting.templates.library.htk.htk_template import HTKReportTemplate
        
        template = HTKReportTemplate()
        
        # Load the template content
        html_content = template.load_html_template()
        
        # Basic syntax checks
        checks = [
            ("Opening tags balance", html_content.count("<div") == html_content.count("</div>")),
            ("No bare basename filters", "| basename" not in html_content),
            ("Contains friendly_name usage", "friendly_name or" in html_content),
            ("Contains CO2 separation", "co2_compliance_1000" in html_content),
            ("Contains room summary", "room-summary" in html_content),
        ]
        
        for check_name, passed in checks:
            if passed:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name}")
                
    except Exception as e:
        print(f"  ✗ Error testing template syntax: {e}")

def main():
    """Run all tests."""
    print("🧪 Testing HTK Template Improvements")
    print("=" * 50)
    
    test_friendly_names()
    print()
    
    test_compliance_class()
    print()
    
    test_relative_paths() 
    print()
    
    test_template_syntax()
    print()
    
    print("✅ Template improvement tests completed!")

if __name__ == "__main__":
    main()
