"""
Climate correlation analysis command for the CLI
"""
import click
import json
import logging
from pathlib import Path
from typing import Optional

from ieq_analytics.climate_analytics import ClimateAnalytics


logger = logging.getLogger(__name__)


@click.command()
@click.option('--climate-dir', 
              type=click.Path(exists=True, path_type=Path),
              default="data/climate",
              help='Directory containing climate data files')
@click.option('--indoor-dir', 
              type=click.Path(exists=True, path_type=Path),
              default="output/mapped_data",
              help='Directory containing processed indoor sensor data')
@click.option('--output-dir', 
              type=click.Path(path_type=Path),
              default="output/climate_analysis",
              help='Output directory for analysis results')
@click.option('--school', 
              type=str,
              help='Specific school name to analyze (optional)')
@click.option('--room', 
              type=str,
              help='Specific room ID to analyze (optional)')
@click.option('--generate-plots', 
              is_flag=True,
              help='Generate correlation visualization plots')
@click.option('--focus-high-temp', 
              is_flag=True,
              help='Focus analysis on high temperature periods for solar shading assessment')
def climate(climate_dir: Path, indoor_dir: Path, output_dir: Path, 
           school: Optional[str], room: Optional[str], 
           generate_plots: bool, focus_high_temp: bool):
    """
    Analyze correlations between outdoor climate conditions and indoor temperature.
    
    This command performs correlation analysis to assess:
    - Overall correlations between outdoor parameters and indoor temperature
    - Monthly and seasonal patterns
    - Day period analysis (morning, afternoon, evening, night)
    - High temperature sensitivity analysis
    - Solar radiation sensitivity for shading recommendations
    
    Example usage:
    
    # Analyze all rooms for climate correlations
    python -m cli climate
    
    # Analyze specific school and room
    python -m cli climate --school floeng_skole --room fløng_skole_0.078
    
    # Generate visualization plots and focus on high temperatures
    python -m cli climate --generate-plots --focus-high-temp
    """
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting climate correlation analysis...")
    logger.info(f"Climate data directory: {climate_dir}")
    logger.info(f"Indoor data directory: {indoor_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        # Initialize climate analytics
        analytics = ClimateAnalytics(
            climate_data_dir=str(climate_dir),
            indoor_data_dir=str(indoor_dir)
        )
        
        if school and room:
            # Analyze specific room
            logger.info(f"Analyzing specific room: {school} - {room}")
            report = analytics.generate_correlation_report(school, room)
            
            # Save report
            report_file = output_dir / f"{school}_{room}_climate_correlation.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Report saved to: {report_file}")
            
            # Print key findings
            if 'error' not in report:
                print_key_findings(report)
            
            # Generate plots if requested
            if generate_plots and 'error' not in report:
                analytics.load_climate_data()
                analytics.load_indoor_data()
                merged_df = analytics.merge_climate_indoor_data(school, room)
                if not merged_df.empty:
                    merged_df = analytics.add_time_features(merged_df)
                    
                    # Create plots for each available climate parameter
                    climate_params = [col for col in merged_df.columns if col not in 
                                    ['timestamp_indoor', 'timestamp_climate', 'timestamp_hour', 
                                     'temperature', 'humidity', 'co2', 'hour', 'month', 
                                     'season', 'day_period', 'weekday', 'is_weekend']]
                    
                    for param in climate_params:
                        plot_file = output_dir / f"{school}_{room}_{param}_correlation_plot.png"
                        analytics.create_correlation_visualization(
                            merged_df, 
                            climate_param=param,
                            output_path=str(plot_file)
                        )
                        logger.info(f"Plot saved to: {plot_file}")
        
        else:
            # Analyze all rooms
            logger.info("Analyzing all available rooms...")
            all_reports = analytics.analyze_all_rooms()
            
            # Save comprehensive report
            all_reports_file = output_dir / "all_rooms_climate_correlation.json"
            with open(all_reports_file, 'w') as f:
                json.dump(all_reports, f, indent=2, default=str)
            
            logger.info(f"Comprehensive report saved to: {all_reports_file}")
            
            # Generate summary
            summary = generate_summary_report(all_reports, focus_high_temp)
            
            summary_file = output_dir / "climate_correlation_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"Summary report saved to: {summary_file}")
            
            # Print summary findings
            print_summary_findings(summary)
            
            # Generate plots for high-priority rooms if requested
            if generate_plots:
                generate_priority_plots(analytics, summary, output_dir)
        
        logger.info("Climate correlation analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during climate analysis: {str(e)}")
        raise click.ClickException(f"Analysis failed: {str(e)}")


