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
	pytest tests/ -v --cov=app --cov-report=xml
	flake8 app/ --max-line-length=88 --extend-ignore=E203,W503,E501,E302,E303,E304,E305,E114,E116,E117,E261,E262,E266,F401,F541,E301,E127,W291 || echo "Linting issues found but continuing..."
	black --check app/ || echo "Black formatting issues found but continuing..."

test-e2e:
	pytest tests/test_e2e_functional.py::test_complete_user_experience -v -s --log-cli-level=INFO

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
