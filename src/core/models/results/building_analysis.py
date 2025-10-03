"""Building analysis results model."""

from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
import json

from src.core.models.enums import Status


class BuildingAnalysis(BaseModel):
    """Aggregated analysis results for a building."""

    # Identification
    building_id: str = Field(..., description="Unique building identifier")
    building_name: str = Field(..., description="Human-readable building name")

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    status: Status = Field(default=Status.COMPLETED, description="Analysis status")

    # Structure references
    level_ids: List[str] = Field(default_factory=list, description="IDs of levels in building")
    room_ids: List[str] = Field(default_factory=list, description="IDs of all rooms in building")
    level_count: int = Field(default=0, description="Number of levels")
    room_count: int = Field(default=0, description="Number of rooms analyzed")

    # Aggregated metrics
    avg_compliance_rate: float = Field(default=0.0, description="Average compliance rate", ge=0, le=100)
    avg_quality_score: float = Field(default=0.0, description="Average data quality score", ge=0, le=100)

    # Test aggregations
    test_aggregations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Aggregated test results across building"
    )

    # Level comparisons
    level_comparisons: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Comparison of levels"
    )

    # Rankings
    best_performing_levels: List[Dict[str, Any]] = Field(default_factory=list, description="Best levels")
    worst_performing_levels: List[Dict[str, Any]] = Field(default_factory=list, description="Worst levels")
    best_performing_rooms: List[Dict[str, Any]] = Field(default_factory=list, description="Best rooms")
    worst_performing_rooms: List[Dict[str, Any]] = Field(default_factory=list, description="Worst rooms")

    # Statistics
    statistics: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Building-wide statistics")

    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical building issues")
    recommendations: List[str] = Field(default_factory=list, description="Building-wide recommendations")

    # Climate correlation (if available)
    climate_correlations: Dict[str, float] = Field(
        default_factory=dict,
        description="Correlations with outdoor climate"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def save_to_json(self, filepath: Path) -> None:
        """Save analysis to JSON file."""
        data = self.model_dump(mode='json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    @classmethod
    def load_from_json(cls, filepath: Path) -> 'BuildingAnalysis':
        """Load analysis from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
