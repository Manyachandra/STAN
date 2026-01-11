# Makefile for chatbot system
# Common development commands

.PHONY: help install dev-install test test-cov clean run-api docker-up docker-down format lint

help:
	@echo "Chatbot System - Available Commands"
	@echo "===================================="
	@echo "make install       - Install dependencies"
	@echo "make dev-install   - Install with dev dependencies"
	@echo "make test          - Run tests"
	@echo "make test-cov      - Run tests with coverage"
	@echo "make run-api       - Run API server"
	@echo "make run-example   - Run basic example"
	@echo "make docker-up     - Start Docker services"
	@echo "make docker-down   - Stop Docker services"
	@echo "make format        - Format code with black"
	@echo "make lint          - Lint code with ruff"
	@echo "make clean         - Clean temporary files"
	@echo "make redis         - Start Redis in Docker"

install:
	pip install -r requirements.txt
	pip install -e .

dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=chatbot_system --cov-report=html --cov-report=term

run-api:
	python examples/api_server.py

run-example:
	python examples/basic_conversation.py

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@docker-compose ps

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f chatbot-api

redis:
	docker run -d -p 6379:6379 --name chatbot-redis redis:7-alpine
	@echo "Redis started on port 6379"

redis-stop:
	docker stop chatbot-redis
	docker rm chatbot-redis

format:
	black chatbot_system/ examples/ tests/
	@echo "Code formatted with black"

lint:
	ruff check chatbot_system/ examples/ tests/
	@echo "Linting complete"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true
	@echo "Cleaned temporary files"

setup:
	@echo "Running setup..."
	@chmod +x setup.sh
	@./setup.sh

health:
	@curl -s http://localhost:8000/health | python -m json.tool

check-redis:
	@redis-cli ping || echo "Redis not running"

check-env:
	@if [ ! -f .env ]; then echo "⚠ .env file not found"; else echo "✓ .env file exists"; fi
	@if [ -z "$$GEMINI_API_KEY" ]; then echo "⚠ GEMINI_API_KEY not set"; else echo "✓ GEMINI_API_KEY is set"; fi

