"""
Unified IEQ Analytics Engine

Consolidated module providing:
- Unified filtering (time-based, opening hours, holidays)
- Rule evaluation (user rules, EN16798 standards)
- Core analytics for modular reporting
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from pathlib import Path
import logging
import yaml
import json
from enum import Enum

logger = logging.getLogger(__name__)

import holidays


class AnalysisType(Enum):
    """Types of analysis supported."""
    USER_RULES = "user_rules"
    EN16798_COMPLIANCE = "en16798_compliance"
    BASIC_STATISTICS = "basic_statistics"
    DATA_QUALITY = "data_quality"


class RuleType(Enum):
    """Types of rules supported."""
    BIDIRECTIONAL = "bidirectional"
    UNIDIRECTIONAL_ASCENDING = "unidirectional_ascending"
    UNIDIRECTIONAL_DESCENDING = "unidirectional_descending"
    COMPLEX = "complex"


@dataclass
class AnalysisResult:
    """Standardized analysis result."""
    parameter: str
    rule_name: str
    compliance_rate: float
    total_points: int
    compliant_points: int
    violations: List[Dict[str, Any]]
    statistics: Dict[str, float]
    recommendations: List[str]
    metadata: Dict[str, Any]


class UnifiedFilterProcessor:
    """Unified processor for all time-based filtering."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, years: Optional[List[int]] = None):
        """Initialize with configuration."""
        self.config = config or {}
        self.periods = self.config.get('periods', {})
        self.filters = self.config.get('filters', {})
        self.holidays_config = self.config.get('holidays', {})
        self.holiday_cache = {}
        self.years = years or [datetime.now().year]
        
        # Default configurations
        self.default_opening_hours = [8, 9, 10, 11, 12, 13, 14, 15]
        self._load_default_periods()
        self._load_default_filters()
    
    def _load_default_periods(self):
        """Load default period definitions."""
        if not self.periods:
            self.periods = {
                'all_year': {'months': list(range(1, 13))},
                'spring': {'months': [3, 4, 5]},
                'summer': {'months': [6, 7, 8]},
                'autumn': {'months': [9, 10, 11]},
                'winter': {'months': [12, 1, 2]},
            }
    
    def _load_default_filters(self):
        """Load default filter definitions."""
        if not self.filters:
            self.filters = {
                'opening_hours': {
                    'hours': self.default_opening_hours,
                    'weekdays_only': True,
                    'exclude_holidays': True
                },
                'school_opening_hours': {
                    'hours': self.default_opening_hours,
                    'weekdays_only': True,
                    'exclude_holidays': True
                },
                'all_hours': {
                    'hours': list(range(24)),
                    'weekdays_only': False,
                    'exclude_holidays': False
                },
                'weekends_only': {
                    'hours': list(range(24)),
                    'weekdays_only': False,
                    'weekends_only': True,
                    'exclude_holidays': False
                },
                'outside_hours': {
                    'exclude_opening_hours': True,
                    'include_weekends': True,
                    'include_holidays': True
                }
            }
    
    def apply_filter(
        self, 
        df: pd.DataFrame, 
        filter_name: str = 'all_hours',
        period_name: str = 'all_year'
    ) -> pd.DataFrame:
        """
        Apply time-based filter to DataFrame.
        
        Args:
            df: DataFrame with datetime index
            filter_name: Name of filter to apply
            period_name: Name of period to apply
            
        Returns:
            Filtered DataFrame
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return df
        
        # Apply period filter first
        filtered_df = self._apply_period_filter(df, period_name)
        
        # Apply time filter
        filtered_df = self._apply_time_filter(filtered_df, filter_name)
        
        return filtered_df
    
    def _apply_period_filter(self, df: pd.DataFrame, period_name: str) -> pd.DataFrame:
        """Apply period-based filtering."""
        if period_name == 'all_year' or period_name not in self.periods:
            return df
        
        period_config = self.periods[period_name]
        months = period_config.get('months', [])
        
        if months:
            # Ensure index is datetime
            df.index = pd.to_datetime(df.index)
            return df[df.index.month.isin(months)]
        
        return df
    
    def _apply_time_filter(self, df: pd.DataFrame, filter_name: str) -> pd.DataFrame:
        """Apply time-based filtering."""
        if filter_name == 'all_hours' or filter_name not in self.filters:
            return df
        
        filter_config = self.filters[filter_name]
        filtered_df = df.copy()
        # Ensure index is datetime on filtered_df
        filtered_df.index = pd.to_datetime(filtered_df.index)
        
        # Handle special outside_hours filter
        if filter_config.get('exclude_opening_hours', False):
            opening_hours = self.default_opening_hours
            outside_hours = [h for h in range(24) if h not in opening_hours]
            mask = filtered_df.index.hour.isin(outside_hours)
            
            if filter_config.get('include_weekends', True):
                mask |= filtered_df.index.weekday >= 5
            
            if filter_config.get('include_holidays', True):
                holiday_mask = self._get_holiday_mask(filtered_df)
                mask |= holiday_mask
            
            return filtered_df[mask]
        
        # Regular hour filtering
        hours = filter_config.get('hours', list(range(24)))
        filtered_df = filtered_df[filtered_df.index.hour.isin(hours)]
        
        # Weekday filtering
        if filter_config.get('weekdays_only', False):
            if isinstance(filtered_df.index, pd.DatetimeIndex):
                filtered_df = filtered_df[filtered_df.index.weekday < 5]
        elif filter_config.get('weekends_only', False):
            if isinstance(filtered_df.index, pd.DatetimeIndex):
                filtered_df = filtered_df[filtered_df.index.weekday >= 5]
        
        # Holiday filtering
        if filter_config.get('exclude_holidays', False):
            holiday_mask = self._get_holiday_mask(filtered_df)
            filtered_df = filtered_df[~holiday_mask]
        
        return filtered_df
    
    def _get_holiday_mask(self, df: pd.DataFrame) -> pd.Series:
        """Get boolean mask for holiday dates."""
        # Extract years from the DataFrame to get holidays for the actual data period
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return pd.Series([False] * len(df), index=df.index)
        
        df.index = pd.to_datetime(df.index)
        data_years = sorted(df.index.year.unique().tolist())
        holiday_dates = self._get_holiday_dates(data_years)
        
        if not holiday_dates:
            return pd.Series([False] * len(df), index=df.index)
        
        mask = pd.Series([False] * len(df), index=df.index)
        
        for holiday_date in holiday_dates:
            if isinstance(holiday_date, str):
                try:
                    holiday_date = pd.to_datetime(holiday_date).date()
                except:
                    continue
            
            daily_mask = df.index.date == holiday_date
            mask |= daily_mask
        
        return mask
    
    def _get_holiday_dates(self, data_years: Optional[List[int]] = None) -> List[date]:
        """Get list of holiday dates for the specified years."""
        # Use data years if provided, otherwise use configured years or current year
        if data_years is not None:
            target_years = data_years
        elif self.years:
            target_years = self.years
        else:
            target_years = [datetime.now().year]
        
        # Create cache key from all years
        cache_key = "_".join(map(str, sorted(target_years)))
        
        if cache_key not in self.holiday_cache:
            holiday_dates = []
            
            # Get Danish holidays if available
            if holidays is not None:
                try:
                    dk_holidays = holidays.country_holidays(self.holidays_config.get('country', 'DK'), years=target_years)
                    holiday_dates.extend(list(dk_holidays.keys()))
                except:
                    pass
            
            # Add custom holidays from config
            custom_holidays = self.holidays_config.get('custom_holidays', [])
            for holiday in custom_holidays:
                try:
                    start_date = pd.to_datetime(holiday['start_date']).date()
                    end_date = holiday.get('end_date')
                    
                    if end_date:
                        end_date = pd.to_datetime(end_date).date()
                        current_date = start_date
                        while current_date <= end_date:
                            # Only include holidays that fall within target years
                            if current_date.year in target_years:
                                holiday_dates.append(current_date)
                            current_date += timedelta(days=1)
                    else:
                        # Only include holidays that fall within target years
                        if start_date.year in target_years:
                            holiday_dates.append(start_date)
                except:
                    continue
            
            self.holiday_cache[cache_key] = holiday_dates
        
        return self.holiday_cache[cache_key]


class UnifiedRuleEngine:
    """Unified rule engine for user rules and EN16798 standards."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with configuration."""
        self.config = config or {}
        self.rules = self.config.get('rules', {})
        self.analytics = self.config.get('analytics', {})
        self.filter_processor = UnifiedFilterProcessor(config)
    
    def evaluate_rule(
        self,
        df: pd.DataFrame,
        rule_name: str,
        rule_config: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Evaluate a single rule against data.
        
        Args:
            df: DataFrame with IEQ data
            rule_name: Name of the rule
            rule_config: Rule configuration (if not in self.rules)
            
        Returns:
            AnalysisResult with evaluation results
        """
        # Get rule configuration
        if rule_config is None:
            rule_config = self.rules.get(rule_name) or self.analytics.get(rule_name)
        
        if not rule_config:
            raise ValueError(f"Rule '{rule_name}' not found in configuration")
        
        # Apply filters
        filter_name = rule_config.get('filter', 'all_hours')
        period_name = rule_config.get('period', 'all_year')
        filtered_df = self.filter_processor.apply_filter(df, filter_name, period_name)
        
        if filtered_df.empty:
            return self._empty_result(rule_name, rule_config)
        
        # Find data column
        parameter = rule_config.get('feature') or rule_config.get('parameter')
        if parameter is None:
            return self._empty_result(rule_name, rule_config, "No parameter specified in rule configuration")
        
        # Ensure parameter is a string
        if not isinstance(parameter, str):
            return self._empty_result(rule_name, rule_config, f"Parameter must be a string, got {type(parameter).__name__}")
        
        # At this point parameter is guaranteed to be a string
        # Cast to str to satisfy type checker (parameter is already verified to be str above)
        data_column = self._find_data_column(filtered_df, str(parameter))
        
        if data_column is None:
            return self._empty_result(rule_name, rule_config, f"Parameter '{parameter}' not found")
        
        # Get clean data
        clean_data = filtered_df[data_column].dropna()
        if clean_data.empty:
            return self._empty_result(rule_name, rule_config, "No valid data points")
        
        # Evaluate based on rule type
        rule_type = self._determine_rule_type(rule_config)
        
        if rule_type == RuleType.BIDIRECTIONAL:
            compliance_series = self._evaluate_bidirectional_rule(clean_data, rule_config)
        elif rule_type == RuleType.UNIDIRECTIONAL_ASCENDING:
            compliance_series = self._evaluate_unidirectional_rule(clean_data, rule_config, ascending=True)
        elif rule_type == RuleType.UNIDIRECTIONAL_DESCENDING:
            compliance_series = self._evaluate_unidirectional_rule(clean_data, rule_config, ascending=False)
        elif rule_type == RuleType.COMPLEX:
            compliance_series = self._evaluate_complex_rule(filtered_df, rule_config)
        else:
            return self._empty_result(rule_name, rule_config, "Unknown rule type")
        
        # Calculate results
        total_points = len(compliance_series)
        compliant_points = compliance_series.sum()
        compliance_rate = (compliant_points / total_points * 100) if total_points > 0 else 0
        
        # Find violations
        violations = self._find_violations(clean_data, compliance_series, rule_config)
        
        # Calculate statistics
        statistics = {
            'mean': float(clean_data.mean()),
            'std': float(clean_data.std()),
            'min': float(clean_data.min()),
            'max': float(clean_data.max()),
            'median': float(clean_data.median()),
            'p95': float(clean_data.quantile(0.95)),
            'p05': float(clean_data.quantile(0.05))
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(rule_config, statistics, compliance_rate)
        
        # Metadata
        metadata = {
            'rule_type': rule_type.value,
            'filter_applied': filter_name,
            'period_applied': period_name,
            'data_column': data_column,
            'original_data_points': len(df),
            'filtered_data_points': len(filtered_df),
            'valid_data_points': len(clean_data)
        }
        
        return AnalysisResult(
            parameter=parameter,
            rule_name=rule_name,
            compliance_rate=compliance_rate,
            total_points=total_points,
            compliant_points=compliant_points,
            violations=violations,
            statistics=statistics,
            recommendations=recommendations,
            metadata=metadata
        )
    
    def _determine_rule_type(self, rule_config: Dict[str, Any]) -> RuleType:
        """Determine the type of rule from configuration."""
        if 'rule' in rule_config:
            return RuleType.COMPLEX
        elif 'mode' in rule_config:
            mode = rule_config['mode']
            if mode == 'bidirectional':
                return RuleType.BIDIRECTIONAL
            elif mode == 'unidirectional_ascending':
                return RuleType.UNIDIRECTIONAL_ASCENDING
            elif mode == 'unidirectional_descending':
                return RuleType.UNIDIRECTIONAL_DESCENDING
        elif 'limits' in rule_config:
            return RuleType.BIDIRECTIONAL
        elif 'limit' in rule_config:
            return RuleType.UNIDIRECTIONAL_ASCENDING
        
        return RuleType.COMPLEX
    
    def _find_data_column(self, df: pd.DataFrame, parameter: str) -> Optional[str]:
        """Find matching data column for parameter."""
        if not parameter:
            return None
        
        # Direct match
        if parameter in df.columns:
            return parameter
        
        # Case-insensitive partial match
        parameter_lower = parameter.lower()
        for col in df.columns:
            if parameter_lower in col.lower():
                return col
        
        # Common aliases
        aliases = {
            'temperature': ['temp', 'temperature_c', 'temp_c', 'air_temperature'],
            'humidity': ['rh', 'relative_humidity', 'humidity_percent', 'humidity_rh'],
            'co2': ['co2_ppm', 'carbon_dioxide', 'co2_concentration'],
        }
        
        if parameter_lower in aliases:
            for alias in aliases[parameter_lower]:
                for col in df.columns:
                    if alias.lower() in col.lower():
                        return col
        
        return None
    
    def _evaluate_bidirectional_rule(
        self, 
        data: pd.Series, 
        rule_config: Dict[str, Any]
    ) -> pd.Series:
        """Evaluate bidirectional rules (min/max limits)."""
        limits = rule_config.get('limits', {})
        lower = limits.get('lower')
        upper = limits.get('upper')
        
        if lower is not None and upper is not None:
            return (data >= lower) & (data <= upper)
        elif lower is not None:
            return data >= lower
        elif upper is not None:
            return data <= upper
        else:
            return pd.Series([True] * len(data), index=data.index)
    
    def _evaluate_unidirectional_rule(
        self, 
        data: pd.Series, 
        rule_config: Dict[str, Any],
        ascending: bool = True
    ) -> pd.Series:
        """Evaluate unidirectional rules (single threshold)."""
        limit = rule_config.get('limit')
        if limit is None:
            return pd.Series([True] * len(data), index=data.index)
        
        if ascending:
            return data <= limit
        else:
            return data >= limit
    
    def _evaluate_complex_rule(
        self, 
        df: pd.DataFrame, 
        rule_config: Dict[str, Any]
    ) -> pd.Series:
        """Evaluate complex rules with logical operators."""
        rule = rule_config.get('rule', {})
        if not rule:
            return pd.Series([True] * len(df), index=df.index)
        
        # Simple implementation for complex rules
        # This would need a full JSON Logic implementation for production
        parameter = rule_config.get('parameter')
        data_column = self._find_data_column(df, str(parameter))
        
        if data_column is None:
            return pd.Series([False] * len(df), index=df.index)
        
        data = df[data_column].dropna()
        
        # Handle simple operators
        if '<=' in rule:
            threshold = rule['<='][1]
            return data <= threshold
        elif '>=' in rule:
            threshold = rule['>='][1]
            return data >= threshold
        elif 'and' in rule:
            # Handle AND conditions
            results = pd.Series([True] * len(data), index=data.index)
            for condition in rule['and']:
                if '>=' in condition:
                    threshold = condition['>='][1]
                    results &= (data >= threshold)
                elif '<=' in condition:
                    threshold = condition['<='][1]
                    results &= (data <= threshold)
            return results
        
        return pd.Series([True] * len(data), index=data.index)
    
    def _find_violations(
        self, 
        data: pd.Series, 
        compliance: pd.Series, 
        rule_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find and categorize violations."""
        violations = []
        violation_data = data[~compliance]
        
        for timestamp, value in violation_data.items():
            if not isinstance(timestamp, (datetime, pd.Timestamp)):
                try:
                    timestamp = pd.to_datetime(str(timestamp))
                except (ValueError, TypeError):
                    timestamp = str(timestamp)
            
            # Convert timestamp to string format
            if hasattr(timestamp, 'isoformat') and not isinstance(timestamp, str):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp)
            
            violation = {
                'timestamp': timestamp_str,
                'value': float(value),
                'parameter': rule_config.get('feature') or rule_config.get('parameter')
            }
            
            # Add violation type based on rule type
            limits = rule_config.get('limits', {})
            limit = rule_config.get('limit')
            
            if limits:
                lower = limits.get('lower')
                upper = limits.get('upper')
                if lower is not None and value < lower:
                    violation['type'] = 'below_minimum'
                    violation['deviation'] = lower - value
                elif upper is not None and value > upper:
                    violation['type'] = 'above_maximum'
                    violation['deviation'] = value - upper
            elif limit is not None:
                mode = rule_config.get('mode', 'unidirectional_ascending')
                if mode == 'unidirectional_ascending' and value > limit:
                    violation['type'] = 'above_limit'
                    violation['deviation'] = value - limit
                elif mode == 'unidirectional_descending' and value < limit:
                    violation['type'] = 'below_limit'
                    violation['deviation'] = limit - value
            
            violations.append(violation)
        
        return violations
    
    def _generate_recommendations(
        self, 
        rule_config: Dict[str, Any], 
        statistics: Dict[str, float], 
        compliance_rate: float
    ) -> List[str]:
        """Generate recommendations based on rule evaluation."""
        recommendations = []
        parameter = rule_config.get('feature') or rule_config.get('parameter', 'parameter')
        
        if compliance_rate < 50:
            recommendations.append(f"Critical: {parameter} compliance is very low ({compliance_rate:.1f}%). Immediate action required.")
        elif compliance_rate < 70:
            recommendations.append(f"Poor: {parameter} compliance is below acceptable levels ({compliance_rate:.1f}%).")
        elif compliance_rate < 85:
            recommendations.append(f"Fair: {parameter} compliance could be improved ({compliance_rate:.1f}%).")
        else:
            recommendations.append(f"Good: {parameter} compliance is acceptable ({compliance_rate:.1f}%).")
        
        # Parameter-specific recommendations
        if parameter.lower() == 'temperature':
            if statistics['std'] > 3.0:
                recommendations.append("High temperature variation detected. Check HVAC control stability.")
        elif parameter.lower() == 'co2':
            if statistics['max'] > 1500:
                recommendations.append("Very high CO2 levels detected. Check ventilation rates and occupancy.")
        elif parameter.lower() == 'humidity':
            if statistics['std'] > 15.0:
                recommendations.append("High humidity variation detected. Check moisture control systems.")
        
        return recommendations
    
    def _empty_result(
        self, 
        rule_name: str, 
        rule_config: Dict[str, Any], 
        reason: str = "No data available"
    ) -> AnalysisResult:
        """Create empty result for failed evaluations."""
        parameter = rule_config.get('feature') or rule_config.get('parameter', 'unknown')
        
        return AnalysisResult(
            parameter=parameter,
            rule_name=rule_name,
            compliance_rate=0.0,
            total_points=0,
            compliant_points=0,
            violations=[],
            statistics={},
            recommendations=[reason],
            metadata={'error': reason}
        )


