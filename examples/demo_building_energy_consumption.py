"""
Demo: Building Energy Consumption and EPC Calculation

This example demonstrates:
1. Tracking energy consumption with various units
2. Converting different energy sources to kWh
3. Calculating primary energy consumption
4. Automatic EPC rating calculation
5. Energy performance analysis with system comparisons
"""

from datetime import datetime, timedelta
from core.domain.models.building import Building
from core.domain.models.energy_consumption import EnergyConsumption
from core.domain.enums.building_type import BuildingType
from core.domain.enums.heating import HeatingType
from core.domain.enums.hvac import HVACType
from core.domain.enums.ventilation import VentilationType
from core.domain.enums.countries import Country
from core.domain.enums.epc import EPCRating
from core.utils.energy_conversion import (
    convert_to_kwh,
    EnergyUnit,
    convert_hot_water_to_kwh,
    calculate_ventilation_energy,
    get_heating_system_efficiency,
)


def demo_basic_consumption_tracking():
    """Demo 1: Basic energy consumption tracking."""
    print("=" * 80)
    print("DEMO 1: Basic Energy Consumption Tracking")
    print("=" * 80)
    
    # Create a building with consumption data
    building = Building(
        id="office_001",
        name="Green Office Building",
        building_type=BuildingType.OFFICE,
        total_area=2500.0,  # m²
        country=Country.GERMANY,
        city="Berlin",
        heating_system=HeatingType.HEAT_PUMP,
        hvac_system=HVACType.VAV,
        ventilation_type=VentilationType.MECHANICAL,
        
        # Annual energy consumption (kWh/year)
        annual_heating_kwh=45000,
        annual_cooling_kwh=18000,
        annual_electricity_kwh=62000,
        annual_hot_water_kwh=12000,
        annual_ventilation_kwh=8500,
        
        # Renewable energy
        annual_solar_pv_kwh=15000,
        
        # Water consumption
        annual_water_m3=750,
    )
    
    print(f"\nBuilding: {building.name}")
    print(f"Type: {building.building_type.display_name}")
    print(f"Area: {building.total_area} m²")
    if building.city and building.country:
        print(f"Location: {building.city}, {building.country.value}")
    
    # Get energy summary
    energy_summary = building.get_energy_summary()
    
    print("\n--- Energy Consumption Summary ---")
    consumption = energy_summary["consumption"]
    print(f"Heating:      {consumption['heating_kwh']:>10,.0f} kWh  ({consumption['heating_kwh_m2']:>6.1f} kWh/m²)")
    print(f"Cooling:      {consumption['cooling_kwh']:>10,.0f} kWh  ({consumption['cooling_kwh_m2']:>6.1f} kWh/m²)")
    print(f"Electricity:  {consumption['electricity_kwh']:>10,.0f} kWh  ({consumption['electricity_kwh_m2']:>6.1f} kWh/m²)")
    print(f"Hot Water:    {consumption['hot_water_kwh']:>10,.0f} kWh  ({consumption['hot_water_kwh_m2']:>6.1f} kWh/m²)")
    print(f"Ventilation:  {consumption['ventilation_kwh']:>10,.0f} kWh  ({consumption['ventilation_kwh_m2']:>6.1f} kWh/m²)")
    print(f"{'-' * 60}")
    print(f"TOTAL:        {consumption['total_kwh']:>10,.0f} kWh  ({consumption['total_kwh_m2']:>6.1f} kWh/m²)")
    
    if "renewable_energy" in energy_summary:
        renewable = energy_summary["renewable_energy"]
        print(f"\nRenewable:    {renewable.get('total_renewable_kwh', 0):>10,.0f} kWh")
    
    # Calculate and display primary energy
    primary_energy = building.calculate_primary_energy_per_m2()
    print(f"\n--- Primary Energy Performance ---")
    print(f"Primary Energy: {primary_energy:.1f} kWh/m²/year")
    if building.country:
        print(f"Energy Type: {EPCRating.get_energy_type(building.country)}")
    
    # Calculate EPC rating
    epc_rating = building.calculate_epc_rating()
    if epc_rating:
        print(f"\n--- EPC Rating ---")
        print(f"Rating: {epc_rating.value}")
        print(f"Description: {epc_rating.description}")
        print(f"Numeric Score: {epc_rating.numeric_score}/8")
        
        # Show threshold range
        if building.country:
            threshold = epc_rating.get_threshold_range(building.country)
            if threshold:
                max_str = f"{threshold['max']:.0f}" if threshold['max'] else "∞"
                print(f"Range: {threshold['min']:.0f} - {max_str} kWh/m²/year ({threshold['energy_type']})")


