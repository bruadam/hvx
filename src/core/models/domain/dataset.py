"""Building dataset collection model."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

from src.core.models.domain.building import Building


class BuildingDataset(BaseModel):
    """Collection of buildings with metadata."""

    buildings: List[Building] = Field(default_factory=list, description="List of buildings")
    source_directory: str = Field(..., description="Root source data directory")
    loaded_at: datetime = Field(default_factory=datetime.now, description="When dataset was loaded")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def add_building(self, building: Building) -> None:
        """Add a building to the dataset."""
        existing_ids = {b.id for b in self.buildings}
        if building.id in existing_ids:
            raise ValueError(f"Building with ID {building.id} already exists in dataset")

        self.buildings.append(building)

    def get_building(self, building_id: str) -> Optional[Building]:
        """Get a building by ID."""
        for building in self.buildings:
            if building.id == building_id:
                return building
        return None

    def get_building_count(self) -> int:
        """Get number of buildings in dataset."""
        return len(self.buildings)

    def get_total_room_count(self) -> int:
        """Get total number of rooms across all buildings."""
        return sum(b.get_room_count() for b in self.buildings)

    def get_summary(self) -> Dict[str, Any]:
        """Get dataset summary."""
        return {
            'source_directory': self.source_directory,
            'loaded_at': self.loaded_at.isoformat(),
            'building_count': self.get_building_count(),
            'total_room_count': self.get_total_room_count(),
            'buildings': [
                {
                    'id': b.id,
                    'name': b.name,
                    'room_count': b.get_room_count(),
                    'level_count': b.get_level_count(),
                    'has_climate_data': b.climate_data is not None
                }
                for b in self.buildings
            ]
        }

    def save_to_json(self, filepath: Path) -> None:
        """Save dataset summary to JSON (not full data)."""
        import json

        summary = self.get_summary()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def save_to_pickle(self, filepath: Path) -> None:
        """Save full dataset to pickle file."""
        import pickle

        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load_from_pickle(cls, filepath: Path) -> 'BuildingDataset':
        """Load dataset from pickle file."""
        import pickle

        with open(filepath, 'rb') as f:
            return pickle.load(f)
