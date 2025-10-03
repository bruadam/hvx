"""
Building Management Service

Manages in-memory building hierarchy: buildings, levels, rooms, and CSV uploads.
Provides CRUD operations and persists to BuildingDataset format.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import uuid

from src.core.models.building_data import (
    BuildingDataset, Building, Level, Room, TimeSeriesData, DataQuality
)
from src.core.models.enums import RoomType

logger = logging.getLogger(__name__)


class BuildingManagementService:
    """Service for managing building hierarchy and data uploads."""

    def __init__(self):
        """Initialize the building management service."""
        self.datasets: Dict[str, BuildingDataset] = {}
        self.active_dataset_id: Optional[str] = None

    # ========== Dataset Management ==========

    def create_dataset(self, name: str, source_directory: str = "user_created") -> str:
        """
        Create a new dataset.

        Returns:
            dataset_id: Unique identifier for the dataset
        """
        dataset_id = f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        dataset = BuildingDataset(
            buildings=[],
            source_directory=source_directory,
            metadata={"name": name, "created_by": "user"}
        )

        self.datasets[dataset_id] = dataset
        self.active_dataset_id = dataset_id

        logger.info(f"Created dataset: {dataset_id}")
        return dataset_id

    def get_dataset(self, dataset_id: str) -> Optional[BuildingDataset]:
        """Get a dataset by ID."""
        return self.datasets.get(dataset_id)

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all datasets."""
        return [
            {
                "dataset_id": dataset_id,
                "name": dataset.metadata.get("name", "Unnamed"),
                "building_count": dataset.get_building_count(),
                "room_count": dataset.get_total_room_count(),
                "created_at": dataset.loaded_at.isoformat()
            }
            for dataset_id, dataset in self.datasets.items()
        ]

    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset."""
        if dataset_id in self.datasets:
            del self.datasets[dataset_id]
            if self.active_dataset_id == dataset_id:
                self.active_dataset_id = None
            logger.info(f"Deleted dataset: {dataset_id}")
            return True
        return False

    def save_dataset(self, dataset_id: str, output_path: Path) -> Path:
        """Save dataset to pickle file."""
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        dataset.save_to_pickle(output_path)
        logger.info(f"Saved dataset {dataset_id} to {output_path}")
        return output_path

    def load_dataset(self, dataset_id: str, filepath: Path) -> BuildingDataset:
        """Load dataset from pickle file."""
        dataset = BuildingDataset.load_from_pickle(filepath)
        self.datasets[dataset_id] = dataset
        self.active_dataset_id = dataset_id
        logger.info(f"Loaded dataset {dataset_id} from {filepath}")
        return dataset

    # ========== Building Management ==========

    def create_building(
        self,
        dataset_id: str,
        name: str,
        building_id: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        postal_code: Optional[str] = None,
        **kwargs
    ) -> Building:
        """Create a new building in a dataset."""
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")

        if not building_id:
            building_id = f"building_{len(dataset.buildings) + 1}"

        building = Building(
            id=building_id,
            name=name,
            address=address,
            city=city,
            postal_code=postal_code,
            **kwargs
        )

        dataset.add_building(building)
        logger.info(f"Created building {building_id} in dataset {dataset_id}")
        return building

    def get_building(self, dataset_id: str, building_id: str) -> Optional[Building]:
        """Get a building by ID."""
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return None
        return dataset.get_building(building_id)

    def list_buildings(self, dataset_id: str) -> List[Dict[str, Any]]:
        """List all buildings in a dataset."""
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return []

        return [
            {
                "building_id": building.id,
                "name": building.name,
                "address": building.address,
                "city": building.city,
                "level_count": building.get_level_count(),
                "room_count": building.get_room_count()
            }
            for building in dataset.buildings
        ]

    def update_building(
        self,
        dataset_id: str,
        building_id: str,
        **updates
    ) -> Optional[Building]:
        """Update building properties."""
        building = self.get_building(dataset_id, building_id)
        if not building:
            return None

        for key, value in updates.items():
            if hasattr(building, key) and value is not None:
                setattr(building, key, value)

        logger.info(f"Updated building {building_id}")
        return building

    def delete_building(self, dataset_id: str, building_id: str) -> bool:
        """Delete a building from a dataset."""
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return False

        building = dataset.get_building(building_id)
        if building:
            dataset.buildings.remove(building)
            logger.info(f"Deleted building {building_id}")
            return True
        return False

    # ========== Level Management ==========

    def create_level(
        self,
        dataset_id: str,
        building_id: str,
        name: str,
        level_id: Optional[str] = None,
        floor_number: Optional[int] = None
    ) -> Level:
        """Create a new level in a building."""
        building = self.get_building(dataset_id, building_id)
        if not building:
            raise ValueError(f"Building not found: {building_id}")

        if not level_id:
            level_id = f"{building_id}_level_{len(building.levels) + 1}"

        level = Level(
            id=level_id,
            name=name,
            building_id=building_id,
            floor_number=floor_number
        )

        building.add_level(level)
        logger.info(f"Created level {level_id} in building {building_id}")
        return level

    def get_level(self, dataset_id: str, building_id: str, level_id: str) -> Optional[Level]:
        """Get a level by ID."""
        building = self.get_building(dataset_id, building_id)
        if not building:
            return None
        return building.get_level(level_id)

    def list_levels(self, dataset_id: str, building_id: str) -> List[Dict[str, Any]]:
        """List all levels in a building."""
        building = self.get_building(dataset_id, building_id)
        if not building:
            return []

        return [
            {
                "level_id": level.id,
                "name": level.name,
                "floor_number": level.floor_number,
                "room_count": level.get_room_count()
            }
            for level in building.levels
        ]

    def update_level(
        self,
        dataset_id: str,
        building_id: str,
        level_id: str,
        **updates
    ) -> Optional[Level]:
        """Update level properties."""
        level = self.get_level(dataset_id, building_id, level_id)
        if not level:
            return None

        for key, value in updates.items():
            if hasattr(level, key) and value is not None:
                setattr(level, key, value)

        logger.info(f"Updated level {level_id}")
        return level

    def delete_level(self, dataset_id: str, building_id: str, level_id: str) -> bool:
        """Delete a level from a building."""
        building = self.get_building(dataset_id, building_id)
        if not building:
            return False

        level = building.get_level(level_id)
        if level:
            building.levels.remove(level)
            # Also remove rooms that belong to this level
            building.rooms = [r for r in building.rooms if r.level_id != level_id]
            logger.info(f"Deleted level {level_id}")
            return True
        return False

    # ========== Room Management ==========

    def create_room(
        self,
        dataset_id: str,
        building_id: str,
        name: str,
        level_id: Optional[str] = None,
        room_id: Optional[str] = None,
        room_type: Optional[str] = None,
        **kwargs
    ) -> Room:
        """Create a new room in a building."""
        building = self.get_building(dataset_id, building_id)
        if not building:
            raise ValueError(f"Building not found: {building_id}")

        if not room_id:
            room_id = f"{building_id}_room_{len(building.rooms) + 1}"

        # Parse room type
        room_type_enum = None
        if room_type:
            try:
                room_type_enum = RoomType(room_type)
            except ValueError:
                logger.warning(f"Invalid room type: {room_type}")

        room = Room(
            id=room_id,
            name=name,
            building_id=building_id,
            level_id=level_id,
            room_type=room_type_enum,
            **kwargs
        )

        building.add_room(room, level_id)
        logger.info(f"Created room {room_id} in building {building_id}")
        return room

    def get_room(
        self,
        dataset_id: str,
        building_id: str,
        room_id: str
    ) -> Optional[Room]:
        """Get a room by ID."""
        building = self.get_building(dataset_id, building_id)
        if not building:
            return None
        return building.get_room(room_id)

    def list_rooms(
        self,
        dataset_id: str,
        building_id: str,
        level_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all rooms in a building or level."""
        building = self.get_building(dataset_id, building_id)
        if not building:
            return []

        rooms = building.rooms
        if level_id:
            rooms = [r for r in rooms if r.level_id == level_id]

        return [
            {
                "room_id": room.id,
                "name": room.name,
                "level_id": room.level_id,
                "room_type": room.room_type.value if room.room_type else None,
                "has_data": len(room.timeseries) > 0,
                "parameter_count": len(room.timeseries)
            }
            for room in rooms
        ]

    def update_room(
        self,
        dataset_id: str,
        building_id: str,
        room_id: str,
        **updates
    ) -> Optional[Room]:
        """Update room properties."""
        room = self.get_room(dataset_id, building_id, room_id)
        if not room:
            return None

        # Handle room_type conversion
        if 'room_type' in updates and updates['room_type']:
            try:
                updates['room_type'] = RoomType(updates['room_type'])
            except ValueError:
                logger.warning(f"Invalid room type: {updates['room_type']}")
                del updates['room_type']

        for key, value in updates.items():
            if hasattr(room, key) and value is not None:
                setattr(room, key, value)

        logger.info(f"Updated room {room_id}")
        return room

    def delete_room(self, dataset_id: str, building_id: str, room_id: str) -> bool:
        """Delete a room from a building."""
        building = self.get_building(dataset_id, building_id)
        if not building:
            return False

        room = building.get_room(room_id)
        if room:
            # Remove from building's flat list
            building.rooms.remove(room)

            # Remove from level if applicable
            if room.level_id:
                level = building.get_level(room.level_id)
                if level and room in level.rooms:
                    level.rooms.remove(room)

            logger.info(f"Deleted room {room_id}")
            return True
        return False

    # ========== CSV Upload Management ==========

    def upload_csv_to_room(
        self,
        dataset_id: str,
        building_id: str,
        room_id: str,
        csv_file_path: Path,
        timestamp_column: str = "timestamp",
        parameters: Optional[List[str]] = None,
        resample_freq: Optional[str] = "H"
    ) -> Dict[str, Any]:
        """
        Upload CSV data to a room.

        Args:
            dataset_id: Dataset identifier
            building_id: Building identifier
            room_id: Room identifier
            csv_file_path: Path to CSV file
            timestamp_column: Name of timestamp column
            parameters: List of parameter columns to load (None = all numeric)
            resample_freq: Resample frequency (e.g., 'H' for hourly)

        Returns:
            Dictionary with upload results
        """
        room = self.get_room(dataset_id, building_id, room_id)
        if not room:
            raise ValueError(f"Room not found: {room_id}")

        # Read CSV
        df = pd.read_csv(csv_file_path)

        # Parse timestamp
        if timestamp_column not in df.columns:
            raise ValueError(f"Timestamp column '{timestamp_column}' not found in CSV")

        df[timestamp_column] = pd.to_datetime(df[timestamp_column])
        df = df.set_index(timestamp_column)
        df = df.sort_index()

        # Determine parameters to load
        if parameters is None:
            parameters = df.select_dtypes(include=['number']).columns.tolist()

        # Resample if requested
        if resample_freq:
            df = df.resample(resample_freq).mean()

        # Create timeseries for each parameter
        results = {
            "room_id": room_id,
            "parameters_loaded": [],
            "data_period": {
                "start": df.index.min().isoformat(),
                "end": df.index.max().isoformat(),
                "total_points": len(df)
            }
        }

        for param in parameters:
            if param not in df.columns:
                logger.warning(f"Parameter '{param}' not found in CSV")
                continue

            # Create DataFrame with just this parameter
            param_df = df[[param]].copy()

            # Create TimeSeriesData
            ts = TimeSeriesData(
                parameter=param,
                data=param_df,
                source_file=str(csv_file_path),
                resolution=resample_freq or "unknown"
            )

            # Add to room
            room.add_timeseries(param, ts)
            room.source_files.append(str(csv_file_path))

            results["parameters_loaded"].append({
                "parameter": param,
                "completeness": ts.data_quality.completeness,
                "quality_score": ts.data_quality.quality_score,
                "total_points": len(param_df),
                "missing_points": ts.data_quality.missing_count
            })

        logger.info(f"Uploaded CSV to room {room_id}: {len(results['parameters_loaded'])} parameters")
        return results

    # ========== Hierarchy Visualization ==========

    def get_hierarchy_tree(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get complete hierarchy tree for visualization.

        Returns:
            Hierarchical tree structure with all buildings, levels, and rooms
        """
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return {"error": "Dataset not found"}

        tree = {
            "dataset_id": dataset_id,
            "name": dataset.metadata.get("name", "Unnamed Dataset"),
            "building_count": dataset.get_building_count(),
            "total_room_count": dataset.get_total_room_count(),
            "buildings": []
        }

        for building in dataset.buildings:
            building_node = {
                "building_id": building.id,
                "name": building.name,
                "address": building.address,
                "level_count": building.get_level_count(),
                "room_count": building.get_room_count(),
                "levels": []
            }

            for level in building.levels:
                level_node = {
                    "level_id": level.id,
                    "name": level.name,
                    "floor_number": level.floor_number,
                    "room_count": level.get_room_count(),
                    "rooms": []
                }

                for room in level.rooms:
                    room_node = {
                        "room_id": room.id,
                        "name": room.name,
                        "room_type": room.room_type.value if room.room_type else None,
                        "has_data": len(room.timeseries) > 0,
                        "parameters": list(room.timeseries.keys()),
                        "data_quality": room.get_overall_quality_score()
                    }
                    level_node["rooms"].append(room_node)

                building_node["levels"].append(level_node)

            # Add rooms without levels
            rooms_without_level = [r for r in building.rooms if not r.level_id]
            if rooms_without_level:
                unassigned_level = {
                    "level_id": "unassigned",
                    "name": "Unassigned Rooms",
                    "floor_number": None,
                    "room_count": len(rooms_without_level),
                    "rooms": [
                        {
                            "room_id": room.id,
                            "name": room.name,
                            "room_type": room.room_type.value if room.room_type else None,
                            "has_data": len(room.timeseries) > 0,
                            "parameters": list(room.timeseries.keys()),
                            "data_quality": room.get_overall_quality_score()
                        }
                        for room in rooms_without_level
                    ]
                }
                building_node["levels"].append(unassigned_level)

            tree["buildings"].append(building_node)

        return tree


# Global service instance
_service_instance: Optional[BuildingManagementService] = None


def get_building_management_service() -> BuildingManagementService:
    """Get or create the global building management service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = BuildingManagementService()
    return _service_instance
