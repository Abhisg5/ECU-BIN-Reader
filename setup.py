#!/usr/bin/env python3
"""
Setup script for ECU BIN Reader
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="ecu-bin-reader",
    version="1.0.0",
    author="ECU Tools",
    author_email="info@ecutools.com",
    description="Cross-platform ECU diagnostic and BIN extraction tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ecutools/ecu-bin-reader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "build": [
            "pyinstaller>=6.0.0",
            "setuptools>=65.0.0",
            "wheel>=0.38.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ecu-bin-reader=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md", "*.txt"],
    },
    keywords=[
        "ecu", "obd2", "can", "uds", "kwp", "diagnostic", "automotive",
        "bin", "flash", "memory", "extraction", "tuning"
    ],
    project_urls={
        "Bug Reports": "https://github.com/ecutools/ecu-bin-reader/issues",
        "Source": "https://github.com/ecutools/ecu-bin-reader",
        "Documentation": "https://github.com/ecutools/ecu-bin-reader#readme",
    },
) 