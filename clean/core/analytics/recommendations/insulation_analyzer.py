"""Insulation need analyzer."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class InsulationAnalysis:
    """Result of insulation analysis."""

    needed: bool
    severity: float  # 0-1
    correlation_with_outdoor_temp: float
    avg_outdoor_temp_during_cold: Optional[float]
    description: str


class InsulationAnalyzer:
    """Analyze insulation needs based on temperature correlations."""

    def analyze(
        self,
        compliance_rate: float,
        outdoor_temp_correlation: float,
        avg_outdoor_temp: Optional[float] = None,
    ) -> InsulationAnalysis:
        """
        Analyze if insulation improvement is needed.

        Args:
            compliance_rate: Cold temperature compliance rate (0-100)
            outdoor_temp_correlation: Correlation with outdoor temp (negative = issue)
            avg_outdoor_temp: Average outdoor temp during cold periods

        Returns:
            InsulationAnalysis
        """
        # Strong negative correlation = poor insulation
        # (cold outside → cold inside)
        needs_insulation = outdoor_temp_correlation < -0.6 and compliance_rate < 80

        # Calculate severity
        severity = 0.0
        if needs_insulation:
            compliance_factor = (100 - compliance_rate) / 100
            correlation_factor = abs(outdoor_temp_correlation)
            severity = (compliance_factor + correlation_factor) / 2

        # Description
        if needs_insulation:
            description = (
                f"Poor thermal insulation detected. Indoor temperature tracks "
                f"outdoor temperature (r={outdoor_temp_correlation:.2f}). "
                f"Insulation improvements recommended."
            )
        else:
            description = "Insulation appears adequate."

        return InsulationAnalysis(
            needed=needs_insulation,
            severity=severity,
            correlation_with_outdoor_temp=outdoor_temp_correlation,
            avg_outdoor_temp_during_cold=avg_outdoor_temp,
            description=description,
        )


def analyze_insulation_need(
    compliance_rate: float,
    outdoor_temp_correlation: float,
) -> bool:
    """Quick check if insulation improvement is needed."""
    analyzer = InsulationAnalyzer()
    result = analyzer.analyze(compliance_rate, outdoor_temp_correlation)
    return result.needed
