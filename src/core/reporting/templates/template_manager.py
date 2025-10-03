"""
Template Manager for IEQ Analytics Reports

Manages the template library and provides interactive selection capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import yaml
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from .base_template import BaseTemplate

logger = logging.getLogger(__name__)
console = Console()


class TemplateManager:
    """Manages the template library and provides interactive selection."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir is None:
            # Default to library directory
            current_dir = Path(__file__).parent
            templates_dir = current_dir / "library"
        
        self.templates_dir = Path(templates_dir)
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all available templates from the library."""
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        for template_dir in self.templates_dir.iterdir():
            if template_dir.is_dir() and (template_dir / "config.yaml").exists():
                try:
                    template = BaseTemplate(template_dir)
                    self.templates[template.template_id] = template
                    logger.info(f"Loaded template: {template.template_id}")
                except Exception as e:
                    logger.error(f"Error loading template {template_dir.name}: {e}")
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available templates."""
        return {
            template_id: template.get_template_info()
            for template_id, template in self.templates.items()
        }
    
    def get_templates_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group templates by category."""
        categories = {}
        for template_id, template in self.templates.items():
            category = template.category
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'id': template_id,
                **template.get_template_info()
            })
        return categories
    
    def get_template(self, template_id: str) -> Optional[BaseTemplate]:
        """Get a specific template by ID."""
        return self.templates.get(template_id)
    
    def display_templates_table(self, category_filter: Optional[str] = None):
        """Display available templates in a formatted table."""
        table = Table(title="Available IEQ Analytics Templates")
        table.add_column("Template ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Category", style="green")
        table.add_column("Description", style="yellow")
        table.add_column("Sections", style="magenta")
        table.add_column("Charts", style="blue")
        table.add_column("Advanced Analytics", style="red")
        
        for template_id, template in self.templates.items():
            template_info = template.get_template_info()
            
            # Apply category filter if specified
            if category_filter and template_info['category'] != category_filter:
                continue
            
            table.add_row(
                template_id,
                template_info['name'],
                template_info['category'],
                template_info['description'][:50] + "..." if len(template_info['description']) > 50 else template_info['description'],
                str(template_info['sections_count']),
                str(template_info['charts_count']),
                "Yes" if template_info['has_advanced_analytics'] else "No"
            )
        
        console.print(table)
    
    def interactive_template_selection(self) -> Optional[str]:
        """Interactive template selection interface."""
        console.print("\n🎯 [bold]Template Selection[/bold]")
        
        # Show available categories
        categories = self.get_templates_by_category()
        
        if not categories:
            console.print("[red]❌ No templates available[/red]")
            return None
        
        console.print("\n📁 Available Categories:")
        for category, templates in categories.items():
            console.print(f"  • {category}: {len(templates)} templates")
        
        # Category selection
        if len(categories) > 1:
            category_choices = list(categories.keys()) + ["all"]
            selected_category = Prompt.ask(
                "Select category",
                choices=category_choices,
                default="all"
            )
        else:
            selected_category = list(categories.keys())[0]
        
        # Display templates table
        if selected_category != "all":
            self.display_templates_table(selected_category)
        else:
            self.display_templates_table()
        
        # Template selection
        template_choices = list(self.templates.keys())
        if not template_choices:
            console.print("[red]❌ No templates found[/red]")
            return None
        
        selected_template_id = Prompt.ask(
            "Select template ID",
            choices=template_choices
        )
        
        return selected_template_id
    
    def interactive_template_configuration(self, template_id: str) -> Dict[str, Any]:
        """Interactive configuration of selected template."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        console.print(f"\n🔧 [bold]Configuring Template: {template.template_name}[/bold]")
        console.print(f"📝 {template.description}")
        
        # Section selection
        available_sections = template.get_available_sections()
        selected_sections = self._select_sections(available_sections)
        
        # Chart selection
        available_charts = template.get_available_charts()
        selected_charts = self._select_charts(available_charts, selected_sections)
        
        # Filter configuration
        filter_options = template.get_filter_options()
        filter_settings = self._configure_filters(filter_options)
        
        # Advanced analytics configuration
        advanced_options = template.get_advanced_analytics_options()
        advanced_settings = self._configure_advanced_analytics(advanced_options)
        
        # Generate final configuration
        try:
            report_config = template.generate_report_config(
                selected_sections,
                selected_charts,
                filter_settings,
                advanced_settings
            )
            
            # Display configuration summary
            self._display_configuration_summary(report_config)
            
            if Confirm.ask("Proceed with this configuration?"):
                return report_config
            else:
                console.print("❌ Configuration cancelled")
                return {}
                
        except ValueError as e:
            console.print(f"[red]❌ Configuration error: {e}[/red]")
            return {}
    
    def _select_sections(self, available_sections: List[Dict[str, Any]]) -> List[str]:
        """Interactive section selection."""
        console.print("\n📋 [bold]Section Selection[/bold]")
        
        selected_sections = []
        
        for section in available_sections:
            section_info = f"{section['name']}"
            if section['required']:
                section_info += " [red](Required)[/red]"
                selected_sections.append(section['id'])
                console.print(f"  ✅ {section_info}")
            else:
                section_info += f" - {section.get('description', 'No description')}"
                if Confirm.ask(f"Include section: {section_info}?"):
                    selected_sections.append(section['id'])
        
        return selected_sections
    
    def _select_charts(self, available_charts: Dict[str, Any], selected_sections: List[str]) -> List[str]:
        """Interactive chart selection."""
        console.print("\n📊 [bold]Chart Selection[/bold]")
        
        selected_charts = []
        
        # Group charts by section for better organization
        section_charts = {}
        for chart_id, chart_config in available_charts.items():
            chart_sections = chart_config.get('sections', ['general'])
            for section in chart_sections:
                if section not in section_charts:
                    section_charts[section] = []
                section_charts[section].append(chart_id)
        
        for chart_id, chart_config in available_charts.items():
            chart_name = chart_config.get('name', chart_id)
            chart_description = chart_config.get('description', 'No description')
            chart_type = chart_config.get('type', 'unknown')
            
            chart_info = f"{chart_name} ({chart_type}) - {chart_description}"
            
            if Confirm.ask(f"Include chart: {chart_info}?"):
                selected_charts.append(chart_id)
        
        return selected_charts
    
    def _configure_filters(self, filter_options: Dict[str, Any]) -> Dict[str, Any]:
        """Interactive filter configuration."""
        console.print("\n🔍 [bold]Filter Configuration[/bold]")
        
        filter_settings = {}
        
        for filter_key, filter_config in filter_options.items():
            filter_type = filter_config.get('type', 'string')
            filter_name = filter_config.get('name', filter_key)
            filter_default = filter_config.get('default')
            
            if filter_type == 'choice':
                choices = filter_config.get('choices', [])
                if choices:
                    selected = Prompt.ask(
                        f"Select {filter_name}",
                        choices=choices,
                        default=str(filter_default) if filter_default else choices[0]
                    )
                    filter_settings[filter_key] = selected
            
            elif filter_type == 'multi_choice':
                choices = filter_config.get('choices', [])
                if choices:
                    console.print(f"Select {filter_name} (comma-separated):")
                    for i, choice in enumerate(choices):
                        console.print(f"  {i+1}. {choice}")
                    
                    selected = Prompt.ask(
                        f"Enter choices for {filter_name} (e.g., 1,2,3)",
                        default=""
                    )
                    
                    if selected:
                        try:
                            indices = [int(x.strip()) - 1 for x in selected.split(',')]
                            filter_settings[filter_key] = [choices[i] for i in indices if 0 <= i < len(choices)]
                        except:
                            filter_settings[filter_key] = []
                    else:
                        filter_settings[filter_key] = []
            
            elif filter_type == 'boolean':
                result = Confirm.ask(f"Enable {filter_name}?", default=bool(filter_default))
                filter_settings[filter_key] = result
            
            else:
                # Text input
                value = Prompt.ask(
                    f"Enter {filter_name}",
                    default=str(filter_default) if filter_default else ""
                )
                filter_settings[filter_key] = value
        
        return filter_settings
    
    def _configure_advanced_analytics(self, advanced_options: Dict[str, Any]) -> Dict[str, Any]:
        """Interactive advanced analytics configuration."""
        console.print("\n🔬 [bold]Advanced Analytics Configuration[/bold]")
        
        advanced_settings = {}
        
        for option_key, option_config in advanced_options.items():
            option_name = option_config.get('name', option_key)
            option_description = option_config.get('description', 'No description')
            
            console.print(f"\n📊 {option_name}")
            console.print(f"   {option_description}")
            
            if Confirm.ask(f"Enable {option_name}?"):
                advanced_settings[option_key] = {
                    'enabled': True
                }
                
                # Configure parameters if available
                parameters = option_config.get('parameters', {})
                for param_key, param_config in parameters.items():
                    param_name = param_config.get('name', param_key)
                    param_default = param_config.get('default')
                    param_type = param_config.get('type', 'string')
                    
                    if param_type == 'number':
                        value = float(Prompt.ask(
                            f"  {param_name}",
                            default=str(param_default) if param_default else "1.0"
                        ))
                    elif param_type == 'boolean':
                        value = Confirm.ask(f"  {param_name}?", default=bool(param_default))
                    else:
                        value = Prompt.ask(
                            f"  {param_name}",
                            default=str(param_default) if param_default else ""
                        )
                    
                    advanced_settings[option_key][param_key] = value
            else:
                advanced_settings[option_key] = {'enabled': False}
        
        return advanced_settings
    
    def _display_configuration_summary(self, report_config: Dict[str, Any]):
        """Display configuration summary."""
        summary_content = f"""
[bold]Template:[/bold] {report_config['template_name']}
[bold]Sections:[/bold] {len(report_config['sections'])}
[bold]Charts:[/bold] {len(report_config['charts'])}
[bold]Advanced Analytics:[/bold] {sum(1 for a in report_config['advanced_analytics'].values() if a.get('enabled', False))}

[bold]Selected Sections:[/bold]
{chr(10).join(f"  • {s['name']}" for s in report_config['sections'])}

[bold]Selected Charts:[/bold]
{chr(10).join(f"  • {chart_id}" for chart_id in report_config['charts'].keys())}

[bold]Advanced Analytics:[/bold]
{chr(10).join(f"  • {key}: {'Enabled' if config.get('enabled', False) else 'Disabled'}" for key, config in report_config['advanced_analytics'].items())}
        """
        
        panel = Panel.fit(
            summary_content,
            title="🎯 Configuration Summary",
            border_style="green"
        )
        console.print(panel)
