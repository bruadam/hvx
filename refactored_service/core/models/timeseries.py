from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class DataSourceType(str, Enum):
    MEASURED = "measured"
    SIMULATED = "simulated"
    HYBRID = "hybrid"
    EXTERNAL_API = "external_api"

class MetricType(str, Enum):
    TEMPERATURE = "temperature"
    CO2 = "co2"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
    ENERGY = "energy"
    POWER = "power"
    WATER = "water"
    OTHER = "other"

class TimeSeries(BaseModel):
    id: str
    point_id: str
    spatial_entity_id: str
    metric: MetricType
    timestamps: List[str]
    values: List[float]

    source_type: DataSourceType
    unit: Optional[str] = None

    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    brick_class: Optional[str] = None
    brick_uri: Optional[str] = None
