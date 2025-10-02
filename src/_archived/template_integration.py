"""
Template Chart Integration

Provides utilities for integrating shared charts into templates.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from .manager import get_chart_library_manager
from . import generate_chart

logger = logging.getLogger(__name__)


class TemplateChartIntegrator:
    """Integrates shared charts into reporting templates."""
    
    def __init__(self, template_config: Dict[str, Any]):
        self.template_config = template_config
        self.chart_manager = get_chart_library_manager()
        self.chart_cache: Dict[str, Any] = {}
    
    def get_template_charts(self) -> Dict[str, List[str]]:
        """Get charts defined in the template configuration."""
        charts = {}
        template_charts = self.template_config.get('charts', {})
        
        for section, chart_configs in template_charts.items():
            charts[section] = []
            
            if isinstance(chart_configs, list):
                for chart_config in chart_configs:
                    chart_id = chart_config.get('id') if isinstance(chart_config, dict) else chart_config
                    if chart_id:
                        charts[section].append(chart_id)
            elif isinstance(chart_configs, dict):
                chart_list = chart_configs.get('charts', [])
                for chart_config in chart_list:
                    chart_id = chart_config.get('id') if isinstance(chart_config, dict) else chart_config
                    if chart_id:
                        charts[section].append(chart_id)
        
        return charts
    
    def add_charts_from_set(self, set_name: str, section: str = "additional"):
        """Add charts from a predefined chart set to the template."""
        chart_ids = self.chart_manager.get_chart_set(set_name)
        
        if not chart_ids:
            logger.warning(f"Chart set '{set_name}' not found")
            return
        
        if 'charts' not in self.template_config:
            self.template_config['charts'] = {}
        
        if section not in self.template_config['charts']:
            self.template_config['charts'][section] = []
        
        for chart_id in chart_ids:
            # Avoid duplicates
            existing_ids = [
                c.get('id') if isinstance(c, dict) else c 
                for c in self.template_config['charts'][section]
            ]
            
            if chart_id not in existing_ids:
                self.template_config['charts'][section].append({'id': chart_id})
    
    def add_charts_by_category(self, category: str, section: str = "additional"):
        """Add all charts from a specific category to the template."""
        charts = self.chart_manager.get_charts_by_category(category)
        
        if 'charts' not in self.template_config:
            self.template_config['charts'] = {}
        
        if section not in self.template_config['charts']:
            self.template_config['charts'][section] = []
        
        for chart_info in charts:
            chart_id = chart_info['chart_id']
            
            # Avoid duplicates
            existing_ids = [
                c.get('id') if isinstance(c, dict) else c 
                for c in self.template_config['charts'][section]
            ]
            
            if chart_id not in existing_ids:
                self.template_config['charts'][section].append({
                    'id': chart_id,
                    'name': chart_info['name'],
                    'description': chart_info['description']
                })
    
    def add_charts_by_tag(self, tag: str, section: str = "additional"):
        """Add all charts with a specific tag to the template."""
        charts = self.chart_manager.get_charts_by_tag(tag)
        
        if 'charts' not in self.template_config:
            self.template_config['charts'] = {}
        
        if section not in self.template_config['charts']:
            self.template_config['charts'][section] = []
        
        for chart_info in charts:
            chart_id = chart_info['chart_id']
            
            # Avoid duplicates
            existing_ids = [
                c.get('id') if isinstance(c, dict) else c 
                for c in self.template_config['charts'][section]
            ]
            
            if chart_id not in existing_ids:
                self.template_config['charts'][section].append({
                    'id': chart_id,
                    'name': chart_info['name'],
                    'description': chart_info['description']
                })
    
    def recommend_charts_for_template(self, data_sample: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recommend charts based on available data in the template."""
        data_keys = set(data_sample.keys())
        return self.chart_manager.recommend_charts_for_data(data_keys)
    
    def generate_template_chart(self, chart_id: str, data: Dict[str, Any], 
                               section: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate a chart for the template with caching."""
        
        # Check cache first
        cache_key = f"{chart_id}_{hash(str(sorted(data.items())))}"
        if cache_key in self.chart_cache:
            return self.chart_cache[cache_key]
        
        # Get chart configuration from template
        chart_config = self._get_chart_config(chart_id, section)
        
        # Generate chart
        result = generate_chart(chart_id, data, chart_config, **kwargs)
        
        # Cache result
        self.chart_cache[cache_key] = result
        
        return result
    
    def generate_all_template_charts(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate all charts defined in the template."""
        results = {}
        template_charts = self.get_template_charts()
        
        for section, chart_ids in template_charts.items():
            results[section] = {}
            
            for chart_id in chart_ids:
                try:
                    result = self.generate_template_chart(chart_id, data, section)
                    results[section][chart_id] = result
                except Exception as e:
                    logger.error(f"Failed to generate chart '{chart_id}' in section '{section}': {e}")
                    results[section][chart_id] = {
                        'error': str(e),
                        'chart_id': chart_id
                    }
        
        return results
    
    def validate_template_charts(self) -> Dict[str, Any]:
        """Validate all charts in the template configuration."""
        return self.chart_manager.validate_template_charts(self.template_config)
    
    def get_template_data_requirements(self) -> Dict[str, List[str]]:
        """Get data requirements for all charts in the template."""
        requirements = {
            'required': set(),
            'optional': set()
        }
        
        template_charts = self.get_template_charts()
        
        for section, chart_ids in template_charts.items():
            for chart_id in chart_ids:
                try:
                    from . import chart_registry
                    chart_info = chart_registry.get_chart_info(chart_id)
                    requirements['required'].update(chart_info['required_data_keys'])
                    requirements['optional'].update(chart_info['optional_data_keys'])
                except ValueError:
                    logger.warning(f"Chart '{chart_id}' not found in registry")
        
        return {
            'required': list(requirements['required']),
            'optional': list(requirements['optional'])
        }
    
    def export_template_chart_config(self, output_path: Path):
        """Export the template's chart configuration."""
        chart_config = {
            'template_info': {
                'name': self.template_config.get('name', 'Unknown Template'),
                'description': self.template_config.get('description', ''),
                'version': self.template_config.get('version', '1.0.0')
            },
            'charts': self.get_template_charts(),
            'data_requirements': self.get_template_data_requirements(),
            'validation': self.validate_template_charts()
        }
        
        with open(output_path, 'w') as f:
            json.dump(chart_config, f, indent=2, default=str)
    
    def _get_chart_config(self, chart_id: str, section: Optional[str] = None) -> Dict[str, Any]:
        """Get chart configuration from template."""
        
        # Start with default config
        config = self.template_config.get('chart_defaults', {}).copy()
        
        # Add chart-specific config
        chart_configs = self.template_config.get('chart_configs', {})
        if chart_id in chart_configs:
            config.update(chart_configs[chart_id])
        
        # Add section-specific config
        if section:
            section_configs = self.template_config.get('section_configs', {})
            if section in section_configs:
                config.update(section_configs[section])
        
        return config


def create_template_with_chart_set(template_name: str, chart_set: str, 
                                  base_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new template configuration using a predefined chart set."""
    
    manager = get_chart_library_manager()
    chart_ids = manager.get_chart_set(chart_set)
    
    if not chart_ids:
        raise ValueError(f"Chart set '{chart_set}' not found")
    
    template_config = base_config.copy() if base_config else {}
    
    # Set basic template info
    template_config.update({
        'name': template_name,
        'description': f'Template created from chart set: {chart_set}',
        'version': '1.0.0',
        'charts': {
            'main': [{'id': chart_id} for chart_id in chart_ids]
        }
    })
    
    return template_config


def merge_templates(template1: Dict[str, Any], template2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two template configurations."""
    
    merged = template1.copy()
    
    # Merge charts
    if 'charts' in template2:
        if 'charts' not in merged:
            merged['charts'] = {}
        
        for section, charts in template2['charts'].items():
            if section not in merged['charts']:
                merged['charts'][section] = []
            
            # Avoid duplicates
            existing_ids = [
                c.get('id') if isinstance(c, dict) else c 
                for c in merged['charts'][section]
            ]
            
            for chart in charts:
                chart_id = chart.get('id') if isinstance(chart, dict) else chart
                if chart_id not in existing_ids:
                    merged['charts'][section].append(chart)
    
    # Merge other configurations
    for key, value in template2.items():
        if key != 'charts':
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key].update(value)
            else:
                merged[key] = value
    
    return merged
