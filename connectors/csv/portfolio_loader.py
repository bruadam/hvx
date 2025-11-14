"""
Portfolio CSV Data Loader

Loads hierarchical building portfolios from nested CSV file structures.
Supports the data folder structure with buildings, floors, and rooms.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any, Iterator
from pathlib import Path
from datetime import datetime
import json
import sys
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spacial_entity import SpatialEntity
from core.entities import Room, Building, Floor, Portfolio
from core.enums import SpatialEntityType
from core.metering import (
    MeteringPoint,
    TimeSeries,
    MetricType,
    PointType,
    TimeSeriesType,
    SensorDefinition,
    SensorSourceType,
)

from .data_loader import CSVDataLoader


@dataclass
class PortfolioLoadResult:
    entities: Dict[str, SpatialEntity]
    metering_points: Dict[str, MeteringPoint]
    timeseries: Dict[str, TimeSeries]
    portfolio: Optional[Portfolio]
    buildings: Dict[str, Building]
    floors: Dict[str, Floor]
    rooms: Dict[str, Room]

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        yield self.entities
        yield self.metering_points
        yield self.timeseries


class PortfolioLoader:
    """
    Loads building portfolios from hierarchical folder structures.
    
    Supports multiple data folder patterns:
    1. hoeje-taastrup: building-X/sensors/room.csv + building-X/climate/climate.csv
    2. dummy_data: building_X/level_Y/room.csv + building_X/climate_data.csv + metadata.json
    3. Simple: building_sample.csv (single file)
    """

    def __init__(self):
        """Initialize portfolio loader."""
        self.loader = CSVDataLoader()
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset cached state before loading a new dataset."""
        self.portfolio: Optional[Portfolio] = None
        self.buildings: Dict[str, Building] = {}
        self.floors: Dict[str, Floor] = {}
        self.rooms: Dict[str, Room] = {}

    def load_portfolio(
        self,
        data_path: Path | str,
        auto_detect: bool = True
    ) -> PortfolioLoadResult:
        """
        Load portfolio from data folder.
        
        Auto-detects the folder structure and loads accordingly.
        
        Args:
            data_path: Path to data folder
            auto_detect: Auto-detect folder structure
            
        Returns:
            Tuple of (entities dict, metering points dict, timeseries dict)
        """
        data_path = Path(data_path)
        
        if not data_path.exists():
            raise ValueError(f"Data path does not exist: {data_path}")
        
        # Detect structure
        self._reset_state()

        if auto_detect:
            structure_type = self._detect_structure(data_path)
        else:
            structure_type = "unknown"
        
        print(f"Detected structure type: {structure_type}")
        
        # Load based on structure
        if structure_type == "hoeje-taastrup":
            return self._wrap_legacy_result(self._load_hoeje_taastrup(data_path))
        elif structure_type == "dummy_data":
            return self._load_dummy_data(data_path)
        elif structure_type == "simple":
            return self._wrap_legacy_result(self._load_simple(data_path))
        else:
            # Try to auto-detect and load
            return self._wrap_legacy_result(self._load_generic(data_path))

    def _detect_structure(self, data_path: Path) -> str:
        """Detect the folder structure type."""
        # Check for hoeje-taastrup pattern
        building_dirs = list(data_path.glob("building-*"))
        if building_dirs:
            if any((bd / "sensors").exists() for bd in building_dirs):
                return "hoeje-taastrup"
        
        # Check for dummy_data pattern
        building_dirs = list(data_path.glob("building_*"))
        if building_dirs:
            if any((bd / "metadata.json").exists() for bd in building_dirs):
                return "dummy_data"
        
        # Check for simple CSV files
        csv_files = list(data_path.glob("*.csv"))
        if csv_files:
            return "simple"
        
        return "unknown"

    def _load_hoeje_taastrup(
        self, 
        data_path: Path
    ) -> Tuple[Dict[str, SpatialEntity], Dict[str, MeteringPoint], Dict[str, TimeSeries]]:
        """
        Load hoeje-taastrup structure.
        
        Structure:
        - building-X/
          - sensors/
            - room_name.csv (DateTime,Temperatur,Fugtighed,CO2,Lys,Tilstedeværelse)
          - climate/
            - climate.csv
        """
        all_entities = {}
        all_points = {}
        all_ts = {}
        portfolio_name = data_path.name.replace("_", " ").title()
        self.portfolio = Portfolio(
            id=f"{data_path.name}_portfolio",
            name=portfolio_name,
            type=SpatialEntityType.PORTFOLIO,
        )
        
        # Find all building directories
        building_dirs = sorted(data_path.glob("building-*"))
        
        for building_dir in building_dirs:
            building_id = building_dir.name
            
            # Create building entity
            building = Building(
                id=building_id,
                name=building_id.replace("-", " ").title(),
                type=SpatialEntityType.BUILDING,
            )
            all_entities[building.id] = building
            self.buildings[building.id] = building
            
            # Load climate data if available
            climate_dir = building_dir / "climate"
            if climate_dir.exists():
                climate_files = list(climate_dir.glob("*.csv"))
                if climate_files:
                    # Load climate data as building-level metrics
                    entity, points, ts = self.loader.load_wide_format(
                        climate_files[0],
                        spatial_entity_id=f"{building_id}_climate",
                        spatial_entity_name=f"{building.name} Climate",
                        entity_type=SpatialEntityType.BUILDING,
                        timestamp_column="DateTime",
                        metric_columns={
                            "Temperatur": "outdoor_temperature",
                            "Fugtighed": "outdoor_humidity",
                        }
                    )
                    all_entities.update({entity.id: entity})
                    all_points.update(points)
                    all_ts.update(ts)
            
            # Load sensor/room data
            sensors_dir = building_dir / "sensors"
            if sensors_dir.exists():
                sensor_files = sorted(sensors_dir.glob("*.csv"))
                
                for sensor_file in sensor_files:
                    room_name = sensor_file.stem
                    room_id = f"{building_id}_{room_name}"
                    
                    # Load room data with Danish column names
                    try:
                        entity, points, ts = self.loader.load_wide_format(
                            sensor_file,
                            spatial_entity_id=room_id,
                            spatial_entity_name=room_name,
                            entity_type=SpatialEntityType.ROOM,
                            timestamp_column="DateTime",
                            metric_columns={
                                "Temperatur": "temperature",
                                "Fugtighed": "humidity",
                                "CO2": "co2",
                                "Lys": "illuminance",
                                "Tilstedeværelse": "occupancy",
                            },
                            building_id=building.id,
                        )
                        
                        all_entities[entity.id] = entity
                        all_points.update(points)
                        all_ts.update(ts)
                        if isinstance(entity, Room):
                            self.rooms[entity.id] = entity
                        
                    except Exception as e:
                        print(f"Warning: Failed to load {sensor_file}: {e}")
                        continue
        self._attach_room_sensors(all_entities, all_points, all_ts)

        return PortfolioLoadResult(
            entities=all_entities,
            metering_points=all_points,
            timeseries=all_ts,
            portfolio=self.portfolio,
            buildings=self.buildings,
            floors=self.floors,
            rooms=self.rooms,
        )

    def _load_dummy_data(
        self, 
        data_path: Path
    ) -> Tuple[Dict[str, SpatialEntity], Dict[str, MeteringPoint], Dict[str, TimeSeries]]:
        """
        Load dummy_data structure.
        
        Structure:
        - building_X/
          - metadata.json
          - climate_data.csv
          - energy_data.csv
          - level_Y/
            - room_name.csv (timestamp,temperature,co2,humidity)
        """
        all_entities = {}
        all_points = {}
        all_ts = {}
        
        # Find all building directories
        building_dirs = sorted(data_path.glob("building_*"))
        
        for building_dir in building_dirs:
            building_id = building_dir.name
            
            # Load metadata if available
            metadata_file = building_dir / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Create building entity
            building = Building(
                id=building_id,
                name=metadata.get("name", building_id.replace("_", " ").title()),
                type=SpatialEntityType.BUILDING,
            )
            self._apply_building_metadata(building, metadata)
            all_entities[building.id] = building
            self.buildings[building.id] = building
            if self.portfolio:
                self.portfolio.add_building(building.id)
                if self.portfolio.id not in building.parent_ids:
                    building.parent_ids.append(self.portfolio.id)
            
            # Load climate data
            climate_file = building_dir / "climate_data.csv"
            if climate_file.exists():
                try:
                    entity, points, ts = self.loader.load_wide_format(
                        climate_file,
                        spatial_entity_id=f"{building_id}_climate",
                        spatial_entity_name=f"{building.name} Climate",
                        entity_type=SpatialEntityType.BUILDING,
                        timestamp_column="timestamp",
                    )
                    new_points, new_ts = self._attach_building_dataset(
                        building,
                        points,
                        ts,
                        dataset_key="climate",
                        source_file=str(climate_file),
                    )
                    all_points.update(new_points)
                    all_ts.update(new_ts)
                except Exception as e:
                    print(f"Warning: Failed to load climate data: {e}")
            
            # Load energy data
            energy_file = building_dir / "energy_data.csv"
            if energy_file.exists():
                try:
                    entity, points, ts = self.loader.load_wide_format(
                        energy_file,
                        spatial_entity_id=f"{building_id}_energy",
                        spatial_entity_name=f"{building.name} Energy",
                        entity_type=SpatialEntityType.BUILDING,
                        timestamp_column="timestamp",
                    )
                    new_points, new_ts = self._attach_building_dataset(
                        building,
                        points,
                        ts,
                        dataset_key="energy",
                        source_file=str(energy_file),
                    )
                    all_points.update(new_points)
                    all_ts.update(new_ts)
                except Exception as e:
                    print(f"Warning: Failed to load energy data: {e}")
            
            # Load floor/level data
            level_dirs = sorted(building_dir.glob("level_*"))
            
            for level_dir in level_dirs:
                floor_id = f"{building_id}_{level_dir.name}"
                
                # Create floor entity
                floor = Floor(
                    id=floor_id,
                    name=level_dir.name.replace("_", " ").title(),
                    type=SpatialEntityType.FLOOR,
                    building_id=building.id,
                )
                all_entities[floor.id] = floor
                self.floors[floor.id] = floor
                if floor.building_id and floor.building_id in self.buildings:
                    parent_building = self.buildings[floor.building_id]
                    parent_building.add_floor(floor.id)
                    if floor.building_id not in floor.parent_ids:
                        floor.parent_ids.append(floor.building_id)
                
                # Load room data
                room_files = sorted(level_dir.glob("*.csv"))
                
                for room_file in room_files:
                    room_name = room_file.stem
                    room_id = f"{floor_id}_{room_name}"
                    
                    try:
                        entity, points, ts = self.loader.load_wide_format(
                            room_file,
                            spatial_entity_id=room_id,
                            spatial_entity_name=room_name.replace("_", " ").title(),
                            entity_type=SpatialEntityType.ROOM,
                            timestamp_column="timestamp",
                            floor_id=floor.id,
                            building_id=building.id,
                        )
                        
                        all_entities[entity.id] = entity
                        all_points.update(points)
                        all_ts.update(ts)
                        if isinstance(entity, Room):
                            self.rooms[entity.id] = entity
                            self._link_room(entity)
                        
                    except Exception as e:
                        print(f"Warning: Failed to load {room_file}: {e}")
                        continue
        
        # Attach sensors and timeseries data to rooms
        self._attach_room_sensors(all_entities, all_points, all_ts)
        
        return all_entities, all_points, all_ts

    def _apply_building_metadata(self, building: Building, metadata: Dict[str, Any]) -> None:
        """Map metadata fields onto explicit building properties."""
        if not metadata:
            return

        field_mapping = {
            "type": "building_type",
            "building_type": "building_type",
            "address": "address",
            "city": "city",
            "country": "country",
            "latitude": "latitude",
            "longitude": "longitude",
            "year_built": "year_built",
            "area_m2": "area_m2",
            "volume_m3": "volume_m3",
        }

        used_keys = set()
        for meta_key, attr_name in field_mapping.items():
            if meta_key in metadata and hasattr(building, attr_name):
                setattr(building, attr_name, metadata[meta_key])
                used_keys.add(meta_key)

        remaining = {
            k: v for k, v in metadata.items()
            if k not in used_keys and k != "name"
        }
        if remaining:
            building.metadata.update(remaining)

    def _link_room(self, room: Room) -> None:
        """Ensure room hierarchy relationships are established."""
        if room.floor_id and room.floor_id in self.floors:
            floor = self.floors[room.floor_id]
            floor.add_room(room.id)
            if room.floor_id not in room.parent_ids:
                room.parent_ids.append(room.floor_id)
        if room.building_id and room.building_id in self.buildings:
            building = self.buildings[room.building_id]
            building.add_room(room.id)
            if room.building_id not in room.parent_ids:
                room.parent_ids.append(room.building_id)

    def _attach_room_sensors(
        self,
        entities: Dict[str, SpatialEntity],
        metering_points: Dict[str, MeteringPoint],
        timeseries: Dict[str, TimeSeries],
    ) -> None:
        """Attach room-level sensors/time series directly to Room objects."""
        for point in metering_points.values():
            target = entities.get(point.spatial_entity_id)
            if not isinstance(target, Room):
                continue

            ts_objects = [timeseries[ts_id] for ts_id in point.timeseries_ids if ts_id in timeseries]
            if not ts_objects:
                continue

            csv_file = ts_objects[0].metadata.get("csv_file")
            sensor = SensorDefinition(
                id=f"sensor::{point.id}",
                spatial_entity_id=target.id,
                metric=point.metric,
                parameter=point.metric.value or point.parameter or point.id,
                unit=point.unit or "",
                name=point.name,
                metadata={"source_point_id": point.id},
            )
            source_kwargs = {"file": csv_file} if csv_file else {}
            target.load_sensor(sensor, source_type=SensorSourceType.CSV, **source_kwargs)

            for ts in ts_objects:
                timestamps = ts.metadata.get("timestamps", [])
                values = ts.metadata.get("values", [])
                if not timestamps or not values:
                    continue

                csv_column = ts.metadata.get("csv_column") or point.metric.value
                sensor.metadata.setdefault("timeseries", {})[ts.id] = {
                    "timestamps": timestamps,
                    "values": values,
                    "point_id": point.id,
                    "timeseries_id": ts.id,
                    "label": csv_column,
                }
                target.add_timeseries(csv_column, values, timestamps)

    def _attach_building_dataset(
        self,
        building: Building,
        dataset_points: Dict[str, MeteringPoint],
        dataset_timeseries: Dict[str, TimeSeries],
        dataset_key: str,
        source_file: Optional[str] = None,
    ) -> Tuple[Dict[str, MeteringPoint], Dict[str, TimeSeries]]:
        """
        Attach a building-level dataset (climate/energy) as sensor groups on the building.
        """
        registered_points: Dict[str, MeteringPoint] = {}
        registered_ts: Dict[str, TimeSeries] = {}

        bucket_name = f"{dataset_key}_timeseries"
        bucket = building.metadata.setdefault(bucket_name, {})

        for point in dataset_points.values():
            metric_key = point.metric.value or point.parameter or point.id
            metric_key = metric_key.replace(" ", "_").lower()
            point_id = f"{building.id}_{dataset_key}_{metric_key}"
            point_name = f"{building.name} {metric_key.replace('_', ' ').title()} ({dataset_key})"

            new_point = MeteringPoint(
                id=point_id,
                name=point_name,
                type=point.type,
                spatial_entity_id=building.id,
                metric=point.metric,
                unit=point.unit,
                timezone=point.timezone,
                sensor_id=None,
                parameter=metric_key,
                timeseries_ids=[],
                metadata={
                    **point.metadata,
                    "dataset": dataset_key,
                    "source_file": source_file or point.metadata.get("csv_file"),
                },
            )
            registered_points[point_id] = new_point

            sensor = SensorDefinition(
                id=f"sensor::{point_id}",
                spatial_entity_id=building.id,
                metric=point.metric,
                parameter=metric_key,
                unit=point.unit or "",
                name=point_name,
                metadata={"dataset": dataset_key},
            )
            building.load_sensor(sensor, source_type=SensorSourceType.CSV, dataset=dataset_key)

            for idx, original_ts_id in enumerate(point.timeseries_ids):
                src_ts = dataset_timeseries.get(original_ts_id)
                if src_ts is None:
                    continue

                suffix = f"_ts{idx}" if idx else "_ts"
                ts_id = f"{point_id}{suffix}"
                new_ts = TimeSeries(
                    id=ts_id,
                    point_id=point_id,
                    type=src_ts.type,
                    metric=src_ts.metric,
                    unit=src_ts.unit,
                    start=src_ts.start,
                    end=src_ts.end,
                    granularity_seconds=src_ts.granularity_seconds,
                    source=src_ts.source,
                    metadata={
                        **src_ts.metadata,
                        "dataset": dataset_key,
                        "source_file": source_file or src_ts.metadata.get("csv_file"),
                    },
                )
                registered_ts[ts_id] = new_ts
                new_point.timeseries_ids.append(ts_id)

                bucket[metric_key] = {
                    "timestamps": new_ts.metadata.get("timestamps", []),
                    "values": new_ts.metadata.get("values", []),
                    "point_id": point_id,
                    "timeseries_id": ts_id,
                    "source_file": source_file or new_ts.metadata.get("csv_file"),
                }

        return registered_points, registered_ts

    def _load_simple(
        self, 
        data_path: Path
    ) -> Tuple[Dict[str, SpatialEntity], Dict[str, MeteringPoint], Dict[str, TimeSeries]]:
        """
        Load simple CSV files.
        
        Each CSV file represents a room or building.
        """
        all_entities = {}
        all_points = {}
        all_ts = {}
        
        csv_files = sorted(data_path.glob("*.csv"))
        
        for csv_file in csv_files:
            entity_id = csv_file.stem
            
            try:
                entity, points, ts = self.loader.load_wide_format(
                    csv_file,
                    spatial_entity_id=entity_id,
                    spatial_entity_name=entity_id.replace("_", " ").title(),
                    entity_type=SpatialEntityType.ROOM,
                    timestamp_column="timestamp",
                )
                
                all_entities[entity.id] = entity
                all_points.update(points)
                all_ts.update(ts)
                
            except Exception as e:
                print(f"Warning: Failed to load {csv_file}: {e}")
                continue
        
        return all_entities, all_points, all_ts

    def _wrap_legacy_result(
        self,
        legacy_tuple: Tuple[Dict[str, SpatialEntity], Dict[str, MeteringPoint], Dict[str, TimeSeries]],
    ) -> PortfolioLoadResult:
        entities, points, ts = legacy_tuple
        return PortfolioLoadResult(
            entities=entities,
            metering_points=points,
            timeseries=ts,
            portfolio=self.portfolio,
            buildings=self.buildings,
            floors=self.floors,
            rooms=self.rooms,
        )
    def _load_generic(
        self, 
        data_path: Path
    ) -> Tuple[Dict[str, SpatialEntity], Dict[str, MeteringPoint], Dict[str, TimeSeries]]:
        """
        Generic loader - tries to load any CSV files found.
        """
        all_entities = {}
        all_points = {}
        all_ts = {}
        
        # Find all CSV files recursively
        csv_files = sorted(data_path.rglob("*.csv"))
        
        for csv_file in csv_files:
            # Generate entity ID from relative path
            rel_path = csv_file.relative_to(data_path)
            entity_id = str(rel_path.with_suffix("")).replace("/", "_").replace("-", "_")
            
            try:
                entity, points, ts = self.loader.load_wide_format(
                    csv_file,
                    spatial_entity_id=entity_id,
                    spatial_entity_name=csv_file.stem.replace("_", " ").title(),
                    entity_type=SpatialEntityType.ROOM,
                    timestamp_column="timestamp",  # Try common names
                )
                
                all_entities[entity.id] = entity
                all_points.update(points)
                all_ts.update(ts)
                
            except Exception:
                # Try alternative timestamp column
                try:
                    entity, points, ts = self.loader.load_wide_format(
                        csv_file,
                        spatial_entity_id=entity_id,
                        spatial_entity_name=csv_file.stem.replace("_", " ").title(),
                        entity_type=SpatialEntityType.ROOM,
                        timestamp_column="DateTime",
                    )
                    
                    all_entities[entity.id] = entity
                    all_points.update(points)
                    all_ts.update(ts)
                    
                except Exception as e:
                    print(f"Warning: Failed to load {csv_file}: {e}")
                    continue
        
        return all_entities, all_points, all_ts

    def get_building_hierarchy(self, building_id: str) -> Dict[str, Any]:
        """
        Get complete hierarchy for a building.
        
        Args:
            building_id: Building ID
            
        Returns:
            Dict with building, floors, and rooms
        """
        if building_id not in self.buildings:
            return {}
        
        building = self.buildings[building_id]
        
        # Find floors
        building_floors = {
            fid: floor for fid, floor in self.floors.items()
            if getattr(floor, 'building_id', None) == building_id
        }
        
        # Find rooms
        building_rooms = {
            rid: room for rid, room in self.rooms.items()
            if getattr(room, 'building_id', None) == building_id
            or any(getattr(room, 'floor_id', None) == fid for fid in building_floors)
        }
        
        return {
            'building': building,
            'floors': building_floors,
            'rooms': building_rooms,
        }


