"""Template Service for managing report templates."""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class TemplateService:
    """Service for creating and managing report templates."""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            storage_dir = Path.home() / ".hvx" / "templates"
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Built-in templates directory
        self.builtin_dir = Path(__file__).parent.parent / "reporting" / "templates" / "library"

    def list_templates(self, include_builtin: bool = True) -> List[Dict[str, Any]]:
        """List all available templates."""
        templates = []

        # User templates
        if self.storage_dir.exists():
            for template_file in self.storage_dir.glob("*.yaml"):
                template_data = self._load_template_file(template_file)
                templates.append({
                    'name': template_file.stem,
                    'path': str(template_file),
                    'type': 'user',
                    'description': template_data.get('description', ''),
                    'created': template_data.get('metadata', {}).get('created', 'Unknown')
                })

        # Built-in templates
        if include_builtin and self.builtin_dir.exists():
            for template_dir in self.builtin_dir.iterdir():
                if template_dir.is_dir():
                    config_file = template_dir / "config.yaml"
                    if config_file.exists():
                        template_data = self._load_template_file(config_file)
                        templates.append({
                            'name': template_dir.name,
                            'path': str(template_dir),
                            'type': 'builtin',
                            'description': template_data.get('description', ''),
                            'created': 'Built-in'
                        })

        return templates

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by name."""
        # Check user templates first
        user_template = self.storage_dir / f"{name}.yaml"
        if user_template.exists():
            return self._load_template_file(user_template)

        # Check built-in templates
        builtin_template = self.builtin_dir / name / "config.yaml"
        if builtin_template.exists():
            return self._load_template_file(builtin_template)

        return None

    def create_template(self, name: str, template_config: Dict[str, Any]) -> Path:
        """Create a new template."""
        # Add metadata
        if 'metadata' not in template_config:
            template_config['metadata'] = {}

        template_config['metadata']['created'] = datetime.now().isoformat()
        template_config['metadata']['version'] = '1.0'

        # Save template
        template_path = self.storage_dir / f"{name}.yaml"

        with open(template_path, 'w') as f:
            yaml.dump(template_config, f, default_flow_style=False, sort_keys=False)

        return template_path

    def update_template(self, name: str, template_config: Dict[str, Any]) -> Path:
        """Update an existing template."""
        template_path = self.storage_dir / f"{name}.yaml"

        if not template_path.exists():
            raise ValueError(f"Template '{name}' not found")

        # Update metadata
        if 'metadata' not in template_config:
            template_config['metadata'] = {}

        template_config['metadata']['updated'] = datetime.now().isoformat()

        with open(template_path, 'w') as f:
            yaml.dump(template_config, f, default_flow_style=False, sort_keys=False)

        return template_path

    def delete_template(self, name: str) -> bool:
        """Delete a user template."""
        template_path = self.storage_dir / f"{name}.yaml"

        if not template_path.exists():
            return False

        template_path.unlink()
        return True

    def _load_template_file(self, path: Path) -> Dict[str, Any]:
        """Load template from YAML file."""
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def create_simple_template(
        self,
        name: str,
        title: str,
        description: str,
        chart_ids: List[str]
    ) -> Path:
        """Create a simple template with basic configuration."""
        template_config = {
            'name': name,
            'description': description,
            'report': {
                'title': title,
                'author': 'HVX Analytics',
                'layout': 'standard'
            },
            'sections': [
                {
                    'title': 'Executive Summary',
                    'type': 'summary',
                    'content': 'auto'
                },
                {
                    'title': 'Analytics Results',
                    'type': 'charts',
                    'charts': [{'id': chart_id} for chart_id in chart_ids]
                }
            ]
        }

        return self.create_template(name, template_config)
