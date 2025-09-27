# Makefile for Zerodha News Analyzer

.PHONY: help install test test-unit test-integration test-coverage clean lint format

help:	## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:	## Install dependencies
	pip install -r requirements.txt

install-test:	## Install test dependencies
	pip install -r requirements-test.txt

test:	## Run all tests
	python tests/test_runner.py all

test-unit:	## Run unit tests only
	python tests/test_runner.py unit

test-integration:	## Run integration tests only
	python tests/test_runner.py integration

test-coverage:	## Run tests with coverage report
	python tests/test_runner.py coverage

test-quick:	## Run tests without verbose output
	pytest tests/ -q

clean:	## Clean up generated files
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

lint:	## Run linting (if flake8 is installed)
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 *.py utils/ tests/ --max-line-length=100 --ignore=E203,W503; \
	else \
		echo "flake8 not installed. Install with: pip install flake8"; \
	fi

format:	## Format code (if black is installed)
	@if command -v black >/dev/null 2>&1; then \
		black *.py utils/ tests/ --line-length=100; \
	else \
		echo "black not installed. Install with: pip install black"; \
	fi

run:	## Run the news analysis pipeline
	python pipeline_orchestrator.py

run-legacy:	## Run using legacy entry point
	python zerodha_news_analyzer.py

setup-dev:	## Setup development environment
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	@echo "Development environment setup complete!"

check:	## Run all checks (lint + test)
	@echo "Running linting..."
	@$(MAKE) lint
	@echo "Running tests..."
	@$(MAKE) test

demo:	## Run a quick demo (scrape + analyze)
	@echo "Running demo - this will scrape real news and use API credits"
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	python pipeline_orchestrator.py