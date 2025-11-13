#!/usr/bin/env python3
"""Demonstration of hierarchical TAIL configuration system."""

# Mock the configuration system for demonstration purposes
def demo_hierarchical_tail_config():
    """Demonstrate how the hierarchical TAIL configuration system works."""
    
    print("=== Hierarchical TAIL Configuration System Demo ===\n")
    
    print("Configuration Priority: Room Type > Building Type > Default\n")
    
    # Example configurations at different levels
    configs = {
        "default": {
            "noise": {
                "calculation_method": "percentile",
                "percentile": 5,
                "thresholds": {
                    "green": {"max": 35},
                    "yellow": {"min": 35, "max": 40},
                    "orange": {"min": 40, "max": 45},
                    "red": {"min": 45}
                }
            },
            "illuminance": {
                "calculation_method": "frequency_range",
                "target_range": {"min": 300, "max": 500},
                "thresholds": {
                    "green": {"frequency_percentage": 60},
                    "yellow": {"frequency_percentage": 40},
                    "orange": {"frequency_percentage": 10},
                    "red": {"frequency_percentage": 0}
                }
            }
        },
        
        "building_overrides": {
            "hotel": {
                "illuminance": {
                    "calculation_method": "frequency_threshold",
                    "threshold": 100,
                    "thresholds": {
                        "green": {"frequency_percentage": 0},
                        "yellow": {"frequency_percentage": 50},
                        "orange": {"frequency_percentage": 90},
                        "red": {"frequency_percentage": 100}
                    }
                }
            }
        },
        
        "room_overrides": {
            "small_office": {
                "noise": {
                    "thresholds": {
                        "green": {"max": 30},
                        "yellow": {"min": 30, "max": 35},
                        "orange": {"min": 35, "max": 40},
                        "red": {"min": 40}
                    }
                }
            },
            "hotel_room": {
                "noise": {
                    "thresholds": {
                        "green": {"max": 25},
                        "yellow": {"min": 25, "max": 30},
                        "orange": {"min": 30, "max": 35},
                        "red": {"min": 35}
                    }
                }
            }
        }
    }
    
    # Demonstration scenarios
    scenarios = [
        {
            "name": "Small Office in Office Building - Noise Parameter",
            "parameter": "noise",
            "building_type": "office",
            "room_type": "small_office",
            "explanation": "Room-specific override takes precedence (stricter 30dB vs default 35dB)"
        },
        {
            "name": "Hotel Room - Noise Parameter", 
            "parameter": "noise",
            "building_type": "hotel",
            "room_type": "hotel_room",
            "explanation": "Room-specific override (25dB) - strictest for guest comfort"
        },
        {
            "name": "Hotel Building - Illuminance Parameter",
            "parameter": "illuminance", 
            "building_type": "hotel",
            "room_type": None,
            "explanation": "Building-specific override (100 lux threshold vs 300-500 lux range)"
        },
        {
            "name": "Default Configuration - Any Parameter",
            "parameter": "noise",
            "building_type": None,
            "room_type": None,
            "explanation": "Default configuration when no overrides exist"
        }
    ]
    
    def get_effective_config(parameter, building_type=None, room_type=None):
        """Simulate the hierarchical configuration loading."""
        # Start with default
        config = configs["default"][parameter].copy()
        
        # Apply building override
        if building_type and building_type in configs["building_overrides"]:
            building_override = configs["building_overrides"][building_type].get(parameter, {})
            config = deep_merge(config, building_override)
        
        # Apply room override (highest priority)
        if room_type and room_type in configs["room_overrides"]:
            room_override = configs["room_overrides"][room_type].get(parameter, {})
            config = deep_merge(config, room_override)
        
        return config
    
    def deep_merge(base, override):
        """Simple deep merge for demo."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    # Show each scenario
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"Parameter: {scenario['parameter']}")
        print(f"Building Type: {scenario['building_type'] or 'None'}")
        print(f"Room Type: {scenario['room_type'] or 'None'}")
        print(f"Explanation: {scenario['explanation']}")
        
        config = get_effective_config(
            scenario['parameter'],
            scenario['building_type'], 
            scenario['room_type']
        )
        
        print("Effective Configuration:")
        if scenario['parameter'] == 'noise' and 'thresholds' in config:
            thresholds = config['thresholds']
            print(f"  Green: ≤{thresholds['green']['max']}dB")
            if 'min' in thresholds['yellow']:
                print(f"  Yellow: {thresholds['yellow']['min']}-{thresholds['yellow']['max']}dB")
            if 'min' in thresholds['orange']:
                print(f"  Orange: {thresholds['orange']['min']}-{thresholds['orange']['max']}dB")
            print(f"  Red: ≥{thresholds['red']['min']}dB")
        elif scenario['parameter'] == 'illuminance':
            if config.get('calculation_method') == 'frequency_threshold':
                print(f"  Method: Frequency below {config['threshold']} lux")
            else:
                print(f"  Method: Frequency in {config['target_range']['min']}-{config['target_range']['max']} lux range")
        
        print("-" * 60)
    
    print("\nKey Benefits of Hierarchical Configuration:")
    print("1. ✅ Flexibility: Different thresholds for different contexts")
    print("2. ✅ Maintainability: Override only what's different") 
    print("3. ✅ Validation: Enum-based validation prevents invalid configurations")
    print("4. ✅ Extensibility: Easy to add new building/room types")
    print("5. ✅ Consistency: Default values ensure nothing is undefined")
    
    print("\nConfiguration File Structure:")
    print("📁 config/")
    print("  📄 tail_schema.yaml              # Default configuration")
    print("  📁 overrides/")
    print("    📁 building_types/")
    print("      📄 office.yaml              # Office-specific overrides")
    print("      📄 hotel.yaml               # Hotel-specific overrides")
    print("    📁 room_types/") 
    print("      📄 small_office.yaml        # Small office overrides")
    print("      📄 open_office.yaml         # Open office overrides")
    print("      📄 hotel_room.yaml          # Hotel room overrides")


if __name__ == "__main__":
    demo_hierarchical_tail_config()