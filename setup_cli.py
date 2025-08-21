#!/usr/bin/env python3
"""
Setup script for IEQ Analytics CLI.

This script creates a proper Python package that can be installed globally.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else "IEQ Analytics CLI - Indoor Environmental Quality Analysis Platform"

setup(
    name="ieq-analyzer",
    version="1.0.0",
    author="IEQ Analytics Team",
    author_email="support@ieq-analytics.com",
    description="A comprehensive CLI tool for analyzing indoor environmental quality data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ieq-analytics/ieq-analyzer",
    packages=["cli", "cli.commands", "ieq_analytics", "ieq_analytics.reporting"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "rich>=12.0.0",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "pydantic>=1.8.0",
        "PyYAML>=6.0",
        "tabulate>=0.9.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.910",
        ],
        "ai": [
            "mistralai>=0.1.0",
        ],
        "reports": [
            "reportlab>=3.6.0",
            "weasyprint>=54.0",
            "jinja2>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ieq-analyzer=cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "cli": ["*.py"],
        "cli.commands": ["*.py"],
        "ieq_analytics": ["*.py"],
        "ieq_analytics.reporting": ["*.py"],
    },
)
