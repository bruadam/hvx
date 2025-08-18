#!/usr/bin/env python3
"""
Main entry point for the IEQ Analytics Engine.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ieq_analytics.cli import cli

if __name__ == "__main__":
    cli()
