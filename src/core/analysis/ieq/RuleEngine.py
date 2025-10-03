import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .types import RuleType, AnalysisResult
from .FilterProcessor import FilterProcessor

logger = logging.getLogger(__name__)

class RuleEngine:
    """Unified rule engine for user rules and EN16798 standards."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with configuration."""
        self.config = config or {}
        self.rules = self.config.get('rules', {})
        self.analytics = self.config.get('analytics', {})
        self.filter_processor = FilterProcessor(config)
    
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