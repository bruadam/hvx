"""
Analyze command module for IEQ Analytics CLI.

Handles comprehensive analysis of mapped IEQ data including:
- Rule-based analytics
- EN16798 standards compliance
- Performance metrics
- Visualization generation
"""

import click
from pathlib import Path
from typing import Optional, List
import json
import sys
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()


@click.command()
@click.option(
    '--data-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Directory containing mapped IEQ data files'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
    help='Output directory for analysis results'
)
@click.option(
    '--buildings-metadata',
    type=click.Path(path_type=Path),
    help='Path to buildings metadata JSON file'
)
@click.option(
    '--rules-config', 
    type=click.Path(path_type=Path),
    help='Analytics rules configuration'
)
@click.option(
    '--export-formats',
    multiple=True,
    type=click.Choice(['json', 'csv', 'excel', 'pdf']),
    default=['json', 'csv'],
    help='Export formats for analysis results'
)
@click.option(
    '--generate-plots/--no-plots',
    default=True,
    help='Generate visualization plots'
)
@click.option(
    '--parallel/--sequential', default=True,
    help='Parallel processing of rooms'
)
@click.option(
    '--ventilation-analysis/--no-ventilation',
    default=False,
    help='Include ventilation rate analysis'
)
@click.option(
    '--ai-insights/--no-ai',
    default=False,
    help='Generate AI-powered insights'
)
@click.option(
    '--cache-results/--no-cache',
    default=True,
    help='Cache analysis results for faster subsequent runs'
)
@click.pass_context
def analyze(
    ctx,
    data_dir: Optional[Path],
    output_dir: Optional[Path],
    buildings_metadata: Optional[Path],
    rules_config: Optional[Path],
    export_formats: List[str],
    generate_plots: bool,
    parallel: bool,
    ventilation_analysis: bool,
    ai_insights: bool,
    cache_results: bool
):
    """🔬 Analyze mapped IEQ data for comfort compliance and performance metrics.
    
    Performs comprehensive analysis including:
    - EN16798-1 standards compliance
    - Custom rule-based analytics  
    - Performance scoring
    - Data quality assessment
    - Visualization generation
    """
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    
    # Set defaults based on workspace structure
    data_dir = data_dir or workspace / "output" / "mapped" / "mapped_data"
    output_dir = output_dir or workspace / "output" / "analysis"
    buildings_metadata = buildings_metadata or workspace / "output" / "mapped" / "buildings_metadata.json"
    rules_config = rules_config or workspace / "config" / "tests.yaml"
    
    console.print("🔬 [bold blue]Starting IEQ Analysis...[/bold blue]")
    console.print(f"📂 Data directory: {data_dir}")
    console.print(f"📤 Output directory: {output_dir}")
    console.print(f"📋 Rules config: {rules_config}")
    
    # Validate inputs
    if not data_dir.exists():
        console.print(f"[red]❌ Data directory not found: {data_dir}[/red]")
        console.print("Run 'ieq-analytics map' first to process raw data.")
        sys.exit(1)
    
    if not rules_config.exists():
        console.print(f"[red]❌ Rules configuration not found: {rules_config}[/red]")
        console.print("Create analytics rules configuration file.")
        sys.exit(1)
    
    try:
        # Import analytics components
        from ieq_analytics.analytics import IEQAnalytics
        from ieq_analytics.unified_analytics import UnifiedAnalyticsEngine
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load buildings metadata if available
        buildings_data = {}
        if buildings_metadata.exists():
            with open(buildings_metadata, 'r') as f:
                buildings_data = json.load(f)
            console.print(f"✅ Loaded metadata for {len(buildings_data)} buildings")
        
        # Initialize analytics components
        console.print("🔧 Initializing unified analytics engine...")
        ieq_analytics = IEQAnalytics()
        unified_engine = UnifiedAnalyticsEngine(rules_config)
        
        # Find all mapped data files
        data_files = list(data_dir.glob("*_processed.csv"))
        if not data_files:
            console.print(f"[red]❌ No processed data files found in {data_dir}[/red]")
            sys.exit(1)
        
        console.print(f"📊 Found {len(data_files)} data files to analyze")
        
        # Initialize collections
        all_room_analyses = []
        building_summaries = {}
        processing_errors = []
        
        # Process files
        if parallel and len(data_files) > 1:
            console.print("⚡ Using parallel processing...")
            
            # Process files in parallel
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing rooms in parallel...", total=len(data_files))
                
                # Determine number of workers (use 75% of available cores, min 1, max 8)
                max_workers = min(8, max(1, int(mp.cpu_count() * 0.75)))
                
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    future_to_file = {}
                    for file_path in data_files:
                        room_id = file_path.stem.replace('_processed', '')
                        future = executor.submit(
                            _analyze_single_room_wrapper,
                            file_path, room_id, rules_config, generate_plots, output_dir, ventilation_analysis
                        )
                        future_to_file[future] = (file_path, room_id)
                    
                    # Process completed tasks
                    for future in as_completed(future_to_file):
                        file_path, room_id = future_to_file[future]
                        progress.update(task, description=f"Processing results for: [cyan]{room_id}[/cyan]")
                        
                        try:
                            room_analysis = future.result()
                            if room_analysis:
                                all_room_analyses.append(room_analysis)
                                
                                # Group by building for summaries
                                building_id = _extract_building_id(room_id, buildings_data)
                                if building_id not in building_summaries:
                                    building_summaries[building_id] = []
                                building_summaries[building_id].append(room_analysis)
                        
                        except Exception as e:
                            error_info = {
                                'room_id': room_id,
                                'file_path': str(file_path),
                                'error': str(e)
                            }
                            processing_errors.append(error_info)
                            console.print(f"[yellow]⚠️ Error analyzing {room_id}: {e}[/yellow]")
                        
                        progress.advance(task)
        else:
            # Sequential processing
            console.print("📈 Processing rooms sequentially...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing rooms...", total=len(data_files))
                
                for i, file_path in enumerate(data_files, 1):
                    room_id = file_path.stem.replace('_processed', '')
                    progress.update(task, description=f"Analyzing room: [cyan]{room_id}[/cyan]")
                    
                    try:
                        # Load and analyze room data
                        room_analysis = _analyze_single_room(
                            file_path, room_id, ieq_analytics, unified_engine,
                            generate_plots, output_dir, ventilation_analysis, rules_config
                        )
                        
                        if room_analysis:
                            all_room_analyses.append(room_analysis)
                            
                            # Group by building for summaries
                            building_id = _extract_building_id(room_id, buildings_data)
                            if building_id not in building_summaries:
                                building_summaries[building_id] = []
                            building_summaries[building_id].append(room_analysis)
                    
                    except Exception as e:
                        error_info = {
                            'room_id': room_id,
                            'file_path': str(file_path),
                            'error': str(e)
                        }
                        processing_errors.append(error_info)
                        console.print(f"[yellow]⚠️ Error analyzing {room_id}: {e}[/yellow]")
                    
                    progress.advance(task)
        
        # Generate building-level analysis
        console.print("🏢 Generating building-level analysis...")
        building_analysis = _analyze_buildings(building_summaries, buildings_data)
        
        # Save results in multiple formats
        console.print("💾 Saving analysis results...")
        _save_analysis_results(
            output_dir, all_room_analyses, building_analysis, 
            export_formats, processing_errors
        )
        
        # Generate AI insights if requested
        if ai_insights:
            console.print("🤖 Generating AI insights...")
            _generate_ai_insights(output_dir, all_room_analyses, building_analysis)
        
        # Display summary
        total_rooms = len(all_room_analyses)
        total_buildings = len(building_analysis)
        errors_count = len(processing_errors)
        
        success_panel = Panel.fit(
            f"[bold green]✅ Analysis Complete![/bold green]\n\n"
            f"📊 Rooms analyzed: {total_rooms}\n"
            f"🏢 Buildings: {total_buildings}\n"
            f"❌ Errors: {errors_count}\n"
            f"📁 Results saved to: {output_dir}\n"
            f"📈 Formats: {', '.join(export_formats)}",
            title="🎉 Analysis Summary",
            border_style="green"
        )
        console.print(success_panel)
        
        # Update pipeline state
        pipeline_state = ctx.obj.get('pipeline_state')
        if pipeline_state:
            pipeline_state.update_analysis_state()
        
        if processing_errors:
            console.print(f"\n[yellow]⚠️ {errors_count} rooms had processing errors. Check the error log for details.[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Analysis failed: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


def _analyze_single_room_wrapper(file_path: Path, room_id: str, rules_config: Path, 
                                generate_plots: bool, output_dir: Path, ventilation_analysis: bool):
    """Wrapper function for parallel processing that initializes analytics engines."""
    try:
        # Import analytics components inside the worker process
        from ieq_analytics.analytics import IEQAnalytics
        from ieq_analytics.unified_analytics import UnifiedAnalyticsEngine
        
        # Initialize analytics components in worker process
        ieq_analytics = IEQAnalytics()
        unified_engine = UnifiedAnalyticsEngine(rules_config)
        
        # Call the main analysis function
        return _analyze_single_room(
            file_path, room_id, ieq_analytics, unified_engine,
            generate_plots, output_dir, ventilation_analysis, rules_config
        )
    except Exception as e:
        # Return error information instead of raising
        return {
            'room_id': room_id,
            'error': str(e),
            'analysis': {},
            'data_summary': {}
        }


def _analyze_single_room(file_path: Path, room_id: str, ieq_analytics, unified_engine, 
                        generate_plots: bool, output_dir: Path, ventilation_analysis: bool, rules_config: Path):
    """Analyze a single room's data."""
    import pandas as pd
    
    # Load room data
    df = pd.read_csv(file_path)
    if df.empty:
        return None
    
    # Convert to IEQData format
    from ieq_analytics.models import IEQData
    
    # Convert timestamp column to DatetimeIndex
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
    
    # Create IEQData object (data_period_start/end will be set by model_validator)
    ieq_data = IEQData(
        room_id=room_id,
        building_id=_extract_building_id(room_id, {}),
        data=df,
        quality_score=0.8,  # Default quality score
        data_period_start=None,  # Will be auto-set by model_validator
        data_period_end=None    # Will be auto-set by model_validator
    )
    
    # Run standard IEQ analysis
    analysis_results = ieq_analytics.analyze_room_data(ieq_data)
    
    # Run rule-based analysis
    try:
        from ieq_analytics.unified_analytics import AnalysisType
        rule_results = unified_engine.analyze_room_data(
            df, room_id, 
            analysis_types=[
                AnalysisType.BASIC_STATISTICS,
                AnalysisType.DATA_QUALITY,
                AnalysisType.USER_RULES
            ]
        )
        analysis_results['rule_based_analysis'] = rule_results
        
        # Export detailed compliance data for each rule in multiple formats
        # Check both user_rules and analytics sections for rule results
        rules_data = rule_results.get('user_rules', {})
        if not rules_data:
            rules_data = rule_results.get('analytics', {})
        
        if rules_data:
            # Use the new comprehensive export functionality
            try:
                compliance_exports = unified_engine.export_compliance_details(
                    df, room_id, rules_data, output_dir
                )
                analysis_results['compliance_exports'] = compliance_exports
            except Exception as e:
                console.print(f"[yellow]⚠️ Detailed compliance export failed for {room_id}: {e}[/yellow]")
                # Fallback to original export method
                _export_boolean_compliance_data(df, rules_data, room_id, output_dir, unified_engine)
        
    except Exception as e:
        console.print(f"[yellow]⚠️ Rule analysis failed for {room_id}: {e}[/yellow]")
    
    # Generate plots if requested
    if generate_plots:
        plots_dir = output_dir / "plots" / room_id
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            _generate_room_plots(ieq_data, analysis_results, plots_dir, rules_config)
        except Exception as e:
            console.print(f"[yellow]⚠️ Plot generation failed for {room_id}: {e}[/yellow]")
    
    # Add ventilation analysis if requested
    if ventilation_analysis:
        try:
            from ieq_analytics.ventilation_rate_predictor import VentilationRatePredictor
            predictor = VentilationRatePredictor()
            
            # Find decay periods and predict ventilation rates
            decay_periods = predictor.find_decay_periods(df)
            ventilation_rates = []
            
            for period in decay_periods:
                rate = predictor.predict_ventilation_rate(period)
                if rate is not None:
                    ventilation_rates.append({
                        'period_start': str(period['start']),
                        'period_end': str(period['end']),
                        'ventilation_rate': rate
                    })
            
            analysis_results['ventilation_analysis'] = {
                'decay_periods_found': len(decay_periods),
                'ventilation_rates': ventilation_rates,
                'average_rate': sum(r['ventilation_rate'] for r in ventilation_rates) / len(ventilation_rates) if ventilation_rates else None
            }
        except Exception as e:
            console.print(f"[yellow]⚠️ Ventilation analysis failed for {room_id}: {e}[/yellow]")
    
    return {
        'room_id': room_id,
        'analysis': analysis_results,
        'data_summary': {
            'total_records': len(df),
            'start_date': str(df.index.min()) if isinstance(df.index, pd.DatetimeIndex) else None,
            'end_date': str(df.index.max()) if isinstance(df.index, pd.DatetimeIndex) else None,
            'parameters': list(df.columns)
        }
    }


def _generate_room_plots(ieq_data, analysis_results: dict, plots_dir: Path, rules_config: Path):
    """Generate visualization plots for a room with non-compliance highlighting and holiday masking."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    from ieq_analytics.unified_analytics import UnifiedFilterProcessor
    import yaml
    
    # Load rules configuration to get holiday settings
    config = {}
    try:
        with open(rules_config, 'r') as f:
            config = yaml.safe_load(f)
        holiday_config = config.get('holidays', {})
    except Exception:
        holiday_config = {}
    
    # Use the original DataFrame from ieq_data.data instead of to_dataframe()
    df = ieq_data.data.copy() if hasattr(ieq_data, 'data') else ieq_data
    
    # Initialize filter processor for holiday detection
    filter_processor = UnifiedFilterProcessor(config)
    
    # Get holiday dates for the data period and filter out holiday data
    holiday_mask = None
    if isinstance(df.index, pd.DatetimeIndex) and holiday_config:
        try:
            holiday_mask = filter_processor._get_holiday_mask(df)
            # Filter out holidays from the data
            if holiday_mask is not None and holiday_mask.any():
                df = df[~holiday_mask]
        except Exception as e:
            print(f"Warning: Could not get holiday mask: {e}")
    
    # Get rule-based analysis results
    rule_based_data = analysis_results.get('rule_based_analysis', {})
    rule_results = rule_based_data.get('user_rules', {})
    if not rule_results:
        rule_results = rule_based_data.get('analytics', {})
    
    # Time series plot with compliance highlighting
    if isinstance(df.index, pd.DatetimeIndex):
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        colors = ['red', 'orange', 'yellow', 'purple', 'brown']  # Define colors for violations
        
        # Temperature plot with compliance zones
        if 'temperature' in df.columns:
            axes[0].plot(df.index, df['temperature'], 'b-', alpha=0.7, linewidth=1, label='Temperature')
            
            # Highlight non-compliance periods for temperature rules
            temp_rules = [name for name in rule_results.keys() if 'temp' in name.lower()]
            
            for i, rule_name in enumerate(temp_rules[:3]):  # Limit to 3 rules for clarity
                rule_result = rule_results.get(rule_name, {})
                violations = rule_result.get('violations', [])
                
                if violations:
                    color = colors[i % len(colors)]
                    for violation in violations:
                        try:
                            start_time = pd.to_datetime(violation['timestamp'])
                            # Only plot violation if it's not filtered out (not a holiday)
                            if start_time in df.index:
                                axes[0].scatter(start_time, violation['value'], 
                                              color=color, s=30, alpha=0.7, 
                                              label=f'{rule_name} violation' if i == 0 else "")
                        except:
                            continue
            
            axes[0].set_ylabel('Temperature (°C)')
            axes[0].set_title(f'Room {ieq_data.room_id} - Environmental Conditions (Holidays Excluded)')
            axes[0].grid(True, alpha=0.3)
            axes[0].legend()
        
        # Humidity plot with compliance zones
        if 'humidity' in df.columns:
            axes[1].plot(df.index, df['humidity'], 'g-', alpha=0.7, linewidth=1, label='Humidity')
            
            # Highlight non-compliance periods for humidity rules
            humidity_rules = [name for name in rule_results.keys() if 'humidity' in name.lower()]
            
            for i, rule_name in enumerate(humidity_rules[:3]):
                rule_result = rule_results.get(rule_name, {})
                violations = rule_result.get('violations', [])
                
                if violations:
                    color = colors[i % len(colors)]
                    for violation in violations:
                        try:
                            start_time = pd.to_datetime(violation['timestamp'])
                            # Only plot violation if it's not filtered out (not a holiday)
                            if start_time in df.index:
                                axes[1].scatter(start_time, violation['value'], 
                                              color=color, s=30, alpha=0.7,
                                              label=f'{rule_name} violation' if i == 0 else "")
                        except:
                            continue
            
            axes[1].set_ylabel('Humidity (%)')
            axes[1].grid(True, alpha=0.3)
            axes[1].legend()
        
        # CO2 plot with compliance zones
        if 'co2' in df.columns:
            axes[2].plot(df.index, df['co2'], 'r-', alpha=0.7, linewidth=1, label='CO2')
            
            # Highlight non-compliance periods for CO2 rules
            co2_rules = [name for name in rule_results.keys() if 'co2' in name.lower()]
            
            for i, rule_name in enumerate(co2_rules[:3]):
                rule_result = rule_results.get(rule_name, {})
                violations = rule_result.get('violations', [])
                
                if violations:
                    color = colors[i % len(colors)]
                    for violation in violations:
                        try:
                            start_time = pd.to_datetime(violation['timestamp'])
                            # Only plot violation if it's not filtered out (not a holiday)
                            if start_time in df.index:
                                axes[2].scatter(start_time, violation['value'], 
                                              color=color, s=30, alpha=0.7,
                                              label=f'{rule_name} violation' if i == 0 else "")
                        except:
                            continue
            
            axes[2].set_ylabel('CO2 (ppm)')
            axes[2].set_xlabel('Time')
            axes[2].grid(True, alpha=0.3)
            axes[2].legend()
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'timeseries_with_compliance.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    # Compliance summary plot
    if rule_results:
        _generate_compliance_summary_plot(rule_results, plots_dir, ieq_data.room_id)
    
    # Original comfort zone plot (enhanced)
    if 'temperature' in df.columns and 'humidity' in df.columns:
        plt.figure(figsize=(12, 10))
        
        # Create scatter plot colored by compliance
        temp_rule = next((name for name in rule_results.keys() if 'temp' in name.lower()), None)
        humidity_rule = next((name for name in rule_results.keys() if 'humidity' in name.lower()), None)
        
        if temp_rule and humidity_rule:
            # Color points based on compliance
            temp_violations = set()
            humidity_violations = set()
            
            for violation in rule_results.get(temp_rule, {}).get('violations', []):
                try:
                    temp_violations.add(pd.to_datetime(violation['timestamp']))
                except:
                    continue
            
            for violation in rule_results.get(humidity_rule, {}).get('violations', []):
                try:
                    humidity_violations.add(pd.to_datetime(violation['timestamp']))
                except:
                    continue
            
            # Create color array (no need for holiday checking since data is already filtered)
            colors = []
            for timestamp in df.index:
                if timestamp in temp_violations and timestamp in humidity_violations:
                    colors.append('red')  # Both parameters violated
                elif timestamp in temp_violations:
                    colors.append('orange')  # Temperature violated
                elif timestamp in humidity_violations:
                    colors.append('yellow')  # Humidity violated
                else:
                    colors.append('green')  # Compliant
            
            # Plot all points with their respective colors
            for color in set(colors):
                mask = [c == color for c in colors]
                temp_data = df['temperature'][mask]
                humidity_data = df['humidity'][mask]
                
                if color == 'green':
                    label = 'Compliant'
                elif color == 'yellow':
                    label = 'Humidity violation'
                elif color == 'orange':
                    label = 'Temperature violation'
                elif color == 'red':
                    label = 'Both violated'
                else:
                    label = 'Unknown'
                
                if len(temp_data) > 0:
                    plt.scatter(temp_data, humidity_data, c=color, alpha=0.6, s=20, label=label)
        else:
            scatter = plt.scatter(df['temperature'], df['humidity'], alpha=0.6, c=range(len(df)), cmap='viridis')
            plt.colorbar(scatter, label='Time Index')
        
        plt.xlabel('Temperature (°C)')
        plt.ylabel('Humidity (%)')
        plt.title(f'Room {ieq_data.room_id} - Comfort Zone Analysis (Holidays Excluded)')
        
        # Add comfort zone boundaries (example values)
        plt.axvline(x=20, color='blue', linestyle='--', alpha=0.7, label='Comfort Min Temp')
        plt.axvline(x=26, color='blue', linestyle='--', alpha=0.7, label='Comfort Max Temp')
        plt.axhline(y=30, color='blue', linestyle='--', alpha=0.7, label='Comfort Min Humidity')
        plt.axhline(y=60, color='blue', linestyle='--', alpha=0.7, label='Comfort Max Humidity')
        
        # Create legend
        plt.legend(loc='upper right')
        
        plt.grid(True, alpha=0.3)
        plt.savefig(plots_dir / 'comfort_zone_with_compliance.png', dpi=300, bbox_inches='tight')
        plt.close()


def _generate_compliance_summary_plot(rule_results: dict, plots_dir: Path, room_id: str):
    """Generate a summary plot of compliance rates for all rules."""
    import matplotlib.pyplot as plt
    import numpy as np
    
    rule_names = []
    compliance_rates = []
    
    for rule_name, rule_result in rule_results.items():
        if isinstance(rule_result, dict) and 'compliance_rate' in rule_result:
            rule_names.append(rule_name.replace('en16798_', '').replace('_', ' ').title())
            compliance_rates.append(rule_result['compliance_rate'])
    
    if not rule_names:
        return
    
    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, max(6, len(rule_names) * 0.5)))
    
    # Color bars based on compliance rate
    colors = ['red' if rate < 70 else 'orange' if rate < 85 else 'green' for rate in compliance_rates]
    
    bars = ax.barh(rule_names, compliance_rates, color=colors, alpha=0.7)
    
    # Add compliance rate labels on bars
    for i, (bar, rate) in enumerate(zip(bars, compliance_rates)):
        ax.text(rate + 1, i, f'{rate:.1f}%', va='center', fontweight='bold')
    
    ax.set_xlabel('Compliance Rate (%)')
    ax.set_title(f'Room {room_id} - Rule Compliance Summary')
    ax.set_xlim(0, 105)
    
    # Add vertical lines for thresholds
    ax.axvline(x=70, color='red', linestyle='--', alpha=0.5, label='Poor (<70%)')
    ax.axvline(x=85, color='orange', linestyle='--', alpha=0.5, label='Fair (<85%)')
    ax.axvline(x=95, color='green', linestyle='--', alpha=0.5, label='Good (>95%)')
    
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(plots_dir / 'compliance_summary.png', dpi=300, bbox_inches='tight')
    plt.close()


def _extract_building_id(room_id: str, buildings_data: dict) -> str:
    """Extract building ID from room ID using metadata."""
    # Simple extraction based on common naming patterns
    if '_' in room_id:
        building_part = room_id.split('_')[0]
        return building_part.replace('_', '-')
    return room_id


def _export_boolean_compliance_data(df, rule_results, room_id: str, output_dir: Path, unified_engine):
    """Export boolean compliance data with timestamps for each rule."""
    import pandas as pd
    
    compliance_dir = output_dir / "compliance_data" / room_id
    compliance_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each rule that has detailed analysis results
    for rule_name, rule_result in rule_results.items():
        if not isinstance(rule_result, dict) or 'metadata' not in rule_result:
            continue
        
        try:
            # Re-evaluate the rule to get the detailed boolean series
            rule_compliance = unified_engine.rule_engine.evaluate_rule(df, rule_name)
            
            # Create compliance DataFrame with timestamp and boolean compliance
            compliance_df = pd.DataFrame({
                'timestamp': df.index,
                'compliant': rule_compliance.compliance_series if hasattr(rule_compliance, 'compliance_series') else [],
                'parameter_value': df[rule_compliance.metadata.get('data_column', 'temperature')] if rule_compliance.metadata.get('data_column') in df.columns else None
            })
            
            # Add violation periods
            compliance_df['violation'] = ~compliance_df['compliant']
            
            # Export as CSV
            compliance_file = compliance_dir / f"{rule_name}_compliance.csv"
            compliance_df.to_csv(compliance_file, index=False)
            
            # Export violation periods summary
            violation_periods = _identify_violation_periods(compliance_df)
            if violation_periods:
                violations_file = compliance_dir / f"{rule_name}_violations.csv"
                pd.DataFrame(violation_periods).to_csv(violations_file, index=False)
        
        except Exception as e:
            console.print(f"[yellow]⚠️ Error exporting compliance data for {rule_name}: {e}[/yellow]")


def _identify_violation_periods(compliance_df):
    """Identify continuous violation periods from compliance data."""
    import pandas as pd
    
    violation_periods = []
    in_violation = False
    start_time = None
    
    for idx, row in compliance_df.iterrows():
        if row['violation'] and not in_violation:
            # Start of violation period
            in_violation = True
            start_time = row['timestamp']
        elif not row['violation'] and in_violation:
            # End of violation period
            in_violation = False
            violation_periods.append({
                'start_time': start_time,
                'end_time': row['timestamp'],
                'duration_hours': (row['timestamp'] - start_time).total_seconds() / 3600,
                'parameter_value_start': compliance_df.loc[compliance_df['timestamp'] == start_time, 'parameter_value'].iloc[0] if 'parameter_value' in compliance_df.columns else None,
                'parameter_value_end': row['parameter_value']
            })
    
    # Handle case where violation period extends to end of data
    if in_violation and start_time is not None:
        last_row = compliance_df.iloc[-1]
        violation_periods.append({
            'start_time': start_time,
            'end_time': last_row['timestamp'],
            'duration_hours': (last_row['timestamp'] - start_time).total_seconds() / 3600,
            'parameter_value_start': compliance_df.loc[compliance_df['timestamp'] == start_time, 'parameter_value'].iloc[0] if 'parameter_value' in compliance_df.columns else None,
            'parameter_value_end': last_row['parameter_value']
        })
    
    return violation_periods


def _analyze_buildings(building_summaries: dict, buildings_data: dict) -> dict:
    """Generate building-level analysis from room data."""
    building_analysis = {}
    
    for building_id, room_analyses in building_summaries.items():
        if not room_analyses:
            continue
        
        # Calculate building-level metrics
        total_rooms = len(room_analyses)
        
        # Aggregate performance scores
        performance_scores = []
        comfort_compliance_rates = []
        data_quality_scores = []
        
        for room_analysis in room_analyses:
            analysis = room_analysis.get('analysis', {})
            
            # Extract performance metrics - handle both numeric and dict types
            # For data quality
            data_quality = analysis.get('data_quality', {})
            if isinstance(data_quality, dict):
                quality_score = data_quality.get('overall_score', 0)
                if isinstance(quality_score, (int, float)):
                    data_quality_scores.append(quality_score)
            elif isinstance(data_quality, (int, float)):
                data_quality_scores.append(data_quality)
            
            # For user rules - calculate average compliance rate
            user_rules = analysis.get('user_rules', {})
            if isinstance(user_rules, dict):
                rule_compliance_rates = []
                for rule_name, rule_result in user_rules.items():
                    if isinstance(rule_result, dict) and 'compliance_rate' in rule_result:
                        compliance_rate = rule_result['compliance_rate']
                        if isinstance(compliance_rate, (int, float)):
                            rule_compliance_rates.append(compliance_rate)
                
                if rule_compliance_rates:
                    avg_compliance = sum(rule_compliance_rates) / len(rule_compliance_rates)
                    comfort_compliance_rates.append(avg_compliance / 100)  # Convert to 0-1 scale
            
            # For EN16798 compliance
            en16798 = analysis.get('en16798_compliance', {})
            if isinstance(en16798, dict):
                en16798_compliance_rates = []
                for rule_name, rule_result in en16798.items():
                    if isinstance(rule_result, dict) and 'compliance_rate' in rule_result:
                        compliance_rate = rule_result['compliance_rate']
                        if isinstance(compliance_rate, (int, float)):
                            en16798_compliance_rates.append(compliance_rate)
                
                if en16798_compliance_rates:
                    avg_en16798 = sum(en16798_compliance_rates) / len(en16798_compliance_rates)
                    performance_scores.append(avg_en16798 / 100)  # Convert to 0-1 scale
        
        # Calculate building averages
        building_analysis[building_id] = {
            'building_id': building_id,
            'room_count': total_rooms,
            'average_performance_score': sum(performance_scores) / len(performance_scores) if performance_scores else 0,
            'average_comfort_compliance': sum(comfort_compliance_rates) / len(comfort_compliance_rates) if comfort_compliance_rates else 0,
            'average_data_quality': sum(data_quality_scores) / len(data_quality_scores) if data_quality_scores else 0,
            'rooms': [r['room_id'] for r in room_analyses],
            'metadata': buildings_data.get(building_id, {})
        }
    
    return building_analysis


def _save_analysis_results(output_dir: Path, room_analyses: list, building_analysis: dict, 
                          export_formats: List[str], processing_errors: list):
    """Save analysis results in multiple formats."""
    import pandas as pd
    
    # Save room analyses
    if 'json' in export_formats:
        with open(output_dir / 'room_analyses.json', 'w') as f:
            json.dump(room_analyses, f, indent=2, default=str)
    
    # Save building analysis
    if 'json' in export_formats:
        with open(output_dir / 'building_analysis.json', 'w') as f:
            json.dump(building_analysis, f, indent=2, default=str)
    
    # Save comprehensive summary
    if 'json' in export_formats:
        summary = {
            'analysis_timestamp': str(pd.Timestamp.now()),
            'total_rooms': len(room_analyses),
            'total_buildings': len(building_analysis),
            'processing_errors': processing_errors,
            'room_analyses': room_analyses,
            'building_analysis': building_analysis
        }
        with open(output_dir / 'comprehensive_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
    
    # Save Excel summary with detailed sheets
    if 'excel' in export_formats and room_analyses:
        try:
            excel_path = output_dir / 'ieq_analysis_comprehensive.xlsx'
            _save_excel_analysis(room_analyses, building_analysis, excel_path)
        except ImportError:
            console.print("[yellow]⚠️ Excel export requires openpyxl package[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Excel export failed: {e}[/yellow]")
    
    # Save CSV summaries
    if 'csv' in export_formats and room_analyses:
        # Create room summary CSV
        room_rows = []
        
        # First, collect all rule names to create columns
        all_user_rules = set()
        all_en16798_rules = set()
        
        for room_analysis in room_analyses:
            analysis = room_analysis.get('analysis', {})
            rule_based_data = analysis.get('rule_based_analysis', {})
            
            # Check both user_rules and analytics sections
            user_rules = rule_based_data.get('user_rules', {})
            analytics_rules = rule_based_data.get('analytics', {})
            
            all_user_rules.update(user_rules.keys())
            
            # Separate EN16798 rules from other analytics rules
            for rule_name in analytics_rules.keys():
                if rule_name.startswith('en16798_'):
                    all_en16798_rules.add(rule_name)
                else:
                    all_user_rules.add(rule_name)
        
        for room_analysis in room_analyses:
            room_id = room_analysis['room_id']
            analysis = room_analysis.get('analysis', {})
            data_summary = room_analysis.get('data_summary', {})
            
            # Extract basic metrics
            row = {
                'room_id': room_id,
                'total_records': data_summary.get('total_records', 0),
                'start_date': data_summary.get('start_date', ''),
                'end_date': data_summary.get('end_date', ''),
            }
            
            # Extract data quality score
            data_quality = analysis.get('data_quality', {})
            if isinstance(data_quality, dict):
                row['data_quality_score'] = round(data_quality.get('overall_score', 0), 3)
            else:
                row['data_quality_score'] = 0
            
            # Extract user rules compliance rates from rule_based_analysis
            rule_based_data = analysis.get('rule_based_analysis', {})
            user_rules = rule_based_data.get('user_rules', {})
            analytics_rules = rule_based_data.get('analytics', {})
            
            # Combine user_rules and non-EN16798 analytics rules
            all_user_rule_results = {}
            all_user_rule_results.update(user_rules)
            
            # Add non-EN16798 analytics rules to user rules
            for rule_name, rule_result in analytics_rules.items():
                if not rule_name.startswith('en16798_'):
                    all_user_rule_results[rule_name] = rule_result
            
            user_compliance_rates = []
            
            for rule_name in sorted(all_user_rules):
                if rule_name in all_user_rule_results and isinstance(all_user_rule_results[rule_name], dict):
                    rule_result = all_user_rule_results[rule_name]
                    compliance_rate = rule_result.get('compliance_rate', 0)
                    total_points = rule_result.get('total_points', 0)
                    compliant_points = rule_result.get('compliant_points', 0)
                    non_compliant_points = total_points - compliant_points
                    
                    row[f'rule_{rule_name}_compliance_rate'] = round(compliance_rate, 1)
                    row[f'rule_{rule_name}_total_hours'] = total_points
                    row[f'rule_{rule_name}_compliant_hours'] = compliant_points
                    row[f'rule_{rule_name}_non_compliant_hours'] = non_compliant_points
                    row[f'rule_{rule_name}_non_compliant_percentage'] = round(100 - compliance_rate, 1)
                    user_compliance_rates.append(compliance_rate)
                else:
                    row[f'rule_{rule_name}_compliance_rate'] = 0
                    row[f'rule_{rule_name}_total_hours'] = 0
                    row[f'rule_{rule_name}_compliant_hours'] = 0
                    row[f'rule_{rule_name}_non_compliant_hours'] = 0
                    row[f'rule_{rule_name}_non_compliant_percentage'] = 0
            
            # Calculate average user rules compliance and totals
            if user_compliance_rates:
                row['avg_user_rules_compliance'] = round(sum(user_compliance_rates) / len(user_compliance_rates), 1)
                # Calculate total hours across all user rules
                total_user_rule_hours = sum(all_user_rule_results[rule_name].get('total_points', 0) 
                                          for rule_name in sorted(all_user_rules) 
                                          if rule_name in all_user_rule_results and isinstance(all_user_rule_results[rule_name], dict))
                total_user_compliant_hours = sum(all_user_rule_results[rule_name].get('compliant_points', 0) 
                                                for rule_name in sorted(all_user_rules) 
                                                if rule_name in all_user_rule_results and isinstance(all_user_rule_results[rule_name], dict))
                total_user_non_compliant_hours = total_user_rule_hours - total_user_compliant_hours
                
                row['total_user_rules_hours'] = total_user_rule_hours
                row['total_user_rules_compliant_hours'] = total_user_compliant_hours
                row['total_user_rules_non_compliant_hours'] = total_user_non_compliant_hours
                row['total_user_rules_non_compliant_percentage'] = round((total_user_non_compliant_hours / total_user_rule_hours * 100) if total_user_rule_hours > 0 else 0, 1)
            else:
                row['avg_user_rules_compliance'] = 0
                row['total_user_rules_hours'] = 0
                row['total_user_rules_compliant_hours'] = 0
                row['total_user_rules_non_compliant_hours'] = 0
                row['total_user_rules_non_compliant_percentage'] = 0
            
            # Extract EN16798 compliance from rule_based_analysis.analytics
            rule_based_data = analysis.get('rule_based_analysis', {})
            analytics_results = rule_based_data.get('analytics', {})
            en16798_compliance_rates = []
            
            # Filter EN16798 rules (those starting with 'en16798_')
            for rule_name, rule_result in analytics_results.items():
                if rule_name.startswith('en16798_') and isinstance(rule_result, dict):
                    compliance_rate = rule_result.get('compliance_rate', 0)
                    total_points = rule_result.get('total_points', 0)
                    compliant_points = rule_result.get('compliant_points', 0)
                    non_compliant_points = total_points - compliant_points
                    
                    row[f'{rule_name}_compliance_rate'] = round(compliance_rate, 1)
                    row[f'{rule_name}_total_hours'] = total_points
                    row[f'{rule_name}_compliant_hours'] = compliant_points
                    row[f'{rule_name}_non_compliant_hours'] = non_compliant_points
                    row[f'{rule_name}_non_compliant_percentage'] = round(100 - compliance_rate, 1)
                    en16798_compliance_rates.append(compliance_rate)
            
            # Calculate average EN16798 compliance and totals
            if en16798_compliance_rates:
                row['avg_en16798_compliance'] = round(sum(en16798_compliance_rates) / len(en16798_compliance_rates), 1)
                # Calculate total hours across all EN16798 rules
                en16798_rule_names = [rule_name for rule_name in analytics_results.keys() if rule_name.startswith('en16798_')]
                total_en16798_hours = sum(analytics_results[rule_name].get('total_points', 0) 
                                        for rule_name in en16798_rule_names 
                                        if isinstance(analytics_results.get(rule_name, {}), dict))
                total_en16798_compliant_hours = sum(analytics_results[rule_name].get('compliant_points', 0) 
                                                  for rule_name in en16798_rule_names 
                                                  if isinstance(analytics_results.get(rule_name, {}), dict))
                total_en16798_non_compliant_hours = total_en16798_hours - total_en16798_compliant_hours
                
                row['total_en16798_hours'] = total_en16798_hours
                row['total_en16798_compliant_hours'] = total_en16798_compliant_hours
                row['total_en16798_non_compliant_hours'] = total_en16798_non_compliant_hours
                row['total_en16798_non_compliant_percentage'] = round((total_en16798_non_compliant_hours / total_en16798_hours * 100) if total_en16798_hours > 0 else 0, 1)
            else:
                row['avg_en16798_compliance'] = 0
                row['total_en16798_hours'] = 0
                row['total_en16798_compliant_hours'] = 0
                row['total_en16798_non_compliant_hours'] = 0
                row['total_en16798_non_compliant_percentage'] = 0
            
            # Overall performance score (average of user rules and EN16798)
            overall_scores = []
            if row['avg_user_rules_compliance'] > 0:
                overall_scores.append(row['avg_user_rules_compliance'])
            if row['avg_en16798_compliance'] > 0:
                overall_scores.append(row['avg_en16798_compliance'])
            
            if overall_scores:
                row['overall_performance_score'] = round(sum(overall_scores) / len(overall_scores), 1)
            else:
                row['overall_performance_score'] = 0
            
            room_rows.append(row)
        
        room_df = pd.DataFrame(room_rows)
        room_df.to_csv(output_dir / 'ieq_analysis_summary.csv', index=False)
    
    # Save error log if there were errors
    if processing_errors:
        with open(output_dir / 'processing_errors.json', 'w') as f:
            json.dump(processing_errors, f, indent=2)


def _generate_ai_insights(output_dir: Path, room_analyses: list, building_analysis: dict):
    """Generate AI-powered insights from analysis results."""
    try:
        from ieq_analytics.reporting.ai_graph_analyzer import AIGraphAnalyzer
        
        ai_analyzer = AIGraphAnalyzer()
        insights = []
        
        # Generate insights for each building
        for building_id, building_data in building_analysis.items():
            # Create a simple text summary for AI analysis
            building_summary = f"""
            Building Analysis Summary for {building_id}:
            - Total rooms analyzed: {building_data['room_count']}
            - Average performance score: {building_data['average_performance_score']:.2f}
            - Average comfort compliance: {building_data['average_comfort_compliance']:.2f}
            - Average data quality: {building_data['average_data_quality']:.2f}
            """
            
            # Simple insight generation (since we don't have access to the full API)
            insight = {
                'building_id': building_id,
                'timestamp': str(datetime.now()),
                'summary': building_summary,
                'recommendations': _generate_simple_recommendations(building_data)
            }
            insights.append(insight)
        
        # Save AI insights
        if insights:
            with open(output_dir / 'ai_insights.json', 'w') as f:
                json.dump(insights, f, indent=2, default=str)
        
    except ImportError:
        console.print("[yellow]⚠️ AI analysis not available (missing dependencies)[/yellow]")
    except Exception as e:
        console.print(f"[yellow]⚠️ AI insights generation failed: {e}[/yellow]")


def _save_excel_analysis(room_analyses: list, building_analysis: dict, output_path: Path):
    """Save comprehensive analysis results to Excel with multiple sheets."""
    import pandas as pd
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Room summary sheet
        room_rows = []
        for room_analysis in room_analyses:
            room_id = room_analysis['room_id']
            analysis = room_analysis.get('analysis', {})
            data_summary = room_analysis.get('data_summary', {})
            
            row = {
                'room_id': room_id,
                'total_records': data_summary.get('total_records', 0),
                'start_date': data_summary.get('start_date', ''),
                'end_date': data_summary.get('end_date', ''),
                'data_quality_score': analysis.get('data_quality', {}).get('overall_score', 0)
            }
            
            # Add rule compliance rates
            rule_based_data = analysis.get('rule_based_analysis', {})
            user_rules = rule_based_data.get('user_rules', {})
            analytics_rules = rule_based_data.get('analytics', {})
            
            all_rules = {}
            all_rules.update(user_rules)
            all_rules.update(analytics_rules)
            
            compliance_rates = []
            for rule_name, rule_result in all_rules.items():
                if isinstance(rule_result, dict) and 'compliance_rate' in rule_result:
                    compliance_rate = rule_result['compliance_rate']
                    total_points = rule_result.get('total_points', 0)
                    compliant_points = rule_result.get('compliant_points', 0)
                    non_compliant_points = total_points - compliant_points
                    
                    row[f'{rule_name}_compliance_rate'] = compliance_rate
                    row[f'{rule_name}_total_hours'] = total_points
                    row[f'{rule_name}_compliant_hours'] = compliant_points
                    row[f'{rule_name}_non_compliant_hours'] = non_compliant_points
                    row[f'{rule_name}_non_compliant_percentage'] = round(100 - compliance_rate, 1)
                    row[f'{rule_name}_violations_count'] = rule_result.get('violations_count', 0)
                    compliance_rates.append(compliance_rate)
            
            row['average_compliance'] = sum(compliance_rates) / len(compliance_rates) if compliance_rates else 0
            room_rows.append(row)
        
        room_df = pd.DataFrame(room_rows)
        room_df.to_excel(writer, sheet_name='Room_Summary', index=False)
        
        # Detailed violations sheet
        violation_rows = []
        for room_analysis in room_analyses:
            room_id = room_analysis['room_id']
            analysis = room_analysis.get('analysis', {})
            rule_based_data = analysis.get('rule_based_analysis', {})
            
            user_rules = rule_based_data.get('user_rules', {})
            analytics_rules = rule_based_data.get('analytics', {})
            
            all_rules = {}
            all_rules.update(user_rules)
            all_rules.update(analytics_rules)
            
            for rule_name, rule_result in all_rules.items():
                if isinstance(rule_result, dict) and 'violations' in rule_result:
                    for violation in rule_result['violations']:
                        violation_rows.append({
                            'room_id': room_id,
                            'rule_name': rule_name,
                            'timestamp': violation.get('timestamp', ''),
                            'parameter': violation.get('parameter', ''),
                            'value': violation.get('value', 0),
                            'violation_type': violation.get('type', ''),
                            'deviation': violation.get('deviation', 0)
                        })
        
        if violation_rows:
            violations_df = pd.DataFrame(violation_rows)
            violations_df.to_excel(writer, sheet_name='Violations_Detail', index=False)
        
        # Building summary sheet
        building_rows = []
        for building_id, building_data in building_analysis.items():
            building_rows.append({
                'building_id': building_id,
                'room_count': building_data.get('room_count', 0),
                'average_performance_score': building_data.get('average_performance_score', 0),
                'average_comfort_compliance': building_data.get('average_comfort_compliance', 0),
                'average_data_quality': building_data.get('average_data_quality', 0)
            })
        
        if building_rows:
            building_df = pd.DataFrame(building_rows)
            building_df.to_excel(writer, sheet_name='Building_Summary', index=False)


def _generate_simple_recommendations(building_data: dict) -> list:
    """Generate simple recommendations based on building performance."""
    recommendations = []
    
    performance_score = building_data.get('average_performance_score', 0)
    comfort_compliance = building_data.get('average_comfort_compliance', 0)
    data_quality = building_data.get('average_data_quality', 0)
    
    if performance_score < 0.7:
        recommendations.append("Consider improving HVAC system performance to enhance indoor environmental quality.")
    
    if comfort_compliance < 0.8:
        recommendations.append("Review comfort thresholds and adjust climate controls to improve occupant satisfaction.")
    
    if data_quality < 0.9:
        recommendations.append("Check sensor calibration and data collection systems for improved monitoring accuracy.")
    
    if len(recommendations) == 0:
        recommendations.append("Building performance is within acceptable ranges. Continue regular monitoring.")
    
    return recommendations
