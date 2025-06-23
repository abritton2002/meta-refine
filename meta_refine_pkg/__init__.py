"""
Meta-Refine: AI-Powered Code Intelligence

A sophisticated code analysis tool powered by Meta's Llama 3.1-8B-Instruct model.
Install globally and run with 'meta' command.
"""

__version__ = "1.0.0"
__author__ = "Alex Britton"  
__email__ = "abritton2002@gmail.com"

from .cli import app

__all__ = ["app"]