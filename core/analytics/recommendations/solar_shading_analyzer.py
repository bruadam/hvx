"""Solar shading need analyzer."""

from dataclasses import dataclass


@dataclass
class SolarShadingAnalysis:
    """Result of solar shading analysis."""

    needed: bool
    severity: float  # 0-1
    correlation_with_radiation: float
    correlation_with_temp: float
    avg_radiation_during_overheat: float | None
    description: str


class SolarShadingAnalyzer:
    """Analyze solar shading needs based on correlations."""

    def analyze(
        self,
        compliance_rate: float,
        radiation_correlation: float,
        outdoor_temp_correlation: float,
        avg_radiation: float | None = None,
    ) -> SolarShadingAnalysis:
        """
        Analyze if solar shading is needed.

        Args:
            compliance_rate: Overheating compliance rate (0-100)
            radiation_correlation: Correlation with solar radiation
            outdoor_temp_correlation: Correlation with outdoor temp
            avg_radiation: Average radiation during overheating

        Returns:
            SolarShadingAnalysis
        """
        # Strong positive correlation with radiation = solar gain issue
        needs_shading = radiation_correlation > 0.5 and compliance_rate < 80

        # Calculate severity
        severity = 0.0
        if needs_shading:
            # Based on both compliance and correlation strength
            compliance_factor = (100 - compliance_rate) / 100  # 0-1
            correlation_factor = radiation_correlation  # Already 0-1
            severity = (compliance_factor + correlation_factor) / 2

        # Description
        if needs_shading:
            description = (
                f"Strong solar heat gain detected. Solar radiation shows "
                f"correlation of {radiation_correlation:.2f} with overheating. "
                f"External shading recommended."
            )
        else:
            description = "Solar shading not required."

        return SolarShadingAnalysis(
            needed=needs_shading,
            severity=severity,
            correlation_with_radiation=radiation_correlation,
            correlation_with_temp=outdoor_temp_correlation,
            avg_radiation_during_overheat=avg_radiation,
            description=description,
        )


def analyze_solar_shading_need(
    compliance_rate: float,
    radiation_correlation: float,
    outdoor_temp_correlation: float = 0.0,
) -> bool:
    """Quick check if solar shading is needed."""
    analyzer = SolarShadingAnalyzer()
    result = analyzer.analyze(
        compliance_rate, radiation_correlation, outdoor_temp_correlation
    )
    return result.needed
