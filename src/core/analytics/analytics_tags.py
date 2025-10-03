"""
Analytics Tags and Requirements System

Defines the tagging system for analytics capabilities and requirements.
Links report sections/graphs to required analytics, tests, and standards.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict, Any


class AnalyticsTag(Enum):
    """Tags for different types of analytics."""
    
    # Statistical Analytics
    STATISTICS_BASIC = "statistics.basic"  # Mean, median, std, min, max
    STATISTICS_DISTRIBUTION = "statistics.distribution"  # Histograms, quartiles
    STATISTICS_TRENDS = "statistics.trends"  # Time series trends, seasonality
    STATISTICS_CORRELATION = "statistics.correlation"  # Parameter correlations
    
    # Compliance Analytics
    COMPLIANCE_OVERALL = "compliance.overall"  # Overall compliance rates
    COMPLIANCE_TEMPORAL = "compliance.temporal"  # Time-based compliance
    COMPLIANCE_SPATIAL = "compliance.spatial"  # Room/zone compliance
    COMPLIANCE_THRESHOLD = "compliance.threshold"  # Threshold exceedances
    
    # Weather Correlation Analytics
    WEATHER_TEMPERATURE = "weather.temperature"  # Temperature correlation
    WEATHER_HUMIDITY = "weather.humidity"  # Humidity correlation
    WEATHER_OUTDOOR_CONDITIONS = "weather.outdoor_conditions"  # General weather
    WEATHER_SEASONAL = "weather.seasonal"  # Seasonal patterns
    
    # Recommendation Analytics
    RECOMMENDATIONS_HVAC = "recommendations.hvac"  # HVAC-related
    RECOMMENDATIONS_VENTILATION = "recommendations.ventilation"  # Ventilation
    RECOMMENDATIONS_INSULATION = "recommendations.insulation"  # Insulation
    RECOMMENDATIONS_OPERATIONAL = "recommendations.operational"  # Operations
    RECOMMENDATIONS_SMART = "recommendations.smart"  # Smart/ML-based
    
    # Data Quality Analytics
    DATA_QUALITY_COMPLETENESS = "data_quality.completeness"  # Missing data
    DATA_QUALITY_VALIDITY = "data_quality.validity"  # Valid ranges
    DATA_QUALITY_CONSISTENCY = "data_quality.consistency"  # Consistency checks
    
    # Performance Analytics
    PERFORMANCE_SCORING = "performance.scoring"  # Overall scores
    PERFORMANCE_RANKING = "performance.ranking"  # Rankings/comparisons
    PERFORMANCE_BENCHMARKING = "performance.benchmarking"  # Against targets
    
    # Temporal Analytics
    TEMPORAL_HOURLY = "temporal.hourly"  # Hourly patterns
    TEMPORAL_DAILY = "temporal.daily"  # Daily patterns
    TEMPORAL_WEEKLY = "temporal.weekly"  # Weekly patterns
    TEMPORAL_MONTHLY = "temporal.monthly"  # Monthly patterns
    TEMPORAL_SEASONAL = "temporal.seasonal"  # Seasonal patterns
    
    # Spatial Analytics
    SPATIAL_ROOM_LEVEL = "spatial.room_level"  # Individual room analysis
    SPATIAL_BUILDING_LEVEL = "spatial.building_level"  # Building aggregation
    SPATIAL_PORTFOLIO_LEVEL = "spatial.portfolio_level"  # Multi-building
    SPATIAL_COMPARISON = "spatial.comparison"  # Spatial comparisons
    
    # Advanced Analytics
    ADVANCED_ANOMALY_DETECTION = "advanced.anomaly_detection"  # Anomalies
    ADVANCED_PATTERN_RECOGNITION = "advanced.pattern_recognition"  # Patterns
    ADVANCED_PREDICTIVE = "advanced.predictive"  # Predictions
    

class GraphTag(Enum):
    """Tags for different types of graphs/visualizations."""
    
    # Time Series
    GRAPH_TIME_SERIES_LINE = "graph.time_series.line"
    GRAPH_TIME_SERIES_AREA = "graph.time_series.area"
    GRAPH_TIME_SERIES_SCATTER = "graph.time_series.scatter"
    
    # Distribution
    GRAPH_HISTOGRAM = "graph.distribution.histogram"
    GRAPH_BOX_PLOT = "graph.distribution.box"
    GRAPH_VIOLIN_PLOT = "graph.distribution.violin"
    
    # Comparison
    GRAPH_BAR_CHART = "graph.comparison.bar"
    GRAPH_HORIZONTAL_BAR = "graph.comparison.horizontal_bar"
    GRAPH_GROUPED_BAR = "graph.comparison.grouped_bar"
    GRAPH_STACKED_BAR = "graph.comparison.stacked_bar"
    
    # Correlation
    GRAPH_SCATTER_PLOT = "graph.correlation.scatter"
    GRAPH_CORRELATION_MATRIX = "graph.correlation.matrix"
    GRAPH_HEATMAP = "graph.correlation.heatmap"
    
    # Spatial
    GRAPH_HEATMAP_TEMPORAL = "graph.spatial.heatmap_temporal"
    GRAPH_FLOOR_PLAN = "graph.spatial.floor_plan"
    GRAPH_GEOGRAPHIC = "graph.spatial.geographic"
    
    # Performance
    GRAPH_GAUGE = "graph.performance.gauge"
    GRAPH_RADAR = "graph.performance.radar"
    GRAPH_SCORE_CARD = "graph.performance.scorecard"
    

@dataclass
class AnalyticsRequirement:
    """Defines what analytics are required for a report section or graph."""
    
    # Analytics tags required
    analytics_tags: Set[AnalyticsTag] = field(default_factory=set)
    
    # Specific tests required (by test ID or pattern)
    required_tests: Set[str] = field(default_factory=set)
    
    # Standards required (by standard ID)
    required_standards: Set[str] = field(default_factory=set)
    
    # Specific parameters required (e.g., "temperature", "co2")
    required_parameters: Set[str] = field(default_factory=set)
    
    # Data level required (room, building, portfolio)
    required_level: Optional[str] = None
    
    # Optional: minimum data quality threshold
    min_data_quality: Optional[float] = None
    
    # Optional: time range requirements
    min_time_range_days: Optional[int] = None
    
    # Optional: custom requirements as key-value pairs
    custom_requirements: Dict[str, Any] = field(default_factory=dict)
    
    def add_analytics_tag(self, tag: AnalyticsTag):
        """Add an analytics tag requirement."""
        self.analytics_tags.add(tag)
    
    def add_test(self, test_id: str):
        """Add a test requirement."""
        self.required_tests.add(test_id)
    
    def add_standard(self, standard_id: str):
        """Add a standard requirement."""
        self.required_standards.add(standard_id)
    
    def add_parameter(self, parameter: str):
        """Add a parameter requirement."""
        self.required_parameters.add(parameter)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            'analytics_tags': [tag.value for tag in self.analytics_tags],
            'required_tests': list(self.required_tests),
            'required_standards': list(self.required_standards),
            'required_parameters': list(self.required_parameters),
            'required_level': self.required_level,
            'min_data_quality': self.min_data_quality,
            'min_time_range_days': self.min_time_range_days,
            'custom_requirements': self.custom_requirements
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsRequirement':
        """Create from dictionary loaded from YAML."""
        req = cls()
        
        # Parse analytics tags
        for tag_str in data.get('analytics_tags', []):
            try:
                tag = AnalyticsTag(tag_str)
                req.analytics_tags.add(tag)
            except ValueError:
                # Skip invalid tags
                pass
        
        # Parse other fields
        req.required_tests = set(data.get('required_tests', []))
        req.required_standards = set(data.get('required_standards', []))
        req.required_parameters = set(data.get('required_parameters', []))
        req.required_level = data.get('required_level')
        req.min_data_quality = data.get('min_data_quality')
        req.min_time_range_days = data.get('min_time_range_days')
        req.custom_requirements = data.get('custom_requirements', {})
        
        return req


@dataclass
class AnalyticsCapability:
    """Describes what analytics are available in the analysis results."""
    
    # Available analytics tags
    available_tags: Set[AnalyticsTag] = field(default_factory=set)
    
    # Completed tests
    completed_tests: Set[str] = field(default_factory=set)
    
    # Applied standards
    applied_standards: Set[str] = field(default_factory=set)
    
    # Available parameters
    available_parameters: Set[str] = field(default_factory=set)
    
    # Analysis level (room, building, portfolio)
    analysis_level: Optional[str] = None
    
    # Data quality score
    data_quality_score: Optional[float] = None
    
    # Time range covered (in days)
    time_range_days: Optional[int] = None
    
    # Custom capabilities
    custom_capabilities: Dict[str, Any] = field(default_factory=dict)
    
    def has_tag(self, tag: AnalyticsTag) -> bool:
        """Check if a specific analytics tag is available."""
        return tag in self.available_tags
    
    def has_test(self, test_id: str) -> bool:
        """Check if a specific test was completed."""
        return test_id in self.completed_tests
    
    def has_standard(self, standard_id: str) -> bool:
        """Check if a specific standard was applied."""
        return standard_id in self.applied_standards
    
    def has_parameter(self, parameter: str) -> bool:
        """Check if a specific parameter is available."""
        return parameter in self.available_parameters


@dataclass
class ValidationResult:
    """Result of validating analytics requirements against capabilities."""
    
    # Whether all requirements are met
    is_valid: bool
    
    # Missing analytics tags
    missing_tags: Set[AnalyticsTag] = field(default_factory=set)
    
    # Missing tests
    missing_tests: Set[str] = field(default_factory=set)
    
    # Missing standards
    missing_standards: Set[str] = field(default_factory=set)
    
    # Missing parameters
    missing_parameters: Set[str] = field(default_factory=set)
    
    # Validation messages
    messages: List[str] = field(default_factory=list)
    
    # Warnings (non-critical issues)
    warnings: List[str] = field(default_factory=list)
    
    def add_message(self, message: str):
        """Add a validation message."""
        self.messages.append(message)
    
    def add_warning(self, warning: str):
        """Add a validation warning."""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'missing_tags': [tag.value for tag in self.missing_tags],
            'missing_tests': list(self.missing_tests),
            'missing_standards': list(self.missing_standards),
            'missing_parameters': list(self.missing_parameters),
            'messages': self.messages,
            'warnings': self.warnings
        }


# Predefined requirement templates for common use cases
REQUIREMENT_TEMPLATES = {
    'basic_summary': AnalyticsRequirement(
        analytics_tags={
            AnalyticsTag.STATISTICS_BASIC,
            AnalyticsTag.COMPLIANCE_OVERALL,
            AnalyticsTag.DATA_QUALITY_COMPLETENESS
        }
    ),
    
    'compliance_analysis': AnalyticsRequirement(
        analytics_tags={
            AnalyticsTag.COMPLIANCE_OVERALL,
            AnalyticsTag.COMPLIANCE_TEMPORAL,
            AnalyticsTag.COMPLIANCE_SPATIAL,
            AnalyticsTag.STATISTICS_BASIC
        }
    ),
    
    'weather_correlation': AnalyticsRequirement(
        analytics_tags={
            AnalyticsTag.WEATHER_TEMPERATURE,
            AnalyticsTag.WEATHER_OUTDOOR_CONDITIONS,
            AnalyticsTag.STATISTICS_CORRELATION
        }
    ),
    
    'recommendations': AnalyticsRequirement(
        analytics_tags={
            AnalyticsTag.RECOMMENDATIONS_HVAC,
            AnalyticsTag.RECOMMENDATIONS_VENTILATION,
            AnalyticsTag.RECOMMENDATIONS_OPERATIONAL,
            AnalyticsTag.COMPLIANCE_OVERALL
        }
    ),
    
    'temporal_analysis': AnalyticsRequirement(
        analytics_tags={
            AnalyticsTag.TEMPORAL_HOURLY,
            AnalyticsTag.TEMPORAL_DAILY,
            AnalyticsTag.STATISTICS_TRENDS
        }
    ),
    
    'room_comparison': AnalyticsRequirement(
        analytics_tags={
            AnalyticsTag.SPATIAL_ROOM_LEVEL,
            AnalyticsTag.SPATIAL_COMPARISON,
            AnalyticsTag.PERFORMANCE_RANKING,
            AnalyticsTag.STATISTICS_BASIC
        }
    ),
}


__all__ = [
    'AnalyticsTag',
    'GraphTag',
    'AnalyticsRequirement',
    'AnalyticsCapability',
    'ValidationResult',
    'REQUIREMENT_TEMPLATES'
]
