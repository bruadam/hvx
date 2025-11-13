"""Quick test of climate data generation."""

from core.utils.synthetic_climate_data import generate_climate_data

print("Testing synthetic climate data generation...")

# Generate data
climate_data = generate_climate_data(
    start_date="2024-01-01",
    end_date="2024-01-31",
    freq="h",  # Use lowercase to avoid deprecation warning
    location_type="temperate",
    seed=42,
)

print(f"\n✓ Generated {len(climate_data)} records")
print(f"✓ Columns: {list(climate_data.columns)}")
print(f"\nFirst 24 hours:")
print(climate_data.head(24))
print(f"\nStatistics:")
print(climate_data.describe())
print("\n✓ Climate data generation works correctly!")
