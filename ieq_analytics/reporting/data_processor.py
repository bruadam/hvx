"""
Report Data Processor

Processes IEQ analysis data for report generation, including worst performer
identification, statistical summaries, and data aggregation for visualizations.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging

from ..models import IEQData
from ..enums import IEQParameter, ComfortCategory

logger = logging.getLogger(__name__)


class WorstPerformerCriteria:
    """Criteria for identifying worst performing rooms."""
    
    def __init__(
        self,
        min_data_quality: float = 0.8,
        min_comfort_compliance: float = 80.0,
        weight_temperature: float = 0.3,
        weight_co2: float = 0.4,
        weight_humidity: float = 0.2,
        weight_data_quality: float = 0.1
    ):
        self.min_data_quality = min_data_quality
        self.min_comfort_compliance = min_comfort_compliance
        self.weight_temperature = weight_temperature
        self.weight_co2 = weight_co2
        self.weight_humidity = weight_humidity
        self.weight_data_quality = weight_data_quality


class ReportDataProcessor:
    """Processes analysis data for report generation."""
    
    def __init__(self, criteria: Optional[WorstPerformerCriteria] = None):
        self.criteria = criteria or WorstPerformerCriteria()
    
    def identify_worst_performers(
        self,
        room_analyses: List[Dict[str, Any]],
        top_n: int = 10,
        by_building: bool = True
    ) -> Dict[str, Any]:
        """
        Identify worst performing rooms based on multiple criteria.
        
        Args:
            room_analyses: List of room analysis results
            top_n: Number of worst performers to identify
            by_building: Whether to identify worst performers per building
            
        Returns:
            Dictionary with worst performer analysis
        """
        logger.info(f"Identifying worst performers from {len(room_analyses)} rooms")
        
        # Calculate performance scores for each room
        room_scores = []
        for analysis in room_analyses:
            score_data = self._calculate_performance_score(analysis)
            if score_data:
                room_scores.append(score_data)
        
        # Sort by performance score (lower is worse)
        room_scores.sort(key=lambda x: x['performance_score'])
        
        results = {
            'criteria': {
                'min_data_quality': self.criteria.min_data_quality,
                'min_comfort_compliance': self.criteria.min_comfort_compliance,
                'weights': {
                    'temperature': self.criteria.weight_temperature,
                    'co2': self.criteria.weight_co2,
                    'humidity': self.criteria.weight_humidity,
                    'data_quality': self.criteria.weight_data_quality
                }
            },
            'overall_worst': room_scores[:top_n],
            'by_building': {},
            'summary_statistics': self._calculate_summary_statistics(room_scores)
        }
        
        if by_building:
            # Group by building and find worst performers per building
            building_groups = {}
            for score_data in room_scores:
                building_id = score_data['building_id']
                if building_id not in building_groups:
                    building_groups[building_id] = []
                building_groups[building_id].append(score_data)
            
            for building_id, building_rooms in building_groups.items():
                # Sort and take top N worst per building
                building_rooms.sort(key=lambda x: x['performance_score'])
                results['by_building'][building_id] = {
                    'worst_performers': building_rooms[:min(top_n, len(building_rooms))],
                    'total_rooms': len(building_rooms),
                    'building_avg_score': np.mean([r['performance_score'] for r in building_rooms])
                }
        
        return results
    
    def _calculate_performance_score(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate overall performance score for a room."""
        room_id = analysis.get('room_id')
        building_id = analysis.get('building_id')
        
        # Data quality score
        data_quality = analysis.get('data_quality', {})
        quality_score = data_quality.get('overall_score', 0.0)
        
        # Comfort compliance scores
        comfort_analysis = analysis.get('comfort_analysis', {})
        
        # Extract Category II compliance (most commonly used standard)
        temp_compliance = 100.0  # Default if no data
        co2_compliance = 100.0
        humidity_compliance = 100.0
        
        if 'temperature' in comfort_analysis:
            temp_cat_ii = comfort_analysis['temperature'].get('II', {})
            temp_compliance = temp_cat_ii.get('compliance_percentage', 100.0)
        
        if 'co2' in comfort_analysis:
            co2_cat_ii = comfort_analysis['co2'].get('II', {})
            co2_compliance = co2_cat_ii.get('compliance_percentage', 100.0)
        
        if 'humidity' in comfort_analysis:
            humidity_cat_ii = comfort_analysis['humidity'].get('II', {})
            humidity_compliance = humidity_cat_ii.get('compliance_percentage', 100.0)
        
        # Calculate weighted performance score (0-100, higher is better)
        performance_score = (
            self.criteria.weight_temperature * temp_compliance +
            self.criteria.weight_co2 * co2_compliance +
            self.criteria.weight_humidity * humidity_compliance +
            self.criteria.weight_data_quality * (quality_score * 100)
        )
        
        # Identify specific issues
        issues = []
        if quality_score < self.criteria.min_data_quality:
            issues.append(f"Poor data quality ({quality_score:.2f})")
        if temp_compliance < self.criteria.min_comfort_compliance:
            issues.append(f"Temperature issues ({temp_compliance:.1f}% compliance)")
        if co2_compliance < self.criteria.min_comfort_compliance:
            issues.append(f"CO2 issues ({co2_compliance:.1f}% compliance)")
        if humidity_compliance < self.criteria.min_comfort_compliance:
            issues.append(f"Humidity issues ({humidity_compliance:.1f}% compliance)")
        
        return {
            'room_id': room_id,
            'building_id': building_id,
            'performance_score': round(performance_score, 2),
            'data_quality_score': quality_score,
            'temperature_compliance': temp_compliance,
            'co2_compliance': co2_compliance,
            'humidity_compliance': humidity_compliance,
            'issues': issues,
            'issue_count': len(issues),
            'total_records': data_quality.get('total_records', 0)
        }
    
    def _calculate_summary_statistics(self, room_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for all rooms."""
        if not room_scores:
            return {}
        
        scores = [r['performance_score'] for r in room_scores]
        quality_scores = [r['data_quality_score'] for r in room_scores]
        temp_compliance = [r['temperature_compliance'] for r in room_scores]
        co2_compliance = [r['co2_compliance'] for r in room_scores]
        humidity_compliance = [r['humidity_compliance'] for r in room_scores]
        
        return {
            'total_rooms': len(room_scores),
            'performance_scores': {
                'mean': round(np.mean(scores), 2),
                'median': round(np.median(scores), 2),
                'std': round(np.std(scores), 2),
                'min': round(np.min(scores), 2),
                'max': round(np.max(scores), 2),
                'q25': round(np.percentile(scores, 25), 2),
                'q75': round(np.percentile(scores, 75), 2)
            },
            'data_quality': {
                'mean': round(np.mean(quality_scores), 3),
                'rooms_below_threshold': sum(1 for q in quality_scores if q < self.criteria.min_data_quality)
            },
            'compliance_summary': {
                'temperature': {
                    'mean': round(np.mean(temp_compliance), 1),
                    'rooms_below_threshold': sum(1 for c in temp_compliance if c < self.criteria.min_comfort_compliance)
                },
                'co2': {
                    'mean': round(np.mean(co2_compliance), 1),
                    'rooms_below_threshold': sum(1 for c in co2_compliance if c < self.criteria.min_comfort_compliance)
                },
                'humidity': {
                    'mean': round(np.mean(humidity_compliance), 1),
                    'rooms_below_threshold': sum(1 for c in humidity_compliance if c < self.criteria.min_comfort_compliance)
                }
            }
        }
    
    def prepare_comparison_data(
        self,
        room_analyses: List[Dict[str, Any]],
        metric: str = 'performance_score',
        group_by: str = 'building'
    ) -> Dict[str, Any]:
        """
        Prepare data for comparison charts.
        
        Args:
            room_analyses: Room analysis results
            metric: Metric to compare ('performance_score', 'temperature_compliance', etc.)
            group_by: How to group data ('building', 'room_type', 'none')
            
        Returns:
            Processed data ready for chart generation
        """
        comparison_data = {
            'metric': metric,
            'group_by': group_by,
            'data': [],
            'summary': {}
        }
        
        # Extract data based on metric
        for analysis in room_analyses:
            room_id = analysis.get('room_id')
            building_id = analysis.get('building_id')
            
            value = self._extract_metric_value(analysis, metric)
            if value is not None:
                comparison_data['data'].append({
                    'room_id': room_id,
                    'building_id': building_id,
                    'value': value,
                    'label': f"{room_id}" if group_by == 'none' else f"{building_id}_{room_id}"
                })
        
        # Group data if requested
        if group_by == 'building':
            grouped_data = {}
            for item in comparison_data['data']:
                building = item['building_id']
                if building not in grouped_data:
                    grouped_data[building] = []
                grouped_data[building].append(item)
            comparison_data['grouped'] = grouped_data
        
        # Calculate summary statistics
        values = [item['value'] for item in comparison_data['data']]
        if values:
            comparison_data['summary'] = {
                'count': len(values),
                'mean': round(np.mean(values), 2),
                'median': round(np.median(values), 2),
                'std': round(np.std(values), 2),
                'min': round(np.min(values), 2),
                'max': round(np.max(values), 2)
            }
        
        return comparison_data
    
    def _extract_metric_value(self, analysis: Dict[str, Any], metric: str) -> Optional[float]:
        """Extract specific metric value from analysis results."""
        if metric == 'performance_score':
            score_data = self._calculate_performance_score(analysis)
            return score_data['performance_score'] if score_data else None
        
        elif metric == 'data_quality_score':
            return analysis.get('data_quality', {}).get('overall_score', None)
        
        elif metric.endswith('_compliance'):
            # Extract compliance percentages
            param = metric.replace('_compliance', '')
            comfort_analysis = analysis.get('comfort_analysis', {})
            if param in comfort_analysis:
                cat_ii = comfort_analysis[param].get('II', {})
                return cat_ii.get('compliance_percentage', None)
        
        elif metric in ['temperature_mean', 'co2_mean', 'humidity_mean']:
            # Extract basic statistics
            param = metric.replace('_mean', '')
            basic_stats = analysis.get('basic_statistics', {})
            for col, stats in basic_stats.items():
                if param.lower() in col.lower():
                    return stats.get('mean', None)
        
        elif metric == 'total_records':
            return analysis.get('data_quality', {}).get('total_records', None)
        
        elif metric.startswith('ach_'):
            # Air change rate metrics
            ach_metrics = analysis.get('ach_metrics', {})
            ach_param = metric.replace('ach_', '')
            return ach_metrics.get(f'ach_{ach_param}', None)
        
        return None
    
    def prepare_time_series_data(
        self,
        ieq_data_list: List[IEQData],
        parameters: Optional[List[str]] = None,
        resample_freq: str = 'h'
    ) -> Dict[str, Any]:
        """
        Prepare time series data for plotting.
        
        Args:
            ieq_data_list: List of IEQ data objects
            parameters: Parameters to include in time series
            resample_freq: Resampling frequency for data
            
        Returns:
            Processed time series data
        """
        if parameters is None:
            parameters = ['temperature', 'co2', 'humidity']
        
        time_series_data = {
            'parameters': parameters,
            'resample_freq': resample_freq,
            'data': {},
            'summary': {}
        }
        
        for ieq_data in ieq_data_list:
            room_id = ieq_data.room_id
            data = ieq_data.data.copy()
            
            # Resample data if needed
            if resample_freq != 'original':
                data = data.resample(resample_freq).mean()
            
            # Extract relevant parameters
            room_data = {}
            for param in parameters:
                param_cols = [col for col in data.columns if param.lower() in col.lower()]
                if param_cols:
                    room_data[param] = data[param_cols[0]].dropna()
            
            if room_data:
                time_series_data['data'][room_id] = room_data
        
        # Calculate summary statistics across all rooms
        for param in parameters:
            all_values = []
            for room_data in time_series_data['data'].values():
                if param in room_data:
                    all_values.extend(room_data[param].values)
            
            if all_values:
                time_series_data['summary'][param] = {
                    'mean': round(np.mean(all_values), 2),
                    'std': round(np.std(all_values), 2),
                    'min': round(np.min(all_values), 2),
                    'max': round(np.max(all_values), 2)
                }
        
        return time_series_data
    
    def prepare_heatmap_data(
        self,
        ieq_data: IEQData,
        parameter: str,
        aggregation: str = 'daily_hourly'
    ) -> Dict[str, Any]:
        """
        Prepare data for heatmap visualization.
        
        Args:
            ieq_data: IEQ data object
            parameter: Parameter to visualize
            aggregation: Type of aggregation ('daily_hourly', 'monthly_daily', etc.)
            
        Returns:
            Processed heatmap data
        """
        data = ieq_data.data.copy()
        
        # Find parameter column
        param_col = None
        for col in data.columns:
            if parameter.lower() in col.lower():
                param_col = col
                break
        
        if param_col is None:
            return {'error': f'Parameter {parameter} not found in data'}
        
        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        heatmap_data = {
            'parameter': parameter,
            'aggregation': aggregation,
            'room_id': ieq_data.room_id,
            'data': None,
            'labels': {}
        }
        
        if aggregation == 'daily_hourly':
            # Hour of day vs. day aggregation
            data['hour'] = data.index.hour
            data['date'] = data.index.date
            
            pivot_data = data.pivot_table(
                values=param_col,
                index='date',
                columns='hour',
                aggfunc='mean'
            )
            
            heatmap_data['data'] = pivot_data
            heatmap_data['labels'] = {
                'x': 'Hour of Day',
                'y': 'Date',
                'title': f'{parameter.title()} - Daily Hourly Patterns'
            }
        
        elif aggregation == 'monthly_hourly':
            # Hour of day vs. month aggregation
            data['hour'] = data.index.hour
            data['month'] = data.index.month
            
            pivot_data = data.pivot_table(
                values=param_col,
                index='month',
                columns='hour',
                aggfunc='mean'
            )
            
            heatmap_data['data'] = pivot_data
            heatmap_data['labels'] = {
                'x': 'Hour of Day',
                'y': 'Month',
                'title': f'{parameter.title()} - Monthly Hourly Patterns'
            }
        
        elif aggregation == 'weekly_hourly':
            # Hour of day vs. day of week aggregation
            data['hour'] = data.index.hour
            data['dayofweek'] = data.index.dayofweek
            
            pivot_data = data.pivot_table(
                values=param_col,
                index='dayofweek',
                columns='hour',
                aggfunc='mean'
            )
            
            # Map day numbers to names
            day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            new_index = [day_names[i] for i in pivot_data.index]
            pivot_data.index = pd.Index(new_index)
            
            heatmap_data['data'] = pivot_data
            heatmap_data['labels'] = {
                'x': 'Hour of Day',
                'y': 'Day of Week',
                'title': f'{parameter.title()} - Weekly Hourly Patterns'
            }
        
        return heatmap_data
