"""
Generate Smart Recommendations Report

Analyzes all room analyses and generates targeted recommendations for:
- Solar shading needs
- Insulation improvements  
- Ventilation strategies
- Natural ventilation conflicts
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.markdown import Markdown

from src.services.smart_recommendations_service import (
    SmartRecommendationsService,
    generate_building_recommendations_report,
    Priority,
    RecommendationType
)
from src.models.analysis_models import RoomAnalysis

console = Console()


def load_room_analyses(analysis_dir: Path) -> dict:
    """Load all room analysis files."""
    room_analyses = {}
    rooms_dir = analysis_dir / 'rooms'
    
    if not rooms_dir.exists():
        console.print(f"[red]Error: Rooms directory not found: {rooms_dir}[/red]")
        return {}
    
    for room_file in rooms_dir.glob('*.json'):
        try:
            room_analysis = RoomAnalysis.load_from_json(room_file)
            room_analyses[room_analysis.room_id] = room_analysis
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load {room_file.name}: {e}[/yellow]")
            continue
    
    return room_analyses


def print_executive_summary(report: dict):
    """Print executive summary."""
    summary = report['summary']
    
    console.print("\n[bold cyan]═══ SMART RECOMMENDATIONS REPORT ═══[/bold cyan]\n")
    
    # Summary table
    table = Table(box=box.ROUNDED, show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")
    
    table.add_row("Total Rooms Analyzed", str(summary['total_rooms_analyzed']))
    table.add_row("Rooms with Recommendations", str(summary['rooms_with_recommendations']))
    table.add_row("Total Recommendations", str(summary['total_recommendations']))
    table.add_row("", "")
    table.add_row("[red]Critical Priority[/red]", f"[red]{summary['priority_breakdown']['critical']}[/red]")
    table.add_row("[yellow]High Priority[/yellow]", f"[yellow]{summary['priority_breakdown']['high']}[/yellow]")
    table.add_row("[cyan]Medium Priority[/cyan]", f"[cyan]{summary['priority_breakdown']['medium']}[/cyan]")
    table.add_row("[green]Low Priority[/green]", f"[green]{summary['priority_breakdown']['low']}[/green]")
    
    console.print(table)
    
    # Key findings
    console.print("\n[bold]Key Findings:[/bold]\n")
    console.print(f"  🌞 {summary['rooms_needing_solar_shading']} rooms need solar shading")
    console.print(f"  🏠 {summary['rooms_needing_insulation']} rooms need insulation improvements")
    console.print(f"  💨 {summary['rooms_needing_mechanical_ventilation']} rooms need mechanical ventilation")
    console.print(f"  ⚠️  {summary['rooms_with_ventilation_conflicts']} rooms have ventilation conflicts")


def print_critical_actions(report: dict):
    """Print critical actions that need immediate attention."""
    critical_actions = report.get('critical_actions', [])
    
    if not critical_actions:
        console.print("\n[green]✓ No critical issues found[/green]\n")
        return
    
    console.print("\n[bold red]═══ CRITICAL ACTIONS REQUIRED ═══[/bold red]\n")
    
    for action in critical_actions:
        console.print(f"\n[bold yellow]Room: {action['room_name']}[/bold yellow] ([dim]{action['room_id']}[/dim])")
        
        for rec in action['recommendations']:
            panel = Panel(
                rec['description'],
                title=f"[red]🚨 {rec['title']}[/red]",
                border_style="red",
                expand=False
            )
            console.print(panel)


def print_ventilation_conflicts(report: dict, room_analyses: dict):
    """Print detailed ventilation conflicts."""
    conflicts_by_room = report.get('ventilation_conflicts', {})
    
    if not conflicts_by_room:
        console.print("\n[green]✓ No ventilation conflicts detected[/green]\n")
        return
    
    console.print("\n[bold cyan]═══ VENTILATION CONFLICTS ANALYSIS ═══[/bold cyan]\n")
    console.print("[dim]Conflicts occur when natural ventilation creates trade-offs between air quality and temperature[/dim]\n")
    
    for room_id, conflicts in conflicts_by_room.items():
        room = room_analyses.get(room_id)
        room_name = room.room_name if room else room_id
        
        console.print(f"\n[bold]📍 {room_name}[/bold]")
        
        for conflict in conflicts:
            severity_color = "red" if conflict.severity == "HIGH" else "yellow"
            season_emoji = "❄️" if conflict.season == "winter" else "☀️"
            
            console.print(f"\n  {season_emoji} [bold {severity_color}]{conflict.season.upper()} CONFLICT[/bold {severity_color}]")
            console.print(f"     {conflict.description}")
            console.print(f"     CO2 Compliance: [{severity_color}]{conflict.co2_compliance:.1f}%[/{severity_color}]")
            console.print(f"     Temperature Compliance: [{severity_color}]{conflict.temp_compliance:.1f}%[/{severity_color}]")
            
            if conflict.outdoor_temp_during_co2_issues:
                avg_temp = conflict.outdoor_temp_during_co2_issues.get('mean', 0)
                min_temp = conflict.outdoor_temp_during_co2_issues.get('min', 0)
                max_temp = conflict.outdoor_temp_during_co2_issues.get('max', 0)
                console.print(f"     Outdoor temp during CO2 issues: {avg_temp:.1f}°C (range: {min_temp:.1f} to {max_temp:.1f}°C)")


def print_recommendations_by_type(report: dict, room_analyses: dict):
    """Print recommendations grouped by type."""
    console.print("\n[bold cyan]═══ RECOMMENDATIONS BY TYPE ═══[/bold cyan]\n")
    
    room_recs = report.get('room_recommendations', {})
    
    # Group by type
    by_type = {}
    for room_id, recs in room_recs.items():
        for rec in recs:
            type_key = rec.type.value
            if type_key not in by_type:
                by_type[type_key] = []
            by_type[type_key].append((room_id, rec))
    
    type_names = {
        'solar_shading': '🌞 Solar Shading',
        'insulation': '🏠 Insulation',
        'mechanical_ventilation': '💨 Mechanical Ventilation',
        'natural_ventilation': '🌬️  Natural Ventilation',
        'hvac_control': '🌡️  HVAC Control',
        'operational': '⚙️  Operational'
    }
    
    for type_key in ['solar_shading', 'insulation', 'mechanical_ventilation', 'natural_ventilation']:
        if type_key not in by_type:
            continue
        
        items = by_type[type_key]
        console.print(f"\n[bold]{type_names.get(type_key, type_key)}[/bold] ({len(items)} rooms)")
        console.print("─" * 80)
        
        # Group by priority
        by_priority = {}
        for room_id, rec in items:
            priority = rec.priority.value
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append((room_id, rec))
        
        # Show by priority
        for priority in ['critical', 'high', 'medium', 'low']:
            if priority not in by_priority:
                continue
            
            priority_items = by_priority[priority]
            priority_color = {
                'critical': 'red',
                'high': 'yellow',
                'medium': 'cyan',
                'low': 'green'
            }[priority]
            
            console.print(f"\n  [{priority_color}]{priority.upper()}[/{priority_color}] ({len(priority_items)} rooms):")
            
            for room_id, rec in priority_items[:5]:  # Show top 5 per priority
                room = room_analyses.get(room_id)
                room_name = room.room_name if room else room_id
                
                console.print(f"\n    • [bold]{room_name}[/bold]")
                console.print(f"      {rec.title}")
                
                # Show key evidence
                if rec.evidence:
                    if 'worst_summer_compliance' in rec.evidence:
                        console.print(f"      Summer compliance: {rec.evidence['worst_summer_compliance']:.1f}%")
                    if 'outdoor_temp_correlation' in rec.evidence and rec.evidence['outdoor_temp_correlation'] != 0:
                        corr = rec.evidence['outdoor_temp_correlation']
                        console.print(f"      Outdoor temp correlation: {corr:+.3f}")
                    if 'radiation_correlation' in rec.evidence and rec.evidence['radiation_correlation'] > 0:
                        corr = rec.evidence['radiation_correlation']
                        console.print(f"      Solar radiation correlation: {corr:+.3f}")
                    if 'worst_cold_compliance' in rec.evidence:
                        console.print(f"      Winter compliance: {rec.evidence['worst_cold_compliance']:.1f}%")
                    if 'worst_co2_compliance' in rec.evidence:
                        console.print(f"      CO2 compliance: {rec.evidence['worst_co2_compliance']:.1f}%")
                
                if rec.estimated_impact:
                    console.print(f"      [dim]Impact: {rec.estimated_impact}[/dim]")
            
            if len(priority_items) > 5:
                console.print(f"\n    [dim]... and {len(priority_items) - 5} more rooms[/dim]")


def save_detailed_report(report: dict, room_analyses: dict, output_file: Path):
    """Save detailed report to JSON."""
    # Convert to serializable format
    detailed_report = {
        'summary': report['summary'],
        'by_recommendation_type': report['by_recommendation_type'],
        'rooms': {}
    }
    
    for room_id, recs in report['room_recommendations'].items():
        room = room_analyses.get(room_id)
        detailed_report['rooms'][room_id] = {
            'room_name': room.room_name if room else room_id,
            'recommendations': [
                {
                    'type': rec.type.value,
                    'priority': rec.priority.value,
                    'title': rec.title,
                    'description': rec.description,
                    'rationale': rec.rationale,
                    'evidence': rec.evidence,
                    'estimated_impact': rec.estimated_impact,
                    'implementation_cost': rec.implementation_cost
                }
                for rec in recs
            ]
        }
    
    # Add conflicts
    conflicts_data = {}
    for room_id, conflicts in report.get('ventilation_conflicts', {}).items():
        conflicts_data[room_id] = [
            {
                'season': c.season,
                'conflict_type': c.conflict_type,
                'co2_compliance': c.co2_compliance,
                'temp_compliance': c.temp_compliance,
                'outdoor_temp_during_co2_issues': c.outdoor_temp_during_co2_issues,
                'severity': c.severity,
                'description': c.description
            }
            for c in conflicts
        ]
    detailed_report['ventilation_conflicts'] = conflicts_data
    
    with open(output_file, 'w') as f:
        json.dump(detailed_report, f, indent=2)
    
    console.print(f"\n[green]✓ Detailed report saved to: {output_file}[/green]")


def main():
    """Main function."""
    analysis_dir = Path('output/analysis')
    
    if not analysis_dir.exists():
        console.print(f"[red]Error: Analysis directory not found: {analysis_dir}[/red]")
        console.print("[yellow]Run analysis first: python3 -m src.cli.main analyze run output/dataset.pkl[/yellow]")
        return
    
    console.print("\n[cyan]Loading room analyses...[/cyan]")
    room_analyses = load_room_analyses(analysis_dir)
    
    if not room_analyses:
        console.print("[red]Error: No room analyses found[/red]")
        return
    
    console.print(f"[green]✓ Loaded {len(room_analyses)} room analyses[/green]")
    
    console.print("[cyan]Generating smart recommendations...[/cyan]")
    report = generate_building_recommendations_report(room_analyses)
    
    # Print reports
    print_executive_summary(report)
    print_critical_actions(report)
    print_ventilation_conflicts(report, room_analyses)
    print_recommendations_by_type(report, room_analyses)
    
    # Save detailed report
    output_file = analysis_dir / 'smart_recommendations.json'
    save_detailed_report(report, room_analyses, output_file)
    
    console.print("\n[bold green]═══ REPORT COMPLETE ═══[/bold green]\n")


if __name__ == '__main__':
    main()