class UnifiedAnalyticsEngine:
    """Main analytics engine for modular reporting."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize analytics engine."""
        self.config = {}
        self.rule_engine = None
        self.filter_processor = None
        
        if config_path and config_path.exists():
            self._load_config(config_path)
        
        self._initialize_processors()
    
    def _load_config(self, config_path: Path):
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() == '.json':
                    self.config = json.load(f)
                else:
                    self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            self.config = {}
    
    def _initialize_processors(self):
        """Initialize processing components."""
        self.rule_engine = UnifiedRuleEngine(self.config)
        self.filter_processor = UnifiedFilterProcessor(self.config)
    
    def analyze_room_data(
        self,
        df: pd.DataFrame,
        room_id: str,
        analysis_types: Optional[List[AnalysisType]] = None,
        rules_to_evaluate: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of room data.
        
        Args:
            df: DataFrame with IEQ data
            room_id: Room identifier
            analysis_types: Types of analysis to perform
            rules_to_evaluate: Specific rules to evaluate
            
        Returns:
            Comprehensive analysis results
        """
        if analysis_types is None:
            analysis_types = [AnalysisType.BASIC_STATISTICS, AnalysisType.DATA_QUALITY]
        
        results = {
            'room_id': room_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'data_period': self._get_data_period(df),
            'analysis_types': [at.value for at in analysis_types]
        }
        
        # Basic statistics
        if AnalysisType.BASIC_STATISTICS in analysis_types:
            results['basic_statistics'] = self._calculate_basic_statistics(df)
        
        # Data quality
        if AnalysisType.DATA_QUALITY in analysis_types:
            results['data_quality'] = self._analyze_data_quality(df)
        
        # User rules evaluation
        if AnalysisType.USER_RULES in analysis_types:
            results['user_rules'] = self._evaluate_user_rules(df, rules_to_evaluate)
        
        # EN16798 compliance
        if AnalysisType.EN16798_COMPLIANCE in analysis_types:
            results['en16798_compliance'] = self._evaluate_en16798_rules(df)
        
        return results
    
    def _get_data_period(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get data period information."""
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return {}
        
        start_time = df.index.min()
        end_time = df.index.max()
        duration = end_time - start_time
        
        return {
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
            'duration_days': duration.days,
            'total_points': len(df)
        }
    
    def _calculate_basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for numeric columns."""
        stats = {}
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            clean_data = df[col].dropna()
            if len(clean_data) > 0:
                stats[col] = {
                    'count': len(clean_data),
                    'mean': float(clean_data.mean()),
                    'std': float(clean_data.std()),
                    'min': float(clean_data.min()),
                    'max': float(clean_data.max()),
                    'median': float(clean_data.median()),
                    'q25': float(clean_data.quantile(0.25)),
                    'q75': float(clean_data.quantile(0.75))
                }
        
        return stats
    
    def _analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data quality metrics."""
        if df.empty:
            return {'overall_score': 0.0, 'total_records': 0}
        
        quality_metrics = {
            'total_records': len(df),
            'completeness': {},
            'missing_periods': [],
            'overall_score': 0.0
        }
        
        # Calculate completeness for each column
        for col in df.columns:
            non_null_count = df[col].count()
            completeness = (non_null_count / len(df)) * 100
            quality_metrics['completeness'][col] = {
                'percentage': completeness,
                'missing_count': len(df) - non_null_count
            }
        
        # Calculate overall score
        if quality_metrics['completeness']:
            avg_completeness = np.mean([
                m['percentage'] for m in quality_metrics['completeness'].values()
            ])
            quality_metrics['overall_score'] = avg_completeness / 100
        
        return quality_metrics
    
    def _evaluate_user_rules(
        self, 
        df: pd.DataFrame, 
        rules_to_evaluate: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate user-defined rules."""
        if not self.rule_engine:
            return {}
        
        rules_to_eval = rules_to_evaluate or list(self.config.get('rules', {}).keys())
        analytics_rules = list(self.config.get('analytics', {}).keys())
        rules_to_eval.extend(analytics_rules)
        
        results = {}
        
        for rule_name in rules_to_eval:
            try:
                result = self.rule_engine.evaluate_rule(df, rule_name)
                results[rule_name] = {
                    'compliance_rate': result.compliance_rate,
                    'total_points': result.total_points,
                    'compliant_points': result.compliant_points,
                    'violations_count': len(result.violations),
                    'violations': result.violations,  # Include detailed violations
                    'statistics': result.statistics,
                    'recommendations': result.recommendations,
                    'metadata': result.metadata
                }
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_name}: {e}")
                results[rule_name] = {'error': str(e)}
        
        return results
    
    def export_compliance_details(
        self, 
        df: pd.DataFrame, 
        room_id: str, 
        rule_results: Dict[str, Any], 
        output_dir: Path
    ) -> Dict[str, str]:
        """Export detailed compliance data for each rule in multiple formats."""
        exports = {}
        
        for rule_name, rule_result in rule_results.items():
            if not isinstance(rule_result, dict) or 'error' in rule_result:
                continue
                
            try:
                # Re-evaluate rule to get boolean compliance series
                result = self.rule_engine.evaluate_rule(df, rule_name)
                
                # Create detailed compliance DataFrame
                compliance_data = self._create_compliance_dataframe(df, result, rule_name)
                
                if not compliance_data.empty:
                    # Export in multiple formats
                    rule_exports = self._export_rule_compliance(
                        compliance_data, rule_name, room_id, output_dir
                    )
                    exports[rule_name] = rule_exports
                    
            except Exception as e:
                logger.error(f"Error exporting compliance data for {rule_name}: {e}")
        
        return exports
    
    def _create_compliance_dataframe(
        self, 
        df: pd.DataFrame, 
        analysis_result: AnalysisResult, 
        rule_name: str
    ) -> pd.DataFrame:
        """Create detailed compliance DataFrame with timestamps and values."""
        
        # Get the parameter column
        data_column = analysis_result.metadata.get('data_column')
        if not data_column or data_column not in df.columns:
            return pd.DataFrame()
        
        # Apply the same filters as the rule
        filter_name = analysis_result.metadata.get('filter_applied', 'all_hours')
        period_name = analysis_result.metadata.get('period_applied', 'all_year')
        filtered_df = self.filter_processor.apply_filter(df, filter_name, period_name)
        
        if filtered_df.empty:
            return pd.DataFrame()
        
        # Re-evaluate rule to get compliance series
        rule_config = (self.config.get('analytics', {}).get(rule_name) or 
                      self.config.get('rules', {}).get(rule_name))
        
        if not rule_config:
            return pd.DataFrame()
        
        # Get clean data and evaluate compliance
        clean_data = filtered_df[data_column].dropna()
        if clean_data.empty:
            return pd.DataFrame()
        
        # Evaluate compliance based on rule type
        rule_type = self.rule_engine._determine_rule_type(rule_config)
        
        if rule_type == RuleType.BIDIRECTIONAL:
            compliance_series = self.rule_engine._evaluate_bidirectional_rule(clean_data, rule_config)
        elif rule_type == RuleType.UNIDIRECTIONAL_ASCENDING:
            compliance_series = self.rule_engine._evaluate_unidirectional_rule(clean_data, rule_config, ascending=True)
        elif rule_type == RuleType.UNIDIRECTIONAL_DESCENDING:
            compliance_series = self.rule_engine._evaluate_unidirectional_rule(clean_data, rule_config, ascending=False)
        else:
            compliance_series = pd.Series([True] * len(clean_data), index=clean_data.index)
        
        # Create comprehensive compliance DataFrame
        compliance_df = pd.DataFrame({
            'timestamp': clean_data.index,
            'parameter': data_column,
            'value': clean_data.values,
            'compliant': compliance_series.values,
            'non_compliant': ~compliance_series.values,
            'rule_name': rule_name,
            'rule_description': rule_config.get('description', ''),
            'filter_applied': filter_name,
            'period_applied': period_name
        })
        
        # Add rule-specific information
        if 'limits' in rule_config:
            limits = rule_config['limits']
            compliance_df['lower_limit'] = limits.get('lower', None)
            compliance_df['upper_limit'] = limits.get('upper', None)
            compliance_df['within_limits'] = compliance_series.values
        elif 'limit' in rule_config:
            limit = rule_config['limit']
            compliance_df['limit'] = limit
            mode = rule_config.get('mode', 'unidirectional_ascending')
            if mode == 'unidirectional_ascending':
                compliance_df['above_limit'] = clean_data.values > limit
            else:
                compliance_df['below_limit'] = clean_data.values < limit
        
        # Add time-based information
        compliance_df['year'] = compliance_df['timestamp'].dt.year
        compliance_df['month'] = compliance_df['timestamp'].dt.month
        compliance_df['day'] = compliance_df['timestamp'].dt.day
        compliance_df['hour'] = compliance_df['timestamp'].dt.hour
        compliance_df['weekday'] = compliance_df['timestamp'].dt.day_name()
        compliance_df['is_weekend'] = compliance_df['timestamp'].dt.weekday >= 5
        
        return compliance_df
    
    def _export_rule_compliance(
        self, 
        compliance_df: pd.DataFrame, 
        rule_name: str, 
        room_id: str, 
        output_dir: Path
    ) -> Dict[str, str]:
        """Export rule compliance data in multiple formats."""
        exports = {}
        
        # Create rule-specific directory
        rule_dir = output_dir / "compliance_details" / room_id / rule_name
        rule_dir.mkdir(parents=True, exist_ok=True)
        
        # Export full compliance data as CSV
        full_csv_path = rule_dir / f"{rule_name}_full_compliance.csv"
        compliance_df.to_csv(full_csv_path, index=False)
        exports['full_csv'] = str(full_csv_path)
        
        # Export compliant records only
        compliant_df = compliance_df[compliance_df['compliant'] == True]
        if not compliant_df.empty:
            compliant_csv_path = rule_dir / f"{rule_name}_compliant_records.csv"
            compliant_df.to_csv(compliant_csv_path, index=False)
            exports['compliant_csv'] = str(compliant_csv_path)
        
        # Export non-compliant records only
        non_compliant_df = compliance_df[compliance_df['compliant'] == False]
        if not non_compliant_df.empty:
            non_compliant_csv_path = rule_dir / f"{rule_name}_non_compliant_records.csv"
            non_compliant_df.to_csv(non_compliant_csv_path, index=False)
            exports['non_compliant_csv'] = str(non_compliant_csv_path)
        
        # Export JSON format with summary statistics
        json_export = {
            'rule_name': rule_name,
            'room_id': room_id,
            'summary': {
                'total_records': len(compliance_df),
                'compliant_records': len(compliant_df),
                'non_compliant_records': len(non_compliant_df),
                'compliance_rate': (len(compliant_df) / len(compliance_df) * 100) if len(compliance_df) > 0 else 0
            },
            'time_period': {
                'start': compliance_df['timestamp'].min().isoformat() if len(compliance_df) > 0 else None,
                'end': compliance_df['timestamp'].max().isoformat() if len(compliance_df) > 0 else None
            },
            'compliant_records': compliant_df.to_dict('records'),
            'non_compliant_records': non_compliant_df.to_dict('records')
        }
        
        json_path = rule_dir / f"{rule_name}_compliance.json"
        with open(json_path, 'w') as f:
            import json
            json.dump(json_export, f, indent=2, default=str)
        exports['json'] = str(json_path)
        
        # Export Excel format if available
        try:
            excel_path = rule_dir / f"{rule_name}_compliance.xlsx"
            with pd.ExcelWriter(excel_path) as writer:
                compliance_df.to_excel(writer, sheet_name='Full_Data', index=False)
                if not compliant_df.empty:
                    compliant_df.to_excel(writer, sheet_name='Compliant', index=False)
                if not non_compliant_df.empty:
                    non_compliant_df.to_excel(writer, sheet_name='Non_Compliant', index=False)
            exports['excel'] = str(excel_path)
        except ImportError:
            pass  # openpyxl not available
        
        return exports
    
    def _evaluate_en16798_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Evaluate EN16798-1 compliance rules."""
        if not self.rule_engine:
            return {}
        
        # Find EN16798 rules in configuration
        en_rules = []
        for rule_name, rule_config in self.config.get('rules', {}).items():
            if 'en16798' in rule_name.lower() or 'EN16798' in rule_config.get('category', ''):
                en_rules.append(rule_name)
        
        return self._evaluate_user_rules(df, en_rules)
    
    def get_available_rules(self) -> Dict[str, List[str]]:
        """Get list of available rules by category."""
        rules = {
            'user_rules': list(self.config.get('analytics', {}).keys()),
            'en16798_rules': [],
            'all_rules': list(self.config.get('rules', {}).keys())
        }
        
        # Categorize EN16798 rules
        for rule_name, rule_config in self.config.get('rules', {}).items():
            if 'en16798' in rule_name.lower() or 'EN16798' in rule_config.get('category', ''):
                rules['en16798_rules'].append(rule_name)
        
        return rules
    
    def get_filter_options(self) -> Dict[str, Any]:
        """Get available filter and period options."""
        if not self.filter_processor:
            return {
                'filters': [],
                'periods': [],
                'default_opening_hours': []
            }
        
        return {
            'filters': list(self.filter_processor.filters.keys()),
            'periods': list(self.filter_processor.periods.keys()),
            'default_opening_hours': self.filter_processor.default_opening_hours
        }
    
    def apply_filters(
        self, 
        df: pd.DataFrame, 
        filter_name: str = 'all_hours',
        period_name: str = 'all_year'
    ) -> pd.DataFrame:
        """Apply time-based filters to data."""
        if not self.filter_processor:
            return df
        return self.filter_processor.apply_filter(df, filter_name, period_name)
