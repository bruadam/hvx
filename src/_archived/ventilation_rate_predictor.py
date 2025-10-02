"""
VentilationRatePredictor Module

This module identifies CO2 decay periods in IEQ data, filters them to outside opening hours (8-17), and predicts ventilation rate using the gas decay function.
"""

import pandas as pd
import numpy as np
from datetime import time
from typing import List, Dict, Any, Optional
from tabulate import tabulate
from pathlib import Path

class VentilationRatePredictor:
    """Predicts ventilation rate based on CO2 decay periods."""

    def __init__(self, co2_col: str = "co2"):
        self.co2_col = co2_col

    def find_decay_periods(self, data: pd.DataFrame, min_length: int = 5) -> List[Dict[str, Any]]:
        """Identify periods where CO2 concentration decays (monotonically decreases)."""
        decay_periods = []
        if self.co2_col not in data.columns:
            return decay_periods
        co2 = data[self.co2_col].dropna()
        idx = co2.index
        values = co2.values
        start = None
        for i in range(1, len(values)):
            if values[i] < values[i-1]:
                if start is None:
                    start = i-1
            else:
                if start is not None and i - start >= min_length:
                    decay_periods.append({
                        "start": idx[start],
                        "end": idx[i-1],
                        "values": values[start:i]
                    })
                start = None
        # Handle last period
        if start is not None and len(values) - start >= min_length:
            decay_periods.append({
                "start": idx[start],
                "end": idx[-1],
                "values": values[start:]
            })
        return decay_periods

    def filter_outside_opening_hours(self, periods: List[Dict[str, Any]], data: pd.DataFrame, start_hour: int = 8, end_hour: int = 17) -> List[Dict[str, Any]]:
        """Filter decay periods to those outside opening hours (8-17)."""
        filtered = []
        for period in periods:
            start_time = period["start"].time() if hasattr(period["start"], "time") else pd.to_datetime(period["start"]).time()
            end_time = period["end"].time() if hasattr(period["end"], "time") else pd.to_datetime(period["end"]).time()
            if (start_time < time(start_hour) or start_time >= time(end_hour)) and (end_time < time(start_hour) or end_time >= time(end_hour)):
                filtered.append(period)
        return filtered

    def predict_ventilation_rate(self, period: Dict[str, Any], dt_minutes: float = 60.0) -> Optional[float]:
        """Predict ventilation rate (ACH) using the gas decay function for a decay period.
        Assumes time interval between measurements is dt_minutes (default 60 min).
        Returns air changes per hour (ACH).
        """
        values = period["values"]
        if len(values) < 2 or np.any(np.array(values) <= 0):
            return None
        c0 = values[0]
        c1 = values[-1]
        t = len(values) * dt_minutes / 60.0  # hours
        if c1 >= c0:
            return None
        # Gas decay: C(t) = C0 * exp(-ACH * t) => ACH = -ln(C(t)/C0)/t
        try:
            ach = -np.log(c1 / c0) / t
            return round(ach, 5)
        except Exception:
            return None

    def analyze(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Full pipeline: find decay periods, filter outside opening hours, predict ventilation rate."""
        decay_periods = self.find_decay_periods(data)
        filtered_periods = self.filter_outside_opening_hours(decay_periods, data)
        results = []
        for period in filtered_periods:
            ach = self.predict_ventilation_rate(period)
            results.append({
                "start": period["start"],
                "end": period["end"],
                "ventilation_rate_ach": ach,
                "values": period["values"]
            })
        return results

    def summarize_ach_statistics(self, results, txt_path=None, ask_save=True, recommended_ach=2.0):
        """Print and optionally save ACH statistics and table. Weighs by number of data points in each period. Calculates a probability for confidence. Compares ACH to standard recommendation."""
        # Collect ACH values and weights
        ach_values = []
        weights = []
        table_rows = []
        for r in results:
            ach = r.get('ventilation_rate_ach')
            n_points = len(r.get('values', []))
            if ach is not None and n_points > 1:
                ach_values.append(ach)
                weights.append(n_points)
                table_rows.append([
                    r['start'], r['end'], ach, n_points
                ])
        if not ach_values:
            print("No valid ACH values found.")
            return
        # Weighted statistics
        ach_mean = np.average(ach_values, weights=weights)
        ach_median = np.median(ach_values)
        ach_std = np.sqrt(np.average((np.array(ach_values)-ach_mean)**2, weights=weights))
        ach_min = np.min(ach_values)
        ach_max = np.max(ach_values)
        n_periods = len(ach_values)
        total_points = sum(weights)
        # Probability for confidence (0-1 scale)
        p_periods = min(n_periods / 20, 1.0)
        p_points = min(total_points / 100, 1.0)
        p_std = max(0, 1 - ach_std / 0.05)
        confidence_prob = round((0.4*p_periods + 0.4*p_points + 0.2*p_std), 2)
        if confidence_prob > 0.85:
            confidence = "High"
        elif confidence_prob > 0.6:
            confidence = "Medium"
        else:
            confidence = "Low"
        # Compare to standard recommendation
        if ach_mean >= recommended_ach:
            ventilation_status = f"Well ventilated (mean ACH {ach_mean:.2f} ≥ recommended {recommended_ach})"
        else:
            ventilation_status = f"Poorly ventilated (mean ACH {ach_mean:.2f} < recommended {recommended_ach})"
        # Print table
        print("\nACH Decay Periods Table:")
        print(tabulate(table_rows, headers=["Start", "End", "ACH", "Data Points"], tablefmt="github"))
        # Print summary
        summary = (
            f"\nACH Statistics (weighted by data points):\n"
            f"Mean: {ach_mean:.4f}\n"
            f"Median: {ach_median:.4f}\n"
            f"Std Dev: {ach_std:.4f}\n"
            f"Min: {ach_min:.4f}\n"
            f"Max: {ach_max:.4f}\n"
            f"Number of periods: {n_periods}\n"
            f"Total data points: {total_points}\n"
            f"Degree of confidence: {confidence} (probability: {confidence_prob})\n"
            f"Ventilation status: {ventilation_status}\n"
        )
        print(summary)
        # Ask to save
        if ask_save:
            save = input("Save summary and table to txt file? (y/n): ").strip().lower()
            if save == 'y':
                if txt_path is None:
                    txt_path = Path("ach_statistics_summary.txt")
                with open(txt_path, "w") as f:
                    f.write(tabulate(table_rows, headers=["Start", "End", "ACH", "Data Points"], tablefmt="github"))
                    f.write("\n" + summary)
                print(f"Summary saved to {txt_path}")