def demo_unit_conversion():
    """Demo 2: Energy consumption with unit conversion."""
    print("\n" + "=" * 80)
    print("DEMO 2: Energy Consumption with Unit Conversion")
    print("=" * 80)
    
    # Example: Office building with mixed fuel sources
    print("\nScenario: Old office building with gas heating and electric cooling")
    
    # Natural gas consumption (measured in m³)
    gas_m3 = 15000  # m³ per year
    gas_kwh = convert_to_kwh(gas_m3, EnergyUnit.NATURAL_GAS_M3)
    print(f"\nNatural Gas: {gas_m3:,} m³/year")
    print(f"           = {gas_kwh:,.0f} kWh/year")
    
    # Heating oil consumption (measured in liters)
    oil_liters = 5000  # liters per year
    oil_kwh = convert_to_kwh(oil_liters, EnergyUnit.HEATING_OIL_LITERS)
    print(f"\nHeating Oil: {oil_liters:,} liters/year")
    print(f"           = {oil_kwh:,.0f} kWh/year")
    
    # Electricity (already in kWh)
    electricity_kwh = 85000
    print(f"\nElectricity: {electricity_kwh:,} kWh/year")
    
    # Hot water from liters consumed
    hot_water_liters = 120000  # liters per year
    hot_water_kwh = convert_hot_water_to_kwh(
        hot_water_liters,
        inlet_temp_celsius=10,
        outlet_temp_celsius=60,
        efficiency=0.85
    )
    print(f"\nHot Water: {hot_water_liters:,} liters/year")
    print(f"         = {hot_water_kwh:,.0f} kWh/year (energy to heat)")
    
    # Create building with converted values
    building = Building(
        id="office_002",
        name="Traditional Office Building",
        building_type=BuildingType.OFFICE,
        total_area=3500.0,
        country=Country.NETHERLANDS,
        heating_system=HeatingType.BOILER,
        
        annual_heating_kwh=gas_kwh + oil_kwh,
        annual_electricity_kwh=electricity_kwh,
        annual_hot_water_kwh=hot_water_kwh,
    )
    
    print(f"\n--- Total Building Consumption ---")
    primary_energy = building.calculate_primary_energy_per_m2()
    epc_rating = building.calculate_epc_rating()
    
    print(f"Primary Energy: {primary_energy:.1f} kWh/m²/year")
    print(f"EPC Rating: {epc_rating.value if epc_rating else 'N/A'} - {epc_rating.description if epc_rating else ''}")


