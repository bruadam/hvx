"""
Data Structure Detector Service.

Detects and validates different directory structures for building data.
Supports multiple formats:
- Nested: building/level/room
- Hybrid: building/sensors/climate
- Flat: files with building_level_room naming convention
- Mixed: various combinations of the above
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class DirectoryStructureType(Enum):
    """Types of directory structures supported."""
    NESTED_BUILDING_SENSORS = "nested_building_sensors"  # building/sensors/room.csv
    NESTED_BUILDING_CLIMATE_SENSORS = "nested_building_climate_sensors"  # building/climate/ + sensors/
    NESTED_FULL = "nested_full"  # building/level/room.csv
    FLAT_BUILDING_PREFIX = "flat_building_prefix"  # building_room.csv in single folder
    FLAT_BUILDING_LEVEL_PREFIX = "flat_building_level_prefix"  # building_level_room.csv
    HYBRID_CLIMATE_FILES = "hybrid_climate_files"  # building/ with climate_*.csv and room files
    UNKNOWN = "unknown"


@dataclass
class StructureAnalysis:
    """Analysis results of a directory structure."""
    structure_type: DirectoryStructureType
    confidence: float  # 0.0 to 1.0
    building_count: int
    total_sensor_files: int
    has_climate_data: bool
    issues: List[str]
    recommendations: List[str]
    details: Dict[str, Any]


class DataStructureDetector:
    """Service for detecting and analyzing data directory structures."""
    
    def __init__(self):
        """Initialize the detector."""
        self.csv_extensions = {'.csv', '.CSV'}
        self.climate_patterns = [
            'climate', 'weather', 'outdoor', 'meteorological', 'meteo'
        ]
        self.building_folder_patterns = [
            r'^building[-_\s]*\d+',  # building-1, building_1
            r'^bldg[-_\s]*\d+',  # bldg-1
            r'^b\d+',  # b1, b2
        ]
    
    def analyze_directory(self, data_dir: Path) -> StructureAnalysis:
        """
        Analyze a data directory and determine its structure.
        
        Args:
            data_dir: Path to the data directory
        
        Returns:
            StructureAnalysis with detected structure and recommendations
        """
        logger.info(f"Analyzing directory structure: {data_dir}")
        
        if not data_dir.exists():
            return StructureAnalysis(
                structure_type=DirectoryStructureType.UNKNOWN,
                confidence=0.0,
                building_count=0,
                total_sensor_files=0,
                has_climate_data=False,
                issues=[f"Directory does not exist: {data_dir}"],
                recommendations=["Create the directory or provide a valid path"],
                details={}
            )
        
        if not data_dir.is_dir():
            return StructureAnalysis(
                structure_type=DirectoryStructureType.UNKNOWN,
                confidence=0.0,
                building_count=0,
                total_sensor_files=0,
                has_climate_data=False,
                issues=["Path is not a directory"],
                recommendations=["Provide a valid directory path"],
                details={}
            )
        
        # Collect directory information
        subdirs = [d for d in data_dir.iterdir() if d.is_dir()]
        csv_files = list(data_dir.glob("*.csv"))
        
        # Try different detection strategies
        detectors = [
            self._detect_nested_building_sensors,
            self._detect_nested_full,
            self._detect_flat_with_prefix,
            self._detect_hybrid_climate_files,
        ]
        
        analyses = []
        for detector in detectors:
            analysis = detector(data_dir, subdirs, csv_files)
            if analysis.confidence > 0:
                analyses.append(analysis)
        
        # Return the analysis with highest confidence
        if analyses:
            best_analysis = max(analyses, key=lambda a: a.confidence)
            logger.info(f"Detected structure: {best_analysis.structure_type.value} "
                       f"(confidence: {best_analysis.confidence:.2f})")
            return best_analysis
        
        # No structure detected
        return self._create_unknown_analysis(data_dir, subdirs, csv_files)
    
    def _detect_nested_building_sensors(
        self, 
        data_dir: Path, 
        subdirs: List[Path], 
        csv_files: List[Path]
    ) -> StructureAnalysis:
        """Detect building/sensors/room.csv structure."""
        if not subdirs:
            return self._empty_analysis()
        
        building_count = 0
        total_sensor_files = 0
        has_climate = False
        issues = []
        
        for subdir in subdirs:
            # Check if it looks like a building folder
            if not self._is_building_folder(subdir):
                continue
            
            # Check for sensors subdirectory
            sensors_dir = subdir / "sensors"
            if sensors_dir.exists() and sensors_dir.is_dir():
                sensor_files = list(sensors_dir.glob("*.csv"))
                if sensor_files:
                    building_count += 1
                    total_sensor_files += len(sensor_files)
            
            # Check for climate subdirectory
            climate_dir = subdir / "climate"
            if climate_dir.exists() and climate_dir.is_dir():
                climate_files = list(climate_dir.glob("*.csv"))
                if climate_files:
                    has_climate = True
        
        if building_count == 0:
            return self._empty_analysis()
        
        # Calculate confidence
        confidence = min(1.0, building_count / max(1, len(subdirs)))
        
        # Check for issues
        if not has_climate:
            issues.append("No climate data directories found")
        
        structure_type = (DirectoryStructureType.NESTED_BUILDING_CLIMATE_SENSORS 
                         if has_climate 
                         else DirectoryStructureType.NESTED_BUILDING_SENSORS)
        
        return StructureAnalysis(
            structure_type=structure_type,
            confidence=confidence,
            building_count=building_count,
            total_sensor_files=total_sensor_files,
            has_climate_data=has_climate,
            issues=issues,
            recommendations=[],
            details={
                'subdirectories': len(subdirs),
                'structure': 'building/sensors/*.csv' + (' + building/climate/*.csv' if has_climate else '')
            }
        )
    
    def _detect_nested_full(
        self, 
        data_dir: Path, 
        subdirs: List[Path], 
        csv_files: List[Path]
    ) -> StructureAnalysis:
        """Detect building/level/room.csv structure."""
        if not subdirs:
            return self._empty_analysis()
        
        building_count = 0
        total_sensor_files = 0
        has_climate = False
        
        for building_dir in subdirs:
            if not self._is_building_folder(building_dir):
                continue
            
            # Look for level subdirectories
            level_dirs = [d for d in building_dir.iterdir() if d.is_dir()]
            level_count = 0
            
            for level_dir in level_dirs:
                # Skip climate directories
                if any(pattern in level_dir.name.lower() for pattern in self.climate_patterns):
                    climate_files = list(level_dir.glob("*.csv"))
                    if climate_files:
                        has_climate = True
                    continue
                
                # Check if this level directory has CSV files (rooms)
                room_files = list(level_dir.glob("*.csv"))
                if room_files:
                    level_count += 1
                    total_sensor_files += len(room_files)
            
            if level_count > 0:
                building_count += 1
        
        if building_count == 0:
            return self._empty_analysis()
        
        confidence = min(1.0, building_count / max(1, len(subdirs)))
        
        return StructureAnalysis(
            structure_type=DirectoryStructureType.NESTED_FULL,
            confidence=confidence,
            building_count=building_count,
            total_sensor_files=total_sensor_files,
            has_climate_data=has_climate,
            issues=[],
            recommendations=[],
            details={
                'subdirectories': len(subdirs),
                'structure': 'building/level/*.csv'
            }
        )
    
    def _detect_flat_with_prefix(
        self, 
        data_dir: Path, 
        subdirs: List[Path], 
        csv_files: List[Path]
    ) -> StructureAnalysis:
        """Detect flat structure with building_level_room.csv naming."""
        if not csv_files:
            return self._empty_analysis()
        
        # Patterns to detect building prefixes
        building_pattern = r'^([a-zA-Z]+[-_]?\d+)[-_]'
        building_level_pattern = r'^([a-zA-Z]+[-_]?\d+)[-_](\d+|[a-zA-Z]+)[-_]'
        
        buildings: Set[str] = set()
        has_levels = False
        climate_files = 0
        
        for csv_file in csv_files:
            filename = csv_file.stem
            
            # Check for climate files
            if any(pattern in filename.lower() for pattern in self.climate_patterns):
                climate_files += 1
                continue
            
            # Try to match building_level_room pattern
            match = re.match(building_level_pattern, filename)
            if match:
                building_id = match.group(1)
                buildings.add(building_id)
                has_levels = True
                continue
            
            # Try to match building_room pattern
            match = re.match(building_pattern, filename)
            if match:
                building_id = match.group(1)
                buildings.add(building_id)
        
        if not buildings:
            return self._empty_analysis()
        
        sensor_files = len(csv_files) - climate_files
        confidence = 0.8 if sensor_files > 0 else 0.0
        
        structure_type = (DirectoryStructureType.FLAT_BUILDING_LEVEL_PREFIX 
                         if has_levels 
                         else DirectoryStructureType.FLAT_BUILDING_PREFIX)
        
        return StructureAnalysis(
            structure_type=structure_type,
            confidence=confidence,
            building_count=len(buildings),
            total_sensor_files=sensor_files,
            has_climate_data=climate_files > 0,
            issues=[],
            recommendations=[
                "Consider organizing into building/sensors/ structure for better organization"
            ],
            details={
                'buildings_detected': list(buildings),
                'naming_pattern': 'building_level_room.csv' if has_levels else 'building_room.csv'
            }
        )
    
    def _detect_hybrid_climate_files(
        self, 
        data_dir: Path, 
        subdirs: List[Path], 
        csv_files: List[Path]
    ) -> StructureAnalysis:
        """Detect hybrid structure with climate_*.csv in building folders."""
        if not subdirs:
            return self._empty_analysis()
        
        building_count = 0
        total_sensor_files = 0
        has_climate = False
        
        for building_dir in subdirs:
            if not self._is_building_folder(building_dir):
                continue
            
            # Get all CSV files in building directory
            building_csvs = list(building_dir.glob("*.csv"))
            if not building_csvs:
                continue
            
            climate_count = 0
            sensor_count = 0
            
            for csv_file in building_csvs:
                filename = csv_file.stem.lower()
                if any(pattern in filename for pattern in self.climate_patterns):
                    climate_count += 1
                else:
                    sensor_count += 1
            
            if sensor_count > 0:
                building_count += 1
                total_sensor_files += sensor_count
                if climate_count > 0:
                    has_climate = True
        
        if building_count == 0:
            return self._empty_analysis()
        
        confidence = 0.7  # Lower confidence as this is a less standard structure
        
        return StructureAnalysis(
            structure_type=DirectoryStructureType.HYBRID_CLIMATE_FILES,
            confidence=confidence,
            building_count=building_count,
            total_sensor_files=total_sensor_files,
            has_climate_data=has_climate,
            issues=[],
            recommendations=[
                "Consider separating climate files into building/climate/ subdirectory",
                "Consider moving sensor files into building/sensors/ subdirectory"
            ],
            details={
                'subdirectories': len(subdirs),
                'structure': 'building/*.csv (mixed climate and sensor files)'
            }
        )
    
    def _is_building_folder(self, folder: Path) -> bool:
        """Check if a folder name looks like a building folder."""
        folder_name = folder.name.lower()
        
        # Check against patterns
        for pattern in self.building_folder_patterns:
            if re.match(pattern, folder_name):
                return True
        
        # Also accept any folder name (permissive approach)
        # This allows custom building names
        return True
    
    def _is_climate_file(self, filename: str) -> bool:
        """Check if a filename looks like a climate data file."""
        filename_lower = filename.lower()
        return any(pattern in filename_lower for pattern in self.climate_patterns)
    
    def _empty_analysis(self) -> StructureAnalysis:
        """Return an empty analysis with zero confidence."""
        return StructureAnalysis(
            structure_type=DirectoryStructureType.UNKNOWN,
            confidence=0.0,
            building_count=0,
            total_sensor_files=0,
            has_climate_data=False,
            issues=[],
            recommendations=[],
            details={}
        )
    
    def _create_unknown_analysis(
        self, 
        data_dir: Path, 
        subdirs: List[Path], 
        csv_files: List[Path]
    ) -> StructureAnalysis:
        """Create analysis for unknown structure with recommendations."""
        issues = []
        recommendations = []
        
        if not subdirs and not csv_files:
            issues.append("Directory is empty")
            recommendations.append("Add building data to this directory")
        elif not subdirs:
            issues.append("No building subdirectories found")
            recommendations.append(
                "Organize CSV files into building folders: "
                "data_dir/building-1/sensors/*.csv"
            )
        elif not csv_files:
            # Has subdirs but couldn't detect structure
            issues.append("Could not detect a supported directory structure")
            recommendations.extend([
                "Expected structure: data_dir/building-X/sensors/*.csv",
                "Optional: data_dir/building-X/climate/*.csv for climate data",
                "Alternative: Use building_room.csv naming in a single folder"
            ])
        
        return StructureAnalysis(
            structure_type=DirectoryStructureType.UNKNOWN,
            confidence=0.0,
            building_count=0,
            total_sensor_files=0,
            has_climate_data=False,
            issues=issues,
            recommendations=recommendations,
            details={
                'subdirectories_found': len(subdirs),
                'csv_files_found': len(csv_files)
            }
        )
    
    def get_reorganization_guide(self, analysis: StructureAnalysis) -> str:
        """
        Get a detailed guide for reorganizing data to the standard structure.
        
        Args:
            analysis: The structure analysis result
        
        Returns:
            Formatted string with reorganization instructions
        """
        if analysis.structure_type == DirectoryStructureType.NESTED_BUILDING_SENSORS:
            return "✓ Your data structure is already in the recommended format!"
        
        guide = """