# Convenience functions

def load_portfolio(
    data_path: Path | str,
    auto_detect: bool = True
) -> PortfolioLoadResult:
    """
    Load portfolio from data folder.
    
    Args:
        data_path: Path to data folder
        auto_detect: Auto-detect folder structure
        
    Returns:
        Tuple of (entities dict, metering points dict, timeseries dict)
    """
    loader = PortfolioLoader()
    return loader.load_portfolio(data_path, auto_detect)


def load_hoeje_taastrup(
    data_path: Path | str
) -> PortfolioLoadResult:
    """Load hoeje-taastrup data structure."""
    loader = PortfolioLoader()
    return loader._wrap_legacy_result(loader._load_hoeje_taastrup(Path(data_path)))


def load_dummy_data(
    data_path: Path | str
) -> PortfolioLoadResult:
    """Load dummy_data structure."""
    loader = PortfolioLoader()
    return loader._wrap_legacy_result(loader._load_dummy_data(Path(data_path)))


if __name__ == "__main__":
    # Example usage
    print("Portfolio CSV Loader")
    print("=" * 60)
    print("\nUsage:")
    print("  from ingestion.csv import load_portfolio")
    print("  entities, points, ts = load_portfolio('data/samples/hoeje-taastrup')")
    print("\nSupported structures:")
    print("  - hoeje-taastrup: building-X/sensors/*.csv + climate/*.csv")
    print("  - dummy_data: building_X/level_Y/*.csv + metadata.json")
    print("  - simple: *.csv files")
