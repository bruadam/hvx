"""Base models package.

This package contains abstract base classes that provide common functionality
for all domain models, reducing code duplication and ensuring consistency.
"""

from core.domain.models.base.base_analysis import BaseAnalysis, MetricsAnalysis
from core.domain.models.base.base_dataset import SensorDataset
from core.domain.models.base.base_entity import BaseEntity, HierarchicalEntity
from core.domain.models.base.base_measurement import BaseMeasurement, UtilityConsumption
from core.domain.models.base.base_validation import BaseValidation, ComplianceValidation

__all__ = [
    # Entity bases
    "BaseEntity",
    "HierarchicalEntity",
    # Measurement bases
    "BaseMeasurement",
    "UtilityConsumption",
    # Validation bases
    "BaseValidation",
    "ComplianceValidation",
    # Analysis bases
    "BaseAnalysis",
    "MetricsAnalysis",
    # Dataset bases
    "SensorDataset",
]