╔══════════════════════════════════════════════════════════════════════╗
║              DATA ORGANIZATION GUIDE                                  ║
╚══════════════════════════════════════════════════════════════════════╝

RECOMMENDED STRUCTURE:
┌────────────────────────────────────────────────────────────────────┐
│ data_directory/                                                     │
│ ├── building-1/                                                     │
│ │   ├── climate/                    (optional)                      │
│ │   │   └── climate-data.csv                                        │
│ │   └── sensors/                    (required)                      │
│ │       ├── room1.csv                                               │
│ │       ├── room2.csv                                               │
│ │       └── ...                                                     │
│ ├── building-2/                                                     │
│ │   └── sensors/                                                    │
│ │       └── ...                                                     │
│ └── ...                                                             │
└────────────────────────────────────────────────────────────────────┘
"""
        
        if analysis.structure_type == DirectoryStructureType.FLAT_BUILDING_PREFIX:
            guide += """
YOUR CURRENT STRUCTURE: Flat with building prefix
  • Files: building_room.csv

REORGANIZATION STEPS:
  1. Create a folder for each building (e.g., building-1/)
  2. Create a 'sensors' subfolder inside each building folder
  3. Move room CSV files into the appropriate building's sensors/ folder
  4. Rename files to remove building prefix (e.g., building1_room.csv → room.csv)

