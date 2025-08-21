"""
Chart management commands for the IEQ Analytics CLI.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import click
import pandas as pd

from ieq_analytics.reporting.charts import (
    chart_registry, 
    list_available_charts, 
    search_charts,
    generate_chart
)
from ieq_analytics.reporting.charts.manager import get_chart_library_manager
from ieq_analytics.reporting.charts.template_integration import (
    TemplateChartIntegrator,
    create_template_with_chart_set,
    merge_templates
)


@click.group()
def charts():
    """Chart Library Management Commands."""
    pass


@charts.command()
@click.option('--category', help='Filter by category')
@click.option('--tag', help='Filter by tag')
@click.option('--output', '-o', help='Output format (table, json, yaml)', default='table')
def list(category: Optional[str], tag: Optional[str], output: str):
    """List available charts in the library."""
    
    charts_list = list_available_charts(category=category, tag=tag)
    
    if output == 'json':
        click.echo(json.dumps(charts_list, indent=2))
    elif output == 'yaml':
        click.echo(yaml.dump(charts_list, default_flow_style=False))
    else:
        # Table format
        if not charts_list:
            click.echo("No charts found.")
            return
        
        # Create a simplified table
        table_data = []
        for chart in charts_list:
            table_data.append({
                'ID': chart['chart_id'],
                'Name': chart['name'],
                'Category': chart['category'],
                'Tags': ', '.join(chart['tags'][:3])  # Limit tags for display
            })
        
        df = pd.DataFrame(table_data)
        click.echo(df.to_string(index=False))


@charts.command()
@click.argument('query')
@click.option('--output', '-o', help='Output format (table, json, yaml)', default='table')
def search(query: str, output: str):
    """Search charts by query."""
    
    charts_list = search_charts(query)
    
    if output == 'json':
        click.echo(json.dumps(charts_list, indent=2))
    elif output == 'yaml':
        click.echo(yaml.dump(charts_list, default_flow_style=False))
    else:
        # Table format
        if not charts_list:
            click.echo(f"No charts found matching '{query}'.")
            return
        
        # Create a simplified table
        table_data = []
        for chart in charts_list:
            table_data.append({
                'ID': chart['chart_id'],
                'Name': chart['name'],
                'Category': chart['category'],
                'Description': chart['description'][:50] + '...' if len(chart['description']) > 50 else chart['description']
            })
        
        df = pd.DataFrame(table_data)
        click.echo(df.to_string(index=False))


@charts.command()
@click.argument('chart_id')
def info(chart_id: str):
    """Get detailed information about a specific chart."""
    
    try:
        chart_info = chart_registry.get_chart_info(chart_id)
        
        click.echo(f"Chart ID: {chart_info['chart_id']}")
        click.echo(f"Name: {chart_info['name']}")
        click.echo(f"Category: {chart_info['category']}")
        click.echo(f"Description: {chart_info['description']}")
        click.echo(f"Tags: {', '.join(chart_info['tags'])}")
        click.echo(f"Required Data Keys: {', '.join(chart_info['required_data_keys'])}")
        click.echo(f"Optional Data Keys: {', '.join(chart_info['optional_data_keys'])}")
        
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)


@charts.command()
def categories():
    """List all available categories."""
    
    categories = chart_registry.list_categories()
    
    click.echo("Available Categories:")
    for category in sorted(categories):
        click.echo(f"  - {category}")


@charts.command()
def tags():
    """List all available tags."""
    
    tags = chart_registry.list_tags()
    
    click.echo("Available Tags:")
    for tag in sorted(tags):
        click.echo(f"  - {tag}")


@charts.command()
@click.argument('data_keys')
@click.option('--output', '-o', help='Output format (table, json, yaml)', default='table')
def recommend(data_keys: str, output: str):
    """Recommend charts based on available data keys."""
    
    manager = get_chart_library_manager()
    
    keys = set(k.strip() for k in data_keys.split(','))
    recommendations = manager.recommend_charts_for_data(keys)
    
    if output == 'json':
        click.echo(json.dumps(recommendations, indent=2, default=str))
    elif output == 'yaml':
        click.echo(yaml.dump(recommendations, default_flow_style=False))
    else:
        # Table format
        if not recommendations:
            click.echo("No chart recommendations found.")
            return
        
        # Create a simplified table
        table_data = []
        for chart in recommendations:
            table_data.append({
                'ID': chart['chart_id'],
                'Name': chart['name'],
                'Category': chart['category'],
                'Match Score': f"{chart.get('match_score', 0):.2f}"
            })
        
        df = pd.DataFrame(table_data)
        click.echo(df.to_string(index=False))


@charts.group()
def sets():
    """Chart set management commands."""
    pass


@sets.command('list')
def list_sets():
    """List available chart sets."""
    
    manager = get_chart_library_manager()
    chart_sets = manager.get_available_chart_sets()
    
    if not chart_sets:
        click.echo("No chart sets found.")
        return
    
    for set_name, set_info in chart_sets.items():
        click.echo(f"\n{set_name}:")
        click.echo(f"  Description: {set_info.get('description', 'No description')}")
        click.echo(f"  Charts: {', '.join(set_info.get('charts', []))}")
        click.echo(f"  Tags: {', '.join(set_info.get('tags', []))}")


@sets.command('info')
@click.argument('set_name')
def set_info(set_name: str):
    """Get information about a specific chart set."""
    
    manager = get_chart_library_manager()
    chart_sets = manager.get_available_chart_sets()
    
    if set_name not in chart_sets:
        click.echo(f"Chart set '{set_name}' not found.", err=True)
        return
    
    set_info = chart_sets[set_name]
    click.echo(f"Chart Set: {set_name}")
    click.echo(f"Description: {set_info.get('description', 'No description')}")
    click.echo(f"Tags: {', '.join(set_info.get('tags', []))}")
    click.echo("\nCharts:")
    
    for chart_id in set_info.get('charts', []):
        try:
            chart_info = chart_registry.get_chart_info(chart_id)
            click.echo(f"  - {chart_id}: {chart_info['name']}")
        except ValueError:
            click.echo(f"  - {chart_id}: (Chart not found)")


@charts.group()
def template():
    """Template integration commands."""
    pass


@template.command('create')
@click.argument('template_name')
@click.argument('chart_set')
@click.option('--output', '-o', help='Output file path', required=True)
@click.option('--description', help='Template description')
def create_template(template_name: str, chart_set: str, output: str, description: Optional[str]):
    """Create a new template from a chart set."""
    
    try:
        base_config = {'description': description} if description else {}
        template_config = create_template_with_chart_set(template_name, chart_set, base_config)
        
        output_path = Path(output)
        with open(output_path, 'w') as f:
            yaml.dump(template_config, f, default_flow_style=False)
        
        click.echo(f"Template '{template_name}' created at {output_path}")
        
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)


@template.command('validate')
@click.argument('template_file')
def validate_template(template_file: str):
    """Validate a template configuration."""
    
    template_path = Path(template_file)
    
    if not template_path.exists():
        click.echo(f"Template file '{template_file}' not found.", err=True)
        return
    
    try:
        with open(template_path, 'r') as f:
            template_config = yaml.safe_load(f)
        
        integrator = TemplateChartIntegrator(template_config)
        validation = integrator.validate_template_charts()
        
        if validation['valid']:
            click.echo("✓ Template is valid.")
        else:
            click.echo("✗ Template validation failed:")
            
            if validation['missing_charts']:
                click.echo(f"  Missing charts: {', '.join(validation['missing_charts'])}")
            
            if validation['invalid_data_requirements']:
                click.echo("  Invalid data requirements:")
                for req in validation['invalid_data_requirements']:
                    click.echo(f"    {req['chart_id']}: missing {', '.join(req['missing_keys'])}")
        
        if validation['warnings']:
            click.echo("Warnings:")
            for warning in validation['warnings']:
                click.echo(f"  - {warning}")
    
    except Exception as e:
        click.echo(f"Error validating template: {e}", err=True)
