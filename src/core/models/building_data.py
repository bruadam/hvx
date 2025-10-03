"""
Enhanced data models for building hierarchy with timeseries data.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
import pandas as pd
import numpy as np

from .enums import IEQParameter, RoomType


class DataQuality(BaseModel):
    """Data quality metrics."""
    
    completeness: float = Field(default=0.0, description="Data completeness percentage (0-100)", ge=0, le=100)
    missing_count: int = Field(default=0, description="Number of missing values", ge=0)
    total_count: int = Field(default=0, description="Total number of expected values", ge=0)
    gaps: List[Dict[str, Any]] = Field(default_factory=list, description="List of data gaps (start, end, duration)")
    quality_score: str = Field(default="Unknown", description="Qualitative quality score (High/Medium/Low)")
    
    def calculate_quality_score(self) -> None:
        """Calculate qualitative quality score based on completeness."""
        if self.completeness >= 90:
            self.quality_score = "High"
        elif self.completeness >= 75:
            self.quality_score = "Medium"
        elif self.completeness >= 50:
            self.quality_score = "Low"
        else:
            self.quality_score = "Very Low"


class TimeSeriesData(BaseModel):
    """Time series data container with quality metrics."""
    
    parameter: str = Field(..., description="Parameter name (temperature, co2, etc.)")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    data: pd.DataFrame = Field(..., description="DataFrame with timestamp index and values")
    source_file: Optional[str] = Field(None, description="Source file path")
    period_start: Optional[datetime] = Field(None, description="Start of data period")
    period_end: Optional[datetime] = Field(None, description="End of data period")
    data_quality: DataQuality = Field(default_factory=DataQuality, description="Data quality metrics")
    resolution: str = Field(default="H", description="Data resolution (pandas frequency string)")
    
    model_config = {"arbitrary_types_allowed": True}
    
    @field_validator('data')
    @classmethod
    def validate_dataframe(cls, v):
        if not isinstance(v, pd.DataFrame):
            raise ValueError("data must be a pandas DataFrame")
        
        if not isinstance(v.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have a DatetimeIndex")
        
        return v
    
    @model_validator(mode="after")
    def extract_period_and_quality(self):
        """Extract data period and calculate quality metrics."""
        if self.data is not None and not self.data.empty:
            self.period_start = self.data.index.min().to_pydatetime()
            self.period_end = self.data.index.max().to_pydatetime()
            
            # Calculate data quality
            if self.parameter in self.data.columns:
                series = self.data[self.parameter]
                total = len(series)
                missing = series.isna().sum()
                completeness = ((total - missing) / total * 100) if total > 0 else 0
                
                self.data_quality.completeness = completeness
                self.data_quality.missing_count = int(missing)
                self.data_quality.total_count = total
                self.data_quality.calculate_quality_score()
        
        return self
    
    def get_statistics(self) -> Dict[str, float]:
        """Calculate basic statistics for the timeseries."""
        if self.parameter not in self.data.columns:
            return {}
        
        series = self.data[self.parameter].dropna()
        if len(series) == 0:
            return {}
        
        return {
            'mean': float(series.mean()),
            'std': float(series.std()),
            'min': float(series.min()),
            'max': float(series.max()),
            'median': float(series.median()),
            'count': int(len(series))
        }


class ClimateData(BaseModel):
    """Climate data for a building."""
    
    building_id: str = Field(..., description="Building identifier")
    source_file: Optional[str] = Field(None, description="Source climate file path")
    timeseries: Dict[str, TimeSeriesData] = Field(default_factory=dict, description="Climate parameters timeseries")
    period_start: Optional[datetime] = Field(None, description="Start of climate data period")
    period_end: Optional[datetime] = Field(None, description="End of climate data period")
    
    def add_timeseries(self, parameter: str, ts: TimeSeriesData) -> None:
        """Add a timeseries for a climate parameter."""
        self.timeseries[parameter] = ts
        
        # Update period boundaries
        if ts.period_start:
            if not self.period_start or ts.period_start < self.period_start:
                self.period_start = ts.period_start
        
        if ts.period_end:
            if not self.period_end or ts.period_end > self.period_end:
                self.period_end = ts.period_end
    
    def get_parameter(self, parameter: str) -> Optional[TimeSeriesData]:
        """Get timeseries for a specific parameter."""
        return self.timeseries.get(parameter)


class Room(BaseModel):
    """Enhanced room model with timeseries data."""
    
    id: str = Field(..., description="Unique room identifier")
    name: str = Field(..., description="Human-readable room name")
    building_id: str = Field(..., description="ID of the building this room belongs to")
    level_id: Optional[str] = Field(None, description="ID of the level/floor this room belongs to")
    room_type: Optional[RoomType] = Field(None, description="Type of room")
    area_m2: Optional[float] = Field(None, description="Room area in square meters", gt=0)
    volume_m3: Optional[float] = Field(None, description="Room volume in cubic meters", gt=0)
    capacity_people: Optional[int] = Field(None, description="Maximum occupancy", gt=0)
    tags: List[str] = Field(default_factory=list, description="Custom tags for room classification")
    
    # Sensor data
    timeseries: Dict[str, TimeSeriesData] = Field(default_factory=dict, description="Sensor timeseries data")
    source_files: List[str] = Field(default_factory=list, description="Source sensor file paths")
    data_period_start: Optional[datetime] = Field(None, description="Start of sensor data period")
    data_period_end: Optional[datetime] = Field(None, description="End of sensor data period")
    
    @field_validator('id', 'name', 'building_id')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v.strip()
    
    def add_timeseries(self, parameter: str, ts: TimeSeriesData) -> None:
        """Add a timeseries for a sensor parameter."""
        self.timeseries[parameter] = ts
        
        # Update period boundaries
        if ts.period_start:
            if not self.data_period_start or ts.period_start < self.data_period_start:
                self.data_period_start = ts.period_start
        
        if ts.period_end:
            if not self.data_period_end or ts.period_end > self.data_period_end:
                self.data_period_end = ts.period_end
    
    def get_parameter(self, parameter: str) -> Optional[TimeSeriesData]:
        """Get timeseries for a specific parameter."""
        return self.timeseries.get(parameter)
    
    def get_data_quality(self) -> Dict[str, DataQuality]:
        """Get data quality metrics for all parameters."""
        return {param: ts.data_quality for param, ts in self.timeseries.items()}
    
    def get_overall_quality_score(self) -> float:
        """Calculate overall data quality score (0-100)."""
        if not self.timeseries:
            return 0.0
        
        completeness_scores = [ts.data_quality.completeness for ts in self.timeseries.values()]
        return float(np.mean(completeness_scores)) if completeness_scores else 0.0


class Level(BaseModel):
    """Building level/floor with rooms."""
    
    id: str = Field(..., description="Unique level identifier")
    name: str = Field(..., description="Human-readable level name (e.g., 'Ground Floor', '1st Floor')")
    building_id: str = Field(..., description="ID of the building this level belongs to")
    floor_number: Optional[int] = Field(None, description="Floor number (0 for ground, negative for basement)")
    rooms: List[Room] = Field(default_factory=list, description="Rooms on this level")
    
    @field_validator('id', 'name', 'building_id')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v.strip()
    
    def add_room(self, room: Room) -> None:
        """Add a room to this level."""
        if room.level_id and room.level_id != self.id:
            room.level_id = self.id
        
        # Check for duplicate room IDs
        existing_ids = {r.id for r in self.rooms}
        if room.id in existing_ids:
            raise ValueError(f"Room with ID {room.id} already exists in level {self.id}")
        
        self.rooms.append(room)
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID."""
        for room in self.rooms:
            if room.id == room_id:
                return room
        return None
    
    def get_room_count(self) -> int:
        """Get number of rooms on this level."""
        return len(self.rooms)


