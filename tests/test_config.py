"""
Tests for Meta-Refine configuration management.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from core.config import (
    ModelConfig,
    AnalysisConfig,
    OutputConfig,
    Settings,
    get_settings,
)


class TestModelConfig:
    """Test ModelConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ModelConfig()
        assert config.model_name == "meta-llama/Llama-3.1-8B-Instruct"
        assert config.device == "auto"
        assert config.temperature == 0.3
        assert config.max_length == 4096
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = ModelConfig(
            temperature=0.7,
            max_length=2048,
            device="cpu"
        )
        assert config.temperature == 0.7
        assert config.max_length == 2048
        assert config.device == "cpu"


class TestAnalysisConfig:
    """Test AnalysisConfig class."""
    
    def test_default_values(self):
        """Test default analysis configuration."""
        config = AnalysisConfig()
        assert "python" in config.supported_languages
        assert "javascript" in config.supported_languages
        assert config.max_file_size == 1_000_000
        assert config.chunk_size == 2000
    
    def test_language_support(self):
        """Test supported language configuration."""
        config = AnalysisConfig()
        expected_languages = ["python", "javascript", "typescript", "java"]
        for lang in expected_languages:
            assert lang in config.supported_languages


class TestOutputConfig:
    """Test OutputConfig class."""
    
    def test_default_values(self):
        """Test default output configuration."""
        config = OutputConfig()
        assert config.default_format == "console"
        assert config.use_colors is True
        assert config.show_progress is True


class TestSettings:
    """Test main Settings class."""
    
    def setup_method(self):
        """Clear cache before each test."""
        get_settings.cache_clear()
    
    def test_default_settings(self):
        """Test default settings initialization."""
        settings = Settings()
        assert isinstance(settings.llama_config, ModelConfig)
        assert isinstance(settings.analysis_config, AnalysisConfig)
        assert isinstance(settings.output_config, OutputConfig)
        assert settings.debug is False
    
    @patch.dict(os.environ, {"HF_TOKEN": "test_token"}, clear=True)
    def test_hf_token_from_env(self):
        """Test HF token loading from environment."""
        get_settings.cache_clear()  # Clear cache to pick up env changes
        settings = Settings()
        assert settings.huggingface_token == "test_token"
    
    @patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "another_token"}, clear=True)
    def test_huggingface_token_from_env(self):
        """Test alternative HF token environment variable."""
        get_settings.cache_clear()  # Clear cache to pick up env changes
        settings = Settings()
        assert settings.huggingface_token == "another_token"


class TestGetSettings:
    """Test settings factory function."""
    
    def setup_method(self):
        """Clear cache before each test."""
        get_settings.cache_clear()
    
    def test_get_settings_caching(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_settings_type(self):
        """Test that get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings) 