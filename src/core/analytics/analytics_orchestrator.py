"""
Analytics Orchestrator

Orchestrates execution of analytics based on requirements.
Runs missing analytics identified by the validator.
"""

import logging
from typing import Dict, List, Set, Optional, Any, Union, Callable
from pathlib import Path
import pandas as pd
import numpy as np

from src.core.analytics.analytics_tags import (
    AnalyticsTag,
    AnalyticsRequirement,
    AnalyticsCapability,
    ValidationResult
)
from src.core.analytics.analytics_validator import AnalyticsValidator

logger = logging.getLogger(__name__)

# Track missing implementations for CLI warnings
MISSING_IMPLEMENTATIONS: Set[str] = set()

# Import analytics library functions
try:
    from src.core.analytics.ieq.library.metrics import (
        calculate_basic_statistics,
        calculate_extended_statistics,
        calculate_distribution_metrics,
        calculate_temporal_statistics,
        calculate_completeness,
        calculate_quality_score
    )
    METRICS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Metrics library not fully available: {e}")
    METRICS_AVAILABLE = False

try:
    from src.core.analytics.ieq.library.correlations.weather_correlator import (
        calculate_weather_correlations,
        calculate_seasonal_correlations
    )
    WEATHER_CORRELATIONS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Weather correlations not available: {e}")
    WEATHER_CORRELATIONS_AVAILABLE = False

try:
    from src.core.analytics.ieq.RecommendationEngine import RecommendationEngine
    RECOMMENDATIONS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RecommendationEngine not available: {e}")
    RECOMMENDATIONS_AVAILABLE = False

try:
    from src.core.analytics.ieq.SmartRecommendationService import SmartRecommendationService
    SMART_RECOMMENDATIONS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"SmartRecommendationService not available: {e}")
    SMART_RECOMMENDATIONS_AVAILABLE = False


