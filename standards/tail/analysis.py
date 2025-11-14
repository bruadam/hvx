"""
TAIL Standard Analysis Module

This module implements TAIL (Thermal, Acoustic, Indoor Air Quality, Luminous)
rating assessment using the refactored service architecture.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
import yaml
from pathlib import Path
from datetime import timezone

from .calculator import TAILCalculator, TAILCategory
from core.rules import RuleSet, TestRule, ApplicabilityCondition
from core.analysis import (
    TestResult,
    ComplianceAnalysis,
    AnalysisStatus,
    AnalysisType,
)
from core.spacial_entity import SpatialEntity
from core.enums import MetricType, RuleOperator, StandardType


def load_config() -> Dict[str, Any]:
    """Load the TAIL configuration file."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_thresholds_for_building_type(
    config: Dict[str, Any],
    building_type: Optional[str] = None
) -> Dict[str, Dict[str, float]]:
    """
    Get thresholds for a specific building type.

    Args:
        config: Loaded configuration
        building_type: Building type (office, school, residential, etc.)

    Returns:
        Dict of parameter -> {lower_bound, upper_bound} thresholds
    """
    default_thresholds = config.get('default_thresholds', {})
    building_thresholds = config.get('building_type_thresholds', {})

    # Start with defaults
    thresholds = {}
    for param, param_config in default_thresholds.items():
        thresholds[param] = {
            'lower': param_config.get('lower_bound', float('-inf')),
            'upper': param_config.get('upper_bound', float('inf')),
        }

    # Override with building-specific thresholds if available
    if building_type and building_type in building_thresholds:
        for param, param_config in building_thresholds[building_type].items():
            if param in thresholds:
                if 'lower_bound' in param_config:
                    thresholds[param]['lower'] = param_config['lower_bound']
                if 'upper_bound' in param_config:
                    thresholds[param]['upper'] = param_config['upper_bound']
            else:
                thresholds[param] = {
                    'lower': param_config.get('lower_bound', float('-inf')),
                    'upper': param_config.get('upper_bound', float('inf')),
                }

    return thresholds


def create_rules_from_config(config: Dict[str, Any]) -> List[TestRule]:
    """
    Create TestRule objects from TAIL configuration.

    Returns:
        List of TestRule objects for all parameters
    """
    rules = []
    default_thresholds = config.get('default_thresholds', {})

    # Metric name mapping
    metric_map = {
        'temperature': MetricType.TEMPERATURE,
        'humidity': MetricType.HUMIDITY,
        'co2': MetricType.CO2,
        'pm25': MetricType.OTHER,
        'pm10': MetricType.OTHER,
        'voc': MetricType.OTHER,
        'tvoc': MetricType.OTHER,
        'noise': MetricType.NOISE,
        'sound_level': MetricType.NOISE,
        'illuminance': MetricType.ILLUMINANCE,
        'daylight_factor': MetricType.OTHER,
    }

    for param_name, param_config in default_thresholds.items():
        metric = metric_map.get(param_name, MetricType.OTHER)
        domain = param_config.get('domain', 'other')

        # Determine operator
        has_lower = 'lower_bound' in param_config
        has_upper = 'upper_bound' in param_config

        if has_lower and has_upper:
            operator = RuleOperator.BETWEEN
        elif has_upper:
            operator = RuleOperator.LE
        elif has_lower:
            operator = RuleOperator.GE
        else:
            continue

        rule = TestRule(
            id=f"tail_{param_name}",
            name=f"TAIL {param_config.get('description', param_name)}",
            metric=metric,
            operator=operator,
            lower_bound=param_config.get('lower_bound'),
            upper_bound=param_config.get('upper_bound'),
            tolerance_percentage=config.get('compliance_settings', {}).get('tolerance_percentage', 5.0),
            applies_during="always",
            metadata={
                'unit': param_config.get('unit', ''),
                'domain': domain,
                'parameter': param_name,
            }
        )
        rules.append(rule)

    return rules


def create_ruleset_from_config(config: Dict[str, Any]) -> RuleSet:
    """
    Create a RuleSet object from TAIL configuration.

    Returns:
        RuleSet object for TAIL assessment
    """
    rules = create_rules_from_config(config)

    # Create applicability conditions
    applicability = config.get('applicability', {})
    conditions = [
        ApplicabilityCondition(
            id="tail_general_applicability",
            countries=applicability.get('countries'),
            regions=applicability.get('regions'),
            building_types=applicability.get('building_types'),
        )
    ]

    # Create ruleset
    ruleset = RuleSet(
        id="tail_rating",
        name="TAIL Indoor Environmental Quality Rating",
        standard=StandardType.TAIL,
        category=None,  # TAIL doesn't have predefined categories
        rules=rules,
        applicability_conditions=conditions,
        metadata={
            'version': config.get('version', '2024.1'),
            'aggregation_method': config.get('aggregation_method', 'worst'),
            'domains': [d['id'] for d in config.get('domains', [])],
        }
    )

    return ruleset


