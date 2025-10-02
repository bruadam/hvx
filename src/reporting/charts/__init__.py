"""
Shared Chart Library for IEQ Analytics Reporting

This module provides a comprehensive library of reusable charts that can be used
across different reporting templates. Charts are organized by categories and can
be easily discovered and integrated into any template.
"""

from typing import Dict, List, Any, Optional, Type
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class BaseChart(ABC):
    """Base class for all charts in the library."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.chart_style = self.config.get('formatting', {}).get('chart_styling', {})
        self.colors = self.config.get('formatting', {}).get('colors', {})
        self._setup_matplotlib_style()
    
    def _setup_matplotlib_style(self):
        """Setup matplotlib styling based on configuration."""
        plt.style.use('default')
        
        if self.chart_style:
            plt.rcParams['font.family'] = self.chart_style.get('font_family', 'Arial')
            plt.rcParams['font.size'] = self.chart_style.get('font_size', 12)
            plt.rcParams['lines.linewidth'] = self.chart_style.get('line_width', 2)
            plt.rcParams['grid.alpha'] = self.chart_style.get('grid_alpha', 0.3)
    
    @abstractmethod
    def generate(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate the chart."""
        pass
    
    @property
    @abstractmethod
    def chart_id(self) -> str:
        """Unique identifier for this chart."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this chart."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this chart shows."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """Category this chart belongs to."""
        pass
    
    @property
    @abstractmethod
    def required_data_keys(self) -> List[str]:
        """List of required data keys for this chart."""
        pass
    
    @property
    def optional_data_keys(self) -> List[str]:
        """List of optional data keys for this chart."""
        return []
    
    @property
    def tags(self) -> List[str]:
        """Tags for categorizing and searching charts."""
        return []
    
    def _empty_chart_result(self, message: str) -> Dict[str, Any]:
        """Return empty chart result with message."""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center', 
               transform=ax.transAxes, fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return {
            'figure': fig,
            'chart_type': 'empty',
            'title': 'No Data Available',
            'description': message,
            'chart_id': self.chart_id
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate that required data is present."""
        for key in self.required_data_keys:
            if key not in data:
                logger.warning(f"Missing required data key '{key}' for chart '{self.chart_id}'")
                return False
        return True


class ChartRegistry:
    """Registry for managing all available charts."""
    
    def __init__(self):
        self._charts: Dict[str, Type[BaseChart]] = {}
        self._categories: Dict[str, List[str]] = {}
        self._tags: Dict[str, List[str]] = {}
    
    def register_chart(self, chart_class: Type[BaseChart]):
        """Register a chart class in the registry."""
        # Create temporary instance to get metadata
        temp_instance = chart_class()
        chart_id = temp_instance.chart_id
        category = temp_instance.category
        tags = temp_instance.tags
        
        self._charts[chart_id] = chart_class
        
        # Update categories
        if category not in self._categories:
            self._categories[category] = []
        if chart_id not in self._categories[category]:
            self._categories[category].append(chart_id)
        
        # Update tags
        for tag in tags:
            if tag not in self._tags:
                self._tags[tag] = []
            if chart_id not in self._tags[tag]:
                self._tags[tag].append(chart_id)
    
    def get_chart(self, chart_id: str, config: Optional[Dict[str, Any]] = None) -> BaseChart:
        """Get a chart instance by ID."""
        if chart_id not in self._charts:
            raise ValueError(f"Chart '{chart_id}' not found in registry")
        
        chart_class = self._charts[chart_id]
        return chart_class(config)
    
    def list_charts(self, category: Optional[str] = None, tag: Optional[str] = None) -> List[str]:
        """List available charts, optionally filtered by category or tag."""
        if category:
            return self._categories.get(category, [])
        elif tag:
            return self._tags.get(tag, [])
        else:
            return list(self._charts.keys())
    
    def list_categories(self) -> List[str]:
        """List all available categories."""
        return list(self._categories.keys())
    
    def list_tags(self) -> List[str]:
        """List all available tags."""
        return list(self._tags.keys())
    
    def get_chart_info(self, chart_id: str) -> Dict[str, Any]:
        """Get information about a chart."""
        if chart_id not in self._charts:
            raise ValueError(f"Chart '{chart_id}' not found in registry")
        
        chart_class = self._charts[chart_id]
        temp_instance = chart_class()
        
        return {
            'chart_id': chart_id,
            'name': temp_instance.name,
            'description': temp_instance.description,
            'category': temp_instance.category,
            'tags': temp_instance.tags,
            'required_data_keys': temp_instance.required_data_keys,
            'optional_data_keys': temp_instance.optional_data_keys
        }
    
    def search_charts(self, query: str) -> List[str]:
        """Search charts by name, description, or tags."""
        query_lower = query.lower()
        matching_charts = []
        
        for chart_id in self._charts:
            info = self.get_chart_info(chart_id)
            
            # Search in name, description, category, and tags
            searchable_text = " ".join([
                info['name'].lower(),
                info['description'].lower(),
                info['category'].lower(),
                " ".join(info['tags']).lower()
            ])
            
            if query_lower in searchable_text:
                matching_charts.append(chart_id)
        
        return matching_charts


# Global chart registry
chart_registry = ChartRegistry()


def register_chart(chart_class: Type[BaseChart]):
    """Decorator to register a chart class."""
    chart_registry.register_chart(chart_class)
    return chart_class


def generate_chart(chart_id: str, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Generate a chart by ID."""
    chart = chart_registry.get_chart(chart_id, config)
    
    if not chart.validate_data(data):
        return chart._empty_chart_result(f"Missing required data for chart '{chart_id}'")
    
    return chart.generate(data, **kwargs)


def list_available_charts(category: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all available charts with their information."""
    chart_ids = chart_registry.list_charts(category, tag)
    return [chart_registry.get_chart_info(chart_id) for chart_id in chart_ids]


def search_charts(query: str) -> List[Dict[str, Any]]:
    """Search for charts matching a query."""
    chart_ids = chart_registry.search_charts(query)
    return [chart_registry.get_chart_info(chart_id) for chart_id in chart_ids]


# Import all chart categories to register the charts
from . import indoor_air_quality
from . import thermal_comfort
from . import performance
from . import compliance
from . import time_analysis
from . import energy
from . import predictive


__all__ = [
    'BaseChart',
    'ChartRegistry',
    'chart_registry',
    'register_chart',
    'generate_chart',
    'list_available_charts',
    'search_charts'
]
