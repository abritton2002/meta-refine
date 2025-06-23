"""
Configuration management for Meta-Refine.

Handles all settings for model configuration, analysis parameters,
and output formatting options.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
# from functools import lru_cache  # Removed temporarily

# Load .env file explicitly
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, try to load manually
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

from pydantic import BaseModel, Field, ConfigDict
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older versions
    from pydantic import BaseSettings

try:
    from pydantic import field_validator
except ImportError:
    # Fallback for pydantic v1
    from pydantic import validator as field_validator


class ModelConfig(BaseModel):
    """Configuration for the Llama model interface."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    model_name: str = Field(default="meta-llama/Llama-3.1-8B-Instruct", alias="MODEL_NAME")
    device: str = Field(default="auto", alias="MODEL_DEVICE") 
    max_length: int = 4096
    temperature: float = Field(default=0.3, alias="MODEL_TEMPERATURE")
    top_p: float = 0.9
    top_k: int = 50
    do_sample: bool = True
    use_cache: bool = True
    torch_dtype: str = "auto"
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @field_validator("top_p") 
    @classmethod
    def validate_top_p(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Top-p must be between 0.0 and 1.0")
        return v


class AnalysisConfig(BaseModel):
    """Configuration for code analysis parameters."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    # Language support
    supported_languages: List[str] = ["python", "javascript", "typescript", "java"]
    
    # Analysis types
    enable_bug_detection: bool = True
    enable_performance_analysis: bool = True
    enable_security_analysis: bool = True
    enable_style_analysis: bool = True
    enable_documentation_analysis: bool = True
    
    # Analysis parameters
    max_file_size: int = Field(default=1_000_000, alias="MAX_FILE_SIZE")
    chunk_size: int = Field(default=2000, alias="CHUNK_SIZE")
    chunk_overlap: int = 200
    max_suggestions_per_file: int = 20
    
    # Severity thresholds
    critical_score_threshold: float = 0.9
    high_score_threshold: float = 0.7
    medium_score_threshold: float = 0.5
    
    # File patterns
    ignore_patterns: List[str] = [
        "*.pyc", "*.pyo", "__pycache__/*", "node_modules/*",
        "*.min.js", "*.bundle.js", "build/*", "dist/*",
        ".git/*", ".vscode/*", ".idea/*"
    ]
    
    include_patterns: List[str] = [
        "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java",
        "*.cpp", "*.c", "*.h", "*.hpp", "*.go", "*.rs"
    ]


class OutputConfig(BaseModel):
    """Configuration for output formatting."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    # Output formats
    default_format: str = Field(default="console", alias="DEFAULT_OUTPUT_FORMAT")
    supported_formats: List[str] = ["console", "json", "html", "markdown", "xml"]
    
    # Console output
    use_colors: bool = Field(default=True, alias="USE_COLORS")
    show_progress: bool = True
    show_timestamps: bool = False
    
    # Formatting options
    max_line_length: int = 100
    indent_size: int = 2
    
    # File output
    output_directory: Path = Path("./meta_refine_output")
    include_metadata: bool = True
    include_source_context: bool = True


class CacheConfig(BaseModel):
    """Configuration for caching."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    enable_cache: bool = Field(default=True, alias="ENABLE_CACHE")
    cache_directory: Path = Path.home() / ".meta_refine_cache"
    cache_ttl: int = 3600 * 24  # 24 hours
    max_cache_size: int = 1_000_000_000  # 1GB


class Settings(BaseSettings):
    """Main settings class combining all configuration sections."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Sub-configurations
    llama_config: ModelConfig = Field(default_factory=ModelConfig)
    analysis_config: AnalysisConfig = Field(default_factory=AnalysisConfig)
    output_config: OutputConfig = Field(default_factory=OutputConfig)
    cache_config: CacheConfig = Field(default_factory=CacheConfig)
    
    # Global settings
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    huggingface_token: Optional[str] = Field(default=None, alias="HF_TOKEN")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set HF token from environment if not provided
        if not self.huggingface_token:
            self.huggingface_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        
        # Create fresh ModelConfig with environment variables
        model_name = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
        model_device = os.getenv("MODEL_DEVICE", "auto")
        model_temp = float(os.getenv("MODEL_TEMPERATURE", "0.3"))
        model_load_4bit = os.getenv("MODEL_LOAD_IN_4BIT", "false").lower() == "true"
        
        # Override the llama_config entirely to ensure fresh loading
        self.llama_config = ModelConfig(
            model_name=model_name,
            device=model_device,
            temperature=model_temp,
            load_in_4bit=model_load_4bit
        )
    
    @field_validator("log_level")
    @classmethod  
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


def get_settings() -> Settings:
    """Get settings instance (no cache for now to ensure fresh loading)."""
    return Settings()


def update_settings(**kwargs) -> Settings:
    """Update settings."""
    return Settings(**kwargs) 