def run(
    spatial_entity: SpatialEntity,
    timeseries_dict: Dict[str, List[float]],
    timestamps: List[str],
    custom_thresholds: Optional[Dict[str, Dict[str, float]]] = None,
    **kwargs
) -> ComplianceAnalysis:
    """
    Run TAIL rating assessment for a spatial entity.

    Args:
        spatial_entity: The spatial entity to analyze
        timeseries_dict: Dict mapping metric names to value lists
        timestamps: List of timestamp strings
        custom_thresholds: Optional custom thresholds override
        **kwargs: Additional configuration

    Returns:
        ComplianceAnalysis object with TAIL results
    """
    import pandas as pd
    from datetime import datetime

    # Load configuration
    config = load_config()

    # Create ruleset
    ruleset = create_ruleset_from_config(config)

    # Get thresholds (building-type specific or custom)
    if custom_thresholds:
        thresholds = custom_thresholds
    else:
        thresholds = get_thresholds_for_building_type(
            config,
            spatial_entity.building_type or spatial_entity.room_type
        )

    # Use TAILCalculator for actual computation
    calculator = TAILCalculator()

    # Convert timeseries to pandas Series
    ts_data = {}
    ts_index = pd.to_datetime(timestamps) if timestamps else None

    for metric, values in timeseries_dict.items():
        if ts_index is not None and len(values) == len(ts_index):
            ts_data[metric] = pd.Series(values, index=ts_index)
        else:
            ts_data[metric] = pd.Series(values)

    season_hint = kwargs.get('season')
    if isinstance(season_hint, str):
        season_hint_normalized = season_hint.lower()
        if season_hint_normalized in ("heating", "cooling"):
            mapped_season = season_hint_normalized
        elif season_hint_normalized in ("winter", "autumn"):
            mapped_season = "heating"
        else:
            mapped_season = "non_heating"
    else:
        mapped_season = None

    metadata = {
        'building_type': spatial_entity.building_type,
        'room_type': spatial_entity.room_type,
        'area_m2': getattr(spatial_entity, 'area_m2', None),
        'design_occupancy': getattr(spatial_entity, 'design_occupancy', None),
        'entity_name': spatial_entity.name,
        'season_hint': mapped_season,
    }

    # Run calculator assessment
    tail_result = calculator.assess_timeseries(
        ts_data,
        thresholds,
        metadata=metadata,
        building_name=spatial_entity.name,
    )

    # Create TestResult for each domain
    test_results = []
    domain_map = {
        TAILCategory.THERMAL: 'thermal',
        TAILCategory.ACOUSTIC: 'acoustic',
        TAILCategory.IAQ: 'iaq',
        TAILCategory.LUMINOUS: 'luminous',
    }

    for domain_enum, domain_name in domain_map.items():
        if domain_enum in tail_result.categories:
            domain_result = tail_result.categories[domain_enum]

            test_result = TestResult(
                id=f"test_{spatial_entity.id}_{domain_name}",
                name=f"TAIL {domain_name.title()} Assessment",
                type=AnalysisType.TEST_RESULT,
                spatial_entity_id=spatial_entity.id,
                rule_id=f"tail_{domain_name}",
                successful=domain_result.rating.value <= 2,  # Pass if Rating I or II
                out_of_range_percentage=100.0 - domain_result.compliance_rate,
                status=AnalysisStatus.COMPLETED,
                details={
                    'domain': domain_name,
                    'rating': domain_result.rating.value,
                    'rating_label': domain_result.rating_label,
                    'compliance_rate': domain_result.compliance_rate,
                    'parameter_count': domain_result.parameter_count,
                    'dominant_color': domain_result.dominant_color,
                }
            )
            test_results.append(test_result)

    # Determine overall pass (all domains pass or at least overall rating <= 2)
    overall_pass = tail_result.overall_rating.value <= 2

    # Get rating information from config
    ratings_config = config.get('ratings', [])
    rating_info = next(
        (r for r in ratings_config if r['value'] == tail_result.overall_rating.value),
        {}
    )

    # Create ComplianceAnalysis
    parameter_payload = {
        param.parameter: {
            'rating': param.rating_label,
            'rating_value': param.rating.value,
            'dominant_color': param.dominant_color,
            'distribution': param.distribution,
            'sample_count': param.sample_count,
            'summary_value': param.summary_value,
            'metadata': param.metadata,
        }
        for param in tail_result.parameter_results
    }

    summary_results = {
        'overall_rating': tail_result.overall_rating.value,
        'overall_rating_label': tail_result.overall_rating_label,
        'overall_compliance_rate': tail_result.overall_compliance_rate,
        'rating_color': rating_info.get('color', 'unknown'),
        'rating_description': rating_info.get('description', ''),
        'domains': {
            domain_name: {
                'rating': domain_result.rating.value,
                'rating_label': domain_result.rating_label,
                'compliance_rate': domain_result.compliance_rate,
                'dominant_color': domain_result.dominant_color,
                'parameter_count': domain_result.parameter_count,
            }
            for domain_enum, domain_name in domain_map.items()
            if domain_enum in tail_result.categories
            for domain_result in [tail_result.categories[domain_enum]]
        },
        'parameters': parameter_payload,
        'total_parameters': tail_result.total_parameters,
        'standard': 'TAIL',
        'version': config.get('version', '2024.1'),
        'visualization': tail_result.visualization,
        'graph_data': tail_result.visualization,
    }

    analysis = ComplianceAnalysis(
        id=f"compliance_{spatial_entity.id}_tail",
        name=f"TAIL Rating for {spatial_entity.name}",
        type=AnalysisType.COMPLIANCE,
        spatial_entity_id=spatial_entity.id,
        rule_set_id=ruleset.id,
        test_result_ids=[tr.id for tr in test_results],
        overall_pass=overall_pass,
        status=AnalysisStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
        summary_results=summary_results,
    )

    # Persist summary onto the spatial entity for downstream aggregations/visuals
    spatial_entity.computed_metrics['tail_overall_rating'] = tail_result.overall_rating.value
    spatial_entity.computed_metrics['tail_overall_rating_label'] = tail_result.overall_rating_label
    spatial_entity.computed_metrics['tail_domains'] = summary_results.get('domains', {})
    spatial_entity.computed_metrics['tail_visualization'] = tail_result.visualization
    spatial_entity.tail_rating = tail_result.overall_rating.value
    spatial_entity.tail_rating_label = tail_result.overall_rating_label
    spatial_entity.tail_domains = summary_results.get('domains', {})
    spatial_entity.tail_visualization = tail_result.visualization

    return analysis


