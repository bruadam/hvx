"""Core services for the IEQ Analytics platform.

Note: Services have been reorganized:
- HierarchicalAnalysisService -> src.core.analytics.hierarchical_analysis_service
- SmartRecommendationsService -> src.core.analytics.smart_recommendations_service  
- TestManagementService -> src.core.analytics.test_management_service
- TemplateService -> src.core.reporting.template_service
- ReportTemplateService -> src.core.reporting.report_template_service
"""

from src.core.analytics.AnalyticsService import *
from src.core.graphs.GraphService import *
from src.core.reporting.ReportService import *

# Backward compatibility imports
from src.core.analytics.hierarchical_analysis_service import HierarchicalAnalysisService
from src.core.analytics.smart_recommendations_service import SmartRecommendationsService
from src.core.analytics.test_management_service import TestManagementService
from src.core.reporting.template_service import TemplateService
from src.core.reporting.report_template_service import ReportTemplateService

__all__ = [
    'AnalyticsService',
    'GraphService',
    'ReportService',
    'HierarchicalAnalysisService',
    'SmartRecommendationsService', 
    'TestManagementService',
    'TemplateService',
    'ReportTemplateService',
    'create_hierarchical_analysis_service',
]
