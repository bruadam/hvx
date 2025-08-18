"""
Setup script for IEQ Analytics Engine.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Analytics Engine for Indoor Environmental Quality"

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = []

setup(
    name="ieq-analytics",
    version="1.0.0",
    author="Bruno Adam",
    author_email="bruno.adam@example.com",
    description="Analytics Engine for Indoor Environmental Quality assessment using IoT sensors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/brunoadam/ieq-analytics",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": ["pytest", "pytest-cov", "black", "flake8", "mypy"],
        "docs": ["sphinx", "sphinx-rtd-theme"],
    },
    entry_points={
        "console_scripts": [
            "ieq-analytics=ieq_analytics.cli:cli",
            "ieq-mapping=ieq_analytics.cli:mapping",
        ],
    },
    include_package_data=True,
    package_data={
        "ieq_analytics": ["config/*.json"],
    },
)
