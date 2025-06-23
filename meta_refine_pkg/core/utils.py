"""
Utility functions for Meta-Refine

Helper functions for logging, environment validation, file operations, and more.
"""

import logging
import os
import sys
import time
import hashlib
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List
import subprocess
import importlib.util

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, log_file: Optional[Path] = None):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[]
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s' if not verbose else 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler if specified
    handlers = [console_handler]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # Apply handlers to root logger
    root_logger = logging.getLogger()
    root_logger.handlers = handlers
    
    # Set specific logger levels
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    if verbose:
        logger.debug("Verbose logging enabled")


def validate_environment(show_suggestions: bool = True) -> tuple[bool, dict]:
    """Validate that the environment is properly set up.
    
    Returns:
        Tuple of (all_passed, detailed_results) where detailed_results
        contains check names, status, and suggested fixes.
    """
    checks = {
        'python_version': (_check_python_version(), "Upgrade to Python 3.8+ from python.org"),
        'torch_available': (_check_torch_availability(), "Install with: pip install torch"),
        'transformers_available': (_check_transformers_availability(), "Install with: pip install transformers"),
        'hf_token': (_check_huggingface_token(), "Set HF_TOKEN in .env file or run 'meta setup'"),
        'model_access': (_check_model_access(), "Verify HF token and network connection"),
        'cache_directory': (_check_cache_directory(), "Check disk space and permissions"),
    }
    
    detailed_results = {}
    all_passed = True
    
    for check_name, (passed, suggestion) in checks.items():
        detailed_results[check_name] = {
            'passed': passed,
            'suggestion': suggestion,
            'status': "✅" if passed else "❌"
        }
        if not passed:
            all_passed = False
    
    if not all_passed and show_suggestions:
        logger.error("Environment validation failed:")
        for check_name, result in detailed_results.items():
            logger.error(f"  {result['status']} {check_name}")
            if not result['passed'] and show_suggestions:
                logger.error(f"    💡 Fix: {result['suggestion']}")
    else:
        logger.info("Environment validation passed")
    
    return all_passed, detailed_results


def _check_python_version() -> bool:
    """Check if Python version is >= 3.8."""
    try:
        return sys.version_info >= (3, 8)
    except Exception:
        return False


def _check_torch_availability() -> bool:
    """Check if PyTorch is available."""
    try:
        import torch
        return True
    except ImportError:
        logger.warning("PyTorch not available")
        return False


def _check_transformers_availability() -> bool:
    """Check if Transformers library is available."""
    try:
        import transformers
        return True
    except ImportError:
        logger.warning("Transformers library not available")
        return False


def _check_huggingface_token() -> bool:
    """Check if Hugging Face token is available."""
    try:
        from .config import get_settings
        settings = get_settings()
        if not settings.huggingface_token:
            logger.warning("HF_TOKEN not configured in settings")
            return False
        return True
    except Exception as e:
        logger.warning(f"Could not check HF token: {e}")
        return False


def _check_model_access() -> bool:
    """Check if we can access the Llama model."""
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        
        # Try to get model info (this doesn't download the model)
        model_info = api.model_info("meta-llama/Llama-3.1-8B-Instruct")
        return model_info is not None
    except Exception as e:
        logger.warning(f"Cannot access Llama model: {e}")
        return False


def _check_cache_directory() -> bool:
    """Check if cache directory is writable."""
    try:
        cache_dir = Path.home() / ".meta_refine_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write access
        test_file = cache_dir / "test_write"
        test_file.write_text("test")
        test_file.unlink()
        
        return True
    except Exception as e:
        logger.warning(f"Cache directory not writable: {e}")
        return False


def get_git_info(project_path: Path) -> Dict[str, str]:
    """Get Git information for a project."""
    try:
        original_cwd = os.getcwd()
        os.chdir(project_path)
        
        git_info = {}
        
        # Get current branch
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            git_info['branch'] = result.stdout.strip()
        
        # Get latest commit hash
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            git_info['commit'] = result.stdout.strip()[:8]
        
        # Get remote URL
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            git_info['remote'] = result.stdout.strip()
        
        os.chdir(original_cwd)
        return git_info
        
    except Exception as e:
        logger.debug(f"Could not get Git info: {e}")
        return {}


