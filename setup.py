#!/usr/bin/env python3
"""
Setup script for Spiderman Swing CLI Game
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="spidy",
    version="1.0.0",
    author="Marvel Games Developers",
    description="Thrilling terminal-based Marvel superhero games: Spiderman and Captain America",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RohithDevarshetty/spidy",
    py_modules=["spiderman_swing", "captain_america"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment :: Arcade",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console :: Curses",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "spidy=spiderman_swing:main_wrapper",
            "cap=captain_america:main_wrapper",
        ],
    },
    install_requires=[],
)
