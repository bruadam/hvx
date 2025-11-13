"""Base classes for data sources (metering and simulated)."""

from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


class DataSourceType(Enum):
    """Type of data source."""
    METERING = "metering"  # Real sensors/meters
    SIMULATED = "simulated"  # Model-derived/computed


class DataCategory(Enum):
    """Category of data."""
    CLIMATE = "climate"  # Temperature, humidity, CO2, etc.
    ENERGY = "energy"  # Electricity, heating, cooling consumption
    WATER = "water"  # Water consumption
    VENTILATION = "ventilation"  # Air flow, ACH
    COMFORT = "comfort"  # Thermal comfort indices
    OCCUPANCY = "occupancy"  # People count, presence


class BaseDataSource(BaseModel):
    """
    Base class for all data sources (metering and simulated).
    
    Data sources have:
    1. Their own hierarchy (parent_data_source_id for meter→submeter relationships)
    2. Link to structural entity (linked_entity_id for Building/Room assignment)
    3. Time-series data or point values
    """
    
    id: str = Field(description="Unique identifier")
    name: str = Field(description="Human-readable name")
    source_type: DataSourceType = Field(description="Metering or simulated")
    data_category: DataCategory = Field(description="What type of data")
    
    # Dual relationships
    parent_data_source_id: str | None = Field(
        default=None,
        description="Parent data source (e.g., main meter → sub-meter)"
    )
    linked_entity_id: str = Field(
        description="Structural entity this data source is assigned to"
    )
    
    # Data storage
    time_series_data: pd.DataFrame | None = Field(
        default=None,
        description="Time-series measurements",
        exclude=True
    )
    point_value: float | None = Field(
        default=None,
        description="Single point value (e.g., annual consumption)"
    )
    
    # Metadata
    unit: str = Field(default="", description="Unit of measurement")
    description: str = Field(default="", description="Detailed description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default=None)
    
    class Config:
        arbitrary_types_allowed = True


class MeteringDataSource(BaseDataSource):
    """
    Real sensor or meter data.
    
    Examples:
    - Climate sensor in Room 101
    - Electricity meter for Building A
    - Sub-meter for HVAC system
    """
    
    source_type: DataSourceType = Field(default=DataSourceType.METERING)
    
    # Metering-specific fields
    sensor_id: str | None = Field(default=None, description="Physical sensor/device ID")
    calibration_date: datetime | None = Field(default=None)
    accuracy: float | None = Field(default=None, description="Sensor accuracy ±%")
    

class SimulatedDataSource(BaseDataSource):
    """
    Model-derived or computed data.
    
    Examples:
    - Thermal model predicting heating consumption
    - Ventilation model estimating ACH from CO2 decay
    - Comfort model calculating PMV/PPD
    
    Can be compared with metering data for validation.
    """
    
    source_type: DataSourceType = Field(default=DataSourceType.SIMULATED)
    
    # Simulation-specific fields
    model_name: str = Field(description="Name of the model used")
    model_version: str | None = Field(default=None)
    input_data_sources: list[str] = Field(
        default_factory=list,
        description="IDs of metering data sources used as input"
    )
    comparable_metering_source_id: str | None = Field(
        default=None,
        description="Metering data source to compare against (e.g., actual energy consumption)"
    )
    model_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Model configuration/parameters"
    )
    validation_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Comparison metrics vs actual data (RMSE, MAE, R²)"
    )
