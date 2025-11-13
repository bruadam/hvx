from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class RuleOperator(str, Enum):
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    BETWEEN = "between"
    OUTSIDE_RANGE = "outside_range"
    EQ = "eq"
    NE = "ne"

class TestRule(BaseModel):
    id: str
    name: str
    metric: str
    operator: RuleOperator

    target_value: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

    tolerance_hours: Optional[float] = None
    tolerance_percentage: Optional[float] = None
    time_window: Optional[str] = None
    applies_during: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

class ApplicabilityCondition(BaseModel):
    id: str
    countries: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    continents: Optional[List[str]] = None
    building_types: Optional[List[str]] = None
    room_types: Optional[List[str]] = None
    min_area_m2: Optional[float] = None
    max_area_m2: Optional[float] = None
    ventilation_types: Optional[List[str]] = None
    seasons: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RuleSet(BaseModel):
    id: str
    name: str
    standard: str
    category: Optional[str] = None
    rules: List[TestRule] = Field(default_factory=list)
    applicability_conditions: List[ApplicabilityCondition] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
