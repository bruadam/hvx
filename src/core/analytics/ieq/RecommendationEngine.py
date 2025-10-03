"""
Recommendation Engine

Orchestrates the generation of smart recommendations by:
1. Checking and running prerequisite tests/analyses
2. Correlating non-compliance with weather parameters
3. Generating recommendations using analyzer modules

Design Principles:
- Checks if required tests have been run before generating recommendations
- Automatically triggers missing prerequisite tests
- Uses correlation analysis to identify root causes
- Generates prioritized, actionable recommendations
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from dataclasses import dataclass

from src.core.models import BuildingDataset, Room
from src.core.models.results.room_analysis import RoomAnalysis

# Import recommendation analyzers
from src.core.analytics.ieq.library.recommendations import (
    analyze_solar_shading_need,
    generate_solar_shading_recommendation,
    analyze_ventilation_need,
    VentilationRecommendation,
    analyze_hvac_performance,
    HVACRecommendation
)

# Import correlation functions
from src.core.analytics.ieq.library.correlations import (
    calculate_boolean_float_correlation,
    calculate_multiple_boolean_float_correlations,
    calculate_non_compliance_weather_stats
)


@dataclass
class PrerequisiteCheck:
    """Result of checking if prerequisites are met for a recommendation."""
    met: bool
    missing_tests: List[str]
    missing_data: List[str]
    can_auto_run: bool


@dataclass
class RecommendationResult:
    """A structured recommendation with evidence and priority."""
    recommendation_type: str  # 'solar_shading', 'ventilation', 'hvac', 'insulation'
    priority: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: str
    rationale: List[str]
    estimated_impact: str
    implementation_cost: str
    evidence: Dict[str, Any]
    weather_correlations: Optional[Dict[str, Any]] = None


class RecommendationEngine:
    """
    Generates smart recommendations based on analysis results and weather correlations.
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize recommendation engine.

        Args:
            config_dict: Optional configuration for analysis
        """
        self.config = config_dict or {}

    def generate_recommendations_for_room(
        self,
        room_data: Room,
        room_analysis: RoomAnalysis,
        weather_data: Optional[pd.DataFrame] = None,
        auto_run_prerequisites: bool = True
    ) -> List[RecommendationResult]:
        """
        Generate recommendations for a single room.

        Args:
            room_data: Room data with timeseries
            room_analysis: Existing analysis results for the room
            weather_data: Optional weather data for correlation analysis
            auto_run_prerequisites: If True, automatically run missing prerequisite tests

        Returns:
            List of recommendations sorted by priority
        """
        recommendations = []

        # Check for temperature-related issues (solar shading, HVAC)
        if self._has_temperature_issues(room_analysis):
            # Check prerequisites
            prereq_check = self._check_temperature_prerequisites(room_analysis)

            if not prereq_check.met and auto_run_prerequisites and prereq_check.can_auto_run:
                # Run missing tests
                self._run_prerequisite_tests(room_data, prereq_check.missing_tests)
                # Re-check prerequisites
                prereq_check = self._check_temperature_prerequisites(room_analysis)

            if prereq_check.met:
                # Generate temperature-related recommendations with weather correlation
                temp_recs = self._generate_temperature_recommendations(
                    room_data,
                    room_analysis,
                    weather_data
                )
                recommendations.extend(temp_recs)

        # Check for air quality issues (ventilation)
        if self._has_air_quality_issues(room_analysis):
            prereq_check = self._check_air_quality_prerequisites(room_analysis)

            if not prereq_check.met and auto_run_prerequisites and prereq_check.can_auto_run:
                self._run_prerequisite_tests(room_data, prereq_check.missing_tests)
                prereq_check = self._check_air_quality_prerequisites(room_analysis)

            if prereq_check.met:
                ventilation_rec = self._generate_ventilation_recommendation(
                    room_analysis,
                    weather_data
                )
                if ventilation_rec:
                    recommendations.append(ventilation_rec)

        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

        return recommendations

    def _has_temperature_issues(self, room_analysis: RoomAnalysis) -> bool:
        """Check if room has temperature compliance issues."""
        # Check test results for temperature violations
        if not room_analysis.test_results:
            return False

        for test_name, test_result in room_analysis.test_results.items():
            if 'temp' in test_name.lower() or 'temperature' in test_name.lower():
                compliance_rate = test_result.get('compliance_rate', 100)
                if compliance_rate < 90:  # Less than 90% compliance
                    return True

        return False

    def _has_air_quality_issues(self, room_analysis: RoomAnalysis) -> bool:
        """Check if room has air quality issues."""
        if not room_analysis.test_results:
            return False

        for test_name, test_result in room_analysis.test_results.items():
            if 'co2' in test_name.lower() or 'humidity' in test_name.lower():
                compliance_rate = test_result.get('compliance_rate', 100)
                if compliance_rate < 90:
                    return True

        return False

    def _check_temperature_prerequisites(self, room_analysis: RoomAnalysis) -> PrerequisiteCheck:
        """Check if temperature analysis prerequisites are met."""
        missing_tests = []
        missing_data = []

        # Required: Temperature tests during summer/non-heating season
        has_summer_temp_test = False
        if room_analysis.test_results:
            for test_name in room_analysis.test_results.keys():
                if ('temp' in test_name.lower() and
                    ('summer' in test_name.lower() or 'non_heating' in test_name.lower())):
                    has_summer_temp_test = True
                    break

        if not has_summer_temp_test:
            missing_tests.append('summer_temperature_test')

        can_auto_run = len(missing_tests) > 0 and len(missing_data) == 0

        return PrerequisiteCheck(
            met=len(missing_tests) == 0 and len(missing_data) == 0,
            missing_tests=missing_tests,
            missing_data=missing_data,
            can_auto_run=can_auto_run
        )

    def _check_air_quality_prerequisites(self, room_analysis: RoomAnalysis) -> PrerequisiteCheck:
        """Check if air quality analysis prerequisites are met."""
        missing_tests = []
        missing_data = []

        # Required: CO2 tests
        has_co2_test = False
        if room_analysis.test_results:
            for test_name in room_analysis.test_results.keys():
                if 'co2' in test_name.lower():
                    has_co2_test = True
                    break

        if not has_co2_test:
            missing_tests.append('co2_test')

        can_auto_run = len(missing_tests) > 0 and len(missing_data) == 0

        return PrerequisiteCheck(
            met=len(missing_tests) == 0 and len(missing_data) == 0,
            missing_tests=missing_tests,
            missing_data=missing_data,
            can_auto_run=can_auto_run
        )

    def _run_prerequisite_tests(self, room_data: Room, missing_tests: List[str]):
        """
        Run missing prerequisite tests.

        Args:
            room_data: Room data to analyze
            missing_tests: List of missing test identifiers
        """
        # This would trigger the actual test execution
        # For now, this is a placeholder that would integrate with the test engine
        pass

    def _generate_temperature_recommendations(
        self,
        room_data: Room,
        room_analysis: RoomAnalysis,
        weather_data: Optional[pd.DataFrame]
    ) -> List[RecommendationResult]:
        """Generate temperature-related recommendations with weather correlation."""
        recommendations = []

        # Extract summer compliance rate
        summer_compliance = self._get_summer_temperature_compliance(room_analysis)

        if summer_compliance is None or summer_compliance >= 90:
            return recommendations

        # Correlate non-compliance with weather if data available
        weather_correlations = None
        outdoor_temp_corr = 0.0
        solar_radiation_corr = 0.0
        avg_outdoor_temp_during_issues = None
        avg_radiation_during_issues = None

        if weather_data is not None and not weather_data.empty:
            # Get non-compliance mask
            non_compliance_mask = self._create_temperature_non_compliance_mask(
                room_data,
                room_analysis
            )

            if non_compliance_mask is not None:
                # Calculate correlations
                weather_correlations = calculate_multiple_boolean_float_correlations(
                    non_compliance_mask,
                    weather_data,
                    weather_parameters=['outdoor_temperature', 'outdoor_temp', 'radiation', 'solar_radiation']
                )

                # Extract specific correlations
                outdoor_temp_corr = self._extract_correlation(
                    weather_correlations,
                    ['outdoor_temperature', 'outdoor_temp']
                )
                solar_radiation_corr = self._extract_correlation(
                    weather_correlations,
                    ['radiation', 'solar_radiation']
                )

                # Get weather stats during non-compliance
                weather_stats = calculate_non_compliance_weather_stats(
                    weather_data,
                    non_compliance_mask,
                    weather_parameters=['outdoor_temperature', 'outdoor_temp', 'radiation', 'solar_radiation']
                )

                avg_outdoor_temp_during_issues = weather_stats.get('outdoor_temperature', {}).get('mean') or \
                                                weather_stats.get('outdoor_temp', {}).get('mean')
                avg_radiation_during_issues = weather_stats.get('radiation', {}).get('mean') or \
                                             weather_stats.get('solar_radiation', {}).get('mean')

        # Generate solar shading recommendation
        needs_shading, priority, rationale = analyze_solar_shading_need(
            summer_compliance_rate=summer_compliance,
            outdoor_temp_correlation=outdoor_temp_corr,
            solar_radiation_correlation=solar_radiation_corr,
            avg_outdoor_temp_during_issues=avg_outdoor_temp_during_issues,
            avg_radiation_during_issues=avg_radiation_during_issues
        )

        if needs_shading:
            rec_dict = generate_solar_shading_recommendation(
                needs_shading,
                priority,
                rationale,
                summer_compliance
            )

            if rec_dict:
                recommendation = RecommendationResult(
                    recommendation_type='solar_shading',
                    priority=priority,
                    title=rec_dict['title'],
                    description=rec_dict['description'],
                    rationale=rec_dict['rationale'],
                    estimated_impact=rec_dict['estimated_impact'],
                    implementation_cost=rec_dict['implementation_cost'],
                    evidence=rec_dict['evidence'],
                    weather_correlations=weather_correlations
                )
                recommendations.append(recommendation)

        # Generate HVAC recommendation if temperature control is poor
        hvac_rec = self._generate_hvac_recommendation(room_analysis, weather_correlations)
        if hvac_rec:
            recommendations.append(hvac_rec)

        return recommendations

    def _generate_ventilation_recommendation(
        self,
        room_analysis: RoomAnalysis,
        weather_data: Optional[pd.DataFrame]
    ) -> Optional[RecommendationResult]:
        """Generate ventilation recommendation."""
        # Extract CO2 and humidity data
        co2_data = self._extract_co2_metrics(room_analysis)
        humidity_data = self._extract_humidity_metrics(room_analysis)

        if not co2_data:
            return None

        # Analyze ventilation need
        vent_rec = analyze_ventilation_need(
            co2_data=co2_data,
            humidity_data=humidity_data
        )

        if not vent_rec.needed:
            return None

        return RecommendationResult(
            recommendation_type='ventilation',
            priority=vent_rec.priority,
            title=f'Improve {vent_rec.ventilation_type.capitalize()} Ventilation',
            description=vent_rec.description,
            rationale=[f'Severity score: {vent_rec.severity_score:.2f}'] + vent_rec.issue_indicators,
            estimated_impact=f'{vent_rec.estimated_improvement:.1f}% improvement in air quality',
            implementation_cost='Varies by solution type',
            evidence={
                'co2_data': co2_data,
                'humidity_data': humidity_data,
                'recommended_ach': vent_rec.recommended_rate
            }
        )

    def _generate_hvac_recommendation(
        self,
        room_analysis: RoomAnalysis,
        weather_correlations: Optional[Dict[str, Any]]
    ) -> Optional[RecommendationResult]:
        """Generate HVAC system recommendation."""
        # Extract temperature control metrics
        temp_control = self._extract_temperature_control_metrics(room_analysis)
        setpoint_deviation = self._extract_setpoint_deviation_metrics(room_analysis)

        if not temp_control or not setpoint_deviation:
            return None

        # Analyze HVAC performance
        hvac_rec = analyze_hvac_performance(
            temperature_control=temp_control,
            setpoint_deviation=setpoint_deviation
        )

        if not hvac_rec.needed:
            return None

        return RecommendationResult(
            recommendation_type='hvac',
            priority=hvac_rec.priority,
            title='Optimize HVAC System Performance',
            description=hvac_rec.description,
            rationale=hvac_rec.recommended_actions,
            estimated_impact=f'{hvac_rec.estimated_improvement:.1f}% improvement',
            implementation_cost=f'Energy impact: {hvac_rec.energy_impact}',
            evidence={
                'temperature_control': temp_control,
                'issue_types': hvac_rec.issue_types
            },
            weather_correlations=weather_correlations
        )

    def _get_summer_temperature_compliance(self, room_analysis: RoomAnalysis) -> Optional[float]:
        """Extract summer temperature compliance rate."""
        if not room_analysis.test_results:
            return None

        for test_name, test_result in room_analysis.test_results.items():
            if ('temp' in test_name.lower() and
                ('summer' in test_name.lower() or 'non_heating' in test_name.lower())):
                return test_result.get('compliance_rate')

        return None

    def _create_temperature_non_compliance_mask(
        self,
        room_data: Room,
        room_analysis: RoomAnalysis
    ) -> Optional[pd.Series]:
        """Create boolean mask for temperature non-compliance periods."""
        # This would extract the actual non-compliance timestamps
        # For now, return None as placeholder
        # In real implementation, this would look at test results and create
        # a boolean series aligned with weather data timestamps
        return None

    def _extract_correlation(
        self,
        correlations: Dict[str, Dict[str, Any]],
        param_names: List[str]
    ) -> float:
        """Extract correlation value from correlation results."""
        for param_name in param_names:
            if param_name in correlations:
                return correlations[param_name].get('correlation', 0.0)
        return 0.0

    def _extract_co2_metrics(self, room_analysis: RoomAnalysis) -> Optional[Dict[str, Any]]:
        """Extract CO2 metrics from room analysis."""
        # Placeholder - would extract from test results
        return None

    def _extract_humidity_metrics(self, room_analysis: RoomAnalysis) -> Optional[Dict[str, Any]]:
        """Extract humidity metrics from room analysis."""
        # Placeholder
        return None

    def _extract_temperature_control_metrics(self, room_analysis: RoomAnalysis) -> Optional[Dict[str, Any]]:
        """Extract temperature control metrics."""
        # Placeholder
        return None

    def _extract_setpoint_deviation_metrics(self, room_analysis: RoomAnalysis) -> Optional[Dict[str, Any]]:
        """Extract setpoint deviation metrics."""
        # Placeholder
        return None
