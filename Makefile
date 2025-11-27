# ============================================
# PRODUCTION MAKEFILE
# ============================================

.PHONY: help install dev test lint format docker-build docker-run docker-stop clean

help:  ## Show this help message
	@echo "=========================================="
	@echo "Travel Assistant - Available Commands"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

dev:  ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black flake8 mypy isort

test:  ## Run tests
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=app --cov-report=html

lint:  ## Run linters
	@echo "🔍 Running linters..."
	flake8 app/ tests/
	mypy app/

format:  ## Format code
	@echo "✨ Formatting code..."
	black app/ tests/
	isort app/ tests/

docker-build:  ## Build Docker image
	@echo "🔨 Building Docker image..."
	docker-compose build

docker-run:  ## Run with Docker Compose
	@echo "🚀 Starting services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "📍 API: http://localhost:8000"
	@echo "📚 Docs: http://localhost:8000/docs"

docker-stop:  ## Stop Docker services
	@echo "🛑 Stopping services..."
	docker-compose down

docker-logs:  ## View Docker logs
	docker-compose logs -f travel-assistant

clean:  ## Clean temporary files
	@echo "🧹 Cleaning..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	@echo "✅ Cleaned!"

setup-env:  ## Create .env from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file"; \
		echo "⚠️  Please edit .env and add your GOOGLE_API_KEY"; \
	else \
		echo "⚠️  .env already exists"; \
	fi

check-env:  ## Validate environment configuration
	@echo "🔍 Checking environment..."
	@python config.py
