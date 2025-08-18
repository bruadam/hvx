"""
Rule builder for creating and managing IEQ analytics rules using json-logic.
"""

import yaml
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime, date
import pandas as pd

try:
    import holidays
    DK_HOLIDAYS = holidays.country_holidays('DK')
except ImportError:
    holidays = None
    DK_HOLIDAYS = []

try:
    from json_logic import jsonLogic
except ImportError:
    # Fallback implementation if json-logic is not available
    def jsonLogic(rule: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Mock implementation of jsonLogic."""
        return False

from .models import IEQData


class RuleBuilder:
    """Builder for creating analytics rules using json-logic syntax."""
    
    def __init__(self):
        """Initialize the rule builder."""
        self.rule = {}
    
    def reset(self) -> 'RuleBuilder':
        """Reset the current rule."""
        self.rule = {}
        return self
    
    def temperature_threshold(self, min_temp: float = None, max_temp: float = None) -> 'RuleBuilder':
        """Add temperature threshold condition."""
        conditions = []
        if min_temp is not None:
            conditions.append({">=": [{"var": "temperature"}, min_temp]})
        if max_temp is not None:
            conditions.append({"<=": [{"var": "temperature"}, max_temp]})
        
        if len(conditions) == 1:
            self._add_condition(conditions[0])
        elif len(conditions) == 2:
            self._add_condition({"and": conditions})
        
        return self
    
    def humidity_threshold(self, min_humidity: float = None, max_humidity: float = None) -> 'RuleBuilder':
        """Add humidity threshold condition."""
        conditions = []
        if min_humidity is not None:
            conditions.append({">=": [{"var": "humidity"}, min_humidity]})
        if max_humidity is not None:
            conditions.append({"<=": [{"var": "humidity"}, max_humidity]})
        
        if len(conditions) == 1:
            self._add_condition(conditions[0])
        elif len(conditions) == 2:
            self._add_condition({"and": conditions})
        
        return self
    
    def co2_threshold(self, max_co2: float) -> 'RuleBuilder':
        """Add CO2 threshold condition."""
        self._add_condition({"<=": [{"var": "co2"}, max_co2]})
        return self
    
    def _add_condition(self, condition: Dict[str, Any]) -> None:
        """Add condition to the current rule."""
        if not self.rule:
            self.rule = condition
        else:
            if "and" in self.rule:
                self.rule["and"].append(condition)
            else:
                self.rule = {"and": [self.rule, condition]}
    
    def build(self) -> Dict[str, Any]:
        """Build and return the final rule."""
        return self.rule.copy()
    
    @staticmethod
    def create_comfort_rule(
        temperature_range: tuple = (20, 26),
        humidity_range: tuple = (30, 70),
        co2_max: float = 800,
        time_range: tuple = (8, 18)
    ) -> Dict[str, Any]:
        """Create a standard comfort assessment rule."""
        builder = RuleBuilder()
        builder.temperature_threshold(temperature_range[0], temperature_range[1])
        builder.humidity_threshold(humidity_range[0], humidity_range[1])
        builder.co2_threshold(co2_max)
        return builder.build()


class AnalyticsFilter:
    """Filter for analyzing IEQ data based on various criteria."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the filter with configuration."""
        self.config = {}
        self.holidays_cache = {}
        
        if config_path and config_path.exists():
            self.load_config(config_path)
    
    def load_config(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
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
                holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
                country_holidays[holiday_date] = holiday["name"]
            
            self.holidays_cache[cache_key] = list(country_holidays.keys())
        
        return self.holidays_cache[cache_key]


class AnalyticsEngine:
    """Main analytics engine using json-logic rules."""
    
    def __init__(self, config_path: Path):
        """Initialize the analytics engine with configuration."""
        self.config_path = config_path
        self.config = {}
        self.filter = AnalyticsFilter(config_path)
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def evaluate_rule(self, rule: Dict[str, Any], data: pd.DataFrame) -> pd.Series:
        """Evaluate a json-logic rule against data."""
        results = pd.Series(False, index=data.index)
        
        for idx, row in data.iterrows():
            try:
                # Convert row to dictionary and add derived values
                row_dict = row.to_dict()
                
                # Add time-based variables if datetime index
                if isinstance(data.index, pd.DatetimeIndex):
                    timestamp = data.index[data.index.get_loc(idx)]
                    row_dict.update({
                        'hour': timestamp.hour,
                        'weekday': timestamp.weekday(),
                        'month': timestamp.month,
                        'day_of_year': timestamp.dayofyear,
                        'is_holiday': timestamp.date() in self.filter.get_holidays(timestamp.year)
                    })
                
                # Evaluate rule
                result = jsonLogic(rule, row_dict)
                results.iloc[results.index.get_loc(idx)] = bool(result)
            except Exception:
                results.iloc[results.index.get_loc(idx)] = False
        
        return results
    
    def analyze_comfort_compliance(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze comfort compliance based on configured rules."""
        rules = self.config.get("comfort_rules", {})
        results = {}
        
        for rule_name, rule_config in rules.items():
            try:
                filtered_data = ieq_data.data.copy()
                
                # Evaluate rule
                if "rule" in rule_config:
                    rule_results = self.evaluate_rule(rule_config["rule"], filtered_data)
                    
                    results[rule_name] = {
                        "compliance_rate": rule_results.mean(),
                        "total_points": len(rule_results),
                        "compliant_points": rule_results.sum(),
                        "description": rule_config.get("description", "No description"),
                        "category": rule_config.get("category", "general")
                    }
                
            except Exception as e:
                results[rule_name] = {
                    "error": str(e),
                    "compliance_rate": 0.0,
                    "total_points": 0
                }
        
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
    
    def analyze_en_standard(self, ieq_data: IEQData) -> Dict[str, Any]:
        """Analyze compliance with EN 16798-1 standard."""
        en_rules = self.config.get("en_16798_rules", {})
        results = {}
        
        for category, category_rules in en_rules.items():
            category_results = {}
            
            for rule_name, rule_config in category_rules.items():
                try:
                    filtered_data = ieq_data.data.copy()
                    
                    # Evaluate rule
                    if "rule" in rule_config:
                        rule_results = self.evaluate_rule(rule_config["rule"], filtered_data)
                        
                        category_results[rule_name] = {
                            "compliance_rate": rule_results.mean(),
                            "total_points": len(rule_results),
                            "compliant_points": rule_results.sum(),
                            "standard_level": rule_config.get("standard_level", "Category II"),
                            "parameter": rule_config.get("parameter", "unknown"),
                            "description": rule_config.get("description", "No description")
                        }
                        
                except Exception as e:
                    category_results[rule_name] = {"error": str(e)}
            
            results[category] = category_results
        
        return results
