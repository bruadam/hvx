"""
Pydantic models for IEQ data structures.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from pydantic import BaseModel, Field, model_validator, field_validator
import pandas as pd

from .enums import IEQParameter, RoomType, ComfortCategory


class Room(BaseModel):
    """Model for a room with IEQ sensors."""
    
    id: str = Field(..., description="Unique room identifier")
    name: str = Field(..., description="Human-readable room name")
    building_id: str = Field(..., description="ID of the building this room belongs to")
    floor: Optional[str] = Field(None, description="Floor identifier")
    room_type: Optional[RoomType] = Field(None, description="Type of room")
    area_m2: Optional[float] = Field(None, description="Room area in square meters", gt=0)
    volume_m3: Optional[float] = Field(None, description="Room volume in cubic meters", gt=0)
    capacity_people: Optional[int] = Field(None, description="Maximum occupancy", gt=0)
    tags: List[str] = Field(default_factory=list, description="Custom tags for room classification")
    
    @field_validator('id', 'name', 'building_id')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        return [tag.strip() for tag in v if tag.strip()]


class Building(BaseModel):
    """Model for a building containing multiple rooms."""
    
    id: str = Field(..., description="Unique building identifier")
    name: str = Field(..., description="Human-readable building name")
    address: Optional[str] = Field(None, description="Building address")
    city: Optional[str] = Field(None, description="City")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country: Optional[str] = Field(default="Denmark", description="Country")
    construction_year: Optional[int] = Field(None, description="Year of construction")
    total_area_m2: Optional[float] = Field(None, description="Total building area in square meters", gt=0)
    floors: Optional[int] = Field(None, description="Number of floors", gt=0)
    rooms: List[Room] = Field(default_factory=list, description="List of rooms in the building")
    
    @field_validator('id', 'name')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v.strip()
    
    @model_validator(mode="after")
    def validate_rooms_belong_to_building(self):
        building_id = self.id
        rooms = self.rooms
        
        for room in rooms:
            if room.building_id != building_id:
                raise ValueError(f"Room {room.id} has building_id {room.building_id} but belongs to building {building_id}")
        
        return self
    
    def add_room(self, room: Room) -> None:
        """Add a room to the building."""
        if room.building_id != self.id:
            room.building_id = self.id
        
        # Check for duplicate room IDs
        existing_ids = {r.id for r in self.rooms}
        if room.id in existing_ids:
            raise ValueError(f"Room with ID {room.id} already exists in building {self.id}")
        
        self.rooms.append(room)
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID."""
        for room in self.rooms:
            if room.id == room_id:
                return room
        return None


