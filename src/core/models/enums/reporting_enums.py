"""Reporting-related enumerations."""

from enum import Enum


class AnalysisLevel(Enum):
    """Analysis hierarchy levels."""
    PORTFOLIO = "portfolio"
    BUILDING = "building"
    LEVEL = "level"
    ROOM = "room"


class SectionType(Enum):
    """Report section types."""
    METADATA = "metadata"
    TEXT = "text"
    GRAPH = "graph"
    TABLE = "table"
    SUMMARY = "summary"
    RECOMMENDATIONS = "recommendations"
    ISSUES = "issues"
    LOOP = "loop"


class SortOrder(Enum):
    """Sorting order for entities."""
    BEST_FIRST = "best_first"
    WORST_FIRST = "worst_first"
    ALPHABETICAL = "alphabetical"
    NONE = "none"
