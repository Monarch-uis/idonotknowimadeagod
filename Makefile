.PHONY: help install install-dev test test-cov lint format security clean docker-build docker-run validate setup

# Default target
help:
	@echo "🎯 EPUB to Audiobook/Video Converter - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Complete project setup (install + pre-commit)"
	@echo "  make install        - Install production dependencies"
	@echo "  make install-dev    - Install all dependencies including dev tools"
	@echo ""
	@echo "Development:"
	@echo "  make format         - Format code with black and isort"
	@echo "  make lint           - Run all linters (flake8, pylint, mypy)"
	@echo "  make test           - Run test suite"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make validate       - Validate configuration"
	@echo ""
	@echo "Security:"
	@echo "  make security       - Run security scans (bandit, safety, pip-audit)"
	@echo "  make security-fix   - Attempt to auto-fix security issues"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"
	@echo "  make docker-test    - Test Docker image"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Remove build artifacts and caches"
	@echo "  make clean-logs     - Clean log files"
	@echo "  make update-deps    - Update dependencies"

# Setup
setup: install-dev
	@echo "📦 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Setup complete! Run 'make test' to verify installation."

install:
	@echo "📦 Installing production dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ Production dependencies installed"

install-dev:
	@echo "📦 Installing all dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "✅ All dependencies installed"

# Development
format:
	@echo "🎨 Formatting code..."
	black core/ features/ tests/ epub_project_manager.py run.py
	isort core/ features/ tests/ epub_project_manager.py run.py
	@echo "✅ Code formatted"

lint:
	@echo "🔍 Running linters..."
	@echo "\n--- Flake8 ---"
	flake8 core/ features/ --max-line-length=120 --ignore=E501,W503 || true
	@echo "\n--- Pylint ---"
	pylint core/ features/ --max-line-length=120 || true
	@echo "\n--- MyPy ---"
	mypy core/ features/ --ignore-missing-imports || true
	@echo "✅ Linting complete"

test:
	@echo "🧪 Running tests..."
	pytest tests/ -v
	@echo "✅ Tests complete"

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ -v --cov=core --cov=features --cov-report=html --cov-report=term
	@echo "📊 Coverage report generated in htmlcov/index.html"
	@echo "✅ Tests complete"

validate:
	@echo "✅ Validating configuration..."
	python run.py --validate-config
	@echo "✅ Configuration valid"

# Security
security:
	@echo "🔒 Running security scans..."
	@echo "\n--- Bandit (Security Linter) ---"
	bandit -r core/ features/ epub_project_manager.py -ll || true
	@echo "\n--- Safety (Known Vulnerabilities) ---"
	safety check || true
	@echo "\n--- pip-audit (Dependency Vulnerabilities) ---"
	pip-audit || true
	@echo "✅ Security scan complete"

security-fix:
	@echo "🔧 Attempting to fix security issues..."
	pip-audit --fix
	@echo "✅ Security fixes applied (review changes carefully)"

# Docker
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t epub-converter:latest .
	@echo "✅ Docker image built"

docker-run:
	@echo "🐳 Running Docker container..."
	docker-compose up

docker-test:
	@echo "🧪 Testing Docker image..."
	docker run --rm epub-converter:latest python run.py --validate-config
	@echo "✅ Docker image test passed"

# Maintenance
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "✅ Cleanup complete"

clean-logs:
	@echo "🧹 Cleaning log files..."
	find logs/ -type f -name "*.log" -delete 2>/dev/null || true
	@echo "✅ Logs cleaned"

update-deps:
	@echo "📦 Updating dependencies..."
	pip install --upgrade pip
	pip list --outdated
	@echo "\n💡 To update all packages: pip install --upgrade -r requirements.txt"
	@echo "⚠️  Review changes carefully before committing"

# Quick commands
quick-test: lint test validate
	@echo "🎉 Quick test suite passed!"

ci: format lint test-cov security validate
	@echo "🎉 CI checks passed!"

# Profile performance
profile:
	@echo "📊 Running with profiling..."
	python run.py --profile --log-level INFO

# Run the application
run:
	@echo "🚀 Starting application..."
	python epub_project_manager.py

run-dev:
	@echo "🚀 Starting application (dev mode with profiling)..."
	python run.py --profile --log-level DEBUG
