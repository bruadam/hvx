"""
Demo: Villa Energy Consumption Simulation

Realistic simulation of a 2-person villa with:
- 4,000 kWh electricity consumption
- 1,500 liters heating oil
- 10 m³ wood for wood burner in living room

This demonstrates:
1. Mixed fuel sources (electricity, oil, wood)
2. Unit conversion from various sources
3. EPC rating calculation for residential buildings
4. Comparison with typical villa consumption
"""

from datetime import datetime, timedelta
from core.domain.models.building import Building
from core.domain.models.energy_consumption import EnergyConsumption
from core.domain.enums.building_type import BuildingType
from core.domain.enums.heating import HeatingType
from core.domain.enums.ventilation import VentilationType
from core.domain.enums.countries import Country
from core.domain.enums.belgium_region import BelgiumRegion
from core.domain.enums.epc import EPCRating
from core.utils.energy_conversion import (
    convert_to_kwh,
    EnergyUnit,
    convert_hot_water_to_kwh,
    get_heating_system_efficiency,
)


def simulate_villa():
    """Simulate a 2-person villa with mixed fuel consumption."""
    
    print("=" * 80)
    print("VILLA ENERGY CONSUMPTION SIMULATION")
    print("=" * 80)
    
    # Villa characteristics
    villa_area = 200.0  # m²
    occupants = 2
    country = Country.BELGIUM  # Belgium
    region = BelgiumRegion.WALLONIA  # Wallonia region
    
    print("\n--- Villa Characteristics ---")
    print(f"Building Type: Residential Villa")
    print(f"Floor Area: {villa_area} m²")
    print(f"Occupants: {occupants} people")
    print(f"Location: {region.value}, {country.value}")
    print(f"Year: 1985")
    
    # Annual consumption data
    print("\n--- Annual Consumption (Raw Data) ---")
    
    # Electricity
    electricity_kwh = 4000.0  # kWh per year
    print(f"Electricity: {electricity_kwh:,.0f} kWh/year")
    print(f"  → {electricity_kwh / villa_area:.1f} kWh/m²/year")
    print(f"  → {electricity_kwh / occupants:.0f} kWh/person/year")
    
    # Heating Oil
    heating_oil_liters = 1500.0  # liters per year
    heating_oil_kwh = convert_to_kwh(heating_oil_liters, EnergyUnit.HEATING_OIL_LITERS)
    print(f"\nHeating Oil: {heating_oil_liters:,.0f} liters/year")
    print(f"  → {heating_oil_kwh:,.0f} kWh (thermal energy)")
    print(f"  → {heating_oil_kwh / villa_area:.1f} kWh/m²/year")
    
    # Wood for burner
    wood_m3 = 10.0  # cubic meters per year
    # 1 m³ wood ≈ 500 kg (depending on wood type and moisture)
    # 1 kg wood ≈ 4.4 kWh
    wood_kg = wood_m3 * 500
    wood_kwh = convert_to_kwh(wood_kg, EnergyUnit.WOOD_KG)
    print(f"\nWood (Living Room Burner): {wood_m3:.1f} m³/year")
    print(f"  → ~{wood_kg:.0f} kg (assuming 500 kg/m³)")
    print(f"  → {wood_kwh:,.0f} kWh (thermal energy)")
    print(f"  → {wood_kwh / villa_area:.1f} kWh/m²/year")
    
    # Total heating
    total_heating_kwh = heating_oil_kwh + wood_kwh
    print(f"\nTotal Heating: {total_heating_kwh:,.0f} kWh/year")
    print(f"  → {total_heating_kwh / villa_area:.1f} kWh/m²/year")
    
    # Hot water (estimated from typical usage)
    # Typical: 50 liters/person/day at 60°C
    daily_hot_water_liters = occupants * 50
    annual_hot_water_liters = daily_hot_water_liters * 365
    hot_water_kwh = convert_hot_water_to_kwh(
        annual_hot_water_liters,
        inlet_temp_celsius=10,
        outlet_temp_celsius=60,
        efficiency=0.85  # Oil boiler efficiency
    )
    print(f"\nHot Water (estimated): {annual_hot_water_liters:,.0f} liters/year")
    print(f"  → {hot_water_kwh:,.0f} kWh (energy to heat)")
    print(f"  → {hot_water_kwh / villa_area:.1f} kWh/m²/year")
    
    # Create the building model
    print("\n" + "=" * 80)
    print("BUILDING MODEL")
    print("=" * 80)
    
    villa = Building(
        id="villa_001",
        name="Family Villa",
        building_type=BuildingType.RESIDENTIAL,
        total_area=villa_area,
        total_occupants=occupants,
        country=country,
        belgium_region=region,
        city="Liège",  # City in Wallonia
        year_built=1989,
        
        # Building systems
        heating_system=HeatingType.BOILER,  # Oil boiler + wood stove
        ventilation_type=VentilationType.NATURAL,
        
        # Annual energy consumption
        annual_heating_kwh=total_heating_kwh,
        annual_electricity_kwh=electricity_kwh,
        annual_hot_water_kwh=hot_water_kwh,
        annual_cooling_kwh=0.0,  # Villas typically don't have AC
        annual_ventilation_kwh=0.0,  # Natural ventilation (no fans)
        
        # No renewable energy (traditional villa)
        annual_solar_pv_kwh=0.0,
    )
    
    print(f"\nBuilding: {villa.name}")
    print(f"Type: {villa.building_type.display_name}")
    print(f"Year Built: {villa.year_built}")
    print(f"Heating System: {villa.heating_system.display_name if villa.heating_system else 'N/A'}")
    print(f"Ventilation: {villa.ventilation_type.display_name if villa.ventilation_type else 'N/A'}")
    
    # Energy summary
    print("\n" + "=" * 80)
    print("ENERGY PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    energy_summary = villa.get_energy_summary()
    consumption = energy_summary["consumption"]
    
    print("\n--- Final Energy Consumption ---")
    print(f"Heating:      {consumption['heating_kwh']:>10,.0f} kWh  ({consumption['heating_kwh_m2']:>6.1f} kWh/m²)")
    print(f"Hot Water:    {consumption['hot_water_kwh']:>10,.0f} kWh  ({consumption['hot_water_kwh_m2']:>6.1f} kWh/m²)")
    print(f"Electricity:  {consumption['electricity_kwh']:>10,.0f} kWh  ({consumption['electricity_kwh_m2']:>6.1f} kWh/m²)")
    print(f"Cooling:      {consumption.get('cooling_kwh', 0):>10,.0f} kWh  (not applicable)")
    print(f"Ventilation:  {consumption.get('ventilation_kwh', 0):>10,.0f} kWh  (natural)")
    print(f"{'-' * 60}")
    print(f"TOTAL:        {consumption['total_kwh']:>10,.0f} kWh  ({consumption['total_kwh_m2']:>6.1f} kWh/m²)")
    
    # Primary energy calculation
    primary_energy = villa.calculate_primary_energy_per_m2()
    
    print("\n--- Primary Energy Performance ---")
    print(f"Final Energy:    {consumption['total_kwh_m2']:.1f} kWh/m²/year")
    print(f"Primary Energy:  {primary_energy:.1f} kWh/m²/year")
    print(f"Energy Type:     {EPCRating.get_energy_type(country)}")
    
    # EPC Rating
    epc_rating = villa.calculate_epc_rating()
    
    print("\n--- Energy Performance Certificate (EPC) ---")
    if epc_rating:
        print(f"Rating: {epc_rating.value}")
        print(f"Description: {epc_rating.description}")
        print(f"Numeric Score: {epc_rating.numeric_score}/8")
        
        threshold = epc_rating.get_threshold_range(country)
        if threshold:
            max_str = f"{threshold['max']:.0f}" if threshold['max'] else "∞"
            print(f"Range: {threshold['min']:.0f} - {max_str} kWh/m²/year")
    else:
        print("Rating: Could not be calculated")
    
    # Breakdown by fuel type
    print("\n--- Fuel Mix Analysis ---")
    print(f"Heating Oil:  {heating_oil_kwh:>10,.0f} kWh ({heating_oil_kwh / consumption['total_kwh'] * 100:.1f}%)")
    print(f"Wood:         {wood_kwh:>10,.0f} kWh ({wood_kwh / consumption['total_kwh'] * 100:.1f}%)")
    print(f"Electricity:  {electricity_kwh:>10,.0f} kWh ({electricity_kwh / consumption['total_kwh'] * 100:.1f}%)")
    
    # CO2 Emissions (approximate)
    print("\n--- CO2 Emissions (Estimated) ---")
    # CO2 factors (kg CO2/kWh)
    co2_oil = 0.27  # kg CO2 per kWh heating oil
    co2_wood = 0.02  # Nearly carbon neutral (growing trees absorb CO2)
    co2_electricity = 0.45  # kg CO2 per kWh (German grid average)
    
    total_co2 = (
        (heating_oil_kwh * co2_oil) +
        (wood_kwh * co2_wood) +
        (electricity_kwh * co2_electricity)
    ) / 1000  # Convert to tons
    
    print(f"From Oil:        {heating_oil_kwh * co2_oil / 1000:.2f} tons CO2/year")
    print(f"From Wood:       {wood_kwh * co2_wood / 1000:.2f} tons CO2/year (near neutral)")
    print(f"From Electricity:{electricity_kwh * co2_electricity / 1000:.2f} tons CO2/year")
    print(f"{'-' * 60}")
    print(f"Total:           {total_co2:.2f} tons CO2/year")
    print(f"Per Person:      {total_co2 / occupants:.2f} tons CO2/person/year")
    
    # Comparison with typical consumption
    print("\n" + "=" * 80)
    print("COMPARISON WITH TYPICAL VALUES")
    print("=" * 80)
    
    # Typical German villa consumption ranges
    typical_heating = (100, 180)  # kWh/m²/year for old villas
    typical_electricity = (20, 35)  # kWh/m²/year
    
    actual_heating = consumption['heating_kwh_m2']
    actual_electricity = consumption['electricity_kwh_m2']
    
    print("\nHeating:")
    print(f"  Your Villa:      {actual_heating:.1f} kWh/m²/year")
    print(f"  Typical Range:   {typical_heating[0]}-{typical_heating[1]} kWh/m²/year")
    if actual_heating < typical_heating[0]:
        print(f"  Status: ✓ Excellent - Below average!")
    elif actual_heating <= typical_heating[1]:
        print(f"  Status: ✓ Good - Within typical range")
    else:
        print(f"  Status: ⚠ High - Above average")
    
    print("\nElectricity:")
    print(f"  Your Villa:      {actual_electricity:.1f} kWh/m²/year")
    print(f"  Typical Range:   {typical_heating[0]}-{typical_heating[1]} kWh/m²/year")
    if actual_electricity < typical_electricity[0]:
        print(f"  Status: ✓ Excellent - Very efficient!")
    elif actual_electricity <= typical_electricity[1]:
        print(f"  Status: ✓ Good - Within typical range")
    else:
        print(f"  Status: ⚠ High - Consider energy efficiency measures")
    
    # Improvement recommendations
    print("\n" + "=" * 80)
    print("IMPROVEMENT RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n1. Heating System:")
    print("   • Consider replacing oil boiler with heat pump (COP ~3.0)")
    print(f"   • Potential savings: ~{heating_oil_kwh * (1 - 1/3.0):,.0f} kWh/year")
    print(f"   • CO2 reduction: ~{heating_oil_kwh * co2_oil / 1000 * 0.7:.1f} tons/year")
    
    print("\n2. Insulation:")
    print("   • Villa built in 1985 likely needs insulation upgrade")
    print("   • Roof insulation could save 15-30% heating energy")
    print(f"   • Potential savings: ~{total_heating_kwh * 0.20:,.0f} kWh/year")
    
    print("\n3. Renewable Energy:")
    print("   • Install solar PV panels (15-20 m²)")
    print(f"   • Could generate ~{villa_area * 0.1 * 150:,.0f} kWh/year")
    print(f"   • Cover ~{(villa_area * 0.1 * 150 / electricity_kwh * 100):.0f}% of electricity needs")
    
    print("\n4. Windows:")
    print("   • If single-glazed, upgrade to double/triple glazing")
    print("   • Can reduce heating demand by 10-15%")
    
    print("\n5. Wood Stove:")
    print("   • Modern wood stove is relatively efficient and low CO2")
    print("   • Ensure proper maintenance and dry wood for best efficiency")
    
    # Cost estimation
    print("\n" + "=" * 80)
    print("ANNUAL ENERGY COSTS (ESTIMATED)")
    print("=" * 80)
    
    # Typical Belgian energy prices (2024)
    price_oil_per_liter = 1.15  # EUR per liter
    price_electricity_per_kwh = 0.38  # EUR per kWh (Belgium has higher electricity prices)
    price_wood_per_m3 = 75.0  # EUR per m³
    
    cost_oil = heating_oil_liters * price_oil_per_liter
    cost_electricity = electricity_kwh * price_electricity_per_kwh
    cost_wood = wood_m3 * price_wood_per_m3
    total_cost = cost_oil + cost_electricity + cost_wood
    
    print(f"\nHeating Oil:   {heating_oil_liters:>6.0f} liters × €{price_oil_per_liter:.2f} = €{cost_oil:>8.2f}")
    print(f"Electricity:   {electricity_kwh:>6.0f} kWh    × €{price_electricity_per_kwh:.2f} = €{cost_electricity:>8.2f}")
    print(f"Wood:          {wood_m3:>6.1f} m³      × €{price_wood_per_m3:.2f} = €{cost_wood:>8.2f}")
    print(f"{'-' * 60}")
    print(f"Total:                                      €{total_cost:>8.2f}/year")
    print(f"Per Month:                                  €{total_cost / 12:>8.2f}")
    print(f"Per Person:                                 €{total_cost / occupants:>8.2f}/year")
    print(f"\nNote: Belgian energy prices (Wallonia region)")
    
    print("\n" + "=" * 80)


def main():
    """Run the villa simulation."""
    simulate_villa()
    
    print("\n" + "=" * 80)
    print("Simulation Complete!")
    print("=" * 80)
    print("\nKey Findings:")
    print("• The villa's energy consumption is tracked across multiple fuel sources")
    print("• Primary energy accounts for conversion efficiency and grid losses")
    print("• EPC rating provides standardized performance assessment")
    print("• Mixed fuel sources (oil + wood + electricity) are common in older villas")
    print("• Significant improvement potential through heat pump and insulation")
    print()


if __name__ == "__main__":
    main()
