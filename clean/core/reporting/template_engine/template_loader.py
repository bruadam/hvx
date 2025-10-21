"""Template loader for reading and parsing YAML report templates."""

from pathlib import Path
from typing import Dict, Any
import yaml

from core.reporting.template_engine.report_template import ReportTemplate


class TemplateLoader:
    """Load and parse report templates from YAML files."""

    @staticmethod
    def load_from_file(template_path: Path) -> ReportTemplate:
        """
        Load report template from YAML file.

        Args:
            template_path: Path to YAML template file

        Returns:
            Parsed ReportTemplate

        Raises:
            FileNotFoundError: If template file doesn't exist
            yaml.YAMLError: If YAML is malformed
            ValueError: If template validation fails
        """
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template_data = yaml.safe_load(f)

        if not template_data:
            raise ValueError(f"Empty template file: {template_path}")

        try:
            template = ReportTemplate(**template_data)
            return template
        except Exception as e:
            raise ValueError(f"Invalid template format: {e}") from e

    @staticmethod
    def load_from_dict(template_data: Dict[str, Any]) -> ReportTemplate:
        """
        Load report template from dictionary.

        Args:
            template_data: Template configuration as dict

        Returns:
            Parsed ReportTemplate

        Raises:
            ValueError: If template validation fails
        """
        try:
            template = ReportTemplate(**template_data)
            return template
        except Exception as e:
            raise ValueError(f"Invalid template format: {e}") from e

    @staticmethod
    def save_template(template: ReportTemplate, output_path: Path) -> None:
        """
        Save report template to YAML file.

        Args:
            template: ReportTemplate to save
            output_path: Path where to save YAML file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save as YAML
        template_dict = template.model_dump(exclude_none=True)

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                template_dict,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    @staticmethod
    def list_templates(templates_dir: Path) -> Dict[str, Path]:
        """
        List all available templates in directory.

        Args:
            templates_dir: Directory containing template files

        Returns:
            Dict mapping template names to file paths
        """
        if not templates_dir.exists():
            return {}

        templates = {}
        for yaml_file in templates_dir.glob("*.yaml"):
            try:
                template = TemplateLoader.load_from_file(yaml_file)
                templates[template.template_name] = yaml_file
            except Exception:
                # Skip invalid templates
                continue

        return templates
