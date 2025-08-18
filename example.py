#!/usr/bin/env python3
"""
Example script demonstrating how to use the IEQ Analytics Engine programmatically.
"""

from pathlib import Path
import pandas as pd
from ieq_analytics import DataMapper, IEQAnalytics, Building, Room, IEQData

def main():
    """Run the example analysis."""
    
    print("🚀 IEQ Analytics Engine - Example Usage")
    
    # Initialize components
    mapper = DataMapper()
    analytics = IEQAnalytics()
    
    # Set up paths
    data_dir = Path("data/raw/concatenated")
    output_dir = Path("output/example")
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        print("Please ensure you have data files in the expected location.")
        return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Example 1: Analyze file structure
    print("\n📊 Step 1: Analyzing file structure...")
    analysis = mapper.analyze_files(data_dir)
    
    print(f"   Found {len(analysis['files'])} files")
    print(f"   Detected {len(analysis['building_patterns'])} building patterns")
    print(f"   Buildings: {', '.join(analysis['building_patterns'][:3])}...")
    
    # Example 2: Process a single file (if available)
    csv_files = list(data_dir.glob("*.csv"))
    if csv_files:
        sample_file = csv_files[0]
        print(f"\n🔍 Step 2: Processing sample file: {sample_file.name}")
        
        # Read file to get columns
        df_sample = pd.read_csv(sample_file, nrows=0)
        columns = list(df_sample.columns)
        
        # Get automatic column mapping suggestions
        suggestions = mapper.suggest_column_mappings(columns)
        print(f"   Suggested mappings: {suggestions}")
        
        # Create a manual mapping for demonstration
        column_mapping = {
            "DateTime": "timestamp",
            "Temperatur": "temperature", 
            "Fugtighed": "humidity",
            "CO2": "co2"
        }
        
        # Filter mapping to only include existing columns
        valid_mapping = {k: v for k, v in column_mapping.items() if k in columns}
        
        if valid_mapping:
            print(f"   Using mapping: {valid_mapping}")
            
            # Process the file
            ieq_data = mapper.map_file(sample_file, valid_mapping)
            
            if ieq_data:
                print(f"   ✅ Successfully processed {sample_file.name}")
                print(f"   Data shape: {ieq_data.data.shape}")
                print(f"   Date range: {ieq_data.data_period_start} to {ieq_data.data_period_end}")
                
                # Example 3: Perform analysis
                print(f"\n🔬 Step 3: Performing IEQ analysis...")
                
                analysis_result = analytics.analyze_room_data(ieq_data)
                
                print(f"   Data quality score: {analysis_result['data_quality']['overall_score']:.3f}")
                print(f"   Total records: {analysis_result['data_quality']['total_records']}")
                
                # Show basic statistics
                basic_stats = analysis_result.get('basic_statistics', {})
                for param, stats in basic_stats.items():
                    print(f"   {param}: mean={stats['mean']:.1f}, std={stats['std']:.1f}")
                
                # Show recommendations
                recommendations = analysis_result.get('recommendations', [])
                print(f"\n💡 Recommendations:")
                for rec in recommendations[:3]:  # Show first 3
                    print(f"   - {rec}")
                
                # Example 4: Generate visualizations
                print(f"\n📈 Step 4: Generating visualizations...")
                
                plots_dir = output_dir / "plots"
                generated_plots = analytics.generate_visualizations(ieq_data, plots_dir)
                
                if generated_plots:
                    print(f"   Generated {len(generated_plots)} plots:")
                    for plot_type, plot_path in generated_plots.items():
                        print(f"   - {plot_type}: {plot_path}")
                else:
                    print("   No plots generated (possible data issues)")
                
                # Save analysis results
                import json
                results_file = output_dir / "analysis_results.json"
                with open(results_file, 'w') as f:
                    json.dump(analysis_result, f, indent=2, default=str)
                
                print(f"\n💾 Results saved to: {results_file}")
            else:
                print("   ❌ Failed to process file")
        else:
            print("   ❌ No valid column mappings found")
    else:
        print("❌ No CSV files found in data directory")
    
    print("\n🎉 Example completed!")

if __name__ == "__main__":
    main()
