"""
Script to pivot climate data, map columns to enum, and enable merging with indoor climate data for correlation/influence analysis (including lagged values).
"""
import pandas as pd
from pathlib import Path
from enum import Enum

# --- Define ClimateParameter Enum ---
class ClimateParameter(Enum):
    MEAN_RADIATION = "mean_radiation"
    # Add more as needed, e.g. WIND_SPEED, WIND_DIRECTION, TEMPERATURE, etc.
    # Example:
    # WIND_SPEED = "wind_speed"
    # WIND_DIRECTION = "wind_direction"

# --- Load and Pivot Climate Data ---
def load_and_pivot_climate_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    # Pivot so each parameter is a column, timestamp as index
    pivot_df = df.pivot_table(index="timestamp", columns="parameter", values="value")
    # Optionally convert index to datetime
    pivot_df.index = pd.to_datetime(pivot_df.index)
    # Map columns to enum
    pivot_df.columns = [ClimateParameter(col) if col in ClimateParameter._value2member_map_ else col for col in pivot_df.columns]
    return pivot_df

# --- Merge with Indoor Data and Correlation Analysis ---
def merge_and_analyze(indoor_df: pd.DataFrame, climate_df: pd.DataFrame, lags=[0, 1, 2]) -> pd.DataFrame:
    # Merge on timestamp (assume both have datetime index)
    merged = indoor_df.join(climate_df, how="left")
    # Add lagged climate columns
    for col in climate_df.columns:
        for lag in lags:
            if lag > 0:
                merged[f"{col.value}_lag{lag}" if isinstance(col, ClimateParameter) else f"{col}_lag{lag}"] = climate_df[col].shift(lag)
    return merged

# --- Example Usage ---
if __name__ == "__main__":
    climate_file = "data/climate/climate_data_floeng-skole_2024-01-01_to_2024-12-31.csv"
    indoor_file = "data/raw/concatenated/Fløng_Skole_0._sal_11_processed.csv"
    # Load climate data
    climate_pivot = load_and_pivot_climate_data(climate_file)
    print("Climate data (pivoted):")
    print(climate_pivot.head())
    # Load indoor data (example: CO2, temperature, etc.)
    indoor_df = pd.read_csv(indoor_file, index_col=0, parse_dates=True)
    # Merge and add lagged values
    merged_df = merge_and_analyze(indoor_df, climate_pivot, lags=[0, 1, 2, 3, 6])
    print("Merged indoor + climate data (with lags):")
    print(merged_df.head())
    # Example: correlation analysis
    corr = merged_df.corr()
    print("Correlation matrix:")
    print(corr)
    # Save merged data for further analysis
    merged_df.to_csv("merged_indoor_climate.csv")