def demo_detailed_consumption_tracking():
    """Demo 3: Detailed consumption tracking with EnergyConsumption model."""
    print("\n" + "=" * 80)
    print("DEMO 3: Detailed Consumption Tracking")
    print("=" * 80)
    
    # Track energy consumption over a specific period
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    consumption = EnergyConsumption(
        measurement_start=start_date,
        measurement_end=end_date,
        
        # Different heating sources
        heating_gas_m3=12000,  # Natural gas
        heating_district_kwh=8000,  # District heating
        
        # Electricity breakdown
        electricity_lighting_kwh=18000,
        electricity_appliances_kwh=25000,
        electricity_hvac_kwh=15000,
        
        # Cooling
        cooling_kwh=22000,
        
        # Hot water
        hot_water_liters=95000,
        
        # Ventilation
        ventilation_kwh=9500,
        
        # Renewable energy
        solar_pv_kwh=12000,
        
        # Water
        cold_water_m3=680,
        
        notes="Annual consumption for 2024"
    )
    
    print(f"\nMeasurement Period: {consumption.measurement_period_days} days")
    print(f"Start: {start_date.date()}")
    print(f"End: {end_date.date()}")
    
    summary = consumption.get_summary()
    print("\n--- Consumption Summary ---")
    print(f"Heating:      {summary['heating_kwh']:>10,.0f} kWh")
    print(f"Cooling:      {summary['cooling_kwh']:>10,.0f} kWh")
    print(f"Electricity:  {summary['electricity_kwh']:>10,.0f} kWh")
    print(f"Hot Water:    {summary['hot_water_kwh']:>10,.0f} kWh")
    print(f"Ventilation:  {summary['ventilation_kwh']:>10,.0f} kWh")
    print(f"{'-' * 40}")
    print(f"Total:        {summary['total_consumption_kwh']:>10,.0f} kWh")
    print(f"Renewable:    {summary['renewable_kwh']:>10,.0f} kWh")
    print(f"Net:          {summary['net_consumption_kwh']:>10,.0f} kWh")
    
    # Calculate primary energy for a building
    floor_area = 2800.0  # m²
    country = Country.AUSTRIA
    
    primary_energy = consumption.calculate_primary_energy(
        country=country,
        floor_area_m2=floor_area
    )
    
    print(f"\n--- Primary Energy Performance ---")
    print(f"Floor Area: {floor_area} m²")
    print(f"Country: {country.value}")
    print(f"Primary Energy: {primary_energy:.1f} kWh/m²/year")
    
    # Calculate EPC rating
    epc_rating = EPCRating.calculate_from_energy_consumption(
        energy_kwh_per_m2=primary_energy,
        country=country
    )
    
    if epc_rating:
        print(f"EPC Rating: {epc_rating.value} - {epc_rating.description}")


def demo_system_comparison():
    """Demo 4: Compare energy performance of different heating systems."""
    print("\n" + "=" * 80)
    print("DEMO 4: Heating System Comparison")
    print("=" * 80)
    
    # Building parameters
    building_area = 2000.0  # m²
    annual_heating_demand = 120000  # kWh thermal energy needed
    country = Country.GERMANY
    
    print(f"\nBuilding: {building_area} m² office in {country.value}")
    print(f"Annual Heating Demand: {annual_heating_demand:,} kWh")
    print(f"\n{'System':<20} {'Efficiency':<12} {'Energy Use':<15} {'CO2 Emissions'}")
    print("-" * 70)
    
    for heating_type in [HeatingType.BOILER, HeatingType.HEAT_PUMP, 
                         HeatingType.DISTRICT_HEATING, HeatingType.ELECTRIC_HEATING]:
        
        efficiency = heating_type.typical_efficiency
        
        # Energy consumption (input energy needed)
        if heating_type == HeatingType.HEAT_PUMP:
            # Heat pump has COP > 1
            energy_input = annual_heating_demand / efficiency
        else:
            # Other systems have efficiency < 1
            energy_input = annual_heating_demand / efficiency
        
        # CO2 emissions
        co2_total = (energy_input * heating_type.co2_intensity_kg_kwh) / 1000  # tons
        
        print(f"{heating_type.display_name:<20} {efficiency:>6.2f}       "
              f"{energy_input:>10,.0f} kWh  {co2_total:>8.1f} tons CO2")
    
    print("\n--- Analysis ---")
    print("• Heat pumps are most efficient (COP 3.0 means 1 kWh electricity → 3 kWh heat)")
    print("• Electric heating has lowest efficiency for heating")
    print("• CO2 emissions depend on both efficiency and fuel source")
    print("• Actual performance varies with climate, installation, and maintenance")


