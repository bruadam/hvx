"""
CO2 Concentration Chart

A chart for displaying CO2 concentration levels over time with threshold indicators.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any
from datetime import datetime

from .. import BaseChart, register_chart


@register_chart
class CO2ConcentrationChart(BaseChart):
    """Chart for displaying CO2 concentration levels over time."""
    
    @property
    def chart_id(self) -> str:
        return "co2_concentration"
    
    @property
    def name(self) -> str:
        return "CO2 Concentration"
    
    @property
    def description(self) -> str:
        return "Line chart showing CO2 concentration levels over time with threshold indicators"
    
    @property
    def category(self) -> str:
        return "Indoor Air Quality"
    
    @property
    def required_data_keys(self) -> List[str]:
        return ["co2_data"]
    
    @property
    def optional_data_keys(self) -> List[str]:
        return ["timestamps", "thresholds", "occupancy_periods"]
    
    @property
    def tags(self) -> List[str]:
        return ["co2", "air_quality", "time_series", "thresholds"]
    
    def generate(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate CO2 concentration chart."""
        
        co2_data = data.get("co2_data", [])
        if not co2_data:
            return self._empty_chart_result("No CO2 data available")
        
        timestamps = data.get("timestamps", range(len(co2_data)))
        thresholds = data.get("thresholds", {"good": 400, "acceptable": 1000, "poor": 1500})
        occupancy_periods = data.get("occupancy_periods", [])
        
        # Create figure
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (12, 6)))
        
        # Plot CO2 data
        color_co2 = self.colors.get('primary', '#2E86AB')
        line = ax.plot(timestamps, co2_data, color=color_co2, linewidth=2, 
                      label='CO2 Concentration', alpha=0.8)
        
        # Add threshold lines
        if thresholds:
            ax.axhline(y=thresholds.get("acceptable", 1000), color='orange', 
                      linestyle='--', alpha=0.7, label='Acceptable Threshold (1000 ppm)')
            ax.axhline(y=thresholds.get("poor", 1500), color='red', 
                      linestyle='--', alpha=0.7, label='Poor Threshold (1500 ppm)')
            
            # Add colored background zones
            ax.fill_between(timestamps, 0, thresholds.get("acceptable", 1000), 
                           alpha=0.2, color='green', label='Good Zone')
            ax.fill_between(timestamps, thresholds.get("acceptable", 1000), 
                           thresholds.get("poor", 1500), 
                           alpha=0.2, color='orange', label='Acceptable Zone')
            ax.fill_between(timestamps, thresholds.get("poor", 1500), 
                           max(co2_data) if co2_data else 2000, 
                           alpha=0.2, color='red', label='Poor Zone')
        
        # Highlight occupancy periods
        if occupancy_periods:
            for start, end in occupancy_periods:
                ax.axvspan(start, end, alpha=0.1, color='blue', label='Occupied Hours')
        
        # Formatting
        ax.set_xlabel('Time')
        ax.set_ylabel('CO2 Concentration (ppm)')
        ax.set_title('CO2 Concentration Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Rotate x-axis labels if timestamps are datetime objects
        if timestamps and isinstance(timestamps[0], datetime):
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Calculate statistics
        stats = {
            'mean': np.mean(co2_data),
            'max': np.max(co2_data),
            'min': np.min(co2_data),
            'std': np.std(co2_data)
        }
        
        if thresholds:
            stats['above_acceptable'] = np.sum(np.array(co2_data) > thresholds.get("acceptable", 1000))
            stats['above_poor'] = np.sum(np.array(co2_data) > thresholds.get("poor", 1500))
        
        return {
            'figure': fig,
            'chart_type': 'line_chart',
            'title': 'CO2 Concentration Over Time',
            'description': 'CO2 concentration levels with threshold indicators',
            'chart_id': self.chart_id,
            'statistics': stats
        }
