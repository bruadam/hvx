"""Level analysis results model."""

from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
import json

from src.core.models.enums import Status


class LevelAnalysis(BaseModel):
    """Aggregated analysis results for a building level/floor."""

    # Identification
    level_id: str = Field(..., description="Unique level identifier")
    level_name: str = Field(..., description="Human-readable level name")
    building_id: str = Field(..., description="Building identifier")

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    status: Status = Field(default=Status.COMPLETED, description="Analysis status")

    # Room references
    room_ids: List[str] = Field(default_factory=list, description="IDs of rooms on this level")
    room_count: int = Field(default=0, description="Number of rooms analyzed")

    # Aggregated metrics
    avg_compliance_rate: float = Field(default=0.0, description="Average compliance rate", ge=0, le=100)
    avg_quality_score: float = Field(default=0.0, description="Average data quality score", ge=0, le=100)

    # Test aggregations
    test_aggregations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Aggregated test results (avg, min, max, etc.)"
    )

    # Room rankings
    best_performing_rooms: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top performing rooms"
    )
    worst_performing_rooms: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Rooms needing attention"
    )

    # Statistics
    statistics: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Aggregated statistics")

    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical issues at level")
    recommendations: List[str] = Field(default_factory=list, description="Level-wide recommendations")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def save_to_json(self, filepath: Path) -> None:
        """Save analysis to JSON file."""
        data = self.model_dump(mode='json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    @classmethod
    def load_from_json(cls, filepath: Path) -> 'LevelAnalysis':
        """Load analysis from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
