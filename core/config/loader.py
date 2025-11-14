"""
Utility helpers for loading YAML-based configuration resources.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml

CONFIG_DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _optional_yaml(path: Path) -> dict:
    return _load_yaml(path) if path.exists() else {}


def _list_yaml_names(directory: Path) -> List[str]:
    if not directory.exists():
        return []
    return sorted(p.stem for p in directory.glob("*.yaml"))


@lru_cache(maxsize=None)
def list_filters() -> List[str]:
    return _list_yaml_names(CONFIG_DATA_DIR / "filters")


@lru_cache(maxsize=None)
def load_filter_config(name: str) -> dict:
    return _load_yaml(CONFIG_DATA_DIR / "filters" / f"{name}.yaml")


@lru_cache(maxsize=None)
def list_periods() -> List[str]:
    return _list_yaml_names(CONFIG_DATA_DIR / "periods")


@lru_cache(maxsize=None)
def load_period_config(name: str) -> dict:
    return _load_yaml(CONFIG_DATA_DIR / "periods" / f"{name}.yaml")


@lru_cache(maxsize=None)
def load_holiday_config(country_code: Optional[str]) -> dict:
    """
    Load holiday metadata for a specific country/region.
    """
    if not country_code:
        return {}
    normalized = country_code.lower().replace("-", "_")
    path = CONFIG_DATA_DIR / "holidays" / f"{normalized}.yaml"
    if not path.exists():
        path = CONFIG_DATA_DIR / "holidays" / f"{country_code.lower()}.yaml"
    return _optional_yaml(path)


@lru_cache(maxsize=1)
def load_epc_thresholds() -> Dict[str, List[dict]]:
    data = _load_yaml(CONFIG_DATA_DIR / "standards" / "epc_thresholds.yaml")
    thresholds = data.get("thresholds") if isinstance(data, dict) else None
    return {k.upper(): v for k, v in (thresholds or {}).items()}