def print_key_findings(report: dict):
    """Print key findings from a single room report."""
    click.echo("\n" + "="*60)
    click.echo("KEY FINDINGS")
    click.echo("="*60)
    
    metadata = report.get('metadata', {})
    click.echo(f"Room: {metadata.get('school_name')} - {metadata.get('room_id')}")
    click.echo(f"Analysis Period: {metadata.get('analysis_period', {}).get('start', 'N/A')} to {metadata.get('analysis_period', {}).get('end', 'N/A')}")
    click.echo(f"Total Records: {metadata.get('total_records', 'N/A')}")
    
    # Solar analysis
    solar_analysis = report.get('solar_analysis', {})
    if solar_analysis:
        shading_rec = solar_analysis.get('shading_recommendation', {})
        click.echo(f"\n🌞 SOLAR SHADING ASSESSMENT:")
        click.echo(f"Priority: {shading_rec.get('priority', 'N/A')}")
        click.echo(f"Recommendation: {shading_rec.get('recommendation', 'N/A')}")
        
        rad_rel = solar_analysis.get('radiation_temperature_relationship', {})
        if rad_rel:
            click.echo(f"Radiation-Temperature Correlation: {rad_rel.get('correlation', 0):.3f} ({rad_rel.get('strength', 'N/A')})")
    
    # Overall correlations
    correlations = report.get('correlations', {}).get('overall', {})
    if correlations:
        click.echo(f"\n📊 OVERALL CORRELATIONS:")
        for param, stats in correlations.items():
            if abs(stats.get('pearson_r', 0)) > 0.3:  # Only show meaningful correlations
                click.echo(f"{param}: r={stats.get('pearson_r', 0):.3f} (p={stats.get('pearson_p', 1):.3f})")
    
    # Temperature statistics
    temp_stats = report.get('summary_statistics', {}).get('indoor_temperature', {})
    if temp_stats:
        click.echo(f"\n🌡️  TEMPERATURE STATISTICS:")
        click.echo(f"Mean: {temp_stats.get('mean', 0):.1f}°C")
        click.echo(f"Range: {temp_stats.get('min', 0):.1f}°C - {temp_stats.get('max', 0):.1f}°C")
        click.echo(f"75th Percentile: {temp_stats.get('q75', 0):.1f}°C")


def generate_summary_report(all_reports: dict, focus_high_temp: bool) -> dict:
    """Generate summary report across all rooms."""
    summary = {
        'total_rooms_analyzed': len(all_reports),
        'rooms_with_data': 0,
        'rooms_with_errors': 0,
        'solar_shading_priorities': {
            'High': [],
            'Medium': [],
            'Low': [],
            'None': []
        },
        'high_correlation_rooms': [],
        'temperature_sensitive_rooms': [],
        'analysis_timestamp': str(Path().cwd())
    }
    
    for room_key, report in all_reports.items():
        if 'error' in report:
            summary['rooms_with_errors'] += 1
            continue
        
        summary['rooms_with_data'] += 1
        
        # Solar shading priority
        solar_analysis = report.get('solar_analysis', {})
        if solar_analysis:
            priority = solar_analysis.get('shading_recommendation', {}).get('priority', 'None')
            summary['solar_shading_priorities'][priority].append(room_key)
        
        # High correlations with radiation
        correlations = report.get('correlations', {}).get('overall', {})
        radiation_corr = correlations.get('mean_radiation', {}).get('pearson_r', 0)
        
        if abs(radiation_corr) > 0.5:
            summary['high_correlation_rooms'].append({
                'room': room_key,
                'radiation_correlation': radiation_corr,
                'significance': correlations.get('mean_radiation', {}).get('pearson_p', 1)
            })
        
        # Temperature sensitivity (high temperature correlation)
        if focus_high_temp:
            high_temp_corr = report.get('correlations', {}).get('high_temperature_correlation', {})
            for param, stats in high_temp_corr.items():
                if abs(stats.get('pearson_r', 0)) > 0.4:
                    summary['temperature_sensitive_rooms'].append({
                        'room': room_key,
                        'parameter': param,
                        'correlation': stats.get('pearson_r', 0),
                        'threshold_temp': stats.get('temperature_threshold', 0)
                    })
    
    return summary


