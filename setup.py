"""Setup configuration for Lakeventory."""

from pathlib import Path
from setuptools import setup, find_packages

# Read version from package
version = {}
with open("lakeventory/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="lakeventory",
    version=version.get("__version__", "1.0.0"),
    description="Automated discovery and inventory of Databricks workspace assets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Felipe Moz",
    author_email="felipe@example.com",
    url="https://github.com/felipemoz/lakeventory",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "lakeventory=lakeventory.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    keywords="databricks inventory audit compliance asset-discovery",
    project_urls={
        "Bug Reports": "https://github.com/felipemoz/lakeventory/issues",
        "Source": "https://github.com/felipemoz/lakeventory",
        "Documentation": "https://github.com/felipemoz/lakeventory/tree/main/docs",
    },
)
