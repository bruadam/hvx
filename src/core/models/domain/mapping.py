"""Data column mapping models."""

from typing import List, Optional, Dict, Union
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

from src.core.models.enums import IEQParameter, RoomType


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
                        from src.core.models.enums import RoomType
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
            from src.core.models.enums import IEQParameter
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
            from src.core.models.enums import RoomType
            for mapping in data['mappings']:
                if 'room_type' in mapping and mapping['room_type'] is not None:
                    room_type_str = mapping['room_type']
                    # Find enum by value
                    for room_type in RoomType:
                        if room_type.value == room_type_str:
                            mapping['room_type'] = room_type
                            break

        return cls(**data)
