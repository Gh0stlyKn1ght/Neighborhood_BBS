#!/usr/bin/env python
"""
Setup configuration for Neighborhood BBS
Allows installation via: pip install neighborhood-bbs
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8")

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = [
    line.strip()
    for line in requirements_file.read_text(encoding="utf-8").split("\n")
    if line.strip() and not line.startswith("#")
]

setup(
    name="neighborhood-bbs",
    version="1.0.0",
    description="A decentralized community board and real-time chatroom for neighborhoods",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Gh0stlyKn1ght",
    author_email="contact@neighborhood-bbs.local",
    url="https://github.com/Gh0stlyKn1ght/Neighborhood_BBS",
    license="MIT",
    packages=find_packages(where="server/src"),
    package_dir={"": "server/src"},
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-flask>=1.2.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.4.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "neighborhood-bbs=server.src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: Communications",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/issues",
        "Documentation": "https://github.com/Gh0stlyKn1ght/Neighborhood_BBS#readme",
        "Source Code": "https://github.com/Gh0stlyKn1ght/Neighborhood_BBS",
        "Changelog": "https://github.com/Gh0stlyKn1ght/Neighborhood_BBS/blob/main/CHANGELOG.md",
    },
    keywords=[
        "bbs",
        "bulletin-board",
        "community",
        "chat",
        "decentralized",
        "local-network",
        "privacy",
        "open-source",
        "raspberry-pi",
        "neighborhood",
    ],
)
