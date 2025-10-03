"""
Data mapping utilities for IEQ sensor data.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
import pandas as pd
import click

from src.core.models.enums import IEQParameter, DEFAULT_COLUMN_MAPPINGS, RoomType, BUILDING_TYPE_PATTERNS, ROOM_TYPE_PATTERNS


class DataMapper:
    """Main class for mapping raw sensor data to standardized IEQ format."""
    
    def __init__(self, config: Optional[MappingConfig] = None):
        """Initialize mapper with optional configuration."""
        self.config = config or MappingConfig(timestamp_format="%Y-%m-%d %H:%M:%S")
        self.buildings: Dict[str, Building] = {}
        self.detected_columns: Set[str] = set()
    
    def analyze_files(self, data_dir: Path) -> Dict[str, Any]:
        """Analyze CSV files to detect column patterns and structure."""
        analysis = {
            'files': [],
            'unique_columns': set(),
            'column_frequency': {},
            'building_patterns': set(),
            'room_patterns': set()
        }
        
        csv_files = list(data_dir.glob("*.csv"))
        
        for file_path in csv_files:
            try:
                # Read just the header to get column names
                df = pd.read_csv(file_path, nrows=0)
                columns = list(df.columns)
                
                file_info = {
                    'path': str(file_path),
                    'name': file_path.name,
                    'columns': columns,
                    'building_hint': self._extract_building_hint(file_path.name),
                    'room_hint': self._extract_room_hint(file_path.name)
                }
                
                analysis['files'].append(file_info)
                analysis['unique_columns'].update(columns)
                
                # Update column frequency
                for col in columns:
                    analysis['column_frequency'][col] = analysis['column_frequency'].get(col, 0) + 1
                
                # Extract building and room patterns
                if file_info['building_hint']:
                    analysis['building_patterns'].add(file_info['building_hint'])
                if file_info['room_hint']:
                    analysis['room_patterns'].add(file_info['room_hint'])
                    
            except Exception as e:
                click.echo(f"Warning: Could not analyze file {file_path}: {e}", err=True)
        
        # Convert sets to lists for JSON serialization
        analysis['unique_columns'] = list(analysis['unique_columns'])
        analysis['building_patterns'] = list(analysis['building_patterns'])
        analysis['room_patterns'] = list(analysis['room_patterns'])
        
        return analysis
    
    def _extract_building_hint(self, filename: str) -> Optional[str]:
        """Extract building name hint from filename."""
        # Common patterns for building names in filenames
        patterns = [
            r'(Fl[øo]ng[\s_]*Skole)',  # Fløng Skole variants
            r'(Ole[\s_]*R[øo]mer[\s\-_]*Skolen?)',  # Ole Rømer-Skolen variants
            r'(Reerslev)',  # Reerslev
            r'^([^_]+(?:[\s_]+[^_]+)*?)_',  # General pattern: words before first major underscore
            r'([A-Za-z]+(?:\s+[A-Za-z]+)*?)_',  # Word sequence before underscore
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                building_hint = match.group(1).replace('_', ' ').strip()
                # Clean up the building name
                building_hint = re.sub(r'\s+', ' ', building_hint)  # Normalize spaces
                if len(building_hint) > 2:  # Avoid very short hints
                    return building_hint
        
        return None
    
    def _extract_room_hint(self, filename: str) -> Optional[str]:
        """Extract room name hint from filename."""
        # Common patterns for room identifiers - ordered by specificity
        patterns = [
            # Specific patterns for different file formats
            r'(?:sal|room)[\s_]*([0-9]+\.[0-9]+)',  # sal_0.078, sal_0.086
            r'(?:klasse|classe)[\s_]*([0-9]+)',  # Klasse_101, Klasse_142
            r'(?:stue|stueplan)[\s_]*([0-9]+\.[0-9]+)',  # Stue_0.016, Stue_0.077
            r'(?:sal|room)[\s_]*([0-9]+)',  # sal_11, sal_34
            # More general decimal patterns
            r'([0-9]+\.[0-9]+)',  # Decimal room numbers (e.g., 0.078, 0.086)
            r'_([0-9]+)_processed',  # Numbers before _processed
            r'([0-9]+)',  # Any integer room numbers
            # Alphanumeric room codes
            r'([A-Z]?[0-9]+[A-Z]?)',  # Alphanumeric room codes
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, filename, re.IGNORECASE)
            if matches:
                # Return the first meaningful match
                for match in matches:
                    if match and len(match) > 0:
                        return match
        
        return None
    
    def suggest_column_mappings(self, columns: List[str]) -> Dict[str, str]:
        """Suggest IEQ parameter mappings for given columns."""
        suggestions = {}
        
        for col in columns:
            col_lower = col.lower()
            
            # Check against default mappings
            for param, possible_names in DEFAULT_COLUMN_MAPPINGS.items():
                if any(name in col_lower for name in possible_names):
                    suggestions[col] = param
                    break
        
        return suggestions
    
    def interactive_column_mapping(self, filename: str, columns: List[str]) -> Dict[str, str]:
        """Interactive CLI for mapping columns to IEQ parameters."""
        click.echo(f"\n📁 Mapping columns for file: {filename}")
        click.echo(f"Available columns: {', '.join(columns)}")
        
        # Get automatic suggestions
        suggestions = self.suggest_column_mappings(columns)
        
        mapping = {}
        available_params = [param.value for param in IEQParameter]
        
        # Show suggestions first
        if suggestions:
            click.echo("\n💡 Automatic suggestions:")
            for col, param in suggestions.items():
                click.echo(f"  {col} -> {param}")
            
            if click.confirm("Accept these suggestions?"):
                mapping.update(suggestions)
        
        # Interactive mapping for remaining columns
        unmapped_columns = [col for col in columns if col not in mapping]
        
        if unmapped_columns:
            click.echo("\n🔧 Manual mapping for remaining columns:")
            
            for col in unmapped_columns:
                click.echo(f"\nColumn: '{col}'")
                click.echo(f"Available IEQ parameters: {', '.join(available_params)}")
                
                param = click.prompt(
                    "Map to IEQ parameter (or 'skip' to ignore)",
                    type=click.Choice(available_params + ['skip']),
                    default='skip'
                )
                
                if param != 'skip':
                    mapping[col] = param
        
        return mapping
    
    def map_file(self, file_path: Path, column_mapping: Dict[str, str], mapping_config: Optional[ColumnMapping] = None) -> Optional[IEQData]:
        """Map a single CSV file to IEQ data format."""
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            if df.empty:
                click.echo(f"Warning: File {file_path} is empty", err=True)
                return None
            
            # Apply column mapping
            mapped_df = pd.DataFrame()
            timestamp_col = None
            
            for source_col, target_param in column_mapping.items():
                if source_col in df.columns:
                    if target_param == IEQParameter.TIMESTAMP.value:
                        timestamp_col = source_col
                    else:
                        mapped_df[target_param] = df[source_col]
            
            # Handle timestamp
            if timestamp_col is None:
                raise ValueError(f"No timestamp column found in {file_path}")
            
            try:
                timestamps = pd.to_datetime(df[timestamp_col])
                mapped_df = mapped_df.set_index(timestamps)
                # Rename the index to 'timestamp' for consistency
                mapped_df.index.name = 'timestamp'
            except Exception as e:
                raise ValueError(f"Could not parse timestamps in {file_path}: {e}")
            
            # Validate hourly resolution
            datetime_index = pd.to_datetime(mapped_df.index)
            datetime_index = pd.DatetimeIndex(datetime_index)
            if not self._validate_hourly_resolution(datetime_index):
                raise ValueError(f"Data in {file_path} is not at hourly resolution")
            
            # Extract building and room info
            building_name = self._extract_building_hint(file_path.name) or self.config.default_building_name
            room_name = self._extract_room_hint(file_path.name) or file_path.stem
            
            # Create or get building
            building_id = self._create_building_id(building_name)
            if building_id not in self.buildings:
                self.buildings[building_id] = Building(
                    id=building_id,
                    name=building_name,
                    address="",
                    city="",
                    postal_code="",
                    construction_year=None,
                    total_area_m2=None,
                    floors=None
                )
            
            # Create room
            room_id = f"{building_id}_{room_name}"
            # Use configured room type if available, otherwise infer from building and room name
            if mapping_config and mapping_config.room_type:
                room_type = mapping_config.room_type
            else:
                room_type = self._infer_room_type(building_name, room_name)
            
            room = Room(
                id=room_id,
                name=room_name,
                building_id=building_id,
                floor=None,
                room_type=room_type,
                area_m2=None,
                volume_m3=None,
                capacity_people=None
            )
            
            # Add room to building if not exists
            if not self.buildings[building_id].get_room(room_id):
                self.buildings[building_id].add_room(room)
            
            # Create IEQ data object
            # Determine data period start and end from the mapped_df index
            data_period_start = mapped_df.index.min() if not mapped_df.empty else None
            data_period_end = mapped_df.index.max() if not mapped_df.empty else None
            quality_score = None  # Set to None or compute as needed

            ieq_data = IEQData(
                room_id=room_id,
                building_id=building_id,
                data=mapped_df,
                source_files=[str(file_path)],
                resolution="H",
                data_period_start=data_period_start,
                data_period_end=data_period_end,
                quality_score=quality_score
            )
            
            return ieq_data
            
        except Exception as e:
            click.echo(f"Error processing file {file_path}: {e}", err=True)
            return None
    
    def _validate_hourly_resolution(self, index: pd.DatetimeIndex) -> bool:
        """Validate that data is at hourly resolution."""
        if len(index) < 2:
            return True
        
        # Calculate time differences
        time_diffs = index[1:] - index[:-1]
        
        # Check if most intervals are 1 hour (allowing some tolerance)
        hour_intervals = time_diffs == pd.Timedelta(hours=1)
        return hour_intervals.sum() / len(time_diffs) > 0.8  # 80% threshold
    
    def _infer_room_type(self, building_name: str, room_name: str) -> RoomType:
        """Infer room type based on building name and room patterns using centralized patterns."""
        building_lower = building_name.lower()
        room_lower = room_name.lower()
        
        # First, check for specific room type patterns in room name
        for room_type_value, patterns in ROOM_TYPE_PATTERNS.items():
            if any(pattern in room_lower for pattern in patterns):
                # Convert string value back to enum
                for room_type in RoomType:
                    if room_type.value == room_type_value:
                        return room_type
        
        # Then, infer based on building type patterns
        # School buildings - default to classroom
        if any(pattern in building_lower for pattern in BUILDING_TYPE_PATTERNS.get("school", [])):
            return RoomType.CLASSROOM
        
        # Office buildings - default to office
        if any(pattern in building_lower for pattern in BUILDING_TYPE_PATTERNS.get("office", [])):
            return RoomType.OFFICE
        
        # Hospital buildings - default to other (could be extended with medical room types)
        if any(pattern in building_lower for pattern in BUILDING_TYPE_PATTERNS.get("hospital", [])):
            return RoomType.OTHER
        
        # Default fallback
        return RoomType.OTHER
    
    def _create_building_id(self, building_name: str) -> str:
        """Create a standardized building ID."""
        # Preserve Danish/Norwegian characters (øæå) and other common European characters
        # Only replace spaces and special punctuation with underscores
        return re.sub(r'[^\w\øæåÆØÅ]', '_', building_name.lower())
    
    def process_directory(
        self, 
        data_dir: Path, 
        output_dir: Optional[Path] = None,
        interactive: bool = True
    ) -> List[IEQData]:
        """Process all CSV files in a directory."""
        
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        csv_files = list(data_dir.glob("*.csv"))
        if not csv_files:
            raise ValueError(f"No CSV files found in {data_dir}")
        
        click.echo(f"Found {len(csv_files)} CSV files to process")
        
        # Analyze files first
        analysis = self.analyze_files(data_dir)
        
        # Create output directory if specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        processed_data = []
        
        for file_path in csv_files:
            click.echo(f"\n📄 Processing: {file_path.name}")
            
            # Check if we have existing mapping for this file
            existing_mapping = self.config.get_mapping_for_file(file_path.name)
            
            if existing_mapping:
                column_mapping = existing_mapping.column_mappings
                click.echo("Using existing column mapping from configuration")
            elif interactive:
                # Read columns for interactive mapping
                df_sample = pd.read_csv(file_path, nrows=0)
                column_mapping = self.interactive_column_mapping(
                    file_path.name, 
                    list(df_sample.columns)
                )
            else:
                # Use automatic suggestions
                df_sample = pd.read_csv(file_path, nrows=0)
                column_mapping = self.suggest_column_mappings(list(df_sample.columns))
                
                if not column_mapping:
                    click.echo(f"⚠️  Could not automatically map columns for {file_path.name}", err=True)
                    continue
            
            # Process the file
            ieq_data = self.map_file(file_path, column_mapping, existing_mapping)
            
            if ieq_data:
                processed_data.append(ieq_data)
                click.echo(f"✅ Successfully processed {file_path.name}")
                
                # Save processed data if output directory specified
                if output_dir:
                    output_file = output_dir / f"{ieq_data.room_id}_processed.csv"
                    ieq_data.data.to_csv(output_file)
            else:
                click.echo(f"❌ Failed to process {file_path.name}")
        
        click.echo(f"\n🎉 Processing complete! Processed {len(processed_data)} files successfully.")
        return processed_data
    
    def save_config(self, filepath: Path) -> None:
        """Save current mapping configuration."""
        self.config.save_to_file(filepath)
        click.echo(f"Configuration saved to {filepath}")
    
    def load_config(self, filepath: Path) -> None:
        """Load mapping configuration."""
        if filepath.exists():
            self.config = MappingConfig.load_from_file(filepath)
            click.echo(f"Configuration loaded from {filepath}")
        else:
            click.echo(f"Configuration file not found: {filepath}", err=True)
