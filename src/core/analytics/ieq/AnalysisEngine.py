import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging
import yaml
import json

from .types import Method, RuleType, AnalysisResult
from .FilterProcessor import FilterProcessor
from .RuleEngine import RuleEngine
from .library.metrics import (
    calculate_basic_statistics,
    calculate_extended_statistics,
    calculate_completeness,
    calculate_quality_score
)

logger = logging.getLogger(__name__)

"""\nUnified IEQ Analytics Engine

Consolidated module providing:
- Unified filtering (time-based, opening hours, holidays)
- Dynamic rule evaluation with standard discovery
- Core analytics using library modules
- Selective standard/parameter testing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging
import yaml
import json

from .types import Method, RuleType, AnalysisResult
from .FilterProcessor import FilterProcessor
from .RuleEngine import RuleEngine

logger = logging.getLogger(__name__)

class AnalysisEngine:
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
        self.rule_engine = RuleEngine(self.config)
        self.filter_processor = FilterProcessor(self.config)
    
    def analyze_room_data(
        self,
        df: pd.DataFrame,
        room_id: str,
        analysis_types: Optional[List[Method]] = None,
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
            analysis_types = [Method.BASIC_STATISTICS, Method.DATA_QUALITY]
        
        results = {
            'room_id': room_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'data_period': self._get_data_period(df),
            'analysis_types': [at.value for at in analysis_types]
        }
        
        # Basic statistics
        if Method.BASIC_STATISTICS in analysis_types:
            results['basic_statistics'] = self._calculate_basic_statistics(df)
        
        # Data quality
        if Method.DATA_QUALITY in analysis_types:
            results['data_quality'] = self._analyze_data_quality(df)
        
        # User rules evaluation
        if Method.USER_RULES in analysis_types:
            results['user_rules'] = self._evaluate_user_rules(df, rules_to_evaluate)
        
        # EN16798 compliance
        if Method.EN16798_COMPLIANCE in analysis_types:
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
        """Calculate basic statistics using library functions."""
        stats = {}
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            clean_data = df[col].dropna()
            if len(clean_data) > 0:
                # Use library function for statistics calculation
                stats[col] = calculate_basic_statistics(clean_data)
        
        return stats
    
    def _analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data quality using library functions."""
        if df.empty:
            return {'overall_score': 0.0, 'total_records': 0}
        
        quality_metrics = {
            'total_records': len(df),
            'completeness': {},
            'missing_periods': [],
            'overall_score': 0.0
        }
        
        # Calculate completeness for each column using library function
        column_scores = []
        for col in df.columns:
            completeness_pct = calculate_completeness(df[col])
            missing_count = len(df) - df[col].count()
            quality_metrics['completeness'][col] = {
                'percentage': completeness_pct,
                'missing_count': missing_count
            }
            
            # Calculate quality score for this column
            col_score = calculate_quality_score(df[col])
            column_scores.append(col_score)
        
        # Calculate overall score as average of column scores
        if column_scores:
            quality_metrics['overall_score'] = sum(column_scores) / len(column_scores)
        
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
                if not self.rule_engine:
                    continue
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
        
        if not self.filter_processor:
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
        if not self.rule_engine:
            return pd.DataFrame()
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
            'non_compliant': np.logical_not(np.asarray(compliance_series.values)),
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
    
    def get_available_standards(self) -> List[str]:
        """Get list of all available standards."""
        if not self.rule_engine:
            return []
        return self.rule_engine.get_available_standards()
    
    def get_rules_for_standard(self, standard_id: str) -> List[str]:
        """Get all rules for a specific standard."""
        if not self.rule_engine:
            return []
        return self.rule_engine.get_rules_for_standard(standard_id)
    
    def analyze_with_standards(
        self,
        df: pd.DataFrame,
        room_id: str,
        standard_ids: List[str],
        parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """\n        Analyze data against selected standards.\n        \n        Args:\n            df: DataFrame with IEQ data\n            room_id: Room identifier\n            standard_ids: List of standard IDs to apply (e.g., ['en16798-1', 'br18'])\n            parameters: Optional list of parameters to filter (e.g., ['temperature', 'co2'])\n        \n        Returns:\n            Analysis results grouped by standard\n        """
        if not self.rule_engine:
            return {}
        
        results = {
            'room_id': room_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'standards_analyzed': standard_ids,
            'data_period': self._get_data_period(df),
            'results_by_standard': {}
        }
        
        for standard_id in standard_ids:
            # Get rules for this standard
            rules = self.rule_engine.get_rules_for_standard(standard_id)
            
            # Filter by parameter if specified
            if parameters:
                filtered_rules = []
                for rule_id in rules:
                    rule_config = self.rule_engine.standard_registry.get_rule_config(rule_id)
                    if rule_config:
                        rule_param = rule_config.get('feature') or rule_config.get('parameter', '')
                        if any(param.lower() in str(rule_param).lower() for param in parameters):
                            filtered_rules.append(rule_id)
                rules = filtered_rules
            
            # Evaluate rules for this standard
            standard_results = {}
            for rule_id in rules:
                try:
                    result = self.rule_engine.evaluate_rule(df, rule_id)
                    standard_results[rule_id] = {
                        'compliance_rate': result.compliance_rate,
                        'total_points': result.total_points,
                        'compliant_points': result.compliant_points,
                        'violations_count': len(result.violations),
                        'statistics': result.statistics,
                        'recommendations': result.recommendations,
                        'metadata': result.metadata
                    }
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule_id}: {e}")
                    standard_results[rule_id] = {'error': str(e)}
            
            results['results_by_standard'][standard_id] = standard_results
        
        return results
