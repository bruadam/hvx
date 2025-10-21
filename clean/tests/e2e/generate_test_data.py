#!/usr/bin/env python3
"""Generate test datasets with specific EN 16798-1 category compliance."""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import yaml

def generate_yearly_data(
    room_name: str,
    compliance_config: dict,
    start_date: str = "2024-01-01",
    output_dir: Path = Path("data/test_rooms"),
) -> Path:
    """
    Generate a year of hourly room data with specific compliance levels.
    
    Args:
        room_name: Name of the room
        compliance_config: Dict with compliance levels per parameter:
            {
                'temperature': 'cat_i',    # 95%+ compliant to cat_i thresholds
                'co2': 'cat_ii',           # 95%+ compliant to cat_ii thresholds
                'humidity': 'cat_iii',     # 95%+ compliant to cat_iii thresholds
            }
        start_date: Start date for generated data
        output_dir: Directory to save CSV
    
    Returns:
        Path to generated CSV file
    """
    # EN 16798-1 thresholds (from config)
    thresholds = {
        'temperature': {
            'cat_i': {'lower': 21, 'upper': 23},      # Strictest
            'cat_ii': {'lower': 20, 'upper': 24},     # Medium
            'cat_iii': {'lower': 19, 'upper': 25},    # Loosest
        },
        'co2': {
            'cat_i': {'upper': 950},      # Strictest (ppm)
            'cat_ii': {'upper': 1200},    # Medium
            'cat_iii': {'upper': 1500},   # Loosest
        },
        'humidity': {
            'cat_i': {'lower': 30, 'upper': 50},      # Strictest (%)
            'cat_ii': {'lower': 25, 'upper': 60},     # Medium
            'cat_iii': {'lower': 20, 'upper': 70},    # Loosest
        },
    }
    
    # Generate hourly timestamps for full year
    start = pd.Timestamp(start_date)
    end = start + timedelta(days=365)
    timestamps = pd.date_range(start, end, freq='h')[:-1]  # 8760 hours
    
    data = {'timestamp': timestamps}
    
    # Generate data for each parameter
    for param, target_category in compliance_config.items():
        if param == 'temperature':
            base_value = 22  # Default comfortable temperature
            target_thresholds = thresholds['temperature'][target_category]
        elif param == 'co2':
            base_value = 600  # Default CO2 level (ppm)
            target_thresholds = thresholds['co2'][target_category]
        elif param == 'humidity':
            base_value = 45  # Default humidity (%)
            target_thresholds = thresholds['humidity'][target_category]
        else:
            continue
        
        # Generate data that is 95% compliant to target category
        lower = target_thresholds.get('lower', None)
        upper = target_thresholds.get('upper', None)
        
        # 95% compliant: 95% within threshold, 5% violating
        num_points = len(timestamps)
        compliant_count = int(num_points * 0.95)
        violating_count = num_points - compliant_count
        
        # Generate compliant values (within bounds)
        if lower is not None and upper is not None:
            compliant_vals = np.random.uniform(lower + 0.5, upper - 0.5, compliant_count)
            # Violating: pick randomly above or below
            violating_vals = []
            for _ in range(violating_count):
                if np.random.random() < 0.5:
                    # Too low
                    violating_vals.append(np.random.uniform(lower - 5, lower - 0.1))
                else:
                    # Too high
                    violating_vals.append(np.random.uniform(upper + 0.1, upper + 5))
            violating_vals = np.array(violating_vals)
        elif upper is not None:
            # Only upper limit (like CO2)
            compliant_vals = np.random.uniform(base_value - 100, upper - 5, compliant_count)  # type: ignore
            violating_vals = np.random.uniform(upper + 5, upper + 300, violating_count)  # type: ignore
        else:
            # Only lower limit
            compliant_vals = np.random.uniform(lower + 5, lower + 100, compliant_count)  # type: ignore
            violating_vals = np.random.uniform(lower - 300, lower - 5, violating_count)  # type: ignore
        
        # Combine and shuffle
        all_vals = np.concatenate([compliant_vals, violating_vals])
        np.random.shuffle(all_vals)
        
        # Add very small daily variation (only 0.1 to avoid pushing over thresholds)
        hour_of_day = timestamps.hour.values
        daily_variation = 0.1 * np.sin(2 * np.pi * hour_of_day / 24)  # Very small variation
        all_vals = all_vals + daily_variation
        
        data[param] = all_vals
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{room_name}.csv"
    df.to_csv(output_file, index=False)
    
    return output_file

# Generate test rooms with different compliance profiles
test_rooms = {
    "room_cat_i_all": {
        "description": "Cat I compliant in all parameters",
        "compliance": {
            "temperature": "cat_i",
            "co2": "cat_i",
            "humidity": "cat_i",
        },
    },
    "room_cat_i_temp_cat_iii_co2": {
        "description": "Cat I for temp, Cat III for CO2",
        "compliance": {
            "temperature": "cat_i",
            "co2": "cat_iii",
            "humidity": "cat_i",
        },
    },
    "room_cat_ii_all": {
        "description": "Cat II compliant in all parameters",
        "compliance": {
            "temperature": "cat_ii",
            "co2": "cat_ii",
            "humidity": "cat_ii",
        },
    },
    "room_cat_ii_temp_cat_iii_other": {
        "description": "Cat II for temp, Cat III for CO2 and humidity",
        "compliance": {
            "temperature": "cat_ii",
            "co2": "cat_iii",
            "humidity": "cat_iii",
        },
    },
    "room_cat_iii_all": {
        "description": "Cat III (basic) compliant in all",
        "compliance": {
            "temperature": "cat_iii",
            "co2": "cat_iii",
            "humidity": "cat_iii",
        },
    },
}

print("Generating test datasets with specific compliance levels...")
print("=" * 80)

generated_files = {}
for room_name, room_config in test_rooms.items():
    output_file = generate_yearly_data(room_name, room_config["compliance"])
    generated_files[room_name] = output_file
    print(f"\n✓ {room_name}")
    print(f"  Description: {room_config['description']}")
    print(f"  Generated: {output_file}")
    print(f"  Compliance profile:")
    for param, category in room_config["compliance"].items():
        print(f"    - {param}: {category}")
    
    # Show sample statistics
    df = pd.read_csv(output_file)
    print(f"  Data shape: {df.shape[0]} hourly records")
    for col in ['temperature', 'co2', 'humidity']:
        if col in df.columns:
            print(f"    {col}: {df[col].min():.1f} - {df[col].max():.1f} (mean: {df[col].mean():.1f})")

print("\n" + "=" * 80)
print(f"Generated {len(generated_files)} test rooms in: data/test_rooms/")
print("\nNext: Run analysis on these rooms to verify compliance ranking")
