"""Building type configuration loader."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class BuildingTypeConfig(BaseModel):
    """Configuration for a single building type."""

    display_name: str = Field(..., description="Human-readable display name")
    typical_occupancy_hours: dict[str, int] = Field(
        ...,
        description="Typical occupancy hours with 'start' and 'end' keys"
    )
    description: str = Field(default="", description="Building type description")
    supported: bool = Field(default=False, description="Whether fully supported")
    default_parameters: list[str] = Field(
        default_factory=list,
        description="Default parameters to monitor for this type"
    )

    @property
    def occupancy_hours_tuple(self) -> tuple[int, int]:
        """Get occupancy hours as tuple (start, end)."""
        start = self.typical_occupancy_hours.get("start", 8)
        end = self.typical_occupancy_hours.get("end", 18)
        return (start, end)

    @property
    def is_24_7(self) -> bool:
        """Check if this is a 24/7 facility."""
        start, end = self.occupancy_hours_tuple
        return start == 0 and end == 24


class BuildingTypeConfigLoader:
    """
    Loader for building type configurations.

    Supports loading from default config and user overrides.
    """

    _instance: Optional['BuildingTypeConfigLoader'] = None
    _configs: dict[str, BuildingTypeConfig] = {}

    def __new__(cls):
        """Singleton pattern to ensure single config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the config loader."""
        if not self._configs:
            self._load_default_configs()

    def _get_default_config_path(self) -> Path:
        """Get path to default building types config."""
        # Assume this file is in core/domain/enums/
        # Config is in config/building_types/
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        config_path = project_root / "config" / "building_types" / "default_building_types.yaml"
        return config_path

    def _load_yaml_config(self, config_path: Path) -> dict[str, BuildingTypeConfig]:
        """Load building type configs from YAML file."""
        if not config_path.exists():
            return {}

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)

            if not data:
                return {}

            configs = {}
            for building_type_id, config_data in data.items():
                if isinstance(config_data, dict):
                    try:
                        configs[building_type_id] = BuildingTypeConfig(**config_data)
                    except Exception as e:
                        print(f"Warning: Failed to load config for '{building_type_id}': {e}")

            return configs

        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return {}

    def _load_default_configs(self) -> None:
        """Load default building type configurations."""
        default_path = self._get_default_config_path()
        self._configs = self._load_yaml_config(default_path)

        if not self._configs:
            # Fallback to hardcoded defaults if config file not found
            self._configs = self._get_fallback_configs()

    def _get_fallback_configs(self) -> dict[str, BuildingTypeConfig]:
        """Get fallback configs if YAML loading fails."""
        return {
            "office": BuildingTypeConfig(
                display_name="Office",
                typical_occupancy_hours={"start": 8, "end": 18},
                description="Commercial office buildings",
                supported=True,
                default_parameters=["temperature", "co2", "humidity", "illuminance", "noise"]
            ),
            "hotel": BuildingTypeConfig(
                display_name="Hotel",
                typical_occupancy_hours={"start": 0, "end": 24},
                description="Hotel and hospitality buildings",
                supported=True,
                default_parameters=["temperature", "co2", "humidity", "noise"]
            ),
            "school": BuildingTypeConfig(
                display_name="School",
                typical_occupancy_hours={"start": 8, "end": 16},
                description="Educational facilities",
                supported=True,
                default_parameters=["temperature", "co2", "humidity", "illuminance", "noise"]
            ),
        }

    def load_user_config(self, config_path: Path) -> None:
        """
        Load user-defined building type configurations.

        User configs override default configs for matching building type IDs.

        Args:
            config_path: Path to user's building types YAML config file
        """
        user_configs = self._load_yaml_config(config_path)

        # Merge user configs with defaults (user overrides default)
        self._configs.update(user_configs)

    def get_config(self, building_type_id: str) -> BuildingTypeConfig | None:
        """
        Get configuration for a building type.

        Args:
            building_type_id: Building type identifier (e.g., 'office', 'hotel')

        Returns:
            BuildingTypeConfig if found, None otherwise
        """
        return self._configs.get(building_type_id)

    def get_occupancy_hours(self, building_type_id: str) -> tuple[int, int]:
        """
        Get typical occupancy hours for a building type.

        Args:
            building_type_id: Building type identifier

        Returns:
            Tuple of (start_hour, end_hour) in 24h format
        """
        config = self.get_config(building_type_id)
        if config:
            return config.occupancy_hours_tuple
        else:
            # Default fallback
            return (8, 18)

    def get_display_name(self, building_type_id: str) -> str:
        """
        Get display name for a building type.

        Args:
            building_type_id: Building type identifier

        Returns:
            Human-readable display name
        """
        config = self.get_config(building_type_id)
        if config:
            return config.display_name
        else:
            return building_type_id.replace("_", " ").title()

    def is_supported(self, building_type_id: str) -> bool:
        """
        Check if a building type is fully supported.

        Args:
            building_type_id: Building type identifier

        Returns:
            True if supported, False otherwise
        """
        config = self.get_config(building_type_id)
        return config.supported if config else False

    def get_all_building_types(self) -> list[str]:
        """Get list of all configured building type IDs."""
        return list(self._configs.keys())

    def get_supported_building_types(self) -> list[str]:
        """Get list of fully supported building type IDs."""
        return [
            type_id
            for type_id, config in self._configs.items()
            if config.supported
        ]

    def get_default_parameters(self, building_type_id: str) -> list[str]:
        """
        Get default parameters to monitor for a building type.

        Args:
            building_type_id: Building type identifier

        Returns:
            List of parameter identifiers
        """
        config = self.get_config(building_type_id)
        return config.default_parameters if config else []

    def reload_configs(self) -> None:
        """Reload configurations from default config file."""
        self._configs.clear()
        self._load_default_configs()


# Global singleton instance
building_type_config_loader = BuildingTypeConfigLoader()
