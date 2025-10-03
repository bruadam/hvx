"""Container for all analysis results."""

from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

from src.core.models.results.room_analysis import RoomAnalysis
from src.core.models.results.level_analysis import LevelAnalysis
from src.core.models.results.building_analysis import BuildingAnalysis
from src.core.models.results.portfolio_analysis import PortfolioAnalysis


class AnalysisResults(BaseModel):
    """Container for all analysis results."""

    portfolio: Optional[PortfolioAnalysis] = Field(None, description="Portfolio-level analysis")
    buildings: Dict[str, BuildingAnalysis] = Field(default_factory=dict, description="Building analyses by ID")
    levels: Dict[str, LevelAnalysis] = Field(default_factory=dict, description="Level analyses by ID")
    rooms: Dict[str, RoomAnalysis] = Field(default_factory=dict, description="Room analyses by ID")

    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata")

    def get_room_analysis(self, room_id: str) -> Optional[RoomAnalysis]:
        """Get room analysis by ID."""
        return self.rooms.get(room_id)

    def get_level_analysis(self, level_id: str) -> Optional[LevelAnalysis]:
        """Get level analysis by ID."""
        return self.levels.get(level_id)

    def get_building_analysis(self, building_id: str) -> Optional[BuildingAnalysis]:
        """Get building analysis by ID."""
        return self.buildings.get(building_id)

    def save_all_to_directory(self, output_dir: Path) -> None:
        """Save all analyses to a directory structure."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save portfolio
        if self.portfolio:
            portfolio_file = output_dir / "portfolio_analysis.json"
            self.portfolio.save_to_json(portfolio_file)

        # Save buildings
        buildings_dir = output_dir / "buildings"
        buildings_dir.mkdir(exist_ok=True)
        for building_id, analysis in self.buildings.items():
            building_file = buildings_dir / f"{building_id}.json"
            analysis.save_to_json(building_file)

        # Save levels
        levels_dir = output_dir / "levels"
        levels_dir.mkdir(exist_ok=True)
        for level_id, analysis in self.levels.items():
            level_file = levels_dir / f"{level_id}.json"
            analysis.save_to_json(level_file)

        # Save rooms
        rooms_dir = output_dir / "rooms"
        rooms_dir.mkdir(exist_ok=True)
        for room_id, analysis in self.rooms.items():
            room_file = rooms_dir / f"{room_id}.json"
            analysis.save_to_json(room_file)
