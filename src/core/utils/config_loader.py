"""
Utility for loading configuration files from the installed package.

This ensures that config files are loaded from the installed package location,
not from the current working directory.

NEW: IEQ configurations now use modular structure in src/core/analysis/ieq/config/
with one file per rule/filter/period, organized by standards.
"""

from pathlib import Path
from typing import Dict, Any
import sys
import yaml


def get_package_config_path(config_filename: str = "tests.yaml") -> Path:
    """
    Get the path to a config file from the installed package.
    
    Args:
        config_filename: Name of the config file (default: "tests.yaml")
    
    Returns:
        Path to the config file in the installed package
    
    Raises:
        FileNotFoundError: If the config file cannot be found
    """
    # Try multiple methods to locate the package config directory
    
    # Method 1: Use __file__ from this module to find the package root
    try:
        # This file is in src/utils/, so go up two levels to get to package root
        current_file = Path(__file__).resolve()
        package_root = current_file.parent.parent.parent  # Go up to analytics/
        config_path = package_root / "config" / config_filename
        
        if config_path.exists():
            return config_path
    except Exception:
        pass
    
    # Method 2: Try using importlib.resources (Python 3.9+)
    try:
        if sys.version_info >= (3, 9):
            from importlib.resources import files
            # Access the config directory inside the 'src' package
            config_dir = files('src').joinpath("config")
            config_path = config_dir.joinpath(config_filename)
            config_path_as_path = Path(str(config_path))
            if config_path_as_path.exists():
                return config_path_as_path
    except Exception:
        pass
    
    # Method 3: Search in sys.path for the installed package
    try:
        import src
        if hasattr(src, '__file__'):
            src_path = Path(src.__file__).parent
            package_root = src_path.parent
            config_path = package_root / "config" / config_filename
            if config_path.exists():
                return config_path
    except Exception:
        pass
    
    # Method 4: Fallback to current directory (for development)
    fallback_path = Path("config") / config_filename
    if fallback_path.exists():
        return fallback_path
    
    # If nothing works, raise an error
    raise FileNotFoundError(
        f"Could not locate config file '{config_filename}'. "
        f"Searched in package installation and current directory."
    )


def get_tests_config_path() -> Path:
    """
    Get the path to the tests.yaml config file.
    
    Returns:
        Path to tests.yaml in the installed package
    """
    return get_package_config_path("tests.yaml")


def get_report_config_path() -> Path:
    """
    Get the path to the report_config.yaml file.
    
    Returns:
        Path to report_config.yaml in the installed package
    """
    return get_package_config_path("report_config.yaml")


def get_en16798_config_path() -> Path:
    """
    Get the path to the en16798.yaml config file.

    DEPRECATED: Use load_ieq_config() instead for modular configuration.

    Returns:
        Path to en16798.yaml in the installed package
    """
    return get_package_config_path("en16798.yaml")


def get_ieq_config_base_path() -> Path:
    """
    Get the base path to the IEQ configuration directory.

    Returns:
        Path to src/core/analysis/ieq/config/ directory

    Raises:
        FileNotFoundError: If the config directory cannot be found
    """
    # Method 1: Use __file__ from this module to find the package root
    try:
        current_file = Path(__file__).resolve()
        # This file is in src/core/utils/, go to src/core/analysis/ieq/config/
        src_core = current_file.parent.parent
        config_path = src_core / "analysis" / "ieq" / "config"

        if config_path.exists():
            return config_path
    except Exception:
        pass

    # Method 2: Try using importlib.resources
    try:
        if sys.version_info >= (3, 9):
            from importlib.resources import files
            config_path = files('src.core.analysis.ieq').joinpath("config")
            config_path_as_path = Path(str(config_path))
            if config_path_as_path.exists():
                return config_path_as_path
    except Exception:
        pass

    # Method 3: Search in sys.path for the installed package
    try:
        import src.core.analysis.ieq
        if hasattr(src.core.analysis.ieq, '__file__'):
            ieq_path = Path(src.core.analysis.ieq.__file__).parent
            config_path = ieq_path / "config"
            if config_path.exists():
                return config_path
    except Exception:
        pass

    # Method 4: Fallback to current directory (for development)
    fallback_path = Path("src/core/analysis/ieq/config")
    if fallback_path.exists():
        return fallback_path

    raise FileNotFoundError(
        "Could not locate IEQ config directory 'src/core/analysis/ieq/config/'. "
        "Searched in package installation and current directory."
    )


def load_ieq_config() -> Dict[str, Any]:
    """
    Load all IEQ configuration from the modular structure.

    This loads:
    - All analytics rules from standards/*/
    - All periods from periods/
    - All filters from filters/
    - Holidays from holidays/

    Returns:
        Dictionary with keys: analytics, periods, filters, holidays
    """
    from src.core.analysis.ieq.config_loader import load_ieq_config as _load_ieq_config

    try:
        config_base_path = get_ieq_config_base_path()
        return _load_ieq_config(config_base_path)
    except Exception:
        # Fallback: try loading directly without path
        return _load_ieq_config()


def load_ieq_standard(standard_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Load only rules from a specific IEQ standard.

    Args:
        standard_name: Name of the standard (e.g., 'en16798-1', 'br18', 'danish-guidelines')

    Returns:
        Dictionary mapping rule names to rule configurations
    """
    from src.core.analysis.ieq.config_loader import load_ieq_standard as _load_ieq_standard

    try:
        config_base_path = get_ieq_config_base_path()
        return _load_ieq_standard(standard_name, config_base_path)
    except Exception:
        # Fallback: try loading directly without path
        return _load_ieq_standard(standard_name)
