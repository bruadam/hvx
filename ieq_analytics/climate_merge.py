"""
IEQ Analytics Climate Merge Module

Provides functions to pivot climate data, map columns to an enum, merge with indoor climate data, and perform correlation/influence analysis with lagged values.
"""
import pandas as pd
from enum import Enum

class ClimateParameter(Enum):
    MEAN_RADIATION = "mean_radiation"
    # Extend with more parameters as needed

def load_and_pivot_climate_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    pivot_df = df.pivot_table(index="timestamp", columns="parameter", values="value")
    pivot_df.index = pd.to_datetime(pivot_df.index)
    pivot_df.columns = [ClimateParameter(col) if col in ClimateParameter._value2member_map_ else col for col in pivot_df.columns]
    return pivot_df

def merge_and_analyze(indoor_df: pd.DataFrame, climate_df: pd.DataFrame, lags=[0, 1, 2]) -> pd.DataFrame:
    merged = indoor_df.join(climate_df, how="left")
    for col in climate_df.columns:
        for lag in lags:
            if lag > 0:
                merged[f"{col.value}_lag{lag}" if isinstance(col, ClimateParameter) else f"{col}_lag{lag}"] = climate_df[col].shift(lag)
    return merged

def correlation_analysis(merged_df: pd.DataFrame) -> pd.DataFrame:
    return merged_df.corr()

# Example usage (can be removed or adapted for CLI)
if __name__ == "__main__":
    climate_file = "../data/climate/climate_data_floeng-skole_2024-01-01_to_2024-12-31.csv"
    indoor_file = "../data/raw/concatenated/Fløng_Skole_0._sal_11_processed.csv"
    climate_pivot = load_and_pivot_climate_data(climate_file)
    print("Climate data (pivoted):")
    print(climate_pivot.head())
    indoor_df = pd.read_csv(indoor_file, index_col=0, parse_dates=True)
    merged_df = merge_and_analyze(indoor_df, climate_pivot, lags=[0, 1, 2, 3, 6])
    print("Merged indoor + climate data (with lags):")
    print(merged_df.head())
    corr = correlation_analysis(merged_df)
    print("Correlation matrix:")
    print(corr)
    merged_df.to_csv("merged_indoor_climate.csv")
