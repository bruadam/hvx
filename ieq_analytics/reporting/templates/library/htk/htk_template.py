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

from ieq_analytics.reporting.templates.base_template import BaseTemplate
from ieq_analytics.reporting.charts.manager import get_chart_library_manager
from ieq_analytics.unified_analytics import UnifiedAnalyticsEngine, AnalysisType

logger = logging.getLogger(__name__)


class HTKReportTemplate(BaseTemplate):
    """HTK Report Template implementation."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent
        super().__init__(template_dir)
        
        self.chart_manager = get_chart_library_manager()
        # Note: Analytics integration would be added here
        
        # HTK-specific configuration
        self.co2_threshold = 1000  # ppm
        self.temp_min = 20  # °C
        self.temp_max = 26  # °C
        
    def generate_report(
        self,
        data_dir: Path,
        output_dir: Path,
        buildings: Optional[List[str]] = None,
        export_formats: List[str] = ["pdf", "html"],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate HTK report from mapped data.
        
        Args:
            data_dir: Directory containing mapped IEQ data files
            output_dir: Directory to save the report
            buildings: List of specific buildings to include (None for all)
            export_formats: Export formats ['pdf', 'html']
            **kwargs: Additional configuration options
            
        Returns:
            Dict with generation results and file paths
        """
        logger.info("Starting HTK report generation")
        
        # Ensure we have Path objects
        data_dir = Path(data_dir)
        output_dir = Path(output_dir)
        
        # Create analysis output directory
        analysis_dir = output_dir / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Run analytics on mapped data to get fresh results
        logger.info("Running analytics on mapped data...")
        analysis_data = self._run_analytics(data_dir, analysis_dir)
        
        # Filter buildings if specified
        if buildings:
            analysis_data = {k: v for k, v in analysis_data.items() if k in buildings}
        
        # Generate report data
        report_data = self._prepare_report_data(analysis_data)
        
        # Load mapped data for chart generation
        mapped_data_dir = data_dir.parent / "mapped_data" if (data_dir.parent / "mapped_data").exists() else data_dir
        mapped_data = self._load_mapped_data(mapped_data_dir)
        
        # Generate charts using mapped data
        charts_dir = output_dir / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)
        chart_paths = self._generate_charts(mapped_data, charts_dir)
        
        # Prepare template context
        template_context = self._prepare_template_context(report_data, chart_paths, mapped_data)
        
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
    
    def _calculate_basic_statistics(self, mapped_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
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
    
    def _run_analytics(self, data_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Run analytics on mapped data and return structured results."""
        logger.info(f"Running analytics on data directory: {data_dir}")
        
        # Check if we already have an analysis summary file
        summary_file = data_dir / "ieq_analysis_summary.csv"
        if summary_file.exists():
            logger.info("Found existing analysis summary, loading results...")
            return self._load_analysis_data(data_dir)
        
        # Find mapped data files (exclude summary files)
        mapped_files = [f for f in data_dir.glob("*.csv") if "summary" not in f.name.lower()]
        if not mapped_files:
            logger.warning(f"No mapped CSV files found in data directory: {data_dir}")
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
                    for col in ['timestamp', 'time', 'date', 'datetime']:
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
                                'completeness': 95,
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
    
    def _prepare_report_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
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
            building_info = self._process_building_data(building_name, building_data)
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
    
    def _process_building_data(self, building_name: str, building_data: Dict[str, Any]) -> Dict[str, Any]:
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
            building_info["metrics"] = self._calculate_building_metrics(room_metrics)
        
        # Calculate performance attributes expected by template
        co2_performance = building_info["metrics"].get("co2_compliance", 85.0)
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
            temp_test = test_results.get("temp_comfort_all_year_opening", {})
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
        
        if "test_results" not in room_data:
            return seasons
        
        test_results = room_data["test_results"]
        
        for season_key, season_name in season_names.items():
            season_data = {
                "name": season_name,
                "co2_compliance": "N/A",
                "temp_compliance": "N/A",
                "avg_co2": "N/A",
                "avg_temp": "N/A",
                "co2_class": "neutral",
                "temp_class": "neutral"
            }
            
            # Look for seasonal test results
            co2_test_key = f"co2_1000_{season_key}_opening"
            temp_test_key = f"temp_comfort_{season_key}_opening"
            
            if co2_test_key in test_results:
                compliance_rate = test_results[co2_test_key].get("compliance_rate", 0)
                if compliance_rate > 0:  # Only show if we have actual data
                    season_data["co2_compliance"] = f"{compliance_rate:.1f}"
                    season_data["co2_class"] = self._get_performance_class(compliance_rate)
                    mean_value = test_results[co2_test_key].get("mean", 0)
                    if mean_value > 0:
                        season_data["avg_co2"] = f"{mean_value:.0f}"
            
            if temp_test_key in test_results:
                compliance_rate = test_results[temp_test_key].get("compliance_rate", 0)
                if compliance_rate > 0:  # Only show if we have actual data
                    season_data["temp_compliance"] = f"{compliance_rate:.1f}"
                    season_data["temp_class"] = self._get_performance_class(compliance_rate)
                    mean_value = test_results[temp_test_key].get("mean", 0)
                    if mean_value > 0:
                        season_data["avg_temp"] = f"{mean_value:.1f}"
            
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
    
    def _calculate_building_metrics(self, room_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        
        overall_co2 = np.mean([b["co2_compliance"] for b in building_metrics])
        overall_temp = np.mean([b["temp_compliance"] for b in building_metrics])
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
            "priority": "high",
            "estimated_cost": "50,000",
            "building": building_name
        })
        
        recommendations.append({
            "title": f"Optimér temperaturregulering i {building_name}",
            "description": "Justér termostatindstillinger for bedre komfort",
            "priority": "medium",
            "estimated_cost": "15,000",
            "building": building_name
        })
        
        return recommendations
    
    def _generate_charts(self, mapped_data: Dict[str, pd.DataFrame], charts_dir: Path) -> Dict[str, str]:
        """Generate all required charts for the report using mapped data."""
        from .charts import generate_htk_charts_from_mapped_data
        
        logger.info("Generating HTK charts from mapped data...")
        chart_paths = generate_htk_charts_from_mapped_data(mapped_data, charts_dir)
        logger.info(f"Generated {len(chart_paths)} charts")
        
        return chart_paths
    
    def _convert_to_relative_paths(self, chart_paths: Dict[str, str]) -> Dict[str, str]:
        """Convert absolute chart paths to relative paths for HTML templates."""
        relative_paths = {}
        for key, path in chart_paths.items():
            if path and os.path.exists(path):
                # Extract just the filename from the path
                filename = os.path.basename(path)
                # Make it relative to the HTML file (which is in the same directory as charts/)
                relative_paths[key] = f"charts/{filename}"
            else:
                relative_paths[key] = ""
        return relative_paths
    
    def _prepare_template_context(self, report_data: Dict[str, Any], chart_paths: Dict[str, str], mapped_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """Prepare the context for the Jinja2 template."""
        
        # Convert absolute chart paths to relative paths for HTML
        relative_chart_paths = self._convert_to_relative_paths(chart_paths)
        
        # Calculate basic statistics from mapped data
        basic_statistics = {}
        if mapped_data:
            basic_statistics = self._calculate_basic_statistics(mapped_data)
        
        # Organize charts by building
        buildings_with_charts = []
        for building in report_data["buildings"]:
            building_id = building["name"].lower().replace(" ", "_")
            
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
                "room_compliance_comparison": relative_chart_paths.get(f'room_compliance_comparison_{building_id}', '')
            }
            
            # Add charts to rooms with basic statistics
            rooms_with_charts = []
            for room in building["rooms"]:
                room_id = f"{building_id}_{room['name'].lower().replace(' ', '_')}"
                full_room_id = f"{building_id}_{room['name']}"
                
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
                
                # Add basic statistics if available
                if full_room_id in basic_statistics:
                    room_with_charts["basic_statistics"] = basic_statistics[full_room_id]
                elif room['name'] in basic_statistics:
                    room_with_charts["basic_statistics"] = basic_statistics[room['name']]
                
                rooms_with_charts.append(room_with_charts)
            
            # Add charts to building data
            building_with_charts = building.copy()
            building_with_charts["charts"] = building_charts
            building_with_charts["rooms"] = rooms_with_charts
            
            # Add building-level basic statistics (aggregate from rooms)
            if rooms_with_charts:
                building_with_charts["basic_statistics"] = self._aggregate_building_statistics(rooms_with_charts)
            
            buildings_with_charts.append(building_with_charts)
        
        context = {
            "report_title": "Indendørs Miljøkvalitets Rapport",
            "generation_date": datetime.now().strftime("%d. %B %Y"),
            "analysis_period": "2024",
            "building_count": len(report_data["buildings"]),
            "include_toc": True,
            "template_version": "1.0.0",
            
            # Data from report preparation with charts
            "buildings": buildings_with_charts,
            "data_quality": report_data["data_quality"],
            "charts": {
                "building_comparison": relative_chart_paths.get('building_comparison', ''),
                "performance_overview": relative_chart_paths.get('performance_overview', ''),
                "data_completeness": relative_chart_paths.get('data_completeness', '')
            },
            
            # Overall metrics
            **report_data["overall_metrics"],
            
            # Recommendations
            "high_priority_recommendations": [
                r for r in report_data["recommendations"] 
                if r.get("priority") == "high"
            ],
            "implementation_phases": self._create_implementation_phases(report_data["recommendations"]),
            
            # Summary text
            "executive_summary_text": self._generate_executive_summary_text(report_data)
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
        
        # Use the first room's data quality as a proxy for building quality
        # In a real implementation, you'd aggregate across all rooms
        avg_completeness = 95.0  # Placeholder
        
        return {
            'completeness': avg_completeness,
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
