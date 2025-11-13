"""
Demonstration: Thermal Comfort Cost Analysis and Optimization

This example shows how to:
1. Load climate and energy data for buildings
2. Calculate the cost of maintaining thermal comfort per EN 16798 category
3. Analyze the cost per delta T (temperature differential)
4. Optimize temperature control to lower comfort boundaries for cost savings
5. Compare optimization strategies across different rooms and buildings
"""

import pandas as pd
from pathlib import Path

from core.analytics.calculators.thermal_comfort_cost_calculator import (
    ThermalComfortCostCalculator,
    EnergyCosts,
    calculate_cost_per_room
)
from core.domain.enums.en16798_category import EN16798Category


def load_building_data(building_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    """
    Load climate and energy data for a building.
    
    Returns:
        Tuple of (climate_data, energy_data, room_data_dict)
    """
    # Load climate data
    climate_file = building_path / "climate_data.csv"
    climate_data = pd.read_csv(climate_file, index_col='timestamp', parse_dates=True)
    
    # Load energy data
    energy_file = building_path / "energy_data.csv"
    energy_data = pd.read_csv(energy_file, index_col='timestamp', parse_dates=True)
    
    # Load room data
    room_data: dict[str, pd.DataFrame] = {}
    for csv_file in building_path.glob("*.csv"):
        if csv_file.name not in ["climate_data.csv", "energy_data.csv", "metadata.json"]:
            room_name = csv_file.stem
            df = pd.read_csv(csv_file, index_col='timestamp', parse_dates=True)
            room_data[room_name] = df
    
    return climate_data, energy_data, room_data


def print_separator(title: str = ""):
    """Print a visual separator."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'=' * 80}\n")


def main():
    """Run the thermal comfort cost analysis demonstration."""
    
    print_separator("THERMAL COMFORT COST ANALYSIS & OPTIMIZATION")
    
    # Define energy costs (example values for Denmark/Europe)
    energy_costs = EnergyCosts(
        district_heating_cost_per_kwh=0.12,  # €/kWh
        electricity_cost_per_kwh=0.30,       # €/kWh
        pv_feed_in_tariff=0.08              # €/kWh
    )
    
    print("Energy Cost Configuration:")
    print(f"  District Heating: €{energy_costs.district_heating_cost_per_kwh:.3f}/kWh")
    print(f"  Grid Electricity: €{energy_costs.electricity_cost_per_kwh:.3f}/kWh")
    print(f"  PV Feed-in Tariff: €{energy_costs.pv_feed_in_tariff:.3f}/kWh")
    print()
    
    # Initialize calculator
    calculator = ThermalComfortCostCalculator(energy_costs)
    
    # Define building paths
    data_dir = Path("data")
    buildings = {
        "Building A (Office Tower)": data_dir / "building_a",
        "Building B (Retail/Mixed)": data_dir / "building_b",
        "Building C (School)": data_dir / "building_c"
    }
    
    all_results = {}
    
    for building_name, building_path in buildings.items():
        print_separator(f"Analysis: {building_name}")
        
        # Check if building exists
        if not building_path.exists():
            print(f"⚠️  Building path not found: {building_path}")
            continue
        
        # Load data
        try:
            climate_data, energy_data, room_data = load_building_data(building_path)
            print(f"✓ Loaded data:")
            print(f"  - Climate data: {len(climate_data)} hours")
            print(f"  - Energy data: {len(energy_data)} hours")
            print(f"  - Rooms found: {len(room_data)}")
            print()
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            continue
        
        if len(room_data) == 0:
            print("⚠️  No room data files found (excluding climate and energy files)")
            continue
        
        # Analyze each room
        building_results: dict[str, dict] = {}
        
        for room_name, room_df in room_data.items():
            room_name_str = str(room_name)
            print(f"\n--- Room: {room_name_str.replace('_', ' ').title()} ---\n")
            
            # Determine appropriate category based on room type
            room_name_lower = room_name_str.lower()
            if "office" in room_name_lower:
                category = EN16798Category.CATEGORY_II
            elif "server" in room_name_lower or "computer" in room_name_lower:
                category = EN16798Category.CATEGORY_I
            elif "storage" in room_name_lower or "basement" in room_name_lower:
                category = EN16798Category.CATEGORY_III
            elif "classroom" in room_name_lower or "library" in room_name_lower:
                category = EN16798Category.CATEGORY_II
            else:
                category = EN16798Category.CATEGORY_II  # Default
            
            print(f"Target Category: {category.value}")
            
            try:
                # Calculate cost and optimization
                cost_result, opt_result = calculate_cost_per_room(
                    room_data=room_df,
                    climate_data=climate_data,
                    energy_data=energy_data,
                    energy_costs=energy_costs,
                    room_category=category,
                    season="heating"
                )
                
                # Display current performance
                print(f"\n📊 Current Performance:")
                print(f"  Period: {cost_result.period_start.strftime('%Y-%m-%d')} to "
                      f"{cost_result.period_end.strftime('%Y-%m-%d')}")
                print(f"  Average Indoor Temperature: {cost_result.avg_indoor_temp:.1f}°C")
                print(f"  Average Outdoor Temperature: {cost_result.avg_outdoor_temp:.1f}°C")
                print(f"  Comfort Range: {cost_result.temp_lower_bound:.1f}°C - "
                      f"{cost_result.temp_upper_bound:.1f}°C")
                print(f"  Comfort Compliance: {cost_result.comfort_compliance_rate:.1f}%")
                print(f"    - Hours in comfort: {cost_result.hours_in_comfort}")
                print(f"    - Hours below comfort: {cost_result.hours_below_comfort}")
                print(f"    - Hours above comfort: {cost_result.hours_above_comfort}")
                
                # Display energy consumption
                print(f"\n⚡ Energy Consumption:")
                print(f"  District Heating: {cost_result.total_heating_kwh:.1f} kWh")
                print(f"  Grid Electricity: {cost_result.total_electricity_kwh:.1f} kWh")
                print(f"  PV Production: {cost_result.total_pv_production_kwh:.1f} kWh")
                print(f"  Net Electricity: {cost_result.net_electricity_kwh:.1f} kWh")
                
                # Display costs
                print(f"\n💰 Energy Costs:")
                print(f"  Heating Cost: €{cost_result.heating_cost:.2f}")
                print(f"  Electricity Cost: €{cost_result.electricity_cost:.2f}")
                print(f"  PV Revenue: €{cost_result.pv_revenue:.2f}")
                print(f"  Total Energy Cost: €{cost_result.total_energy_cost:.2f}")
                
                # Display efficiency metrics
                print(f"\n📈 Efficiency Metrics:")
                print(f"  Cost per Delta T: €{cost_result.cost_per_delta_t:.3f}/°C")
                print(f"  Heating per Delta T: {cost_result.heating_per_delta_t:.2f} kWh/°C")
                print(f"  Cost per Degree-Hour: €{cost_result.cost_per_degree_hour:.4f}/°C·h")
                
                # Display optimization results
                print(f"\n🎯 Optimization Analysis:")
                print(f"  Strategy: {opt_result.strategy.split(' | ')[0]}")
                print(f"  Temperature Reduction: {opt_result.temp_reduction:.1f}°C")
                print(f"  Optimized Setpoint: {opt_result.optimized_avg_temp:.1f}°C")
                
                if opt_result.cost_savings > 0:
                    print(f"\n💡 Potential Savings:")
                    print(f"  Annual Cost Savings: €{opt_result.cost_savings:.2f}")
                    print(f"  Savings Percentage: {opt_result.cost_savings_percent:.1f}%")
                    print(f"  Feasibility Score: {opt_result.feasibility_score:.0f}/100")
                    if opt_result.estimated_roi_months:
                        print(f"  Estimated ROI: {opt_result.estimated_roi_months:.1f} months")
                    
                    # Extrapolate to annual
                    days_in_period = (cost_result.period_end - cost_result.period_start).days
                    annual_factor = 365 / days_in_period
                    annual_savings = opt_result.cost_savings * annual_factor
                    print(f"  Extrapolated Annual Savings: €{annual_savings:.2f}/year")
                else:
                    print(f"\n✅ Already Optimized!")
                    print(f"  {opt_result.strategy}")
                
                # Store results
                building_results[room_name_str] = {
                    'cost_result': cost_result,
                    'opt_result': opt_result,
                    'category': category
                }
                
            except Exception as e:
                print(f"❌ Error analyzing room: {e}")
                import traceback
                traceback.print_exc()
        
        all_results[building_name] = building_results
    
    # Summary comparison across all buildings
    print_separator("SUMMARY: Building-Wide Optimization Potential")
    
    total_current_cost = 0
    total_optimized_cost = 0
    total_savings = 0
    
    for building_name, building_results in all_results.items():
        if not building_results:
            continue
        
        print(f"\n{building_name}:")
        building_current_cost = sum(r['cost_result'].total_energy_cost 
                                    for r in building_results.values())
        building_optimized_cost = sum(r['opt_result'].optimized_total_cost 
                                      for r in building_results.values())
        building_savings = building_current_cost - building_optimized_cost
        
        print(f"  Current Total Cost: €{building_current_cost:.2f}")
        print(f"  Optimized Total Cost: €{building_optimized_cost:.2f}")
        print(f"  Potential Savings: €{building_savings:.2f} "
              f"({(building_savings/building_current_cost*100):.1f}%)")
        
        # Show room-by-room breakdown
        print(f"\n  Room Breakdown:")
        for room_name, results in building_results.items():
            opt = results['opt_result']
            if opt.cost_savings > 0:
                print(f"    {room_name.replace('_', ' ').title()}: "
                      f"€{opt.cost_savings:.2f} savings "
                      f"({opt.temp_reduction:.1f}°C reduction)")
            else:
                print(f"    {room_name.replace('_', ' ').title()}: Already optimized")
        
        total_current_cost += building_current_cost
        total_optimized_cost += building_optimized_cost
        total_savings += building_savings
    
    if total_current_cost > 0:
        print(f"\n{'=' * 80}")
        print(f"PORTFOLIO TOTALS:")
        print(f"  Current Total Cost: €{total_current_cost:.2f}")
        print(f"  Optimized Total Cost: €{total_optimized_cost:.2f}")
        print(f"  Total Potential Savings: €{total_savings:.2f}")
        print(f"  Overall Savings: {(total_savings/total_current_cost*100):.1f}%")
        print(f"{'=' * 80}\n")
    
    # Generate recommendations
    print_separator("RECOMMENDATIONS")
    
    print("Based on the thermal comfort cost analysis:\n")
    
    print("1. IMMEDIATE ACTIONS (0-3 months):")
    print("   - Adjust temperature setpoints to lower comfort boundaries")
    print("   - Enable night setback (reduce temps by 2-3°C during unoccupied hours)")
    print("   - Implement weekend temperature optimization for non-24/7 spaces")
    
    print("\n2. SHORT-TERM IMPROVEMENTS (3-12 months):")
    print("   - Install or upgrade room-level temperature controls")
    print("   - Implement weather-compensated heating curves")
    print("   - Enable adaptive comfort strategies for naturally ventilated spaces")
    
    print("\n3. LONG-TERM OPTIMIZATION (1-3 years):")
    print("   - Consider building envelope improvements to reduce heating demand")
    print("   - Expand PV capacity to offset electricity costs")
    print("   - Implement predictive control using weather forecasts")
    
    print("\n4. MONITORING & VERIFICATION:")
    print("   - Track actual savings vs. projections monthly")
    print("   - Monitor comfort compliance to ensure occupant satisfaction")
    print("   - Adjust strategies based on seasonal performance")
    
    print_separator()
    print("Analysis complete! Review the results above to identify optimization opportunities.")
    print()


if __name__ == "__main__":
    main()
