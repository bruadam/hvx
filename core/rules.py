"""
Rule and Applicability Models

Models for defining test rules, applicability conditions, and rule sets.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import (
    MetricType,
    RuleOperator,
    Season,
    StandardType,
    VentilationType,
    DynamicFunctionType,
)


class StandardDefinition(BaseModel):
    """
    Metadata describing a regulation or internal standard.
    """

    id: str  # e.g. "en16798_1"
    name: str
    version: str
    jurisdiction: str  # e.g. "EU", "DK"
    scope: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuleClause(BaseModel):
    """
    Machine-friendly representation of a single clause in a standard.
    """

    id: str
    description: Optional[str] = None
    metric: MetricType
    category: Optional[str] = None

    condition: Dict[str, Any] = Field(default_factory=dict)
    thresholds: Dict[str, Any] = Field(default_factory=dict)
    severity: Optional[str] = None
    rationale: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApplicabilityCondition(BaseModel):
    """
    Generic applicability condition.

    All fields are ANDed inside one condition;
    multiple conditions in a RuleSet are usually ORed.
    """
    id: str

    countries: Optional[List[str]] = None      # ["EU"], ["US"], ["DK"]
    regions: Optional[List[str]] = None        # ["NA", "Nordic", "California"]
    climate_zones: Optional[List[str]] = None  # ["Cfb", "Dfb", etc.]

    building_types: Optional[List[str]] = None
    room_types: Optional[List[str]] = None

    min_area_m2: Optional[float] = None
    max_area_m2: Optional[float] = None

    ventilation_types: Optional[List[VentilationType]] = None
    seasons: Optional[List[Season]] = None

    dynamic_functions: Optional[List[DynamicFunctionType]] = None

    # Free-form; e.g. {"min_year_built": 1980}
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestRule(BaseModel):
    """
    Reusable rule definition like:
    - Temperature < 26°C with tolerance 100h/year
    - 20°C <= Temperature <= 26°C with tolerance 100h/year
    - CO2 < 1000ppm for 95% occupied hours
    """
    id: str
    name: str
    description: Optional[str] = None

    metric: MetricType
    operator: RuleOperator

    # For simple comparisons
    target_value: Optional[float] = None

    # For ranges (between / outside_range)
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

    # Tolerance settings
    tolerance_hours: Optional[float] = None          # e.g. 100 hours
    tolerance_percentage: Optional[float] = None     # e.g. 20% of occupied time

    # Time window expressed in ISO8601 or descriptive strings
    # e.g. "P1Y", "P1M", "P7D"
    time_window: Optional[str] = None

    # When to apply: "occupied", "always", or custom tags
    applies_during: Optional[str] = None

    # For adaptive/dynamic rules: expression references
    # These would be interpreted by the engine, not Pydantic
    dynamic_lower_expr: Optional[str] = None
    dynamic_upper_expr: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuleSet(BaseModel):
    """
    Bundle of rules (e.g. EN16798 Cat II, ASHRAE 55, internal corporate standard)
    with applicability conditions.
    """
    id: str
    name: str
    standard: StandardType
    description: Optional[str] = None

    # e.g. "Category II", "Office", "InternalPolicyA"
    category: Optional[str] = None

    rules: List[TestRule] = Field(default_factory=list)
    applicability_conditions: List[ApplicabilityCondition] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class CountryRuleProfile(BaseModel):
    """
    Mapping of countries/regions to applicable standards and overrides.
    """

    country_code: str
    standard_ids: List[str] = Field(default_factory=list)
    overrides: Dict[str, RuleClause] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "StandardDefinition",
    "RuleClause",
    "ApplicabilityCondition",
    "TestRule",
    "RuleSet",
    "CountryRuleProfile",
]
