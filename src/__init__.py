"""
IEQ Analytics Engine

A comprehensive analytics engine for Indoor Environmental Quality (IEQ) assessment
using IoT indoor climate sensors data.
"""

__version__ = "0.1.0"
__author__ = "Bruno Adam"

# Core analytics
from src.core import UnifiedAnalyticsEngine

# Services
from src.core.services import (
    GraphService,
    TemplateService,
    AnalyticsService,
    ReportService
)

__all__ = [
    "UnifiedAnalyticsEngine",
    "GraphService",
    "TemplateService",
    "AnalyticsService",
    "ReportService",
]