def print_summary_findings(summary: dict):
    """Print summary findings across all rooms."""
    click.echo("\n" + "="*80)
    click.echo("CLIMATE CORRELATION ANALYSIS SUMMARY")
    click.echo("="*80)
    
    click.echo(f"Total Rooms Analyzed: {summary['total_rooms_analyzed']}")
    click.echo(f"Rooms with Valid Data: {summary['rooms_with_data']}")
    click.echo(f"Rooms with Errors: {summary['rooms_with_errors']}")
    
    # Solar shading priorities
    click.echo(f"\n🌞 SOLAR SHADING PRIORITIES:")
    priorities = summary['solar_shading_priorities']
    click.echo(f"High Priority (Strong sensitivity): {len(priorities['High'])} rooms")
    click.echo(f"Medium Priority (Moderate sensitivity): {len(priorities['Medium'])} rooms")
    click.echo(f"Low Priority (Weak sensitivity): {len(priorities['Low'])} rooms")
    click.echo(f"No Action Needed: {len(priorities['None'])} rooms")
    
    if priorities['High']:
        click.echo(f"\n🚨 HIGH PRIORITY ROOMS (require solar shading):")
        for room in priorities['High'][:5]:  # Show first 5
            click.echo(f"  - {room}")
        if len(priorities['High']) > 5:
            click.echo(f"  ... and {len(priorities['High']) - 5} more")
    
    # High correlation rooms
    high_corr = summary['high_correlation_rooms']
    if high_corr:
        click.echo(f"\n📊 ROOMS WITH HIGH RADIATION CORRELATION:")
        for room_data in sorted(high_corr, key=lambda x: abs(x['radiation_correlation']), reverse=True)[:5]:
            click.echo(f"  - {room_data['room']}: r={room_data['radiation_correlation']:.3f}")
    
    # Temperature sensitive rooms
    temp_sensitive = summary['temperature_sensitive_rooms']
    if temp_sensitive:
        click.echo(f"\n🌡️  HIGH TEMPERATURE SENSITIVE ROOMS:")
        for room_data in sorted(temp_sensitive, key=lambda x: abs(x['correlation']), reverse=True)[:5]:
            click.echo(f"  - {room_data['room']}: {room_data['parameter']} r={room_data['correlation']:.3f}")


def generate_priority_plots(analytics: ClimateAnalytics, summary: dict, output_dir: Path):
    """Generate plots for high-priority rooms."""
    logger.info("Generating plots for high-priority rooms...")
    
    high_priority_rooms = summary['solar_shading_priorities']['High']
    
    for room_key in high_priority_rooms[:3]:  # Limit to first 3 for performance
        try:
            # Parse school and room from key
            parts = room_key.split('_')
            if len(parts) >= 3:
                school = '_'.join(parts[:2])
                room = '_'.join(parts[2:])
                
                merged_df = analytics.merge_climate_indoor_data(school, room)
                if not merged_df.empty:
                    merged_df = analytics.add_time_features(merged_df)
                    
                    plot_file = output_dir / f"{room_key}_high_priority_radiation_plot.png"
                    analytics.create_correlation_visualization(
                        merged_df,
                        climate_param='mean_radiation',
                        output_path=str(plot_file)
                    )
                    logger.info(f"High-priority plot saved: {plot_file}")
        
        except Exception as e:
            logger.warning(f"Could not generate plot for {room_key}: {str(e)}")
