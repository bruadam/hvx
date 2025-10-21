"""Dataset builder for loading complete building hierarchies."""

from pathlib import Path
from typing import List, Dict, Optional, Any
import json

from core.domain.models.room import Room
from core.domain.models.level import Level
from core.domain.models.building import Building
from core.domain.models.dataset import Dataset
from core.domain.enums.building_type import BuildingType
from core.infrastructure.data_loaders.csv_loader import CSVDataLoader
from core.infrastructure.data_loaders.excel_loader import ExcelDataLoader


class DatasetBuilder:
    """
    Build complete dataset hierarchies from directory structures.

    Expected directory structure:
    data_root/
        building1/
            metadata.json (optional)
            level1/
                room1.csv
                room2.csv
            level2/
                room3.csv
        building2/
            ...
    """

    def __init__(self):
        """Initialize dataset builder."""
        self.csv_loader = CSVDataLoader()
        self.excel_loader = ExcelDataLoader()

    def build_from_directory(
        self,
        root_dir: Path,
        dataset_id: str = "dataset_001",
        dataset_name: str = "IEQ Dataset",
    ) -> tuple[Dataset, Dict[str, Building], Dict[str, Level], Dict[str, Room]]:
        """
        Build complete dataset from directory structure.

        Args:
            root_dir: Root directory containing building folders
            dataset_id: Dataset identifier
            dataset_name: Dataset name

        Returns:
            Tuple of (Dataset, buildings_dict, levels_dict, rooms_dict)
        """
        if not root_dir.exists():
            raise FileNotFoundError(f"Root directory not found: {root_dir}")

        # Initialize collections
        buildings: Dict[str, Building] = {}
        levels: Dict[str, Level] = {}
        rooms: Dict[str, Room] = {}

        # Scan for building directories
        for building_dir in root_dir.iterdir():
            if not building_dir.is_dir():
                continue

            building_id = building_dir.name
            print(f"Loading building: {building_id}")

            # Load building metadata if available
            metadata = self._load_building_metadata(building_dir)

            # Map building type (handle variations)
            building_type_str = metadata.get("type", "office")
            building_type_map = {
                "education": "school",
                "educational": "school",
                "commercial": "office",
                "healthcare": "hospital",
            }
            building_type_str = building_type_map.get(building_type_str, building_type_str)
            
            # Get building type, default to OTHER if invalid
            try:
                building_type = BuildingType(building_type_str)
            except ValueError:
                building_type = BuildingType.OTHER

            # Create building
            building = Building(
                id=building_id,
                name=metadata.get("name", building_id),
                building_type=building_type,
                address=metadata.get("address"),
                city=metadata.get("city"),
                country=metadata.get("country"),
            )

            # Scan for level directories
            level_count = 0
            for level_dir in building_dir.iterdir():
                if not level_dir.is_dir():
                    continue

                level_id = f"{building_id}_{level_dir.name}"
                level_count += 1

                print(f"  Loading level: {level_dir.name}")

                # Create level
                level = Level(
                    id=level_id,
                    name=level_dir.name,
                    building_id=building_id,
                    floor_number=self._extract_floor_number(level_dir.name, level_count),
                )

                # Load rooms from CSV files in level
                room_files = list(level_dir.glob("*.csv"))
                for room_file in room_files:
                    room_id = f"{building_id}_{level_dir.name}_{room_file.stem}"

                    print(f"    Loading room: {room_file.stem}")

                    try:
                        room = self.csv_loader.load_room(
                            file_path=room_file,
                            room_id=room_id,
                            room_name=room_file.stem.replace("_", " ").title(),
                            level_id=level_id,
                            building_id=building_id,
                        )

                        rooms[room_id] = room
                        level.add_room(room_id)

                    except Exception as e:
                        print(f"      Warning: Failed to load {room_file.name}: {e}")

                # Add level to collections
                if level.room_count > 0:
                    levels[level_id] = level
                    building.add_level(level_id)

            # Add building to collection
            if building.level_count > 0:
                buildings[building_id] = building

        # Create dataset
        dataset = Dataset(
            id=dataset_id,
            name=dataset_name,
            source_directory=root_dir,
            building_ids=[b.id for b in buildings.values()],
        )

        print(f"\nDataset loaded:")
        print(f"  Buildings: {len(buildings)}")
        print(f"  Levels: {len(levels)}")
        print(f"  Rooms: {len(rooms)}")

        return dataset, buildings, levels, rooms

    def build_from_excel(
        self,
        excel_file: Path,
        building_id: str,
        building_name: str,
        dataset_id: str = "dataset_001",
        dataset_name: str = "IEQ Dataset",
    ) -> tuple[Dataset, Dict[str, Building], Dict[str, Level], Dict[str, Room]]:
        """
        Build dataset from single Excel file with multiple sheets.

        Args:
            excel_file: Path to Excel file
            building_id: Building identifier
            building_name: Building name
            dataset_id: Dataset identifier
            dataset_name: Dataset name

        Returns:
            Tuple of (Dataset, buildings_dict, levels_dict, rooms_dict)
        """
        print(f"Loading Excel file: {excel_file}")

        # Create single building
        building = Building(
            id=building_id,
            name=building_name,
            building_type=BuildingType.OFFICE,
        )

        # Create single level
        level_id = f"{building_id}_L001"
        level = Level(
            id=level_id,
            name="Level 1",
            building_id=building_id,
            floor_number=1,
        )

        # Load all sheets as rooms
        rooms_list = self.excel_loader.load_all_sheets(
            file_path=excel_file,
            building_id=building_id,
            level_id=level_id,
        )

        # Create collections
        rooms = {r.id: r for r in rooms_list}

        for room in rooms_list:
            level.add_room(room.id)

        building.add_level(level_id)

        # Create dataset
        dataset = Dataset(
            id=dataset_id,
            name=dataset_name,
            source_directory=excel_file.parent,
            building_ids=[building_id],
        )

        print(f"\nDataset loaded from Excel:")
        print(f"  Buildings: 1")
        print(f"  Levels: 1")
        print(f"  Rooms: {len(rooms)}")

        return dataset, {building_id: building}, {level_id: level}, rooms

    def _load_building_metadata(self, building_dir: Path) -> Dict[str, Any]:
        """Load building metadata from JSON file if available."""
        metadata_file = building_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load metadata from {metadata_file}: {e}")

        return {}

    def _extract_floor_number(self, level_name: str, default: int) -> int:
        """Extract floor number from level name."""
        # Try to extract number from name
        import re

        match = re.search(r"(\d+)", level_name)
        if match:
            return int(match.group(1))

        # Check for common patterns
        if "ground" in level_name.lower() or "g" == level_name.lower():
            return 0
        elif "basement" in level_name.lower() or "b" in level_name.lower():
            return -1

        return default
