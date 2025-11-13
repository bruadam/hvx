#!/usr/bin/env python3
"""Demonstration of building-dependent TAIL configuration."""

# Simple demo script showing how TAIL parameters depend on building types
def demo_tail_building_dependency():
    """Demonstrate TAIL parameter building type dependencies."""
    
    print("=== TAIL Building Type Dependencies Demo ===\n")
    
    # Mock the enums for demonstration
    print("Building Types supported by TAIL:")
    building_types = ["OFFICE", "HOTEL"]
    for bt in building_types:
        print(f"  - {bt}")
    print()
    
    print("Parameter configurations by building type:\n")
    
    # Demonstrate key differences between Office and Hotel
    configs = {
        "HUMIDITY": {
            "OFFICE": "Green: 30-50%, Yellow: 25-30% or 50-60%, Orange: 20-25% or 60-70%, Red: <20% or >70%",
            "HOTEL": "Green: 30-50%, Yellow: 25-30% or 50-60%, Orange: 20-25% or 60-70%, Red: <20% or >70%"
        },
        "NOISE": {
            "OFFICE": "Room-dependent: Small Office ≤30dB (Green), Open Office ≤35dB (Green)",
            "HOTEL": "Hotel Room: ≤25dB (Green), 25-30dB (Yellow), 30-35dB (Orange), >35dB (Red)"
        },
        "ILLUMINANCE": {
            "OFFICE": "Frequency-based: % time in 300-500 lux range",
            "HOTEL": "Frequency-based: % time ≥ 100 lux"
        },
        "CO2": {
            "OFFICE": "95th percentile: ≤970ppm (Green), 970-1220ppm (Yellow), 1220-1770ppm (Orange), >1770ppm (Red)",
            "HOTEL": "95th percentile: ≤970ppm (Green), 970-1220ppm (Yellow), 1220-1770ppm (Orange), >1770ppm (Red)"
        }
    }
    
    for param, building_configs in configs.items():
        print(f"{param}:")
        for building, config in building_configs.items():
            print(f"  {building}: {config}")
        print()
    
    print("Key Differences:")
    print("1. NOISE: Hotels have stricter thresholds (≤25dB vs ≤30-35dB for offices)")
    print("2. ILLUMINANCE: Different evaluation criteria (100 lux for hotels vs 300-500 lux range for offices)")
    print("3. Room Types: Offices distinguish between small/open offices, hotels focus on guest rooms")
    print("4. Most IAQ parameters (CO2, PM2.5, VOCs) use same WHO-based thresholds regardless of building type")
    print("\nTAIL Method Key Features:")
    print("- Building-specific thresholds for acoustic and lighting parameters")
    print("- Universal health-based thresholds for air quality parameters")
    print("- Frequency-based analysis for temperature and humidity")
    print("- Conservative approach: worst category determines overall rating")


if __name__ == "__main__":
    demo_tail_building_dependency()