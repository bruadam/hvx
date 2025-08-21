"""
Performance Overview Dashboard

A comprehensive dashboard showing key performance metrics in a grid layout.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from typing import Dict, List, Any

from .. import BaseChart, register_chart


@register_chart
class PerformanceOverviewChart(BaseChart):
    """Dashboard chart showing key performance indicators."""
    
    @property
    def chart_id(self) -> str:
        return "performance_overview"
    
    @property
    def name(self) -> str:
        return "Performance Overview Dashboard"
    
    @property
    def description(self) -> str:
        return "Comprehensive dashboard showing key performance metrics in gauge format"
    
    @property
    def category(self) -> str:
        return "Performance"
    
    @property
    def required_data_keys(self) -> List[str]:
        return ["summary_metrics"]
    
    @property
    def optional_data_keys(self) -> List[str]:
        return ["thresholds", "targets"]
    
    @property
    def tags(self) -> List[str]:
        return ["dashboard", "kpi", "overview", "gauges", "performance"]
    
    def generate(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate performance overview dashboard."""
        
        metrics = data.get('summary_metrics', {})
        if not metrics:
            return self._empty_chart_result("No summary metrics available")
        
        thresholds = data.get('thresholds', {})
        targets = data.get('targets', {})
        
        # Create 2x2 subplot grid
        fig, axes = plt.subplots(2, 2, figsize=kwargs.get('figsize', (14, 10)))
        fig.suptitle('Performance Overview Dashboard', fontsize=16, fontweight='bold')
        
        # Define metrics to display
        metric_configs = [
            {
                'key': 'avg_co2',
                'title': 'Average CO2 (ppm)',
                'max_value': 2000,
                'thresholds': [400, 1000, 1500],
                'position': (0, 0)
            },
            {
                'key': 'avg_temperature',
                'title': 'Average Temperature (°C)',
                'max_value': 30,
                'thresholds': [18, 22, 26],
                'position': (0, 1)
            },
            {
                'key': 'compliance_rate',
                'title': 'Compliance Rate (%)',
                'max_value': 100,
                'thresholds': [70, 85, 95],
                'position': (1, 0)
            },
            {
                'key': 'data_quality',
                'title': 'Data Quality Score',
                'max_value': 1.0,
                'thresholds': [0.6, 0.8, 0.9],
                'position': (1, 1)
            }
        ]
        
        for config in metric_configs:
            value = metrics.get(config['key'], 0)
            if config['key'] == 'data_quality' and value > 1:
                value = value / 100  # Convert percentage to decimal if needed
            
            row, col = config['position']
            self._create_gauge_chart(
                axes[row, col], 
                value, 
                config['title'], 
                config['max_value'],
                config['thresholds']
            )
        
        plt.tight_layout()
        
        # Calculate overall score
        scores = []
        for config in metric_configs:
            value = metrics.get(config['key'], 0)
            max_val = config['max_value']
            
            if config['key'] in ['compliance_rate', 'data_quality']:
                # Higher is better
                if config['key'] == 'data_quality' and value > 1:
                    value = value / 100
                score = (value / max_val) * 100
            else:
                # For CO2 and temperature, calculate based on thresholds
                thresholds = config['thresholds']
                if value <= thresholds[0]:
                    score = 100
                elif value <= thresholds[1]:
                    score = 75
                elif value <= thresholds[2]:
                    score = 50
                else:
                    score = 25
            
            scores.append(score)
        
        overall_score = np.mean(scores)
        
        return {
            'figure': fig,
            'chart_type': 'dashboard_grid',
            'title': 'Performance Overview Dashboard',
            'description': 'Key performance indicators for indoor environmental quality',
            'chart_id': self.chart_id,
            'statistics': {
                'overall_score': overall_score,
                'individual_scores': dict(zip([c['key'] for c in metric_configs], scores))
            }
        }
    
    def _create_gauge_chart(self, ax, value: float, title: str, max_value: float, 
                           thresholds: List[float]):
        """Create a gauge chart for dashboard metrics."""
        
        # Determine color based on thresholds
        if len(thresholds) >= 3:
            if value >= thresholds[2]:
                color = 'green'
            elif value >= thresholds[1]:
                color = 'orange'
            else:
                color = 'red'
        else:
            color = 'blue'
        
        # Create gauge using pie chart
        # Calculate angle based on value (semicircle gauge)
        angle = (value / max_value) * 180  # Half circle
        
        # Create gauge background
        theta = np.linspace(0, np.pi, 100)
        radius = 1
        
        # Background arc
        ax.plot(radius * np.cos(theta), radius * np.sin(theta), 
               color='lightgray', linewidth=10, alpha=0.3)
        
        # Value arc
        value_theta = np.linspace(0, np.radians(angle), int(angle))
        ax.plot(radius * np.cos(value_theta), radius * np.sin(value_theta), 
               color=color, linewidth=10)
        
        # Add threshold markers
        for i, threshold in enumerate(thresholds):
            threshold_angle = (threshold / max_value) * 180
            marker_theta = np.radians(threshold_angle)
            x = radius * np.cos(marker_theta)
            y = radius * np.sin(marker_theta)
            ax.plot([x*0.9, x*1.1], [y*0.9, y*1.1], 
                   color='black', linewidth=2)
        
        # Add value text in center
        ax.text(0, -0.3, f'{value:.1f}', ha='center', va='center', 
               fontsize=14, fontweight='bold')
        
        # Add title
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        # Set equal aspect ratio and remove axes
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.5, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
