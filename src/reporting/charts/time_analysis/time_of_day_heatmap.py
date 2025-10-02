"""
Time of Day Heatmap

A heatmap showing parameter values by hour of day and day of week.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any

from .. import BaseChart, register_chart


@register_chart
class TimeOfDayHeatmapChart(BaseChart):
    """Chart for displaying parameter heatmaps by time of day."""
    
    @property
    def chart_id(self) -> str:
        return "time_of_day_heatmap"
    
    @property
    def name(self) -> str:
        return "Time of Day Heatmap"
    
    @property
    def description(self) -> str:
        return "Heatmap showing parameter values by hour of day and day of week"
    
    @property
    def category(self) -> str:
        return "Time Analysis"
    
    @property
    def required_data_keys(self) -> List[str]:
        return ["hourly_data"]
    
    @property
    def optional_data_keys(self) -> List[str]:
        return ["parameter_name", "units", "colormap"]
    
    @property
    def tags(self) -> List[str]:
        return ["heatmap", "time_analysis", "hourly", "pattern", "schedule"]
    
    def generate(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate time of day heatmap chart."""
        
        hourly_data = data.get('hourly_data', {})
        if not hourly_data:
            return self._empty_chart_result("No hourly data available")
        
        parameter_name = data.get('parameter_name', 'Parameter')
        units = data.get('units', '')
        colormap = data.get('colormap', 'RdYlBu_r')
        
        # Check if we have a matrix or need to create one
        if 'matrix' in hourly_data:
            matrix = np.array(hourly_data['matrix'])
        else:
            # Create matrix from raw data
            matrix = self._create_hourly_matrix(hourly_data)
        
        if matrix.size == 0:
            return self._empty_chart_result("No valid matrix data available")
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (12, 6)))
        
        im = ax.imshow(matrix, cmap=colormap, aspect='auto')
        
        # Set labels
        day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        hour_labels = [f'{h:02d}:00' for h in range(24)]
        
        ax.set_xticks(range(24))
        ax.set_yticks(range(7))
        ax.set_xticklabels(hour_labels, rotation=45)
        ax.set_yticklabels(day_labels)
        
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Day of Week')
        
        title = f'{parameter_name} by Hour and Day'
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Add colorbar
        cbar_label = f'{parameter_name} ({units})' if units else parameter_name
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(cbar_label, rotation=270, labelpad=20)
        
        # Add value annotations for smaller matrices
        if matrix.shape[0] <= 7 and matrix.shape[1] <= 24:
            for i in range(matrix.shape[0]):
                for j in range(matrix.shape[1]):
                    if not np.isnan(matrix[i, j]):
                        text = ax.text(j, i, f'{matrix[i, j]:.1f}',
                                     ha="center", va="center", color="white", 
                                     fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        
        # Calculate statistics
        valid_data = matrix[~np.isnan(matrix)]
        stats = {}
        if len(valid_data) > 0:
            stats = {
                'mean': np.mean(valid_data),
                'max': np.max(valid_data),
                'min': np.min(valid_data),
                'std': np.std(valid_data),
                'peak_hour': np.unravel_index(np.nanargmax(matrix), matrix.shape),
                'low_hour': np.unravel_index(np.nanargmin(matrix), matrix.shape)
            }
        
        return {
            'figure': fig,
            'chart_type': 'heatmap',
            'title': title,
            'description': f'Hour-by-day heatmap for {parameter_name}',
            'chart_id': self.chart_id,
            'statistics': stats
        }
    
    def _create_hourly_matrix(self, hourly_data: Dict[str, Any]) -> np.ndarray:
        """Create 7x24 matrix from hourly data."""
        
        # Initialize 7x24 matrix (days x hours)
        matrix = np.full((7, 24), np.nan)
        
        # Try different data formats
        if 'values' in hourly_data and 'hours' in hourly_data and 'days' in hourly_data:
            values = hourly_data['values']
            hours = hourly_data['hours']
            days = hourly_data['days']
            
            for value, hour, day in zip(values, hours, days):
                if 0 <= day < 7 and 0 <= hour < 24:
                    matrix[day, hour] = value
        
        elif isinstance(hourly_data, dict):
            # Try to parse day-hour structure
            for day_key, day_data in hourly_data.items():
                if isinstance(day_data, dict):
                    try:
                        day_idx = int(day_key) if day_key.isdigit() else self._parse_day_name(day_key)
                        if 0 <= day_idx < 7:
                            for hour_key, value in day_data.items():
                                try:
                                    hour_idx = int(hour_key)
                                    if 0 <= hour_idx < 24:
                                        matrix[day_idx, hour_idx] = float(value)
                                except (ValueError, TypeError):
                                    continue
                    except (ValueError, TypeError):
                        continue
        
        return matrix
    
    def _parse_day_name(self, day_name: str) -> int:
        """Parse day name to index."""
        day_mapping = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        return day_mapping.get(day_name.lower(), -1)