class Building(BaseModel):
    """Enhanced building model with levels and climate data."""
    
    id: str = Field(..., description="Unique building identifier")
    name: str = Field(..., description="Human-readable building name")
    address: Optional[str] = Field(None, description="Building address")
    city: Optional[str] = Field(None, description="City")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country: Optional[str] = Field(default="Denmark", description="Country")
    construction_year: Optional[int] = Field(None, description="Year of construction")
    total_area_m2: Optional[float] = Field(None, description="Total building area in square meters", gt=0)
    
    # Hierarchical structure
    levels: List[Level] = Field(default_factory=list, description="Building levels/floors")
    rooms: List[Room] = Field(default_factory=list, description="All rooms in building (flat structure)")
    
    # Climate data
    climate_data: Optional[ClimateData] = Field(None, description="Building climate data")
    
    # Source information
    source_directory: Optional[str] = Field(None, description="Source data directory")
    loaded_at: datetime = Field(default_factory=datetime.now, description="When data was loaded")
    
    @field_validator('id', 'name')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v.strip()
    
    def add_level(self, level: Level) -> None:
        """Add a level to the building."""
        if level.building_id != self.id:
            level.building_id = self.id
        
        # Check for duplicate level IDs
        existing_ids = {l.id for l in self.levels}
        if level.id in existing_ids:
            raise ValueError(f"Level with ID {level.id} already exists in building {self.id}")
        
        self.levels.append(level)
    
    def add_room(self, room: Room, level_id: Optional[str] = None) -> None:
        """Add a room to the building and optionally to a specific level."""
        if room.building_id != self.id:
            room.building_id = self.id
        
        # Check for duplicate room IDs
        existing_ids = {r.id for r in self.rooms}
        if room.id in existing_ids:
            raise ValueError(f"Room with ID {room.id} already exists in building {self.id}")
        
        self.rooms.append(room)
        
        # Add to level if specified
        if level_id:
            level = self.get_level(level_id)
            if level:
                room.level_id = level_id
                level.add_room(room)
    
    def get_level(self, level_id: str) -> Optional[Level]:
        """Get a level by ID."""
        for level in self.levels:
            if level.id == level_id:
                return level
        return None
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID from flat structure."""
        for room in self.rooms:
            if room.id == room_id:
                return room
        return None
    
    def get_room_count(self) -> int:
        """Get total number of rooms in building."""
        return len(self.rooms)
    
    def get_level_count(self) -> int:
        """Get number of levels in building."""
        return len(self.levels)
    
    def set_climate_data(self, climate_data: ClimateData) -> None:
        """Set climate data for the building."""
        if climate_data.building_id != self.id:
            climate_data.building_id = self.id
        self.climate_data = climate_data
    
    def get_data_quality_summary(self) -> Dict[str, Any]:
        """Get overall data quality summary for the building."""
        summary = {
            'building_id': self.id,
            'building_name': self.name,
            'total_rooms': self.get_room_count(),
            'total_levels': self.get_level_count(),
            'rooms_with_data': 0,
            'overall_quality_score': 0.0,
            'climate_data_available': self.climate_data is not None
        }
        
        if self.rooms:
            rooms_with_data = [r for r in self.rooms if r.timeseries]
            summary['rooms_with_data'] = len(rooms_with_data)
            
            if rooms_with_data:
                quality_scores = [r.get_overall_quality_score() for r in rooms_with_data]
                summary['overall_quality_score'] = float(np.mean(quality_scores))
        
        return summary


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
