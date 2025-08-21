.PHONY: dev test lint build run deploy clean

# Development
dev:
	PYTHONPATH=. uvicorn app.main:app --reload --port 8080

# Testing
test:
	pytest -v

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term

test-ci:
	pytest -v --cov=app --cov-report=xml
	flake8 app/ --max-line-length=88 --extend-ignore=E203,W503
	black --check app/

# Linting
lint:
	ruff check app tests
	black --check app tests

format:
	black app tests
	ruff check --fix app tests

# Build
build:
	docker build -t tdg-mvp:latest .

# Run
run:
	docker run -p 8080:8080 --env-file .env tdg-mvp:latest

# Deploy
deploy:
	fly deploy

# Clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf artifacts tmp

# Setup
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov ruff black
