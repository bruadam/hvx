"""
Data Loader Service for building hierarchy and timeseries data.

Scans folder structures, identifies buildings/levels/rooms from naming patterns,
and loads sensor and climate data into hierarchical data models.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import pandas as pd
import numpy as np

from src.models.building_data import (
    Building, Level, Room, ClimateData, TimeSeriesData, 
    BuildingDataset, DataQuality
)
from src.models.enums import RoomType, IEQParameter, DEFAULT_COLUMN_MAPPINGS, ROOM_TYPE_PATTERNS

logger = logging.getLogger(__name__)


class DataLoaderService:
    """Service for loading building data from folder structures."""
    
    def __init__(self, auto_infer_levels: bool = True, auto_infer_room_types: bool = True):
        """
        Initialize the data loader service.
        
        Args:
            auto_infer_levels: Automatically infer building levels from room names
            auto_infer_room_types: Automatically infer room types from names
        """
        self.auto_infer_levels = auto_infer_levels
        self.auto_infer_room_types = auto_infer_room_types
        
        # Column mapping cache
        self.column_mappings = DEFAULT_COLUMN_MAPPINGS.copy()
    
    def load_from_directory(self, data_dir: Path, validate: bool = True) -> BuildingDataset:
        """
        Load building data from a directory structure.
        
        Expected structure:
        data_dir/
            building-1/
                climate/
                    climate-data.csv
                sensors/
                    room1.csv
                    room2.csv
            building-2/
                ...
        
        Args:
            data_dir: Root directory containing building folders
            validate: Whether to validate data quality
        
        Returns:
            BuildingDataset with all loaded buildings
        """
        logger.info(f"Loading data from directory: {data_dir}")
        
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        dataset = BuildingDataset(source_directory=str(data_dir))
        
        # Find all building directories
        building_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
        
        if not building_dirs:
            logger.warning(f"No building directories found in {data_dir}")
            return dataset
        
        logger.info(f"Found {len(building_dirs)} building directories")
        
        # Load each building
        for building_dir in building_dirs:
            try:
                building = self._load_building(building_dir, validate=validate)
                if building:
                    dataset.add_building(building)
                    logger.info(f"Loaded building: {building.name} ({building.get_room_count()} rooms)")
            except Exception as e:
                logger.error(f"Error loading building from {building_dir}: {e}")
                continue
        
        logger.info(f"Dataset loaded: {dataset.get_building_count()} buildings, "
                   f"{dataset.get_total_room_count()} total rooms")
        
        return dataset
    
    def _load_building(self, building_dir: Path, validate: bool = True) -> Optional[Building]:
        """Load a single building from its directory."""
        building_name = building_dir.name
        building_id = self._sanitize_id(building_name)
        
        logger.info(f"Loading building: {building_name} from {building_dir}")
        
        building = Building(
            id=building_id,
            name=building_name.replace('-', ' ').replace('_', ' ').title(),
            address=None,
            city=None,
            postal_code=None,
            construction_year=None,
            total_area_m2=None,
            source_directory=str(building_dir),
            climate_data=None
        )
        
        # Load climate data if available
        climate_dir = building_dir / "climate"
        if climate_dir.exists():
            climate_data = self._load_climate_data(building_id, climate_dir)
            if climate_data:
                building.set_climate_data(climate_data)
                logger.info(f"Loaded climate data with {len(climate_data.timeseries)} parameters")
        
        # Load sensor data from rooms
        sensors_dir = building_dir / "sensors"
        if sensors_dir.exists():
            rooms = self._load_rooms(building_id, sensors_dir)
            
            for room in rooms:
                # Infer level if enabled
                if self.auto_infer_levels:
                    level_id = self._infer_level_from_room(room)
                    if level_id:
                        level = building.get_level(level_id)
                        if not level:
                            # Extract floor_number from level_id (e.g., "level_1" -> 1)
                            match = re.match(r'level_(-?\d+)', level_id)
                            floor_number = int(match.group(1)) if match else None
                            level = Level(
                                id=level_id,
                                name=self._format_level_name(level_id),
                                building_id=building_id,
                                floor_number=floor_number
                            )
                            building.add_level(level)
                        
                        building.add_room(room, level_id=level_id)
                    else:
                        building.add_room(room)
                else:
                    building.add_room(room)
            
            logger.info(f"Loaded {len(rooms)} rooms for building {building_name}")
        else:
            logger.warning(f"No sensors directory found for building {building_name}")
        
        # Validate if requested
        if validate and building.rooms:
            self._validate_building_data(building)
        
        return building if building.rooms or building.climate_data else None
    
    def _load_climate_data(self, building_id: str, climate_dir: Path) -> Optional[ClimateData]:
        """Load climate data from climate directory."""
        climate_files = list(climate_dir.glob("*.csv"))
        
        if not climate_files:
            logger.warning(f"No climate data files found in {climate_dir}")
            return None
        
        # Use the first climate file found
        climate_file = climate_files[0]
        
        try:
            df = pd.read_csv(climate_file)
            
            # Parse timestamp column
            timestamp_col = self._find_timestamp_column(list(df.columns))
            if not timestamp_col:
                logger.error(f"No timestamp column found in {climate_file}")
                return None
            
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            df = df.set_index(timestamp_col)
            df.index.name = 'timestamp'
            
            climate_data = ClimateData(
                building_id=building_id,
                source_file=str(climate_file),
                period_start=df.index.min(),
                period_end=df.index.max()
            )
            
            # Create timeseries for each climate parameter
            climate_params = {
                'temperature': ['mean_temp', 'temp', 'temperature', 'outdoor_temp'],
                'humidity': ['mean_relative_hum', 'humidity', 'rh', 'relative_humidity'],
                'precipitation': ['acc_precip', 'precip', 'precipitation', 'rain'],
                'wind_speed': ['mean_wind_speed', 'wind_speed', 'wind'],
                'radiation': ['mean_radiation', 'radiation', 'solar_radiation'],
                'sunshine': ['bright_sunshine', 'sunshine', 'sun_hours']
            }
            
            for param_name, possible_cols in climate_params.items():
                col = self._find_column(list(df.columns), possible_cols)
                if col:
                    ts_data = TimeSeriesData(
                        parameter=param_name,
                        unit=self._infer_unit(param_name),
                        data=df[[col]].rename(columns={col: param_name}),
                        source_file=str(climate_file),
                        period_start=df.index.min(),
                        period_end=df.index.max()
                    )
                    climate_data.add_timeseries(param_name, ts_data)
            
            return climate_data
            
        except Exception as e:
            logger.error(f"Error loading climate data from {climate_file}: {e}")
            return None
    
    def _load_rooms(self, building_id: str, sensors_dir: Path) -> List[Room]:
        """Load all rooms from sensors directory."""
        rooms = []
        sensor_files = list(sensors_dir.glob("*.csv"))
        
        if not sensor_files:
            logger.warning(f"No sensor files found in {sensors_dir}")
            return rooms
        
        logger.info(f"Found {len(sensor_files)} sensor files")
        
        for sensor_file in sensor_files:
            try:
                room = self._load_room(building_id, sensor_file)
                if room:
                    rooms.append(room)
            except Exception as e:
                logger.error(f"Error loading room from {sensor_file}: {e}")
                continue
        
        return rooms
    
    def _load_room(self, building_id: str, sensor_file: Path) -> Optional[Room]:
        """Load a single room from a sensor file."""
        room_name = sensor_file.stem
        room_id = self._sanitize_id(f"{building_id}_{room_name}")
        
        try:
            df = pd.read_csv(sensor_file)
            
            # Parse timestamp column
            timestamp_col = self._find_timestamp_column(list(df.columns))
            if not timestamp_col:
                logger.error(f"No timestamp column found in {sensor_file}")
                return None
            
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            df = df.set_index(timestamp_col)
            df.index.name = 'timestamp'
            
            # Create room
            room = Room(
                id=room_id,
                name=room_name.replace('_', ' ').replace('-', ' ').title(),
                building_id=building_id,
                level_id=None,
                room_type=None,
                area_m2=None,
                volume_m3=None,
                capacity_people=None,
                data_period_start=None,
                data_period_end=None
            )
            
            # Infer room type if enabled
            if self.auto_infer_room_types:
                room.room_type = self._infer_room_type(room_name)
            
            # Map columns to IEQ parameters and create timeseries
            ieq_params = {
                IEQParameter.TEMPERATURE.value: 'temperature',
                IEQParameter.HUMIDITY.value: 'humidity',
                IEQParameter.CO2.value: 'co2',
                IEQParameter.LIGHT.value: 'light',
                IEQParameter.PRESENCE.value: 'presence'
            }
            
            for param_enum, param_name in ieq_params.items():
                possible_cols = self.column_mappings.get(param_enum, [])
                col = self._find_column(list(df.columns), possible_cols)
                
                if col:
                    ts_data = TimeSeriesData(
                        parameter=param_name,
                        unit=self._infer_unit(param_name),
                        data=df[[col]].rename(columns={col: param_name}),
                        source_file=str(sensor_file),
                        period_start=df.index.min(),
                        period_end=df.index.max()
                    )
                    room.add_timeseries(param_name, ts_data)
            
            room.source_files.append(str(sensor_file))
            
            return room if room.timeseries else None
            
        except Exception as e:
            logger.error(f"Error loading room from {sensor_file}: {e}")
            return None
    
    def _find_timestamp_column(self, columns: List[str]) -> Optional[str]:
        """Find the timestamp column in a DataFrame."""
        timestamp_patterns = self.column_mappings.get(IEQParameter.TIMESTAMP.value, [])
        
        for col in columns:
            col_lower = col.lower().strip()
            if col_lower in timestamp_patterns:
                return col
        
        return None
    
    def _find_column(self, columns: List[str], possible_names: List[str]) -> Optional[str]:
        """Find a column by matching possible names."""
        columns_lower = {col.lower().strip(): col for col in columns}
        
        for name in possible_names:
            name_lower = name.lower().strip()
            if name_lower in columns_lower:
                return columns_lower[name_lower]
        
        return None
    
    def _sanitize_id(self, text: str) -> str:
        """Sanitize text to create a valid ID."""
        # Remove special characters and convert to lowercase
        sanitized = re.sub(r'[^\w\s-]', '', text.lower())
        # Replace spaces and multiple hyphens with single underscore
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized.strip('_')
    
    def _infer_unit(self, parameter: str) -> str:
        """Infer measurement unit for a parameter."""
        units = {
            'temperature': '°C',
            'humidity': '%',
            'co2': 'ppm',
            'light': 'lux',
            'presence': 'binary',
            'precipitation': 'mm',
            'wind_speed': 'm/s',
            'radiation': 'W/m²',
            'sunshine': 'hours'
        }
        return units.get(parameter, '')
    
    def _infer_level_from_room(self, room: Room) -> Optional[str]:
        """Infer building level from room name."""
        # Common patterns for floor/level identification
        patterns = [
            r'(\d+)\.?\s*(?:sal|floor|etage|stock)',  # "1. sal", "1. floor"
            r'(?:sal|floor|etage|stock)[_\s-]*(\d+)',  # "sal_1", "floor-1"
            r'^(\d+)\.',  # Starting with number and dot "1."
            r'_(\d+)_',  # Between underscores "_1_"
        ]
        
        room_name_lower = room.name.lower()
        
        for pattern in patterns:
            match = re.search(pattern, room_name_lower)
            if match:
                floor_num = match.group(1)
                return f"level_{floor_num}"
        
        # Check for special level names
        if any(term in room_name_lower for term in ['ground', 'stue', 'erdgeschoss', 'rez']):
            return "level_0"
        if any(term in room_name_lower for term in ['basement', 'kælder', 'keller', 'sous-sol']):
            return "level_-1"
        
        return None
    
    def _format_level_name(self, level_id: str) -> str:
        """Format level ID to human-readable name."""
        match = re.search(r'level_(-?\d+)', level_id)
        if match:
            floor_num = int(match.group(1))
            if floor_num == 0:
                return "Ground Floor"
            elif floor_num < 0:
                return f"Basement {abs(floor_num)}"
            elif floor_num == 1:
                return "1st Floor"
            elif floor_num == 2:
                return "2nd Floor"
            elif floor_num == 3:
                return "3rd Floor"
            else:
                return f"{floor_num}th Floor"
        return level_id.replace('_', ' ').title()
    
    def _infer_room_type(self, room_name: str) -> Optional[RoomType]:
        """Infer room type from room name."""
        room_name_lower = room_name.lower()
        
        for room_type_str, patterns in ROOM_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in room_name_lower:
                    # Find the matching RoomType enum
                    for room_type in RoomType:
                        if room_type.value == room_type_str:
                            return room_type
        
        return None
    
    def _validate_building_data(self, building: Building) -> None:
        """Validate building data quality."""
        logger.info(f"Validating data for building: {building.name}")
        
        issues = []
        
        # Check if building has rooms
        if not building.rooms:
            issues.append("No rooms with sensor data")
        
        # Check if building has climate data
        if not building.climate_data:
            issues.append("No climate data available")
        
        # Check room data quality
        for room in building.rooms:
            quality_score = room.get_overall_quality_score()
            
            if quality_score < 50:
                issues.append(f"Room {room.name} has low data quality ({quality_score:.1f}%)")
            
            # Check for required parameters
            required_params = ['temperature', 'co2', 'humidity']
            for param in required_params:
                if param not in room.timeseries:
                    issues.append(f"Room {room.name} missing {param} data")
        
        if issues:
            logger.warning(f"Data quality issues for {building.name}:\n" + 
                         "\n".join(f"  - {issue}" for issue in issues))
        else:
            logger.info(f"Data validation passed for {building.name}")
    
    def load_single_building(self, building_dir: Path, validate: bool = True) -> Optional[Building]:
        """
        Load a single building from a directory.
        
        Args:
            building_dir: Directory containing building data
            validate: Whether to validate data quality
        
        Returns:
            Building object or None if loading failed
        """
        return self._load_building(building_dir, validate=validate)


def create_data_loader(auto_infer_levels: bool = True, 
                       auto_infer_room_types: bool = True) -> DataLoaderService:
    """
    Factory function to create a DataLoaderService instance.
    
    Args:
        auto_infer_levels: Automatically infer building levels from room names
        auto_infer_room_types: Automatically infer room types from names
    
    Returns:
        DataLoaderService instance
    """
    return DataLoaderService(
        auto_infer_levels=auto_infer_levels,
        auto_infer_room_types=auto_infer_room_types
    )
