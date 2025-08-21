"""
Opening Hours CO2 & Temperature Analysis Chart

Specialized chart for analyzing CO2 and temperature patterns during opening hours.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional
from datetime import datetime

from ..base_chart import BaseChart, register_chart


@register_chart
class OpeningHoursAnalysisChart(BaseChart):
    """Dual-axis chart showing CO2 and temperature during opening hours."""
    
    chart_id = 'opening_hours_analysis'
    name = 'Opening Hours Analysis'
    description = 'Dual-axis line chart showing CO2 and temperature patterns during opening hours'
    category = 'Indoor Air Quality'
    tags = ['co2', 'temperature', 'opening_hours', 'dual_axis']
    
    required_data_keys = ['opening_hours_data']
    optional_data_keys = ['thresholds', 'comfort_zone']
    
    def generate(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate opening hours analysis chart."""
        
        config = config or {}
        figsize = config.get('figsize', [14, 8])
        
        opening_hours_data = data.get('opening_hours_data', {})
        if not opening_hours_data:
            return self._empty_chart_result('No opening hours data available')
        
        # Extract data
        timestamps = opening_hours_data.get('timestamps', [])
        co2_data = opening_hours_data.get('co2', [])
        temp_data = opening_hours_data.get('temperature', [])
        
        if not timestamps or not co2_data or not temp_data:
            return self._empty_chart_result('Incomplete opening hours data')
        
        fig, ax1 = plt.subplots(figsize=figsize)
        
        # CO2 on primary axis
        color_co2 = config.get('co2_color', '#2E86AB')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('CO2 Concentration (ppm)', color=color_co2)
        line1 = ax1.plot(timestamps, co2_data, color=color_co2, 
                        linewidth=2, label='CO2', alpha=0.8)
        ax1.tick_params(axis='y', labelcolor=color_co2)
        ax1.grid(True, alpha=0.3)
        
        # Temperature on secondary axis
        ax2 = ax1.twinx()
        color_temp = config.get('temp_color', '#A23B72')
        ax2.set_ylabel('Temperature (°C)', color=color_temp)
        line2 = ax2.plot(timestamps, temp_data, color=color_temp, 
                        linewidth=2, label='Temperature', alpha=0.8)
        ax2.tick_params(axis='y', labelcolor=color_temp)
        
        # Add thresholds
        thresholds = data.get('thresholds', {})
        if thresholds.get('acceptable'):
            ax1.axhline(y=thresholds['acceptable'], color='red', linestyle='--', 
                       alpha=0.5, label='CO2 Threshold')
        
        comfort_zone = data.get('comfort_zone', {})
        if comfort_zone.get('max'):
            ax2.axhline(y=comfort_zone['max'], color='orange', linestyle='--', 
                       alpha=0.5, label='Temp Threshold')
        
        # Legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left')
        
        plt.title('CO2 & Temperature During Opening Hours', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        return {
            'figure': fig,
            'title': self.name,
            'description': self.description,
            'chart_type': 'dual_axis_line'
        }
