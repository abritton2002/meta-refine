#!/usr/bin/env python3
"""
Setup script for Meta-Refine - AI-powered code intelligence tool.

This allows installation via: pip install meta-refine
After installation, use: meta
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="meta-refine",
    version="1.0.0",
    author="Alex Britton",
    author_email="abritton2002@gmail.com",
    description="AI-powered code intelligence tool built with Meta's Llama 3.1 - Install globally and run with 'meta'",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abritton2002/meta-refine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "huggingface-hub>=0.19.0",
        "accelerate>=0.24.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "colorama>=0.4.6",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "pyyaml>=6.0.1",
        "libcst>=1.1.0",
        "diskcache>=5.6.0",
        "psutil>=5.9.0",
        "tqdm>=4.66.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-benchmark>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "pre-commit>=3.6.0",
            "watchdog>=3.0.0",
        ],
        "security": [
            "bandit>=1.7.5",
            "safety>=2.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "meta=meta_refine:app",
            "meta-refine=meta_refine:app",
        ],
    },
    keywords="meta ai llama code-analysis code-review cli-tool security performance static-analysis meta-ai developer-tools",
    project_urls={
        "Bug Reports": "https://github.com/abritton2002/meta-refine/issues",
        "Source": "https://github.com/abritton2002/meta-refine",
        "Documentation": "https://github.com/abritton2002/meta-refine#readme",
    },
)