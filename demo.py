#!/usr/bin/env python3
"""
Example script demonstrating the IEQ Analytics system with rule-based analysis.

This script shows how to:
1. Create sample IEQ data
2. Perform comprehensive analytics
3. Use rule-based evaluation (if json-logic is available)
4. Export results
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Add the package to path for development
sys.path.insert(0, '.')

from ieq_analytics import IEQAnalytics, IEQData, Room, Building
from ieq_analytics.rule_builder import RuleBuilder, AnalyticsEngine
from ieq_analytics.enums import IEQParameter, ComfortCategory


def create_sample_data() -> pd.DataFrame:
    """Create sample IEQ data for demonstration."""
    # Create 24 hours of data with 15-minute intervals
    dates = pd.date_range(
        start='2024-01-15 08:00',
        end='2024-01-15 18:00',
        freq='15min'
    )
    
    n_points = len(dates)
    
    # Simulate realistic IEQ data patterns
    np.random.seed(42)  # For reproducible results
    
    # Base patterns with some variation
    temperature = 21 + 3 * np.sin(np.linspace(0, 2*np.pi, n_points)) + np.random.normal(0, 0.5, n_points)
    humidity = 45 + 15 * np.sin(np.linspace(0, np.pi, n_points) + np.pi/4) + np.random.normal(0, 2, n_points)
    co2 = 400 + 300 * (np.sin(np.linspace(0, 4*np.pi, n_points)) + 1) + np.random.normal(0, 20, n_points)
    
    # Add some realistic constraints
    temperature = np.clip(temperature, 18, 28)
    humidity = np.clip(humidity, 25, 75)
    co2 = np.clip(co2, 350, 1200)
    
    # Add some "problem periods" for demonstration
    # High CO2 during mid-day (simulating high occupancy)
    midday_mask = (dates.hour >= 11) & (dates.hour <= 14)
    co2[midday_mask] += 200
    
    # Temperature spike in afternoon
    afternoon_mask = (dates.hour >= 14) & (dates.hour <= 16)
    temperature[afternoon_mask] += 2
    
    data = pd.DataFrame({
        'temperature': temperature,
        'humidity': humidity,
        'co2': co2,
        'pm25': np.random.lognormal(2, 0.5, n_points),  # PM2.5 in μg/m³
        'noise': 35 + 15 * np.random.random(n_points)    # Noise in dB
    }, index=dates)
    
    return data


def demonstrate_basic_analytics():
    """Demonstrate basic analytics functionality."""
    print("🏢 IEQ Analytics System Demo")
    print("=" * 50)
    
    # Create sample data
    print("\n1. Creating sample IEQ data...")
    sample_data = create_sample_data()
    print(f"   ✅ Created data with {len(sample_data)} data points")
    print(f"   📊 Time range: {sample_data.index[0]} to {sample_data.index[-1]}")
    print(f"   🌡️  Temperature range: {sample_data['temperature'].min():.1f}°C - {sample_data['temperature'].max():.1f}°C")
    print(f"   💧 Humidity range: {sample_data['humidity'].min():.1f}% - {sample_data['humidity'].max():.1f}%")
    print(f"   🫁 CO2 range: {sample_data['co2'].min():.0f} - {sample_data['co2'].max():.0f} ppm")
    
    # Create IEQ data object
    ieq_data = IEQData(
        data=sample_data,
        room_id="demo_classroom",
        building_id="demo_school",
        source_files=["demo_data.csv"],
        data_period_start=sample_data.index[0],
        data_period_end=sample_data.index[-1],
        quality_score=0.95
    )
    
    # Initialize analytics
    print("\n2. Initializing analytics engine...")
    analytics = IEQAnalytics()
    print("   ✅ Analytics engine initialized")
    
    if analytics.rules_engine:
        print("   ✅ Rule-based analytics engine available")
    else:
        print("   ⚠️  Rule-based analytics not available (install json-logic package)")
    
    # Perform analysis
    print("\n3. Performing comprehensive analysis...")
    results = analytics.analyze_room_data(ieq_data)
    print("   ✅ Analysis completed")
    
    # Display key results
    print("\n📊 ANALYSIS RESULTS")
    print("-" * 30)
    
    # Basic statistics
    if 'basic_statistics' in results:
        stats = results['basic_statistics']
        print(f"\n🌡️  Temperature Statistics:")
        print(f"   Mean: {stats['temperature']['mean']:.1f}°C")
        print(f"   Range: {stats['temperature']['min']:.1f}°C - {stats['temperature']['max']:.1f}°C")
        print(f"   Std Dev: {stats['temperature']['std']:.1f}°C")
        
        print(f"\n💧 Humidity Statistics:")
        print(f"   Mean: {stats['humidity']['mean']:.1f}%")
        print(f"   Range: {stats['humidity']['min']:.1f}% - {stats['humidity']['max']:.1f}%")
        
        print(f"\n🫁 CO2 Statistics:")
        print(f"   Mean: {stats['co2']['mean']:.0f} ppm")
        print(f"   Max: {stats['co2']['max']:.0f} ppm")
    
    # Comfort analysis
    if 'comfort_analysis' in results:
        comfort = results['comfort_analysis']
        print(f"\n🏡 Comfort Analysis:")
        for category, data in comfort.items():
            if isinstance(data, dict) and 'percentage' in data:
                print(f"   {category.replace('_', ' ').title()}: {data['percentage']:.1f}%")
    
    # Data quality
    if 'data_quality' in results:
        quality = results['data_quality']
        print(f"\n✅ Data Quality Score: {quality.get('overall_score', 'N/A')}")
        if 'completeness' in quality and isinstance(quality['completeness'], dict):
            if 'percentage' in quality['completeness']:
                print(f"   Completeness: {quality['completeness']['percentage']:.1f}%")
            else:
                print(f"   Completeness: {quality['completeness']}")
    
    # Recommendations
    if 'recommendations' in results:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(results['recommendations'][:3], 1):
            print(f"   {i}. {rec}")
    
    # Rule-based analysis (if available)
    if 'rule_based_analysis' in results and results['rule_based_analysis'].get('comfort_compliance'):
        print(f"\n📋 Rule-based Analysis:")
        rule_analysis = results['rule_based_analysis']
        if 'comfort_compliance' in rule_analysis:
            for rule_name, rule_results in rule_analysis['comfort_compliance'].items():
                if isinstance(rule_results, dict) and 'compliance_rate' in rule_results:
                    print(f"   {rule_name}: {rule_results['compliance_rate']:.1%} compliance")
        else:
            print("   No rule-based analysis available (install json-logic package)")
    else:
        print(f"\n📋 Rule-based Analysis: Not available (install json-logic package)")
    
    return results


def demonstrate_rule_builder():
    """Demonstrate rule builder functionality."""
    print("\n\n🔧 RULE BUILDER DEMO")
    print("=" * 50)
    
    # Create a custom rule using the builder
    print("\n1. Building custom comfort rule...")
    
    builder = RuleBuilder()
    custom_rule = (builder
                   .temperature_threshold(min_temp=20, max_temp=25)
                   .humidity_threshold(min_humidity=30, max_humidity=60)
                   .co2_threshold(max_co2=800)
                   .build())
    
    print("   ✅ Custom rule created:")
    print(f"   📝 Rule: {custom_rule}")
    
    # Create a standard comfort rule
    standard_rule = RuleBuilder.create_comfort_rule(
        temperature_range=(21, 26),
        humidity_range=(40, 70),
        co2_max=1000,
        time_range=(8, 18)
    )
    
    print(f"\n   📝 Standard comfort rule created")
    print(f"   🎯 Temperature: 21-26°C, Humidity: 40-70%, CO2 < 1000 ppm")
    
    return custom_rule, standard_rule


def demonstrate_cli_usage():
    """Show CLI usage examples."""
    print("\n\n💻 CLI USAGE EXAMPLES")
    print("=" * 50)
    
    cli_examples = [
        "# Map CSV files to standard format",
        "python -m ieq_analytics.cli mapping --input-file data.csv --interactive",
        "",
        "# Analyze a single room",
        "python -m ieq_analytics.cli analyze --input-file processed_data.csv --room-id classroom1",
        "",
        "# Run complete pipeline",
        "python -m ieq_analytics.cli run --input-dir data/ --output-dir results/",
        "",
        "# Inspect data structure",
        "python -m ieq_analytics.cli inspect --input-file data.csv",
        "",
        "# Generate visualizations",
        "python -m ieq_analytics.cli analyze --input-file data.csv --visualizations --output-dir plots/"
    ]
    
    for example in cli_examples:
        print(f"   {example}")


def main():
    """Main demonstration function."""
    try:
        # Basic analytics demo
        results = demonstrate_basic_analytics()
        
        # Rule builder demo
        custom_rule, standard_rule = demonstrate_rule_builder()
        
        # CLI usage examples
        demonstrate_cli_usage()
        
        print("\n\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("The IEQ Analytics system is ready for use.")
        print("\n📚 Next steps:")
        print("   1. Install optional packages: pip install json-logic holidays")
        print("   2. Prepare your IEQ data in CSV format")
        print("   3. Use the CLI or Python API for analysis")
        print("   4. Customize rules in config/analytics_rules.yaml")
        print("\n📖 For more info, see README.md and documentation.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
