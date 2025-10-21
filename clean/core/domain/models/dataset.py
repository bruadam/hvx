"""Dataset collection entity."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field


class Dataset(BaseModel):
    """
    Dataset collection entity managing multiple buildings.

    Represents a portfolio or collection of buildings to be analyzed together.
    """

    # Identity
    id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Dataset name")

    # Contained buildings
    building_ids: List[str] = Field(default_factory=list, description="IDs of buildings in dataset")

    # Source information
    source_directory: Path = Field(..., description="Root source data directory")
    loaded_at: datetime = Field(default_factory=datetime.now, description="When dataset was loaded")

    # Metadata
    description: Optional[str] = Field(default=None, description="Dataset description")
    version: Optional[str] = Field(default=None, description="Dataset version")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Custom attributes and metadata"
    )

    model_config = {"arbitrary_types_allowed": True}  # Allow Path

    def add_building(self, building_id: str) -> None:
        """
        Add a building to this dataset.

        Args:
            building_id: Building identifier to add

        Raises:
            ValueError: If building already exists in dataset
        """
        if building_id in self.building_ids:
            raise ValueError(f"Building {building_id} already exists in dataset")
        self.building_ids.append(building_id)

    def remove_building(self, building_id: str) -> bool:
        """
        Remove a building from this dataset.

        Args:
            building_id: Building identifier to remove

        Returns:
            True if building was removed, False if not found
        """
        if building_id in self.building_ids:
            self.building_ids.remove(building_id)
            return True
        return False

    def has_building(self, building_id: str) -> bool:
        """Check if dataset contains a specific building."""
        return building_id in self.building_ids

    @property
    def building_count(self) -> int:
        """Get number of buildings in dataset."""
        return len(self.building_ids)

    @property
    def is_empty(self) -> bool:
        """Check if dataset has no buildings."""
        return len(self.building_ids) == 0

    def get_summary(self) -> Dict[str, Any]:
        """Get summary information about this dataset."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "building_count": self.building_count,
            "source_directory": str(self.source_directory),
            "loaded_at": self.loaded_at.isoformat(),
            "version": self.version,
            "building_ids": self.building_ids,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Dataset(name={self.name}, buildings={self.building_count})"

    def __repr__(self) -> str:
        """Repr representation."""
        return f"Dataset(id={self.id!r}, name={self.name!r}, building_count={self.building_count})"
