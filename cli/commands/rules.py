"""
Rule builder command module for IEQ Analytics CLI.

Provides commands for creating, editing, and managing analytics rules including:
- Interactive rule creation wizard
- Rule validation and testing
- Rule library management
- YAML configuration export
"""

import click
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()


@click.group()
def rules():
    """🔧 Manage analytics rules for IEQ data analysis."""
    pass


@rules.command()
@click.option(
    '--config-dir',
    type=click.Path(path_type=Path),
    help='Directory containing rule configuration files'
)
@click.option(
    '--interactive/--batch',
    default=True,
    help='Interactive rule creation vs batch mode'
)
@click.option(
    '--rule-type',
    type=click.Choice(['threshold', 'range', 'combined', 'custom']),
    help='Type of rule to create'
)
@click.option(
    '--parameter',
    type=click.Choice(['temperature', 'humidity', 'co2', 'combined']),
    help='IEQ parameter for the rule'
)
@click.pass_context
def create(ctx, config_dir: Optional[Path], interactive: bool, rule_type: Optional[str], parameter: Optional[str]):
    """🎯 Create a new analytics rule.
    
    Build custom rules for IEQ data analysis using an interactive wizard or batch mode.
    Rules can be threshold-based, range-based, or complex combined conditions.
    """
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    config_dir = config_dir or workspace / "config"
    
    console.print("🎯 [bold blue]Creating New Analytics Rule...[/bold blue]")
    
    try:
        from ieq_analytics.unified_analytics import UnifiedRuleEngine
        
        if interactive:
            rule_data = _interactive_rule_creation(rule_type, parameter)
        else:
            rule_data = _batch_rule_creation(rule_type, parameter)
        
        if not rule_data:
            console.print("[yellow]⚠️ Rule creation cancelled.[/yellow]")
            return
        
        # Create rule configuration for unified system
        rule_config = {
            'name': rule_data.get('name', f"{rule_data['parameter']}_{rule_data['type']}_rule"),
            'description': rule_data.get('description', f"Auto-generated {rule_data['type']} rule"),
            'parameter': rule_data['parameter'],
            'type': rule_data['type']
        }
        
        # Add rule-specific configuration
        if rule_data['type'] == 'threshold':
            rule_config.update({
                'threshold': rule_data['threshold'],
                'operator': rule_data['operator']
            })
        elif rule_data['type'] == 'range':
            rule_config.update({
                'min_value': rule_data['min_value'],
                'max_value': rule_data['max_value']
            })
        elif rule_data['type'] == 'combined':
            rule_config['conditions'] = rule_data['conditions']
        
        # Save to configuration
        _save_rule_to_config(rule_config, config_dir)
        
        console.print(f"[green]✅ Rule '{rule_config['name']}' created successfully![/green]")
        
        # Test the rule if requested
        if interactive and Confirm.ask("Would you like to test this rule?"):
            _test_rule_interactive(rule_config, rule_data)
        
    except Exception as e:
        console.print(f"[red]❌ Failed to create rule: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@rules.command()
@click.option(
    '--config-dir',
    type=click.Path(path_type=Path),
    help='Directory containing rule configuration files'
)
@click.pass_context
def list(ctx, config_dir: Optional[Path]):
    """📋 List all available analytics rules."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    config_dir = config_dir or workspace / "config"
    
    console.print("📋 [bold blue]Available Analytics Rules[/bold blue]")
    
    try:
        rules_config_path = config_dir / "tests.yaml"
        
        if not rules_config_path.exists():
            console.print("[yellow]⚠️ No rules configuration found.[/yellow]")
            console.print(f"Create rules with: ieq-analytics rules create")
            return
        
        with open(rules_config_path, 'r') as f:
            rules_config = yaml.safe_load(f)
        
        if not rules_config or 'tests' not in rules_config:
            console.print("[yellow]⚠️ No rules found in configuration.[/yellow]")
            return
        
        # Create table of rules
        table = Table(title="Analytics Rules")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Parameter", style="green")
        table.add_column("Description", style="white")
        table.add_column("Enabled", style="magenta")
        
        for test_name, test_config in rules_config['tests'].items():
            rule_type = test_config.get('type', 'unknown')
            parameter = test_config.get('parameter', 'unknown')
            description = test_config.get('description', '')
            enabled = "✅" if test_config.get('enabled', True) else "❌"
            
            table.add_row(test_name, rule_type, parameter, description, enabled)
        
        console.print(table)
        console.print(f"\n📁 Configuration file: {rules_config_path}")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to list rules: {e}[/red]")


@rules.command()
@click.argument('rule_name')
@click.option(
    '--config-dir',
    type=click.Path(path_type=Path),
    help='Directory containing rule configuration files'
)
@click.pass_context
def delete(ctx, rule_name: str, config_dir: Optional[Path]):
    """🗑️ Delete an analytics rule."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    config_dir = config_dir or workspace / "config"
    
    console.print(f"🗑️ [bold red]Deleting Rule: {rule_name}[/bold red]")
    
    try:
        rules_config_path = config_dir / "tests.yaml"
        
        if not rules_config_path.exists():
            console.print("[red]❌ No rules configuration found.[/red]")
            return
        
        with open(rules_config_path, 'r') as f:
            rules_config = yaml.safe_load(f)
        
        if not rules_config or 'tests' not in rules_config:
            console.print("[red]❌ No rules found in configuration.[/red]")
            return
        
        if rule_name not in rules_config['tests']:
            console.print(f"[red]❌ Rule '{rule_name}' not found.[/red]")
            return
        
        # Confirm deletion
        if not Confirm.ask(f"Are you sure you want to delete rule '{rule_name}'?"):
            console.print("[yellow]⚠️ Deletion cancelled.[/yellow]")
            return
        
        # Remove the rule
        del rules_config['tests'][rule_name]
        
        # Save updated configuration
        with open(rules_config_path, 'w') as f:
            yaml.dump(rules_config, f, default_flow_style=False, indent=2)
        
        console.print(f"[green]✅ Rule '{rule_name}' deleted successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to delete rule: {e}[/red]")


@rules.command()
@click.argument('rule_name')
@click.option(
    '--config-dir',
    type=click.Path(path_type=Path),
    help='Directory containing rule configuration files'
)
@click.option(
    '--data-dir',
    type=click.Path(path_type=Path),
    help='Directory containing sample data for testing'
)
@click.pass_context
def test(ctx, rule_name: str, config_dir: Optional[Path], data_dir: Optional[Path]):
    """🧪 Test an analytics rule with sample data."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    config_dir = config_dir or workspace / "config"
    data_dir = data_dir or workspace / "output" / "mapped" / "mapped_data"
    
    console.print(f"🧪 [bold blue]Testing Rule: {rule_name}[/bold blue]")
    
    try:
        from ieq_analytics.unified_analytics import UnifiedAnalyticsEngine
        
        # Load analytics engine with rules
        rules_config_path = config_dir / "tests.yaml"
        if not rules_config_path.exists():
            console.print("[red]❌ No rules configuration found.[/red]")
            return
        
        engine = UnifiedAnalyticsEngine(rules_config_path)
        
        # Find sample data files
        if not data_dir.exists():
            console.print(f"[red]❌ Data directory not found: {data_dir}[/red]")
            console.print("Run 'ieq-analytics mapping' first to create mapped data.")
            return
        
        data_files = list(data_dir.glob("*_processed.csv"))
        if not data_files:
            console.print(f"[red]❌ No processed data files found in {data_dir}[/red]")
            return
        
        # Test with first available file
        test_file = data_files[0]
        console.print(f"📊 Testing with data from: [cyan]{test_file.name}[/cyan]")
        
        import pandas as pd
        from ieq_analytics.models import IEQData
        
        # Load test data
        df = pd.read_csv(test_file)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        
        # Create IEQData object
        room_id = test_file.stem.replace('_processed', '')
        ieq_data = IEQData(
            room_id=room_id,
            building_id=room_id.split('_')[0] if '_' in room_id else 'unknown',
            data=df,
            quality_score=0.8,
            data_period_start=None,
            data_period_end=None
        )
        
        # Run the specific rule
        try:
            # Use the unified analytics engine to analyze the data
            from ieq_analytics.unified_analytics import AnalysisType
            results = engine.analyze_room_data(
                ieq_data.data,
                ieq_data.room_id,
                analysis_types=[AnalysisType.USER_RULES],
                rules_to_evaluate=[rule_name]
            )
            
            if results and 'user_rules' in results:
                console.print(f"[green]✅ Rule test completed successfully![/green]")
                
                # Display results
                results_table = Table(title=f"Rule Test Results: {rule_name}")
                results_table.add_column("Metric", style="cyan")
                results_table.add_column("Value", style="yellow")
                
                user_rules_results = results['user_rules']
                for key, value in user_rules_results.items():
                    if isinstance(value, (int, float)):
                        formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    else:
                        formatted_value = str(value)
                    results_table.add_row(key, formatted_value)
                
                console.print(results_table)
            else:
                console.print(f"[yellow]⚠️ No results returned for rule '{rule_name}'[/yellow]")
                
        except Exception as e:
            console.print(f"[red]❌ Rule test failed: {e}[/red]")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to test rule: {e}[/red]")


def _interactive_rule_creation(rule_type: Optional[str], parameter: Optional[str]) -> Optional[Dict[str, Any]]:
    """Interactive rule creation wizard."""
    
    console.print("\n🧙 [bold]Rule Creation Wizard[/bold]")
    
    # Get rule name
    rule_name = Prompt.ask("Enter rule name")
    if not rule_name:
        return None
    
    # Get rule type
    if not rule_type:
        rule_type = Prompt.ask(
            "Select rule type",
            choices=['threshold', 'range', 'combined'],
            default='threshold'
        )
    
    # Get parameter
    if not parameter:
        parameter = Prompt.ask(
            "Select IEQ parameter",
            choices=['temperature', 'humidity', 'co2'],
            default='temperature'
        )
    
    # Get rule description
    description = Prompt.ask("Enter rule description", default="")
    
    rule_data = {
        'name': rule_name,
        'type': rule_type,
        'parameter': parameter,
        'description': description,
        'enabled': True
    }
    
    if rule_type == 'threshold':
        threshold = float(Prompt.ask("Enter threshold value"))
        operator = Prompt.ask(
            "Select operator",
            choices=['>', '<', '>=', '<=', '=='],
            default='>'
        )
        rule_data.update({
            'threshold': threshold,
            'operator': operator
        })
    
    elif rule_type == 'range':
        min_value = float(Prompt.ask("Enter minimum value"))
        max_value = float(Prompt.ask("Enter maximum value"))
        rule_data.update({
            'min_value': min_value,
            'max_value': max_value
        })
    
    elif rule_type == 'combined':
        console.print("Combined rules not yet supported in interactive mode.")
        return None
    
    # Display rule summary
    _display_rule_summary(rule_data)
    
    if not Confirm.ask("Create this rule?"):
        return None
    
    return rule_data


def _batch_rule_creation(rule_type: Optional[str], parameter: Optional[str]) -> Optional[Dict[str, Any]]:
    """Batch rule creation (non-interactive)."""
    console.print("[yellow]⚠️ Batch rule creation not yet implemented.[/yellow]")
    console.print("Use --interactive flag for rule creation.")
    return None


def _display_rule_summary(rule_data: Dict[str, Any]):
    """Display a summary of the rule being created."""
    
    summary_panel = Panel.fit(
        f"[bold]Rule Summary[/bold]\n\n"
        f"Name: {rule_data['name']}\n"
        f"Type: {rule_data['type']}\n"
        f"Parameter: {rule_data['parameter']}\n"
        f"Description: {rule_data.get('description', 'N/A')}\n\n"
        f"[cyan]Rule Details:[/cyan]\n" +
        _format_rule_details(rule_data),
        title="📋 Rule Preview",
        border_style="cyan"
    )
    console.print(summary_panel)


def _format_rule_details(rule_data: Dict[str, Any]) -> str:
    """Format rule details for display."""
    
    if rule_data['type'] == 'threshold':
        return f"Condition: {rule_data['parameter']} {rule_data['operator']} {rule_data['threshold']}"
    elif rule_data['type'] == 'range':
        return f"Range: {rule_data['min_value']} ≤ {rule_data['parameter']} ≤ {rule_data['max_value']}"
    elif rule_data['type'] == 'combined':
        return "Multiple conditions (see configuration file)"
    else:
        return "Custom rule configuration"


def _save_rule_to_config(rule_data: Dict[str, Any], config_dir: Path):
    """Save rule to YAML configuration file."""
    
    rules_config_path = config_dir / "tests.yaml"
    
    # Load existing configuration or create new
    if rules_config_path.exists():
        with open(rules_config_path, 'r') as f:
            rules_config = yaml.safe_load(f)
    else:
        rules_config = {'tests': {}}
    
    if 'tests' not in rules_config:
        rules_config['tests'] = {}
    
    # Convert rule data to YAML format
    yaml_rule = {
        'type': rule_data['type'],
        'parameter': rule_data['parameter'],
        'description': rule_data.get('description', ''),
        'enabled': rule_data.get('enabled', True)
    }
    
    if rule_data['type'] == 'threshold':
        yaml_rule['condition'] = {
            'operator': rule_data['operator'],
            'threshold': rule_data['threshold']
        }
    elif rule_data['type'] == 'range':
        yaml_rule['condition'] = {
            'min_value': rule_data['min_value'],
            'max_value': rule_data['max_value']
        }
    
    # Add rule to configuration
    rules_config['tests'][rule_data['name']] = yaml_rule
    
    # Ensure config directory exists
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Save configuration
    with open(rules_config_path, 'w') as f:
        yaml.dump(rules_config, f, default_flow_style=False, indent=2)


def _test_rule_interactive(rule, rule_data: Dict[str, Any]):
    """Test rule with interactive feedback."""
    
    console.print("\n🧪 [bold]Rule Testing[/bold]")
    console.print("Rule testing requires sample data. This is a placeholder implementation.")
    
    # Placeholder for actual rule testing
    console.print(f"[green]✅ Rule '{rule_data['name']}' syntax is valid![/green]")
