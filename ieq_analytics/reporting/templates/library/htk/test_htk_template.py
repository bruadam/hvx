#!/usr/bin/env python3
"""
Test script for HTK Report Template

This script tests the HTK template functionality with sample data.
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime
import sys
import os

# Add the analytics package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

def create_sample_analysis_data():
    """Create sample analysis data for testing."""
    
    sample_data = {
        "floeng-skole": {
            "building_name": "Floeng Skole",
            "rooms": {
                "Klasserum 1A": {
                    "test_results": {
                        "co2_1000_all_year_opening": {
                            "compliance_rate": 0.85,
                            "violations_count": 120,
                            "mean": 950
                        },
                        "temp_comfort_all_year_opening": {
                            "compliance_rate": 0.92,
                            "violations_count": 45,
                            "mean": 23.2
                        },
                        "co2_1000_spring_opening": {
                            "compliance_rate": 0.88,
                            "violations_count": 25,
                            "mean": 920
                        },
                        "temp_comfort_spring_opening": {
                            "compliance_rate": 0.95,
                            "violations_count": 8,
                            "mean": 22.1
                        }
                    },
                    "statistics": {
                        "co2": {"mean": 950, "std": 200, "min": 400, "max": 1800},
                        "temperature": {"mean": 23.2, "std": 1.5, "min": 18.5, "max": 28.1}
                    }
                },
                "Klasserum 1B": {
                    "test_results": {
                        "co2_1000_all_year_opening": {
                            "compliance_rate": 0.78,
                            "violations_count": 180,
                            "mean": 1050
                        },
                        "temp_comfort_all_year_opening": {
                            "compliance_rate": 0.88,
                            "violations_count": 65,
                            "mean": 24.1
                        }
                    },
                    "statistics": {
                        "co2": {"mean": 1050, "std": 250, "min": 450, "max": 2100},
                        "temperature": {"mean": 24.1, "std": 2.1, "min": 19.2, "max": 29.3}
                    }
                }
            },
            "data_quality": {
                "completeness": 98.5,
                "missing_periods": "2 days in March",
                "quality_score": "High"
            }
        },
        "ole-roemer-skolen": {
            "building_name": "Ole Rømer Skolen",
            "rooms": {
                "Fysiklokale": {
                    "test_results": {
                        "co2_1000_all_year_opening": {
                            "compliance_rate": 0.91,
                            "violations_count": 75,
                            "mean": 880
                        },
                        "temp_comfort_all_year_opening": {
                            "compliance_rate": 0.96,
                            "violations_count": 32,
                            "mean": 22.8
                        }
                    },
                    "statistics": {
                        "co2": {"mean": 880, "std": 180, "min": 420, "max": 1650},
                        "temperature": {"mean": 22.8, "std": 1.2, "min": 19.5, "max": 26.8}
                    }
                },
                "Bibliotek": {
                    "test_results": {
                        "co2_1000_all_year_opening": {
                            "compliance_rate": 0.94,
                            "violations_count": 45,
                            "mean": 820
                        },
                        "temp_comfort_all_year_opening": {
                            "compliance_rate": 0.98,
                            "violations_count": 15,
                            "mean": 22.1
                        }
                    },
                    "statistics": {
                        "co2": {"mean": 820, "std": 150, "min": 400, "max": 1450},
                        "temperature": {"mean": 22.1, "std": 0.9, "min": 20.1, "max": 25.2}
                    }
                }
            },
            "data_quality": {
                "completeness": 96.2,
                "missing_periods": "1 week in July",
                "quality_score": "High"
            }
        }
    }
    
    return sample_data

def test_htk_template():
    """Test the HTK template with sample data."""
    
    print("🧪 Testing HTK Report Template...")
    
    try:
        # Import the HTK template
        from ieq_analytics.reporting.templates.library.htk import create_htk_template
        
        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            data_dir = temp_path / "analysis"
            output_dir = temp_path / "output"
            
            data_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)
            
            # Create sample analysis data files
            sample_data = create_sample_analysis_data()
            
            for building_id, building_data in sample_data.items():
                analysis_file = data_dir / f"{building_id}_analysis.json"
                with open(analysis_file, 'w') as f:
                    json.dump(building_data, f, indent=2)
                print(f"  ✓ Created sample data: {analysis_file}")
            
            # Create HTK template instance
            htk_template = create_htk_template()
            print("  ✓ HTK template created successfully")
            
            # Test template info
            template_info = htk_template.get_template_info()
            print(f"  ✓ Template info: {template_info['name']}")
            
            # Generate the report
            print("  📊 Generating HTK report...")
            
            result = htk_template.generate_report(
                data_dir=data_dir,
                output_dir=output_dir,
                config_path=Path(__file__).parent / "tests.yaml",
                mapped_dir=data_dir,  # Provide appropriate mapped_dir
                climate_dir=data_dir,  # Provide appropriate climate_dir
                export_formats=["html"],  # Only HTML for testing
            )
            
            if result.get('success'):
                print("  ✅ HTK report generated successfully!")
                
                # Check generated files
                generated_files = result.get('files', {})
                for fmt, file_path in generated_files.items():
                    if Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size
                        print(f"    📄 {fmt.upper()}: {file_path} ({file_size} bytes)")
                    else:
                        print(f"    ❌ {fmt.upper()}: File not found at {file_path}")
                
                # Check charts
                charts_generated = result.get('charts_generated', 0)
                print(f"    📊 Charts generated: {charts_generated}")
                
                # Check buildings analyzed
                buildings_analyzed = result.get('buildings_analyzed', [])
                print(f"    🏗️ Buildings analyzed: {', '.join(buildings_analyzed)}")
                
                return True
            else:
                print("  ❌ HTK report generation failed")
                if 'error' in result:
                    print(f"    Error: {result['error']}")
                return False
                
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("    Make sure the HTK template is properly installed")
        return False
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        print(f"    {traceback.format_exc()}")
        return False

def test_chart_generation():
    """Test chart generation separately."""
    
    print("\n🎨 Testing Chart Generation...")
    
    try:
        from ieq_analytics.reporting.templates.library.htk.charts import HTKChartGenerator
        
        # Create temporary directory for charts
        with tempfile.TemporaryDirectory() as temp_dir:
            charts_dir = Path(temp_dir) / "charts"
            charts_dir.mkdir(parents=True)
            
            # Create chart generator
            chart_generator = HTKChartGenerator(charts_dir, config={})
            print("  ✓ Chart generator created")
            
            # Generate sample analysis data
            sample_data = create_sample_analysis_data()
            
            # Test individual chart generation
            charts_generated = chart_generator.generate_all_charts(sample_data)
            
            print(f"  ✓ Generated {len(charts_generated)} chart types")
            
            for chart_name, chart_path in charts_generated.items():
                if Path(chart_path).exists():
                    file_size = Path(chart_path).stat().st_size
                    print(f"    📊 {chart_name}: {file_size} bytes")
                else:
                    print(f"    ❌ {chart_name}: File not found")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Chart generation error: {e}")
        import traceback
        print(f"    {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🏢 HTK Report Template Test Suite")
    print("=" * 50)
    
    # Test chart generation
    chart_test_passed = test_chart_generation()
    
    # Test full template
    template_test_passed = test_htk_template()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"  Chart Generation: {'✅ PASSED' if chart_test_passed else '❌ FAILED'}")
    print(f"  Template Generation: {'✅ PASSED' if template_test_passed else '❌ FAILED'}")
    
    if chart_test_passed and template_test_passed:
        print("\n🎉 All tests passed! HTK template is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
