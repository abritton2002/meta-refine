"""
Meta-Refine Core Package

Core components for intelligent code analysis with Llama 3.1.
"""

__version__ = "1.0.0"
__author__ = "Meta-Refine Team"

from .analyzer import CodeAnalyzer
from .config import Settings, get_settings
from .formatter import ResultFormatter
from .model import LlamaModelInterface

__all__ = [
    "CodeAnalyzer",
    "Settings", 
    "get_settings",
    "ResultFormatter",
    "LlamaModelInterface",
] 