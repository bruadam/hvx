#!/usr/bin/env python3
"""
Standalone mapping script for IEQ sensor data.
This script provides the mapping functionality described in the README.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ieq_analytics.cli import mapping

if __name__ == "__main__":
    mapping()
