"""
Chart Library Manager

Manages the shared chart library and provides discovery and integration capabilities
for templates.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import logging

from . import chart_registry, list_available_charts, search_charts, generate_chart

logger = logging.getLogger(__name__)


class ChartLibraryManager:
    """Manager for the shared chart library."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.chart_sets: Dict[str, Dict[str, Any]] = {}
        self.load_chart_sets()
    
    def load_chart_sets(self):
        """Load predefined chart sets from configuration."""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.chart_sets = config.get('chart_sets', {})
            except Exception as e:
                logger.warning(f"Failed to load chart sets config: {e}")
    
    def get_charts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all charts in a specific category."""
        return list_available_charts(category=category)
    
    def get_charts_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get all charts with a specific tag."""
        return list_available_charts(tag=tag)
    
    def search_charts_by_query(self, query: str) -> List[Dict[str, Any]]:
        """Search charts by query."""
        return search_charts(query)
    
    def get_chart_set(self, set_name: str) -> List[str]:
        """Get a predefined set of chart IDs."""
        return self.chart_sets.get(set_name, {}).get('charts', [])
    
    def create_chart_set(self, set_name: str, chart_ids: List[str], 
                        description: str = "", tags: Optional[List[str]] = None):
        """Create a new chart set."""
        self.chart_sets[set_name] = {
            'charts': chart_ids,
            'description': description,
            'tags': tags or []
        }
    
    def get_available_chart_sets(self) -> Dict[str, Dict[str, Any]]:
        """Get all available chart sets."""
        return self.chart_sets.copy()
    
    def recommend_charts_for_data(self, data_keys: Set[str]) -> List[Dict[str, Any]]:
        """Recommend charts based on available data keys."""
        all_charts = list_available_charts()
        recommended = []
        
        for chart_info in all_charts:
            required_keys = set(chart_info['required_data_keys'])
            optional_keys = set(chart_info['optional_data_keys'])
            
            # Check if all required keys are available
            if required_keys.issubset(data_keys):
                # Calculate match score based on available optional keys
                optional_matches = len(optional_keys.intersection(data_keys))
                total_optional = len(optional_keys) if optional_keys else 1
                
                chart_info['match_score'] = 1.0 + (optional_matches / total_optional)
                recommended.append(chart_info)
        
        # Sort by match score (descending)
        recommended.sort(key=lambda x: x['match_score'], reverse=True)
        return recommended
    
    def generate_chart_from_library(self, chart_id: str, data: Dict[str, Any], 
                                   config: Optional[Dict[str, Any]] = None, 
                                   **kwargs) -> Dict[str, Any]:
        """Generate a chart from the library."""
        return generate_chart(chart_id, data, config, **kwargs)
    
    def get_chart_compatibility(self, chart_ids: List[str]) -> Dict[str, Any]:
        """Check compatibility between charts (for dashboards)."""
        charts_info = []
        all_required_keys = set()
        all_optional_keys = set()
        categories = set()
        
        for chart_id in chart_ids:
            try:
                info = chart_registry.get_chart_info(chart_id)
                charts_info.append(info)
                all_required_keys.update(info['required_data_keys'])
                all_optional_keys.update(info['optional_data_keys'])
                categories.add(info['category'])
            except ValueError:
                logger.warning(f"Chart '{chart_id}' not found in registry")
        
        return {
            'total_charts': len(charts_info),
            'valid_charts': len(charts_info),
            'categories': list(categories),
            'total_required_keys': list(all_required_keys),
            'total_optional_keys': list(all_optional_keys),
            'data_key_count': len(all_required_keys) + len(all_optional_keys)
        }
    
    def export_chart_library_info(self, output_path: Path):
        """Export chart library information to a file."""
        library_info = {
            'categories': chart_registry.list_categories(),
            'tags': chart_registry.list_tags(),
            'charts': {},
            'chart_sets': self.chart_sets
        }
        
        # Get detailed info for each chart
        for chart_id in chart_registry.list_charts():
            library_info['charts'][chart_id] = chart_registry.get_chart_info(chart_id)
        
        with open(output_path, 'w') as f:
            json.dump(library_info, f, indent=2, default=str)
    
    def validate_template_charts(self, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that all charts in a template configuration are available."""
        template_charts = template_config.get('charts', {})
        validation_results = {
            'valid': True,
            'missing_charts': [],
            'invalid_data_requirements': [],
            'warnings': []
        }
        
        for section, charts in template_charts.items():
            if isinstance(charts, list):
                chart_list = charts
            elif isinstance(charts, dict):
                chart_list = charts.get('charts', [])
            else:
                continue
            
            for chart_config in chart_list:
                chart_id = chart_config.get('id') if isinstance(chart_config, dict) else chart_config
                
                if not chart_id:
                    continue
                
                try:
                    chart_info = chart_registry.get_chart_info(chart_id)
                    
                    # Check if template provides required data
                    template_data_keys = set(template_config.get('data_mapping', {}).keys())
                    required_keys = set(chart_info['required_data_keys'])
                    
                    missing_data = required_keys - template_data_keys
                    if missing_data:
                        validation_results['invalid_data_requirements'].append({
                            'chart_id': chart_id,
                            'missing_keys': list(missing_data)
                        })
                        validation_results['valid'] = False
                    
                except ValueError:
                    validation_results['missing_charts'].append(chart_id)
                    validation_results['valid'] = False
        
        return validation_results


# Create global instance
chart_library_manager = ChartLibraryManager()


def get_chart_library_manager() -> ChartLibraryManager:
    """Get the global chart library manager instance."""
    return chart_library_manager
