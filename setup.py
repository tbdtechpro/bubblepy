"""Setup file for Bubble Tea Python port."""

import os

from setuptools import setup

# Read README for long description
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="charm-bubbletea",
    version="0.1.0",
    description="A Python TUI framework based on The Elm Architecture (port of Go Bubble Tea)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/charmbracelet/bubbletea",
    author="Charm",
    author_email="vt100@charm.sh",
    license="MIT",
    # Flat-layout: all source files live at the repo root alongside __init__.py.
    # Explicitly list the package and map it to "" so setuptools finds the right files.
    packages=["bubbletea"],
    package_dir={"bubbletea": ""},
    python_requires=">=3.10",
    # No external dependencies for core functionality
    install_requires=[],
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
            "mypy",
            "black",
            "isort",
            "flake8",
        ],
    },
    # Entry points (if you want CLI commands)
    entry_points={
        "console_scripts": [
            # "bubbletea-example=examples.basics:main",
        ],
    },
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Terminals",
        "Typing :: Typed",
    ],
    # Keywords for discoverability
    keywords=[
        "tui",
        "terminal",
        "cli",
        "console",
        "elm-architecture",
        "bubbletea",
        "charm",
        "user-interface",
    ],
    # Include type hints
    package_data={
        "bubbletea": ["py.typed"],
    },
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/charmbracelet/bubbletea/issues",
        "Source": "https://github.com/charmbracelet/bubbletea",
        "Original Go Library": "https://github.com/charmbracelet/bubbletea",
    },
)
