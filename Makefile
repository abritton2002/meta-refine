# Meta-Refine Makefile
# Development and deployment automation

.PHONY: help install install-dev test lint format clean docker run-example setup-env

# Default target
help:
	@echo "Meta-Refine Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install Meta-Refine and dependencies with uv"
	@echo "  install-dev      Install with development dependencies"
	@echo "  setup-env        Set up environment configuration"
	@echo ""
	@echo "Development:"
	@echo "  test             Run test suite"
	@echo "  lint             Run linting and type checking"
	@echo "  format           Format code with black and isort"
	@echo "  clean            Clean build artifacts and cache"
	@echo ""
	@echo "Docker:"
	@echo "  docker           Build Docker image"
	@echo "  docker-run       Run analysis in Docker container"
	@echo ""
	@echo "Examples:"
	@echo "  run-example      Run analysis on example files"
	@echo "  demo             Run full demonstration"

# Check if uv is installed
check-uv:
	@which uv > /dev/null || (echo "❌ uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)

# Installation
install: check-uv
	uv pip install -e .

install-dev: check-uv
	uv pip install -e ".[dev]"
	pre-commit install

setup-env:
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ Created .env file from template"; \
		echo "⚠️  Please edit .env and add your HF_TOKEN"; \
		echo "   Get your token from: https://huggingface.co/settings/tokens"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

# Development
test: check-uv
	@if [ ! -d "tests" ]; then \
		echo "⚠️  Creating basic test structure..."; \
		mkdir -p tests; \
		touch tests/__init__.py; \
		echo "✅ Test directory created"; \
	fi
	uv pip install -e ".[dev]"
	python -m pytest tests/ -v --cov=core --cov-report=term-missing

test-integration:
	uv pip install -e ".[dev]"
	python -m pytest tests/ -v --cov=core -m integration

lint: check-uv
	uv pip install -e ".[dev]"
	black --check core/ meta_refine.py
	isort --check core/ meta_refine.py
	flake8 core/ meta_refine.py
	mypy core/ meta_refine.py

format: check-uv
	uv pip install -e ".[dev]"
	black core/ meta_refine.py
	isort core/ meta_refine.py

security: check-uv
	uv pip install -e ".[security]"
	bandit -r core/ meta_refine.py
	safety check

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker
docker:
	docker build -t meta-refine:latest .

docker-run: docker
	@mkdir -p output
	docker run --rm \
		-v $(PWD)/examples:/app/examples:ro \
		-v $(PWD)/output:/app/output \
		meta-refine:latest analyze --project /app/examples --format json --output /app/output/analysis.json

# Examples and demonstrations
run-example: install
	python3 meta_refine.py analyze --file examples/example.py --format console

run-js-example: install
	python3 meta_refine.py analyze --file examples/example.js --format console

run-project-example: install
	python3 meta_refine.py analyze --project examples/ --format console

demo: setup-env install
	@echo "🚀 Meta-Refine Demonstration"
	@echo "============================="
	@echo ""
	@echo "1. System Health Check:"
	python3 meta_refine.py doctor
	@echo ""
	@echo "2. Analyzing Python Example:"
	python3 meta_refine.py analyze --file examples/example.py --format console
	@echo ""
	@echo "3. Analyzing JavaScript Example:"  
	python3 meta_refine.py analyze --file examples/example.js --format console
	@echo ""
	@echo "4. Full Project Analysis:"
	@mkdir -p output
	python3 meta_refine.py analyze --project examples/ --format json --output output/demo_results.json
	@echo ""
	@echo "✅ Demo complete! Check output/demo_results.json for detailed results."

# CI/CD targets
ci-test: install-dev lint test

ci-build: clean
	uv build

# Development helpers
watch:
	watchmedo shell-command --patterns="*.py" --recursive --command="make test" .

profile-example:
	python3 -m cProfile -o profile_stats.prof meta_refine.py analyze --file examples/example.py
	python3 -c "import pstats; pstats.Stats('profile_stats.prof').sort_stats('cumulative').print_stats(20)"

benchmark: install
	python3 meta_refine.py benchmark examples/example.py

# Release helpers
version-bump:
	@read -p "Enter new version (current: 1.0.0): " version; \
	sed -i.bak "s/version = \"1.0.0\"/version = \"$$version\"/" pyproject.toml && \
	sed -i.bak "s/__version__ = \"1.0.0\"/__version__ = \"$$version\"/" core/__init__.py && \
	rm *.bak

release: clean ci-test ci-build
	@echo "Ready for release! Build artifacts are in dist/"

# Quick setup for new developers
quick-start: check-uv setup-env install-dev
	@echo ""
	@echo "🎉 Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env and add your HF_TOKEN"
	@echo "2. Run 'make demo' to test the system"
	@echo "3. Run 'make test' to run the test suite" 