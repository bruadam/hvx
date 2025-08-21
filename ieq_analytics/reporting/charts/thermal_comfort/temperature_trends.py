"""
Temperature Trends Chart

A chart for displaying temperature trends with comfort zone indicators.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any
from datetime import datetime

from .. import BaseChart, register_chart


@register_chart
class TemperatureTrendsChart(BaseChart):
    """Chart for displaying temperature trends over time."""
    
    @property
    def chart_id(self) -> str:
        return "temperature_trends"
    
    @property
    def name(self) -> str:
        return "Temperature Trends"
    
    @property
    def description(self) -> str:
        return "Line chart showing temperature trends over time with comfort zone indicators"
    
    @property
    def category(self) -> str:
        return "Thermal Comfort"
    
    @property
    def required_data_keys(self) -> List[str]:
        return ["temperature_data"]
    
    @property
    def optional_data_keys(self) -> List[str]:
        return ["timestamps", "comfort_zone", "outdoor_temperature", "setpoints"]
    
    @property
    def tags(self) -> List[str]:
        return ["temperature", "thermal_comfort", "time_series", "comfort_zone"]
    
    def generate(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate temperature trends chart."""
        
        temp_data = data.get("temperature_data", [])
        if not temp_data:
            return self._empty_chart_result("No temperature data available")
        
        timestamps = data.get("timestamps", range(len(temp_data)))
        comfort_zone = data.get("comfort_zone", {"min": 20, "max": 26})
        outdoor_temp = data.get("outdoor_temperature", [])
        setpoints = data.get("setpoints", [])
        
        # Create figure
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (12, 6)))
        
        # Plot indoor temperature
        color_indoor = self.colors.get('primary', '#2E86AB')
        ax.plot(timestamps, temp_data, color=color_indoor, linewidth=2, 
               label='Indoor Temperature', alpha=0.8)
        
        # Plot outdoor temperature if available
        if outdoor_temp and len(outdoor_temp) == len(timestamps):
            color_outdoor = self.colors.get('secondary', '#A23B72')
            ax.plot(timestamps, outdoor_temp, color=color_outdoor, linewidth=1.5, 
                   linestyle='--', label='Outdoor Temperature', alpha=0.7)
        
        # Plot setpoints if available
        if setpoints and len(setpoints) == len(timestamps):
            ax.plot(timestamps, setpoints, color='gray', linewidth=1, 
                   linestyle=':', label='Setpoint', alpha=0.6)
        
        # Add comfort zone
        if comfort_zone:
            comfort_min = comfort_zone.get("min", 20)
            comfort_max = comfort_zone.get("max", 26)
            
            ax.fill_between(timestamps, comfort_min, comfort_max, 
                           alpha=0.2, color='green', label='Comfort Zone')
            ax.axhline(y=comfort_min, color='green', linestyle='--', 
                      alpha=0.5, label=f'Comfort Min ({comfort_min}°C)')
            ax.axhline(y=comfort_max, color='green', linestyle='--', 
                      alpha=0.5, label=f'Comfort Max ({comfort_max}°C)')
        
        # Formatting
        ax.set_xlabel('Time')
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('Temperature Trends', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Rotate x-axis labels if timestamps are datetime objects
        if timestamps and isinstance(timestamps[0], datetime):
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Calculate statistics
        stats = {
            'mean': np.mean(temp_data),
            'max': np.max(temp_data),
            'min': np.min(temp_data),
            'std': np.std(temp_data)
        }
        
        if comfort_zone:
            comfort_min = comfort_zone.get("min", 20)
            comfort_max = comfort_zone.get("max", 26)
            in_comfort = np.sum((np.array(temp_data) >= comfort_min) & 
                               (np.array(temp_data) <= comfort_max))
            stats['comfort_compliance'] = (in_comfort / len(temp_data)) * 100
            stats['below_comfort'] = np.sum(np.array(temp_data) < comfort_min)
            stats['above_comfort'] = np.sum(np.array(temp_data) > comfort_max)
        
        return {
            'figure': fig,
            'chart_type': 'line_chart',
            'title': 'Temperature Trends',
            'description': 'Temperature trends with comfort zone indicators',
            'chart_id': self.chart_id,
            'statistics': stats
        }
