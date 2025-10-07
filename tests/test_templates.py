"""
Test Different Report Templates

This script tests various report template configurations to ensure
the room-by-room reporting works with different settings.
"""

import json
from pathlib import Path
from src.core.reporting.HTMLReportRenderer import HTMLReportRenderer

def test_template(template_name, analysis_file, output_name, description):
    """Test a single template configuration."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Template: {template_name}")
    print(f"{'='*60}")
    
    try:
        html_renderer = HTMLReportRenderer()
        
        # Load analysis to show basic info
        if isinstance(analysis_file, (str, Path)):
            with open(analysis_file, 'r') as f:
                analysis_data = json.load(f)
        else:
            analysis_data = analysis_file
        
        print(f"Building: {analysis_data.get('building_name', 'Unknown')}")
        print(f"Rooms: {analysis_data.get('room_count', 0)}")
        print(f"Avg Compliance: {analysis_data.get('avg_compliance_rate', 0):.1f}%")
        
        # Generate report (handle both old and new template formats)
        try:
            result = html_renderer.render_report(
                config_path=Path(f"config/report_templates/{template_name}.yaml"),
                analysis_results=analysis_data,
                output_filename=output_name
            )
        except Exception as template_error:
            print(f"  Template error: {template_error}")
            print(f"  This template may use an older format or missing required sections")
            return False
        
        # Check output
        output_path = Path("output/reports") / output_name
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"\n✓ Report generated successfully")
            print(f"  File: {output_path}")
            print(f"  Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            # Count room cards and charts
            content = output_path.read_text()
            room_cards = content.count('room-card')
            room_table_rows = content.count('<tr>') - content.count('<thead>')  # Exclude header rows
            charts = content.count('data:image/png;base64,')
            weather_sections = content.count('weather-correlations')
            sections = content.count('class="section"')
            
            print(f"\n📊 Content Summary:")
            print(f"  Sections: {sections}")
            print(f"  Room cards: {room_cards}")
            print(f"  Room table rows: {max(0, room_table_rows)}")
            print(f"  Charts embedded: {charts}")
            print(f"  Weather correlation sections: {weather_sections}")
            
            # Check for errors in the HTML
            if 'error' in content.lower() or 'exception' in content.lower():
                print(f"  ⚠️ Possible errors found in output")
            
            return True
        else:
            print(f"\n✗ Report file not found: {output_path}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run template tests."""
    print("=" * 60)
    print("REPORT TEMPLATE TESTING")
    print("=" * 60)
    
    # Find available analysis files
    analysis_dir = Path("output/analysis/buildings")
    analysis_files = list(analysis_dir.glob("*.json"))
    
    if not analysis_files:
        print("\n✗ No analysis files found in output/analysis/buildings/")
        return
    
    print(f"\nFound {len(analysis_files)} building analysis file(s)")
    
    # Use first available analysis file
    analysis_file = analysis_files[0]
    print(f"Using: {analysis_file}")
    
    # Test configurations
    tests = []
    results = {}
    
    # Test 1: Building Detailed (with detailed room cards)
    tests.append({
        'template': 'building_detailed',
        'output': 'test_detailed_cards.html',
        'description': 'Building Detailed Report (Cards View)'
    })
    
    # Test 2: Standard Building (if exists)
    if Path("config/report_templates/standard_building.yaml").exists():
        tests.append({
            'template': 'standard_building',
            'output': 'test_standard_building.html',
            'description': 'Standard Building Report'
        })
    
    # Test 3: Portfolio Summary (if exists)
    if Path("config/report_templates/portfolio_summary.yaml").exists():
        # Use portfolio analysis if available
        portfolio_file = Path("output/analysis/portfolio_analysis.json")
        if portfolio_file.exists():
            tests.append({
                'template': 'portfolio_summary',
                'output': 'test_portfolio_summary.html',
                'description': 'Portfolio Summary Report',
                'analysis_file': portfolio_file
            })
    
    # Run tests
    for test_config in tests:
        test_file = test_config.get('analysis_file', analysis_file)
        success = test_template(
            test_config['template'],
            test_file,
            test_config['output'],
            test_config['description']
        )
        results[test_config['description']] = success
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All template tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")

if __name__ == "__main__":
    main()
