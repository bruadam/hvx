#!/usr/bin/env python3
"""
Generate sample room data with varying EN16798-1 categories and TAIL ratings.

Creates realistic time-series data for rooms with different quality levels:
- Category I (Excellent): 95%+ compliance
- Category II (Good): 70-95% compliance
- Category III (Fair): 50-70% compliance
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_room_data(
    room_type: str,
    quality_level: str,
    start_date: datetime,
    days: int = 7,
    hourly: bool = True
) -> pd.DataFrame:
    """
    Generate time-series data for a room with specific quality level.
    
    Args:
        room_type: Type of room (office, conference, etc.)
        quality_level: "excellent" (Cat I), "good" (Cat II), "fair" (Cat III), "poor" (Cat IV)
        start_date: Start date for data
        days: Number of days to generate
        hourly: If True, hourly data; if False, 15-min intervals
        
    Returns:
        DataFrame with timestamp, temperature, co2, humidity, lux, voc, radon, daylight_factor columns
    """
    # Generate timestamps
    freq = 'h' if hourly else '15min'
    periods = days * 24 if hourly else days * 24 * 4
    timestamps = pd.date_range(start=start_date, periods=periods, freq=freq)
    
    # Initialize data as lists
    n_points = len(timestamps)
    
    # Determine target ranges based on quality level
    # EN16798-1 Category II thresholds (typical good performance):
    # Temperature: 20-24°C (heating), CO2: <1200ppm, Humidity: 25-60%
    # Lux: 300-500 (office work), VOC: <500 µg/m³, Radon: <100 Bq/m³
    # Daylight Factor: 2-5% (good), Acoustic: 35-45 dB(A)
    
    if quality_level == "excellent":
        # Category I - Very tight control, minimal excursions
        temp_base = 22.0
        temp_variation = 1.0  # ±1°C
        temp_excursion_prob = 0.02  # 2% chance of excursion
        
        co2_base = 600
        co2_variation = 150
        co2_excursion_prob = 0.02
        
        humidity_base = 45
        humidity_variation = 8
        
        lux_base = 450
        lux_variation = 50
        lux_excursion_prob = 0.02
        
        voc_base = 150
        voc_variation = 50
        voc_excursion_prob = 0.02
        
        radon_base = 40
        radon_variation = 15
        
        daylight_factor = 4.5
        daylight_variation = 0.5
        
    elif quality_level == "good":
        # Category II - Good control, some excursions
        temp_base = 22.0
        temp_variation = 1.5  # ±1.5°C
        temp_excursion_prob = 0.15  # 15% chance of excursion
        
        co2_base = 700
        co2_variation = 200
        co2_excursion_prob = 0.15
        
        humidity_base = 45
        humidity_variation = 12
        
        lux_base = 400
        lux_variation = 80
        lux_excursion_prob = 0.15
        
        voc_base = 250
        voc_variation = 100
        voc_excursion_prob = 0.15
        
        radon_base = 60
        radon_variation = 25
        
        daylight_factor = 3.5
        daylight_variation = 1.0
        
    elif quality_level == "fair":
        # Category III - Moderate control, frequent excursions
        temp_base = 22.0
        temp_variation = 2.5  # ±2.5°C
        temp_excursion_prob = 0.35  # 35% chance of excursion
        
        co2_base = 900
        co2_variation = 300
        co2_excursion_prob = 0.30
        
        humidity_base = 45
        humidity_variation = 18
        
        lux_base = 350
        lux_variation = 120
        lux_excursion_prob = 0.30
        
        voc_base = 400
        voc_variation = 150
        voc_excursion_prob = 0.30
        
        radon_base = 90
        radon_variation = 40
        
        daylight_factor = 2.5
        daylight_variation = 1.5
        
    else:  # poor
        # Category IV - Poor control, many excursions
        temp_base = 22.0
        temp_variation = 4.0  # ±4°C
        temp_excursion_prob = 0.60  # 60% chance of excursion
        
        co2_base = 1200
        co2_variation = 500
        co2_excursion_prob = 0.60
        
        humidity_base = 45
        humidity_variation = 25
        
        lux_base = 250
        lux_variation = 150
        lux_excursion_prob = 0.50
        
        voc_base = 700
        voc_variation = 300
        voc_excursion_prob = 0.50
        
        radon_base = 150
        radon_variation = 60
        
        daylight_factor = 1.5
        daylight_variation = 2.0
    
    # Generate temperature data with daily and occupancy patterns
    hour_of_day = timestamps.hour.to_numpy()
    day_of_week = timestamps.dayofweek.to_numpy()
    
    # Base temperature with daily cycle
    temp_daily_cycle = 1.0 * np.sin(2 * np.pi * hour_of_day / 24)
    
    # Occupancy pattern (higher during work hours on weekdays)
    is_workday = day_of_week < 5
    is_work_hours = (hour_of_day >= 8) & (hour_of_day < 18)
    occupancy_factor = np.where(is_workday & is_work_hours, 1.0, 0.3)
    
    # Temperature: base + daily cycle + random variation + excursions
    temperature = temp_base + temp_daily_cycle + np.random.normal(0, temp_variation * 0.3, n_points)
    
    # Add excursions (times when temp goes out of range)
    excursion_mask = np.random.random(n_points) < temp_excursion_prob
    excursion_direction = np.random.choice([-1, 1], size=sum(excursion_mask))
    excursion_magnitude = np.random.uniform(2, 4, size=sum(excursion_mask))
    temperature[excursion_mask] += excursion_direction * excursion_magnitude
    
    temperature_values = np.round(temperature, 2)
    
    # CO2: Base + occupancy effect + random variation + excursions
    co2_occupancy_effect = occupancy_factor * co2_variation
    co2 = co2_base + co2_occupancy_effect + np.random.normal(0, co2_variation * 0.2, n_points)
    
    # Add CO2 excursions during occupied hours
    co2_excursion_mask = (np.random.random(n_points) < co2_excursion_prob) & (occupancy_factor > 0.5)
    co2[co2_excursion_mask] += np.random.uniform(300, 800, size=sum(co2_excursion_mask))
    
    # Ensure CO2 stays above outdoor level (400 ppm) and reasonable max
    co2 = np.clip(co2, 400, 3000)
    co2_values = np.round(co2, 0)
    
    # Humidity: base + random variation + seasonal effect
    humidity = humidity_base + np.random.normal(0, humidity_variation * 0.4, n_points)
    
    # Humidity tends to vary more in certain conditions
    humidity_variation_mask = np.random.random(n_points) < 0.1
    humidity[humidity_variation_mask] += np.random.uniform(-15, 15, size=sum(humidity_variation_mask))
    
    # Ensure humidity stays in reasonable range
    humidity = np.clip(humidity, 15, 80)
    humidity_values = np.round(humidity, 2)
    
    # Lux (illuminance): varies by time of day and occupancy
    # Higher during work hours, lower at night
    lux_time_factor = np.where(is_work_hours, 1.0, 0.2)
    lux = lux_base * lux_time_factor + np.random.normal(0, lux_variation * 0.3, n_points)
    
    # Add lux excursions (lighting issues)
    lux_excursion_mask = np.random.random(n_points) < lux_excursion_prob
    lux_excursion_direction = np.random.choice([-1, 1], size=sum(lux_excursion_mask))
    lux[lux_excursion_mask] += lux_excursion_direction * np.random.uniform(50, 150, size=sum(lux_excursion_mask))
    
    # Ensure lux stays in reasonable range (0-1000 lux for offices)
    lux = np.clip(lux, 0, 1000)
    lux_values = np.round(lux, 1)
    
    # VOC (Volatile Organic Compounds): increases with occupancy
    voc_occupancy_effect = occupancy_factor * voc_variation
    voc = voc_base + voc_occupancy_effect + np.random.normal(0, voc_variation * 0.2, n_points)
    
    # Add VOC excursions (e.g., cleaning, equipment)
    voc_excursion_mask = np.random.random(n_points) < voc_excursion_prob
    voc[voc_excursion_mask] += np.random.uniform(100, 400, size=sum(voc_excursion_mask))
    
    # Ensure VOC stays in reasonable range (0-2000 µg/m³)
    voc = np.clip(voc, 0, 2000)
    voc_values = np.round(voc, 1)
    
    # Radon: relatively stable but with some daily variation
    radon = radon_base + np.random.normal(0, radon_variation * 0.4, n_points)
    
    # Radon tends to be higher at night when ventilation is reduced
    radon_night_increase = np.where(is_work_hours, 0, radon_variation * 0.5)
    radon += radon_night_increase
    
    # Ensure radon stays in reasonable range (0-400 Bq/m³)
    radon = np.clip(radon, 0, 400)
    radon_values = np.round(radon, 1)
    
    # Daylight Factor: varies throughout the day based on sun position
    # Higher during midday, lower morning/evening
    hour_factor = 1.0 - np.abs(hour_of_day - 12) / 12  # Peak at noon
    daylight = daylight_factor * hour_factor + np.random.normal(0, daylight_variation * 0.3, n_points)
    
    # Zero at night (before 6am, after 8pm)
    is_daytime = (hour_of_day >= 6) & (hour_of_day <= 20)
    daylight = np.where(is_daytime, daylight, 0)
    
    # Ensure daylight factor stays in reasonable range (0-10%)
    daylight = np.clip(daylight, 0, 10)
    daylight_values = np.round(daylight, 2)
    
    # Create DataFrame
    data = {
        'timestamp': timestamps,
        'temperature': temperature_values,
        'co2': co2_values,
        'humidity': humidity_values,
        'lux': lux_values,
        'voc': voc_values,
        'radon': radon_values,
        'daylight_factor': daylight_values
    }
    
    return pd.DataFrame(data)


def create_sample_dataset():
    """Create a comprehensive sample dataset with diverse room qualities."""
    
    output_dir = project_root / "data" / "samples" / "sample_varied_quality"
    
    # Clear and create output directory
    import shutil
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("  GENERATING SAMPLE ROOM DATA WITH VARIED QUALITY LEVELS")
    print("=" * 80)
    
    start_date = datetime(2024, 1, 1)
    
    # Define rooms with different quality levels
    rooms = [
        # Excellent quality rooms (Category I)
        {"name": "executive_office", "type": "office", "quality": "excellent", "description": "Executive office with premium climate control"},
        {"name": "high_tech_lab", "type": "laboratory", "quality": "excellent", "description": "High-tech laboratory with strict environmental control"},
        
        # Good quality rooms (Category II)
        {"name": "conference_room_a", "type": "conference", "quality": "good", "description": "Modern conference room with good HVAC"},
        {"name": "open_office_zone_1", "type": "office", "quality": "good", "description": "Open office with standard climate control"},
        {"name": "training_room", "type": "classroom", "quality": "good", "description": "Training room with adequate ventilation"},
        
        # Fair quality rooms (Category III)
        {"name": "meeting_room_b", "type": "meeting", "quality": "fair", "description": "Older meeting room, moderate control"},
        {"name": "open_office_zone_2", "type": "office", "quality": "fair", "description": "Busy open office, occasional comfort issues"},
        {"name": "cafeteria", "type": "cafeteria", "quality": "fair", "description": "Cafeteria with variable occupancy"},
        
        # Poor quality rooms (Category IV) - for comparison
        {"name": "storage_area", "type": "storage", "quality": "poor", "description": "Storage area with minimal climate control"},
    ]
    
    # Generate data for each room
    for room_info in rooms:
        room_name = room_info["name"]
        quality = room_info["quality"]
        
        print(f"\nGenerating: {room_name} ({quality} quality)")
        
        # Generate 7 days of hourly data
        df = generate_room_data(
            room_type=room_info["type"],
            quality_level=quality,
            start_date=start_date,
            days=7,
            hourly=True
        )
        
        # Save to CSV
        output_file = output_dir / f"{room_name}.csv"
        df.to_csv(output_file, index=False)
        
        # Print statistics
        print(f"  ✓ Saved {len(df)} records to {output_file.name}")
        print(f"    Temperature: {df['temperature'].min():.1f}°C - {df['temperature'].max():.1f}°C (mean: {df['temperature'].mean():.1f}°C)")
        print(f"    CO2: {df['co2'].min():.0f} - {df['co2'].max():.0f} ppm (mean: {df['co2'].mean():.0f} ppm)")
        print(f"    Humidity: {df['humidity'].min():.1f}% - {df['humidity'].max():.1f}% (mean: {df['humidity'].mean():.1f}%)")
        print(f"    Lux: {df['lux'].min():.0f} - {df['lux'].max():.0f} lx (mean: {df['lux'].mean():.0f} lx)")
        print(f"    VOC: {df['voc'].min():.0f} - {df['voc'].max():.0f} µg/m³ (mean: {df['voc'].mean():.0f} µg/m³)")
        print(f"    Radon: {df['radon'].min():.0f} - {df['radon'].max():.0f} Bq/m³ (mean: {df['radon'].mean():.0f} Bq/m³)")
        print(f"    Daylight Factor: {df['daylight_factor'].min():.1f} - {df['daylight_factor'].max():.1f}% (mean: {df['daylight_factor'].mean():.1f}%)")
    
    # Create metadata file
    import json
    metadata = {
        "dataset_name": "Sample Varied Quality Dataset",
        "description": "Sample dataset with rooms of varying EN16798-1 categories",
        "generated_date": datetime.now().isoformat(),
        "start_date": start_date.isoformat(),
        "days": 7,
        "frequency": "hourly",
        "rooms": rooms
    }
    
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Saved metadata to {metadata_file.name}")
    print(f"\n✅ Generated {len(rooms)} rooms in: {output_dir}")
    print("\nQuality Distribution:")
    print(f"  - Excellent (Cat I): {sum(1 for r in rooms if r['quality'] == 'excellent')} rooms")
    print(f"  - Good (Cat II): {sum(1 for r in rooms if r['quality'] == 'good')} rooms")
    print(f"  - Fair (Cat III): {sum(1 for r in rooms if r['quality'] == 'fair')} rooms")
    print(f"  - Poor (Cat IV): {sum(1 for r in rooms if r['quality'] == 'poor')} rooms")
    
    return output_dir


if __name__ == "__main__":
    output_dir = create_sample_dataset()
    print(f"\n{'=' * 80}")
    print("Sample data generation complete!")
    print(f"Data location: {output_dir}")
    print("=" * 80)
