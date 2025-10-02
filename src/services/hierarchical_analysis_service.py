"""
Hierarchical Analysis Service

Performs analysis at room, level, building, and portfolio levels.
Integrates with the existing UnifiedAnalyticsEngine to run tests on timeseries data.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import warnings

import pandas as pd
import numpy as np
import yaml

from src.models.building_data import BuildingDataset, Building, Level, Room, TimeSeriesData
from src.models.analysis_models import (
    RoomAnalysis, LevelAnalysis, BuildingAnalysis, PortfolioAnalysis,
    AnalysisResults, TestResult, AnalysisSeverity, AnalysisStatus
)
from src.core.analytics_engine import UnifiedAnalyticsEngine, AnalysisType, UnifiedFilterProcessor

logger = logging.getLogger(__name__)


class HierarchicalAnalysisService:
    """Service for performing hierarchical analysis on building data."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the hierarchical analysis service.
        
        Args:
            config_path: Path to tests.yaml configuration file
        """
        self.config_path = config_path or Path("config/tests.yaml")
        self.config = self._load_config()
        self.analytics_engine = None
        # Initialize filter processor with config
        self.filter_processor = UnifiedFilterProcessor(self.config)
        # Cache for warnings to display at end
        self.filter_warnings = []  # List of (room_name, room_id, filter_name, test_name, reason) tuples
    
    def _load_config(self) -> Dict[str, Any]:
        """Load analysis configuration."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return {'analytics': {}}
    
    def analyze_dataset(
        self,
        dataset: BuildingDataset,
        output_dir: Path,
        portfolio_name: str = "Portfolio",
        save_individual_files: bool = True
    ) -> AnalysisResults:
        """
        Perform complete hierarchical analysis on a dataset.
        
        Args:
            dataset: BuildingDataset to analyze
            output_dir: Directory to save analysis results
            portfolio_name: Name for the portfolio analysis
            save_individual_files: Whether to save individual JSON files per room/level/building
        
        Returns:
            AnalysisResults containing all analyses
        """
        logger.info(f"Starting hierarchical analysis of dataset with {dataset.get_building_count()} buildings")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        results = AnalysisResults(
            rooms={},
            levels={},
            buildings={},
            portfolio=None,
            metadata={'portfolio_name': portfolio_name}
        )
        
        # 1. Analyze rooms
        logger.info("Step 1/4: Analyzing rooms...")
        room_analyses = self._analyze_all_rooms(dataset, output_dir if save_individual_files else None)
        results.rooms = room_analyses
        logger.info(f"  Completed {len(room_analyses)} room analyses")
        
        # 2. Analyze levels
        logger.info("Step 2/4: Aggregating level analyses...")
        level_analyses = self._analyze_all_levels(dataset, room_analyses, output_dir if save_individual_files else None)
        results.levels = level_analyses
        logger.info(f"  Completed {len(level_analyses)} level analyses")
        
        # 3. Analyze buildings
        logger.info("Step 3/4: Aggregating building analyses...")
        building_analyses = self._analyze_all_buildings(dataset, room_analyses, level_analyses, output_dir if save_individual_files else None)
        results.buildings = building_analyses
        logger.info(f"  Completed {len(building_analyses)} building analyses")
        
        # 4. Analyze portfolio
        logger.info("Step 4/4: Aggregating portfolio analysis...")
        portfolio_analysis = self._analyze_portfolio(dataset, building_analyses, portfolio_name)
        results.portfolio = portfolio_analysis
        logger.info(f"  Completed portfolio analysis")
        
        # Save all results
        results.save_all_to_directory(output_dir)
        logger.info(f"Analysis complete. Results saved to: {output_dir}")
        
        # Display grouped warnings at the end
        self._display_filter_warnings_summary()
        
        return results
    
    def _analyze_all_rooms(
        self,
        dataset: BuildingDataset,
        output_dir: Optional[Path]
    ) -> Dict[str, RoomAnalysis]:
        """Analyze all rooms in the dataset."""
        room_analyses = {}
        
        for building in dataset.buildings:
            for room in building.rooms:
                try:
                    analysis = self._analyze_room(room, building)
                    room_analyses[room.id] = analysis
                    
                    if output_dir:
                        room_file = output_dir / "rooms" / f"{room.id}.json"
                        room_file.parent.mkdir(parents=True, exist_ok=True)
                        analysis.save_to_json(room_file)
                        
                except Exception as e:
                    logger.error(f"Error analyzing room {room.id}: {e}")
                    continue
        
        return room_analyses
    
    def _analyze_room(self, room: Room, building: Building) -> RoomAnalysis:
        """Perform analysis on a single room."""
        analysis = RoomAnalysis(
            room_id=room.id,
            room_name=room.name,
            building_id=room.building_id,
            level_id=room.level_id,
            data_period_start=room.data_period_start,
            data_period_end=room.data_period_end,
            overall_quality_score=room.get_overall_quality_score(),
            parameters_analyzed=list(room.timeseries.keys())
        )
        
        # Calculate data completeness
        if room.timeseries:
            completeness_scores = [ts.data_quality.completeness for ts in room.timeseries.values()]
            analysis.data_completeness = sum(completeness_scores) / len(completeness_scores)
        
        # Run tests on each parameter
        test_results = self._run_room_tests(room, building)
        for test_name, result in test_results.items():
            analysis.add_test_result(test_name, result)
        
        # Calculate statistics for each parameter
        for param_name, ts in room.timeseries.items():
            analysis.statistics[param_name] = ts.get_statistics()
        
        # Calculate overall metrics
        analysis.calculate_overall_metrics()
        
        # Calculate weather correlation summary
        analysis.weather_correlation_summary = self._calculate_weather_correlation_summary(test_results)
        
        # Generate recommendations
        analysis.recommendations = self._generate_room_recommendations(analysis)
        
        # Identify critical issues
        analysis.critical_issues = self._identify_critical_issues(analysis)
        
        return analysis
    
    def _run_room_tests(self, room: Room, building: Building) -> Dict[str, TestResult]:
        """Run configured tests on room data."""
        test_results = {}
        
        tests_config = self.config.get('analytics', {})
        
        for test_name, test_config in tests_config.items():
            try:
                parameter = test_config.get('feature', test_config.get('parameter', 'temperature'))
                
                # Check if room has this parameter
                if parameter not in room.timeseries:
                    continue
                
                ts = room.timeseries[parameter]
                
                # Run the test
                result = self._evaluate_test(ts, test_name, test_config, building, room)
                if result:
                    test_results[test_name] = result
                    
            except Exception as e:
                logger.error(f"Error running test {test_name} on room {room.id}: {e}")
                continue
        
        return test_results
    
    def _evaluate_test(
        self,
        ts: TimeSeriesData,
        test_name: str,
        test_config: Dict[str, Any],
        building: Building,
        room: Optional[Room] = None
    ) -> Optional[TestResult]:
        """Evaluate a single test on timeseries data."""
        try:
            # Extract test parameters
            parameter = test_config.get('feature', test_config.get('parameter', ts.parameter))
            threshold = test_config.get('limit', test_config.get('threshold'))
            mode = test_config.get('mode', 'bidirectional')
            description = test_config.get('description', '')
            filter_name = test_config.get('filter')
            period_name = test_config.get('period')
            
            if threshold is None:
                return None
            
            # Get the data
            df = ts.data
            if parameter not in df.columns:
                return None
            
            # Apply temporal filter if specified
            if filter_name:
                logger.debug(f"Applying filter '{filter_name}' for test '{test_name}'")
                df = self.filter_processor.apply_filter(df, filter_name, period_name or '')
                if df.empty:
                    # Cache warning instead of logging immediately
                    room_name = room.name if room else "Unknown"
                    room_id = room.id if room else "unknown"
                    self.filter_warnings.append({
                        'room_name': room_name,
                        'room_id': room_id,
                        'filter_name': filter_name,
                        'test_name': test_name,
                        'period': period_name or 'all_year'
                    })
                    return None
            
            data_series = df[parameter].dropna()
            if len(data_series) == 0:
                return None
            
            # Determine compliance based on mode
            if mode == 'unidirectional_ascending':
                # Value should be BELOW threshold (violations are ABOVE)
                compliant = data_series <= threshold
                threshold_type = 'above'
            elif mode == 'unidirectional_descending':
                # Value should be ABOVE threshold (violations are BELOW)
                compliant = data_series >= threshold
                threshold_type = 'below'
            else:  # bidirectional or range
                # Assuming range with min/max
                if isinstance(threshold, dict):
                    min_val = threshold.get('min', float('-inf'))
                    max_val = threshold.get('max', float('inf'))
                    compliant = (data_series >= min_val) & (data_series <= max_val)
                    threshold_type = 'range'
                else:
                    # Simple bidirectional - assume within ±threshold
                    compliant = data_series.abs() <= threshold
                    threshold_type = 'bidirectional'
            
            # Calculate metrics
            total_hours = len(data_series)
            compliant_hours = int(compliant.sum())
            non_compliant_hours = total_hours - compliant_hours
            compliance_rate = (compliant_hours / total_hours * 100) if total_hours > 0 else 0
            
            # Calculate statistics
            statistics = {
                'mean': float(data_series.mean()),
                'std': float(data_series.std()),
                'min': float(data_series.min()),
                'max': float(data_series.max()),
                'median': float(data_series.median()),
                'p95': float(data_series.quantile(0.95)),
                'p05': float(data_series.quantile(0.05))
            }
            
            # Determine severity
            severity = self._determine_severity(compliance_rate, non_compliant_hours)
            
            # Generate recommendations
            recommendations = self._generate_test_recommendations(
                parameter, threshold, threshold_type, compliance_rate, statistics
            )
            
            # Calculate weather correlations if building has climate data
            weather_correlations = {}
            non_compliance_weather_stats = {}
            if building.climate_data and non_compliant_hours > 0:
                try:
                    weather_correlations, non_compliance_weather_stats = self._calculate_weather_correlations(
                        data_series, compliant, building.climate_data
                    )
                except Exception as e:
                    logger.warning(f"Could not calculate weather correlations for {test_name}: {e}")
            
            return TestResult(
                test_name=test_name,
                description=description,
                parameter=parameter,
                compliance_rate=compliance_rate,
                total_hours=total_hours,
                compliant_hours=compliant_hours,
                non_compliant_hours=non_compliant_hours,
                threshold=threshold,
                threshold_type=threshold_type,
                statistics=statistics,
                severity=severity,
                recommendations=recommendations,
                period=test_config.get('period'),
                filter_applied=test_config.get('filter'),
                weather_correlations=weather_correlations,
                non_compliance_weather_stats=non_compliance_weather_stats
            )
            
        except Exception as e:
            logger.error(f"Error evaluating test {test_name}: {e}")
            return None
    
    def _determine_severity(self, compliance_rate: float, non_compliant_hours: int) -> AnalysisSeverity:
        """Determine severity level based on compliance."""
        if compliance_rate >= 95:
            return AnalysisSeverity.INFO
        elif compliance_rate >= 85:
            return AnalysisSeverity.LOW
        elif compliance_rate >= 70:
            return AnalysisSeverity.MEDIUM
        elif compliance_rate >= 50:
            return AnalysisSeverity.HIGH
        else:
            return AnalysisSeverity.CRITICAL
    
    def _generate_test_recommendations(
        self,
        parameter: str,
        threshold: Any,
        threshold_type: str,
        compliance_rate: float,
        statistics: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if compliance_rate < 70:
            if parameter == 'temperature':
                if threshold_type == 'above':
                    recommendations.append(f"Temperature frequently exceeds {threshold}°C. Consider improving cooling or ventilation.")
                elif threshold_type == 'below':
                    recommendations.append(f"Temperature frequently below {threshold}°C. Check heating system and insulation.")
            elif parameter == 'co2':
                if threshold_type == 'above':
                    recommendations.append(f"CO2 levels frequently exceed {threshold} ppm. Increase ventilation rates.")
            elif parameter == 'humidity':
                if threshold_type == 'above':
                    recommendations.append(f"Humidity frequently exceeds {threshold}%. Check ventilation and dehumidification.")
                elif threshold_type == 'below':
                    recommendations.append(f"Humidity frequently below {threshold}%. Consider humidification.")
        
        return recommendations
    
    def _generate_room_recommendations(self, analysis: RoomAnalysis) -> List[str]:
        """Generate overall recommendations for a room."""
        recommendations = []
        
        # Aggregate recommendations from tests
        for result in analysis.test_results.values():
            recommendations.extend(result.recommendations)
        
        # Add data quality recommendations
        if analysis.data_completeness < 80:
            recommendations.append("Data completeness is low. Verify sensor functionality and data collection.")
        
        # Remove duplicates
        return list(set(recommendations))
    
    def _identify_critical_issues(self, analysis: RoomAnalysis) -> List[str]:
        """Identify critical issues in room analysis."""
        issues = []
        
        for result in analysis.test_results.values():
            if result.severity in [AnalysisSeverity.CRITICAL, AnalysisSeverity.HIGH]:
                if result.compliance_rate < 50:
                    issues.append(
                        f"{result.parameter.upper()}: {result.description} - "
                        f"Only {result.compliance_rate:.1f}% compliant"
                    )
        
        return issues
    
    def _calculate_weather_correlations(
        self,
        data_series: pd.Series,
        compliant: pd.Series,
        climate_data
    ) -> tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Calculate correlation between non-compliance and weather factors.
        
        Args:
            data_series: Indoor parameter timeseries
            compliant: Boolean series indicating compliance
            climate_data: ClimateData object with outdoor weather data
        
        Returns:
            Tuple of (correlations dict, weather stats dict)
        """
        from src.models.building_data import ClimateData
        
        correlations = {}
        weather_stats = {}
        
        # Get non-compliant periods
        non_compliant_mask = ~compliant
        non_compliant_index = data_series[non_compliant_mask].index
        
        if len(non_compliant_index) == 0:
            return correlations, weather_stats
        
        # Weather parameters to analyze
        weather_params = ['outdoor_temp', 'temperature', 'radiation', 'sunshine']
        
        for param in weather_params:
            try:
                # Get weather timeseries
                weather_ts = climate_data.get_parameter(param)
                if not weather_ts:
                    continue
                
                weather_df = weather_ts.data
                if param not in weather_df.columns:
                    continue
                
                # Get weather series
                weather_series = weather_df[param].copy()
                
                # Handle timezone mismatch - make both timezone-naive for alignment
                if hasattr(weather_series.index, 'tz') and weather_series.index.tz is not None:
                    weather_series.index = weather_series.index.tz_localize(None)
                
                indoor_index = data_series.index
                if hasattr(indoor_index, 'tz') and indoor_index.tz is not None:
                    indoor_index = indoor_index.tz_localize(None)
                
                # Align weather data with indoor data
                weather_aligned = weather_series.reindex(indoor_index, method='nearest', tolerance=pd.Timedelta('1h'))
                weather_aligned = weather_aligned.dropna()
                
                # Get common index between indoor and weather data
                common_idx = data_series.index.intersection(weather_aligned.index)
                if len(common_idx) < 10:  # Need minimum data points for correlation
                    continue
                
                # Calculate correlation between non-compliance and weather
                # Create binary non-compliance series for correlation
                non_compliance_binary = (~compliant.reindex(common_idx)).astype(int)
                weather_common = weather_aligned.reindex(common_idx)
                
                # Calculate Pearson correlation (suppress divide-by-zero warnings)
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value encountered in divide')
                    correlation = non_compliance_binary.corr(weather_common)
                
                if not np.isnan(correlation):
                    # Normalize parameter name for consistency
                    param_name = 'outdoor_temp' if param == 'temperature' else param
                    correlations[param_name] = float(correlation)
                    
                    # Calculate weather statistics during non-compliant periods
                    non_compliant_common_idx = common_idx.intersection(non_compliant_index)
                    if len(non_compliant_common_idx) > 0:
                        weather_during_nc = weather_common.reindex(non_compliant_common_idx).dropna()
                        if len(weather_during_nc) > 0:
                            weather_stats[param_name] = {
                                'mean': float(weather_during_nc.mean()),
                                'min': float(weather_during_nc.min()),
                                'max': float(weather_during_nc.max()),
                                'std': float(weather_during_nc.std())
                            }
                
            except Exception as e:
                logger.debug(f"Error calculating correlation for {param}: {e}")
                continue
        
        return correlations, weather_stats
    
    def _calculate_weather_correlation_summary(
        self,
        test_results: Dict[str, TestResult]
    ) -> Dict[str, Any]:
        """
        Calculate summary of weather correlations across all tests.
        
        Args:
            test_results: Dictionary of test results
        
        Returns:
            Summary dictionary with averaged correlations
        """
        summary = {
            'has_correlations': False,
            'avg_correlations': {},
            'strongest_correlations': []
        }
        
        # Collect all correlations
        all_correlations = {}
        for test_name, result in test_results.items():
            if result.weather_correlations:
                summary['has_correlations'] = True
                for param, corr in result.weather_correlations.items():
                    if param not in all_correlations:
                        all_correlations[param] = []
                    all_correlations[param].append({
                        'test': test_name,
                        'correlation': corr
                    })
        
        # Calculate averages
        for param, corr_list in all_correlations.items():
            avg_corr = sum(c['correlation'] for c in corr_list) / len(corr_list)
            summary['avg_correlations'][param] = float(avg_corr)
            
            # Track strongest correlations (absolute value)
            for item in corr_list:
                summary['strongest_correlations'].append({
                    'test': item['test'],
                    'weather_parameter': param,
                    'correlation': item['correlation']
                })
        
        # Sort by absolute correlation strength
        summary['strongest_correlations'].sort(
            key=lambda x: abs(x['correlation']),
            reverse=True
        )
        summary['strongest_correlations'] = summary['strongest_correlations'][:5]  # Top 5
        
        return summary
    
    def _analyze_all_levels(
        self,
        dataset: BuildingDataset,
        room_analyses: Dict[str, RoomAnalysis],
        output_dir: Optional[Path]
    ) -> Dict[str, LevelAnalysis]:
        """Analyze all levels by aggregating room data."""
        level_analyses = {}
        
        for building in dataset.buildings:
            for level in building.levels:
                try:
                    analysis = self._analyze_level(level, building, room_analyses)
                    level_analyses[level.id] = analysis
                    
                    if output_dir:
                        level_file = output_dir / "levels" / f"{level.id}.json"
                        level_file.parent.mkdir(parents=True, exist_ok=True)
                        analysis.save_to_json(level_file)
                        
                except Exception as e:
                    logger.error(f"Error analyzing level {level.id}: {e}")
                    continue
        
        return level_analyses
    
    def _analyze_level(
        self,
        level: Level,
        building: Building,
        room_analyses: Dict[str, RoomAnalysis]
    ) -> LevelAnalysis:
        """Aggregate room analyses to level analysis."""
        room_ids = [room.id for room in level.rooms]
        level_room_analyses = [room_analyses[rid] for rid in room_ids if rid in room_analyses]
        
        analysis = LevelAnalysis(
            level_id=level.id,
            level_name=level.name,
            building_id=building.id,
            room_ids=room_ids,
            room_count=len(level_room_analyses)
        )
        
        if not level_room_analyses:
            analysis.status = AnalysisStatus.FAILED
            return analysis
        
        # Aggregate compliance and quality scores
        compliance_rates = [ra.overall_compliance_rate for ra in level_room_analyses]
        quality_scores = [ra.overall_quality_score for ra in level_room_analyses]
        
        analysis.avg_compliance_rate = sum(compliance_rates) / len(compliance_rates) if compliance_rates else 0
        analysis.avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Aggregate test results
        analysis.test_aggregations = self._aggregate_test_results(level_room_analyses)
        
        # Rank rooms
        sorted_rooms = sorted(level_room_analyses, key=lambda x: x.overall_compliance_rate, reverse=True)
        analysis.best_performing_rooms = [
            {'room_id': r.room_id, 'room_name': r.room_name, 'compliance_rate': r.overall_compliance_rate}
            for r in sorted_rooms[:3]
        ]
        # Get worst performing rooms in ascending order (worst first)
        worst_rooms = list(reversed(sorted_rooms[-5:]))  # Get bottom 5 rooms, reverse to show worst first
        analysis.worst_performing_rooms = [
            {'room_id': r.room_id, 'room_name': r.room_name, 'compliance_rate': r.overall_compliance_rate}
            for r in worst_rooms
        ]
        
        # Aggregate issues and recommendations
        all_issues = [issue for ra in level_room_analyses for issue in ra.critical_issues]
        all_recommendations = [rec for ra in level_room_analyses for rec in ra.recommendations]
        
        analysis.critical_issues = list(set(all_issues))[:10]  # Top 10 unique issues
        analysis.recommendations = list(set(all_recommendations))[:10]  # Top 10 unique recommendations
        
        return analysis
    
    def _analyze_all_buildings(
        self,
        dataset: BuildingDataset,
        room_analyses: Dict[str, RoomAnalysis],
        level_analyses: Dict[str, LevelAnalysis],
        output_dir: Optional[Path]
    ) -> Dict[str, BuildingAnalysis]:
        """Analyze all buildings by aggregating level and room data."""
        building_analyses = {}
        
        for building in dataset.buildings:
            try:
                analysis = self._analyze_building(building, room_analyses, level_analyses)
                building_analyses[building.id] = analysis
                
                if output_dir:
                    building_file = output_dir / "buildings" / f"{building.id}.json"
                    building_file.parent.mkdir(parents=True, exist_ok=True)
                    analysis.save_to_json(building_file)
                    
            except Exception as e:
                logger.error(f"Error analyzing building {building.id}: {e}")
                continue
        
        return building_analyses
    
    def _analyze_building(
        self,
        building: Building,
        room_analyses: Dict[str, RoomAnalysis],
        level_analyses: Dict[str, LevelAnalysis]
    ) -> BuildingAnalysis:
        """Aggregate room and level analyses to building analysis."""
        room_ids = [room.id for room in building.rooms]
        level_ids = [level.id for level in building.levels]
        
        building_room_analyses = [room_analyses[rid] for rid in room_ids if rid in room_analyses]
        building_level_analyses = [level_analyses[lid] for lid in level_ids if lid in level_analyses]
        
        analysis = BuildingAnalysis(
            building_id=building.id,
            building_name=building.name,
            level_ids=level_ids,
            room_ids=room_ids,
            level_count=len(building_level_analyses),
            room_count=len(building_room_analyses)
        )
        
        if not building_room_analyses:
            analysis.status = AnalysisStatus.FAILED
            return analysis
        
        # Aggregate metrics
        compliance_rates = [ra.overall_compliance_rate for ra in building_room_analyses]
        quality_scores = [ra.overall_quality_score for ra in building_room_analyses]
        
        analysis.avg_compliance_rate = sum(compliance_rates) / len(compliance_rates) if compliance_rates else 0
        analysis.avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Aggregate test results
        analysis.test_aggregations = self._aggregate_test_results(building_room_analyses)
        
        # Compare levels
        if building_level_analyses:
            analysis.level_comparisons = {
                level.level_id: {
                    'level_name': level.level_name,
                    'avg_compliance': level.avg_compliance_rate,
                    'room_count': level.room_count
                }
                for level in building_level_analyses
            }
            
            # Rank levels
            sorted_levels = sorted(building_level_analyses, key=lambda x: x.avg_compliance_rate, reverse=True)
            analysis.best_performing_levels = [
                {'level_id': l.level_id, 'level_name': l.level_name, 'compliance_rate': l.avg_compliance_rate}
                for l in sorted_levels[:3]
            ]
            analysis.worst_performing_levels = [
                {'level_id': l.level_id, 'level_name': l.level_name, 'compliance_rate': l.avg_compliance_rate}
                for l in sorted_levels[-3:]
            ]
        
        # Rank rooms
        sorted_rooms = sorted(building_room_analyses, key=lambda x: x.overall_compliance_rate, reverse=True)
        analysis.best_performing_rooms = [
            {'room_id': r.room_id, 'room_name': r.room_name, 'compliance_rate': r.overall_compliance_rate}
            for r in sorted_rooms[:5]
        ]
        # Get worst performing rooms in ascending order (worst first)
        worst_rooms = list(reversed(sorted_rooms[-5:]))  # Get bottom 5 rooms, reverse to show worst first
        analysis.worst_performing_rooms = [
            {'room_id': r.room_id, 'room_name': r.room_name, 'compliance_rate': r.overall_compliance_rate}
            for r in worst_rooms
        ]
        
        # Aggregate issues and recommendations
        all_issues = [issue for ra in building_room_analyses for issue in ra.critical_issues]
        all_recommendations = [rec for ra in building_room_analyses for rec in ra.recommendations]
        
        analysis.critical_issues = list(set(all_issues))[:15]
        analysis.recommendations = list(set(all_recommendations))[:15]
        
        return analysis
    
    def _analyze_portfolio(
        self,
        dataset: BuildingDataset,
        building_analyses: Dict[str, BuildingAnalysis],
        portfolio_name: str
    ) -> PortfolioAnalysis:
        """Aggregate building analyses to portfolio analysis."""
        building_list = list(building_analyses.values())
        
        analysis = PortfolioAnalysis(
            portfolio_name=portfolio_name,
            portfolio_id=portfolio_name.lower().replace(' ', '_'),
            building_ids=[b.building_id for b in building_list],
            building_count=len(building_list),
            total_room_count=sum(b.room_count for b in building_list),
            total_level_count=sum(b.level_count for b in building_list)
        )
        
        if not building_list:
            analysis.status = AnalysisStatus.FAILED
            return analysis
        
        # Aggregate metrics
        compliance_rates = [b.avg_compliance_rate for b in building_list]
        quality_scores = [b.avg_quality_score for b in building_list]
        
        analysis.avg_compliance_rate = sum(compliance_rates) / len(compliance_rates) if compliance_rates else 0
        analysis.avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Compare buildings
        analysis.building_comparisons = {
            b.building_id: {
                'building_name': b.building_name,
                'avg_compliance': b.avg_compliance_rate,
                'room_count': b.room_count,
                'level_count': b.level_count
            }
            for b in building_list
        }
        
        # Rank buildings
        sorted_buildings = sorted(building_list, key=lambda x: x.avg_compliance_rate, reverse=True)
        analysis.best_performing_buildings = [
            {
                'building_id': b.building_id,
                'building_name': b.building_name,
                'compliance_rate': b.avg_compliance_rate
            }
            for b in sorted_buildings[:5]
        ]
        analysis.worst_performing_buildings = [
            {
                'building_id': b.building_id,
                'building_name': b.building_name,
                'compliance_rate': b.avg_compliance_rate
            }
            for b in sorted_buildings[-5:]
        ]
        
        # Aggregate issues and recommendations
        all_issues = [issue for b in building_list for issue in b.critical_issues]
        all_recommendations = [rec for b in building_list for rec in b.recommendations]
        
        # Find common issues
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        analysis.common_issues = [
            {'issue': issue, 'occurrence_count': count}
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        analysis.critical_issues = list(set(all_issues))[:20]
        analysis.recommendations = list(set(all_recommendations))[:20]
        
        # Generate investment priorities
        analysis.investment_priorities = self._generate_investment_priorities(building_list)
        
        return analysis
    
    def _aggregate_test_results(self, analyses: List[RoomAnalysis]) -> Dict[str, Dict[str, Any]]:
        """Aggregate test results across multiple room analyses."""
        aggregations = {}
        
        # Collect all test names
        all_test_names = set()
        for analysis in analyses:
            all_test_names.update(analysis.test_results.keys())
        
        # Aggregate each test
        for test_name in all_test_names:
            test_results = [
                analysis.test_results[test_name]
                for analysis in analyses
                if test_name in analysis.test_results
            ]
            
            if not test_results:
                continue
            
            compliance_rates = [tr.compliance_rate for tr in test_results]
            
            aggregations[test_name] = {
                'avg_compliance_rate': sum(compliance_rates) / len(compliance_rates),
                'min_compliance_rate': min(compliance_rates),
                'max_compliance_rate': max(compliance_rates),
                'room_count': len(test_results),
                'parameter': test_results[0].parameter,
                'threshold': test_results[0].threshold
            }
        
        return aggregations
    
    def _generate_investment_priorities(
        self,
        building_analyses: List[BuildingAnalysis]
    ) -> List[Dict[str, Any]]:
        """Generate investment priorities based on analysis."""
        priorities = []
        
        # Sort buildings by compliance (worst first)
        sorted_buildings = sorted(building_analyses, key=lambda x: x.avg_compliance_rate)
        
        for i, building in enumerate(sorted_buildings[:10], 1):
            priority = {
                'priority_rank': i,
                'building_id': building.building_id,
                'building_name': building.building_name,
                'compliance_rate': building.avg_compliance_rate,
                'room_count': building.room_count,
                'estimated_impact': 'High' if building.avg_compliance_rate < 70 else 'Medium',
                'key_issues': building.critical_issues[:3] if building.critical_issues else []
            }
            priorities.append(priority)
        
        return priorities
    
    def _display_filter_warnings_summary(self):
        """Display grouped summary of filter warnings at the end of analysis."""
        if not self.filter_warnings:
            return
        
        from collections import defaultdict
        
        # Group warnings by room
        warnings_by_room = defaultdict(list)
        for warning in self.filter_warnings:
            warnings_by_room[warning['room_name']].append(warning)
        
        # Count total issues
        total_warnings = len(self.filter_warnings)
        affected_rooms = len(warnings_by_room)
        
        # Display summary
        logger.warning("\n" + "="*80)
        logger.warning(f"⚠️  FILTER WARNINGS SUMMARY: {total_warnings} missing data instances across {affected_rooms} rooms")
        logger.warning("="*80)
        
        # Group by issue type
        issue_summary = defaultdict(int)
        for warning in self.filter_warnings:
            key = f"{warning['filter_name']} / {warning['period']}"
            issue_summary[key] += 1
        
        logger.warning("\n📊 Most Common Issues:")
        for issue, count in sorted(issue_summary.items(), key=lambda x: x[1], reverse=True)[:5]:
            logger.warning(f"   • {issue}: {count} occurrences")
        
        # Display details by room (top 10 most affected)
        room_counts = {room: len(warnings) for room, warnings in warnings_by_room.items()}
        top_affected = sorted(room_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        logger.warning(f"\n🏢 Most Affected Rooms (showing top {min(10, len(top_affected))}):")
        for room_name, count in top_affected:
            warnings_list = warnings_by_room[room_name]
            logger.warning(f"\n   📍 {room_name} ({count} missing datasets):")
            
            # Group by period for this room
            periods = defaultdict(list)
            for w in warnings_list:
                periods[w['period']].append(w['test_name'])
            
            for period, tests in periods.items():
                if len(tests) <= 3:
                    test_names = ', '.join([t.split('_')[-2] if '_' in t else t for t in tests])
                else:
                    test_names = f"{len(tests)} tests"
                logger.warning(f"      - {period}: {test_names}")
        
        # Provide diagnostic guidance
        logger.warning("\n💡 Common Causes:")
        logger.warning("   1. Seasonal gaps: Schools often have extended breaks (summer, autumn, holidays)")
        logger.warning("   2. Sensor activation: Some sensors may not have been active in certain periods")
        logger.warning("   3. Filter overlap: Combining period filters with holiday exclusions may remove all data")
        logger.warning("   4. Room usage patterns: Some rooms (e.g., classrooms) are only used during school year")
        
        logger.warning("\n✓ These warnings are informational. Tests with sufficient data completed successfully.")
        logger.warning("="*80 + "\n")


def create_hierarchical_analysis_service(config_path: Optional[Path] = None) -> HierarchicalAnalysisService:
    """Factory function to create a HierarchicalAnalysisService instance."""
    return HierarchicalAnalysisService(config_path=config_path)
