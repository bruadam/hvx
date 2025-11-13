"""
Demo: EN 16798-1 Adaptive Thermal Comfort Model

This demo showcases the adaptive comfort model for naturally ventilated buildings,
where temperature thresholds dynamically adjust based on outdoor running mean temperature.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.analytics.calculators.en16798_calculator import (
    EN16798StandardCalculator,
    EN16798RoomMetadata,
)
from core.domain.enums.en16798_category import EN16798Category
from core.domain.enums.pollution_level import PollutionLevel
from core.domain.enums.ventilation import VentilationType


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def demo_running_mean_calculation():
    """Demonstrate running mean outdoor temperature calculation."""
    print_section("1. RUNNING MEAN OUTDOOR TEMPERATURE CALCULATION")
    
    print("\nThe running mean outdoor temperature (T_rm) is calculated using:")
    print("T_rm = (1-α) × [T_ed-1 + α×T_ed-2 + α²×T_ed-3 + ...]")
    print("where α = 0.8 (recommended for EN 16798-1)")
    
    # Example: Spring season with warming trend
    daily_temps_spring = [18.5, 17.2, 16.8, 15.5, 14.2, 13.8, 12.5]  # Most recent first
    t_rm_spring = EN16798StandardCalculator.calculate_running_mean_outdoor_temp(daily_temps_spring)
    
    print(f"\nSpring Example (warming trend):")
    print(f"  Daily outdoor temps (°C): {daily_temps_spring}")
    print(f"  Running mean T_rm: {t_rm_spring:.1f}°C")
    
    # Example: Summer season - warm
    daily_temps_summer = [25.2, 24.8, 26.1, 25.5, 24.2, 23.8, 24.5]
    t_rm_summer = EN16798StandardCalculator.calculate_running_mean_outdoor_temp(daily_temps_summer)
    
    print(f"\nSummer Example (warm period):")
    print(f"  Daily outdoor temps (°C): {daily_temps_summer}")
    print(f"  Running mean T_rm: {t_rm_summer:.1f}°C")
    
    # Example: Winter season - cold
    daily_temps_winter = [5.2, 4.8, 6.1, 5.5, 4.2, 3.8, 4.5]
    t_rm_winter = EN16798StandardCalculator.calculate_running_mean_outdoor_temp(daily_temps_winter)
    
    print(f"\nWinter Example (cold period):")
    print(f"  Daily outdoor temps (°C): {daily_temps_winter}")
    print(f"  Running mean T_rm: {t_rm_winter:.1f}°C")
    
    return t_rm_spring, t_rm_summer, t_rm_winter


def demo_adaptive_vs_fixed_thresholds():
    """Compare adaptive and fixed temperature thresholds."""
    print_section("2. ADAPTIVE vs FIXED TEMPERATURE THRESHOLDS")
    
    # Calculate running mean temps for different seasons
    t_rm_spring = 16.0  # Moderate
    t_rm_summer = 25.0  # Warm
    t_rm_winter = 5.0   # Cold (will fall back to fixed)
    
    print("\n" + "-" * 100)
    print("SPRING SEASON (T_rm = 16.0°C) - Adaptive Model Applied")
    print("-" * 100)
    
    for category in EN16798Category:
        # Fixed thresholds (mechanical)
        fixed_heating = EN16798StandardCalculator.get_temperature_thresholds(
            category, "heating", ventilation_type=VentilationType.MECHANICAL
        )
        
        # Adaptive thresholds (natural)
        adaptive = EN16798StandardCalculator.get_temperature_thresholds(
            category, "heating", outdoor_running_mean_temp=t_rm_spring,
            ventilation_type=VentilationType.NATURAL
        )
        
        print(f"\n{category.display_name}:")
        print(f"  Fixed (Mechanical):  {fixed_heating['lower']:.1f}°C - {fixed_heating['upper']:.1f}°C")
        if adaptive.get('adaptive_model'):
            print(f"  Adaptive (Natural):  {adaptive['lower']:.1f}°C - {adaptive['upper']:.1f}°C")
            print(f"  Comfort temp (T_comf): {adaptive['design']:.1f}°C")
        else:
            print(f"  Adaptive: Falls back to fixed thresholds")
    
    print("\n" + "-" * 100)
    print("SUMMER SEASON (T_rm = 25.0°C) - Adaptive Model Applied")
    print("-" * 100)
    
    for category in EN16798Category:
        # Fixed thresholds (mechanical)
        fixed_cooling = EN16798StandardCalculator.get_temperature_thresholds(
            category, "cooling", ventilation_type=VentilationType.MECHANICAL
        )
        
        # Adaptive thresholds (natural)
        adaptive = EN16798StandardCalculator.get_temperature_thresholds(
            category, "cooling", outdoor_running_mean_temp=t_rm_summer,
            ventilation_type=VentilationType.NATURAL
        )
        
        print(f"\n{category.display_name}:")
        print(f"  Fixed (Mechanical):  {fixed_cooling['lower']:.1f}°C - {fixed_cooling['upper']:.1f}°C")
        if adaptive.get('adaptive_model'):
            print(f"  Adaptive (Natural):  {adaptive['lower']:.1f}°C - {adaptive['upper']:.1f}°C")
            print(f"  Comfort temp (T_comf): {adaptive['design']:.1f}°C")
        else:
            print(f"  Adaptive: Falls back to fixed thresholds")
    
    print("\n" + "-" * 100)
    print("WINTER SEASON (T_rm = 5.0°C) - Outside Valid Range, Falls Back to Fixed")
    print("-" * 100)
    print("\nNote: Adaptive model is valid for 10°C ≤ T_rm ≤ 30°C")
    print("Below this range, fixed heating thresholds are used.")


def demo_naturally_ventilated_office():
    """Demo naturally ventilated office with adaptive comfort."""
    print_section("3. NATURALLY VENTILATED OFFICE - ADAPTIVE COMFORT")
    
    # Running mean outdoor temperature for a mild spring day
    t_rm = 18.0  # °C
    
    # Room metadata for naturally ventilated office
    room_metadata = EN16798RoomMetadata(
        room_type="office",
        floor_area=25.0,  # m²
        volume=75.0,  # m³
        occupancy_count=2,
        ventilation_type=VentilationType.NATURAL,
        pollution_level=PollutionLevel.LOW,
        target_category=EN16798Category.CATEGORY_II,
    )
    
    print(f"\nRoom Configuration:")
    print(f"  Type: {room_metadata.room_type}")
    print(f"  Floor area: {room_metadata.floor_area} m²")
    print(f"  Occupancy: {room_metadata.occupancy_count} persons")
    print(f"  Ventilation: {room_metadata.ventilation_type.value}")
    print(f"  Outdoor running mean temp: {t_rm}°C")
    
    print(f"\nAdaptive Temperature Thresholds (T_rm = {t_rm}°C):")
    print(f"  Comfort temperature: T_comf = 0.33 × {t_rm} + 18.8 = {0.33 * t_rm + 18.8:.1f}°C")
    
    # Get thresholds for all categories
    all_thresholds = EN16798StandardCalculator.get_all_thresholds_for_room(
        room_metadata, outdoor_running_mean_temp=t_rm
    )
    
    for category, thresholds in all_thresholds.items():
        temp_heating = thresholds['temperature_heating']
        print(f"\n{category.display_name}:")
        if temp_heating.get('adaptive_model'):
            print(f"  Acceptable range: {temp_heating['lower']:.1f}°C - {temp_heating['upper']:.1f}°C")
            print(f"  Design/Comfort: {temp_heating['design']:.1f}°C")
        else:
            print(f"  Range: {temp_heating['lower']:.1f}°C - {temp_heating['upper']:.1f}°C (fixed)")
    
    # Test different measured temperatures
    print("\n" + "-" * 100)
    print("CATEGORY ACHIEVEMENT FOR DIFFERENT INDOOR TEMPERATURES")
    print("-" * 100)
    
    test_temps = [20.0, 22.0, 24.0, 26.0, 28.0]
    
    for temp in test_temps:
        measured = {
            "temperature": temp,
            "co2": 800,  # Good air quality
            "humidity": 45,  # Good humidity
        }
        
        result = EN16798StandardCalculator.determine_achieved_category(
            room_metadata, measured, outdoor_running_mean_temp=t_rm
        )
        
        achieved = result['achieved_category_name']
        print(f"\nIndoor temp: {temp}°C → {achieved}")
        
        # Show which categories passed temperature test
        for cat_key, cat_details in result['compliance_details'].items():
            if 'temperature' in cat_details['details']:
                temp_compliant = cat_details['details']['temperature']['compliant']
                status = "✓" if temp_compliant else "✗"
                print(f"  {status} {cat_key.display_name}")


def demo_mixed_mode_building():
    """Demo mixed-mode building switching between adaptive and fixed thresholds."""
    print_section("4. MIXED-MODE BUILDING - SEASONAL ADAPTATION")
    
    print("\nMixed-mode buildings can switch between natural ventilation")
    print("(adaptive comfort) and mechanical conditioning (fixed thresholds).")
    
    room_metadata = EN16798RoomMetadata(
        room_type="office",
        floor_area=30.0,
        volume=90.0,
        occupancy_count=3,
        ventilation_type=VentilationType.MIXED_MODE,
        pollution_level=PollutionLevel.LOW,
        target_category=EN16798Category.CATEGORY_II,
    )
    
    # Scenarios for different seasons
    scenarios = [
        {"season": "Spring (Mild)", "t_rm": 16.0, "mode": "Natural"},
        {"season": "Summer (Hot)", "t_rm": 28.0, "mode": "Natural"},
        {"season": "Winter (Cold)", "t_rm": 3.0, "mode": "Mechanical (T_rm < 10°C)"},
    ]
    
    for scenario in scenarios:
        t_rm = scenario['t_rm']
        
        print(f"\n{'-' * 100}")
        print(f"{scenario['season']} - T_rm = {t_rm}°C - Mode: {scenario['mode']}")
        print(f"{'-' * 100}")
        
        cat_ii_thresh = EN16798StandardCalculator.get_temperature_thresholds(
            EN16798Category.CATEGORY_II,
            outdoor_running_mean_temp=t_rm,
            ventilation_type=VentilationType.MIXED_MODE
        )
        
        if cat_ii_thresh.get('adaptive_model'):
            print(f"  Using Adaptive Model:")
            print(f"  Comfort temperature: {cat_ii_thresh['design']:.1f}°C")
            print(f"  Acceptable range: {cat_ii_thresh['lower']:.1f}°C - {cat_ii_thresh['upper']:.1f}°C")
        else:
            print(f"  Using Fixed Thresholds (outside adaptive range):")
            print(f"  Range: {cat_ii_thresh['lower']:.1f}°C - {cat_ii_thresh['upper']:.1f}°C")


def main():
    """Run all adaptive comfort demos."""
    print("\n" + "=" * 100)
    print("  EN 16798-1 ADAPTIVE THERMAL COMFORT MODEL - COMPREHENSIVE DEMO")
    print("=" * 100)
    print("\nThis demo shows how EN 16798-1 uses dynamic temperature thresholds")
    print("for naturally ventilated buildings based on outdoor running mean temperature.")
    
    try:
        # Demo 1: Running mean calculation
        demo_running_mean_calculation()
        
        # Demo 2: Adaptive vs fixed comparison
        demo_adaptive_vs_fixed_thresholds()
        
        # Demo 3: Naturally ventilated office
        demo_naturally_ventilated_office()
        
        # Demo 4: Mixed-mode building
        demo_mixed_mode_building()
        
        print("\n" + "=" * 100)
        print("  KEY TAKEAWAYS")
        print("=" * 100)
        print("\n1. ADAPTIVE MODEL (Natural/Mixed-Mode Ventilation):")
        print("   - Comfort temp: T_comf = 0.33 × T_rm + 18.8")
        print("   - Valid for: 10°C ≤ T_rm ≤ 30°C")
        print("   - Category I: ±2°C from comfort temp")
        print("   - Category II: ±3°C from comfort temp")
        print("   - Category III: ±4°C from comfort temp")
        print("   - Category IV: ±5°C from comfort temp")
        
        print("\n2. FIXED MODEL (Mechanical Conditioning):")
        print("   - Uses standard heating/cooling season thresholds")
        print("   - Does not depend on outdoor temperature")
        
        print("\n3. RUNNING MEAN OUTDOOR TEMPERATURE:")
        print("   - Exponentially weighted average of past daily temps")
        print("   - Default α = 0.8 (more weight on recent days)")
        print("   - Minimum 7 days of data recommended")
        
        print("\n" + "=" * 100)
        print("  DEMO COMPLETE")
        print("=" * 100)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
