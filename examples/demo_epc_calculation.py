"""
Demo: EPC (Energy Performance Certificate) Rating Calculation

This example demonstrates how to calculate EPC ratings per country using the
official European DataWarehouse GmbH, 2024 data.
"""

from core.domain.enums.epc import EPCRating
from core.domain.enums.countries import Country


def demo_direct_rating_calculation():
    """Calculate EPC rating from energy consumption."""
    print("\n" + "="*70)
    print("DEMO 1: Direct EPC Rating Calculation from Energy Consumption")
    print("="*70)
    
    # Example: Building in Spain with 65 kWh/m²/year
    energy_consumption = 65  # kWh/m²/year
    country = Country.SPAIN
    
    rating = EPCRating.calculate_from_energy_consumption(
        energy_kwh_per_m2=energy_consumption,
        country=country
    )
    
    if rating:
        print(f"\nBuilding in {country.value}:")
        print(f"  Energy Consumption: {energy_consumption} kWh/m²/year")
        print(f"  Energy Type: {EPCRating.get_energy_type(country)}")
        print(f"  EPC Rating: {rating.value}")
        print(f"  Description: {rating.description}")
        print(f"  Numeric Score: {rating.numeric_score}/8")
        
        # Get threshold range
        threshold_range = rating.get_threshold_range(country)
        if threshold_range:
            print(f"  Rating Range: {threshold_range['min']}-{threshold_range['max']} kWh/m²/year")


def demo_primary_energy_calculation():
    """Calculate primary energy and EPC rating."""
    print("\n" + "="*70)
    print("DEMO 2: Primary Energy Calculation with Country-Specific Factors")
    print("="*70)
    
    # Example building data
    building_data = {
        "heating_kwh": 15000,
        "cooling_kwh": 5000,
        "electricity_kwh": 8000,
        "hot_water_kwh": 4000,
        "floor_area_m2": 250,
        "renewable_energy_kwh": 2000,
    }
    
    countries = [Country.DENMARK, Country.GERMANY, Country.FRANCE, Country.ITALY]
    
    for country in countries:
        primary_energy = EPCRating.calculate_primary_energy(
            heating_kwh=building_data["heating_kwh"],
            cooling_kwh=building_data["cooling_kwh"],
            electricity_kwh=building_data["electricity_kwh"],
            hot_water_kwh=building_data["hot_water_kwh"],
            country=country,
            floor_area_m2=building_data["floor_area_m2"],
            renewable_energy_kwh=building_data["renewable_energy_kwh"]
        )
        
        rating = EPCRating.calculate_from_energy_consumption(
            energy_kwh_per_m2=primary_energy,
            country=country
        )
        
        if rating:
            print(f"\n{country.value} ({country.code}):")
            print(f"  Primary Energy: {primary_energy:.1f} kWh/m²/year")
            print(f"  EPC Rating: {rating.value} - {rating.description}")


def demo_country_thresholds():
    """Display EPC thresholds for different countries."""
    print("\n" + "="*70)
    print("DEMO 3: EPC Rating Thresholds by Country")
    print("="*70)
    
    countries = [
        Country.LUXEMBOURG,
        Country.BELGIUM,
        Country.NETHERLANDS,
        Country.AUSTRIA,
    ]
    
    for country in countries:
        thresholds = EPCRating.get_country_thresholds(country)
        rating_info = EPCRating.get_rating_info(country)
        
        print(f"\n{country.value}:")
        print(f"  Energy Type: {rating_info.get('energy_type')}")
        if 'note' in rating_info:
            print(f"  Note: {rating_info['note']}")
        print(f"  Thresholds (kWh/m²/year):")
        
        for rating, (min_val, max_val) in sorted(thresholds.items(), 
                                                   key=lambda x: x[1][0]):
            max_str = f"{max_val:.1f}" if max_val != float('inf') else "∞"
            print(f"    {rating:3s}: {min_val:6.1f} - {max_str:>6s}")


