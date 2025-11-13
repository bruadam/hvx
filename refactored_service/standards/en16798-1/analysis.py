"""
EN 16798-1 Standard Analysis Module

This module implements EN 16798-1 compliance assessment using the
refactored service architecture with RuleSet and TestRule models.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
import yaml
from pathlib import Path

# Import from refactored calculators
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from calculators.en16798_calculator import EN16798Calculator
from core.models import (
    RuleSet,
    TestRule,
    TestResult,
    ComplianceAnalysis,
    SpatialEntity,
    MetricType,
    RuleOperator,
    StandardType,
    AnalysisStatus,
    AnalysisType,
    ApplicabilityCondition,
    VentilationType,
)


def load_config() -> Dict[str, Any]:
    """Load the EN16798-1 configuration file."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_rulesets_from_config(config: Dict[str, Any]) -> List[RuleSet]:
    """
    Create RuleSet objects from config file.

    Returns:
        List of RuleSet objects for each category
    """
    rulesets = []

    for ruleset_config in config.get('rulesets', []):
        category = ruleset_config['category']

        # Create test rules
        rules = []
        for rule_config in ruleset_config.get('rules', []):
            # Map metric string to MetricType enum
            metric_map = {
                'temperature': MetricType.TEMPERATURE,
                'co2': MetricType.CO2,
                'humidity': MetricType.HUMIDITY,
            }
            metric = metric_map.get(rule_config['metric'], MetricType.OTHER)

            # Map operator string to RuleOperator enum
            operator_map = {
                'between': RuleOperator.BETWEEN,
                '<=': RuleOperator.LE,
                '<': RuleOperator.LT,
                '>=': RuleOperator.GE,
                '>': RuleOperator.GT,
                '==': RuleOperator.EQ,
            }
            operator = operator_map.get(rule_config['operator'], RuleOperator.LE)

            rule = TestRule(
                id=rule_config['id'],
                name=rule_config['name'],
                metric=metric,
                operator=operator,
                target_value=rule_config.get('target_value'),
                lower_bound=rule_config.get('lower_bound'),
                upper_bound=rule_config.get('upper_bound'),
                tolerance_hours=rule_config.get('tolerance_hours'),
                tolerance_percentage=rule_config.get('tolerance_percentage'),
                applies_during=rule_config.get('applies_during'),
                metadata={
                    'unit': rule_config.get('unit', ''),
                    'season': rule_config.get('season', 'all_year'),
                }
            )
            rules.append(rule)

        # Create applicability conditions
        applicability = config.get('applicability', {})
        conditions = [
            ApplicabilityCondition(
                id=f"en16798_{category}_applicability",
                countries=applicability.get('countries'),
                regions=applicability.get('regions'),
                building_types=applicability.get('building_types'),
                ventilation_types=[
                    VentilationType(vt) for vt in applicability.get('ventilation_types', [])
                ] if applicability.get('ventilation_types') else None,
            )
        ]

        # Create ruleset
        ruleset = RuleSet(
            id=f"en16798_cat_{category}",
            name=f"EN 16798-1 Category {category}",
            standard=StandardType.EN16798,
            category=category,
            rules=rules,
            applicability_conditions=conditions,
            metadata={
                'version': config.get('version', '2024.1'),
                'ventilation_rate': config.get('ventilation_rates', {}).get(category),
            }
        )
        rulesets.append(ruleset)

    return rulesets


