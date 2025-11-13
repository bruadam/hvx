"""
Demonstration of building performance evaluation and recommendation generation.

This example shows how to:
1. Load temperature and energy consumption data
2. Estimate thermal parameters (R_env, C_in)
3. Evaluate building performance
4. Get specific recommendations (insulation, HVAC, solar, etc.)
5. Quantify savings potential
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analytics.recommendations.building_performance_evaluator import (
    BuildingPerformanceEvaluator,
    BuildingType,
    InterventionType
)


def generate_building_data_scenario(scenario: str = "poor_insulation"):
    """
    Generate realistic building data for different scenarios.

    Args:
        scenario: "poor_insulation", "old_hvac", "good_building"
    """
    np.random.seed(42)

    # 30 days of hourly data
    n_hours = 30 * 24
    timestamps = pd.date_range('2024-01-01', periods=n_hours, freq='H')

    # Outdoor temperature with diurnal variation (winter scenario)
    hour_of_day = timestamps.hour.values
    day_of_year = timestamps.dayofyear.values

    T_out = (
        5  # Base winter temperature
        + 5 * np.sin(2 * np.pi * hour_of_day / 24 - np.pi/2)  # Diurnal cycle
        + 3 * np.sin(2 * np.pi * day_of_year / 30)  # Monthly variation
        + np.random.normal(0, 1, n_hours)  # Weather noise
    )

    # Building parameters based on scenario
    if scenario == "poor_insulation":
        R_env = 0.006  # Poor insulation
        C_in = 4e6     # Medium thermal mass
        heating_cop = 0.75  # Old inefficient boiler
        setpoint = 21.0
        description = "Poorly insulated residential building with old boiler"

    elif scenario == "old_hvac":
        R_env = 0.012  # Average insulation
        C_in = 8e6     # Heavy construction
        heating_cop = 0.65  # Very old, inefficient system
        setpoint = 22.0
        description = "Well-constructed building but very old heating system"

    elif scenario == "good_building":
        R_env = 0.022  # Excellent insulation
        C_in = 6e6     # Good thermal mass
        heating_cop = 3.5  # Modern heat pump
        setpoint = 20.5
        description = "Modern, well-insulated building with heat pump"

    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    # Occupancy pattern for internal gains
    is_night = (hour_of_day < 6) | (hour_of_day >= 22)
    is_workday = timestamps.weekday.values < 5
    is_business_hours = is_workday & (hour_of_day >= 8) & (hour_of_day < 18)

    # Internal gains from occupants and equipment
    Q_internal = np.zeros(n_hours)
    Q_internal[is_night] = 300  # Minimal gains at night
    Q_internal[~is_night & ~is_business_hours] = 600  # Moderate gains
    Q_internal[is_business_hours] = 1200  # Full occupancy
    Q_internal += np.random.normal(0, 100, n_hours)

    # Simulate building thermal dynamics
    T_in = np.zeros(n_hours)
    T_in[0] = setpoint
    heating_power = np.zeros(n_hours)

    dt_seconds = 3600  # 1 hour

    for i in range(1, n_hours):
        # Simple thermostat control
        if T_in[i-1] < setpoint - 0.5:
            # Heating needed
            heat_loss = (T_in[i-1] - T_out[i-1]) / R_env
            required_heat = max(heat_loss - Q_internal[i-1], 0)
            heating_power[i] = required_heat / heating_cop  # Input power

            # Net heat into building
            net_heat = (heating_power[i] * heating_cop) + Q_internal[i-1] - heat_loss
        else:
            # No heating
            heating_power[i] = 0
            heat_loss = (T_in[i-1] - T_out[i-1]) / R_env
            net_heat = Q_internal[i-1] - heat_loss

        # Temperature change
        dT_dt = net_heat / C_in
        T_in[i] = T_in[i-1] + dT_dt * dt_seconds

    # Add measurement noise
    T_in += np.random.normal(0, 0.1, n_hours)
    T_out += np.random.normal(0, 0.15, n_hours)

    # Calculate electricity consumption (lighting, equipment, fans)
    electricity_power = np.zeros(n_hours)
    electricity_power[is_night] = 200
    electricity_power[~is_night & ~is_business_hours] = 400
    electricity_power[is_business_hours] = 800
    electricity_power += np.random.normal(0, 50, n_hours)

    # Annual totals (extrapolate from 30 days)
    annual_heating_kwh = (heating_power.sum() / 1000) * (365 / 30)
    annual_electricity_kwh = (electricity_power.sum() / 1000) * (365 / 30)

    return {
        'timestamps': timestamps,
        'T_in': T_in,
        'T_out': T_out,
        'heating_power': heating_power,
        'electricity_power': electricity_power,
        'annual_heating_kwh': annual_heating_kwh,
        'annual_electricity_kwh': annual_electricity_kwh,
        'true_R_env': R_env,
        'true_C_in': C_in,
        'true_cop': heating_cop,
        'description': description
    }


def demo_full_evaluation():
    """Complete building performance evaluation workflow."""

    print("=" * 80)
    print("BUILDING PERFORMANCE EVALUATION - PRACTICAL DEMONSTRATION")
    print("=" * 80)
    print()

    # Scenario: Poorly insulated residential building
    print("Loading building data...")
    data = generate_building_data_scenario("poor_insulation")

    print(f"Scenario: {data['description']}")
    print(f"Data period: {data['timestamps'][0]} to {data['timestamps'][-1]}")
    print(f"Annual heating consumption: {data['annual_heating_kwh']:.0f} kWh")
    print(f"Annual electricity consumption: {data['annual_electricity_kwh']:.0f} kWh")
    print()
    print(f"True building parameters (for validation):")
    print(f"  R_env: {data['true_R_env']:.6f} K/W")
    print(f"  C_in:  {data['true_C_in']:.4e} J/K")
    print(f"  Heating COP: {data['true_cop']:.2f}")
    print()

    # Initialize evaluator
    floor_area_m2 = 150  # 150 m² residential building
    evaluator = BuildingPerformanceEvaluator(
        building_type=BuildingType.RESIDENTIAL_DETACHED,
        floor_area_m2=floor_area_m2,
        energy_cost_per_kwh=0.15,  # €0.15/kWh
        co2_per_kwh_heating=0.25,  # kg CO2/kWh for district heating
        co2_per_kwh_electricity=0.40  # kg CO2/kWh for grid electricity
    )

    print("Step 1: Estimating thermal parameters...")
    print("-" * 80)

    thermal_params = evaluator.estimate_thermal_parameters(
        T_in=data['T_in'],
        T_out=data['T_out'],
        heating_power=data['heating_power'],
        electricity_power=data['electricity_power'],
        dt=1.0,
        method='nonlinear'
    )

    print(f"Estimated R_env: {thermal_params.R_env:.6f} K/W "
          f"(true: {data['true_R_env']:.6f}, error: {abs(thermal_params.R_env - data['true_R_env']) / data['true_R_env'] * 100:.1f}%)")
    print(f"Estimated C_in:  {thermal_params.C_in:.4e} J/K "
          f"(true: {data['true_C_in']:.4e}, error: {abs(thermal_params.C_in - data['true_C_in']) / data['true_C_in'] * 100:.1f}%)")
    print(f"Model fit (R²): {thermal_params.r_squared:.3f}")
    print(f"Model RMSE: {thermal_params.rmse:.3f}°C")
    print()

    print("Step 2: Evaluating building performance...")
    print("-" * 80)

    report = evaluator.evaluate_performance(
        thermal_params=thermal_params,
        T_in=data['T_in'],
        T_out=data['T_out'],
        heating_energy_kwh=data['annual_heating_kwh'],
        electricity_kwh=data['annual_electricity_kwh'],
        timestamps=data['timestamps']
    )

    print()
    evaluator.print_report(report)

    return report


def demo_scenario_comparison():
    """Compare different building scenarios."""

    print("\n\n")
    print("=" * 80)
    print("SCENARIO COMPARISON")
    print("=" * 80)
    print()

    scenarios = ["poor_insulation", "old_hvac", "good_building"]
    results = []

    for scenario in scenarios:
        print(f"\nAnalyzing: {scenario.replace('_', ' ').title()}")
        print("-" * 80)

        data = generate_building_data_scenario(scenario)

        evaluator = BuildingPerformanceEvaluator(
            building_type=BuildingType.RESIDENTIAL_DETACHED,
            floor_area_m2=150,
            energy_cost_per_kwh=0.15
        )

        thermal_params = evaluator.estimate_thermal_parameters(
            T_in=data['T_in'],
            T_out=data['T_out'],
            heating_power=data['heating_power'],
            electricity_power=data['electricity_power'],
            dt=1.0,
            method='nonlinear'
        )

        report = evaluator.evaluate_performance(
            thermal_params=thermal_params,
            T_in=data['T_in'],
            T_out=data['T_out'],
            heating_energy_kwh=data['annual_heating_kwh'],
            electricity_kwh=data['annual_electricity_kwh'],
            timestamps=data['timestamps']
        )

        results.append({
            'scenario': scenario,
            'r_env': thermal_params.R_env,
            'c_in': thermal_params.C_in,
            'r_env_rating': report.r_env_rating,
            'heating_kwh': report.annual_heating_kwh,
            'cost': report.annual_energy_cost,
            'co2': report.current_co2_kg_per_year,
            'savings_potential_pct': report.total_savings_potential_percent,
            'savings_potential_eur': report.total_savings_potential_cost,
            'top_intervention': report.interventions[0].intervention_type.value if report.interventions else "None"
        })

        print(f"  R_env: {thermal_params.R_env:.6f} K/W ({report.r_env_rating})")
        print(f"  Annual cost: €{report.annual_energy_cost:.0f}")
        print(f"  CO₂ emissions: {report.current_co2_kg_per_year:.0f} kg/year")
        print(f"  Savings potential: {report.total_savings_potential_percent:.0f}% (€{report.total_savings_potential_cost:.0f}/year)")
        print(f"  Top recommendation: {report.interventions[0].intervention_type.value if report.interventions else 'None'}")

    # Summary table
    print("\n\n")
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print(f"{'Scenario':<25} {'R_env Rating':<15} {'Annual Cost':<15} {'CO₂ (kg/yr)':<15} {'Savings %':<12}")
    print("-" * 80)

    for r in results:
        print(f"{r['scenario'].replace('_', ' ').title():<25} "
              f"{r['r_env_rating']:<15} "
              f"€{r['cost']:<14.0f} "
              f"{r['co2']:<15.0f} "
              f"{r['savings_potential_pct']:<12.0f}%")

    print()


def demo_intervention_analysis():
    """Detailed analysis of individual interventions."""

    print("\n\n")
    print("=" * 80)
    print("INTERVENTION ANALYSIS")
    print("=" * 80)
    print()

    data = generate_building_data_scenario("poor_insulation")

    evaluator = BuildingPerformanceEvaluator(
        building_type=BuildingType.RESIDENTIAL_DETACHED,
        floor_area_m2=150,
        energy_cost_per_kwh=0.15
    )

    thermal_params = evaluator.estimate_thermal_parameters(
        T_in=data['T_in'],
        T_out=data['T_out'],
        heating_power=data['heating_power'],
        electricity_power=data['electricity_power'],
        dt=1.0
    )

    report = evaluator.evaluate_performance(
        thermal_params=thermal_params,
        T_in=data['T_in'],
        T_out=data['T_out'],
        heating_energy_kwh=data['annual_heating_kwh'],
        electricity_kwh=data['annual_electricity_kwh'],
        timestamps=data['timestamps']
    )

    # Create comparison table
    print("INTERVENTION RANKING")
    print("=" * 80)
    print(f"{'#':<3} {'Intervention':<30} {'Savings %':<12} {'Cost (€)':<12} {'Payback (yr)':<14} {'CO₂ Reduction':<15}")
    print("-" * 80)

    for i, intervention in enumerate(report.interventions[:5], 1):  # Top 5
        print(f"{i:<3} "
              f"{intervention.intervention_type.value.replace('_', ' ').title():<30} "
              f"{intervention.estimated_savings_percent:<12.0f}% "
              f"{intervention.estimated_cost_per_m2 * 150:<12.0f} "
              f"{intervention.payback_years:<14.1f} "
              f"{intervention.co2_reduction_kg_per_year:<15.0f} kg/yr")

    # Cumulative analysis
    print("\n\nCUMULATIVE IMPACT ANALYSIS")
    print("=" * 80)

    cumulative_savings = 0
    cumulative_cost = 0
    cumulative_co2 = 0

    for i, intervention in enumerate(report.interventions[:3], 1):
        cumulative_savings += intervention.estimated_savings_percent
        cumulative_cost += intervention.estimated_cost_per_m2 * 150
        cumulative_co2 += intervention.co2_reduction_kg_per_year

        annual_savings_eur = (data['annual_heating_kwh'] + data['annual_electricity_kwh']) * \
                            (cumulative_savings / 100) * 0.15

        print(f"\nAfter implementing top {i} intervention(s):")
        print(f"  Total energy savings: {cumulative_savings:.0f}%")
        print(f"  Total investment: €{cumulative_cost:.0f}")
        print(f"  Annual cost savings: €{annual_savings_eur:.0f}")
        print(f"  CO₂ reduction: {cumulative_co2:.0f} kg/year ({cumulative_co2/1000:.1f} tonnes/year)")
        print(f"  Combined payback: {cumulative_cost / annual_savings_eur:.1f} years")


def main():
    """Run all demonstrations."""

    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "BUILDING PERFORMANCE EVALUATION SYSTEM" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This demonstration shows how to:")
    print("  1. Estimate thermal parameters (R_env, C_in) from real data")
    print("  2. Evaluate building performance against benchmarks")
    print("  3. Generate specific, prioritized recommendations")
    print("  4. Quantify savings and payback periods")
    print("  5. Compare different building scenarios")
    print()

    try:
        # Full evaluation of one building
        print("DEMONSTRATION 1: Complete Building Evaluation")
        print()
        demo_full_evaluation()

        input("\nPress Enter to continue to scenario comparison...")

        # Compare scenarios
        demo_scenario_comparison()

        input("\nPress Enter to continue to intervention analysis...")

        # Detailed intervention analysis
        demo_intervention_analysis()

        print("\n\n")
        print("=" * 80)
        print("DEMONSTRATION COMPLETE")
        print("=" * 80)
        print()
        print("Key Takeaways:")
        print("  ✓ Thermal parameters (R_env, C_in) can be estimated from temperature + energy data")
        print("  ✓ These parameters reveal insulation quality and thermal mass")
        print("  ✓ Benchmarking identifies performance gaps")
        print("  ✓ Specific interventions are recommended with costs and savings")
        print("  ✓ Poor insulation (R_env < 0.01) typically needs urgent attention")
        print("  ✓ Old HVAC systems (COP < 1.0) offer significant upgrade potential")
        print("  ✓ Combining multiple interventions maximizes impact")
        print()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
