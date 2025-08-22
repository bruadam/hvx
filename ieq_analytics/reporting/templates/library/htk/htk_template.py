"""
HTK (Høje-Taastrup Kommune) Report Template

Comprehensive building performance analysis template for Høje-Taastrup Kommune.
Includes data quality assessment, building-specific analysis, room-level details,
and recommendations based on defined user rules.
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from jinja2 import Template
import logging
import glob
import yaml

from ieq_analytics.reporting.templates.base_template import BaseTemplate
from ieq_analytics.reporting.charts.manager import get_chart_library_manager
from ieq_analytics.unified_analytics import UnifiedAnalyticsEngine, AnalysisType
from ieq_analytics.ventilation_rate_predictor import VentilationRatePredictor
from ieq_analytics.reporting.floorplan_mapper import FloorplanMapper

logger = logging.getLogger(__name__)


class HTKReportTemplate(BaseTemplate):
    """HTK Report Template implementation."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent
        super().__init__(template_dir)
        
        self.chart_manager = get_chart_library_manager()
        self.ventilation_predictor = VentilationRatePredictor()
        # Note: Analytics integration would be added here
        
        # HTK-specific configuration
        self.co2_threshold = 1000  # ppm
        self.temp_min = 20  # °C
        self.temp_max = 26  # °C
        
    def generate_report(
        self,
        mapped_dir: Path,
        climate_dir: Path,
        output_dir: Path,
        config_path: Path,
        buildings: Optional[List[str]] = None,
        export_formats: List[str] = ["pdf", "html"],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate HTK report from mapped data.
        
        Args:
            data_dir: Directory containing mapped IEQ data files
            climate_dir: Directory containing climate data files
            output_dir: Directory to save the report
            config_path: Path to the configuration file
            buildings: List of specific buildings to include (None for all)
            export_formats: Export formats ['pdf', 'html']
            **kwargs: Additional configuration options
            
        Returns:
            Dict with generation results and file paths
        """
        logger.info("Starting HTK report generation")
        
        # Ensure we have Path objects
        mapped_dir = Path(mapped_dir)
        climate_dir = Path(climate_dir)
        output_dir = Path(output_dir)
        config_path = Path(config_path)

        # Load tests.yaml
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            logger.warning(f"Config file not found: {config_path}")
            config = {}

        # Create analysis output directory
        analysis_dir = output_dir / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Run analytics on mapped data to get fresh results
        logger.info("Running analytics on mapped data...")
        analysis_data = self._run_analytics(mapped_dir, analysis_dir)
        
        # Filter buildings if specified
        if buildings:
            analysis_data = {k: v for k, v in analysis_data.items() if k in buildings}
        
        # Generate report data
        report_data = self._prepare_report_data(analysis_data, config)
        
        # Load mapped data for chart generation
        mapped_data_dir = mapped_dir.parent / "mapped_data" if (mapped_dir.parent / "mapped_data").exists() else mapped_dir
        mapped_data = self._load_mapped_data(mapped_data_dir)
        
        # Generate charts using mapped data
        charts_dir = output_dir / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)
        chart_paths = self._generate_charts(mapped_data, charts_dir, config)
        
        # Prepare template context
        template_context = self._prepare_template_context(report_data, chart_paths, mapped_data, config)
        
        # Generate reports in requested formats
        generated_files = {}
        for format_type in export_formats:
            if format_type == "html":
                file_path = self._generate_html_report(template_context, output_dir)
                generated_files["html"] = file_path
            elif format_type == "pdf":
                file_path = self._generate_pdf_report(template_context, output_dir)
                generated_files["pdf"] = file_path
        
        logger.info(f"HTK report generation completed. Files: {list(generated_files.keys())}")
        
        return {
            "success": True,
            "files": generated_files,
            "buildings_analyzed": list(analysis_data.keys()),
            "charts_generated": len(chart_paths),
            "generation_time": datetime.now().isoformat()
        }
    
    def _load_mapped_data(self, mapped_data_dir: Path) -> Dict[str, pd.DataFrame]:
        """Load mapped data files for chart generation and basic statistics."""
        logger.info(f"Loading mapped data from: {mapped_data_dir}")
        
        mapped_data = {}
        
        # Find all mapped data files
        csv_files = list(mapped_data_dir.glob("*_processed.csv"))
        if not csv_files:
            logger.warning(f"No mapped data files found in {mapped_data_dir}")
            return mapped_data
        
        for file_path in csv_files:
            try:
                # Load the CSV file
                df = pd.read_csv(file_path)
                
                # Parse timestamp column
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.set_index('timestamp')
                
                # Extract room/building identifier from filename
                room_id = file_path.stem.replace('_processed', '')
                mapped_data[room_id] = df
                
                logger.info(f"Loaded {len(df)} records for {room_id}")
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                continue
        
        logger.info(f"Loaded mapped data for {len(mapped_data)} rooms")
        return mapped_data
    
    def _calculate_basic_statistics(self, mapped_data: Dict[str, pd.DataFrame], config: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
        """Calculate basic statistics from mapped data."""
        statistics = {}
        
        for room_id, df in mapped_data.items():
            room_stats = {
                'temperature': {},
                'co2': {},
                'humidity': {},
                'data_quality': {}
            }
            
            # Temperature statistics
            if 'temperature' in df.columns:
                temp_data = df['temperature'].dropna()
                room_stats['temperature'] = {
                    'mean': float(temp_data.mean()),
                    'std': float(temp_data.std()),
                    'min': float(temp_data.min()),
                    'max': float(temp_data.max()),
                    'median': float(temp_data.median()),
                    'count': len(temp_data)
                }
            
            # CO2 statistics
            if 'co2' in df.columns:
                co2_data = df['co2'].dropna()
                room_stats['co2'] = {
                    'mean': float(co2_data.mean()),
                    'std': float(co2_data.std()),
                    'min': float(co2_data.min()),
                    'max': float(co2_data.max()),
                    'median': float(co2_data.median()),
                    'count': len(co2_data)
                }
            
            # Humidity statistics
            if 'humidity' in df.columns:
                humidity_data = df['humidity'].dropna()
                room_stats['humidity'] = {
                    'mean': float(humidity_data.mean()),
                    'std': float(humidity_data.std()),
                    'min': float(humidity_data.min()),
                    'max': float(humidity_data.max()),
                    'median': float(humidity_data.median()),
                    'count': len(humidity_data)
                }
            
            # Ventilation rate (ACH) prediction
            room_stats['ventilation'] = self._calculate_ach_analysis(df)
            
            # Temperature-based solar shading recommendation
            room_stats['solar_shading'] = self._calculate_solar_shading_recommendation(df)
            
            # Detailed compliance analysis with separated thresholds and periods
            room_stats['compliance_analysis'] = self._calculate_detailed_compliance(df, room_id, config)
            
            # Data quality statistics
            total_expected = len(df)
            missing_temp = df['temperature'].isna().sum() if 'temperature' in df.columns else 0
            missing_co2 = df['co2'].isna().sum() if 'co2' in df.columns else 0
            missing_humidity = df['humidity'].isna().sum() if 'humidity' in df.columns else 0
            
            room_stats['data_quality'] = {
                'total_records': total_expected,
                'missing_temperature': int(missing_temp),
                'missing_co2': int(missing_co2),
                'missing_humidity': int(missing_humidity),
                'completeness_temperature': float((total_expected - missing_temp) / total_expected * 100) if total_expected > 0 else 0,
                'completeness_co2': float((total_expected - missing_co2) / total_expected * 100) if total_expected > 0 else 0,
                'completeness_humidity': float((total_expected - missing_humidity) / total_expected * 100) if total_expected > 0 else 0,
                'start_date': df.index.min().strftime('%Y-%m-%d') if not df.empty and hasattr(df.index, 'min') else 'N/A',
                'end_date': df.index.max().strftime('%Y-%m-%d') if not df.empty and hasattr(df.index, 'max') else 'N/A'
            }
            
            statistics[room_id] = room_stats
        
        return statistics
    
    def _aggregate_building_statistics(self, rooms_with_charts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate basic statistics from rooms to building level."""
        building_stats = {
            'temperature': {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'median': 0.0, 'count': 0},
            'co2': {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'median': 0.0, 'count': 0},
            'humidity': {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'median': 0.0, 'count': 0},
            'data_quality': {'total_records': 0, 'completeness_temperature': 0.0, 'completeness_co2': 0.0, 'completeness_humidity': 0.0}
        }
        
        rooms_with_stats = [room for room in rooms_with_charts if 'basic_statistics' in room]
        
        if not rooms_with_stats:
            return building_stats
        
        # Aggregate temperature statistics
        temp_means = [room['basic_statistics']['temperature']['mean'] for room in rooms_with_stats if room['basic_statistics']['temperature']['count'] > 0]
        if temp_means:
            building_stats['temperature']['mean'] = float(np.mean(temp_means))
            building_stats['temperature']['min'] = float(min([room['basic_statistics']['temperature']['min'] for room in rooms_with_stats if room['basic_statistics']['temperature']['count'] > 0]))
            building_stats['temperature']['max'] = float(max([room['basic_statistics']['temperature']['max'] for room in rooms_with_stats if room['basic_statistics']['temperature']['count'] > 0]))
            building_stats['temperature']['median'] = float(np.median([room['basic_statistics']['temperature']['median'] for room in rooms_with_stats if room['basic_statistics']['temperature']['count'] > 0]))
            building_stats['temperature']['count'] = sum([room['basic_statistics']['temperature']['count'] for room in rooms_with_stats])
        
        # Aggregate CO2 statistics
        co2_means = [room['basic_statistics']['co2']['mean'] for room in rooms_with_stats if room['basic_statistics']['co2']['count'] > 0]
        if co2_means:
            building_stats['co2']['mean'] = float(np.mean(co2_means))
            building_stats['co2']['min'] = float(min([room['basic_statistics']['co2']['min'] for room in rooms_with_stats if room['basic_statistics']['co2']['count'] > 0]))
            building_stats['co2']['max'] = float(max([room['basic_statistics']['co2']['max'] for room in rooms_with_stats if room['basic_statistics']['co2']['count'] > 0]))
            building_stats['co2']['median'] = float(np.median([room['basic_statistics']['co2']['median'] for room in rooms_with_stats if room['basic_statistics']['co2']['count'] > 0]))
            building_stats['co2']['count'] = sum([room['basic_statistics']['co2']['count'] for room in rooms_with_stats])
        
        # Aggregate humidity statistics
        humidity_means = [room['basic_statistics']['humidity']['mean'] for room in rooms_with_stats if room['basic_statistics']['humidity']['count'] > 0]
        if humidity_means:
            building_stats['humidity']['mean'] = float(np.mean(humidity_means))
            building_stats['humidity']['min'] = float(min([room['basic_statistics']['humidity']['min'] for room in rooms_with_stats if room['basic_statistics']['humidity']['count'] > 0]))
            building_stats['humidity']['max'] = float(max([room['basic_statistics']['humidity']['max'] for room in rooms_with_stats if room['basic_statistics']['humidity']['count'] > 0]))
            building_stats['humidity']['median'] = float(np.median([room['basic_statistics']['humidity']['median'] for room in rooms_with_stats if room['basic_statistics']['humidity']['count'] > 0]))
            building_stats['humidity']['count'] = sum([room['basic_statistics']['humidity']['count'] for room in rooms_with_stats])
        
        # Aggregate data quality
        building_stats['data_quality']['total_records'] = sum([room['basic_statistics']['data_quality']['total_records'] for room in rooms_with_stats])
        if len(rooms_with_stats) > 0:
            building_stats['data_quality']['completeness_temperature'] = float(np.mean([room['basic_statistics']['data_quality']['completeness_temperature'] for room in rooms_with_stats]))
            building_stats['data_quality']['completeness_co2'] = float(np.mean([room['basic_statistics']['data_quality']['completeness_co2'] for room in rooms_with_stats]))
            building_stats['data_quality']['completeness_humidity'] = float(np.mean([room['basic_statistics']['data_quality']['completeness_humidity'] for room in rooms_with_stats]))
        
        return building_stats
    
    def _run_analytics(self, mapped_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Run analytics on mapped data and return structured results."""
        logger.info(f"Running analytics on mapped data directory: {mapped_dir}")
        
        # Find mapped data files (exclude summary files)
        mapped_files = [f for f in mapped_dir.glob("*.csv") if "summary" not in f.name.lower()]
        if not mapped_files:
            logger.warning(f"No mapped CSV files found in mapped data directory: {mapped_dir}")
            return {}
        
        # Initialize analytics engine
        rules_config = Path("config/tests.yaml")
        if not rules_config.exists():
            logger.warning(f"Rules config not found: {rules_config}")
            rules_config = None
        
        try:
            # Initialize analytics engine
            analytics_engine = UnifiedAnalyticsEngine(rules_config)
            
            # Process each mapped file
            all_results = {}
            
            for file_path in mapped_files:
                logger.info(f"Processing file: {file_path.name}")
                
                try:
                    # Load the data
                    df = pd.read_csv(file_path)
                    
                    if df.empty:
                        logger.warning(f"Empty data file: {file_path}")
                        continue
                    
                    # Extract room ID from filename or data
                    room_id = file_path.stem
                    
                    # Check for available columns (be flexible about column names)
                    available_columns = df.columns.tolist()
                    logger.info(f"Available columns in {file_path}: {available_columns}")
                    
                    # Look for timestamp column (various possible names)
                    timestamp_col = None
                    for col in ['timestamp', 'time', 'date', 'datetime', 'DateTime']:
                        if col in df.columns:
                            timestamp_col = col
                            break
                    
                    if timestamp_col:
                        # Convert timestamp to datetime
                        df['timestamp'] = pd.to_datetime(df[timestamp_col])
                        df = df.set_index('timestamp')
                    else:
                        logger.warning(f"No timestamp column found in {file_path}, using row index")
                        # Create a simple index if no timestamp
                        df.index.name = 'timestamp'
                    
                    # Run analytics on this room using unified engine
                    # You can add here the rules to run if you want to.
                    room_results = analytics_engine.analyze_room_data(
                        df, 
                        room_id,
                        analysis_types=[
                            AnalysisType.BASIC_STATISTICS,
                            AnalysisType.DATA_QUALITY,
                            AnalysisType.USER_RULES
                        ]
                    )
                    
                    # Extract building name from room ID
                    # e.g., "ole_rømer_skolen_107" -> "ole_rømer_skolen"
                    parts = room_id.split('_')
                    if len(parts) >= 2:
                        # Find the last part that's not a number
                        building_parts = []
                        for part in parts:
                            # If it's a number or looks like a room identifier, stop
                            if part.replace('.', '').isdigit() or (len(part) <= 3 and any(c.isdigit() for c in part)):
                                break
                            building_parts.append(part)
                        
                        if building_parts:
                            building_name = '_'.join(building_parts)
                        else:
                            building_name = 'unknown'
                    else:
                        building_name = 'unknown'
                    

                    # Organize by building
                    if building_name not in all_results:
                        all_results[building_name] = {
                            'building_name': building_name.replace('_', ' ').title(),
                            'rooms': {},
                            'data_quality': {
                                'completeness': 0,
                                'missing_periods': "Minimal gaps",
                                'quality_score': "High"
                            }
                        }
                    
                    # Convert room results to expected format
                    room_data = self._convert_analytics_result_to_room_data(room_results)
                    all_results[building_name]['rooms'][room_id] = room_data
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    continue
            
            # Calculate building-level data quality based on completeness of the rooms
            for building_name, building_data in all_results.items():
                if building_data['rooms']:
                    room_completeness = [
                        room['data_quality']['completeness']
                        for room in building_data['rooms'].values()
                        if 'data_quality' in room
                    ]
                    if room_completeness:
                        building_data['data_quality']['completeness'] = float(np.mean(room_completeness))
                        # Give a qualitative assessment based on completeness
                        if building_data['data_quality']['completeness'] >= 90:
                            building_data['data_quality']['quality_score'] = "High"
                            building_data['data_quality']['missing_periods'] = "Minimal gaps"
                        elif building_data['data_quality']['completeness'] >= 75:
                            building_data['data_quality']['quality_score'] = "Medium"
                            building_data['data_quality']['missing_periods'] = "Some gaps"
                        else:
                            building_data['data_quality']['quality_score'] = "Low"
                            building_data['data_quality']['missing_periods'] = "Significant gaps"


            # Save analytics results
            summary_file = output_dir / "ieq_analysis_summary.csv"
            self._save_analytics_summary(all_results, summary_file)
            
            logger.info(f"Analytics completed. Processed {len(all_results)} buildings")
            return all_results
            
        except Exception as e:
            logger.error(f"Error running analytics: {e}")
            return {}
    
    def _convert_analytics_result_to_room_data(self, analytics_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert analytics engine result to room data format expected by template."""
        room_data = {
            'test_results': {},
            'statistics': {
                'co2': {'mean': 0, 'std': 0, 'min': 0, 'max': 0},
                'temperature': {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
            },
            'data_quality': {
                'completeness': 0,
            }
        }
        
        # Extract statistics if available
        if 'basic_statistics' in analytics_result:
            stats = analytics_result['basic_statistics']
            if 'co2' in stats:
                room_data['statistics']['co2'] = stats['co2']
            if 'temperature' in stats:
                room_data['statistics']['temperature'] = stats['temperature']
        
        # Extract rule results if available
        if 'user_rules' in analytics_result:
            rules = analytics_result['user_rules']
            for rule_name, rule_result in rules.items():
                room_data['test_results'][rule_name] = {
                    'compliance_rate': rule_result.get('compliance_rate', 0.0),
                    'violations_count': rule_result.get('violations_count', 0),
                    'total_hours': rule_result.get('total_hours', 0),
                    'mean': rule_result.get('mean_value', 0)
                }

        if 'data_quality' in analytics_result:
            percentages = {k: v['percentage'] for k, v in analytics_result['data_quality']['completeness'].items() if 'percentage' in v}
            avg_completeness = sum(percentages.values()) / len(percentages) if percentages else 0
            room_data['data_quality'] = {
                'completeness': float(avg_completeness)
            }

        return room_data
    
    def _save_analytics_summary(self, results: Dict[str, Any], output_file: Path):
        """Save analytics results to CSV summary file."""
        try:
            rows = []
            for building_name, building_data in results.items():
                for room_id, room_data in building_data.get('rooms', {}).items():
                    row = {'room_id': room_id, 'building': building_name}
                    
                    # Add test results as columns
                    for test_name, test_result in room_data.get('test_results', {}).items():
                        row[f"{test_name}_compliance_rate"] = test_result.get('compliance_rate', 0)  # Already a percentage
                        row[f"{test_name}_non_compliant_hours"] = test_result.get('violations_count', 0)
                        row[f"{test_name}_total_hours"] = test_result.get('total_hours', 0)
                    
                    rows.append(row)
            
            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(output_file, index=False)
                logger.info(f"Analytics summary saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving analytics summary: {e}")
    
    def _load_analysis_data(self, data_dir: Path) -> Dict[str, Any]:
        """Load analyzed data from the analytics engine."""
        analysis_data = {}
        
        # Look for the main analysis CSV file
        csv_file = data_dir / "ieq_analysis_summary.csv"
        
        if not csv_file.exists():
            logger.warning(f"Analysis summary file not found: {csv_file}")
            return analysis_data
        
        try:
            # Load the CSV data
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded {len(df)} room records from analysis summary")
            
            # Group rooms by building (extract building name from room_id)
            for _, row in df.iterrows():
                room_id = row['room_id']
                
                # Extract building name (everything before the last underscore and number)
                # e.g., "ole_rømer_skolen_107" -> "ole_rømer_skolen"
                parts = room_id.split('_')
                if len(parts) >= 2:
                    # Find the last part that's not a number
                    building_parts = []
                    for part in parts:
                        # If it's a number or looks like a room identifier, stop
                        if part.replace('.', '').isdigit() or (len(part) <= 3 and any(c.isdigit() for c in part)):
                            break
                        building_parts.append(part)
                    
                    if building_parts:
                        building_name = '_'.join(building_parts)
                        room_name = room_id[len(building_name)+1:]  # Everything after building name
                    else:
                        building_name = 'unknown'
                        room_name = room_id
                else:
                    building_name = 'unknown'
                    room_name = room_id
                
                # Create building entry if not exists
                if building_name not in analysis_data:
                    analysis_data[building_name] = {
                        'building_name': building_name.replace('_', ' ').title(),
                        'rooms': {},
                        'data_quality': {
                            'completeness': 100,  # Will be calculated from room data
                            'missing_periods': "None",
                            'quality_score': "High"
                        }
                    }
                
                # Convert CSV row to room data structure
                room_data = self._convert_csv_row_to_room_data(row)
                analysis_data[building_name]['rooms'][room_name] = room_data
            
            # Calculate building-level data quality
            for building_name, building_data in analysis_data.items():
                building_data['data_quality'] = self._calculate_building_data_quality(building_data['rooms'])
            
            logger.info(f"Processed {len(analysis_data)} buildings with analysis data")
            
        except Exception as e:
            logger.error(f"Error loading analysis data: {e}")
            
        return analysis_data
    
    def _prepare_report_data(self, analysis_data: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare structured report data from analysis results."""
        report_data = {
            "buildings": [],
            "overall_metrics": {},
            "data_quality": [],
            "recommendations": []
        }
        
        # Process each building
        building_metrics = []
        for building_name, building_data in analysis_data.items():
            building_info = self._process_building_data(building_name, building_data, analysis_data)
            report_data["buildings"].append(building_info)
            building_metrics.append(building_info["metrics"])
        
        # Calculate overall metrics
        if building_metrics:
            report_data["overall_metrics"] = self._calculate_overall_metrics(building_metrics)
        else:
            # Fallback for empty building metrics
            report_data["overall_metrics"] = {
                "overall_performance": {"value": 0.0, "class": "poor"},
                "co2_compliance": {"value": 0.0, "class": "poor"},
                "temperature_compliance": {"value": 0.0, "class": "poor"}
            }
        
        # Generate data quality assessment
        report_data["data_quality"] = self._assess_data_quality(analysis_data)
        
        # Generate recommendations
        report_data["recommendations"] = self._generate_recommendations(analysis_data)
        
        return report_data
    
    def _process_building_data(self, building_name: str, building_data: Dict[str, Any], analysis_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process analysis data for a single building."""
        building_info = {
            "id": building_name.lower().replace(" ", "_"),
            "name": building_name,
            "rooms": [],
            "metrics": {},
            "top_issue_rooms": [],
            "recommendations": []
        }
        
        # Process room data
        room_metrics = []
        if "rooms" in building_data:
            for room_name, room_data in building_data["rooms"].items():
                room_info = self._process_room_data(room_name, room_data)
                building_info["rooms"].append(room_info)
                room_metrics.append(room_info["metrics"])
        
        # Calculate building-level metrics
        if room_metrics:
            # Use the old aggregation method which works correctly
            building_info["metrics"] = self._calculate_old_building_metrics(room_metrics)
        
        # Calculate performance attributes expected by template
        co2_performance = building_info["metrics"].get("co2_compliance", building_info["metrics"].get("co2_2000_compliance", 85.0))
        temp_performance = building_info["metrics"].get("temp_compliance", 90.0)
        
        building_info.update({
            # Performance metrics with styling classes
            "co2_performance": {
                "value": f"{co2_performance:.1f}",
                "class": self._get_performance_class(co2_performance)
            },
            "temp_performance": {
                "value": f"{temp_performance:.1f}",
                "class": self._get_performance_class(temp_performance)
            },
            
            # Data quality attributes
            "completeness": building_data.get("data_quality", {}).get("completeness", 95),
            "missing_periods": building_data.get("data_quality", {}).get("missing_periods", "Minimal gaps"),
            "quality_score": building_data.get("data_quality", {}).get("quality_score", "High"),
            "quality_class": self._get_quality_class(building_data.get("data_quality", {}).get("quality_score", "High")),
            "notes": "Automated analysis results",
            
            # Basic counts
            "room_count": len(building_info["rooms"])
        })
        
        # Identify top issue rooms
        building_info["top_issue_rooms"] = self._identify_top_issue_rooms(building_info["rooms"])
        
        # Generate building-specific recommendations
        building_info["recommendations"] = self._generate_building_recommendations(building_info)
        
        return building_info
    
    def _process_room_data(self, room_name: str, room_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process analysis data for a single room."""
        room_info = {
            "name": room_name,
            "metrics": {},
            "daily_periods": [],
            "seasons": [],
            "issues": []
        }
        
        # Extract compliance metrics
        room_info["metrics"] = self._extract_room_metrics(room_data)
        
        # Add template-expected attributes
        co2_compliance = room_info["metrics"].get("co2_compliance", 85.0)
        temp_compliance = room_info["metrics"].get("temp_compliance", 90.0)
        
        room_info.update({
            "co2_performance": {
                "value": f"{co2_compliance:.1f}",
                "class": self._get_performance_class(co2_compliance)
            },
            "temp_performance": {
                "value": f"{temp_compliance:.1f}",
                "class": self._get_performance_class(temp_compliance)
            },
            "data_quality": {
                "value": "95.0",  # Placeholder for data quality percentage
                "class": "good"
            },
            "sensor_count": 2,  # Placeholder for sensor count (usually temp + co2)
            "id": room_name.lower().replace(" ", "_").replace(".", "_"),
            "status": "Good" if co2_compliance > 80 and temp_compliance > 80 else "Warning",
            "status_class": "good" if co2_compliance > 80 and temp_compliance > 80 else "warning"
        })
        
        # Process daily periods
        room_info["daily_periods"] = self._process_daily_periods(room_data)
        
        # Process seasonal data
        room_info["seasons"] = self._process_seasonal_data(room_data)
        
        # Identify issues
        room_info["issues"] = self._identify_room_issues(room_data)
        
        return room_info
    
    def _extract_room_metrics(self, room_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from room analysis data."""
        metrics = {
            "co2_compliance": 0,
            "temp_compliance": 0,
            "avg_co2": 0,
            "avg_temp": 0,
            "co2_violations": 0,
            "temp_violations": 0
        }
        
        # Extract from test results if available
        if "test_results" in room_data:
            test_results = room_data["test_results"]
            
            # CO2 compliance (opening hours)
            co2_test = test_results.get("co2_1000_all_year_opening", {})
            if "compliance_rate" in co2_test:
                metrics["co2_compliance"] = co2_test["compliance_rate"]  # Already percentage
            if "violations_count" in co2_test:
                metrics["co2_violations"] = co2_test["violations_count"]
            
            # Temperature compliance (opening hours)
            temp_test = test_results.get("temp_comfort_zone_20_26_all_year_opening", {})
            if "compliance_rate" in temp_test:
                metrics["temp_compliance"] = temp_test["compliance_rate"]  # Already percentage
            if "violations_count" in temp_test:
                metrics["temp_violations"] = temp_test["violations_count"]
        
        # Extract averages from statistics if available
        if "statistics" in room_data:
            stats = room_data["statistics"]
            metrics["avg_co2"] = stats.get("co2", {}).get("mean", 0)
            metrics["avg_temp"] = stats.get("temperature", {}).get("mean", 0)
        
        return metrics
    
    def _process_daily_periods(self, room_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process daily period performance."""
        periods = []
        period_names = {
            "morning": "Morgen (08-12)",
            "afternoon": "Eftermiddag (12-16)",
            "evening": "Aften (16-21)"
        }
        
        if "test_results" not in room_data:
            return periods
        
        test_results = room_data["test_results"]
        
        for period_key, period_name in period_names.items():
            period_data = {
                "name": period_name,
                "co2_compliance": "N/A",
                "temp_compliance": "N/A", 
                "avg_co2": "N/A",
                "avg_temp": "N/A",
                "co2_class": "neutral",
                "temp_class": "neutral"
            }
            
            # Look for period-specific test results
            co2_test_key = f"co2_1000_{period_key}"
            temp_test_key = f"temp_summer_limit_{period_key}"
            
            if co2_test_key in test_results:
                compliance_rate = test_results[co2_test_key].get("compliance_rate", 0)
                if compliance_rate > 0:  # Only show if we have actual data
                    period_data["co2_compliance"] = f"{compliance_rate:.1f}"
                    period_data["co2_class"] = self._get_performance_class(compliance_rate)
                    mean_value = test_results[co2_test_key].get("mean", 0)
                    if mean_value > 0:
                        period_data["avg_co2"] = f"{mean_value:.0f}"
            
            if temp_test_key in test_results:
                compliance_rate = test_results[temp_test_key].get("compliance_rate", 0)
                if compliance_rate > 0:  # Only show if we have actual data
                    period_data["temp_compliance"] = f"{compliance_rate:.1f}"
                    period_data["temp_class"] = self._get_performance_class(compliance_rate)
                    mean_value = test_results[temp_test_key].get("mean", 0)
                    if mean_value > 0:
                        period_data["avg_temp"] = f"{mean_value:.1f}"
            
            periods.append(period_data)
        
        return periods
    
    def _process_seasonal_data(self, room_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process seasonal performance."""
        seasons = []
        season_names = {
            "spring": "Forår",
            "summer": "Sommer", 
            "autumn": "Efterår",
            "winter": "Vinter"
        }
        
        # Use compliance_analysis data which has better structure for averages
        compliance_analysis = room_data.get("compliance_analysis", {})
        if not compliance_analysis:
            return seasons
        
        # Also keep test_results for seasonal compliance rates
        test_results = room_data.get("test_results", {})
        
        for season_key, season_name in season_names.items():
            season_data = {
                "name": season_name,
                "co2_1000_compliance": "N/A",
                "co2_2000_compliance": "N/A", 
                "temp_compliance": "N/A",
                "avg_co2": "N/A",
                "avg_temp": "N/A",
                "co2_1000_class": "neutral",
                "co2_2000_class": "neutral",
                "temp_class": "neutral",
                "avg_co2_class": "neutral",
                "avg_temp_class": "neutral"
            }
            
            # Look for seasonal test results - CO2 1000ppm
            co2_1000_test_key = f"co2_1000_{season_key}_opening"
            co2_2000_test_key = f"co2_2000_{season_key}_opening"
            temp_test_key = "temp_comfort_zone_20_26_all_year_opening"  # Temperature test is only all_year
            
            if co2_1000_test_key in test_results:
                compliance_rate = test_results[co2_1000_test_key].get("compliance_rate", 0)
                if compliance_rate > 0:  # Only show if we have actual data
                    season_data["co2_1000_compliance"] = f"{compliance_rate:.1f}"
                    season_data["co2_1000_class"] = self._get_performance_class(compliance_rate)
                # Always try to get mean value regardless of compliance rate
                mean_value = test_results[co2_1000_test_key].get("mean", 0)
                if mean_value > 0:
                    season_data["avg_co2"] = f"{mean_value:.0f}"
                    season_data["avg_co2_class"] = "good" if mean_value < 800 else "warning" if mean_value < 1200 else "danger"
            
            # Also try to get mean values from compliance_analysis opening_hours data
            co2_compliance = compliance_analysis.get('co2_compliance', {})
            temp_compliance = compliance_analysis.get('temperature_compliance', {})
            opening_hours_co2 = co2_compliance.get('opening_hours', {})
            opening_hours_temp = temp_compliance.get('opening_hours', {})
            
            # Extract mean values if not already set
            if season_data["avg_co2"] == "N/A" and opening_hours_co2.get('mean_co2'):
                mean_co2 = float(opening_hours_co2['mean_co2'])
                season_data["avg_co2"] = f"{mean_co2:.0f}"
                season_data["avg_co2_class"] = "good" if mean_co2 < 800 else "warning" if mean_co2 < 1200 else "danger"
            
            if season_data["avg_temp"] == "N/A" and opening_hours_temp.get('mean_temperature'):
                mean_temp = float(opening_hours_temp['mean_temperature'])
                season_data["avg_temp"] = f"{mean_temp:.1f}"
                season_data["avg_temp_class"] = "good" if 20 <= mean_temp <= 24 else "warning" if 18 <= mean_temp <= 26 else "danger"
            
            # CO2 2000ppm data
            if co2_2000_test_key in test_results:
                compliance_rate = test_results[co2_2000_test_key].get("compliance_rate", 0)
                if compliance_rate > 0:
                    season_data["co2_2000_compliance"] = f"{compliance_rate:.1f}"
                    season_data["co2_2000_class"] = self._get_performance_class(compliance_rate)
            
            # Temperature data
            if temp_test_key in test_results:
                compliance_rate = test_results[temp_test_key].get("compliance_rate", 0)
                if compliance_rate > 0:  # Only show if we have actual data
                    season_data["temp_compliance"] = f"{compliance_rate:.1f}"
                    season_data["temp_class"] = self._get_performance_class(compliance_rate)
                # Always try to get mean value regardless of compliance rate
                mean_value = test_results[temp_test_key].get("mean", 0)
                if mean_value > 0:
                    season_data["avg_temp"] = f"{mean_value:.1f}"
                    season_data["avg_temp_class"] = "good" if 20 <= mean_value <= 24 else "warning" if 18 <= mean_value <= 26 else "danger"
            
            seasons.append(season_data)
        
        return seasons
    
    def _identify_room_issues(self, room_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify issues in a room."""
        issues = []
        
        if "test_results" not in room_data:
            return issues
        
        test_results = room_data["test_results"]
        
        # Check CO2 compliance
        co2_test = test_results.get("co2_1000_all_year_opening", {})
        if co2_test.get("compliance_rate", 1) < 0.9:  # Less than 90% compliance
            issues.append({
                "type": "co2",
                "severity": "high" if co2_test.get("compliance_rate", 1) < 0.7 else "medium",
                "description": f"CO₂ overholdelse: {co2_test.get('compliance_rate', 0):.1f}%"  # Already percentage
            })
        
        # Check temperature compliance
        temp_test = test_results.get("temp_comfort_all_year_opening", {})
        if temp_test.get("compliance_rate", 1) < 0.9:  # Less than 90% compliance
            issues.append({
                "type": "temperature",
                "severity": "high" if temp_test.get("compliance_rate", 1) < 0.7 else "medium",
                "description": f"Temperatur overholdelse: {temp_test.get('compliance_rate', 0):.1f}%"  # Already percentage
            })
        
        return issues
    
    def _calculate_old_building_metrics(self, room_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate building-level metrics from room metrics."""
        if not room_metrics:
            return {}
        
        metrics = {
            "co2_compliance": np.mean([r["co2_compliance"] for r in room_metrics]),
            "temp_compliance": np.mean([r["temp_compliance"] for r in room_metrics]),
            "avg_co2": np.mean([r["avg_co2"] for r in room_metrics]),
            "avg_temp": np.mean([r["avg_temp"] for r in room_metrics]),
            "total_co2_violations": sum([r["co2_violations"] for r in room_metrics]),
            "total_temp_violations": sum([r["temp_violations"] for r in room_metrics]),
            "room_count": len(room_metrics)
        }
        
        # Add performance classes
        metrics["co2_performance"] = {
            "value": round(metrics["co2_compliance"], 1),
            "class": self._get_performance_class(metrics["co2_compliance"])
        }
        metrics["temp_performance"] = {
            "value": round(metrics["temp_compliance"], 1),
            "class": self._get_performance_class(metrics["temp_compliance"])
        }
        
        return metrics
    
    def _calculate_overall_metrics(self, building_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall metrics across all buildings."""
        if not building_metrics:
            # Return default values when no building metrics available
            return {
                "overall_performance": {
                    "value": 0.0,
                    "class": "poor"
                },
                "co2_compliance": {
                    "value": 0.0,
                    "class": "poor"
                },
                "temp_compliance": {
                    "value": 0.0,
                    "class": "poor"
                }
            }
        
        # Handle both old and new key names for building metrics
        overall_co2 = np.mean([b.get("co2_compliance", b.get("co2_2000_compliance", 0)) for b in building_metrics])
        overall_temp = np.mean([b.get("temp_compliance", 0) for b in building_metrics])
        overall_performance = (overall_co2 + overall_temp) / 2
        
        return {
            "overall_performance": {
                "value": round(float(overall_performance), 1),
                "class": self._get_performance_class(float(overall_performance))
            },
            "co2_compliance": {
                "value": round(float(overall_co2), 1),
                "class": self._get_performance_class(float(overall_co2))
            },
            "temperature_compliance": {
                "value": round(float(overall_temp), 1),
                "class": self._get_performance_class(float(overall_temp))
            }
        }
    
    def _get_performance_class(self, value: float) -> str:
        """Get CSS class based on performance value."""
        if value >= 90:
            return "good"
        elif value >= 70:
            return "warning"
        else:
            return "danger"
    
    def _get_quality_class(self, quality_score: str) -> str:
        """Get CSS class for quality score."""
        if quality_score == "High":
            return "good"
        elif quality_score == "Medium":
            return "warning"
        else:
            return "danger"
    
    def _identify_top_issue_rooms(self, rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify rooms with the most issues."""
        room_scores = []
        
        for room in rooms:
            score = 0
            # Calculate issue score based on violations
            metrics = room["metrics"]
            score += metrics.get("co2_violations", 0)
            score += metrics.get("temp_violations", 0)
            
            room_scores.append({
                "name": room["name"],
                "score": score,
                "co2_compliance": metrics.get("co2_compliance", 0),
                "temp_compliance": metrics.get("temp_compliance", 0)
            })
        
        # Sort by score (descending) and return top 10
        room_scores.sort(key=lambda x: x["score"], reverse=True)
        return room_scores[:10]
    
    def _assess_data_quality(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess data quality for each building."""
        data_quality = []
        
        for building_name, building_data in analysis_data.items():
            quality_info = {
                "name": building_name,
                "completeness": 100,  # Default to 100%
                "missing_periods": "Ingen",
                "quality_score": "Høj",
                "quality_class": "good",
                "notes": "God datakvalitet"
            }
            
            # Check if we have quality metrics in the data
            if "data_quality" in building_data:
                quality_metrics = building_data["data_quality"]
                quality_info["completeness"] = quality_metrics.get("completeness", 100)
                quality_info["missing_periods"] = quality_metrics.get("missing_periods", "Ingen")
                
                # Determine quality score
                completeness = quality_info["completeness"]
                if completeness >= 95:
                    quality_info["quality_score"] = "Høj"
                    quality_info["quality_class"] = "good"
                elif completeness >= 85:
                    quality_info["quality_score"] = "Medium"
                    quality_info["quality_class"] = "warning"
                else:
                    quality_info["quality_score"] = "Lav"
                    quality_info["quality_class"] = "danger"
            
            data_quality.append(quality_info)
        
        return data_quality
    
    def _generate_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # This is a simplified implementation - in a real scenario,
        # you would analyze the data patterns to generate specific recommendations
        
        for building_name, building_data in analysis_data.items():
            building_recs = self._generate_building_recommendations({
                "name": building_name,
                "data": building_data
            })
            recommendations.extend(building_recs)
        
        return recommendations
    
    def _generate_building_recommendations(self, building_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for a specific building."""
        recommendations = []
        
        # This is a template - you would implement real logic based on the analysis results
        building_name = building_info.get("name", "Unknown")
        
        recommendations.append({
            "title": f"Forbedre ventilation i {building_name}",
            "description": "Øg ventilationsraten i rum med højt CO₂-niveau",
            "building": building_name
        })
        
        recommendations.append({
            "title": f"Optimér temperaturregulering i {building_name}",
            "description": "Justér termostatindstillinger for bedre komfort",
            "building": building_name
        })
        
        return recommendations
    
    def _generate_charts(self, mapped_data: Dict[str, pd.DataFrame], charts_dir: Path, config: Dict[str, Any]) -> Dict[str, str]:
        """Generate all required charts for the report using mapped data."""
        from .charts import generate_htk_charts_from_mapped_data
        
        logger.info("Generating HTK charts from mapped data...")
        chart_paths = generate_htk_charts_from_mapped_data(mapped_data, charts_dir, config)
        logger.info(f"Generated {len(chart_paths)} charts")
        
        return chart_paths
    
    def _get_friendly_name(self, original_name: str) -> str:
        """Convert building/room slugs to friendly names."""
        # Define mapping from slugs to friendly names
        friendly_mappings = {
            # Buildings
            "floeng-skole": "Fløng Skolen",
            "fløng-skole": "Fløng Skolen",
            "ole-roemer-skolen": "Ole Rømer-Skolen",
            "ole_roemer-skolen": "Ole Rømer-Skolen",
            "reerslev": "Reerslev Skolen",
            
            # Common room patterns  
            "klasserum": "Klasserum",
            "kontor": "Kontor",
            "gang": "Gang",
            "bibliotek": "Bibliotek",
            "kantine": "Kantine",
            "hall": "Hall",
            "auditorium": "Auditorium",
            "musikrum": "Musikrum",
            "idraetshal": "Idrætshall",
            "gym": "Gymnastiksal",
            "køkken": "Køkken",
            "toiletter": "Toiletter",
        }
        
        # Try exact match first
        if original_name.lower() in friendly_mappings:
            return friendly_mappings[original_name.lower()]
        
        # Try partial matches for room names
        lower_name = original_name.lower()
        for key, friendly in friendly_mappings.items():
            if key in lower_name:
                # Replace the key part with friendly name while preserving rest
                return original_name.replace(key, friendly).replace("_", " ").replace("-", " ")
        
        # If no mapping found, capitalize and clean up the name
        # Replace underscores and hyphens with spaces, title case
        # Also remove "processed" from the name
        clean_name = original_name.replace("_", " ").replace("-", " ").replace("processed", "").replace("Processed", "")
        return " ".join(word.capitalize() for word in clean_name.split() if word.strip())

    def _get_compliance_class(self, percentage: float) -> str:
        """Get CSS class for compliance percentage."""
        try:
            # Convert to float if it's a string
            if isinstance(percentage, str):
                percentage = float(percentage)
            elif percentage is None:
                percentage = 0.0
                
            if percentage >= 80:
                return "good"
            elif percentage >= 60:
                return "warning" 
            else:
                return "danger"
        except (ValueError, TypeError):
            # Return neutral if we can't parse the value
            return "neutral"

    def _safe_get_numeric(self, data_dict: Dict[str, Any], key: str, default: float = 0.0) -> float:
        """Safely get a numeric value from a dictionary, converting strings if needed."""
        try:
            value = data_dict.get(key, default)
            if isinstance(value, str):
                return float(value)
            elif isinstance(value, (int, float)):
                return float(value)
            else:
                return default
        except (ValueError, TypeError):
            return default

    def _calculate_ach_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Air Changes per Hour (ACH) using ventilation rate predictor."""
        try:
            # Use the ventilation rate predictor to analyze CO2 decay periods
            results = self.ventilation_predictor.analyze(df)
            
            if not results:
                return {
                    'ach_mean': 0.0,
                    'ach_median': 0.0,
                    'ach_std': 0.0,
                    'ach_min': 0.0,
                    'ach_max': 0.0,
                    'confidence': 'Low',
                    'periods_analyzed': 0,
                    'ventilation_status': 'No data available',
                    'recommendation': 'Unable to assess ventilation rate due to insufficient CO₂ decay periods.'
                }
            
            # Collect valid ACH values
            ach_values = []
            weights = []
            for result in results:
                ach = result.get('ventilation_rate_ach')
                if ach is not None and ach > 0:
                    ach_values.append(ach)
                    weights.append(len(result.get('values', [])))
            
            if not ach_values:
                return {
                    'ach_mean': 0.0,
                    'ach_median': 0.0,
                    'ach_std': 0.0,
                    'ach_min': 0.0,
                    'ach_max': 0.0,
                    'confidence': 'Low',
                    'periods_analyzed': len(results),
                    'ventilation_status': 'Invalid data',
                    'recommendation': 'CO₂ decay periods detected but ventilation rate calculation failed.'
                }
            
            # Calculate weighted statistics
            ach_mean = np.average(ach_values, weights=weights)
            ach_median = np.median(ach_values)
            ach_std = np.sqrt(np.average((np.array(ach_values)-ach_mean)**2, weights=weights))
            ach_min = np.min(ach_values)
            ach_max = np.max(ach_values)
            
            # Calculate confidence
            n_periods = len(ach_values)
            total_points = sum(weights)
            p_periods = min(n_periods / 20, 1.0)
            p_points = min(total_points / 100, 1.0)
            p_std = max(0, 1 - ach_std / 0.05)
            confidence_prob = (0.4*p_periods + 0.4*p_points + 0.2*p_std)
            
            if confidence_prob > 0.85:
                confidence = "High"
            elif confidence_prob > 0.6:
                confidence = "Medium"
            else:
                confidence = "Low"
            
            # Determine ventilation status and recommendation
            recommended_ach = 2.0
            if ach_mean >= recommended_ach:
                status = f"Well ventilated (ACH {ach_mean:.2f} ≥ {recommended_ach})"
                recommendation = f"Ventilation rate is adequate. Mean ACH of {ach_mean:.2f} meets recommended minimum of {recommended_ach}."
            else:
                status = f"Poorly ventilated (ACH {ach_mean:.2f} < {recommended_ach})"
                improvement_needed = recommended_ach - ach_mean
                recommendation = f"Increase ventilation rate by {improvement_needed:.2f} ACH to meet minimum recommendation of {recommended_ach}. Consider improving mechanical ventilation or natural ventilation strategies."
            
            return {
                'ach_mean': round(ach_mean, 3),
                'ach_median': round(ach_median, 3),
                'ach_std': round(ach_std, 3),
                'ach_min': round(ach_min, 3),
                'ach_max': round(ach_max, 3),
                'confidence': confidence,
                'confidence_probability': round(confidence_prob, 2),
                'periods_analyzed': n_periods,
                'total_data_points': total_points,
                'ventilation_status': status,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error calculating ACH analysis: {e}")
            return {
                'ach_mean': 0.0,
                'ach_median': 0.0,
                'ach_std': 0.0,
                'ach_min': 0.0,
                'ach_max': 0.0,
                'confidence': 'Low',
                'periods_analyzed': 0,
                'ventilation_status': 'Error in analysis',
                'recommendation': 'Unable to analyze ventilation rate due to data processing error.'
            }

    def _calculate_solar_shading_recommendation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate solar shading recommendation based on high temperature periods."""
        try:
            if 'temperature' in df.columns:
                temp_data = df['temperature'].dropna()
                
                if temp_data.empty:
                    return {
                        'high_temp_hours': 0,
                        'total_hours': 0,
                        'high_temp_percentage': 0.0,
                        'max_temperature': 0.0,
                        'recommendation': 'No temperature data available for solar shading assessment.',
                        'priority': 'Unknown'
                    }
                
                # Define high temperature thresholds
                comfort_max = 26.0  # °C - upper comfort limit
                critical_temp = 28.0  # °C - critical overheating threshold
                
                total_hours = len(temp_data)
                high_temp_hours = (temp_data > comfort_max).sum()
                critical_temp_hours = (temp_data > critical_temp).sum()
                max_temperature = temp_data.max()
                
                high_temp_percentage = (high_temp_hours / total_hours * 100) if total_hours > 0 else 0
                critical_temp_percentage = (critical_temp_hours / total_hours * 100) if total_hours > 0 else 0
                
                # Generate recommendation based on overheating severity
                if critical_temp_percentage > 5:  # More than 5% of time above 28°C
                    priority = 'High'
                    recommendation = f"High priority: Install external solar shading. {critical_temp_percentage:.1f}% of time above {critical_temp}°C (max: {max_temperature:.1f}°C). External blinds or awnings recommended to reduce solar heat gain."
                elif high_temp_percentage > 10:  # More than 10% of time above 26°C
                    priority = 'Medium'
                    recommendation = f"Medium priority: Consider solar shading. {high_temp_percentage:.1f}% of time above {comfort_max}°C (max: {max_temperature:.1f}°C). Internal blinds or window films may help reduce overheating."
                elif high_temp_percentage > 5:  # More than 5% of time above 26°C
                    priority = 'Low'
                    recommendation = f"Low priority: Monitor temperatures. {high_temp_percentage:.1f}% of time above {comfort_max}°C (max: {max_temperature:.1f}°C). Current overheating is mild but consider shading for hot periods."
                else:
                    priority = 'None'
                    recommendation = f"No solar shading needed. Temperatures well controlled with only {high_temp_percentage:.1f}% of time above {comfort_max}°C (max: {max_temperature:.1f}°C)."
                
                return {
                    'high_temp_hours': int(high_temp_hours),
                    'critical_temp_hours': int(critical_temp_hours),
                    'total_hours': int(total_hours),
                    'high_temp_percentage': round(high_temp_percentage, 1),
                    'critical_temp_percentage': round(critical_temp_percentage, 1),
                    'max_temperature': round(max_temperature, 1),
                    'comfort_threshold': comfort_max,
                    'critical_threshold': critical_temp,
                    'recommendation': recommendation,
                    'priority': priority
                }
            else:
                return {
                    'high_temp_hours': 0,
                    'total_hours': 0,
                    'high_temp_percentage': 0.0,
                    'max_temperature': 0.0,
                    'recommendation': 'No temperature data available for solar shading assessment.',
                    'priority': 'Unknown'
                }
                
        except Exception as e:
            logger.error(f"Error calculating solar shading recommendation: {e}")
            return {
                'high_temp_hours': 0,
                'total_hours': 0,
                'high_temp_percentage': 0.0,
                'max_temperature': 0.0,
                'recommendation': 'Error analyzing temperature data for solar shading assessment.',
                'priority': 'Unknown'
            }

    def _extract_thresholds_from_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract threshold values from config."""
        thresholds = {
            'temp_min': 20,
            'temp_max': 26,
            'temp_critical': 27,
            'temp_optimal_min': 21,
            'temp_optimal_max': 24,
            'co2_standard': 1000,
            'co2_max': 2000
        }
        
        if config and 'analytics' in config:
            analytics = config['analytics']
            
            # Extract temperature thresholds
            if 'temp_below_20_all_year_opening' in analytics:
                thresholds['temp_min'] = analytics['temp_below_20_all_year_opening']['limit']
            if 'temp_above_26_all_year_opening' in analytics:
                thresholds['temp_max'] = analytics['temp_above_26_all_year_opening']['limit']
            if 'temp_above_27_all_year_opening' in analytics:
                thresholds['temp_critical'] = analytics['temp_above_27_all_year_opening']['limit']
            if 'temp_optimal_zone_21_24_all_year_opening' in analytics:
                limits = analytics['temp_optimal_zone_21_24_all_year_opening'].get('limits', {})
                thresholds['temp_optimal_min'] = limits.get('lower', 21)
                thresholds['temp_optimal_max'] = limits.get('upper', 24)
            
            # Extract CO2 thresholds  
            if 'co2_1000_all_year_opening' in analytics:
                thresholds['co2_standard'] = analytics['co2_1000_all_year_opening']['limit']
            # Look for co2_2000 threshold
            for key, value in analytics.items():
                if 'co2' in key and value.get('limit') == 2000:
                    thresholds['co2_max'] = value['limit']
                    break
        
        return thresholds
    
    def _generate_analysis_explanations(self) -> Dict[str, str]:
        """Generate explanations for different analysis logics used in the report."""
        explanations = {
            'ventilation_rate': """
            <h3>🌬️ Ventilationsrate analyse</h3>
            <p>Ventilationsraten beregnes ud fra CO₂-koncentrationen i rummet og estimeret personbelastning.
            Analysen bruger følgende logik:</p>
            <ul>
                <li><strong>Standard grænse (1000 ppm):</strong> Indikerer tilstrækkelig ventilation for normal komfort</li>
                <li><strong>Acceptabel grænse (2000 ppm):</strong> Maximum acceptabelt niveau ifølge danske bygningsregler</li>
                <li><strong>Tidsperioder:</strong> Separat analyse for åbningstid vs. ikke-åbningstid</li>
                <li><strong>Sæsonanalyse:</strong> Vinter/sommer forskelle i ventilationsmønstre</li>
            </ul>
            <p><em>Høje CO₂-værdier indikerer utilstrækkelig ventilation og kan føre til træthed og reduceret koncentration.</em></p>
            """,
            
            'temperature_comfort': """
            <h3>🌡️ Temperaturkomfort analyse</h3>
            <p>Temperaturanalysen evaluerer termisk komfort baseret på DS/EN 16798-1 standarder:</p>
            <ul>
                <li><strong>Underkøling (&lt;20°C):</strong> For lav temperatur, kan føre til ubehag og energispild</li>
                <li><strong>Komfortzone (20-26°C):</strong> Acceptabelt temperaturområde for de fleste aktiviteter</li>
                <li><strong>Optimal zone (21-24°C):</strong> Ideelt temperaturområde for maksimal komfort</li>
                <li><strong>Overophedning (&gt;26°C):</strong> For høj temperatur, reducerer komfort og produktivitet</li>
                <li><strong>Kritisk overophedning (&gt;27°C):</strong> Uacceptabelt højt niveau, kræver øjeblikkelig handling</li>
            </ul>
            <p><em>Analysen tager højde for årstider og åbningstider for mere præcise anbefalinger.</em></p>
            """,
            
            'data_quality': """
            <h3>📊 Datakvalitets analyse</h3>
            <p>Datakvalitetsanalysen sikrer pålideligheden af de præsenterede resultater:</p>
            <ul>
                <li><strong>Tilgængelighed:</strong> Procentdel af forventede datapunkter der er til stede</li>
                <li><strong>Validitet:</strong> Kontrol for urealistiske værdier og målefejl</li>
                <li><strong>Kontinuitet:</strong> Identifikation af huller i datasamlingen</li>
                <li><strong>Kvalitetsscore:</strong> Samlet vurdering af datasættets pålidelighed (0-100%)</li>
            </ul>
            <p><em>Kun data med tilstrækkelig kvalitet inkluderes i compliance-analyserne.</em></p>
            """,
            
            'period_analysis': """
            <h3>📅 Periodeanalyse</h3>
            <p>Analysen opdeler data i forskellige tidsperioder for nuanceret forståelse:</p>
            <ul>
                <li><strong>Åbningstider:</strong> Hverdage 8:00-15:30, ekskluderer skoleferier</li>
                <li><strong>Sæsoner:</strong> Vinter, forår, sommer, efterår baseret på måneder</li>
                <li><strong>Tid på dagen:</strong> Morgen (8-11), eftermiddag (12-15)</li>
                <li><strong>Ferieperioder:</strong> Sommerferie, vinterferie, påskeferie automatisk ekskluderet</li>
            </ul>
            <p><em>Denne opdeling gør det muligt at identificere specifikke problemer og optimeringsmuligheder.</em></p>
            """,
            
            'compliance_scoring': """
            <h3>✅ Compliance scoring</h3>
            <p>Compliance-scoring giver et samlet mål for bygningens præstation:</p>
            <ul>
                <li><strong>Temperatur compliance:</strong> Baseret på tid inden for komfortzone</li>
                <li><strong>CO₂ compliance:</strong> Baseret på ventilationseffektivitet</li>
                <li><strong>Vægtning:</strong> Åbningstimer tæller mere end ikke-åbningstimer</li>
                <li><strong>Sæsonkorrektion:</strong> Justering for sæsonvariationer</li>
            </ul>
            <p><em>Scoring hjælper med at prioritere forbedringsindsatser og sammenligne bygninger.</em></p>
            """
        }
        
        return explanations
    
    def _generate_issues_summary(self, basic_statistics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of specific issues and affected rooms."""
        issues_summary = {
            'overheating_critical': {'rooms': [], 'threshold': '27°C', 'count': 0},
            'overheating_moderate': {'rooms': [], 'threshold': '26°C', 'count': 0},
            'undercooling': {'rooms': [], 'threshold': '20°C', 'count': 0},
            'poor_co2_standard': {'rooms': [], 'threshold': '1000ppm', 'count': 0},
            'poor_co2_critical': {'rooms': [], 'threshold': '2000ppm', 'count': 0},
            'poor_ventilation': {'rooms': [], 'description': 'Utilstrækkelig ventilation', 'count': 0},
            'total_rooms_analyzed': len(basic_statistics)
        }
        
        for room_id, room_stats in basic_statistics.items():
            # Get friendly room name
            room_name = self._get_friendly_name(room_id)
            
            if 'compliance_analysis' not in room_stats:
                continue
                
            compliance = room_stats['compliance_analysis']
            
            # Check opening hours data specifically (most relevant period)
            temp_compliance = compliance.get('temperature_compliance', {})
            co2_compliance = compliance.get('co2_compliance', {})
            
            opening_hours_temp = temp_compliance.get('opening_hours', {})
            opening_hours_co2 = co2_compliance.get('opening_hours', {})
            
            # Critical overheating (>27°C more than 2% of opening hours)
            if opening_hours_temp.get('above_27_percentage', 0) > 2.0:
                issues_summary['overheating_critical']['rooms'].append({
                    'name': room_name,
                    'percentage': round(opening_hours_temp['above_27_percentage'], 1),
                    'hours': opening_hours_temp.get('above_27_hours', 0)
                })
                issues_summary['overheating_critical']['count'] += 1
            
            # Moderate overheating (>26°C more than 10% of opening hours)  
            elif opening_hours_temp.get('above_26_percentage', 0) > 10.0:
                issues_summary['overheating_moderate']['rooms'].append({
                    'name': room_name,
                    'percentage': round(opening_hours_temp['above_26_percentage'], 1),
                    'hours': opening_hours_temp.get('above_26_hours', 0)
                })
                issues_summary['overheating_moderate']['count'] += 1
            
            # Undercooling (<20°C more than 15% of opening hours)
            if opening_hours_temp.get('below_20_percentage', 0) > 15.0:
                issues_summary['undercooling']['rooms'].append({
                    'name': room_name,
                    'percentage': round(opening_hours_temp['below_20_percentage'], 1),
                    'hours': opening_hours_temp.get('below_20_hours', 0)
                })
                issues_summary['undercooling']['count'] += 1
            
            # Poor CO2 standard (<80% below 1000ppm during opening hours)
            if opening_hours_co2.get('below_1000_percentage', 100) < 80.0:
                issues_summary['poor_co2_standard']['rooms'].append({
                    'name': room_name,
                    'percentage': round(opening_hours_co2['below_1000_percentage'], 1),
                    'hours': opening_hours_co2.get('below_1000_hours', 0)
                })
                issues_summary['poor_co2_standard']['count'] += 1
            
            # Critical CO2 levels (<90% below 2000ppm during opening hours)
            if opening_hours_co2.get('below_2000_percentage', 100) < 90.0:
                issues_summary['poor_co2_critical']['rooms'].append({
                    'name': room_name,
                    'percentage': round(opening_hours_co2['below_2000_percentage'], 1),
                    'hours': opening_hours_co2.get('below_2000_hours', 0)
                })
                issues_summary['poor_co2_critical']['count'] += 1
            
            # Poor ventilation (based on ventilation analysis)
            ventilation = room_stats.get('ventilation', {})
            if ventilation.get('ventilation_status') in ['Lav', 'Kritisk lav']:
                issues_summary['poor_ventilation']['rooms'].append({
                    'name': room_name,
                    'status': ventilation.get('ventilation_status', 'Unknown'),
                    'ach': round(ventilation.get('ach_mean', 0), 2)
                })
                issues_summary['poor_ventilation']['count'] += 1
        
        # Sort rooms by severity (highest percentage first)
        for issue_type in ['overheating_critical', 'overheating_moderate', 'undercooling', 'poor_co2_standard', 'poor_co2_critical']:
            issues_summary[issue_type]['rooms'].sort(key=lambda x: x.get('percentage', 0), reverse=True)
        
        # Sort ventilation by ACH (lowest first)
        issues_summary['poor_ventilation']['rooms'].sort(key=lambda x: x.get('ach', 999))
        
        return issues_summary
    
    def _generate_building_summary(self, building_name: str, basic_statistics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate key findings and recommendations summary for a building."""
        building_summary = {
            'key_findings': [],
            'recommendations': [],
            'total_rooms': 0,
            'rooms_with_issues': 0
        }
        
        # Filter statistics for this building
        building_rooms = {}
        for room_id, room_stats in basic_statistics.items():
            room_name = self._get_friendly_name(room_id)
            # Check if room belongs to this building
            if building_name.lower().replace(' ', '_') in room_id.lower():
                building_rooms[room_id] = room_stats
        
        building_summary['total_rooms'] = len(building_rooms)
        
        if not building_rooms:
            return building_summary
        
        # Analyze aggregated findings
        temp_issues = []
        co2_issues = []
        ventilation_issues = []
        
        for room_id, room_stats in building_rooms.items():
            room_name = self._get_friendly_name(room_id)
            
            if 'compliance_analysis' not in room_stats:
                continue
            
            compliance = room_stats['compliance_analysis']
            temp_compliance = compliance.get('temperature_compliance', {})
            co2_compliance = compliance.get('co2_compliance', {})
            
            # Check opening hours specifically
            opening_hours_temp = temp_compliance.get('opening_hours', {})
            opening_hours_co2 = co2_compliance.get('opening_hours', {})
            
            has_issues = False
            
            # Temperature issues
            if opening_hours_temp.get('above_27_percentage', 0) > 2.0:
                temp_issues.append(f"{room_name} ({opening_hours_temp['above_27_percentage']:.1f}% over 27°C)")
                has_issues = True
            elif opening_hours_temp.get('above_26_percentage', 0) > 10.0:
                temp_issues.append(f"{room_name} ({opening_hours_temp['above_26_percentage']:.1f}% over 26°C)")
                has_issues = True
            elif opening_hours_temp.get('below_20_percentage', 0) > 15.0:
                temp_issues.append(f"{room_name} ({opening_hours_temp['below_20_percentage']:.1f}% under 20°C)")
                has_issues = True
            
            # CO2 issues
            if opening_hours_co2.get('below_1000_percentage', 100) < 80.0:
                co2_issues.append(f"{room_name} ({opening_hours_co2['below_1000_percentage']:.1f}% under 1000ppm)")
                has_issues = True
            
            # Ventilation issues
            ventilation = room_stats.get('ventilation', {})
            if ventilation.get('ventilation_status') in ['Lav', 'Kritisk lav']:
                ventilation_issues.append(f"{room_name} ({ventilation.get('ach_mean', 0):.2f} ACH)")
                has_issues = True
            
            if has_issues:
                building_summary['rooms_with_issues'] += 1
        
        # Generate key findings
        if temp_issues:
            if len(temp_issues) > 5:
                building_summary['key_findings'].append(f"Temperaturproblemer i {len(temp_issues)} rum - se detaljeret analyse")
            else:
                building_summary['key_findings'].append(f"Temperaturproblemer: {', '.join(temp_issues[:3])}")
        
        if co2_issues:
            if len(co2_issues) > 5:
                building_summary['key_findings'].append(f"CO₂-problemer i {len(co2_issues)} rum - utilstrækkelig ventilation")
            else:
                building_summary['key_findings'].append(f"CO₂-problemer: {', '.join(co2_issues[:3])}")
        
        if ventilation_issues:
            if len(ventilation_issues) > 5:
                building_summary['key_findings'].append(f"Lav ventilation i {len(ventilation_issues)} rum")
            else:
                building_summary['key_findings'].append(f"Lav ventilation: {', '.join(ventilation_issues[:3])}")
        
        if not temp_issues and not co2_issues and not ventilation_issues:
            building_summary['key_findings'].append("Ingen kritiske problemer identificeret - bygningen overholder de grundlæggende krav")
        
        # Generate recommendations based on issues
        if temp_issues:
            if any('over 27°C' in issue for issue in temp_issues):
                building_summary['recommendations'].append("Høj prioritet: Installer solafskærmning og forbedre køling i overophedede rum")
            elif any('over 26°C' in issue for issue in temp_issues):
                building_summary['recommendations'].append("Medium prioritet: Overvej solafskærmning og ventilationsoptimering")
            if any('under 20°C' in issue for issue in temp_issues):
                building_summary['recommendations'].append("Juster varmeregulering for at undgå energispild og komfortproblemer")
        
        if co2_issues or ventilation_issues:
            building_summary['recommendations'].append("Optimer ventilationssystem og kontroller luftskiftefrekvens")
            building_summary['recommendations'].append("Overvej behovsstyret ventilation for bedre energieffektivitet")
        
        if len(building_summary['recommendations']) == 0:
            building_summary['recommendations'].append("Fortsæt med den nuværende drift og overvågning")
            building_summary['recommendations'].append("Regelmæssig kalibrering af sensorer anbefales")
        
        return building_summary
    
    def _calculate_building_metrics(self, building_name: str, basic_statistics: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregated building-level metrics from room statistics."""
        metrics = {
            'co2_1000_compliance': 0.0,
            'co2_2000_compliance': 0.0,
            'temp_compliance': 0.0,
            'total_rooms': 0
        }
        
        # Filter statistics for this building
        building_rooms = {}
        for room_id, room_stats in basic_statistics.items():
            # Check if room belongs to this building
            if building_name.lower().replace(' ', '_') in room_id.lower():
                building_rooms[room_id] = room_stats
        
        if not building_rooms:
            return metrics
        
        metrics['total_rooms'] = len(building_rooms)
        
        # Aggregate compliance data from opening hours (most relevant period)
        co2_1000_total = 0
        co2_2000_total = 0
        temp_compliance_total = 0
        valid_rooms = 0
        
        for room_id, room_stats in building_rooms.items():
            if 'compliance_analysis' not in room_stats:
                continue
                
            compliance = room_stats['compliance_analysis']
            temp_compliance = compliance.get('temperature_compliance', {})
            co2_compliance = compliance.get('co2_compliance', {})
            
            # Use opening hours data for most relevant metrics
            opening_hours_temp = temp_compliance.get('opening_hours', {})
            opening_hours_co2 = co2_compliance.get('opening_hours', {})
            
            if opening_hours_co2:
                co2_1000_total += float(opening_hours_co2.get('below_1000_percentage', 0))
                co2_2000_total += float(opening_hours_co2.get('below_2000_percentage', 0))
                
            if opening_hours_temp:
                # Calculate temperature compliance as comfort zone percentage
                temp_compliance_total += float(opening_hours_temp.get('comfort_zone_20_26_percentage', 0))
                
            valid_rooms += 1
        
        # Calculate averages
        if valid_rooms > 0:
            metrics['co2_1000_compliance'] = round(co2_1000_total / valid_rooms, 1)
            metrics['co2_2000_compliance'] = round(co2_2000_total / valid_rooms, 1) 
            metrics['temp_compliance'] = round(temp_compliance_total / valid_rooms, 1)
            # Add legacy key for overall metrics calculation
            metrics['co2_compliance'] = metrics['co2_2000_compliance']  # Use 2000ppm as primary CO2 metric
        
        return metrics
    
    def _calculate_detailed_compliance(self, df: pd.DataFrame, room_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate detailed compliance analysis with separated temperature and CO2 thresholds and period analysis."""
        try:
            # Extract thresholds from config
            thresholds = self._extract_thresholds_from_config(config)
            
            # Define analysis periods
            periods = self._define_analysis_periods(df, room_id)
            
            # Initialize results structure
            compliance_results = {
                'period_analysis': periods,
                'temperature_compliance': {},
                'co2_compliance': {},
                'summary': {}
            }
            
            # Analyze each period
            for period_name, period_data in periods.items():
                if period_data['data'].empty:
                    continue
                    
                period_df = period_data['data']
                
                # Temperature compliance analysis with multiple thresholds
                temp_compliance = self._analyze_temperature_compliance(period_df, thresholds)
                compliance_results['temperature_compliance'][period_name] = temp_compliance
                
                # CO2 compliance analysis with separate thresholds
                co2_compliance = self._analyze_co2_compliance(period_df, thresholds)
                compliance_results['co2_compliance'][period_name] = co2_compliance
            
            # Generate overall summary
            compliance_results['summary'] = self._generate_compliance_summary(compliance_results)
            
            return compliance_results
            
        except Exception as e:
            logger.error(f"Error calculating detailed compliance for {room_id}: {e}")
            return {
                'period_analysis': {},
                'temperature_compliance': {},
                'co2_compliance': {},
                'summary': {'error': f'Analysis failed: {str(e)}'}
            }

    def _define_analysis_periods(self, df: pd.DataFrame, room_id: str) -> Dict[str, Dict[str, Any]]:
        """Define and extract different analysis periods from the data."""
        periods = {}
        
        if df.empty or not hasattr(df.index, 'hour'):
            return periods
        
        try:
            # Ensure index is datetime
            if not isinstance(df.index, pd.DatetimeIndex):
                try:
                    df.index = pd.to_datetime(df.index)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not convert index to datetime for room {room_id}: {e}")
                    return periods
            
            # Add time-based columns for filtering
            df_copy = df.copy()
            try:
                # Try to access hour attribute first to verify it's a DatetimeIndex
                if hasattr(df_copy.index, 'hour'):
                    df_copy['hour'] = df_copy.index.hour
                    df_copy['weekday'] = df_copy.index.weekday  # 0=Monday, 6=Sunday
                    df_copy['month'] = df_copy.index.month
                else:
                    # Try to convert to DatetimeIndex if not already
                    df_copy.index = pd.to_datetime(df_copy.index)
                    df_copy['hour'] = df_copy.index.hour
                    df_copy['weekday'] = df_copy.index.weekday  # 0=Monday, 6=Sunday
                    df_copy['month'] = df_copy.index.month
            except (AttributeError, TypeError, ValueError) as e:
                logger.warning(f"Could not extract datetime components for room {room_id}: {e}")
                return periods
            
            # Define periods
            # Opening hours (8:00-17:00, Monday-Friday, excluding summer holidays)
            opening_hours_mask = (
                (df_copy['hour'] >= 8) & (df_copy['hour'] < 17) &
                (df_copy['weekday'] < 5) &  # Monday to Friday
                ~((df_copy['month'] >= 7) & (df_copy['month'] <= 8))  # Exclude July-August
            )
            
            # Non-opening hours (evenings, nights, weekends)
            non_opening_mask = ~opening_hours_mask
            
            # Summer period (July-August)
            summer_mask = (df_copy['month'] >= 7) & (df_copy['month'] <= 8)
            
            # Winter period (December-February)
            winter_mask = (df_copy['month'].isin([12, 1, 2]))
            
            # All data
            periods['all_data'] = {
                'data': df_copy,
                'description': 'Hele perioden - alle data',
                'total_hours': len(df_copy)
            }
            
            periods['opening_hours'] = {
                'data': df_copy[opening_hours_mask],
                'description': 'Åbningstid (8-17, man-fre, ekskl. sommerferie)',
                'total_hours': opening_hours_mask.sum()
            }
            
            periods['non_opening_hours'] = {
                'data': df_copy[non_opening_mask],
                'description': 'Uden for åbningstid (aftener, nætter, weekender)',
                'total_hours': non_opening_mask.sum()
            }
            
            periods['summer_holidays'] = {
                'data': df_copy[summer_mask],
                'description': 'Sommerferie (juli-august)',
                'total_hours': summer_mask.sum()
            }
            
            periods['winter_period'] = {
                'data': df_copy[winter_mask],
                'description': 'Vinterperiode (december-februar)',
                'total_hours': winter_mask.sum()
            }
            
            return periods
            
        except Exception as e:
            logger.error(f"Error defining analysis periods: {e}")
            return periods

    def _analyze_temperature_compliance(self, df: pd.DataFrame, thresholds: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze temperature compliance with multiple thresholds."""
        if thresholds is None:
            thresholds = {'temp_min': 20, 'temp_max': 26, 'temp_critical': 27, 'temp_optimal_min': 21, 'temp_optimal_max': 24}
            
        if 'temperature' not in df.columns or df['temperature'].dropna().empty:
            return {
                'total_hours': 0,
                'below_20_hours': 0, 'below_20_percentage': 0.0,
                'above_26_hours': 0, 'above_26_percentage': 0.0,
                'above_27_hours': 0, 'above_27_percentage': 0.0,
                'comfort_zone_20_26_hours': 0, 'comfort_zone_20_26_percentage': 0.0,
                'optimal_zone_21_24_hours': 0, 'optimal_zone_21_24_percentage': 0.0,
                'mean_temperature': 0.0, 'max_temperature': 0.0, 'min_temperature': 0.0
            }
        
        temp_data = df['temperature'].dropna()
        total_hours = len(temp_data)
        
        if total_hours == 0:
            return {
                'total_hours': 0,
                'below_20_hours': 0, 'below_20_percentage': 0.0,
                'above_26_hours': 0, 'above_26_percentage': 0.0,
                'above_27_hours': 0, 'above_27_percentage': 0.0,
                'comfort_zone_20_26_hours': 0, 'comfort_zone_20_26_percentage': 0.0,
                'optimal_zone_21_24_hours': 0, 'optimal_zone_21_24_percentage': 0.0,
                'mean_temperature': 0.0, 'max_temperature': 0.0, 'min_temperature': 0.0
            }
        
        # Calculate different temperature thresholds using config values
        temp_min = thresholds['temp_min']
        temp_max = thresholds['temp_max']
        temp_critical = thresholds['temp_critical']
        temp_opt_min = thresholds['temp_optimal_min']
        temp_opt_max = thresholds['temp_optimal_max']
        
        below_min = (temp_data < temp_min).sum()
        above_max = (temp_data > temp_max).sum()
        above_critical = (temp_data > temp_critical).sum()
        comfort_zone = ((temp_data >= temp_min) & (temp_data <= temp_max)).sum()
        optimal_zone = ((temp_data >= temp_opt_min) & (temp_data <= temp_opt_max)).sum()
        
        return {
            'total_hours': total_hours,
            'below_20_hours': int(below_min),
            'below_20_percentage': round((below_min / total_hours) * 100, 1),
            'above_26_hours': int(above_max),
            'above_26_percentage': round((above_max / total_hours) * 100, 1),
            'above_27_hours': int(above_critical),
            'above_27_percentage': round((above_critical / total_hours) * 100, 1),
            'comfort_zone_20_26_hours': int(comfort_zone),
            'comfort_zone_20_26_percentage': round((comfort_zone / total_hours) * 100, 1),
            'optimal_zone_21_24_hours': int(optimal_zone),
            'optimal_zone_21_24_percentage': round((optimal_zone / total_hours) * 100, 1),
            'mean_temperature': round(temp_data.mean(), 1),
            'max_temperature': round(temp_data.max(), 1),
            'min_temperature': round(temp_data.min(), 1)
        }

    def _analyze_co2_compliance(self, df: pd.DataFrame, thresholds: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze CO2 compliance with separate 1000ppm and 2000ppm thresholds."""
        if thresholds is None:
            thresholds = {'co2_standard': 1000, 'co2_max': 2000}
        if 'co2' not in df.columns or df['co2'].dropna().empty:
            return {
                'total_hours': 0,
                'below_1000_hours': 0, 'below_1000_percentage': 0.0,
                'below_2000_hours': 0, 'below_2000_percentage': 0.0,
                'above_1000_hours': 0, 'above_1000_percentage': 0.0,
                'above_2000_hours': 0, 'above_2000_percentage': 0.0,
                'between_1000_2000_hours': 0, 'between_1000_2000_percentage': 0.0,
                'mean_co2': 0.0, 'max_co2': 0.0, 'min_co2': 0.0
            }
        
        co2_data = df['co2'].dropna()
        total_hours = len(co2_data)
        
        if total_hours == 0:
            return {
                'total_hours': 0,
                'below_1000_hours': 0, 'below_1000_percentage': 0.0,
                'below_2000_hours': 0, 'below_2000_percentage': 0.0,
                'above_1000_hours': 0, 'above_1000_percentage': 0.0,
                'above_2000_hours': 0, 'above_2000_percentage': 0.0,
                'between_1000_2000_hours': 0, 'between_1000_2000_percentage': 0.0,
                'mean_co2': 0.0, 'max_co2': 0.0, 'min_co2': 0.0
            }
        
        # Calculate CO2 threshold compliance using configurable thresholds
        co2_standard = thresholds['co2_standard']  # Default 1000ppm
        co2_acceptable = thresholds['co2_max']  # Default 2000ppm
        
        below_standard = (co2_data < co2_standard).sum()
        below_acceptable = (co2_data < co2_acceptable).sum()
        above_standard = (co2_data >= co2_standard).sum()
        above_acceptable = (co2_data >= co2_acceptable).sum()
        between_standard_acceptable = ((co2_data >= co2_standard) & (co2_data < co2_acceptable)).sum()
        
        return {
            'total_hours': total_hours,
            'below_1000_hours': int(below_standard),
            'below_1000_percentage': round((below_standard / total_hours) * 100, 1),
            'below_2000_hours': int(below_acceptable),
            'below_2000_percentage': round((below_acceptable / total_hours) * 100, 1),
            'above_1000_hours': int(above_standard),
            'above_1000_percentage': round((above_standard / total_hours) * 100, 1),
            'above_2000_hours': int(above_acceptable),
            'above_2000_percentage': round((above_acceptable / total_hours) * 100, 1),
            'between_1000_2000_hours': int(between_standard_acceptable),
            'between_1000_2000_percentage': round((between_standard_acceptable / total_hours) * 100, 1),
            'mean_co2': round(co2_data.mean(), 0),
            'max_co2': round(co2_data.max(), 0),
            'min_co2': round(co2_data.min(), 0)
        }

    def _generate_compliance_summary(self, compliance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of compliance analysis across all periods."""
        summary = {
            'periods_analyzed': list(compliance_results.get('temperature_compliance', {}).keys()),
            'key_findings': [],
            'recommendations': []
        }
        
        # Analyze opening hours specifically (most important period)
        opening_hours_temp = compliance_results.get('temperature_compliance', {}).get('opening_hours', {})
        opening_hours_co2 = compliance_results.get('co2_compliance', {}).get('opening_hours', {})
        
        if opening_hours_temp and opening_hours_co2:
            # Temperature findings
            if opening_hours_temp.get('above_27_percentage', 0) > 5:
                summary['key_findings'].append(f"Kritisk overophedning: {opening_hours_temp['above_27_percentage']}% af åbningstid over 27°C")
                summary['recommendations'].append("Høj prioritet: Installer solafskærmning og forbedre køling")
            elif opening_hours_temp.get('above_26_percentage', 0) > 10:
                summary['key_findings'].append(f"Overophedning: {opening_hours_temp['above_26_percentage']}% af åbningstid over 26°C")
                summary['recommendations'].append("Medium prioritet: Overvej solafskærmning")
            
            if opening_hours_temp.get('below_20_percentage', 0) > 10:
                summary['key_findings'].append(f"Underkøling: {opening_hours_temp['below_20_percentage']}% af åbningstid under 20°C")
                summary['recommendations'].append("Forbedre opvarmning i koldere perioder")
            
            # CO2 findings
            if opening_hours_co2.get('above_2000_percentage', 0) > 1:
                summary['key_findings'].append(f"Kritisk luftkvalitet: {opening_hours_co2['above_2000_percentage']}% af åbningstid over 2000ppm CO₂")
                summary['recommendations'].append("Akut: Øg ventilation kraftigt")
            elif opening_hours_co2.get('above_1000_percentage', 0) > 20:
                summary['key_findings'].append(f"Dårlig luftkvalitet: {opening_hours_co2['above_1000_percentage']}% af åbningstid over 1000ppm CO₂")
                summary['recommendations'].append("Øg ventilationsrate eller forbedre ventilationsstyring")
        
        return summary

    def _add_friendly_names_to_data_quality(self, data_quality: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add friendly names to data quality entries."""
        updated_data_quality = []
        for item in data_quality:
            updated_item = item.copy()
            updated_item["friendly_name"] = self._get_friendly_name(item["name"])
            updated_data_quality.append(updated_item)
        return updated_data_quality

    def _prepare_overall_metrics(self, overall_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare overall metrics with separated CO2 compliance."""
        # Extract existing CO2 compliance or create defaults
        co2_compliance = overall_metrics.get("co2_compliance", {"value": 0, "class": "neutral"})
        co2_value = self._safe_get_numeric(co2_compliance, "value", 0) if isinstance(co2_compliance, dict) else self._safe_get_numeric({"value": co2_compliance}, "value", 0)
        
        # Create separated CO2 metrics (these would be calculated from actual data)
        prepared_metrics = overall_metrics.copy()
        
        co2_1000_value = self._safe_get_numeric(overall_metrics, "co2_1000_compliance", int(co2_value * 0.7))
        co2_2000_value = self._safe_get_numeric(overall_metrics, "co2_2000_compliance", co2_value)
        
        prepared_metrics.update({
            "co2_compliance_1000": {
                "value": co2_1000_value,
                "class": self._get_compliance_class(co2_1000_value)
            },
            "co2_compliance_2000": {
                "value": co2_2000_value,
                "class": self._get_compliance_class(co2_2000_value)
            }
        })
        
        return prepared_metrics

    def _convert_to_relative_paths(self, chart_paths: Dict[str, str]) -> Dict[str, str]:
        """Convert absolute chart paths to relative paths for HTML templates."""
        relative_paths = {}
        for key, path in chart_paths.items():
            if path and os.path.exists(path):
                # Extract just the filename from the path
                filename = os.path.basename(path)
                # Make it relative to the HTML file (which is in the same directory as charts/)
                relative_paths[key] = f"./charts/{filename}"
            else:
                relative_paths[key] = ""
        return relative_paths
    
    def _prepare_template_context(self, report_data: Dict[str, Any], chart_paths: Dict[str, str], mapped_data: Optional[Dict[str, pd.DataFrame]] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare the context for the Jinja2 template."""
        
        # Convert absolute chart paths to relative paths for HTML
        relative_chart_paths = self._convert_to_relative_paths(chart_paths)
        
        # Calculate basic statistics from mapped data
        basic_statistics = {}
        if mapped_data:
            basic_statistics = self._calculate_basic_statistics(mapped_data, config)
        
        # Organize charts by building
        buildings_with_charts = []
        for building in report_data["buildings"]:
            building_id = building["name"].lower().replace(" ", "_")
            
            # Add friendly name
            building_friendly_name = self._get_friendly_name(building["name"])
            
            # Create charts object for this building
            building_charts = {
                "top_issues": relative_chart_paths.get(f'top_issues_{building_id}', ''),
                "non_compliant_opening": relative_chart_paths.get(f'non_compliant_opening_{building_id}', ''),
                "non_compliant_non_opening": relative_chart_paths.get(f'non_compliant_non_opening_{building_id}', ''),
                "seasonal_patterns": relative_chart_paths.get(f'seasonal_patterns_{building_id}', ''),
                "daily_patterns": relative_chart_paths.get(f'daily_patterns_{building_id}', ''),
                "monthly_analysis": relative_chart_paths.get(f'monthly_analysis_{building_id}', ''),
                "improvement_potential": relative_chart_paths.get(f'improvement_potential_{building_id}', ''),
                "cost_benefit": relative_chart_paths.get(f'cost_benefit_{building_id}', ''),
                "room_compliance_comparison": relative_chart_paths.get(f'room_compliance_comparison_{building_id}', ''),
                # Climate correlation charts
                "climate_correlation_heatmap": relative_chart_paths.get(f'climate_correlation_heatmap_{building_id}', ''),
                "solar_sensitivity": relative_chart_paths.get(f'solar_sensitivity_{building_id}', ''),
                "seasonal_climate_correlation": relative_chart_paths.get(f'seasonal_climate_correlation_{building_id}', '')
            }
            
            # Add charts to rooms with basic statistics
            rooms_with_charts = []
            for room in building["rooms"]:
                room_id = f"{building_id}_{room['name'].lower().replace(' ', '_')}"
                full_room_id = f"{building_id}_{room['name']}"
                
                # Add friendly name for room
                room_friendly_name = self._get_friendly_name(room["name"])
                
                # Create charts object for this room
                room_charts = {
                    "yearly_trends": relative_chart_paths.get(f'yearly_trends_{room_id}', ''),
                    "seasonal_patterns": relative_chart_paths.get(f'seasonal_patterns_{room_id}', ''),
                    "daily_distribution": relative_chart_paths.get(f'daily_distribution_{room_id}', ''),
                    "temperature_heatmap": relative_chart_paths.get(f'temperature_heatmap_{room_id}', ''),
                    "co2_heatmap": relative_chart_paths.get(f'co2_heatmap_{room_id}', '')
                }
                
                # Add charts and basic statistics to room data
                room_with_charts = room.copy()
                room_with_charts["charts"] = room_charts
                room_with_charts["friendly_name"] = room_friendly_name
                
                # Add separated CO2 compliance metrics
                room_with_charts["co2_1000_compliance"] = self._safe_get_numeric(room, "co2_1000_compliance", room.get("co2_performance", {}).get("value", 0))
                room_with_charts["co2_2000_compliance"] = self._safe_get_numeric(room, "co2_2000_compliance", 0)
                room_with_charts["co2_1000_class"] = self._get_compliance_class(room_with_charts["co2_1000_compliance"])
                room_with_charts["co2_2000_class"] = self._get_compliance_class(room_with_charts["co2_2000_compliance"])
                room_with_charts["temp_class"] = room.get("temp_performance", {}).get("class", "neutral")
                
                # Add room summary data (to be filled by analytics)
                room_with_charts.update({
                    "solar_shading": {"need": "Anbefales", "priority_class": "warning"},
                    "estimated_ach": "3.5",
                    "ventilation_need": "Øget ventilation nødvendig",
                    "critical_period": {"time": "13:00-15:00", "season": "Sommer"}
                })
                
                # Add basic statistics if available
                room_found = False
                # Try multiple room ID patterns for matching
                room_name_clean = room['name'].replace('_processed', '')
                possible_room_ids = [
                    full_room_id,
                    room['name'],
                    room_name_clean,
                    f"{building['name']}_{room['name']}",
                    f"{building['name']}_{room_name_clean}",
                    f"{building_id}_{room['name']}",
                    f"{building_id}_{room_name_clean}",
                    f"{building['name'].lower()}_{room['name'].lower()}",
                    f"{building['name'].lower()}_{room_name_clean.lower()}",
                    f"{building_id}_{room['name'].lower()}",
                    f"{building_id}_{room_name_clean.lower()}",
                ]
                
                if len(basic_statistics) > 0:
                    logger.debug(f"Looking for room statistics for '{room['name']}' with patterns: {possible_room_ids[:3]}...")
                    logger.debug(f"First few available statistics keys: {list(basic_statistics.keys())[:5]}")
                
                for room_id_attempt in possible_room_ids:
                    if room_id_attempt in basic_statistics:
                        room_with_charts["basic_statistics"] = basic_statistics[room_id_attempt]
                        logger.info(f"Found statistics for room {room['name']} using ID: {room_id_attempt}")
                        room_found = True
                        break
                
                if not room_found and len(basic_statistics) > 0:
                    logger.warning(f"No statistics found for room {room['name']} in building {building['name']}")
                
                rooms_with_charts.append(room_with_charts)
            
            # Add charts to building data
            building_with_charts = building.copy()
            building_with_charts["charts"] = building_charts
            building_with_charts["friendly_name"] = building_friendly_name
            building_with_charts["rooms"] = rooms_with_charts
            
            # Calculate proper building-level metrics from room statistics
            building_metrics = self._calculate_building_metrics(building["name"], basic_statistics)
            
            building_with_charts["co2_compliance_1000"] = {
                "value": building_metrics.get("co2_1000_compliance", 0), 
                "class": "neutral"
            }
            building_with_charts["co2_compliance_2000"] = {
                "value": building_metrics.get("co2_2000_compliance", 0), 
                "class": "neutral"
            }
            building_with_charts["temp_performance"] = {
                "value": building_metrics.get("temp_compliance", 0),
                "class": "neutral"
            }
            building_with_charts["co2_compliance_1000"]["class"] = self._get_compliance_class(building_with_charts["co2_compliance_1000"]["value"])
            building_with_charts["co2_compliance_2000"]["class"] = self._get_compliance_class(building_with_charts["co2_compliance_2000"]["value"])
            building_with_charts["temp_performance"]["class"] = self._get_compliance_class(building_with_charts["temp_performance"]["value"])
            
            # Add building-level basic statistics (aggregate from rooms)
            if rooms_with_charts:
                building_with_charts["basic_statistics"] = self._aggregate_building_statistics(rooms_with_charts)
            
            # Add building summary with key findings and recommendations
            building_with_charts["summary"] = self._generate_building_summary(building["name"], basic_statistics)
            
            buildings_with_charts.append(building_with_charts)
        
        context = {
            "report_title": "Indeklima vurdering",
            "generation_date": datetime.now().strftime("%d. %B %Y"),
            "analysis_period": "2024",
            "building_count": len(report_data["buildings"]),
            "author": "Bruno Adam",
            "include_toc": True,
            "template_version": "1.0.0",
            
            # Data from report preparation with charts
            "buildings": buildings_with_charts,
            "data_quality": self._add_friendly_names_to_data_quality(report_data["data_quality"]),
            "charts": {
                "building_comparison": relative_chart_paths.get('building_comparison', ''),
                "data_completeness": relative_chart_paths.get('data_completeness', ''),
                "monthly_trends": relative_chart_paths.get('monthly_trends', ''),
                "priority_matrix": relative_chart_paths.get('priority_matrix', '')
            },
            
            # Overall metrics with separated CO2 compliance
            **self._prepare_overall_metrics(report_data["overall_metrics"]),
            
            # Recommendations
            "high_priority_recommendations": [
                r for r in report_data["recommendations"] 
                if r.get("priority") == "high"
            ],
            "implementation_phases": self._create_implementation_phases(report_data["recommendations"]),
            
            # Summary text
            "executive_summary_text": self._generate_executive_summary_text(report_data),
            
            # Analysis explanations  
            "analysis_explanations": self._generate_analysis_explanations(),
            
            # Issues summary with affected rooms
            "issues_summary": self._generate_issues_summary(basic_statistics) if basic_statistics else {}
        }
        
        return context
    
    def _create_implementation_phases(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create implementation phases from recommendations."""
        phases = [
            {
                "name": "Fase 1: Akutte forbedringer",
                "timeframe": "0-3 måneder",
                "description": "Hurtige justeringer og reparationer",
                "cost": "100,000"
            },
            {
                "name": "Fase 2: Systemoptimering",
                "timeframe": "3-12 måneder", 
                "description": "Optimering af HVAC-systemer og kontrolstrategier",
                "cost": "300,000"
            },
            {
                "name": "Fase 3: Systemopgraderinger",
                "timeframe": "1-2 år",
                "description": "Større systemopgraderinger og udskiftninger",
                "cost": "750,000"
            }
        ]
        
        return phases
    
    def _generate_executive_summary_text(self, report_data: Dict[str, Any]) -> str:
        """Generate executive summary text."""
        building_count = len(report_data["buildings"])
        
        summary = f"""
        Denne rapport analyserer indendørs miljøkvalitet i {building_count} bygninger 
        i Høje-Taastrup Kommune. Analysen omfatter temperatur- og CO₂-målinger gennem 
        hele året, med fokus på både åbningstider og perioder uden for åbningstid.
        
        Rapporten identificerer rum med flest problemer og giver konkrete anbefalinger 
        til forbedringer baseret på etablerede standarder og best practices.
        """
        
        return summary.strip()
    
    def _generate_html_report(self, context: Dict[str, Any], output_dir: Path) -> str:
        """Generate HTML report."""
        template_content = self.load_html_template()
        template = Template(template_content)
        
        # Add custom filters
        template.environment.filters['basename'] = lambda path: os.path.basename(path) if path else ""
        
        html_content = template.render(**context)
        
        html_file = output_dir / "htk_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(html_file)
    
    def _convert_csv_row_to_room_data(self, row: pd.Series) -> Dict[str, Any]:
        """Convert a CSV row to room data structure."""
        room_data = {
            'test_results': {},
            'statistics': {
                'co2': {'mean': 0, 'std': 0, 'min': 0, 'max': 0},
                'temperature': {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
            }
        }
        
        # Map CSV columns to test results
        test_mappings = {
            'co2_1000_all_year_opening': 'rule_co2_1000_all_year_opening',
            'co2_1000_all_year_non_opening': 'rule_co2_1000_all_year_non_opening',
            'temp_comfort_all_year_opening': 'rule_temp_comfort_all_year_opening',
            'temp_comfort_all_year_non_opening': 'rule_temp_comfort_all_year_non_opening',
            'co2_1000_spring_opening': 'rule_co2_1000_spring_opening',
            'co2_1000_summer_opening': 'rule_co2_1000_summer_opening',
            'co2_1000_autumn_opening': 'rule_co2_1000_autumn_opening',
            'co2_1000_winter_opening': 'rule_co2_1000_winter_opening',
            'temp_comfort_spring_opening': 'rule_temp_comfort_spring_opening',
            'temp_comfort_summer_opening': 'rule_temp_comfort_summer_opening',
            'temp_comfort_autumn_opening': 'rule_temp_comfort_autumn_opening',
            'temp_comfort_winter_opening': 'rule_temp_comfort_winter_opening',
            # Daily period mappings
            'co2_1000_morning': 'rule_co2_1000_morning',
            'co2_1000_afternoon': 'rule_co2_1000_afternoon',
            'co2_1000_evening': 'rule_co2_1000_evening',
            'temp_summer_limit_morning': 'rule_temp_summer_limit_morning',
            'temp_summer_limit_afternoon': 'rule_temp_summer_limit_afternoon',
            'temp_summer_limit_evening': 'rule_temp_summer_limit_evening'
        }
        
        # Extract test results from CSV columns
        for test_name, csv_prefix in test_mappings.items():
            compliance_col = f"{csv_prefix}_compliance_rate"
            non_compliant_col = f"{csv_prefix}_non_compliant_hours"
            total_col = f"{csv_prefix}_total_hours"
            
            if compliance_col in row and pd.notna(row[compliance_col]):
                room_data['test_results'][test_name] = {
                    'compliance_rate': float(row[compliance_col]),  # Keep as percentage (0-100)
                    'violations_count': int(row.get(non_compliant_col, 0)) if pd.notna(row.get(non_compliant_col, 0)) else 0,
                    'total_hours': int(row.get(total_col, 0)) if pd.notna(row.get(total_col, 0)) else 0,
                    'mean': 0  # Not available in CSV, using placeholder
                }
        
        return room_data
    
    def _calculate_building_data_quality(self, rooms: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate building-level data quality from room data."""
        if not rooms:
            return {
                'completeness': 0,
                'missing_periods': "No data",
                'quality_score': "Low"
            }

        # Extract completeness values from room data_quality
        completeness_values = []
        for room in rooms.values():
            if 'data_quality' in room and 'completeness' in room['data_quality']:
                completeness_values.append(room['data_quality']['completeness'])
            elif 'completeness' in room:  # Fallback for rooms with direct completeness field
                completeness_values.append(room['completeness'])
        
        if not completeness_values:
            return {
                'completeness': 0,
                'missing_periods': "No data",
                'quality_score': "Low"
            }
            
        avg_completeness = sum(completeness_values) / len(completeness_values)

        return {
            'completeness': round(avg_completeness, 1),
            'missing_periods': "Minimal gaps" if avg_completeness > 95 else "Some gaps",
            'quality_score': "High" if avg_completeness > 95 else ("Medium" if avg_completeness > 85 else "Low")
        }
    
    def _generate_pdf_report(self, context: Dict[str, Any], output_dir: Path) -> str:
        """Generate PDF report from HTML."""
        # Generate HTML first
        html_file = self._generate_html_report(context, output_dir)
        pdf_file = output_dir / "htk_report.pdf"
        
        # Try multiple PDF generation methods
        
        # Method 1: Try weasyprint with proper error handling
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            # Configure fonts for proper Unicode support
            font_config = FontConfiguration()
            
            # Create CSS for print media
            print_css = CSS(string='''
                @page {
                    size: A4 portrait;
                    margin: 2cm;
                    @bottom-center {
                        content: counter(page) " / " counter(pages);
                        font-size: 10pt;
                        color: #666;
                    }
                    @top-right {
                        content: "HTK Indeklima Rapport";
                        font-size: 9pt;
                        color: #666;
                    }
                }
                
                /* Page structure */
                .page {
                    page-break-before: always;
                    page-break-after: always;
                    min-height: 80vh;
                }
                
                .page:first-child {
                    page-break-before: auto;
                }
                
                .page:last-child {
                    page-break-after: auto;
                }
                
                .page-header {
                    border-bottom: 2px solid #0066cc;
                    padding-bottom: 15px;
                    margin-bottom: 30px;
                    page-break-after: avoid;
                }
                
                .page-header h1 {
                    color: #0066cc;
                    font-size: 16pt;
                    margin: 0;
                    page-break-after: avoid;
                }
                
                .page-header .page-subtitle {
                    color: #666;
                    font-size: 11pt;
                    margin: 5px 0 0 0;
                }
                
                /* Chart layouts */
                .chart-full-page {
                    page-break-before: always;
                    page-break-after: always;
                    text-align: center;
                    padding: 2cm 1cm;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    min-height: 80vh;
                }
                
                .chart-full-page img {
                    max-width: 90%;
                    max-height: 60vh;
                    object-fit: contain;
                }
                
                .charts-grid {
                    display: block;
                    page-break-inside: avoid;
                }
                
                .charts-grid-2col {
                    display: block;
                    page-break-inside: avoid;
                }
                
                .charts-grid-2col .chart {
                    width: 100%;
                    margin: 20px 0;
                    page-break-inside: avoid;
                }
                
                body {
                    font-family: Arial, sans-serif;
                    font-size: 10pt;
                    line-height: 1.4;
                    color: #333;
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                    border-bottom: 3px solid #0066cc;
                    padding-bottom: 20px;
                }
                
                .header h1 {
                    color: #0066cc;
                    font-size: 24pt;
                    margin-bottom: 10px;
                    page-break-after: avoid;
                }
                
                .header .subtitle {
                    color: #666;
                    font-size: 14pt;
                }
                
                .header .meta {
                    margin-top: 20px;
                    font-size: 10pt;
                    color: #888;
                }
                
                /* Table of Contents */
                .toc {
                    margin: 40px 0;
                }
                
                .toc ul {
                    list-style: none;
                    padding-left: 0;
                }
                
                .toc li {
                    margin: 8px 0;
                    font-size: 11pt;
                }
                
                .toc a {
                    text-decoration: none;
                    color: #333;
                }
                
                .toc a:hover {
                    color: #0066cc;
                }
                
                /* Content sections */
                .section {
                    page-break-inside: avoid;
                    margin-bottom: 30px;
                }
                
                .section-full-page {
                    page-break-before: always;
                    page-break-after: always;
                    min-height: 80vh;
                }
                
                .chart-container {
                    page-break-inside: avoid;
                    margin: 1em 0;
                    max-width: 100%;
                    text-align: center;
                }
                
                .chart-container img {
                    max-width: 100%;
                    height: auto;
                }
                
                .chart {
                    page-break-inside: avoid;
                    margin: 20px 0;
                    text-align: center;
                }
                
                .chart img {
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                
                .chart-title {
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #333;
                    font-size: 11pt;
                    page-break-after: avoid;
                }
                
                .chart-caption {
                    font-size: 9pt;
                    color: #666;
                    margin-top: 10px;
                    font-style: italic;
                }
                
                .building-section {
                    page-break-before: always;
                }
                
                .building-section:first-child {
                    page-break-before: auto;
                }
                
                /* Typography */
                h1 {
                    font-size: 18pt;
                    color: #0066cc;
                    page-break-after: avoid;
                    margin-top: 0;
                }
                
                h2 {
                    font-size: 14pt;
                    color: #0066cc;
                    page-break-after: avoid;
                    margin-top: 1.5em;
                    border-bottom: 2px solid #e0e0e0;
                    padding-bottom: 10px;
                }
                
                h3 {
                    font-size: 12pt;
                    color: #004499;
                    page-break-after: avoid;
                    margin-top: 1em;
                }
                
                h4 {
                    font-size: 11pt;
                    color: #333;
                    page-break-after: avoid;
                    margin-top: 1em;
                }
                
                /* Tables */
                table {
                    page-break-inside: avoid;
                    font-size: 9pt;
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }
                
                table th {
                    background-color: #f5f5f5;
                    font-weight: bold;
                    padding: 8px;
                    border: 1px solid #ddd;
                }
                
                table td {
                    padding: 6px 8px;
                    border: 1px solid #ddd;
                }
                
                .data-quality-table,
                .periods-table {
                    page-break-inside: avoid;
                }
                
                /* Metrics and cards */
                .metrics-grid {
                    display: block;
                    page-break-inside: avoid;
                    margin: 20px 0;
                }
                
                .metric-card {
                    display: inline-block;
                    width: 45%;
                    margin: 0 2% 10px 0;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    text-align: center;
                    page-break-inside: avoid;
                    vertical-align: top;
                }
                
                .metric-value {
                    font-size: 14pt;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                
                .metric-label {
                    font-size: 9pt;
                    color: #666;
                }
                
                .metric-value.good { color: #28a745; }
                .metric-value.warning { color: #ffc107; }
                .metric-value.danger { color: #dc3545; }
                .metric-value.neutral { color: #6c757d; }
                
                /* Recommendations */
                .recommendations {
                    page-break-inside: avoid;
                    margin: 1em 0;
                }
                
                .recommendation-list {
                    list-style: none;
                    padding: 0;
                }
                
                .recommendation-list li {
                    margin: 10px 0;
                    padding: 10px;
                    border-left: 4px solid #0066cc;
                    background-color: #f9f9f9;
                    page-break-inside: avoid;
                }
                
                .priority-high {
                    border-left-color: #dc3545 !important;
                    background-color: #fff5f5 !important;
                }
                
                .priority-medium {
                    border-left-color: #ffc107 !important;
                    background-color: #fffbf0 !important;
                }
                
                .priority-low {
                    border-left-color: #28a745 !important;
                    background-color: #f0fff4 !important;
                }
                
                /* Room analysis */
                .room {
                    page-break-inside: avoid;
                    margin: 20px 0;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                }
                
                .room-header {
                    border-bottom: 1px solid #e0e0e0;
                    padding-bottom: 10px;
                    margin-bottom: 15px;
                    page-break-after: avoid;
                }
                
                .basic-statistics {
                    page-break-inside: avoid;
                }
                
                .room-statistics {
                    page-break-inside: avoid;
                }
                
                /* Footer */
                .footer {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 50px;
                    background: white;
                    border-top: 1px solid #ddd;
                    padding: 10px;
                    text-align: center;
                    font-size: 8pt;
                    color: #666;
                }
                
                /* Hide screen-only elements */
                .no-print {
                    display: none;
                }
            ''', font_config=font_config)
            
            # Convert HTML to PDF
            html_doc = HTML(filename=html_file)
            html_doc.write_pdf(pdf_file, stylesheets=[print_css], font_config=font_config)
            
            logger.info(f"PDF report generated successfully using weasyprint: {pdf_file}")
            return str(pdf_file)
            
        except ImportError as e:
            logger.warning(f"weasyprint not available: {e}")
        except OSError as e:
            logger.warning(f"weasyprint system dependencies missing: {e}")
        except Exception as e:
            logger.warning(f"weasyprint failed: {e}")
        
        # Method 2: Try subprocess with wkhtmltopdf (if available)
        try:
            import subprocess
            import shutil
            
            if shutil.which('wkhtmltopdf'):
                logger.info("Attempting PDF generation with wkhtmltopdf")
                cmd = [
                    'wkhtmltopdf',
                    '--page-size', 'A4',
                    '--orientation', 'Portrait',
                    '--margin-top', '2cm',
                    '--margin-bottom', '2cm',
                    '--margin-left', '2cm',
                    '--margin-right', '2cm',
                    '--enable-local-file-access',
                    '--print-media-type',
                    str(html_file),
                    str(pdf_file)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"PDF report generated successfully using wkhtmltopdf: {pdf_file}")
                    return str(pdf_file)
                else:
                    logger.warning(f"wkhtmltopdf failed: {result.stderr}")
            
        except Exception as e:
            logger.warning(f"wkhtmltopdf approach failed: {e}")
        
        # Method 3: Create a print-optimized HTML with instructions
        try:
            print_html_file = output_dir / "htk_report_print.html"
            
            # Read the generated HTML
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Add print-specific CSS
            print_css_inline = '''
            <style media="print">
                @page {
                    size: A4 portrait;
                    margin: 2cm;
                }
                
                body {
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                    color: #333;
                }
                
                .chart-container {
                    page-break-inside: avoid;
                    margin: 1em 0;
                    max-width: 100%;
                }
                
                .chart-container img {
                    max-width: 100%;
                    height: auto;
                }
                
                .building-section {
                    page-break-before: always;
                }
                
                .building-section:first-child {
                    page-break-before: auto;
                }
                
                h1 {
                    font-size: 18pt;
                    color: #2c5530;
                    page-break-after: avoid;
                }
                
                h2 {
                    font-size: 14pt;
                    color: #4a7c59;
                    page-break-after: avoid;
                }
                
                h3 {
                    font-size: 12pt;
                    color: #4a7c59;
                    page-break-after: avoid;
                }
                
                .metric-card {
                    page-break-inside: avoid;
                }
                
                .recommendations {
                    page-break-inside: avoid;
                }
                
                .no-print {
                    display: none;
                }
            </style>
            
            <style media="screen">
                .print-instructions {
                    background: #f0f8f0;
                    border: 2px solid #4a7c59;
                    padding: 1em;
                    margin: 1em 0;
                    border-radius: 5px;
                }
                
                .print-instructions h3 {
                    color: #2c5530;
                    margin-top: 0;
                }
            </style>
            '''
            
            # Add print instructions at the top
            print_instructions = '''
            <div class="print-instructions no-print">
                <h3>📄 PDF Print Instructions</h3>
                <p><strong>To create a PDF from this report:</strong></p>
                <ol>
                    <li>Press <kbd>Ctrl+P</kbd> (Windows/Linux) or <kbd>Cmd+P</kbd> (macOS)</li>
                    <li>Select "Save as PDF" as destination</li>
                    <li>Choose A4 paper size and Portrait orientation</li>
                    <li>Set margins to 2cm (or use default)</li>
                    <li>Ensure "More settings" → "Print backgrounds" is enabled</li>
                    <li>Click "Save" and choose your filename</li>
                </ol>
                <p><em>Note: Automatic PDF generation is not available due to missing system dependencies. 
                This HTML version is optimized for printing and will create a professional PDF when printed to file.</em></p>
            </div>
            '''
            
            # Insert CSS and instructions into HTML
            if '<head>' in html_content:
                html_content = html_content.replace('<head>', f'<head>{print_css_inline}')
            else:
                html_content = print_css_inline + html_content
            
            if '<body>' in html_content:
                html_content = html_content.replace('<body>', f'<body>{print_instructions}')
            else:
                html_content = print_instructions + html_content
            
            # Write print-optimized HTML
            with open(print_html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Print-optimized HTML generated: {print_html_file}")
            logger.info("Use browser's 'Print to PDF' function to create PDF from the HTML report")
            
            return str(print_html_file)
            
        except Exception as e:
            logger.error(f"Failed to create print-optimized HTML: {e}")
        
        # Fallback: Return original HTML
        logger.info(f"PDF generation not available - HTML report: {html_file}")
        return str(html_file)


def create_htk_template() -> HTKReportTemplate:
    """Factory function to create HTK template instance."""
    return HTKReportTemplate()
