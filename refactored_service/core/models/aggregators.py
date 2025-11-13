"""
Aggregator Models

Models for defining aggregation strategies (worst, best, average, weighted).
"""

from __future__ import annotations
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .enums import AggregatorType


class Aggregator(BaseModel):
    """
    Defines an aggregation strategy for combining child results.

    Used to aggregate compliance results, metrics, or ratings across
    multiple spatial entities.
    """
    id: str
    name: str
    type: AggregatorType

    # For weighted aggregators: list of properties to use as weights
    # e.g. ["area_m2"], or ["area_m2", "design_occupancy"]
    weight_properties: List[str] = Field(default_factory=list)

    # Optional config (e.g. tie-breaking rules, normalization, etc.)
    config: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "Aggregator",
]
