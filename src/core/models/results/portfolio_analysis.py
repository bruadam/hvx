"""Portfolio analysis results model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
import json

from src.core.models.enums import Status


class PortfolioAnalysis(BaseModel):
    """Aggregated analysis results for a portfolio of buildings."""

    # Identification
    portfolio_name: str = Field(..., description="Portfolio name")
    portfolio_id: Optional[str] = Field(None, description="Portfolio identifier")

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    status: Status = Field(default=Status.COMPLETED, description="Analysis status")

    # Structure references
    building_ids: List[str] = Field(default_factory=list, description="IDs of buildings in portfolio")
    building_count: int = Field(default=0, description="Number of buildings")
    total_room_count: int = Field(default=0, description="Total rooms across portfolio")
    total_level_count: int = Field(default=0, description="Total levels across portfolio")

    # Aggregated metrics
    avg_compliance_rate: float = Field(default=0.0, description="Portfolio average compliance", ge=0, le=100)
    avg_quality_score: float = Field(default=0.0, description="Portfolio average quality", ge=0, le=100)

    # Test aggregations
    test_aggregations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Aggregated test results across portfolio"
    )

    # Building comparisons
    building_comparisons: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Comparison of buildings"
    )

    # Rankings
    best_performing_buildings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Best performing buildings"
    )
    worst_performing_buildings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Buildings needing attention"
    )

    # Benchmark statistics
    benchmark_statistics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Benchmark stats across portfolio"
    )

    # Portfolio-wide insights
    portfolio_trends: Dict[str, Any] = Field(default_factory=dict, description="Trends across portfolio")
    common_issues: List[Dict[str, Any]] = Field(default_factory=list, description="Common issues found")

    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical portfolio issues")
    recommendations: List[str] = Field(default_factory=list, description="Portfolio-wide recommendations")

    # Investment priorities
    investment_priorities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Prioritized investment recommendations"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def save_to_json(self, filepath: Path) -> None:
        """Save analysis to JSON file."""
        data = self.model_dump(mode='json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    @classmethod
    def load_from_json(cls, filepath: Path) -> 'PortfolioAnalysis':
        """Load analysis from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