def demo_comparison_across_countries():
    """Compare how the same building performs across countries."""
    print("\n" + "="*70)
    print("DEMO 4: Same Building Performance Across European Countries")
    print("="*70)
    
    # A building with fixed final energy consumption
    building = {
        "heating_kwh": 12000,
        "cooling_kwh": 3000,
        "electricity_kwh": 6000,
        "hot_water_kwh": 3000,
        "floor_area_m2": 200,
        "renewable_energy_kwh": 1000,
    }
    
    print(f"\nBuilding Data:")
    print(f"  Floor Area: {building['floor_area_m2']} m²")
    print(f"  Heating: {building['heating_kwh']} kWh/year")
    print(f"  Cooling: {building['cooling_kwh']} kWh/year")
    print(f"  Electricity: {building['electricity_kwh']} kWh/year")
    print(f"  Hot Water: {building['hot_water_kwh']} kWh/year")
    print(f"  Renewable Energy: {building['renewable_energy_kwh']} kWh/year")
    
    print(f"\n{'Country':<20} {'Energy Type':<15} {'Primary':<10} {'Rating':<10} {'Score'}")
    print("-" * 70)
    
    countries = [
        Country.DENMARK, Country.GERMANY, Country.FRANCE, Country.SPAIN,
        Country.ITALY, Country.PORTUGAL, Country.NETHERLANDS, Country.POLAND
    ]
    
    for country in countries:
        primary_energy = EPCRating.calculate_primary_energy(
            **{k: v for k, v in building.items() if k != 'floor_area_m2'},
            country=country,
            floor_area_m2=building['floor_area_m2']
        )
        
        rating = EPCRating.calculate_from_energy_consumption(
            energy_kwh_per_m2=primary_energy,
            country=country
        )
        
        energy_type = EPCRating.get_energy_type(country)
        
        if rating:
            print(f"{country.value:<20} {energy_type:<15} {primary_energy:>8.1f} "
                  f"{rating.value:>8s}  {rating.numeric_score}/8")


def demo_energy_improvement_scenarios():
    """Show how improvements affect EPC rating."""
    print("\n" + "="*70)
    print("DEMO 5: Energy Improvement Scenarios")
    print("="*70)
    
    country = Country.GERMANY
    floor_area = 180
    
    scenarios = {
        "Current Building": {
            "heating_kwh": 18000,
            "cooling_kwh": 4000,
            "electricity_kwh": 7000,
            "hot_water_kwh": 4000,
            "renewable_energy_kwh": 0,
        },
        "After Insulation": {
            "heating_kwh": 12000,  # 33% reduction
            "cooling_kwh": 3000,
            "electricity_kwh": 7000,
            "hot_water_kwh": 4000,
            "renewable_energy_kwh": 0,
        },
        "After Solar Panels": {
            "heating_kwh": 12000,
            "cooling_kwh": 3000,
            "electricity_kwh": 7000,
            "hot_water_kwh": 4000,
            "renewable_energy_kwh": 4000,  # Solar generation
        },
        "Full Renovation": {
            "heating_kwh": 8000,   # 56% reduction
            "cooling_kwh": 2000,
            "electricity_kwh": 5000,
            "hot_water_kwh": 2500,
            "renewable_energy_kwh": 5000,
        },
    }
    
    print(f"\nCountry: {country.value}")
    print(f"Floor Area: {floor_area} m²")
    print(f"\n{'Scenario':<25} {'Primary Energy':<18} {'Rating':<10} {'Improvement'}")
    print("-" * 75)
    
    baseline_primary = None
    
    for scenario_name, data in scenarios.items():
        primary_energy = EPCRating.calculate_primary_energy(
            **data,
            country=country,
            floor_area_m2=floor_area
        )
        
        rating = EPCRating.calculate_from_energy_consumption(
            energy_kwh_per_m2=primary_energy,
            country=country
        )
        
        if baseline_primary is None:
            baseline_primary = primary_energy
            improvement = "-"
        else:
            reduction = ((baseline_primary - primary_energy) / baseline_primary) * 100
            improvement = f"{reduction:+.1f}%"
        
        if rating:
            print(f"{scenario_name:<25} {primary_energy:>8.1f} kWh/m²/y  "
                  f"{rating.value:>8s}  {improvement:>10s}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  EPC (Energy Performance Certificate) Rating Calculator")
    print("  Data source: European DataWarehouse GmbH, 2024")
    print("="*70)
    
    demo_direct_rating_calculation()
    demo_primary_energy_calculation()
    demo_country_thresholds()
    demo_comparison_across_countries()
    demo_energy_improvement_scenarios()
    
    print("\n" + "="*70)
    print("Demo completed!")
    print("="*70 + "\n")
