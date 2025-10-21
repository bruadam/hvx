"""TAIL parameter configurations loaded from YAML configuration files.

This module provides configuration data types and loading mechanisms for TAIL
parameters. All configuration values are loaded from YAML files, ensuring
centralized management of thresholds and settings.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from .building_type import BuildingType
from .parameter_type import ParameterType
from .room_type import RoomType


@dataclass
class ParameterThreshold:
    """Threshold configuration for a parameter."""

    green_min: Optional[float] = None
    green_max: Optional[float] = None
    yellow_min: Optional[float] = None
    yellow_max: Optional[float] = None
    orange_min: Optional[float] = None
    orange_max: Optional[float] = None
    red_condition: Optional[str] = None  # Special condition for red category

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterThreshold":
        """Create ParameterThreshold from dictionary."""
        if not data:
            return cls()
        return cls(
            green_min=data.get("green", {}).get("min"),
            green_max=data.get("green", {}).get("max"),
            yellow_min=data.get("yellow", {}).get("min"),
            yellow_max=data.get("yellow", {}).get("max"),
            orange_min=data.get("orange", {}).get("min"),
            orange_max=data.get("orange", {}).get("max"),
            red_condition=data.get("red", {}).get("condition"),
        )


@dataclass
class TAILParameterConfig:
    """Configuration for a TAIL parameter including building type specific thresholds."""

    parameter: ParameterType
    building_type: BuildingType
    thresholds: ParameterThreshold
    calculation_method: str = "direct"  # direct, percentile, frequency
    percentile: Optional[float] = None  # For CO2 95th percentile
    frequency_based: bool = False  # For parameters requiring frequency analysis
    room_type_dependent: bool = False  # For noise parameters

    @classmethod
    def from_dict(
        cls,
        parameter: ParameterType,
        building_type: BuildingType,
        data: Dict[str, Any],
    ) -> "TAILParameterConfig":
        """Create TAILParameterConfig from dictionary."""
        if not data:
            return cls(
                parameter=parameter,
                building_type=building_type,
                thresholds=ParameterThreshold(),
            )

        return cls(
            parameter=parameter,
            building_type=building_type,
            thresholds=ParameterThreshold.from_dict(data.get("thresholds", {})),
            calculation_method=data.get("calculation_method", "direct"),
            percentile=data.get("percentile"),
            frequency_based=data.get("frequency_based", False),
            room_type_dependent=data.get("room_type_dependent", False),
        )


class TAILConfigLoader:
    """Loads and manages hierarchical TAIL configuration with validation."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the configuration loader.

        Args:
            config_dir: Path to TAIL configuration directory. If None, uses default.
            
        Raises:
            ImportError: If PyYAML is not installed.
        """
        if yaml is None:
            raise ImportError(
                "PyYAML is required for configuration loading. "
                "Install it with: pip install pyyaml"
            )
            
        if config_dir is None:
            # Default to TAIL standards directory relative to this file
            self.config_dir = (
                Path(__file__).parent.parent.parent.parent
                / "config"
                / "standards"
                / "tail"
            )
        else:
            self.config_dir = Path(config_dir)

        self._default_config: Dict[str, Any] = {}
        self._building_overrides: Dict[str, Dict[str, Any]] = {}
        self._room_overrides: Dict[str, Dict[str, Any]] = {}

    def load_default_config(self) -> Dict[str, Any]:
        """Load the default TAIL configuration."""
        if not self._default_config:
            config_path = self.config_dir / "tail_schema.yaml"
            with open(config_path) as f:
                loaded = yaml.safe_load(f)
                self._default_config = loaded if loaded is not None else {}
        return self._default_config

    def load_building_override(self, building_type: BuildingType) -> Dict[str, Any]:
        """Load building-specific configuration overrides."""
        if building_type.value not in self._building_overrides:
            override_path = (
                self.config_dir
                / "overrides"
                / "building_types"
                / f"{building_type.value}.yaml"
            )
            if override_path.exists():
                with open(override_path) as f:
                    self._building_overrides[building_type.value] = yaml.safe_load(f)
            else:
                self._building_overrides[building_type.value] = {}
        return self._building_overrides[building_type.value]

    def load_room_override(self, room_type: RoomType) -> Dict[str, Any]:
        """Load room-specific configuration overrides."""
        if room_type.value not in self._room_overrides:
            override_path = (
                self.config_dir / "overrides" / "room_types" / f"{room_type.value}.yaml"
            )
            if override_path.exists():
                with open(override_path) as f:
                    self._room_overrides[room_type.value] = yaml.safe_load(f)
            else:
                self._room_overrides[room_type.value] = {}
        return self._room_overrides[room_type.value]

    def get_parameter_config(
        self,
        parameter: ParameterType,
        building_type: Optional[BuildingType] = None,
        room_type: Optional[RoomType] = None,
    ) -> Dict[str, Any]:
        """Get configuration for a parameter with hierarchical overrides.

        Priority: room_type > building_type > default

        Args:
            parameter: The parameter to get configuration for
            building_type: Building type for building-specific overrides
            room_type: Room type for room-specific overrides (highest priority)

        Returns:
            Merged configuration dictionary
        """
        # Validate parameter
        if not isinstance(parameter, ParameterType):
            raise ValueError(f"Invalid parameter type: {parameter}")

        # Validate building type if provided
        if building_type is not None and not isinstance(building_type, BuildingType):
            raise ValueError(f"Invalid building type: {building_type}")

        # Validate room type if provided
        if room_type is not None and not isinstance(room_type, RoomType):
            raise ValueError(f"Invalid room type: {room_type}")

        # Start with default configuration
        default_config = self.load_default_config()
        param_config = (
            default_config.get("tail_config", {})
            .get("default_parameters", {})
            .get(parameter.value, {})
            .copy()
        )

        # Apply building-specific overrides
        if building_type is not None:
            building_override = self.load_building_override(building_type)
            if "parameter_overrides" in building_override:
                building_param_override = building_override["parameter_overrides"].get(
                    parameter.value, {}
                )
                param_config = self._deep_merge(param_config, building_param_override)

        # Apply room-specific overrides (highest priority)
        if room_type is not None:
            room_override = self.load_room_override(room_type)
            if "parameter_overrides" in room_override:
                room_param_override = room_override["parameter_overrides"].get(
                    parameter.value, {}
                )
                param_config = self._deep_merge(param_config, room_param_override)

        return param_config

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = TAILConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def validate_configuration(self) -> bool:
        """Validate all configuration files against enum types."""
        errors = []

        # Validate default config
        try:
            default_config = self.load_default_config()
            for param_name in default_config.get("tail_config", {}).get(
                "default_parameters", {}
            ):
                try:
                    ParameterType(param_name)
                except ValueError:
                    errors.append(f"Invalid parameter '{param_name}' in default config")
        except Exception as e:
            errors.append(f"Error loading default config: {e}")

        # Validate building overrides
        building_overrides_dir = self.config_dir / "overrides" / "building_types"
        if building_overrides_dir.exists():
            for override_file in building_overrides_dir.glob("*.yaml"):
                building_name = override_file.stem
                try:
                    BuildingType(building_name)
                except ValueError:
                    errors.append(
                        f"Invalid building type '{building_name}' in override file"
                    )

                # Validate parameters in override
                try:
                    with open(override_file) as f:
                        override_config = yaml.safe_load(f)
                    if "parameter_overrides" in override_config:
                        for param_name in override_config["parameter_overrides"]:
                            try:
                                ParameterType(param_name)
                            except ValueError:
                                errors.append(
                                    f"Invalid parameter '{param_name}' in {override_file}"
                                )
                except Exception as e:
                    errors.append(f"Error loading {override_file}: {e}")

        # Validate room overrides
        room_overrides_dir = self.config_dir / "overrides" / "room_types"
        if room_overrides_dir.exists():
            for override_file in room_overrides_dir.glob("*.yaml"):
                room_name = override_file.stem
                try:
                    RoomType(room_name)
                except ValueError:
                    errors.append(
                        f"Invalid room type '{room_name}' in override file"
                    )

                # Validate parameters in override
                try:
                    with open(override_file) as f:
                        override_config = yaml.safe_load(f)
                    if "parameter_overrides" in override_config:
                        for param_name in override_config["parameter_overrides"]:
                            try:
                                ParameterType(param_name)
                            except ValueError:
                                errors.append(
                                    f"Invalid parameter '{param_name}' in {override_file}"
                                )
                except Exception as e:
                    errors.append(f"Error loading {override_file}: {e}")

        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("Configuration validation successful!")
        return True

    def get_supported_combinations(self) -> Dict[str, Any]:
        """Get all supported building type and room type combinations."""
        combinations = {
            "building_types": [],
            "room_types": [],
            "valid_combinations": [],
        }

        # Get available building types
        building_overrides_dir = self.config_dir / "overrides" / "building_types"
        if building_overrides_dir.exists():
            for override_file in building_overrides_dir.glob("*.yaml"):
                building_name = override_file.stem
                try:
                    building_type = BuildingType(building_name)
                    combinations["building_types"].append(building_type.value)
                except ValueError:
                    continue

        # Get available room types
        room_overrides_dir = self.config_dir / "overrides" / "room_types"
        if room_overrides_dir.exists():
            for override_file in room_overrides_dir.glob("*.yaml"):
                room_name = override_file.stem
                try:
                    room_type = RoomType(room_name)
                    combinations["room_types"].append(room_type.value)
                except ValueError:
                    continue

        # Define logical combinations
        logical_combinations = [
            ("office", "small_office"),
            ("office", "open_office"),
            ("hotel", "hotel_room"),
        ]

        for building, room in logical_combinations:
            if (
                building in combinations["building_types"]
                and room in combinations["room_types"]
            ):
                combinations["valid_combinations"].append(
                    {"building_type": building, "room_type": room}
                )

        return combinations


# Global instance for easy access
tail_config_loader = TAILConfigLoader()


class TAILConfig:
    """TAIL configuration accessor providing building-specific parameter thresholds.

    This class provides a clean interface to access TAIL configurations loaded
    from YAML files. All configuration values come from the YAML schema,
    with no hardcoded defaults.
    """

    @classmethod
    def get_parameter_config(
        cls,
        parameter: ParameterType,
        building_type: BuildingType,
    ) -> Optional[TAILParameterConfig]:
        """Get configuration for a specific parameter and building type.

        Args:
            parameter: The TAIL parameter
            building_type: The building type

        Returns:
            TAILParameterConfig or None if not configured
        """
        try:
            config_dict = tail_config_loader.get_parameter_config(
                parameter, building_type
            )
            if config_dict:
                return TAILParameterConfig.from_dict(
                    parameter, building_type, config_dict
                )
            return None
        except (FileNotFoundError, KeyError, ValueError) as e:
            raise ValueError(
                f"Failed to load configuration for {parameter.value} in {building_type.value}: {e}"
            )

    @classmethod
    def get_supported_parameters(
        cls, building_type: BuildingType
    ) -> List[ParameterType]:
        """Get all parameters supported for a specific building type.

        Args:
            building_type: The building type

        Returns:
            List of supported ParameterType values
        """
        try:
            default_config = tail_config_loader.load_default_config()
            building_override = tail_config_loader.load_building_override(building_type)

            # Collect all parameter names from default and building-specific config
            params = set(
                default_config.get("tail_config", {})
                .get("default_parameters", {})
                .keys()
            )
            params.update(
                building_override.get("parameter_overrides", {}).keys()
            )

            # Convert to ParameterType enum values
            return [ParameterType(p) for p in params if p in ParameterType.__members__]
        except Exception as e:
            raise ValueError(f"Failed to get supported parameters: {e}")

    @classmethod
    def is_parameter_supported(
        cls, parameter: ParameterType, building_type: BuildingType
    ) -> bool:
        """Check if a parameter is supported for a specific building type.

        Args:
            parameter: The TAIL parameter
            building_type: The building type

        Returns:
            True if the parameter is supported for this building type
        """
        return cls.get_parameter_config(parameter, building_type) is not None