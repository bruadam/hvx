"""
Utility for loading configuration files from the installed package.

This ensures that config files are loaded from the installed package location,
not from the current working directory.
"""

from pathlib import Path
import sys


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
    
    Returns:
        Path to en16798.yaml in the installed package
    """
    return get_package_config_path("en16798.yaml")
