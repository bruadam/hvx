"""
Dynamic Standard Registry

Automatically discovers and registers available IEQ standards from configuration files.
Supports dynamic addition of new standards without code changes.

Design Principles:
- Dynamic discovery: Automatically finds all standard configuration files
- Extensible: Add new standards by simply adding YAML files
- Type-safe: Provides enums and type hints for standards
"""

import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from dataclasses import dataclass
import yaml

logger = logging.getLogger(__name__)


@dataclass
class StandardInfo:
    """Information about a discovered standard."""
    
    id: str  # Unique identifier (e.g., "en16798-1", "br18")
    name: str  # Display name
    description: str  # Human-readable description
    rules: List[str]  # List of rule identifiers
    config_dir: Path  # Path to standard config directory
    category: str  # Category/classification


class StandardRegistry:
    """
    Registry for dynamically discovered IEQ standards.
    
    Automatically scans standard configuration directories and builds
    a registry of available standards and their rules.
    """
    
    def __init__(self, config_base_dir: Optional[Path] = None):
        """
        Initialize registry and discover standards.
        
        Args:
            config_base_dir: Base directory for standard configs
                           If None, uses default location
        """
        if config_base_dir is None:
            # Default to standards directory in config
            module_dir = Path(__file__).parent
            config_base_dir = module_dir / "config" / "standards"
        
        self.config_base_dir = Path(config_base_dir)
        self.standards: Dict[str, StandardInfo] = {}
        self.rules_by_standard: Dict[str, List[str]] = {}
        self.all_rules: Dict[str, Dict[str, Any]] = {}
        
        # Discover standards on initialization
        self._discover_standards()
    
    def _discover_standards(self):
        """
        Discover all available standards by scanning config directories.
        
        This method scans the standards directory structure and automatically
        registers all found standards.
        """
        if not self.config_base_dir.exists():
            logger.warning(f"Standards config directory not found: {self.config_base_dir}")
            return
        
        logger.info(f"Discovering standards in {self.config_base_dir}")
        
        # Scan for standard directories
        for standard_dir in self.config_base_dir.iterdir():
            if not standard_dir.is_dir():
                continue
            
            # Register this standard
            standard_id = standard_dir.name
            self._register_standard(standard_id, standard_dir)
        
        logger.info(f"Discovered {len(self.standards)} standards with {len(self.all_rules)} total rules")
    
    def _register_standard(self, standard_id: str, standard_dir: Path):
        """
        Register a single standard and its rules.
        
        Args:
            standard_id: Standard identifier (e.g., "en16798-1")
            standard_dir: Path to standard config directory
        """
        rules = []
        
        # Scan for YAML rule files
        for rule_file in standard_dir.glob("*.yaml"):
            try:
                rule_config = self._load_rule_config(rule_file)
                if rule_config:
                    # Create rule ID from standard and filename
                    rule_name = rule_file.stem
                    rule_id = f"{standard_id}_{rule_name}"
                    
                    # Store rule configuration
                    self.all_rules[rule_id] = {
                        **rule_config,
                        'standard_id': standard_id,
                        'rule_name': rule_name,
                        'config_file': str(rule_file)
                    }
                    
                    rules.append(rule_id)
            
            except Exception as e:
                logger.error(f"Error loading rule from {rule_file}: {e}")
        
        if rules:
            # Create standard info
            standard_info = StandardInfo(
                id=standard_id,
                name=self._format_standard_name(standard_id),
                description=f"{self._format_standard_name(standard_id)} compliance rules",
                rules=rules,
                config_dir=standard_dir,
                category=self._categorize_standard(standard_id)
            )
            
            self.standards[standard_id] = standard_info
            self.rules_by_standard[standard_id] = rules
            
            logger.debug(f"Registered standard '{standard_id}' with {len(rules)} rules")
    
    def _load_rule_config(self, rule_file: Path) -> Optional[Dict[str, Any]]:
        """
        Load rule configuration from YAML file.
        
        Args:
            rule_file: Path to rule YAML file
        
        Returns:
            Rule configuration dictionary or None if invalid
        """
        try:
            with open(rule_file, 'r') as f:
                config = yaml.safe_load(f)
                
                # Validate required fields
                if not isinstance(config, dict):
                    logger.warning(f"Invalid config format in {rule_file}")
                    return None
                
                # Must have at least a feature/parameter
                if 'feature' not in config and 'parameter' not in config:
                    logger.warning(f"Missing feature/parameter in {rule_file}")
                    return None
                
                return config
        
        except Exception as e:
            logger.error(f"Error loading {rule_file}: {e}")
            return None
    
    def _format_standard_name(self, standard_id: str) -> str:
        """
        Format standard ID into display name.
        
        Args:
            standard_id: Standard identifier (e.g., "en16798-1")
        
        Returns:
            Formatted name (e.g., "EN16798-1")
        """
        # Handle special cases
        if standard_id.startswith('en'):
            return standard_id.upper()
        elif standard_id.startswith('br'):
            return standard_id.upper()
        else:
            # Title case for others
            return standard_id.replace('-', ' ').replace('_', ' ').title()
    
    def _categorize_standard(self, standard_id: str) -> str:
        """
        Categorize standard by type.
        
        Args:
            standard_id: Standard identifier
        
        Returns:
            Category string
        """
        if 'en' in standard_id.lower():
            return "European Standard"
        elif 'br' in standard_id.lower():
            return "Building Regulation"
        elif 'danish' in standard_id.lower():
            return "National Guideline"
        else:
            return "Other"
    
    def get_standard_ids(self) -> List[str]:
        """
        Get list of all available standard IDs.
        
        Returns:
            List of standard identifiers
        
        Example:
            >>> registry = StandardRegistry()
            >>> standards = registry.get_standard_ids()
            >>> 'en16798-1' in standards
            True
        """
        return sorted(self.standards.keys())
    
    def get_standard_info(self, standard_id: str) -> Optional[StandardInfo]:
        """
        Get information about a specific standard.
        
        Args:
            standard_id: Standard identifier
        
        Returns:
            StandardInfo object or None if not found
        
        Example:
            >>> registry = StandardRegistry()
            >>> info = registry.get_standard_info('en16798-1')
            >>> info.name
            'EN16798-1'
        """
        return self.standards.get(standard_id)
    
    def get_rules_for_standard(self, standard_id: str) -> List[str]:
        """
        Get all rules for a specific standard.
        
        Args:
            standard_id: Standard identifier
        
        Returns:
            List of rule IDs
        
        Example:
            >>> registry = StandardRegistry()
            >>> rules = registry.get_rules_for_standard('en16798-1')
            >>> len(rules) > 0
            True
        """
        return self.rules_by_standard.get(standard_id, [])
    
    def get_rule_config(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific rule.
        
        Args:
            rule_id: Full rule identifier (e.g., "en16798-1_cat_i_temp_heating_season")
        
        Returns:
            Rule configuration dictionary or None
        
        Example:
            >>> registry = StandardRegistry()
            >>> config = registry.get_rule_config('en16798-1_cat_i_temp_heating_season')
            >>> config['feature']
            'temperature'
        """
        return self.all_rules.get(rule_id)
    
    def get_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all rule configurations.
        
        Returns:
            Dictionary mapping rule IDs to configurations
        """
        return self.all_rules.copy()
    
    def filter_rules(
        self,
        standard_ids: Optional[List[str]] = None,
        parameter: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[str]:
        """
        Filter rules by criteria.
        
        Args:
            standard_ids: Filter by specific standards
            parameter: Filter by parameter (e.g., "temperature", "co2")
            category: Filter by category
        
        Returns:
            List of matching rule IDs
        
        Example:
            >>> registry = StandardRegistry()
            >>> temp_rules = registry.filter_rules(parameter='temperature')
            >>> len(temp_rules) > 0
            True
        """
        matching_rules = []
        
        for rule_id, rule_config in self.all_rules.items():
            # Filter by standard
            if standard_ids:
                if rule_config['standard_id'] not in standard_ids:
                    continue
            
            # Filter by parameter
            if parameter:
                rule_param = rule_config.get('feature') or rule_config.get('parameter', '')
                if parameter.lower() not in str(rule_param).lower():
                    continue
            
            # Filter by category
            if category:
                if category.lower() not in str(rule_config.get('category', '')).lower():
                    continue
            
            matching_rules.append(rule_id)
        
        return matching_rules
    
    def get_standards_by_category(self) -> Dict[str, List[str]]:
        """
        Group standards by category.
        
        Returns:
            Dictionary mapping categories to standard IDs
        
        Example:
            >>> registry = StandardRegistry()
            >>> by_category = registry.get_standards_by_category()
            >>> 'European Standard' in by_category
            True
        """
        by_category: Dict[str, List[str]] = {}
        
        for standard_id, info in self.standards.items():
            category = info.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(standard_id)
        
        return by_category
    
    def create_standard_enum(self) -> type:
        """
        Dynamically create an Enum of available standards.
        
        Returns:
            Enum class with standard IDs as members
        
        Example:
            >>> registry = StandardRegistry()
            >>> StandardEnum = registry.create_standard_enum()
            >>> hasattr(StandardEnum, 'EN16798_1')
            True
        """
        # Create enum members
        members = {}
        for standard_id in self.standards.keys():
            # Convert to valid Python identifier
            enum_name = standard_id.upper().replace('-', '_').replace(' ', '_')
            members[enum_name] = standard_id
        
        # Create and return enum
        return Enum('DiscoveredStandards', members)
    
    def reload(self):
        """
        Reload standards from disk.
        
        Useful when new standards are added while system is running.
        """
        self.standards.clear()
        self.rules_by_standard.clear()
        self.all_rules.clear()
        self._discover_standards()
        logger.info("Standards registry reloaded")


# Global registry instance (lazy-loaded)
_global_registry: Optional[StandardRegistry] = None


def get_global_registry() -> StandardRegistry:
    """
    Get or create the global standard registry.
    
    Returns:
        Global StandardRegistry instance
    
    Example:
        >>> registry = get_global_registry()
        >>> len(registry.get_standard_ids()) > 0
        True
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = StandardRegistry()
    
    return _global_registry


def reload_global_registry():
    """Reload the global registry from disk."""
    global _global_registry
    
    if _global_registry is not None:
        _global_registry.reload()
    else:
        _global_registry = StandardRegistry()


__all__ = [
    'StandardRegistry',
    'StandardInfo',
    'get_global_registry',
    'reload_global_registry'
]
