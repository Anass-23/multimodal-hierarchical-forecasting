PROJECT_NAME = educast
PYTHON = env/bin/python

.PHONY: install format lint test typecheck all clean check-format

install:
	@echo "📦 Installing $(PROJECT_NAME) in editable mode with dev tools..."
	@$(PYTHON) -m pip install -e ".[dev]"

format:
	@echo "🎨 Formatting code with Black..."
	@$(PYTHON) -m black src tests
	@echo "📋 Sorting imports with isort..."
	@$(PYTHON) -m isort src tests

lint:
	@echo "🔍 Linting code with Flake8..."
	@$(PYTHON) -m flake8 src tests

check-format:
	@echo "✅ Checking code format..."
	@$(PYTHON) -m black --check src tests
	@$(PYTHON) -m isort --check-only src tests

test:
	@echo "🧪 Running tests with Pytest..."
	@$(PYTHON) -m pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	@$(PYTHON) -m pytest --cov=educast --cov-report=term-missing

typecheck:
	@echo "🔠 Type checking with MyPy..."
	@$(PYTHON) -m mypy src

clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true

# Run everything (format → lint → typecheck → test)
all: format lint typecheck test
	@echo "✅ All checks passed successfully!"

# CI/CD check (non-modifying checks only)
ci: check-format lint typecheck test
	@echo "✅ CI checks passed successfully!"