class AnalyticsOrchestrator:
    """
    Orchestrates execution of analytics based on requirements.
    
    Identifies missing analytics and executes them to complete
    the required analytics for report generation.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to analytics configuration
        """
        self.validator = AnalyticsValidator()
        self.config_path = config_path
        
        # Analytics executors registry
        self._tag_executors = self._register_tag_executors()
    
    @staticmethod
    def print_missing_implementations_warning():
        """
        Print CLI warnings for missing or incomplete implementations.
        Should be called after analytics execution to inform users.
        """
        global MISSING_IMPLEMENTATIONS
        
        if MISSING_IMPLEMENTATIONS:
            print("\n" + "="*70)
            print("⚠️  ANALYTICS VALIDATION WARNINGS")
            print("="*70)
            print("\nThe following analytics could not be fully executed:\n")
            
            for idx, warning in enumerate(sorted(MISSING_IMPLEMENTATIONS), 1):
                print(f"  {idx}. {warning}")
            
            print("\n" + "-"*70)
            print("These analytics will be gradually implemented or require:")
            print("  • Additional data (e.g., weather data for correlations)")
            print("  • Hierarchical dataset structure (for spatial analysis)")
            print("  • Portfolio context (for ranking/comparison)")
            print("  • Library modules to be available")
            print("-"*70 + "\n")
            
            # Clear after displaying
            MISSING_IMPLEMENTATIONS.clear()
        
        return len(MISSING_IMPLEMENTATIONS) > 0
    
    @staticmethod
    def get_missing_implementations() -> Set[str]:
        """
        Get the set of missing implementations.
        
        Returns:
            Set of warning messages about missing implementations
        """
        global MISSING_IMPLEMENTATIONS
        return MISSING_IMPLEMENTATIONS.copy()
    
    def ensure_requirements(
        self,
        analysis_results: Any,
        requirement: AnalyticsRequirement,
        dataset: Optional[Any] = None,
        weather_data: Optional[pd.DataFrame] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ensure all requirements are met, running missing analytics if needed.
        
        Args:
            analysis_results: Current analysis results
            requirement: Required analytics
            dataset: Original dataset (for re-analysis)
            weather_data: Weather data (for correlations)
            config: Analytics configuration
        
        Returns:
            Dictionary with status and updated results
        """
        # Extract current capability
        capability = self.validator.extract_capability_from_analysis(analysis_results)
        
        # Validate
        validation = self.validator.validate_requirements(requirement, capability)
        
        if validation.is_valid:
            logger.info("All analytics requirements already met")
            return {
                'status': 'complete',
                'analysis_results': analysis_results,
                'validation': validation.to_dict()
            }
        
        logger.info(
            f"Missing analytics detected: {len(validation.missing_tags)} tags, "
            f"{len(validation.missing_tests)} tests, "
            f"{len(validation.missing_standards)} standards"
        )
        
        # Execute missing analytics
        updated_results = self._execute_missing_analytics(
            analysis_results=analysis_results,
            validation=validation,
            dataset=dataset,
            weather_data=weather_data,
            config=config
        )
        
        return {
            'status': 'updated',
            'analysis_results': updated_results,
            'validation': validation.to_dict(),
            'executed_analytics': {
                'tags': [tag.value for tag in validation.missing_tags],
                'tests': list(validation.missing_tests),
                'standards': list(validation.missing_standards)
            }
        }
    
    def execute_analytics_by_tags(
        self,
        tags: Set[AnalyticsTag],
        dataset: Any,
        analysis_results: Optional[Any] = None,
        weather_data: Optional[pd.DataFrame] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute specific analytics by tags.
        
        Args:
            tags: Set of analytics tags to execute
            dataset: Dataset to analyze
            analysis_results: Existing results to augment (optional)
            weather_data: Weather data (optional)
            config: Analytics configuration (optional)
        
        Returns:
            Analytics results
        """
        results = analysis_results if analysis_results is not None else {}
        
        for tag in tags:
            logger.info(f"Executing analytics: {tag.value}")
            
            executor = self._tag_executors.get(tag)
            if executor:
                try:
                    tag_results = executor(
                        dataset=dataset,
                        existing_results=results,
                        weather_data=weather_data,
                        config=config
                    )
                    
                    # Merge results
                    results = self._merge_results(results, tag_results, tag)
                    
                except Exception as e:
                    logger.error(f"Error executing {tag.value}: {e}")
            else:
                logger.warning(f"No executor registered for tag: {tag.value}")
        
        return results
    
    def execute_tests(
        self,
        test_ids: Set[str],
        dataset: Any,
        analysis_results: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute specific tests.
        
        Args:
            test_ids: Set of test IDs to execute
            dataset: Dataset to analyze
            analysis_results: Existing results to augment (optional)
            config: Analytics configuration (optional)
        
        Returns:
            Updated analysis results with test results
        """
        results = analysis_results if analysis_results is not None else {}
        
        # Import test execution engine
        try:
            from src.core.analytics.test_management_service import TestManagementService
            
            test_service = TestManagementService(config_path=self.config_path)
            
            for test_id in test_ids:
                logger.info(f"Executing test: {test_id}")
                
                try:
                    # Execute single test - placeholder for actual implementation
                    # test_result = test_service.execute_test(test_id=test_id, dataset=dataset)
                    # For now, log that test execution would happen here
                    logger.info(f"Would execute test {test_id} (implementation pending)")
                    
                except Exception as e:
                    logger.error(f"Error executing test {test_id}: {e}")
        
        except ImportError:
            logger.warning("TestManagementService not available")
        
        return results
    
    def execute_standards(
        self,
        standard_ids: Set[str],
        dataset: Any,
        analysis_results: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute specific standards compliance checks.
        
        Args:
            standard_ids: Set of standard IDs to execute
            dataset: Dataset to analyze
            analysis_results: Existing results to augment (optional)
            config: Analytics configuration (optional)
        
        Returns:
            Updated analysis results with standard compliance results
        """
        results = analysis_results if analysis_results is not None else {}
        
        # Import standard execution engine
        try:
            from src.core.analytics.ieq import AnalysisEngine
            
            engine = AnalysisEngine()
            
            for standard_id in standard_ids:
                logger.info(f"Executing standard: {standard_id}")
                
                try:
                    # Execute standard compliance - placeholder for actual implementation
                    # standard_result = engine.evaluate_standard(standard_id=standard_id, dataset=dataset)
                    # For now, log that standard execution would happen here
                    logger.info(f"Would execute standard {standard_id} (implementation pending)")
                    
                except Exception as e:
                    logger.error(f"Error executing standard {standard_id}: {e}")
        
        except ImportError:
            logger.warning("AnalysisEngine not available")
        
        return results
    
    def _execute_missing_analytics(
        self,
        analysis_results: Any,
        validation: ValidationResult,
        dataset: Optional[Any] = None,
        weather_data: Optional[pd.DataFrame] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute all missing analytics.
        
        Args:
            analysis_results: Current results
            validation: Validation result with missing analytics
            dataset: Original dataset
            weather_data: Weather data
            config: Configuration
        
        Returns:
            Updated analysis results
        """
        updated_results = analysis_results
        
        # Execute missing analytics tags
        if validation.missing_tags and dataset:
            tag_results = self.execute_analytics_by_tags(
                tags=validation.missing_tags,
                dataset=dataset,
                analysis_results=updated_results,
                weather_data=weather_data,
                config=config
            )
            updated_results = tag_results
        
        # Execute missing tests
        if validation.missing_tests and dataset:
            test_results = self.execute_tests(
                test_ids=validation.missing_tests,
                dataset=dataset,
                analysis_results=updated_results,
                config=config
            )
            updated_results = test_results
        
        # Execute missing standards
        if validation.missing_standards and dataset:
            standard_results = self.execute_standards(
                standard_ids=validation.missing_standards,
                dataset=dataset,
                analysis_results=updated_results,
                config=config
            )
            updated_results = standard_results
        
        return updated_results
    
    def _register_tag_executors(self) -> Dict[AnalyticsTag, Callable]:
        """
        Register executor functions for each analytics tag.
        
        Returns:
            Dictionary mapping tags to executor functions
        """
        return {
            # Statistics
            AnalyticsTag.STATISTICS_BASIC: self._execute_basic_statistics,
            AnalyticsTag.STATISTICS_DISTRIBUTION: self._execute_distribution_analysis,
            AnalyticsTag.STATISTICS_TRENDS: self._execute_trend_analysis,
            AnalyticsTag.STATISTICS_CORRELATION: self._execute_correlation_analysis,
            
            # Compliance
            AnalyticsTag.COMPLIANCE_OVERALL: self._execute_overall_compliance,
            AnalyticsTag.COMPLIANCE_TEMPORAL: self._execute_temporal_compliance,
            AnalyticsTag.COMPLIANCE_SPATIAL: self._execute_spatial_compliance,
            AnalyticsTag.COMPLIANCE_THRESHOLD: self._execute_threshold_compliance,
            
            # Weather
            AnalyticsTag.WEATHER_TEMPERATURE: self._execute_weather_temperature,
            AnalyticsTag.WEATHER_OUTDOOR_CONDITIONS: self._execute_weather_correlation,
            
            # Recommendations
            AnalyticsTag.RECOMMENDATIONS_HVAC: self._execute_hvac_recommendations,
            AnalyticsTag.RECOMMENDATIONS_VENTILATION: self._execute_ventilation_recommendations,
            AnalyticsTag.RECOMMENDATIONS_OPERATIONAL: self._execute_operational_recommendations,
            AnalyticsTag.RECOMMENDATIONS_SMART: self._execute_smart_recommendations,
            
            # Data Quality
            AnalyticsTag.DATA_QUALITY_COMPLETENESS: self._execute_data_quality_check,
            
            # Performance
            AnalyticsTag.PERFORMANCE_SCORING: self._execute_performance_scoring,
            AnalyticsTag.PERFORMANCE_RANKING: self._execute_performance_ranking,
            
            # Temporal
            AnalyticsTag.TEMPORAL_HOURLY: self._execute_hourly_analysis,
            AnalyticsTag.TEMPORAL_DAILY: self._execute_daily_analysis,
            AnalyticsTag.TEMPORAL_SEASONAL: self._execute_seasonal_analysis,
            
            # Spatial
            AnalyticsTag.SPATIAL_ROOM_LEVEL: self._execute_room_level_analysis,
            AnalyticsTag.SPATIAL_COMPARISON: self._execute_spatial_comparison,
        }
    
    def _merge_results(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any],
        tag: AnalyticsTag
    ) -> Dict[str, Any]:
        """Merge new analytics results into existing results."""
        if isinstance(existing, dict) and isinstance(new, dict):
            existing.update(new)
            return existing
        return new
    
    # Analytics executor implementations
    
    def _execute_basic_statistics(self, dataset, existing_results, **kwargs):
        """Execute basic statistical analysis."""
        logger.debug("Executing basic statistics")
        
        if not METRICS_AVAILABLE:
            MISSING_IMPLEMENTATIONS.add("STATISTICS_BASIC: Metrics library not available")
            logger.warning("⚠️  Metrics library not available for basic statistics")
            return {}
        
        results = {'statistics': {}}
        
        # Extract data from dataset
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            logger.warning("Dataset format not recognized for statistics")
            return results
        
        # Calculate statistics for numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            try:
                if METRICS_AVAILABLE and callable(calculate_basic_statistics):
                    stats = calculate_basic_statistics(df[col].dropna())
                    results['statistics'][col] = stats
            except Exception as e:
                logger.error(f"Error calculating statistics for {col}: {e}")
        
        return results
    
    def _execute_distribution_analysis(self, dataset, existing_results, **kwargs):
        """Execute distribution analysis."""
        logger.debug("Executing distribution analysis")
        
        if not METRICS_AVAILABLE:
            MISSING_IMPLEMENTATIONS.add("STATISTICS_DISTRIBUTION: Metrics library not available")
            logger.warning("⚠️  Metrics library not available for distribution analysis")
            return {}
        
        results = {'distributions': {}}
        
        # Extract data from dataset
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            return results
        
        # Calculate distribution metrics for numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            try:
                if METRICS_AVAILABLE and callable(calculate_distribution_metrics):
                    dist_metrics = calculate_distribution_metrics(df[col].dropna())
                    results['distributions'][col] = dist_metrics
            except Exception as e:
                logger.error(f"Error calculating distribution for {col}: {e}")
        
        return results
    
    def _execute_trend_analysis(self, dataset, existing_results, **kwargs):
        """Execute trend analysis."""
        logger.debug("Executing trend analysis")
        
        if not METRICS_AVAILABLE:
            MISSING_IMPLEMENTATIONS.add("STATISTICS_TRENDS: Temporal statistics not available")
            logger.warning("⚠️  Temporal analysis functions not available")
            return {}
        
        results = {'trends': {}}
        
        # Extract data from dataset
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            return results
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df = df.set_index('timestamp')
            else:
                logger.warning("No timestamp column found for trend analysis")
                return results
        
        # Calculate temporal statistics for numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            try:
                if METRICS_AVAILABLE and callable(calculate_temporal_statistics):
                    temporal_stats = calculate_temporal_statistics(df[col].dropna())
                    results['trends'][col] = temporal_stats
            except Exception as e:
                logger.error(f"Error calculating trends for {col}: {e}")
        
        return results
    
    def _execute_correlation_analysis(self, dataset, existing_results, **kwargs):
        """Execute correlation analysis."""
        logger.debug("Executing correlation analysis")
        
        results = {'correlations': {}}
        
        # Extract data from dataset
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            return results
        
        # Calculate correlation matrix for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            try:
                corr_matrix = df[numeric_cols].corr()
                results['correlations']['matrix'] = corr_matrix.to_dict()
                
                # Find strong correlations (|r| > 0.7)
                strong_correlations = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if pd.notna(corr_val) and isinstance(corr_val, (int, float)) and abs(float(corr_val)) > 0.7:
                            strong_correlations.append({
                                'feature1': corr_matrix.columns[i],
                                'feature2': corr_matrix.columns[j],
                                'correlation': float(corr_val)
                            })
                
                results['correlations']['strong'] = strong_correlations
            except Exception as e:
                logger.error(f"Error calculating correlations: {e}")
        
        return results
    
    def _execute_overall_compliance(self, dataset, existing_results, **kwargs):
        """Execute overall compliance analysis."""
        logger.debug("Executing overall compliance")
        
        results = {'compliance': {'overall': {}}}
        
        try:
            from src.core.analytics.test_management_service import TestManagementService
            test_service = TestManagementService(config_path=self.config_path)
            
            # Execute core compliance tests
            # For now, log placeholder - actual test execution would go here
            logger.info("Overall compliance check initiated")
            results['compliance']['overall'] = {
                'status': 'analyzed',
                'tests_run': 0,
                'note': 'Test execution integration pending'
            }
        except ImportError:
            MISSING_IMPLEMENTATIONS.add("COMPLIANCE_OVERALL: TestManagementService not available")
            logger.warning("⚠️  TestManagementService not available for compliance checks")
        except Exception as e:
            logger.error(f"Error in overall compliance analysis: {e}")
        
        return results
    
    def _execute_temporal_compliance(self, dataset, existing_results, **kwargs):
        """Execute temporal compliance analysis."""
        logger.debug("Executing temporal compliance")
        
        results = {'compliance': {'temporal': {}}}
        
        try:
            # Temporal compliance requires time-based filtering
            logger.info("Temporal compliance check initiated")
            results['compliance']['temporal'] = {
                'hourly': {},
                'daily': {},
                'note': 'Temporal compliance integration pending'
            }
        except Exception as e:
            logger.error(f"Error in temporal compliance: {e}")
        
        return results
    
    def _execute_spatial_compliance(self, dataset, existing_results, **kwargs):
        """Execute spatial compliance analysis."""
        logger.debug("Executing spatial compliance")
        
        results = {'compliance': {'spatial': {}}}
        
        try:
            # Spatial compliance compares across rooms/levels/buildings
            logger.info("Spatial compliance check initiated")
            results['compliance']['spatial'] = {
                'room_level': {},
                'building_level': {},
                'note': 'Spatial compliance integration pending'
            }
        except Exception as e:
            logger.error(f"Error in spatial compliance: {e}")
        
        return results
    
    def _execute_threshold_compliance(self, dataset, existing_results, **kwargs):
        """Execute threshold exceedance analysis."""
        logger.debug("Executing threshold compliance")
        
        config = kwargs.get('config', {})
        results = {'compliance': {'threshold_exceedances': {}}}
        
        try:
            # Extract data from dataset
            if hasattr(dataset, 'data'):
                df = dataset.data
            elif isinstance(dataset, pd.DataFrame):
                df = dataset
            else:
                logger.warning("Dataset format not recognized for threshold compliance")
                return results
            
            # Analyze threshold exceedances for key parameters
            # Common IEQ thresholds (could be from config)
            thresholds = config.get('thresholds', {
                'co2': {'max': 1000, 'unit': 'ppm'},
                'temperature': {'min': 20, 'max': 26, 'unit': '°C'},
                'humidity': {'min': 30, 'max': 70, 'unit': '%'}
            })
            
            threshold_stats = {}
            for param, limits in thresholds.items():
                if param in df.columns:
                    data = df[param].dropna()
                    total_points = len(data)
                    
                    if total_points > 0:
                        stats = {
                            'total_points': total_points,
                            'unit': limits.get('unit', '')
                        }
                        
                        if 'max' in limits:
                            exceedances = data > limits['max']
                            stats['max_threshold'] = limits['max']
                            stats['above_max'] = int(exceedances.sum())
                            stats['above_max_pct'] = float((exceedances.sum() / total_points) * 100)
                        
                        if 'min' in limits:
                            exceedances = data < limits['min']
                            stats['min_threshold'] = limits['min']
                            stats['below_min'] = int(exceedances.sum())
                            stats['below_min_pct'] = float((exceedances.sum() / total_points) * 100)
                        
                        threshold_stats[param] = stats
            
            results['compliance']['threshold_exceedances'] = threshold_stats
            logger.info(f"Threshold compliance calculated for {len(threshold_stats)} parameters")
        
        except Exception as e:
            logger.error(f"Error in threshold compliance: {e}")
        
        return results
    
    def _execute_weather_temperature(self, dataset, existing_results, **kwargs):
        """Execute weather temperature correlation."""
        logger.debug("Executing weather temperature correlation")
        
        weather_data = kwargs.get('weather_data')
        if weather_data is None:
            MISSING_IMPLEMENTATIONS.add("WEATHER_TEMPERATURE: Weather data not provided")
            logger.warning("⚠️  Weather data not provided for temperature correlation")
            return {}
        
        if not WEATHER_CORRELATIONS_AVAILABLE:
            MISSING_IMPLEMENTATIONS.add("WEATHER_TEMPERATURE: Weather correlations library not available")
            logger.warning("⚠️  Weather correlations library not available")
            return {}
        
        results = {'weather_correlation': {'temperature': {}}}
        
        # Extract data from dataset
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            return results
        
        try:
            # Calculate weather correlations
            correlations = calculate_weather_correlations(df, weather_data)
            results['weather_correlation']['temperature'] = correlations
        except Exception as e:
            logger.error(f"Error calculating weather temperature correlation: {e}")
        
        return results
    
    def _execute_weather_correlation(self, dataset, existing_results, **kwargs):
        """Execute weather correlation analysis."""
        logger.debug("Executing weather correlation")
        
        weather_data = kwargs.get('weather_data')
        if weather_data is None:
            MISSING_IMPLEMENTATIONS.add("WEATHER_CORRELATION: Weather data not provided")
            logger.warning("⚠️  Weather data not provided for correlation analysis")
            return {}
        
        if not WEATHER_CORRELATIONS_AVAILABLE:
            MISSING_IMPLEMENTATIONS.add("WEATHER_CORRELATION: Weather correlations library not available")
            logger.warning("⚠️  Weather correlations library not available")
            return {}
        
        results = {'weather_correlation': {}}
        
        # Extract data from dataset  
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            return results
        
        try:
            # Calculate seasonal correlations
            seasonal = calculate_seasonal_correlations(df, weather_data)
            results['weather_correlation']['seasonal'] = seasonal
        except Exception as e:
            logger.error(f"Error calculating weather correlations: {e}")
        
        return results
    
    def _execute_hvac_recommendations(self, dataset, existing_results, **kwargs):
        """Execute HVAC recommendations."""
        logger.debug("Executing HVAC recommendations")
        
        if not RECOMMENDATIONS_AVAILABLE:
            MISSING_IMPLEMENTATIONS.add("RECOMMENDATIONS_HVAC: RecommendationEngine not available")
            logger.warning("⚠️  RecommendationEngine not available for HVAC recommendations")
            return {}
        
        results = {'recommendations': {'hvac': []}}
        
        try:
            # RecommendationEngine requires Room and RoomAnalysis objects
            # For now, log that proper integration is needed
            MISSING_IMPLEMENTATIONS.add("RECOMMENDATIONS_HVAC: Requires Room and RoomAnalysis objects")
            logger.info("HVAC recommendations require Room and RoomAnalysis object integration")
        except Exception as e:
            logger.error(f"Error generating HVAC recommendations: {e}")
        
        return results
    
    def _execute_ventilation_recommendations(self, dataset, existing_results, **kwargs):
        """Execute ventilation recommendations."""
        logger.debug("Executing ventilation recommendations")
        
        if not RECOMMENDATIONS_AVAILABLE:
            MISSING_IMPLEMENTATIONS.add("RECOMMENDATIONS_VENTILATION: RecommendationEngine not available")
            logger.warning("⚠️  RecommendationEngine not available for ventilation recommendations")
            return {}
        
        results = {'recommendations': {'ventilation': []}}
        
        try:
            # RecommendationEngine requires Room and RoomAnalysis objects
            # For now, log that proper integration is needed
            MISSING_IMPLEMENTATIONS.add("RECOMMENDATIONS_VENTILATION: Requires Room and RoomAnalysis objects")
            logger.info("Ventilation recommendations require Room and RoomAnalysis object integration")
        except Exception as e:
            logger.error(f"Error generating ventilation recommendations: {e}")
        
        return results
    
    def _execute_operational_recommendations(self, dataset, existing_results, **kwargs):
        """Execute operational recommendations."""
        logger.debug("Executing operational recommendations")
        
        if not RECOMMENDATIONS_AVAILABLE:
            MISSING_IMPLEMENTATIONS.add("RECOMMENDATIONS_OPERATIONAL: RecommendationEngine not available")
            logger.warning("⚠️  RecommendationEngine not available for operational recommendations")
            return {}
        
        results = {'recommendations': {'operational': []}}
        
        try:
            # RecommendationEngine requires Room and RoomAnalysis objects
            # For now, log that proper integration is needed
            MISSING_IMPLEMENTATIONS.add("RECOMMENDATIONS_OPERATIONAL: Requires Room and RoomAnalysis objects")
            logger.info("Operational recommendations require Room and RoomAnalysis object integration")
        except Exception as e:
            logger.error(f"Error generating operational recommendations: {e}")
        
        return results
    
    def _execute_smart_recommendations(self, dataset, existing_results, **kwargs):
        """Execute smart/ML-based recommendations."""
        logger.debug("Executing smart recommendations")
        
        if not SMART_RECOMMENDATIONS_AVAILABLE:
            MISSING_IMPLEMENTATIONS.add("RECOMMENDATIONS_SMART: SmartRecommendationService not available")
            logger.warning("⚠️  SmartRecommendationService not available")
            return {}
        
        results = {'recommendations': {'smart': []}}
        
        try:
            service = SmartRecommendationService()
            # Generate smart recommendations based on portfolio analysis
            if hasattr(existing_results, 'get'):
                building_id = existing_results.get('building_id')
                if building_id:
                    recs = service.generate_building_recommendations(building_id, existing_results)
                    results['recommendations']['smart'] = recs
        except Exception as e:
            logger.error(f"Error generating smart recommendations: {e}")
        
        return results
    
    def _execute_data_quality_check(self, dataset, existing_results, **kwargs):
        """Execute data quality checks."""
        logger.debug("Executing data quality check")
        
        results = {'data_quality': {}}
        
        # Extract data from dataset
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            MISSING_IMPLEMENTATIONS.add("DATA_QUALITY: Dataset format not recognized")
            return results
        
        try:
            total_cells = df.size
            non_null_cells = df.count().sum()
            completeness = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0
            
            # Calculate per-column quality
            column_quality = {}
            for col in df.columns:
                col_completeness = (df[col].count() / len(df)) * 100 if len(df) > 0 else 0
                column_quality[col] = {
                    'completeness': float(col_completeness),
                    'missing_count': int(df[col].isna().sum()),
                    'total_count': len(df)
                }
            
            results['data_quality'] = {
                'overall_completeness': float(completeness),
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': column_quality
            }
            
            # Use library function if available
            if METRICS_AVAILABLE:
                for col in df.select_dtypes(include=[np.number]).columns:
                    if callable(calculate_quality_score):
                        quality_score = calculate_quality_score(df[col])
                        if col in column_quality:
                            column_quality[col]['quality_score'] = quality_score
        
        except Exception as e:
            logger.error(f"Error calculating data quality: {e}")
        
        return results
    
    def _execute_performance_scoring(self, dataset, existing_results, **kwargs):
        """Execute performance scoring."""
        logger.debug("Executing performance scoring")
        
        results = {'performance': {'score': 0, 'factors': {}}}
        
        try:
            # Calculate performance score based on compliance and data quality
            if hasattr(existing_results, 'get'):
                compliance = existing_results.get('compliance', {})
                data_quality = existing_results.get('data_quality', {})
                
                # Simple scoring algorithm
                score = 0
                factors = {}
                
                # Data quality factor (0-40 points)
                if 'overall_completeness' in data_quality:
                    dq_score = min(40, data_quality['overall_completeness'] * 0.4)
                    score += dq_score
                    factors['data_quality'] = float(dq_score)
                
                # Compliance factor (0-60 points) - placeholder
                factors['compliance'] = 0  # Would calculate from actual compliance results
                
                results['performance']['score'] = float(score)
                results['performance']['factors'] = factors
                results['performance']['grade'] = self._score_to_grade(score)
        
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
        
        return results
    
    def _execute_performance_ranking(self, dataset, existing_results, **kwargs):
        """Execute performance ranking."""
        logger.debug("Executing performance ranking")
        
        results = {'performance': {'ranking': {}}}
        
        try:
            # Ranking requires multiple rooms/buildings for comparison
            MISSING_IMPLEMENTATIONS.add("PERFORMANCE_RANKING: Multi-entity comparison not implemented")
            logger.info("Performance ranking requires portfolio-level analysis")
            results['performance']['ranking'] = {
                'note': 'Requires portfolio context for ranking',
                'current_score': existing_results.get('performance', {}).get('score', 0) if hasattr(existing_results, 'get') else 0
            }
        except Exception as e:
            logger.error(f"Error in performance ranking: {e}")
        
        return results
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _execute_hourly_analysis(self, dataset, existing_results, **kwargs):
        """Execute hourly pattern analysis."""
        logger.debug("Executing hourly analysis")
        
        results = {'temporal': {'hourly': {}}}
        
        # Extract data from dataset
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            return results
        
        try:
            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'timestamp' in df.columns:
                    df = df.set_index('timestamp')
                else:
                    logger.warning("No timestamp column for hourly analysis")
                    return results
            
            # Group by hour and calculate stats
            hourly_stats = {}
            for col in df.select_dtypes(include=[np.number]).columns:
                hourly = df[col].groupby(df.index.hour).agg(['mean', 'std', 'min', 'max'])
                hourly_stats[col] = hourly.to_dict('index')
            
            results['temporal']['hourly'] = hourly_stats
        
        except Exception as e:
            logger.error(f"Error in hourly analysis: {e}")
        
        return results
    
    def _execute_daily_analysis(self, dataset, existing_results, **kwargs):
        """Execute daily pattern analysis."""
        logger.debug("Executing daily analysis")
        
        results = {'temporal': {'daily': {}}}
        
        # Extract data from dataset
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            return results
        
        try:
            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'timestamp' in df.columns:
                    df = df.set_index('timestamp')
                else:
                    logger.warning("No timestamp column for daily analysis")
                    return results
            
            # Group by date and calculate stats
            daily_stats = {}
            for col in df.select_dtypes(include=[np.number]).columns:
                daily = df[col].groupby(df.index.date).agg(['mean', 'std', 'min', 'max'])
                # Convert to serializable format
                daily_stats[col] = {
                    str(date): stats.to_dict()
                    for date, stats in daily.iterrows()
                }
            
            results['temporal']['daily'] = daily_stats
        
        except Exception as e:
            logger.error(f"Error in daily analysis: {e}")
        
        return results
    
    def _execute_seasonal_analysis(self, dataset, existing_results, **kwargs):
        """Execute seasonal pattern analysis."""
        logger.debug("Executing seasonal analysis")
        
        results = {'temporal': {'seasonal': {}}}
        
        # Extract data from dataset
        if hasattr(dataset, 'data'):
            df = dataset.data
        elif isinstance(dataset, pd.DataFrame):
            df = dataset
        else:
            return results
        
        try:
            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'timestamp' in df.columns:
                    df = df.set_index('timestamp')
                else:
                    logger.warning("No timestamp column for seasonal analysis")
                    return results
            
            # Define seasons
            def get_season(month):
                if month in [12, 1, 2]:
                    return 'winter'
                elif month in [3, 4, 5]:
                    return 'spring'
                elif month in [6, 7, 8]:
                    return 'summer'
                else:
                    return 'fall'
            
            # Group by season and calculate stats
            seasonal_stats = {}
            df_with_season = df.copy()
            df_with_season['season'] = df_with_season.index.month.map(get_season)
            
            for col in df.select_dtypes(include=[np.number]).columns:
                season_groups = df_with_season.groupby('season')[col]
                seasonal_stats[col] = {
                    season: {
                        'mean': float(group.mean()),
                        'std': float(group.std()),
                        'min': float(group.min()),
                        'max': float(group.max()),
                        'count': int(len(group))
                    }
                    for season, group in season_groups
                }
            
            results['temporal']['seasonal'] = seasonal_stats
            logger.info(f"Seasonal analysis completed for {len(seasonal_stats)} parameters")
        
        except Exception as e:
            logger.error(f"Error in seasonal analysis: {e}")
        
        return results
    
    def _execute_room_level_analysis(self, dataset, existing_results, **kwargs):
        """Execute room-level analysis."""
        logger.debug("Executing room-level analysis")
        
        results = {'spatial': {'room_level': {}}}
        
        try:
            # Room-level analysis requires hierarchical dataset
            if hasattr(dataset, 'rooms'):
                room_stats = {}
                for room in dataset.rooms:
                    room_stats[room.id] = {
                        'name': room.name,
                        'analyzed': True
                    }
                results['spatial']['room_level'] = room_stats
            else:
                MISSING_IMPLEMENTATIONS.add("SPATIAL_ROOM_LEVEL: Hierarchical dataset required")
                logger.info("Room-level analysis requires hierarchical dataset structure")
        
        except Exception as e:
            logger.error(f"Error in room-level analysis: {e}")
        
        return results
    
    def _execute_spatial_comparison(self, dataset, existing_results, **kwargs):
        """Execute spatial comparison."""
        logger.debug("Executing spatial comparison")
        
        results = {'spatial': {'comparison': {}}}
        
        try:
            # Spatial comparison requires multiple entities
            MISSING_IMPLEMENTATIONS.add("SPATIAL_COMPARISON: Multi-entity comparison not implemented")
            logger.info("Spatial comparison requires multiple rooms/buildings")
            results['spatial']['comparison'] = {
                'note': 'Requires multiple entities for comparison',
                'available_entities': 0
            }
        
        except Exception as e:
            logger.error(f"Error in spatial comparison: {e}")
        
        return results


__all__ = ['AnalyticsOrchestrator']