def find_project_files(
    project_path: Path,
    extensions: List[str],
    exclude_patterns: List[str] = None
) -> List[Path]:
    """Find project files with specified extensions."""
    if exclude_patterns is None:
        exclude_patterns = [
            '__pycache__', '.git', 'node_modules', '.venv', 'venv',
            '.pytest_cache', '.mypy_cache', 'build', 'dist'
        ]
    
    files = []
    
    for ext in extensions:
        pattern = f"**/*{ext}" if ext.startswith('.') else f"**/*.{ext}"
        for file_path in project_path.rglob(pattern):
            if file_path.is_file():
                # Check if file should be excluded
                exclude = False
                for pattern in exclude_patterns:
                    if pattern in str(file_path):
                        exclude = True
                        break
                
                if not exclude:
                    files.append(file_path)
    
    return sorted(files)


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    import hashlib
    
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        logger.warning(f"Could not hash file {file_path}: {e}")
        return ""


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def get_system_info() -> Dict[str, Any]:
    """Get system information for diagnostics."""
    import platform
    import psutil
    
    try:
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': format_file_size(psutil.virtual_memory().total),
            'memory_available': format_file_size(psutil.virtual_memory().available),
        }
        
        # GPU information
        try:
            import torch
            if torch.cuda.is_available():
                info['gpu_available'] = True
                info['gpu_count'] = torch.cuda.device_count()
                info['gpu_name'] = torch.cuda.get_device_name(0)
                info['gpu_memory'] = format_file_size(torch.cuda.get_device_properties(0).total_memory)
            else:
                info['gpu_available'] = False
        except Exception:
            info['gpu_available'] = False
        
        return info
        
    except Exception as e:
        logger.warning(f"Could not get system info: {e}")
        return {}


def create_example_files(output_dir: Path):
    """Create example files for testing the analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Example Python file with various issues
    python_example = '''
import os
import sys

def vulnerable_login(username, password):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    
    # Hardcoded credentials
    admin_pass = "admin123"
    
    # Unhandled exception
    result = execute_query(query)
    return result[0]

class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, user):
        # O(n) search that could be optimized
        for existing_user in self.users:
            if existing_user.id == user.id:
                return False
        self.users.append(user)
        return True
    
    # Missing docstring
    def get_user_count(self):
        return len(self.users)
    
    def process_users(self, user_data):
        # Inefficient nested loops
        results = []
        for user in self.users:
            for data in user_data:
                if user.id == data.id:
                    results.append(process_user_data(user, data))
        return results

# Missing error handling
def read_config_file():
    with open("config.txt", "r") as f:
        return f.read()

# Unused import and variable
import json
unused_variable = "not used"
'''
    
    (output_dir / "example.py").write_text(python_example)
    
    # Example JavaScript file
    js_example = '''
// Example JavaScript with issues
function authenticateUser(username, password) {
    // XSS vulnerability - no input sanitization
    document.getElementById("welcome").innerHTML = "Welcome " + username;
    
    // Hardcoded API key
    const apiKey = "sk-1234567890abcdef";
    
    // Missing error handling
    const response = fetch("/api/login", {
        method: "POST",
        body: JSON.stringify({username, password})
    });
    
    return response.json();
}

class DataProcessor {
    constructor() {
        this.cache = new Map();
    }
    
    // Memory leak - no cleanup
    processLargeDataset(data) {
        for (let item of data) {
            this.cache.set(item.id, this.expensiveOperation(item));
        }
    }
    
    // O(n²) algorithm
    findDuplicates(array) {
        const duplicates = [];
        for (let i = 0; i < array.length; i++) {
            for (let j = i + 1; j < array.length; j++) {
                if (array[i] === array[j]) {
                    duplicates.push(array[i]);
                }
            }
        }
        return duplicates;
    }
    
    // Missing input validation
    updateUserProfile(userId, profileData) {
        const query = `UPDATE users SET profile='${JSON.stringify(profileData)}' WHERE id=${userId}`;
        return executeQuery(query);
    }
}

// Unused function
function unusedFunction() {
    console.log("This function is never called");
}
'''
    
    (output_dir / "example.js").write_text(js_example)
    
    logger.info(f"Example files created in {output_dir}")


def cleanup_cache():
    """Clean up old cache files."""
    try:
        cache_dir = Path.home() / ".meta_refine_cache"
        if cache_dir.exists():
            import time
            current_time = time.time()
            
            for cache_file in cache_dir.iterdir():
                if cache_file.is_file():
                    # Remove files older than 7 days
                    if current_time - cache_file.stat().st_mtime > 7 * 24 * 3600:
                        cache_file.unlink()
                        logger.debug(f"Removed old cache file: {cache_file}")
        
    except Exception as e:
        logger.warning(f"Cache cleanup failed: {e}")


def is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk
    except Exception:
        return True


def get_language_stats(files: List[Path]) -> Dict[str, int]:
    """Get statistics about programming languages in file list."""
    extension_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript', 
        '.tsx': 'TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.c': 'C',
        '.h': 'C/C++',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.rb': 'Ruby',
    }
    
    stats = {}
    for file_path in files:
        ext = file_path.suffix.lower()
        language = extension_map.get(ext, 'Other')
        stats[language] = stats.get(language, 0) + 1
    
    return stats 