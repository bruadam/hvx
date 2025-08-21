"""
EN16798-1 Compliance Chart

A chart showing compliance with EN16798-1 standard categories.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any

from .. import BaseChart, register_chart


@register_chart
class EN16798ComplianceChart(BaseChart):
    """Chart for displaying EN16798-1 compliance matrix."""
    
    @property
    def chart_id(self) -> str:
        return "en16798_compliance"
    
    @property
    def name(self) -> str:
        return "EN16798-1 Compliance"
    
    @property
    def description(self) -> str:
        return "Heatmap showing compliance with EN16798-1 standard categories"
    
    @property
    def category(self) -> str:
        return "Compliance"
    
    @property
    def required_data_keys(self) -> List[str]:
        return ["en16798_compliance"]
    
    @property
    def optional_data_keys(self) -> List[str]:
        return ["categories", "parameters"]
    
    @property
    def tags(self) -> List[str]:
        return ["compliance", "en16798", "standard", "heatmap", "matrix"]
    
    def generate(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate EN16798-1 compliance matrix chart."""
        
        compliance_data = data.get('en16798_compliance', {})
        if not compliance_data:
            return self._empty_chart_result("No EN16798-1 compliance data available")
        
        # Define default categories and parameters
        categories = data.get('categories', ['Category I', 'Category II', 'Category III'])
        parameters = data.get('parameters', ['Temperature', 'CO2', 'Humidity'])
        
        # Extract compliance percentages
        matrix_data = []
        for category in categories:
            row = []
            for param in parameters:
                # Try different key formats
                key_options = [
                    f"{category.lower().replace(' ', '_')}_{param.lower()}_compliance",
                    f"{category}_{param}_compliance",
                    f"{category.replace(' ', '')}_{param}",
                    f"cat_{categories.index(category)+1}_{param.lower()}"
                ]
                
                compliance = 0
                for key in key_options:
                    if key in compliance_data:
                        compliance = compliance_data[key]
                        break
                
                row.append(compliance)
            matrix_data.append(row)
        
        matrix_data = np.array(matrix_data)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (10, 6)))
        
        im = ax.imshow(matrix_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
        
        # Set ticks and labels
        ax.set_xticks(np.arange(len(parameters)))
        ax.set_yticks(np.arange(len(categories)))
        ax.set_xticklabels(parameters)
        ax.set_yticklabels(categories)
        
        # Add text annotations
        for i in range(len(categories)):
            for j in range(len(parameters)):
                text = ax.text(j, i, f'{matrix_data[i, j]:.1f}%',
                             ha="center", va="center", color="black", fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Compliance Percentage', rotation=270, labelpad=20)
        
        ax.set_title('EN16798-1 Compliance Overview', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Calculate overall compliance
        overall_compliance = np.mean(matrix_data)
        category_averages = np.mean(matrix_data, axis=1)
        parameter_averages = np.mean(matrix_data, axis=0)
        
        return {
            'figure': fig,
            'chart_type': 'compliance_matrix',
            'title': 'EN16798-1 Compliance Overview',
            'description': 'Compliance matrix for all EN16798-1 categories and parameters',
            'chart_id': self.chart_id,
            'statistics': {
                'overall_compliance': overall_compliance,
                'category_averages': dict(zip(categories, category_averages)),
                'parameter_averages': dict(zip(parameters, parameter_averages))
            }
        }
