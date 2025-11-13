"""Use case for loading building data."""

from pathlib import Path

from core.domain.models.building import Building
from core.domain.models.dataset import Dataset
from core.domain.models.level import Level
from core.domain.models.room import Room
from core.infrastructure.data_loaders.dataset_builder import DatasetBuilder


class LoadDataUseCase:
    """Use case for loading building data from directory."""

    def __init__(self):
        """Initialize use case."""
        self.dataset_builder = DatasetBuilder()

    def execute(
        self,
        data_directory: Path,
        dataset_id: str = "dataset",
        dataset_name: str = "IEQ Dataset",
    ) -> tuple[Dataset, dict[str, Building], dict[str, Level], dict[str, Room]]:
        """
        Load building data from directory.

        Args:
            data_directory: Path to directory containing building data
            dataset_id: Unique identifier for dataset
            dataset_name: Human-readable name for dataset

        Returns:
            Tuple of (dataset, buildings_dict, levels_dict, rooms_dict)

        Raises:
            FileNotFoundError: If directory doesn't exist
            ValueError: If data format is invalid
        """
        if not data_directory.exists():
            raise FileNotFoundError(f"Data directory not found: {data_directory}")

        dataset, buildings, levels, rooms = self.dataset_builder.build_from_directory(
            root_dir=data_directory,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
        )

        return dataset, buildings, levels, rooms
