"""
Analytics Data Aggregator

Collects and aggregates analytics data required by report templates.
Maps analytics tags to actual data from analysis results.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class AnalyticsDataAggregator:
    """
    Aggregates analytics data based on template requirements.
    
    Collects data from analysis results and organizes it according
    to the analytics tags specified in templates.
    """
    
    def __init__(self):
        """Initialize the aggregator."""
        self.analytics_cache = {}
    
    def collect_required_analytics(
        self,
        analysis_results: Any,
        required_tags: Set[str],
        required_parameters: Set[str],
        required_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Collect analytics data based on requirements.
        
        Args:
            analysis_results: Analysis results object or dict
            required_tags: Set of required analytics tags
            required_parameters: Set of required parameters
            required_level: Required analysis level (optional)
            
        Returns:
            Dictionary with collected analytics data
        """
        collected_data = {
            'statistics': {},
            'compliance': {},
            'temporal': {},
            'spatial': {},
            'recommendations': {},
            'data_quality': {},
            'performance': {},
            'weather': {}
        }
        
        # Convert analysis_results to dict if it's an object
        if hasattr(analysis_results, '__dict__'):
            results_dict = analysis_results.__dict__
        else:
            results_dict = analysis_results
        
        # Collect data based on tags
        for tag in required_tags:
            category, subcategory = tag.split('.') if '.' in tag else (tag, None)
            
            if category == 'statistics':
                self._collect_statistics(
                    results_dict, collected_data['statistics'],
                    subcategory, required_parameters
                )
            elif category == 'compliance':
                self._collect_compliance(
                    results_dict, collected_data['compliance'],
                    subcategory
                )
            elif category == 'temporal':
                self._collect_temporal(
                    results_dict, collected_data['temporal'],
                    subcategory
                )
            elif category == 'spatial':
                self._collect_spatial(
                    results_dict, collected_data['spatial'],
                    subcategory
                )
            elif category == 'recommendations':
                self._collect_recommendations(
                    results_dict, collected_data['recommendations'],
                    subcategory
                )
            elif category == 'data_quality':
                self._collect_data_quality(
                    results_dict, collected_data['data_quality'],
                    subcategory
                )
            elif category == 'performance':
                self._collect_performance(
                    results_dict, collected_data['performance'],
                    subcategory
                )
            elif category == 'weather':
                self._collect_weather(
                    results_dict, collected_data['weather'],
                    subcategory
                )
        
        # Add metadata
        collected_data['_metadata'] = {
            'tags_requested': list(required_tags),
            'parameters_requested': list(required_parameters),
            'level_requested': required_level,
            'data_available': self._check_data_availability(collected_data)
        }
        
        return collected_data
    
    def _collect_statistics(
        self,
        results: Dict[str, Any],
        target: Dict[str, Any],
        subcategory: str,
        required_parameters: Set[str]
    ) -> None:
        """Collect statistical data."""
        stats = results.get('statistics', {})
        
        if subcategory == 'basic':
            # Basic statistics for each parameter
            for param in required_parameters:
                if param in stats:
                    target[param] = {
                        'mean': stats[param].get('mean'),
                        'median': stats[param].get('median'),
                        'std': stats[param].get('std'),
                        'min': stats[param].get('min'),
                        'max': stats[param].get('max'),
                        'count': stats[param].get('count')
                    }
        
        elif subcategory == 'trends':
            # Trend analysis data
            target['trends'] = results.get('trends', {})
        
        elif subcategory == 'distribution':
            # Distribution data
            target['distribution'] = results.get('distribution', {})
    
    def _collect_compliance(
        self,
        results: Dict[str, Any],
        target: Dict[str, Any],
        subcategory: str
    ) -> None:
        """Collect compliance data."""
        test_results = results.get('test_results', {})
        test_aggs = results.get('test_aggregations', {})
        
        if subcategory == 'overall':
            # Overall compliance rates
            target['overall'] = {
                'avg_compliance_rate': results.get('avg_compliance_rate'),
                'test_aggregations': test_aggs
            }
        
        elif subcategory == 'temporal':
            # Time-based compliance
            target['temporal'] = {}
            for test_name, test_data in test_results.items():
                if 'opening_hours' in test_data or 'non_opening_hours' in test_data:
                    target['temporal'][test_name] = {
                        'opening_hours': test_data.get('opening_hours'),
                        'non_opening_hours': test_data.get('non_opening_hours')
                    }
        
        elif subcategory == 'spatial':
            # Space-based compliance (room comparisons)
            target['spatial'] = {
                'room_comparisons': results.get('room_comparisons', {}),
                'level_comparisons': results.get('level_comparisons', {})
            }
        
        elif subcategory == 'threshold':
            # Threshold-based compliance
            target['thresholds'] = {}
            for test_name, test_data in test_results.items():
                if 'threshold' in test_data:
                    target['thresholds'][test_name] = {
                        'threshold': test_data['threshold'],
                        'compliance_rate': test_data.get('compliance_rate'),
                        'non_compliant_hours': test_data.get('total_non_compliant_hours')
                    }
    
    def _collect_temporal(
        self,
        results: Dict[str, Any],
        target: Dict[str, Any],
        subcategory: str
    ) -> None:
        """Collect temporal analysis data."""
        # Temporal patterns (hourly, daily, weekly, etc.)
        target[subcategory] = results.get(f'{subcategory}_patterns', {})
    
    def _collect_spatial(
        self,
        results: Dict[str, Any],
        target: Dict[str, Any],
        subcategory: str
    ) -> None:
        """Collect spatial analysis data."""
        if subcategory == 'room_level':
            target['rooms'] = {
                'room_ids': results.get('room_ids', []),
                'room_count': results.get('room_count', 0)
            }
        
        elif subcategory == 'level_level':
            target['levels'] = {
                'level_ids': results.get('level_ids', []),
                'level_count': results.get('level_count', 0)
            }
        
        elif subcategory == 'building_level':
            target['buildings'] = {
                'building_id': results.get('building_id'),
                'building_name': results.get('building_name')
            }
        
        elif subcategory == 'comparison':
            target['comparisons'] = {
                'room_comparisons': results.get('room_comparisons', {}),
                'level_comparisons': results.get('level_comparisons', {})
            }
        
        elif subcategory == 'ranking':
            target['rankings'] = {
                'best_performing_rooms': results.get('best_performing_rooms', []),
                'worst_performing_rooms': results.get('worst_performing_rooms', []),
                'best_performing_levels': results.get('best_performing_levels', []),
                'worst_performing_levels': results.get('worst_performing_levels', [])
            }
    
    def _collect_recommendations(
        self,
        results: Dict[str, Any],
        target: Dict[str, Any],
        subcategory: str
    ) -> None:
        """Collect recommendations data."""
        recommendations = results.get('recommendations', [])
        
        if subcategory:
            # Filter by recommendation type
            filtered = [
                r for r in recommendations
                if r.get('category') == subcategory or r.get('type') == subcategory
            ]
            target[subcategory] = filtered
        else:
            target['all'] = recommendations
    
    def _collect_data_quality(
        self,
        results: Dict[str, Any],
        target: Dict[str, Any],
        subcategory: str
    ) -> None:
        """Collect data quality metrics."""
        if subcategory == 'completeness':
            target['completeness'] = {
                'overall_quality_score': results.get('avg_quality_score'),
                'quality_score': results.get('overall_quality_score')
            }
        
        elif subcategory == 'accuracy':
            target['accuracy'] = results.get('data_accuracy', {})
    
    def _collect_performance(
        self,
        results: Dict[str, Any],
        target: Dict[str, Any],
        subcategory: str
    ) -> None:
        """Collect performance metrics."""
        if subcategory == 'scoring':
            target['scores'] = {
                'avg_compliance_rate': results.get('avg_compliance_rate'),
                'avg_quality_score': results.get('avg_quality_score')
            }
        
        elif subcategory == 'ranking':
            target['rankings'] = {
                'best_performing': results.get('best_performing_rooms', [])[:10],
                'worst_performing': results.get('worst_performing_rooms', [])[:10]
            }
    
    def _collect_weather(
        self,
        results: Dict[str, Any],
        target: Dict[str, Any],
        subcategory: str
    ) -> None:
        """Collect weather correlation data."""
        weather_data = results.get('weather_correlation_summary', {})
        
        if subcategory == 'correlation':
            target['correlations'] = {
                'avg_correlations': weather_data.get('avg_correlations', {}),
                'strongest_correlations': weather_data.get('strongest_correlations', [])
            }
        
        elif subcategory == 'impact':
            target['impact'] = {
                'has_correlations': weather_data.get('has_correlations', False),
                'significant_correlations': weather_data.get('significant_correlations', [])
            }
    
    def _check_data_availability(self, collected_data: Dict[str, Any]) -> Dict[str, bool]:
        """Check which categories of data are available."""
        availability = {}
        
        for category, data in collected_data.items():
            if category.startswith('_'):
                continue
            
            # Check if category has any data
            has_data = False
            if isinstance(data, dict):
                has_data = len(data) > 0 and any(
                    v is not None and v != {} and v != []
                    for v in data.values()
                )
            elif isinstance(data, list):
                has_data = len(data) > 0
            else:
                has_data = data is not None
            
            availability[category] = has_data
        
        return availability
    
    def validate_requirements_met(
        self,
        collected_data: Dict[str, Any],
        required_tags: Set[str]
    ) -> Dict[str, Any]:
        """
        Validate that collected data meets requirements.
        
        Args:
            collected_data: Collected analytics data
            required_tags: Required analytics tags
            
        Returns:
            Validation result with missing data info
        """
        availability = collected_data.get('_metadata', {}).get('data_available', {})
        
        missing_categories = []
        for tag in required_tags:
            category = tag.split('.')[0] if '.' in tag else tag
            if not availability.get(category, False):
                missing_categories.append(category)
        
        return {
            'all_requirements_met': len(missing_categories) == 0,
            'missing_categories': list(set(missing_categories)),
            'available_categories': [k for k, v in availability.items() if v],
            'coverage_percentage': (
                len([v for v in availability.values() if v]) / len(availability) * 100
                if availability else 0
            )
        }
    
    def load_room_data_for_analysis(
        self,
        room_ids: List[str],
        rooms_dir: Path = Path("output/analysis/rooms")
    ) -> Dict[str, Dict[str, Any]]:
        """
        Load room data from JSON files for detailed analysis.
        
        Args:
            room_ids: List of room IDs to load
            rooms_dir: Directory containing room JSON files
            
        Returns:
            Dictionary mapping room_id to room data
        """
        room_data = {}
        
        for room_id in room_ids:
            room_file = rooms_dir / f"{room_id}.json"
            
            if not room_file.exists():
                logger.warning(f"Room file not found: {room_file}")
                continue
            
            try:
                with open(room_file, 'r') as f:
                    room_data[room_id] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading room {room_id}: {e}")
                continue
        
        logger.info(f"Loaded {len(room_data)}/{len(room_ids)} room data files")
        return room_data