def run(
    spatial_entity: SpatialEntity,
    timeseries_dict: Dict[str, List[float]],
    timestamps: List[str],
    season: str = "winter",
    categories: Optional[List[str]] = None,
    **kwargs
) -> ComplianceAnalysis:
    """
    Run EN 16798-1 compliance analysis for a spatial entity.

    Args:
        spatial_entity: The spatial entity to analyze
        timeseries_dict: Dict mapping metric names to value lists
        timestamps: List of timestamp strings
        season: "winter" or "summer"
        categories: List of categories to check (default: all)
        **kwargs: Additional configuration

    Returns:
        ComplianceAnalysis object with results
    """
    import pandas as pd
    from datetime import datetime

    # Load configuration
    config = load_config()

    # Create rulesets
    rulesets = create_rulesets_from_config(config)

    # Filter categories if specified
    if categories:
        rulesets = [rs for rs in rulesets if rs.category in categories]

    # Use EN16798Calculator for actual computation
    calculator = EN16798Calculator()

    # Convert timeseries to pandas Series
    ts_data = {}
    ts_index = pd.to_datetime(timestamps) if timestamps else None

    for metric, values in timeseries_dict.items():
        if metric in ['temperature', 'co2', 'humidity', 'outdoor_temperature']:
            ts_data[metric] = pd.Series(values, index=ts_index) if ts_index else pd.Series(values)

    # Determine ventilation type
    vent_type_map = {
        VentilationType.NATURAL: 'natural',
        VentilationType.MECHANICAL: 'mechanical',
        VentilationType.MIXED: 'mixed',
    }
    from calculators.en16798_calculator import VentilationType as CalcVentType
    vent_type = CalcVentType.MECHANICAL
    if spatial_entity.ventilation_type and spatial_entity.ventilation_type != VentilationType.UNKNOWN:
        vent_str = vent_type_map.get(spatial_entity.ventilation_type, 'mechanical')
        vent_type = CalcVentType(vent_str)

    # Run calculator assessment
    from calculators.en16798_calculator import EN16798Category

    cat_map = {'I': EN16798Category.CATEGORY_I, 'II': EN16798Category.CATEGORY_II,
               'III': EN16798Category.CATEGORY_III, 'IV': EN16798Category.CATEGORY_IV}
    categories_to_check = [cat_map[rs.category] for rs in rulesets if rs.category in cat_map]

    calc_result = calculator.assess_timeseries_compliance(
        temperature=ts_data.get('temperature'),
        co2=ts_data.get('co2'),
        humidity=ts_data.get('humidity'),
        outdoor_temperature=ts_data.get('outdoor_temperature'),
        season=season,
        ventilation_type=vent_type,
        categories_to_check=categories_to_check,
    )

    # Convert calculator results to TestResult objects
    test_results = []
    for category_key, category_data in calc_result.items():
        compliance_rate = category_data.get('compliance_rate', 0.0)
        passed = compliance_rate >= 95.0  # Pass if >= 95% compliant

        test_result = TestResult(
            id=f"test_{spatial_entity.id}_{category_key}",
            name=f"EN16798 Category {category_key} Test",
            type=AnalysisType.TEST_RESULT,
            spatial_entity_id=spatial_entity.id,
            rule_id=f"en16798_cat_{category_key}",
            pass_=passed,
            out_of_range_percentage=100.0 - compliance_rate,
            status=AnalysisStatus.COMPLETED,
            details={
                'compliance_rate': compliance_rate,
                'category': category_key,
                'thresholds': category_data.get('thresholds', {}),
            }
        )
        test_results.append(test_result)

    # Determine overall compliance (best achieved category)
    overall_pass = any(tr.pass_ for tr in test_results)
    best_category = None
    best_compliance = 0.0
    for tr in test_results:
        compliance = tr.details.get('compliance_rate', 0.0)
        if tr.pass_ and compliance > best_compliance:
            best_compliance = compliance
            best_category = tr.details.get('category')

    # Create ComplianceAnalysis
    analysis = ComplianceAnalysis(
        id=f"compliance_{spatial_entity.id}_en16798",
        name=f"EN 16798-1 Compliance for {spatial_entity.name}",
        type=AnalysisType.COMPLIANCE,
        spatial_entity_id=spatial_entity.id,
        rule_set_id=f"en16798_multi_category",
        test_result_ids=[tr.id for tr in test_results],
        overall_pass=overall_pass,
        status=AnalysisStatus.COMPLETED,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        summary_results={
            'best_category': best_category,
            'best_compliance_rate': best_compliance,
            'tested_categories': [tr.details.get('category') for tr in test_results],
            'season': season,
            'standard': 'EN16798-1',
            'version': config.get('version', '2024.1'),
        }
    )

    return analysis


# Convenience function for backward compatibility
def analyze(
    spatial_entity: SpatialEntity,
    temperature: Optional[List[float]] = None,
    co2: Optional[List[float]] = None,
    humidity: Optional[List[float]] = None,
    outdoor_temperature: Optional[List[float]] = None,
    timestamps: Optional[List[str]] = None,
    season: str = "winter",
    categories: Optional[List[str]] = None,
) -> ComplianceAnalysis:
    """
    Convenience function for EN 16798-1 analysis.

    Args:
        spatial_entity: Entity to analyze
        temperature: Temperature values (°C)
        co2: CO2 values (ppm)
        humidity: Relative humidity values (%)
        outdoor_temperature: Outdoor temperature values (°C)
        timestamps: Timestamp strings
        season: "winter" or "summer"
        categories: Categories to check

    Returns:
        ComplianceAnalysis with results
    """
    timeseries_dict = {}
    if temperature:
        timeseries_dict['temperature'] = temperature
    if co2:
        timeseries_dict['co2'] = co2
    if humidity:
        timeseries_dict['humidity'] = humidity
    if outdoor_temperature:
        timeseries_dict['outdoor_temperature'] = outdoor_temperature

    return run(
        spatial_entity=spatial_entity,
        timeseries_dict=timeseries_dict,
        timestamps=timestamps or [],
        season=season,
        categories=categories,
    )


if __name__ == "__main__":
    # Test the configuration loading
    config = load_config()
    print(f"Loaded EN 16798-1 config: {config['name']}")
    print(f"Version: {config['version']}")
    print(f"Categories: {[c['id'] for c in config['categories']]}")

    # Create rulesets
    rulesets = create_rulesets_from_config(config)
    print(f"\nCreated {len(rulesets)} rulesets:")
    for rs in rulesets:
        print(f"  - {rs.name}: {len(rs.rules)} rules")
