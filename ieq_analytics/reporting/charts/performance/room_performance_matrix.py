"""
Room Performance Matrix Chart

Scatter plot showing room performance across multiple metrics.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from typing import Dict, Any, Optional

from ..base_chart import BaseChart, register_chart


@register_chart
class RoomPerformanceMatrixChart(BaseChart):
    """Scatter plot matrix showing room performance metrics."""
    
    chart_id = 'room_performance_matrix'
    name = 'Room Performance Matrix'
    description = 'Scatter plot showing room performance across CO2 and temperature metrics'
    category = 'Performance'
    tags = ['room_analysis', 'performance', 'scatter_plot', 'matrix']
    
    required_data_keys = ['room_data']
    optional_data_keys = ['buildings']
    
    def generate(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate room performance matrix chart."""
        
        config = config or {}
        figsize = config.get('figsize', [12, 8])
        
        room_data = data.get('room_data', {})
        if not room_data:
            return self._empty_chart_result('No room data available')
        
        # Extract room performance metrics
        rooms = list(room_data.keys())
        co2_scores = [room_data[room].get('co2_score', 0) for room in rooms]
        temp_scores = [room_data[room].get('temp_score', 0) for room in rooms]
        data_quality = [room_data[room].get('data_quality', 0.5) for room in rooms]
        buildings = [room_data[room].get('building', 'Unknown') for room in rooms]
        
        # Create scatter plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Color by building
        unique_buildings = list(set(buildings))
        colors = cm.get_cmap('Set1')(np.linspace(0, 1, len(unique_buildings)))
        building_colors = {building: colors[i] for i, building in enumerate(unique_buildings)}
        
        for building in unique_buildings:
            building_mask = [b == building for b in buildings]
            building_co2 = [co2_scores[i] for i, mask in enumerate(building_mask) if mask]
            building_temp = [temp_scores[i] for i, mask in enumerate(building_mask) if mask]
            building_quality = [data_quality[i] for i, mask in enumerate(building_mask) if mask]
            
            scatter = ax.scatter(building_co2, building_temp, 
                               s=[q*100 for q in building_quality],  # Size by data quality
                               c=[building_colors[building]], 
                               alpha=0.7, label=building)
        
        ax.set_xlabel('CO2 Performance Score')
        ax.set_ylabel('Temperature Performance Score')
        ax.set_title('Room Performance Matrix', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add quadrant lines
        ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=50, color='gray', linestyle='--', alpha=0.5)
        
        # Add quadrant labels
        ax.text(75, 75, 'Good\nPerformance', ha='center', va='center', 
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        ax.text(25, 25, 'Poor\nPerformance', ha='center', va='center',
               bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
        
        plt.tight_layout()
        
        return {
            'figure': fig,
            'title': self.name,
            'description': self.description,
            'chart_type': 'room_matrix'
        }
