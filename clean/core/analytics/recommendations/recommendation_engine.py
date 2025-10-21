"""
Smart recommendation engine using sensitivity analysis and climate correlations.

Generates prioritized, evidence-based recommendations for improving IEQ.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import pandas as pd

from core.domain.enums.priority import Priority
from core.domain.models.room_analysis import RoomAnalysis
from core.analytics.correlations import ClimateCorrelator, CorrelationResult


class RecommendationType(Enum):
    """Types of recommendations."""

    SOLAR_SHADING = "solar_shading"
    INSULATION = "insulation"
    MECHANICAL_VENTILATION = "mechanical_ventilation"
    NATURAL_VENTILATION = "natural_ventilation"
    HVAC_OPTIMIZATION = "hvac_optimization"
    OPERATIONAL = "operational"
    SCHEDULE_ADJUSTMENT = "schedule_adjustment"


@dataclass
class SmartRecommendation:
    """
    A smart, evidence-based recommendation.

    Includes rationale, evidence from correlations, and estimated impact.
    """

    type: RecommendationType
    priority: Priority
    title: str
    description: str
    rationale: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    estimated_impact: str = ""
    implementation_cost: str = ""
    climate_correlations: Dict[str, CorrelationResult] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "estimated_impact": self.estimated_impact,
            "implementation_cost": self.implementation_cost,
            "climate_correlations": {
                k: {
                    "correlation": v.correlation,
                    "p_value": v.p_value,
                    "strength": v.strength,
                    "interpretation": v.interpretation,
                }
                for k, v in self.climate_correlations.items()
            },
        }


class RecommendationEngine:
    """
    Generate smart recommendations based on analysis results and climate data.

    Uses:
    - Compliance test results
    - Climate correlations (sensitivity analysis)
    - Violation patterns
    - Parameter statistics
    """

    def __init__(self):
        """Initialize recommendation engine."""
        self.correlator = ClimateCorrelator()

    def generate_recommendations(
        self,
        room_analysis: RoomAnalysis,
        climate_data: Optional[pd.DataFrame] = None,
    ) -> List[SmartRecommendation]:
        """
        Generate recommendations for a room.

        Args:
            room_analysis: Room analysis results
            climate_data: Optional climate data for correlation analysis

        Returns:
            List of smart recommendations, sorted by priority
        """
        recommendations = []

        # Analyze temperature issues
        if self._has_temperature_violations(room_analysis):
            temp_recs = self._generate_temperature_recommendations(
                room_analysis, climate_data
            )
            recommendations.extend(temp_recs)

        # Analyze air quality issues
        if self._has_air_quality_violations(room_analysis):
            air_recs = self._generate_air_quality_recommendations(
                room_analysis, climate_data
            )
            recommendations.extend(air_recs)

        # Analyze humidity issues
        if self._has_humidity_violations(room_analysis):
            humidity_recs = self._generate_humidity_recommendations(
                room_analysis, climate_data
            )
            recommendations.extend(humidity_recs)

        # Sort by priority
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
        }
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

        return recommendations

    def _has_temperature_violations(self, room_analysis: RoomAnalysis) -> bool:
        """Check if room has temperature compliance issues."""
        # Check compliance results for temperature tests
        for result in room_analysis.compliance_results.values():
            if result.test_id and "temp" in result.test_id.lower():
                if result.compliance_rate < 90:  # Less than 90% compliance
                    return True
        return False

    def _has_air_quality_violations(self, room_analysis: RoomAnalysis) -> bool:
        """Check if room has air quality issues."""
        for result in room_analysis.compliance_results.values():
            if result.test_id and "co2" in result.test_id.lower():
                if result.compliance_rate < 90:
                    return True
        return False

    def _has_humidity_violations(self, room_analysis: RoomAnalysis) -> bool:
        """Check if room has humidity issues."""
        for result in room_analysis.compliance_results.values():
            if result.test_id and "humidity" in result.test_id.lower():
                if result.compliance_rate < 90:
                    return True
        return False

    def _generate_temperature_recommendations(
        self,
        room_analysis: RoomAnalysis,
        climate_data: Optional[pd.DataFrame],
    ) -> List[SmartRecommendation]:
        """Generate temperature-related recommendations."""
        recommendations = []

        # Find worst temperature compliance
        worst_compliance = 100.0
        worst_test_id = None

        for result in room_analysis.compliance_results.values():
            if result.test_id and "temp" in result.test_id.lower():
                if result.compliance_rate < worst_compliance:
                    worst_compliance = result.compliance_rate
                    worst_test_id = result.test_id

        if worst_test_id is None:
            return recommendations

        # Analyze with climate correlations if available
        climate_correlations = {}
        if climate_data is not None:
            # Get violation mask for this test
            # Note: This requires access to time series data
            # For now, we'll work with the compliance rate
            pass

        # Determine recommendation based on pattern
        if "above" in worst_test_id.lower() or "overheat" in worst_test_id.lower():
            # Overheating issue
            rec = self._create_overheating_recommendation(
                worst_compliance, climate_correlations
            )
            if rec:
                recommendations.append(rec)

        elif "below" in worst_test_id.lower() or "cold" in worst_test_id.lower():
            # Underheating issue
            rec = self._create_underheating_recommendation(
                worst_compliance, climate_correlations
            )
            if rec:
                recommendations.append(rec)

        return recommendations

    def _create_overheating_recommendation(
        self,
        compliance_rate: float,
        climate_correlations: Dict[str, CorrelationResult],
    ) -> Optional[SmartRecommendation]:
        """Create recommendation for overheating."""
        # Determine priority
        if compliance_rate < 50:
            priority = Priority.CRITICAL
        elif compliance_rate < 70:
            priority = Priority.HIGH
        else:
            priority = Priority.MEDIUM

        # Build rationale
        rationale = [
            f"Overheating compliance is only {compliance_rate:.1f}%",
        ]

        # Check climate correlations for solar gain
        has_solar_correlation = False
        for param, corr in climate_correlations.items():
            if "radiation" in param.lower() and corr.correlation > 0.5:
                has_solar_correlation = True
                rationale.append(
                    f"Strong positive correlation with solar radiation (r={corr.correlation:.2f})"
                )

        # Recommendation type
        if has_solar_correlation:
            rec_type = RecommendationType.SOLAR_SHADING
            title = "Install External Solar Shading"
            description = (
                f"Room experiences significant overheating ({compliance_rate:.1f}% compliant). "
                "Analysis shows solar heat gain is a major factor. Installing external solar "
                "shading (external blinds, awnings, or brise-soleil) will significantly reduce "
                "solar heat gain while maintaining natural light and views."
            )
            estimated_impact = "Could improve summer compliance by 20-40 percentage points"
            cost = "Medium (€100-300 per window)"
        else:
            rec_type = RecommendationType.HVAC_OPTIMIZATION
            title = "Optimize Cooling System"
            description = (
                f"Room experiences overheating ({compliance_rate:.1f}% compliant). "
                "Consider: (1) Reviewing cooling system capacity and settings, "
                "(2) Checking thermostat placement and calibration, "
                "(3) Improving natural ventilation during cooler periods, "
                "(4) Reducing internal heat gains from equipment/lighting."
            )
            estimated_impact = "Could improve compliance by 15-30 percentage points"
            cost = "Low to Medium (€200-2000)"

        return SmartRecommendation(
            type=rec_type,
            priority=priority,
            title=title,
            description=description,
            rationale=rationale,
            evidence={"compliance_rate": compliance_rate},
            estimated_impact=estimated_impact,
            implementation_cost=cost,
            climate_correlations=climate_correlations,
        )

    def _create_underheating_recommendation(
        self,
        compliance_rate: float,
        climate_correlations: Dict[str, CorrelationResult],
    ) -> Optional[SmartRecommendation]:
        """Create recommendation for underheating."""
        # Determine priority
        if compliance_rate < 50:
            priority = Priority.CRITICAL
        elif compliance_rate < 70:
            priority = Priority.HIGH
        else:
            priority = Priority.MEDIUM

        # Build rationale
        rationale = [
            f"Cold temperature compliance is only {compliance_rate:.1f}%",
        ]

        # Check for insulation issues
        has_insulation_issue = False
        for param, corr in climate_correlations.items():
            if "temp" in param.lower() and corr.correlation < -0.6:
                has_insulation_issue = True
                rationale.append(
                    f"Strong negative correlation with outdoor temperature (r={corr.correlation:.2f})"
                )
                rationale.append("Indoor temperature closely tracks outdoor temperature")

        if has_insulation_issue:
            rec_type = RecommendationType.INSULATION
            title = "Improve Thermal Insulation and Air Sealing"
            description = (
                f"Room experiences cold temperature issues ({compliance_rate:.1f}% compliant). "
                "The strong relationship between outdoor and indoor temperatures indicates "
                "heat is being lost through the building envelope. Priority actions: "
                "(1) Inspect windows for drafts and poor seals, "
                "(2) Check wall and roof insulation levels, "
                "(3) Consider upgrading to double/triple glazing, "
                "(4) Seal air leaks around doors and windows."
            )
            estimated_impact = "Could improve winter compliance by 15-30 percentage points"
            cost = "Medium to High (€500-5000)"
        else:
            rec_type = RecommendationType.HVAC_OPTIMIZATION
            title = "Optimize Heating System"
            description = (
                f"Room experiences cold periods ({compliance_rate:.1f}% compliant). "
                "Consider: (1) Reviewing heating system capacity and settings, "
                "(2) Checking radiator/heating distribution, "
                "(3) Verifying thermostat placement and calibration, "
                "(4) Reducing heat loss from windows during cold periods."
            )
            estimated_impact = "Could improve compliance by 10-25 percentage points"
            cost = "Low to Medium (€200-2000)"

        return SmartRecommendation(
            type=rec_type,
            priority=priority,
            title=title,
            description=description,
            rationale=rationale,
            evidence={"compliance_rate": compliance_rate},
            estimated_impact=estimated_impact,
            implementation_cost=cost,
            climate_correlations=climate_correlations,
        )

    def _generate_air_quality_recommendations(
        self,
        room_analysis: RoomAnalysis,
        climate_data: Optional[pd.DataFrame],
    ) -> List[SmartRecommendation]:
        """Generate air quality recommendations."""
        recommendations = []

        # Find worst CO2 compliance
        worst_compliance = 100.0
        for result in room_analysis.compliance_results.values():
            if result.test_id and "co2" in result.test_id.lower():
                if result.compliance_rate < worst_compliance:
                    worst_compliance = result.compliance_rate

        if worst_compliance >= 90:
            return recommendations

        # Determine ventilation recommendation
        if worst_compliance < 50:
            priority = Priority.CRITICAL
            rec_type = RecommendationType.MECHANICAL_VENTILATION
            title = "Install Mechanical Ventilation System"
            description = (
                f"Room has severe air quality issues ({worst_compliance:.1f}% CO2 compliance). "
                "Natural ventilation alone is insufficient. Recommend installing mechanical "
                "ventilation system (demand-controlled ventilation with CO2 sensors) to ensure "
                "adequate air quality year-round regardless of outdoor conditions."
            )
            estimated_impact = "Could improve CO2 compliance to 85-95%"
            cost = "High (€2000-8000 per room)"
        elif worst_compliance < 75:
            priority = Priority.MEDIUM
            rec_type = RecommendationType.NATURAL_VENTILATION
            title = "Enhance Natural Ventilation Strategy"
            description = (
                f"Room shows moderate air quality issues ({worst_compliance:.1f}% CO2 compliance). "
                "Consider: (1) Improving natural ventilation with larger/additional openable windows, "
                "(2) Installing window automation for automatic opening based on CO2 levels, "
                "(3) Educating occupants about ventilation needs, "
                "(4) If issues persist, consider mechanical ventilation."
            )
            estimated_impact = "Could improve CO2 compliance by 10-20 percentage points"
            cost = "Low to Medium (€100-2000)"
        else:
            priority = Priority.LOW
            rec_type = RecommendationType.OPERATIONAL
            title = "Improve Ventilation Practices"
            description = (
                f"Room has minor air quality issues ({worst_compliance:.1f}% CO2 compliance). "
                "Simple operational improvements may help: (1) Increase window opening frequency, "
                "(2) Reduce occupancy during peak periods, (3) Monitor CO2 levels with sensors."
            )
            estimated_impact = "Could improve compliance by 5-15 percentage points"
            cost = "Very Low (€50-500)"

        recommendations.append(
            SmartRecommendation(
                type=rec_type,
                priority=priority,
                title=title,
                description=description,
                rationale=[f"CO2 compliance at {worst_compliance:.1f}%"],
                evidence={"co2_compliance": worst_compliance},
                estimated_impact=estimated_impact,
                implementation_cost=cost,
            )
        )

        return recommendations

    def _generate_humidity_recommendations(
        self,
        room_analysis: RoomAnalysis,
        climate_data: Optional[pd.DataFrame],
    ) -> List[SmartRecommendation]:
        """Generate humidity-related recommendations."""
        # Similar pattern to temperature recommendations
        # For now, return empty list
        return []


def generate_recommendations_for_room(
    room_analysis: RoomAnalysis,
    climate_data: Optional[pd.DataFrame] = None,
) -> List[SmartRecommendation]:
    """
    Convenience function to generate recommendations.

    Args:
        room_analysis: Room analysis results
        climate_data: Optional climate data

    Returns:
        List of smart recommendations
    """
    engine = RecommendationEngine()
    return engine.generate_recommendations(room_analysis, climate_data)
