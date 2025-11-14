"""
Aggregator Models

Models for defining aggregation strategies (worst, best, average, weighted).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

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

    def aggregate(
        self,
        values: List[float],
        weights: Optional[List[float]] = None,
    ) -> Optional[float]:
        """
        Aggregate numerical values using the configured strategy.

        Args:
            values: List of numerical values to aggregate.
            weights: Optional weights aligned with values when using weighted modes.

        Returns:
            Aggregated value or None if no inputs.
        """
        if not values:
            return None

        if self.type == AggregatorType.WORST:
            return max(values)

        if self.type == AggregatorType.BEST:
            return min(values)

        if self.type == AggregatorType.AVERAGE:
            return sum(values) / len(values)

        if self.type in (AggregatorType.WEIGHTED_AVERAGE, AggregatorType.MULTI_PROPERTY_WEIGHTED):
            if not weights or len(weights) != len(values):
                raise ValueError("Weights must be provided and match values length for weighted aggregators")
            total_weight = sum(weights)
            if total_weight == 0:
                return sum(values) / len(values)
            return sum(v * w for v, w in zip(values, weights)) / total_weight

        # Default fallback
        return values[-1]


__all__ = [
    "Aggregator",
]
