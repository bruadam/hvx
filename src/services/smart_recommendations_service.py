"""
Smart Recommendations Service

Advanced recommendations engine that analyzes test results and weather correlations
to provide targeted recommendations for:
- Solar shading needs
- Insulation improvements
- Ventilation strategies
- Natural ventilation conflicts (CO2 vs temperature trade-offs)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.models.analysis_models import RoomAnalysis, TestResult, AnalysisSeverity

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Types of recommendations."""
    SOLAR_SHADING = "solar_shading"
    INSULATION = "insulation"
    MECHANICAL_VENTILATION = "mechanical_ventilation"
    NATURAL_VENTILATION = "natural_ventilation"
    HVAC_CONTROL = "hvac_control"
    OPERATIONAL = "operational"


class Priority(Enum):
    """Recommendation priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SmartRecommendation:
    """A targeted recommendation with supporting evidence."""
    type: RecommendationType
    priority: Priority
    title: str
    description: str
    rationale: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    estimated_impact: str = ""
    implementation_cost: str = ""


@dataclass
class VentilationConflict:
    """Identified conflict between CO2 and temperature control."""
    season: str
    conflict_type: str  # "co2_vs_cold" or "co2_vs_heat"
    co2_compliance: float
    temp_compliance: float
    outdoor_temp_during_co2_issues: Dict[str, float]
    severity: str
    description: str


class SmartRecommendationsService:
    """Generate intelligent recommendations based on test results and weather correlations."""
    
    def __init__(self):
        """Initialize the recommendations service."""
        pass
    
    def generate_recommendations(self, room: RoomAnalysis) -> List[SmartRecommendation]:
        """
        Generate comprehensive recommendations for a room.
        
        Args:
            room: RoomAnalysis object with test results and weather correlations
        
        Returns:
            List of smart recommendations prioritized by impact
        """
        recommendations = []
        
        # Analyze solar shading needs
        solar_rec = self._analyze_solar_shading_needs(room)
        if solar_rec:
            recommendations.append(solar_rec)
        
        # Analyze insulation needs
        insulation_rec = self._analyze_insulation_needs(room)
        if insulation_rec:
            recommendations.append(insulation_rec)
        
        # Analyze ventilation needs
        ventilation_recs = self._analyze_ventilation_needs(room)
        recommendations.extend(ventilation_recs)
        
        # Identify ventilation conflicts
        conflicts = self._identify_ventilation_conflicts(room)
        conflict_recs = self._generate_conflict_recommendations(conflicts)
        recommendations.extend(conflict_recs)
        
        # Sort by priority
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        recommendations.sort(key=lambda x: priority_order[x.priority])
        
        return recommendations
    
    def _analyze_solar_shading_needs(self, room: RoomAnalysis) -> Optional[SmartRecommendation]:
        """
        Analyze if room needs solar shading based on overheating and weather correlations.
        
        Strong positive correlation between outdoor temp/radiation and overheating
        indicates solar gain is a major issue.
        """
        # Find summer overheating tests
        summer_overheat_tests = []
        for test_name, result in room.test_results.items():
            if ('summer' in test_name.lower() and 
                ('temp_above' in test_name.lower() or 'overheating' in test_name.lower())):
                summer_overheat_tests.append((test_name, result))
        
        if not summer_overheat_tests:
            return None
        
        # Analyze correlations
        max_temp_correlation = 0
        max_radiation_correlation = 0
        worst_compliance = 100
        avg_outdoor_temp = None
        avg_radiation = None
        
        for test_name, result in summer_overheat_tests:
            if result.compliance_rate < worst_compliance:
                worst_compliance = result.compliance_rate
            
            # Check weather correlations
            temp_corr = result.weather_correlations.get('outdoor_temp', 0)
            radiation_corr = result.weather_correlations.get('radiation', 0)
            
            max_temp_correlation = max(max_temp_correlation, temp_corr)
            max_radiation_correlation = max(max_radiation_correlation, radiation_corr)
            
            # Get weather stats during non-compliance
            if result.non_compliance_weather_stats:
                if 'outdoor_temp' in result.non_compliance_weather_stats:
                    avg_outdoor_temp = result.non_compliance_weather_stats['outdoor_temp'].get('mean')
                if 'radiation' in result.non_compliance_weather_stats:
                    avg_radiation = result.non_compliance_weather_stats['radiation'].get('mean')
        
        # Determine if solar shading is needed
        needs_shading = False
        priority = Priority.LOW
        rationale = []
        
        # Strong positive correlation with temperature/radiation indicates solar gain issue
        if max_temp_correlation > 0.5 or max_radiation_correlation > 0.5:
            needs_shading = True
            priority = Priority.HIGH if worst_compliance < 70 else Priority.MEDIUM
            
            if max_temp_correlation > 0.5:
                rationale.append(
                    f"Strong positive correlation ({max_temp_correlation:+.2f}) between outdoor "
                    f"temperature and indoor overheating indicates solar heat gain is a major driver"
                )
            
            if max_radiation_correlation > 0.5:
                rationale.append(
                    f"Strong positive correlation ({max_radiation_correlation:+.2f}) between solar "
                    f"radiation and overheating confirms direct solar gain through windows"
                )
        
        # Even moderate correlation with poor compliance suggests shading
        elif (max_temp_correlation > 0.3 or max_radiation_correlation > 0.3) and worst_compliance < 60:
            needs_shading = True
            priority = Priority.MEDIUM
            rationale.append(
                f"Moderate weather correlation combined with poor compliance ({worst_compliance:.1f}%) "
                f"suggests solar heat gain is contributing to overheating"
            )
        
        if not needs_shading:
            return None
        
        # Build recommendation
        description = (
            f"Room experiences significant overheating during summer months "
            f"({worst_compliance:.1f}% compliant). Analysis shows solar heat gain is a major factor. "
        )
        
        if avg_outdoor_temp and avg_radiation:
            description += (
                f"During overheating periods, outdoor temperature averages {avg_outdoor_temp:.1f}°C "
                f"with solar radiation of {avg_radiation:.0f} W/m². "
            )
        
        description += (
            "Installing external solar shading (external blinds, awnings, or brise-soleil) "
            "will significantly reduce solar heat gain while maintaining natural light and views."
        )
        
        return SmartRecommendation(
            type=RecommendationType.SOLAR_SHADING,
            priority=priority,
            title="Install External Solar Shading",
            description=description,
            rationale=rationale,
            evidence={
                'worst_summer_compliance': worst_compliance,
                'outdoor_temp_correlation': max_temp_correlation,
                'radiation_correlation': max_radiation_correlation,
                'avg_outdoor_temp_during_issues': avg_outdoor_temp,
                'avg_radiation_during_issues': avg_radiation,
                'affected_tests': [t[0] for t in summer_overheat_tests]
            },
            estimated_impact="Could improve summer compliance by 20-40 percentage points",
            implementation_cost="Medium (€100-300 per window depending on solution)"
        )
    
    def _analyze_insulation_needs(self, room: RoomAnalysis) -> Optional[SmartRecommendation]:
        """
        Analyze if room needs better insulation based on winter underheating
        and strong negative correlation with outdoor temperature.
        """
        # Find winter/all-year cold temperature tests
        cold_tests = []
        for test_name, result in room.test_results.items():
            if 'temp_below' in test_name.lower():
                cold_tests.append((test_name, result))
        
        if not cold_tests:
            return None
        
        # Analyze correlations
        min_temp_correlation = 0  # Most negative
        worst_compliance = 100
        avg_outdoor_temp = None
        winter_test_name = None
        
        for test_name, result in cold_tests:
            if result.compliance_rate < worst_compliance:
                worst_compliance = result.compliance_rate
                winter_test_name = test_name
            
            # Check outdoor temperature correlation (negative = cold outside causes cold inside)
            temp_corr = result.weather_correlations.get('outdoor_temp', 0)
            if temp_corr < min_temp_correlation:
                min_temp_correlation = temp_corr
                
                # Get weather stats
                if result.non_compliance_weather_stats:
                    if 'outdoor_temp' in result.non_compliance_weather_stats:
                        avg_outdoor_temp = result.non_compliance_weather_stats['outdoor_temp'].get('mean')
        
        # Determine if insulation is needed
        needs_insulation = False
        priority = Priority.LOW
        rationale = []
        
        # Strong negative correlation indicates poor insulation
        if min_temp_correlation < -0.6:
            needs_insulation = True
            priority = Priority.HIGH if worst_compliance < 70 else Priority.MEDIUM
            rationale.append(
                f"Very strong negative correlation ({min_temp_correlation:.2f}) between outdoor "
                f"temperature and indoor underheating indicates poor thermal insulation"
            )
            rationale.append(
                "Indoor temperature closely tracks outdoor temperature, suggesting significant "
                "heat loss through building envelope"
            )
        
        elif min_temp_correlation < -0.4 and worst_compliance < 70:
            needs_insulation = True
            priority = Priority.MEDIUM
            rationale.append(
                f"Moderate negative correlation ({min_temp_correlation:.2f}) combined with poor "
                f"compliance ({worst_compliance:.1f}%) suggests insulation improvements would help"
            )
        
        if not needs_insulation:
            return None
        
        # Build recommendation
        description = (
            f"Room experiences significant cold temperature issues "
            f"({worst_compliance:.1f}% compliant during winter/cold periods). "
            f"The strong relationship between outdoor and indoor temperatures indicates "
            f"heat is being lost through the building envelope. "
        )
        
        if avg_outdoor_temp:
            description += (
                f"During underheating periods, outdoor temperature averages {avg_outdoor_temp:.1f}°C, "
                f"and the indoor space cannot maintain comfort levels. "
            )
        
        description += (
            "Priority actions: (1) Inspect windows for drafts and poor seals, "
            "(2) Check wall and roof insulation levels, "
            "(3) Consider upgrading single-glazed windows to double/triple glazing, "
            "(4) Seal air leaks around doors and windows."
        )
        
        return SmartRecommendation(
            type=RecommendationType.INSULATION,
            priority=priority,
            title="Improve Thermal Insulation and Air Sealing",
            description=description,
            rationale=rationale,
            evidence={
                'worst_cold_compliance': worst_compliance,
                'outdoor_temp_correlation': min_temp_correlation,
                'avg_outdoor_temp_during_issues': avg_outdoor_temp,
                'affected_test': winter_test_name
            },
            estimated_impact="Could improve winter compliance by 15-30 percentage points",
            implementation_cost="Medium to High (€500-5000 depending on scope)"
        )
    
    def _analyze_ventilation_needs(self, room: RoomAnalysis) -> List[SmartRecommendation]:
        """
        Analyze ventilation needs based on CO2 levels and correlations.
        """
        recommendations = []
        
        # Find CO2 tests
        co2_tests = []
        for test_name, result in room.test_results.items():
            if 'co2' in test_name.lower():
                co2_tests.append((test_name, result))
        
        if not co2_tests:
            return recommendations
        
        # Analyze CO2 compliance across different periods
        worst_compliance = 100
        worst_test_name = None
        co2_weather_pattern = {}
        
        for test_name, result in co2_tests:
            if result.compliance_rate < worst_compliance:
                worst_compliance = result.compliance_rate
                worst_test_name = test_name
            
            # Track weather correlations
            temp_corr = result.weather_correlations.get('outdoor_temp', 0)
            if temp_corr != 0:
                co2_weather_pattern[test_name] = temp_corr
        
        # Severe CO2 issues need mechanical ventilation
        if worst_compliance < 50:
            priority = Priority.CRITICAL if worst_compliance < 30 else Priority.HIGH
            
            rationale = [
                f"Severe CO2 compliance issues ({worst_compliance:.1f}%) indicate "
                f"insufficient ventilation capacity"
            ]
            
            # Check if weather-dependent
            avg_temp_corr = sum(co2_weather_pattern.values()) / len(co2_weather_pattern) if co2_weather_pattern else 0
            if avg_temp_corr < -0.3:
                rationale.append(
                    f"Negative correlation with outdoor temperature ({avg_temp_corr:.2f}) "
                    f"suggests natural ventilation is insufficient in cold weather when "
                    f"windows are kept closed"
                )
            
            description = (
                f"Room has severe air quality issues with only {worst_compliance:.1f}% compliance "
                f"on CO2 tests. Natural ventilation alone is insufficient. Recommend installing "
                f"mechanical ventilation system (demand-controlled ventilation with CO2 sensors) "
                f"to ensure adequate air quality year-round regardless of outdoor conditions."
            )
            
            recommendations.append(SmartRecommendation(
                type=RecommendationType.MECHANICAL_VENTILATION,
                priority=priority,
                title="Install Mechanical Ventilation System",
                description=description,
                rationale=rationale,
                evidence={
                    'worst_co2_compliance': worst_compliance,
                    'affected_test': worst_test_name,
                    'temp_correlation': avg_temp_corr
                },
                estimated_impact="Could improve CO2 compliance to 85-95%",
                implementation_cost="High (€2000-8000 per room)"
            ))
        
        # Moderate issues - enhanced natural ventilation might help
        elif worst_compliance < 75:
            priority = Priority.MEDIUM
            
            description = (
                f"Room shows moderate air quality issues ({worst_compliance:.1f}% CO2 compliance). "
                f"Consider: (1) Improving natural ventilation with larger/additional openable windows, "
                f"(2) Installing window automation for automatic opening based on CO2 levels, "
                f"(3) Educating occupants about ventilation needs, "
                f"(4) If issues persist, consider mechanical ventilation."
            )
            
            recommendations.append(SmartRecommendation(
                type=RecommendationType.NATURAL_VENTILATION,
                priority=priority,
                title="Enhance Natural Ventilation Strategy",
                description=description,
                rationale=[
                    f"Moderate CO2 compliance ({worst_compliance:.1f}%) suggests "
                    f"natural ventilation is partially effective but needs improvement"
                ],
                evidence={
                    'worst_co2_compliance': worst_compliance,
                    'affected_test': worst_test_name
                },
                estimated_impact="Could improve CO2 compliance by 10-20 percentage points",
                implementation_cost="Low to Medium (€100-2000)"
            ))
        
        return recommendations
    
    def _identify_ventilation_conflicts(self, room: RoomAnalysis) -> List[VentilationConflict]:
        """
        Identify conflicts where natural ventilation for CO2 causes temperature issues.
        
        Common conflicts:
        1. Winter: Opening windows for CO2 causes underheating
        2. Summer: Closing windows for cooling causes CO2 buildup
        """
        conflicts = []
        
        # Get CO2 and temperature test results by season
        winter_co2_tests = []
        winter_temp_tests = []
        summer_co2_tests = []
        summer_temp_tests = []
        
        for test_name, result in room.test_results.items():
            if 'winter' in test_name.lower():
                if 'co2' in test_name.lower():
                    winter_co2_tests.append((test_name, result))
                elif 'temp' in test_name.lower():
                    winter_temp_tests.append((test_name, result))
            
            if 'summer' in test_name.lower():
                if 'co2' in test_name.lower():
                    summer_co2_tests.append((test_name, result))
                elif 'temp' in test_name.lower():
                    summer_temp_tests.append((test_name, result))
        
        # Check for winter conflict (CO2 vs cold)
        if winter_co2_tests and winter_temp_tests:
            co2_compliance = min(r[1].compliance_rate for r in winter_co2_tests)
            temp_below_tests = [t for t in winter_temp_tests if 'below' in t[0].lower()]
            
            if temp_below_tests:
                temp_compliance = min(r[1].compliance_rate for r in temp_below_tests)
                
                # Both poor = conflict (natural ventilation causes cold)
                if co2_compliance < 70 and temp_compliance < 70:
                    # Get outdoor temp during CO2 issues
                    outdoor_temp_stats = {}
                    for test_name, result in winter_co2_tests:
                        if result.non_compliance_weather_stats:
                            outdoor_temp_stats = result.non_compliance_weather_stats.get('outdoor_temp', {})
                            break
                    
                    severity = "HIGH" if (co2_compliance < 50 or temp_compliance < 50) else "MEDIUM"
                    
                    conflicts.append(VentilationConflict(
                        season="winter",
                        conflict_type="co2_vs_cold",
                        co2_compliance=co2_compliance,
                        temp_compliance=temp_compliance,
                        outdoor_temp_during_co2_issues=outdoor_temp_stats,
                        severity=severity,
                        description=(
                            f"Winter ventilation conflict detected: CO2 compliance is {co2_compliance:.1f}% "
                            f"and cold temperature compliance is {temp_compliance:.1f}%. "
                            f"Opening windows for air quality causes indoor temperatures to drop. "
                            f"Natural ventilation creates a trade-off between air quality and thermal comfort."
                        )
                    ))
        
        # Check for summer conflict (CO2 vs heat)
        if summer_co2_tests and summer_temp_tests:
            co2_compliance = min(r[1].compliance_rate for r in summer_co2_tests)
            temp_above_tests = [t for t in summer_temp_tests if 'above' in t[0].lower()]
            
            if temp_above_tests:
                temp_compliance = min(r[1].compliance_rate for r in temp_above_tests)
                
                # Check if negative correlation between outdoor temp and CO2
                # (hot outside → windows closed → high CO2)
                temp_corr = 0
                for test_name, result in summer_co2_tests:
                    temp_corr = result.weather_correlations.get('outdoor_temp', 0)
                    if temp_corr < -0.3:  # Negative = hot outside, high CO2
                        break
                
                # Both poor + negative correlation = conflict
                if co2_compliance < 70 and temp_compliance < 70 and temp_corr < -0.3:
                    outdoor_temp_stats = {}
                    for test_name, result in summer_co2_tests:
                        if result.non_compliance_weather_stats:
                            outdoor_temp_stats = result.non_compliance_weather_stats.get('outdoor_temp', {})
                            break
                    
                    severity = "HIGH" if (co2_compliance < 50 or temp_compliance < 50) else "MEDIUM"
                    
                    conflicts.append(VentilationConflict(
                        season="summer",
                        conflict_type="co2_vs_heat",
                        co2_compliance=co2_compliance,
                        temp_compliance=temp_compliance,
                        outdoor_temp_during_co2_issues=outdoor_temp_stats,
                        severity=severity,
                        description=(
                            f"Summer ventilation conflict detected: CO2 compliance is {co2_compliance:.1f}% "
                            f"and overheating compliance is {temp_compliance:.1f}%. "
                            f"Negative correlation ({temp_corr:.2f}) suggests windows are closed during hot "
                            f"weather to prevent heat gain, causing CO2 buildup. Natural ventilation alone "
                            f"cannot solve both issues simultaneously."
                        )
                    ))
        
        return conflicts
    
    def _generate_conflict_recommendations(
        self, 
        conflicts: List[VentilationConflict]
    ) -> List[SmartRecommendation]:
        """Generate recommendations to resolve ventilation conflicts."""
        recommendations = []
        
        for conflict in conflicts:
            if conflict.conflict_type == "co2_vs_cold":
                # Winter conflict - need mechanical ventilation with heat recovery
                priority = Priority.CRITICAL if conflict.severity == "HIGH" else Priority.HIGH
                
                avg_outdoor_temp = conflict.outdoor_temp_during_co2_issues.get('mean', 0)
                
                description = (
                    f"{conflict.description} "
                    f"\n\nDuring CO2 issues, outdoor temperature averages {avg_outdoor_temp:.1f}°C. "
                    f"Opening windows for ventilation brings in cold air, overwhelming the heating system. "
                    f"\n\nSOLUTION: Install Heat Recovery Ventilation (HRV) or Energy Recovery Ventilation (ERV) system. "
                    f"These systems provide fresh air while recovering 70-90% of heat energy from exhaust air, "
                    f"maintaining both air quality and thermal comfort without the energy penalty of opening windows."
                )
                
                recommendations.append(SmartRecommendation(
                    type=RecommendationType.MECHANICAL_VENTILATION,
                    priority=priority,
                    title="Resolve Winter Ventilation Conflict with HRV/ERV System",
                    description=description,
                    rationale=[
                        "Natural ventilation causes unacceptable thermal comfort loss in winter",
                        "Mechanical ventilation with heat recovery is the only solution that addresses both issues",
                        f"Current situation: {conflict.co2_compliance:.1f}% CO2 compliance, "
                        f"{conflict.temp_compliance:.1f}% thermal compliance"
                    ],
                    evidence={
                        'conflict_type': conflict.conflict_type,
                        'season': conflict.season,
                        'co2_compliance': conflict.co2_compliance,
                        'temp_compliance': conflict.temp_compliance,
                        'outdoor_temp_stats': conflict.outdoor_temp_during_co2_issues
                    },
                    estimated_impact=(
                        "Can achieve 85-95% compliance on both CO2 and temperature while "
                        "reducing heating energy by 40-60%"
                    ),
                    implementation_cost="High (€3000-10000 for HRV/ERV system)"
                ))
            
            elif conflict.conflict_type == "co2_vs_heat":
                # Summer conflict - need mechanical ventilation + cooling/shading
                priority = Priority.CRITICAL if conflict.severity == "HIGH" else Priority.HIGH
                
                avg_outdoor_temp = conflict.outdoor_temp_during_co2_issues.get('mean', 0)
                
                description = (
                    f"{conflict.description} "
                    f"\n\nDuring CO2 issues, outdoor temperature averages {avg_outdoor_temp:.1f}°C. "
                    f"Opening windows brings in hot air, causing overheating. "
                    f"\n\nSOLUTION: Implement two-part strategy: "
                    f"\n1. Install mechanical ventilation to provide fresh air without relying on windows "
                    f"\n2. Add solar shading (external blinds/awnings) to reduce heat gain "
                    f"\n3. Consider cooling system if budget allows (e.g., heat pump in cooling mode)"
                    f"\n\nThis combination allows ventilation without heat gain, resolving the conflict."
                )
                
                recommendations.append(SmartRecommendation(
                    type=RecommendationType.MECHANICAL_VENTILATION,
                    priority=priority,
                    title="Resolve Summer Ventilation Conflict with Mechanical Ventilation + Shading",
                    description=description,
                    rationale=[
                        "Natural ventilation brings hot outdoor air, worsening overheating",
                        "Mechanical ventilation + solar shading allows air quality without heat gain",
                        f"Current situation: {conflict.co2_compliance:.1f}% CO2 compliance, "
                        f"{conflict.temp_compliance:.1f}% overheating compliance"
                    ],
                    evidence={
                        'conflict_type': conflict.conflict_type,
                        'season': conflict.season,
                        'co2_compliance': conflict.co2_compliance,
                        'temp_compliance': conflict.temp_compliance,
                        'outdoor_temp_stats': conflict.outdoor_temp_during_co2_issues
                    },
                    estimated_impact=(
                        "Can achieve 80-90% compliance on both CO2 and temperature. "
                        "Solar shading alone can improve summer compliance by 20-30 percentage points."
                    ),
                    implementation_cost="High (€2000-8000 for ventilation + €100-300/window for shading)"
                ))
        
        return recommendations


def generate_building_recommendations_report(
    room_analyses: Dict[str, RoomAnalysis]
) -> Dict[str, Any]:
    """
    Generate a building-wide recommendations report.
    
    Args:
        room_analyses: Dictionary of room analyses {room_id: RoomAnalysis}
    
    Returns:
        Comprehensive recommendations report
    """
    service = SmartRecommendationsService()
    
    # Generate recommendations for each room
    room_recommendations = {}
    all_recommendations = []
    conflicts_by_room = {}
    
    for room_id, room in room_analyses.items():
        recs = service.generate_recommendations(room)
        if recs:
            room_recommendations[room_id] = recs
            all_recommendations.extend(recs)
        
        # Track conflicts
        conflicts = service._identify_ventilation_conflicts(room)
        if conflicts:
            conflicts_by_room[room_id] = conflicts
    
    # Aggregate by recommendation type
    by_type = {}
    for rec in all_recommendations:
        type_key = rec.type.value
        if type_key not in by_type:
            by_type[type_key] = []
        by_type[type_key].append(rec)
    
    # Count priorities
    priority_counts = {
        'critical': sum(1 for r in all_recommendations if r.priority == Priority.CRITICAL),
        'high': sum(1 for r in all_recommendations if r.priority == Priority.HIGH),
        'medium': sum(1 for r in all_recommendations if r.priority == Priority.MEDIUM),
        'low': sum(1 for r in all_recommendations if r.priority == Priority.LOW)
    }
    
    # Summary statistics
    rooms_needing_shading = len([r for r in by_type.get('solar_shading', [])])
    rooms_needing_insulation = len([r for r in by_type.get('insulation', [])])
    rooms_needing_mech_vent = len([r for r in by_type.get('mechanical_ventilation', [])])
    
    return {
        'summary': {
            'total_rooms_analyzed': len(room_analyses),
            'rooms_with_recommendations': len(room_recommendations),
            'total_recommendations': len(all_recommendations),
            'priority_breakdown': priority_counts,
            'rooms_needing_solar_shading': rooms_needing_shading,
            'rooms_needing_insulation': rooms_needing_insulation,
            'rooms_needing_mechanical_ventilation': rooms_needing_mech_vent,
            'rooms_with_ventilation_conflicts': len(conflicts_by_room)
        },
        'by_recommendation_type': {
            type_key: len(recs) for type_key, recs in by_type.items()
        },
        'room_recommendations': room_recommendations,
        'ventilation_conflicts': conflicts_by_room,
        'critical_actions': [
            {
                'room_id': room_id,
                'room_name': room_analyses[room_id].room_name,
                'recommendations': [
                    {
                        'type': rec.type.value,
                        'priority': rec.priority.value,
                        'title': rec.title,
                        'description': rec.description
                    }
                    for rec in recs if rec.priority == Priority.CRITICAL
                ]
            }
            for room_id, recs in room_recommendations.items()
            if any(r.priority == Priority.CRITICAL for r in recs)
        ]
    }
