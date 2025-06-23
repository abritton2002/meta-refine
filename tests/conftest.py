"""
Pytest configuration for Meta-Refine tests.
"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return '''
def hello_world():
    """A simple hello world function."""
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
'''


@pytest.fixture
def sample_javascript_code():
    """Sample JavaScript code for testing."""
    return '''
function helloWorld() {
    console.log("Hello, World!");
}

helloWorld();
''' 