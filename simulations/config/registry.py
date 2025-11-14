"""
Simulation model configuration registry and discovery helpers.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import yaml

from core.spacial_entity import SpatialEntity
from core.enums.spatial import SpatialEntityType

SIMULATION_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
SIMULATION_CONFIG_DIR = SIMULATION_MODELS_DIR  # Backwards compatibility alias
CONFIG_FILENAME = "config.yaml"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Simulation config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def _model_directories() -> List[Path]:
    if not SIMULATION_MODELS_DIR.exists():
        return []
    return sorted(
        [
            path for path in SIMULATION_MODELS_DIR.iterdir()
            if path.is_dir() and (path / CONFIG_FILENAME).exists()
        ],
        key=lambda p: p.name,
    )


@lru_cache(maxsize=None)
def list_simulation_models() -> List[str]:
    """Return the identifiers of all available simulation configs."""
    return [path.name for path in _model_directories()]


@lru_cache(maxsize=None)
def load_simulation_config(model_id: str) -> Dict[str, Any]:
    """Load a specific simulation model configuration."""
    return _load_yaml((SIMULATION_MODELS_DIR / model_id / CONFIG_FILENAME))


def load_all_simulation_configs() -> Dict[str, Dict[str, Any]]:
    """Return all simulation configs keyed by model id."""
    return {model_id: load_simulation_config(model_id) for model_id in list_simulation_models()}


def _normalize(values: Optional[Sequence[Any]]) -> List[str]:
    return [str(value).lower() for value in values or [] if value is not None]


def _value_allowed(value: Optional[str], spec: Optional[Dict[str, Sequence[str]]]) -> bool:
    if not spec:
        return True
    normalized_value = str(value).lower() if value else None
    includes = set(_normalize(spec.get("include")))
    excludes = set(_normalize(spec.get("exclude")))

    if normalized_value and normalized_value in excludes:
        return False

    if includes and normalized_value:
        return normalized_value in includes or "*" in includes or "any" in includes

    if includes:
        # Allow unknown values when config explicitly permits "other"/"any"
        return "other" in includes or "*" in includes or "any" in includes

    return True


def _resolve_entity_value(entity: SpatialEntity, path: str) -> Any:
    current: Any = entity
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current


def _metadata_requirements_satisfied(entity: SpatialEntity, requirements: Optional[Sequence[Any]]) -> bool:
    if not requirements:
        return True
    for item in requirements:
        if isinstance(item, str):
            path = item
        else:
            path = item.get("path") if isinstance(item, dict) else None
        if not path:
            continue
        if _resolve_entity_value(entity, path) is None:
            return False
    return True


def applicable_models_for_entity(
    entity: SpatialEntity,
    available_parameters: Optional[Iterable[str]] = None,
    include_rollup: bool = True,
) -> List[Dict[str, Any]]:
    """Return simulation configs applicable to the provided spatial entity."""
    entity_type = entity.type.value if isinstance(entity.type, SpatialEntityType) else str(entity.type)
    available = None
    if available_parameters is not None:
        available = {param.lower() for param in available_parameters if param}

    matches: List[Dict[str, Any]] = []
    for config in load_all_simulation_configs().values():
        scope = config.get("spatial_scope", {})
        run_on = set(_normalize(scope.get("run_on_types")))
        aggregate_to = set(_normalize(scope.get("aggregate_to_types"))) if include_rollup else set()
        rollup_from = set(_normalize(scope.get("rollup_from_children")))

        execution_mode: Optional[str] = None
        if entity_type in run_on:
            execution_mode = "direct"
        elif entity_type in aggregate_to:
            execution_mode = "aggregate"
        else:
            continue

        applicability = config.get("applicability", {})
        if not _value_allowed(entity.building_type, applicability.get("building_types")):
            continue
        if entity.type == SpatialEntityType.ROOM:
            if not _value_allowed(entity.room_type, applicability.get("room_types")):
                continue

        requirements = config.get("requirements", {})
        required_param_entries = requirements.get("parameters", {}).get("required", [])
        required_params: set[str] = set()
        for entry in required_param_entries:
            if isinstance(entry, str):
                required_params.add(entry.lower())
            elif isinstance(entry, dict) and entry.get("parameter"):
                required_params.add(str(entry["parameter"]).lower())
        if available is not None and required_params and not required_params.issubset(available):
            continue

        metadata_required = requirements.get("metadata", {}).get("required")
        if not _metadata_requirements_satisfied(entity, metadata_required):
            continue

        matches.append({
            "model_id": config.get("id"),
            "config": config,
            "execution_mode": execution_mode,
            "rollup_child_types": list(rollup_from),
        })

    return matches


__all__ = [
    "SIMULATION_MODELS_DIR",
    "SIMULATION_CONFIG_DIR",
    "list_simulation_models",
    "load_simulation_config",
    "load_all_simulation_configs",
    "applicable_models_for_entity",
]
