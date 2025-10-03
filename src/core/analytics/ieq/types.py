from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass

class Method(Enum):
    """Types of analysis supported."""
    USER_RULES = "user_rules"
    EN16798_COMPLIANCE = "en16798_compliance"
    BASIC_STATISTICS = "basic_statistics"
    DATA_QUALITY = "data_quality"

class RuleType(Enum):
    """Types of rules supported."""
    BIDIRECTIONAL = "bidirectional"
    UNIDIRECTIONAL_ASCENDING = "unidirectional_ascending"
    UNIDIRECTIONAL_DESCENDING = "unidirectional_descending"
    COMPLEX = "complex"

@dataclass
class AnalysisResult:
    """Standardized analysis result."""
    parameter: str
    rule_name: str
    compliance_rate: float
    total_points: int
    compliant_points: int
    violations: List[Dict[str, Any]]
    statistics: Dict[str, float]
    recommendations: List[str]
    metadata: Dict[str, Any]