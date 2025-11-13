"""
Example: Using SpatialEntity with automated compute() methods

This example demonstrates the refactored SpatialEntity model with
automated compute methods for all standards and calculators.

Features demonstrated:
- SpatialEntity with timeseries data
- compute_en16798() - automated EN 16798-1 compliance
- compute_tail() - automated TAIL rating
- compute_ventilation() - automated ventilation estimation
- compute_occupancy() - automated occupancy detection
- compute_rc_model() - automated RC thermal modeling
- compute_all() - run all analyses at once
- Analysis result caching
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add refactored_service to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models.spatial_entities import SpatialEntity, SpatialEntityType


def generate_sample_data(hours=720):
    """Generate sample environmental data (30 days)."""
    import numpy as np

    # Timestamps
    start = datetime(2024, 1, 1)
    timestamps = [(start + timedelta(hours=i)).isoformat() for i in range(hours)]

    # Temperature (20-24°C)
    temperature = (22 + 2 * np.sin(2 * np.pi * np.arange(hours) / 24) +
                   np.random.normal(0, 0.5, hours)).tolist()

    # CO2 (400-1000 ppm with occupancy pattern)
    base_co2 = 400
    is_weekday = [((i // 24) % 7) < 5 for i in range(hours)]
    is_workhours = [(i % 24) >= 8 and (i % 24) <= 17 for i in range(hours)]
    is_occupied = [wd and wh for wd, wh in zip(is_weekday, is_workhours)]

    co2 = []
    for i in range(hours):
        if is_occupied[i]:
            co2.append(base_co2 + 400 + np.random.normal(0, 50))
        else:
            co2.append(base_co2 + np.random.normal(0, 20))

    # Humidity (30-50%)
    humidity = (40 + np.random.normal(0, 5, hours)).tolist()

    # Outdoor temperature
    outdoor_temp = (10 + 5 * np.sin(2 * np.pi * np.arange(hours) / 24) +
                    np.random.normal(0, 1, hours)).tolist()

    # Solar irradiance
    hour_of_day = [i % 24 for i in range(hours)]
    solar = [max(0, 800 * np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0
             for h in hour_of_day]

    return {
        'timestamps': timestamps,
        'temperature': temperature,
        'co2': co2,
        'humidity': humidity,
        'outdoor_temperature': outdoor_temp,
        'solar_irradiance': solar,
    }


def main():
    """Demonstrate SpatialEntity compute() methods."""
    print("\n" + "=" * 80)
    print("SPATIAL ENTITY AUTOMATED COMPUTE METHODS DEMO")
    print("=" * 80)

    # Step 1: Create SpatialEntity
    print("\n📍 Step 1: Creating SpatialEntity...")

    entity = SpatialEntity(
        id="room_101",
        name="Office 101",
        type=SpatialEntityType.ROOM,
        area_m2=25.0,
        volume_m3=75.0,
        window_area_m2=5.0,
        occupancy_count=3,
        room_type="office",
        ventilation_type="mechanical",
        pollution_level="low",
        construction_type="medium",
    )

    print(f"✓ Created {entity.name} (ID: {entity.id})")
    print(f"  Type: {entity.type.value}")
    print(f"  Area: {entity.area_m2} m²")
    print(f"  Volume: {entity.volume_m3} m³")

    # Step 2: Add timeseries data
    print("\n📊 Step 2: Adding timeseries data...")

    data = generate_sample_data(hours=720)  # 30 days

    for param in ['temperature', 'co2', 'humidity', 'outdoor_temperature', 'solar_irradiance']:
        entity.set_timeseries(param, data[param], data['timestamps'])

    print(f"✓ Added {len(data['timestamps'])} data points for:")
    for param in ['temperature', 'co2', 'humidity', 'outdoor_temperature', 'solar_irradiance']:
        if entity.has_parameter(param):
            print(f"  - {param}")

    # Step 3: Compute EN 16798-1
    print("\n🌡️  Step 3: Computing EN 16798-1 compliance...")

    en_result = entity.compute_en16798(
        categories=["II", "III"],
        season="heating"
    )

    if "error" not in en_result:
        print("✓ EN 16798-1 Results:")
        for category, data in en_result.items():
            print(f"  Category {category}: {data.get('compliance_rate', 0):.1f}% compliant")
    else:
        print(f"✗ {en_result['error']}")

    # Step 4: Compute TAIL rating
    print("\n🎯 Step 4: Computing TAIL rating...")

    tail_result = entity.compute_tail()

    if "error" not in tail_result:
        print(f"✓ TAIL Rating: {tail_result['overall_rating_label']} "
              f"({tail_result['overall_compliance_rate']:.1f}%)")
        print("  Categories:")
        for cat_name, cat_data in tail_result['categories'].items():
            print(f"    {cat_name}: {cat_data['rating_label']} "
                  f"({cat_data['compliance_rate']:.1f}%)")
    else:
        print(f"✗ {tail_result['error']}")

    # Step 5: Compute ventilation
    print("\n💨 Step 5: Estimating ventilation rate...")

    vent_result = entity.compute_ventilation()

    if "error" not in vent_result:
        print(f"✓ Ventilation Rate: {vent_result['ach']} ACH "
              f"({vent_result['category']})")
        print(f"  Confidence: R² = {vent_result['r_squared']}")
        if vent_result['ventilation_l_s']:
            print(f"  Flow rate: {vent_result['ventilation_l_s']} L/s")
    else:
        print(f"✗ {vent_result['error']}")

    # Step 6: Compute occupancy
    print("\n👥 Step 6: Detecting occupancy patterns...")

    occ_result = entity.compute_occupancy()

    if "error" not in occ_result:
        print(f"✓ Occupancy: {occ_result['estimated_occupants']} persons")
        print(f"  Occupancy rate: {occ_result['occupancy_rate']*100:.1f}%")
        print(f"  Typical hours: {occ_result['typical_hours']}")
        print(f"  Avg CO2 (occupied): {occ_result['avg_co2_occupied']:.0f} ppm")
        print(f"  Avg CO2 (unoccupied): {occ_result['avg_co2_unoccupied']:.0f} ppm")
    else:
        print(f"✗ {occ_result['error']}")

    # Step 7: Compute RC model
    print("\n🏠 Step 7: Running RC thermal model...")

    rc_result = entity.compute_rc_model(
        setpoint_heating=21.0,
        setpoint_cooling=25.0,
        model_type="2R2C"
    )

    if "error" not in rc_result:
        print("✓ RC Model Results:")
        metrics = rc_result['metrics']
        print(f"  Total heating: {metrics['total_heating_kwh']:.1f} kWh")
        print(f"  Total cooling: {metrics['total_cooling_kwh']:.1f} kWh")
        print(f"  U-value: {rc_result['u_value']:.3f} W/(m²·K)")
        print(f"  Time constant: {rc_result['time_constant_hours']:.1f} hours")
    else:
        print(f"✗ {rc_result['error']}")

    # Step 8: Compute all at once
    print("\n🚀 Step 8: Computing all analyses at once...")

    all_results = entity.compute_all()

    print("✓ All analyses completed:")
    for analysis_type, result in all_results.items():
        has_error = isinstance(result, dict) and "error" in result
        status = "✗ Error" if has_error else "✓ Success"
        print(f"  {status}: {analysis_type}")

    # Step 9: Demonstrate caching
    print("\n💾 Step 9: Demonstrating result caching...")

    cached_tail = entity.get_cached_result('tail')
    if cached_tail:
        print(f"✓ Retrieved cached TAIL result: {cached_tail['overall_rating_label']}")

    print("\n  Clearing cache...")
    entity.clear_cache()

    cached_tail_after = entity.get_cached_result('tail')
    print(f"  Cache after clear: {'Empty' if not cached_tail_after else 'Still has data'}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)

    print("\n📝 Summary of SpatialEntity compute() methods:")
    print("  • compute_en16798() - EN 16798-1 compliance (all categories)")
    print("  • compute_tail() - TAIL rating (T, A, I, L)")
    print("  • compute_ventilation() - Ventilation rate from CO2 decay")
    print("  • compute_occupancy() - Occupancy patterns from CO2")
    print("  • compute_rc_model() - RC thermal simulation")
    print("  • compute_all() - Run all available analyses")
    print("  • get_cached_result() - Retrieve cached results")
    print("  • clear_cache() - Clear analysis cache")

    print("\n✨ Key Benefits:")
    print("  ✓ Automated analysis based on available data")
    print("  ✓ Built-in result caching for performance")
    print("  ✓ Clean, simple API")
    print("  ✓ Scalable to thousands of entities")
    print("  ✓ Type-safe with Pydantic")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Note: This example requires numpy, pandas, scipy
    try:
        import numpy
        import pandas
        import scipy
        main()
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install numpy pandas scipy pythermalcomfort")