class IEQData(BaseModel):
    """Model for processed IEQ sensor data."""
    
    room_id: str = Field(..., description="Room identifier")
    building_id: str = Field(..., description="Building identifier") 
    data: pd.DataFrame = Field(..., description="DataFrame with timestamp index and IEQ measurements")
    source_files: List[str] = Field(default_factory=list, description="Original source file paths")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="When data was processed")
    data_period_start: Optional[datetime] = Field(None, description="Start of data period")
    data_period_end: Optional[datetime] = Field(None, description="End of data period")
    resolution: str = Field(default="H", description="Data resolution (pandas frequency string)")
    quality_score: Optional[float] = Field(None, description="Data quality score (0-1)", ge=0, le=1)
    
    model_config = {"arbitrary_types_allowed": True}
    
    @field_validator('data')
    @classmethod
    def validate_dataframe(cls, v):
        if not isinstance(v, pd.DataFrame):
            raise ValueError("data must be a pandas DataFrame")
        
        if v.empty:
            raise ValueError("DataFrame cannot be empty")
        
        # Check for timestamp index
        if not isinstance(v.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have a DatetimeIndex")
        
        return v
    
    @model_validator(mode="after")
    def extract_data_period(self):
        data = self.data
        if data is not None and not data.empty:
            self.data_period_start = data.index.min().to_pydatetime()
            self.data_period_end = data.index.max().to_pydatetime()
        
        return self
    
    def get_measurement_columns(self) -> List[str]:
        """Get columns that contain measurement data."""
        measurement_params = [param.value for param in IEQParameter.get_measurement_parameters()]
        return [col for col in self.data.columns if any(param in col.lower() for param in measurement_params)]
    
    def get_data_completeness(self) -> Dict[str, float]:
        """Calculate data completeness for each column."""
        return {
            col: (self.data[col].count() / len(self.data)) 
            for col in self.data.columns
        }
    
    def resample_data(self, frequency: str) -> 'IEQData':
        """Resample data to different frequency."""
        resampled_data = self.data.resample(frequency).mean()
        
        return IEQData(
            room_id=self.room_id,
            building_id=self.building_id,
            data=resampled_data,
            source_files=self.source_files,
            resolution=frequency,
            quality_score=self.quality_score,
            data_period_start=None,  # Will be set by model_validator
            data_period_end=None     # Will be set by model_validator
        )


class ColumnMapping(BaseModel):
    """Model for column mapping configuration."""
    
    file_pattern: str = Field(..., description="File name pattern or regex")
    column_mappings: Dict[str, str] = Field(..., description="Mapping from source column to IEQ parameter")
    building_name: Optional[str] = Field(None, description="Building name extracted from file pattern")
    room_name: Optional[str] = Field(None, description="Room name extracted from file pattern")
    room_type: Optional[RoomType] = Field(None, description="Default room type for rooms in this mapping")
    
    @field_validator('column_mappings')
    @classmethod
    def validate_mappings(cls, v):
        valid_params = {param.value for param in IEQParameter}
        for target_param in v.values():
            if target_param not in valid_params:
                raise ValueError(f"Invalid IEQ parameter: {target_param}")
        return v


class MappingConfig(BaseModel):
    """Configuration for data mapping process."""
    
    mappings: List[ColumnMapping] = Field(default_factory=list, description="List of column mappings")
    default_building_name: str = Field(default="Unknown Building", description="Default building name")
    timestamp_format: Optional[str] = Field(None, description="Expected timestamp format")
    required_parameters: List[IEQParameter] = Field(
        default_factory=lambda: [IEQParameter.TIMESTAMP, IEQParameter.TEMPERATURE],
        description="Parameters that must be present"
    )
    
    def add_mapping(self, mapping: ColumnMapping) -> None:
        """Add a column mapping."""
        self.mappings.append(mapping)
    
    def get_mapping_for_file(self, filename: str) -> Optional[ColumnMapping]:
        """Get mapping configuration for a specific file."""
        import re
        
        for mapping in self.mappings:
            if re.match(mapping.file_pattern, filename):
                return mapping
        return None
    
    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        import json
        
        # Convert the model to dict and handle enum serialization
        data = self.model_dump()
        
        # Convert IEQParameter enums to their string values
        if 'required_parameters' in data:
            data['required_parameters'] = [
                param.value if hasattr(param, 'value') else str(param)
                for param in self.required_parameters
            ]
        
        # Convert RoomType enums in mappings to their string values
        if 'mappings' in data:
            for mapping in data['mappings']:
                if 'room_type' in mapping and mapping['room_type'] is not None:
                    if hasattr(mapping['room_type'], 'value'):
                        mapping['room_type'] = mapping['room_type'].value
                    elif isinstance(mapping['room_type'], str) and mapping['room_type'].startswith('RoomType.'):
                        # Handle case where it's already a string representation
                        from .enums import RoomType
                        enum_name = mapping['room_type'].split('.')[1]
                        try:
                            mapping['room_type'] = getattr(RoomType, enum_name).value
                        except AttributeError:
                            mapping['room_type'] = 'other'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> 'MappingConfig':
        """Load configuration from JSON file."""
        import json
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Convert string values back to IEQParameter enums
        if 'required_parameters' in data:
            from .enums import IEQParameter
            converted_params = []
            for param_str in data['required_parameters']:
                # Handle both enum value strings and enum representation strings
                if param_str.startswith('IEQParameter.'):
                    # Extract the enum name and get the corresponding enum
                    enum_name = param_str.split('.')[1]
                    try:
                        converted_params.append(getattr(IEQParameter, enum_name))
                    except AttributeError:
                        # If enum name doesn't exist, try to find by value
                        for param in IEQParameter:
                            if param.value == param_str.lower():
                                converted_params.append(param)
                                break
                else:
                    # Find enum by value
                    for param in IEQParameter:
                        if param.value == param_str:
                            converted_params.append(param)
                            break
            data['required_parameters'] = converted_params
        
        # Convert string values back to RoomType enums in mappings
        if 'mappings' in data:
            from .enums import RoomType
            for mapping in data['mappings']:
                if 'room_type' in mapping and mapping['room_type'] is not None:
                    room_type_str = mapping['room_type']
                    # Find enum by value
                    for room_type in RoomType:
                        if room_type.value == room_type_str:
                            mapping['room_type'] = room_type
                            break
        
        return cls(**data)
