"""Ventilation optimization and analysis."""

from typing import Optional
from dataclasses import dataclass
from enum import Enum


class VentilationType(Enum):
    """Types of ventilation systems."""

    NATURAL = "natural"
    MECHANICAL = "mechanical"
    HYBRID = "hybrid"


@dataclass
class VentilationAnalysis:
    """Result of ventilation analysis."""

    improvement_needed: bool
    recommended_type: VentilationType
    severity: float  # 0-1
    compliance_rate: float
    description: str
    recommended_ach: Optional[float] = None  # Air changes per hour


class VentilationOptimizer:
    """Analyze ventilation needs and recommend improvements."""

    def analyze(
        self,
        co2_compliance_rate: float,
        avg_co2: Optional[float] = None,
        peak_co2: Optional[float] = None,
    ) -> VentilationAnalysis:
        """
        Analyze ventilation needs.

        Args:
            co2_compliance_rate: CO2 compliance rate (0-100)
            avg_co2: Average CO2 level (ppm)
            peak_co2: Peak CO2 level (ppm)

        Returns:
            VentilationAnalysis
        """
        needs_improvement = co2_compliance_rate < 90

        # Determine recommended ventilation type
        if co2_compliance_rate < 50:
            rec_type = VentilationType.MECHANICAL
            description = "Severe air quality issues - mechanical ventilation required"
        elif co2_compliance_rate < 75:
            rec_type = VentilationType.HYBRID
            description = "Moderate issues - hybrid ventilation recommended"
        else:
            rec_type = VentilationType.NATURAL
            description = "Minor issues - enhance natural ventilation"

        # Calculate severity
        severity = (100 - co2_compliance_rate) / 100

        # Estimate recommended ACH based on CO2 levels
        recommended_ach = None
        if avg_co2:
            if avg_co2 > 1400:
                recommended_ach = 8.0
            elif avg_co2 > 1200:
                recommended_ach = 6.0
            elif avg_co2 > 1000:
                recommended_ach = 4.0
            else:
                recommended_ach = 2.0

        return VentilationAnalysis(
            improvement_needed=needs_improvement,
            recommended_type=rec_type,
            severity=severity,
            compliance_rate=co2_compliance_rate,
            description=description,
            recommended_ach=recommended_ach,
        )


def analyze_ventilation_needs(
    co2_compliance_rate: float,
    avg_co2: Optional[float] = None,
) -> VentilationAnalysis:
    """Convenience function for ventilation analysis."""
    optimizer = VentilationOptimizer()
    return optimizer.analyze(co2_compliance_rate, avg_co2)
