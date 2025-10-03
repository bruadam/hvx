"""
Base Template Class for IEQ Analytics Reports

Provides the foundation for all report templates with common functionality.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseTemplate:
    """Base class for all report templates."""
    
    def __init__(self, template_dir: Path):
        self.template_dir = Path(template_dir)
        self.config_path = self.template_dir / "config.yaml"
        self.template_path = self.template_dir / "template.html"
        self.charts_config_path = self.template_dir / "charts.py"
        
        # Load template configuration
        self.config = self._load_config()
        
        # Initialize template properties
        self.template_id = self.config.get('template', {}).get('id', 'unknown')
        self.template_name = self.config.get('template', {}).get('name', 'Unknown Template')
        self.description = self.config.get('template', {}).get('description', '')
        self.category = self.config.get('template', {}).get('category', 'general')
        
        # Sections and charts configuration
        self.sections = self.config.get('sections', [])
        self.charts_config = self.config.get('charts', {})
        self.filters_config = self.config.get('filters', {})
        self.advanced_analytics = self.config.get('advanced_analytics', {})
        
    def _load_config(self) -> Dict[str, Any]:
        """Load template configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def get_template_info(self) -> Dict[str, Any]:
        """Get basic template information."""
        return {
            'id': self.template_id,
            'name': self.template_name,
            'description': self.description,
            'category': self.category,
            'sections_count': len(self.sections),
            'charts_count': len(self.charts_config),
            'has_advanced_analytics': bool(self.advanced_analytics)
        }
    
    def get_available_sections(self) -> List[Dict[str, Any]]:
        """Get list of available sections for this template."""
        return [{
            'id': section['id'],
            'name': section['name'],
            'required': section.get('required', False),
            'charts': section.get('charts', []),
            'description': section.get('description', '')
        } for section in self.sections]
    
    def get_available_charts(self) -> Dict[str, Any]:
        """Get available charts for this template."""
        return self.charts_config
    
    def get_filter_options(self) -> Dict[str, Any]:
        """Get available filter options."""
        return self.filters_config
    
    def get_advanced_analytics_options(self) -> Dict[str, Any]:
        """Get available advanced analytics options."""
        return self.advanced_analytics
    
    def validate_selection(self, selected_sections: List[str], selected_charts: List[str]) -> Dict[str, Any]:
        """Validate user selections against template requirements."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required sections
        required_sections = [s['id'] for s in self.sections if s.get('required', False)]
        missing_required = [s for s in required_sections if s not in selected_sections]
        
        if missing_required:
            validation_result['valid'] = False
            validation_result['errors'].append(
                f"Missing required sections: {', '.join(missing_required)}"
            )
        
        # Check if selected charts are available
        available_charts = list(self.charts_config.keys())
        invalid_charts = [c for c in selected_charts if c not in available_charts]
        
        if invalid_charts:
            validation_result['warnings'].append(
                f"Unknown charts will be ignored: {', '.join(invalid_charts)}"
            )
        
        return validation_result
    
    def generate_report_config(
        self,
        selected_sections: List[str],
        selected_charts: List[str],
        filter_settings: Dict[str, Any],
        advanced_analytics_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate complete report configuration based on selections."""
        
        # Validate selections
        validation = self.validate_selection(selected_sections, selected_charts)
        if not validation['valid']:
            raise ValueError(f"Invalid selections: {validation['errors']}")
        
        # Build report configuration
        report_config = {
            'template_id': self.template_id,
            'template_name': self.template_name,
            'generation_timestamp': datetime.now().isoformat(),
            'sections': [],
            'charts': {},
            'filters': filter_settings,
            'advanced_analytics': advanced_analytics_settings,
            'validation': validation
        }
        
        # Add selected sections
        for section_id in selected_sections:
            section = next((s for s in self.sections if s['id'] == section_id), None)
            if section:
                section_config = {
                    'id': section_id,
                    'name': section['name'],
                    'charts': [c for c in section.get('charts', []) if c in selected_charts]
                }
                report_config['sections'].append(section_config)
        
        # Add selected charts configuration
        for chart_id in selected_charts:
            if chart_id in self.charts_config:
                report_config['charts'][chart_id] = self.charts_config[chart_id]
        
        return report_config
    
    def load_html_template(self) -> str:
        """Load HTML template content."""
        if not self.template_path.exists():
            logger.warning(f"HTML template not found: {self.template_path}")
            return self._get_default_template()
        
        try:
            with open(self.template_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading HTML template: {e}")
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Get default HTML template if template file is missing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{{ title }}</title>
        </head>
        <body>
            <h1>{{ template_name }}</h1>
            <p>{{ description }}</p>
            
            {% for section in sections %}
            <div class="section">
                <h2>{{ section.name }}</h2>
                {% for chart in section.charts %}
                <div class="chart">
                    <h3>{{ chart.name }}</h3>
                    <!-- Chart content will be inserted here -->
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </body>
        </html>
        """
