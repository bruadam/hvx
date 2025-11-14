"""
Analysis- and model-related enums.
"""

from enum import Enum


class AggregatorType(str, Enum):
    WORST = "worst"
    BEST = "best"
    AVERAGE = "average"
    WEIGHTED_AVERAGE = "weighted_average"
    MULTI_PROPERTY_WEIGHTED = "multi_property_weighted"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, Enum):
    TEST_RESULT = "test_result"
    COMPLIANCE = "compliance"
    AGGREGATED = "aggregated"
    FORECAST = "forecast"
    ENERGY_SIGNATURE = "energy_signature"
    SIMULATION_RUN = "simulation_run"
    OTHER = "other"


class ModelType(str, Enum):
    ENERGY_MODEL = "energy_model"
    COMFORT_MODEL = "comfort_model"
    CLIMATE_MODEL = "climate_model"
    FORECAST_MODEL = "forecast_model"
    DATA_DRIVEN_MODEL = "data_driven_model"


__all__ = [
    "AggregatorType",
    "AnalysisStatus",
    "AnalysisType",
    "ModelType",
]
