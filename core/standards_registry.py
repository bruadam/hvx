"""
Standards and Simulations Registry

This module provides a registry system for standards and simulations,
along with logic to determine applicability based on entity properties.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import yaml

from .enums import SpatialEntityType


@dataclass
class StandardConfig:
    """Configuration for a standard loaded from YAML."""
    
    id: str
    name: str
    version: str
    standard_type: str
    description: str
    category_based: bool
    
    # Applicability criteria
    countries: Optional[List[str]]
    regions: Optional[List[str]]
    building_types: Optional[List[str]]
    ventilation_types: Optional[List[str]]
    seasons: Optional[List[str]]
    
    # Required inputs for this standard
    required_inputs: Dict[str, Any]
    
    # Analysis module path
    analysis_module: str
    
    # Full config data
    config_data: Dict[str, Any]
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> StandardConfig:
        """Load a standard configuration from a YAML file."""
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        applicability = config.get('applicability', {})
        
        return cls(
            id=config['id'],
            name=config['name'],
            version=config['version'],
            standard_type=config.get('standard_type', ''),
            description=config.get('description', ''),
            category_based=config.get('category_based', False),
            countries=applicability.get('countries'),
            regions=applicability.get('regions'),
            building_types=applicability.get('building_types'),
            ventilation_types=applicability.get('ventilation_types'),
            seasons=applicability.get('seasons'),
            required_inputs=config.get('required_inputs', {}),
            analysis_module=config.get('analysis_module', ''),
            config_data=config,
        )
    
    def is_applicable(
        self,
        country: Optional[str] = None,
        region: Optional[str] = None,
        building_type: Optional[str] = None,
        room_type: Optional[str] = None,
        ventilation_type: Optional[str] = None,
        season: Optional[str] = None,
    ) -> bool:
        """
        Check if this standard is applicable based on entity properties.
        
        Args:
            country: Country code (e.g., 'DK', 'DE')
            region: Region name (e.g., 'Europe', 'Nordic')
            building_type: Building type (e.g., 'office', 'school')
            room_type: Room type (e.g., 'classroom', 'meeting_room')
            ventilation_type: Ventilation type (e.g., 'natural', 'mechanical')
            season: Season (e.g., 'winter', 'summer', 'all_year')
        
        Returns:
            True if standard is applicable, False otherwise
        """
        # Check country
        if self.countries is not None and country:
            if country not in self.countries:
                return False
        
        # Check region
        if self.regions is not None and region:
            if region not in self.regions:
                return False
        
        # Check building type
        if self.building_types is not None:
            # Check both building_type and room_type
            types_to_check = []
            if building_type:
                types_to_check.append(building_type)
            if room_type:
                types_to_check.append(room_type)
            
            if types_to_check:
                # If any type matches, it's applicable
                if not any(t in self.building_types for t in types_to_check):
                    return False
        
        # Check ventilation type
        if self.ventilation_types is not None and ventilation_type:
            if ventilation_type not in self.ventilation_types:
                return False
        
        # Check season
        if self.seasons is not None and season:
            # 'all_year' matches any season
            if 'all_year' not in self.seasons and season not in self.seasons:
                return False
        
        return True
    
    def has_required_data(self, available_metrics: Set[str]) -> bool:
        """
        Check if the available metrics satisfy the required inputs.
        
        Args:
            available_metrics: Set of available metric names
        
        Returns:
            True if all required inputs are available
        """
        if not self.required_inputs:
            return True
        
        # Handle nested required inputs (like TAIL's domain structure)
        if isinstance(self.required_inputs, dict):
            for key, value in self.required_inputs.items():
                if isinstance(value, dict):
                    # Nested structure - check if at least one required metric is available
                    required_count = sum(1 for req in value.values() if req is True)
                    available_count = sum(1 for metric in value.keys() if value.get(metric) and metric in available_metrics)
                    if required_count > 0 and available_count == 0:
                        return False
                elif value is True:
                    # Top-level required input
                    if key not in available_metrics:
                        return False
        
        return True


@dataclass
class SimulationConfig:
    """Configuration for a simulation model."""
    
    id: str
    name: str
    description: str
    module_path: str
    
    # Applicability
    entity_types: List[str]  # ['room', 'building', etc.]
    required_metrics: List[str]
    optional_metrics: List[str]
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> SimulationConfig:
        """Create from dictionary configuration."""
        return cls(
            id=config['id'],
            name=config['name'],
            description=config.get('description', ''),
            module_path=config['module_path'],
            entity_types=config.get('entity_types', ['room']),
            required_metrics=config.get('required_metrics', []),
            optional_metrics=config.get('optional_metrics', []),
        )
    
    def is_applicable(
        self,
        entity_type: SpatialEntityType,
        available_metrics: Set[str],
    ) -> bool:
        """
        Check if this simulation is applicable.
        
        Args:
            entity_type: Type of spatial entity
            available_metrics: Available metrics for the entity
        
        Returns:
            True if simulation is applicable
        """
        # Check entity type
        entity_type_str = entity_type.value.lower() if hasattr(entity_type, 'value') else str(entity_type).lower()
        if entity_type_str not in self.entity_types:
            return False
        
        # Check required metrics
        for metric in self.required_metrics:
            if metric not in available_metrics:
                return False
        
        return True


class AnalysisRegistry:
    """Registry for standards and simulations."""
    
    def __init__(self):
        self.standards: Dict[str, StandardConfig] = {}
        self.simulations: Dict[str, SimulationConfig] = {}
        self._initialized = False
    
    def initialize(self, standards_root: Optional[Path] = None):
        """
        Initialize the registry by scanning for standard configurations.
        
        Args:
            standards_root: Root directory containing standards. If None, auto-detect.
        """
        if self._initialized:
            return
        
        if standards_root is None:
            # Auto-detect standards directory
            current_file = Path(__file__).resolve()
            standards_root = current_file.parent.parent / "standards"
        
        if not standards_root.exists():
            return
        
        # Scan for standard configurations
        for config_file in standards_root.rglob("config.yaml"):
            try:
                standard_config = StandardConfig.from_yaml(config_file)
                self.standards[standard_config.id] = standard_config
            except Exception as e:
                print(f"Warning: Could not load standard config from {config_file}: {e}")
        
        # Register simulations
        self._register_default_simulations()
        
        self._initialized = True
    
    def _register_default_simulations(self):
        """Register built-in simulation models."""
        # Occupancy simulation
        self.simulations['occupancy'] = SimulationConfig(
            id='occupancy',
            name='Occupancy Detection',
            description='Detect occupancy patterns from CO2 data',
            module_path='simulations.models.occupancy:OccupancyCalculator',
            entity_types=['room'],
            required_metrics=['co2'],
            optional_metrics=['temperature', 'humidity'],
        )
        
        # Ventilation simulation
        self.simulations['ventilation'] = SimulationConfig(
            id='ventilation',
            name='Ventilation Analysis',
            description='Analyze ventilation effectiveness',
            module_path='simulations.models.ventilation:VentilationCalculator',
            entity_types=['room'],
            required_metrics=['co2'],
            optional_metrics=['outdoor_co2'],
        )
    
    def get_applicable_standards(
        self,
        country: Optional[str] = None,
        region: Optional[str] = None,
        building_type: Optional[str] = None,
        room_type: Optional[str] = None,
        ventilation_type: Optional[str] = None,
        season: Optional[str] = None,
        available_metrics: Optional[Set[str]] = None,
    ) -> List[StandardConfig]:
        """
        Get all applicable standards based on entity properties.
        
        Args:
            country: Country code
            region: Region name
            building_type: Building type
            room_type: Room type
            ventilation_type: Ventilation type
            season: Season
            available_metrics: Available metrics
        
        Returns:
            List of applicable StandardConfig objects
        """
        if not self._initialized:
            self.initialize()
        
        applicable = []
        
        for standard in self.standards.values():
            # Check applicability criteria
            is_appl = standard.is_applicable(
                country=country,
                region=region,
                building_type=building_type,
                room_type=room_type,
                ventilation_type=ventilation_type,
                season=season,
            )
            if not is_appl:
                continue
            
            # Check required data
            if available_metrics is not None:
                has_data = standard.has_required_data(available_metrics)
                if not has_data:
                    continue
            
            applicable.append(standard)
        
        return applicable
    
    def get_applicable_simulations(
        self,
        entity_type: SpatialEntityType,
        available_metrics: Set[str],
    ) -> List[SimulationConfig]:
        """
        Get all applicable simulations for an entity.
        
        Args:
            entity_type: Type of spatial entity
            available_metrics: Available metrics
        
        Returns:
            List of applicable SimulationConfig objects
        """
        if not self._initialized:
            self.initialize()
        
        applicable = []
        
        for simulation in self.simulations.values():
            if simulation.is_applicable(entity_type, available_metrics):
                applicable.append(simulation)
        
        return applicable
    
    def load_analysis_module(self, module_path: str) -> Callable:
        """
        Load and return the analysis function from a module path.
        
        Args:
            module_path: Module path like "standards.en16798.analysis:run"
        
        Returns:
            The analysis function
        """
        module_name, function_name = module_path.split(':')
        module = importlib.import_module(module_name)
        return getattr(module, function_name)
    
    def load_simulation_class(self, module_path: str) -> type:
        """
        Load and return the simulation class from a module path.
        
        Args:
            module_path: Module path like "simulations.models.occupancy:OccupancyCalculator"
        
        Returns:
            The simulation class
        """
        module_name, class_name = module_path.split(':')
        module = importlib.import_module(module_name)
        return getattr(module, class_name)


# Global registry instance
_registry = AnalysisRegistry()


def get_registry() -> AnalysisRegistry:
    """Get the global analysis registry."""
    if not _registry._initialized:
        _registry.initialize()
    return _registry


__all__ = [
    "StandardConfig",
    "SimulationConfig",
    "AnalysisRegistry",
    "get_registry",
]