# Convenience function for backward compatibility
def analyze(
    spatial_entity: SpatialEntity,
    temperature: Optional[List[float]] = None,
    co2: Optional[List[float]] = None,
    humidity: Optional[List[float]] = None,
    illuminance: Optional[List[float]] = None,
    noise: Optional[List[float]] = None,
    pm25: Optional[List[float]] = None,
    timestamps: Optional[List[str]] = None,
    custom_thresholds: Optional[Dict[str, Dict[str, float]]] = None,
) -> ComplianceAnalysis:
    """
    Convenience function for TAIL analysis.

    Args:
        spatial_entity: Entity to analyze
        temperature: Temperature values (°C)
        co2: CO2 values (ppm)
        humidity: Relative humidity values (%)
        illuminance: Illuminance values (lux)
        noise: Noise levels (dB(A))
        pm25: PM2.5 values (μg/m³)
        timestamps: Timestamp strings
        custom_thresholds: Custom threshold overrides

    Returns:
        ComplianceAnalysis with TAIL results
    """
    timeseries_dict = {}
    if temperature:
        timeseries_dict['temperature'] = temperature
    if co2:
        timeseries_dict['co2'] = co2
    if humidity:
        timeseries_dict['humidity'] = humidity
    if illuminance:
        timeseries_dict['illuminance'] = illuminance
    if noise:
        timeseries_dict['noise'] = noise
    if pm25:
        timeseries_dict['pm25'] = pm25

    return run(
        spatial_entity=spatial_entity,
        timeseries_dict=timeseries_dict,
        timestamps=timestamps or [],
        custom_thresholds=custom_thresholds,
    )


if __name__ == "__main__":
    # Test the configuration loading
    config = load_config()
    print(f"Loaded TAIL config: {config['name']}")
    print(f"Version: {config['version']}")

    # Show domains
    domains = config.get('domains', [])
    print(f"\nTAIL Domains ({len(domains)}):")
    for domain in domains:
        print(f"  - {domain['name']} ({domain['id']})")
        print(f"    Metrics: {', '.join(domain['metrics'])}")

    # Show ratings
    ratings = config.get('ratings', [])
    print(f"\nTAIL Ratings ({len(ratings)}):")
    for rating in ratings:
        print(f"  - Rating {rating['id']}: {rating['name']}")
        print(f"    Min compliance: {rating['min_compliance']}%")

    # Create ruleset
    ruleset = create_ruleset_from_config(config)
    print(f"\nCreated ruleset: {ruleset.name}")
    print(f"  Rules: {len(ruleset.rules)}")

    # Show default thresholds
    thresholds = get_thresholds_for_building_type(config, 'office')
    print(f"\nDefault thresholds for office:")
    for param, bounds in list(thresholds.items())[:5]:  # Show first 5
        print(f"  - {param}: {bounds}")