def demo_ventilation_energy_calculation():
    """Demo 5: Calculate ventilation energy consumption."""
    print("\n" + "=" * 80)
    print("DEMO 5: Ventilation Energy Calculation")
    print("=" * 80)
    
    # Building parameters
    floor_area = 3000.0  # m²
    ceiling_height = 3.0  # m
    air_changes_per_hour = 2.0
    operating_hours_per_day = 12
    operating_days_per_year = 250
    
    # Calculate air volume
    building_volume = floor_area * ceiling_height
    air_volume_m3_h = building_volume * air_changes_per_hour
    operating_hours = operating_hours_per_day * operating_days_per_year
    
    print(f"\nBuilding Parameters:")
    print(f"  Floor Area: {floor_area} m²")
    print(f"  Ceiling Height: {ceiling_height} m")
    print(f"  Volume: {building_volume:,} m³")
    print(f"  Air Changes: {air_changes_per_hour} ACH")
    print(f"  Air Flow Rate: {air_volume_m3_h:,} m³/h")
    print(f"  Operating Hours: {operating_hours:,} hours/year")
    
    # Compare ventilation types
    print(f"\n{'Ventilation Type':<25} {'Energy Use':<15} {'Energy Intensity'}")
    print("-" * 60)
    
    for vent_type in [VentilationType.NATURAL, VentilationType.MECHANICAL, 
                      VentilationType.MIXED_MODE]:
        
        if vent_type == VentilationType.NATURAL:
            energy_kwh = 0.0  # Natural ventilation uses no energy
        else:
            sfp = vent_type.specific_fan_power_w_per_l_s
            # Convert m³/h to L/s: 1 m³/h = 0.2778 L/s
            air_flow_l_s = air_volume_m3_h * 0.2778
            fan_power_w = air_flow_l_s * sfp
            energy_kwh = (fan_power_w / 1000) * operating_hours
        
        energy_per_m2 = energy_kwh / floor_area
        
        print(f"{vent_type.display_name:<25} {energy_kwh:>10,.0f} kWh  "
              f"{energy_per_m2:>6.1f} kWh/m²/year")
    
    print("\n--- Heat Recovery Benefits ---")
    
    # Calculate energy savings from heat recovery
    mechanical_vent = VentilationType.MECHANICAL
    hr_efficiency = mechanical_vent.heat_recovery_efficiency
    
    # Simplified calculation (actual would need climate data)
    heating_degree_days = 3000  # Typical for Central Europe
    air_density = 1.2  # kg/m³
    specific_heat = 1.005  # kJ/(kg·K)
    
    # Annual heat loss through ventilation without recovery
    ventilation_heat_loss = (air_volume_m3_h * operating_hours * 
                            air_density * specific_heat * 
                            heating_degree_days / 24) / 3600
    
    # Heat recovery savings
    heat_recovered = ventilation_heat_loss * hr_efficiency
    
    print(f"Heat Loss (no recovery): {ventilation_heat_loss:,.0f} kWh/year")
    print(f"Heat Recovery Efficiency: {hr_efficiency * 100:.0f}%")
    print(f"Heat Recovered: {heat_recovered:,.0f} kWh/year")
    print(f"Savings: {heat_recovered / floor_area:.1f} kWh/m²/year")


def main():
    """Run all demonstration examples."""
    print("\n" + "=" * 80)
    print("BUILDING ENERGY CONSUMPTION AND EPC CALCULATION DEMONSTRATIONS")
    print("=" * 80)
    
    demo_basic_consumption_tracking()
    demo_unit_conversion()
    demo_detailed_consumption_tracking()
    demo_system_comparison()
    demo_ventilation_energy_calculation()
    
    print("\n" + "=" * 80)
    print("All demonstrations completed!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("• Track consumption in multiple units (kWh, m³, liters, etc.)")
    print("• Automatic conversion to kWh for standardized analysis")
    print("• Primary energy accounts for production and distribution losses")
    print("• EPC ratings vary by country based on local standards")
    print("• System efficiency significantly impacts overall building performance")
    print("• Renewable energy generation reduces net consumption and EPC rating")
    print()


if __name__ == "__main__":
    main()
