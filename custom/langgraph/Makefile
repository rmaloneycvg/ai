.PHONY: test test-unit test-integration lint profile serve generate-models clean

# All commands use uv run — no pip, no activation needed.

test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v -m integration

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff format src/ tests/

profile:
	uv run python -m src.main profile

serve:
	uv run python -m src.main serve

budget:
	uv run python -m src.main budget-report

providers:
	uv run python -m src.main providers

generate-models:
	uv run python -m src.models.generate

clean:
	rm -rf .pytest_cache __pycache__ src/__pycache__ tests/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