EXAMPLE COMMANDS (macOS/Linux):
  mkdir -p building-1/sensors
  mv building1_*.csv building-1/sensors/
  cd building-1/sensors && for f in building1_*.csv; do mv "$f" "${f#building1_}"; done
"""
        
        elif analysis.structure_type == DirectoryStructureType.FLAT_BUILDING_LEVEL_PREFIX:
            guide += """
YOUR CURRENT STRUCTURE: Flat with building_level prefix
  • Files: building_level_room.csv

REORGANIZATION STEPS:
  1. Create a folder for each building (e.g., building-1/)
  2. Create a 'sensors' subfolder inside each building folder
  3. Move room CSV files into the appropriate building's sensors/ folder
  4. Rename files to remove building/level prefix
  5. Note: Level information will be auto-inferred from room names

EXAMPLE COMMANDS (macOS/Linux):
  mkdir -p building-1/sensors
  mv building1_*.csv building-1/sensors/
  cd building-1/sensors && for f in building1_*_*.csv; do mv "$f" "${f#building1_*_}"; done
"""
        
        elif analysis.structure_type == DirectoryStructureType.HYBRID_CLIMATE_FILES:
            guide += """
YOUR CURRENT STRUCTURE: Hybrid with climate files in building folders
  • Structure: building/*.csv (mixed)

REORGANIZATION STEPS:
  1. Create 'sensors' subfolder in each building folder
  2. Create 'climate' subfolder in each building folder (if climate files exist)
  3. Move sensor CSV files to sensors/ subfolder
  4. Move climate CSV files to climate/ subfolder

EXAMPLE COMMANDS (macOS/Linux):
  cd building-1
  mkdir -p sensors climate
  mv *climate*.csv climate/
  mv *.csv sensors/
"""
        
        elif analysis.structure_type == DirectoryStructureType.NESTED_FULL:
            guide += """
YOUR CURRENT STRUCTURE: Nested with level folders
  • Structure: building/level/*.csv

REORGANIZATION STEPS:
  1. Create a 'sensors' folder in each building directory
  2. Move all room CSV files from level folders into the sensors/ folder
  3. Ensure room files are named to preserve level information
     (e.g., level1_room.csv or use level prefixes in room names)

EXAMPLE COMMANDS (macOS/Linux):
  cd building-1
  mkdir -p sensors
  find . -name "*.csv" -not -path "./sensors/*" -exec mv {} sensors/ \\;
"""
        
        else:
            guide += """
CURRENT STRUCTURE: Unknown or unsupported

REORGANIZATION STEPS:
  1. Identify your building data files (CSV files with sensor data)
  2. Identify your climate data files (optional)
  3. Create the recommended structure:
     - One folder per building
     - A 'sensors' subfolder in each building folder
     - Optionally, a 'climate' subfolder for weather data
  4. Move your files accordingly

If you're unsure, please provide examples of your current file structure.
"""
        
        guide += """
NOTES:
  • Building folders can have any name (not just 'building-1')
  • Room CSV files should contain: timestamp, temperature, co2, humidity columns
  • Climate CSV files should contain: timestamp, temperature, humidity, etc.
  • Level information will be auto-inferred from room names (e.g., '1. sal', 'floor_2')
  • Room types will be auto-inferred from names (e.g., 'office', 'classroom')

NEED HELP?
  Run the interactive workflow with: hvx start
  Or see documentation: docs/QUICKSTART.md
"""
        
        return guide


def create_structure_detector() -> DataStructureDetector:
    """Factory function to create a DataStructureDetector instance."""
    return DataStructureDetector()
