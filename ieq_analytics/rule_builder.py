"""
Rule builder for creating and managing IEQ analytics rules.
Supports bidirectional, unidirectional, and complex rule evaluation.
"""

import yaml
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import logging

logger = logging.getLogger(__name__)

try:
    import holidays
    DK_HOLIDAYS = holidays.country_holidays('DK')
except ImportError:
    holidays = None
    DK_HOLIDAYS = []

from .models import IEQData


class RuleEvaluator:
    """Evaluates rules"""
    
    @staticmethod
    def evaluate_condition(condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition against data.
        
        Args:
            condition: Condition dictionary with operator and operands
            data: Data dictionary containing values
            
        Returns:
            Boolean result of condition evaluation
        """
        if not isinstance(condition, dict) or not condition:
            return False
        
        # Get the operator (first key)
        operator = list(condition.keys())[0]
        operands = condition[operator]
        
        try:
            if operator == 'and':
                return all(RuleEvaluator.evaluate_condition(op, data) for op in operands)
            
            elif operator == 'or':
                return any(RuleEvaluator.evaluate_condition(op, data) for op in operands)
            
            elif operator == 'not':
                return not RuleEvaluator.evaluate_condition(operands, data)
            
            elif operator in ['>=', '<=', '>', '<', '==', '!=']:
                if len(operands) != 2:
                    return False
                
                left = RuleEvaluator._get_value(operands[0], data)
                right = RuleEvaluator._get_value(operands[1], data)
                
                if left is None or right is None:
                    return False
                
                if operator == '>=':
                    return left >= right
                elif operator == '<=':
                    return left <= right
                elif operator == '>':
                    return left > right
                elif operator == '<':
                    return left < right
                elif operator == '==':
                    return left == right
                elif operator == '!=':
                    return left != right
            
            return False
            
        except (TypeError, ValueError, KeyError):
            return False
    
    @staticmethod
    def _get_value(operand: Any, data: Dict[str, Any]) -> Any:
        """
        Get value from operand, which can be a variable reference or literal value.
        
        Args:
            operand: Operand that can be a dict with 'var' key or a literal value
            data: Data dictionary
            
        Returns:
            The resolved value
        """
        if isinstance(operand, dict) and 'var' in operand:
            var_name = operand['var']
            return data.get(var_name)
        else:
            return operand


class SimpleRuleBuilder:
    """Simple rule builder for basic IEQ analytics rules."""
    
    def __init__(self):
        """Initialize the rule builder."""
        self.conditions = []
    
    def reset(self) -> 'SimpleRuleBuilder':
        """Reset the current rule."""
        self.conditions = []
        return self
    
    def add_range_condition(self, variable: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> 'SimpleRuleBuilder':
        """Add a range condition (bidirectional)."""
        if min_val is not None and max_val is not None:
            self.conditions.append({
                'and': [
                    {'>=': [{'var': variable}, min_val]},
                    {'<=': [{'var': variable}, max_val]}
                ]
            })
        elif min_val is not None:
            self.conditions.append({'>=': [{'var': variable}, min_val]})
        elif max_val is not None:
            self.conditions.append({'<=': [{'var': variable}, max_val]})
        
        return self
    
    def add_threshold_condition(self, variable: str, threshold: float, operator: str = '<=') -> 'SimpleRuleBuilder':
        """Add a threshold condition (unidirectional)."""
        if operator not in ['<=', '>=', '<', '>', '==', '!=']:
            raise ValueError(f"Invalid operator: {operator}")
        
        self.conditions.append({operator: [{'var': variable}, threshold]})
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the final rule."""
        if not self.conditions:
            return {}
        elif len(self.conditions) == 1:
            return self.conditions[0]
        else:
            return {'and': self.conditions}


class AnalyticsFilter:
    """Filter for analyzing IEQ data based on various criteria."""
    
    def __init__(self, config_path: Union[str, Path, None] = None):
        """Initialize the filter with configuration."""
        self.config = {}
        self.holidays_cache = {}
        
        if config_path:
            if isinstance(config_path, str):
                config_path = Path(config_path)
            
            if config_path.exists():
                self.load_config(config_path)
    
    def load_config(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            self.config = {}
    
    def get_holidays(self, year: int, country: str = "Denmark") -> List[date]:
        """Get holidays for a specific year and country."""
        cache_key = f"{country}_{year}"
        
        if cache_key not in self.holidays_cache:
            try:
                if holidays is not None:
                    country_holidays = holidays.country_holidays('DK', years=year)
                else:
                    country_holidays = {}
            except:
                country_holidays = {}
            
            # Add custom holidays if defined in config
            custom_holidays = self.config.get("holidays", {}).get("custom_holidays", [])
            for holiday in custom_holidays:
                try:
                    holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
                    country_holidays[holiday_date] = holiday["name"]
                except (ValueError, KeyError):
                    continue
            
            self.holidays_cache[cache_key] = list(country_holidays.keys())
        
        return self.holidays_cache[cache_key]
    
    def apply_time_filters(self, data: pd.DataFrame, filter_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply time-based filters to data.
        
        Args:
            data: DataFrame with DatetimeIndex
            filter_config: Filter configuration dictionary
            
        Returns:
            Filtered DataFrame
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            logger.warning("Data must have DatetimeIndex for time filtering")
            return data
        
        filtered_data = data.copy()
        
        # Hour filter
        hours = filter_config.get('hours', [])
        if hours:
            filtered_data = filtered_data[filtered_data.index.hour.isin(hours)]  # type: ignore
        
        # Weekday filter
        if filter_config.get('weekdays_only', False):
            filtered_data = filtered_data[filtered_data.index.weekday < 5]  # type: ignore
        elif filter_config.get('weekends_only', False):
            filtered_data = filtered_data[filtered_data.index.weekday >= 5]  # type: ignore
        
        # Weekend exclusion
        if filter_config.get('exclude_weekends', False):
            filtered_data = filtered_data[filtered_data.index.weekday < 5]  # type: ignore
        
        # Holiday exclusion
        if filter_config.get('exclude_holidays', False):
            holiday_dates = []
            for year in filtered_data.index.year.unique():  # type: ignore
                holiday_dates.extend(self.get_holidays(year))
            
            if holiday_dates:
                # Convert to set of dates for faster lookup
                holiday_set = set(holiday_dates)
                filtered_data = filtered_data[~pd.Series(filtered_data.index.date).isin(holiday_set).values]  # type: ignore
        
        return filtered_data
    
    def apply_period_filter(self, data: pd.DataFrame, period_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply period-based filters to data.
        
        Args:
            data: DataFrame with DatetimeIndex
            period_config: Period configuration dictionary
            
        Returns:
            Filtered DataFrame
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            return data
        
        months = period_config.get('months', [])
        if months:
            data = data[data.index.month.isin(months)]  # type: ignore
        
        return data


class AnalyticsEngine:
    """Main analytics engine using custom rule evaluation."""
    
    def __init__(self, config_path: Union[str, Path]):
        """Initialize the analytics engine with configuration."""
        if isinstance(config_path, str):
            config_path = Path(config_path)
        
        self.config_path = config_path
        self.config = {}
        self.filter = AnalyticsFilter(config_path)
        self.rule_evaluator = RuleEvaluator()
        self.load_config()
        
        # Load rules from the configuration
        self.rules = {}
        if 'rules' in self.config:
            self.rules = self.config['rules']
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            self.config = {}
    
    def find_data_column(self, data: pd.DataFrame, feature: str) -> Optional[str]:
        """
        Find the matching column name for a feature.
        
        Args:
            data: DataFrame to search in
            feature: Feature name to find
            
        Returns:
            Column name if found, None otherwise
        """
        # Direct match
        if feature in data.columns:
            return feature
        
        # Case-insensitive partial match
        feature_lower = feature.lower()
        for col in data.columns:
            if feature_lower in col.lower():
                return col
        
        # Common aliases
        aliases = {
            'temperature': ['temp', 'temperature_c', 'temp_c', 'air_temperature'],
            'humidity': ['rh', 'relative_humidity', 'humidity_percent', 'humidity_rh'],
            'co2': ['co2_ppm', 'carbon_dioxide', 'co2_concentration'],
        }
        
        if feature_lower in aliases:
            for alias in aliases[feature_lower]:
                for col in data.columns:
                    if alias in col.lower():
                        return col
        
        return None
    
    def evaluate_rule_config(self, data: pd.DataFrame, rule_config: Dict[str, Any]) -> pd.Series:
        """
        Evaluate a rule configuration against data.
        
        Args:
            data: DataFrame with IEQ data
            rule_config: Rule configuration dictionary
            
        Returns:
            Boolean series indicating compliance for each data point
        """
        try:
            # Apply period filters first
            filtered_data = data.copy()
            
            period = rule_config.get("period", "all_year")
            if period and period != "all_year":
                periods_config = self.config.get("periods", {})
                if period in periods_config:
                    filtered_data = self.filter.apply_period_filter(
                        filtered_data, periods_config[period]
                    )
            
            # Apply time filters
            filter_name = rule_config.get("filter", "all_hours")
            if filter_name and filter_name != "all_hours":
                filters_config = self.config.get("filters", {})
                if filter_name in filters_config:
                    filtered_data = self.filter.apply_time_filters(
                        filtered_data, filters_config[filter_name]
                    )
            
            if filtered_data.empty:
                return pd.Series(dtype=bool)
            
            # Evaluate based on rule type
            if "json_logic" in rule_config:
                # Complex rule with json_logic structure
                return self._evaluate_complex_rule(filtered_data, rule_config["json_logic"])
            
            elif "limits" in rule_config:
                # Bidirectional rule (temperature, humidity)
                return self._evaluate_bidirectional_rule(filtered_data, rule_config)
            
            elif "limit" in rule_config:
                # Unidirectional rule (CO2)
                return self._evaluate_unidirectional_rule(filtered_data, rule_config)
            
            else:
                logger.warning(f"Unknown rule type in config: {rule_config}")
                return pd.Series(False, index=filtered_data.index)
                
        except Exception as e:
            logger.error(f"Error evaluating rule: {e}")
            return pd.Series(False, index=data.index)
    
    def _evaluate_complex_rule(self, data: pd.DataFrame, rule: Dict[str, Any]) -> pd.Series:
        """Evaluate complex rules with logical operators."""
        results = pd.Series(False, index=data.index)
        
        for idx, row in data.iterrows():
            try:
                # Convert row to dictionary and add derived values
                row_dict = row.to_dict()
                
                # Add time-based variables if datetime index
                if isinstance(data.index, pd.DatetimeIndex) and isinstance(idx, pd.Timestamp):
                    timestamp = idx
                    
                    row_dict.update({
                        'hour': timestamp.hour,
                        'weekday': timestamp.weekday(),
                        'month': timestamp.month,
                        'day_of_year': timestamp.dayofyear,
                        'is_holiday': timestamp.date() in self.filter.get_holidays(timestamp.year)
                    })
                
                # Evaluate rule using our custom evaluator
                result = self.rule_evaluator.evaluate_condition(rule, row_dict)
                results[idx] = bool(result)
            except Exception:
                results[idx] = False
        
        return results
    
    def _evaluate_bidirectional_rule(self, data: pd.DataFrame, rule_config: Dict[str, Any]) -> pd.Series:
        """Evaluate bidirectional rules (temperature, humidity with min/max limits)."""
        feature = rule_config.get("feature", "")
        limits = rule_config.get("limits", {})
        
        # Find matching column
        feature_col = self.find_data_column(data, feature)
        if feature_col is None:
            logger.warning(f"Column for feature '{feature}' not found in data")
            return pd.Series(False, index=data.index)
        
        # Get clean data
        series = data[feature_col].dropna()
        
        # Apply limits
        min_val = limits.get("lower")
        max_val = limits.get("upper")
        
        if min_val is not None and max_val is not None:
            compliant = (series >= min_val) & (series <= max_val)
        elif min_val is not None:
            compliant = series >= min_val
        elif max_val is not None:
            compliant = series <= max_val
        else:
            compliant = pd.Series(True, index=series.index)
        
        # Align with original data index
        result = pd.Series(False, index=data.index)
        result.loc[compliant.index] = compliant
        
        return result
    
    def _evaluate_unidirectional_rule(self, data: pd.DataFrame, rule_config: Dict[str, Any]) -> pd.Series:
        """Evaluate unidirectional rules (CO2 with single limit)."""
        feature = rule_config.get("feature", "")
        limit = rule_config.get("limit")
        mode = rule_config.get("mode", "unidirectional_ascending")
        
        # Find matching column
        feature_col = self.find_data_column(data, feature)
        if feature_col is None or limit is None:
            logger.warning(f"Column for feature '{feature}' not found or limit not specified")
            return pd.Series(False, index=data.index)
        
        # Get clean data
        series = data[feature_col].dropna()
        
        # Apply limit based on mode
        if mode == "unidirectional_ascending":
            compliant = series <= limit
        else:  # mode == "unidirectional_descending"
            compliant = series >= limit
        
        # Align with original data index
        result = pd.Series(False, index=data.index)
        result.loc[compliant.index] = compliant
        
        return result
    
    def analyze_comfort_compliance(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze comfort compliance based on configured rules."""
        analytics_rules = self.config.get("analytics", {})
        results = {}
        
        for rule_name, rule_config in analytics_rules.items():
            try:
                # Evaluate rule
                rule_results = self.evaluate_rule_config(ieq_data.data, rule_config)
                
                if rule_results.empty:
                    results[rule_name] = {
                        "compliance_rate": 0.0,
                        "total_points": 0,
                        "compliant_points": 0,
                        "non_compliant_hours": 0,
                        "description": rule_config.get("description", "No description"),
                        "feature": rule_config.get("feature", "unknown")
                    }
                    continue
                
                total_points = len(rule_results)
                compliant_points = rule_results.sum()
                non_compliant_hours = total_points - compliant_points
                
                results[rule_name] = {
                    "compliance_rate": rule_results.mean() if total_points > 0 else 0.0,
                    "total_points": total_points,
                    "compliant_points": int(compliant_points),
                    "non_compliant_hours": int(non_compliant_hours),
                    "description": rule_config.get("description", "No description"),
                    "feature": rule_config.get("feature", "unknown")
                }
                
            except Exception as e:
                logger.error(f"Error analyzing rule {rule_name}: {e}")
                results[rule_name] = {
                    "error": str(e),
                    "compliance_rate": 0.0,
                    "total_points": 0,
                    "compliant_points": 0,
                    "non_compliant_hours": 0
                }
        
        return results
    
    def analyze_en_standard(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze compliance with EN 16798-1 standard."""
        en_rules = self.config.get("rules", {})
        results = {}
        
        for rule_name, rule_config in en_rules.items():
            try:
                if "rule" in rule_config:
                    # Complex rule with json_logic structure
                    rule_results = self._evaluate_complex_rule(ieq_data.data, rule_config["rule"])
                    
                    results[rule_name] = {
                        "compliance_rate": rule_results.mean() if len(rule_results) > 0 else 0.0,
                        "total_points": len(rule_results),
                        "compliant_points": int(rule_results.sum()),
                        "category": rule_config.get("category", "Unknown"),
                        "parameter": rule_config.get("parameter", "unknown"),
                        "description": rule_config.get("description", "No description")
                    }
                    
            except Exception as e:
                logger.error(f"Error analyzing EN rule {rule_name}: {e}")
                results[rule_name] = {"error": str(e)}
        
        return results
    
    def analyze_all_rules(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze all configured rules."""
        all_results = {}
        
        # Comfort compliance
        comfort_results = self.analyze_comfort_compliance(ieq_data)
        all_results["comfort_compliance"] = comfort_results
        
        # EN standard compliance
        en_results = self.analyze_en_standard(ieq_data)
        all_results["en_standard_compliance"] = en_results
        
        return all_results
    
    def analyze_rule(self, data: pd.DataFrame, rule_name: str) -> Dict[str, Any]:
        """Analyze a specific rule against data."""
        # Check in analytics rules first
        analytics_rules = self.config.get("analytics", {})
        if rule_name in analytics_rules:
            rule_config = analytics_rules[rule_name]
            rule_results = self.evaluate_rule_config(data, rule_config)
            
            return {
                "total_points": len(rule_results),
                "compliant_points": int(rule_results.sum()),
                "compliance_rate": float(rule_results.mean()) if len(rule_results) > 0 else 0.0,
                "description": rule_config.get("description", "No description"),
                "feature": rule_config.get("feature", "unknown")
            }
        
        # Check in EN rules
        en_rules = self.config.get("rules", {})
        if rule_name in en_rules:
            rule_config = en_rules[rule_name]
            try:
                if "rule" in rule_config:
                    rule_results = self._evaluate_complex_rule(data, rule_config["rule"])
                    
                    return {
                        "total_points": len(rule_results),
                        "compliant_points": int(rule_results.sum()),
                        "compliance_rate": float(rule_results.mean()) if len(rule_results) > 0 else 0.0,
                        "description": rule_config.get("description", "No description"),
                        "category": rule_config.get("category", "Unknown")
                    }
            except Exception as e:
                return {
                    "error": str(e),
                    "total_points": 0,
                    "compliant_points": 0,
                    "compliance_rate": 0.0
                }
        
        return {
            "error": f"Rule '{rule_name}' not found",
            "total_points": 0,
            "compliant_points": 0,
            "compliance_rate": 0.0
        }
