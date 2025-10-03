"""Data models for IEQ Analytics.

This module provides a well-organized structure for all data models:
- enums: All enumerations (IEQ parameters, room types, severity levels, etc.)
- domain: Domain/semantic models (Building hierarchy, IEQ data, mappings)
- results: Analysis result models (room, level, building, portfolio analyses)
- reporting: Report template and section models
"""

# Enums
from src.core.models.enums import (
    IEQParameter,
    DataResolution,
    ComfortCategory,
    RoomType,
    Severity,
    Status,
    AnalysisLevel,
    SectionType,
    SortOrder,
    DEFAULT_COLUMN_MAPPINGS,
    BUILDING_TYPE_PATTERNS,
    ROOM_TYPE_PATTERNS,
)

# Domain models
from src.core.models.domain import (
    DataQuality,
    TimeSeriesData,
    ClimateData,
    Room,
    Level,
    Building,
    BuildingDataset,
    IEQData,
    ColumnMapping,
    MappingConfig,
)

# Results models
from src.core.models.results import (
    TestResult,
    RoomAnalysis,
    LevelAnalysis,
    BuildingAnalysis,
    PortfolioAnalysis,
    AnalysisResults,
)

# Reporting models
from src.core.models.reporting import (
    MetadataSection,
    TextSection,
    GraphSection,
    TableSection,
    SummarySection,
    RecommendationsSection,
    IssuesSection,
    LoopSection,
    ReportSection,
    ReportTemplate,
)

__all__ = [
    # Enums
    'IEQParameter',
    'RoomType',
    'DataResolution',
    'ComfortCategory',
    'Severity',
    'Status',
    'AnalysisLevel',
    'SectionType',
    'SortOrder',
    # Enum constants
    'DEFAULT_COLUMN_MAPPINGS',
    'BUILDING_TYPE_PATTERNS',
    'ROOM_TYPE_PATTERNS',
    # Domain models - Data quality
    'DataQuality',
    'TimeSeriesData',
    'ClimateData',
    # Domain models - Building hierarchy
    'Room',
    'Level',
    'Building',
    'BuildingDataset',
    # Domain models - IEQ data
    'IEQData',
    'ColumnMapping',
    'MappingConfig',
    # Results models
    'TestResult',
    'RoomAnalysis',
    'LevelAnalysis',
    'BuildingAnalysis',
    'PortfolioAnalysis',
    'AnalysisResults',
    # Reporting models
    'MetadataSection',
    'TextSection',
    'GraphSection',
    'TableSection',
    'SummarySection',
    'RecommendationsSection',
    'IssuesSection',
    'LoopSection',
    'ReportSection',
    'ReportTemplate',
]
