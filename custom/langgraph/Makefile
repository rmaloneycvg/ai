.PHONY: help test test-unit test-integration test-live lint format \
       list-agents list-skills execute execute-skill execute-orch \
       run provider-test profile budget providers tools disclose serve \
       generate-models infra-up infra-down infra-logs clean

# Default: show help
.DEFAULT_GOAL := help

# All commands use uv run — no pip, no activation needed.

# --- Help ---

help: ## Show this help message
	@echo ""
	@echo "LangGraph Workspace — Makefile Commands"
	@echo "========================================"
	@echo ""
	@echo "Usage: make <target> [ARGS]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make execute-agent AGENT=general-dev TASK=\"Show project structure\""
	@echo "  make execute-skill SKILL=general-debug TASK=\"API returns 500\""
	@echo "  make execute-orch AGENT=react-orchestrator TASK=\"scaffold: a Button\""
	@echo "  make run TASK=\"Create a skill for database migrations\""
	@echo "  make profile MODEL=qwen2.5:14b"
	@echo ""

# --- Execution (Runtime) ---

list-agents: ## List available agents from the workspace
	uv run python -m src.main list-agents

list-skills: ## List available skills from the workspace
	uv run python -m src.main list-skills

execute-agent: ## Execute an agent (AGENT=name TASK="..." [MODEL=x])
	@test -n "$(AGENT)" || (echo "Error: AGENT is required. Usage: make execute-agent AGENT=general-dev TASK=\"...\"" && exit 1)
	@test -n "$(TASK)" || (echo "Error: TASK is required." && exit 1)
	uv run python -m src.main execute --agent $(AGENT) $(if $(MODEL),--model $(MODEL),) "$(TASK)"

execute-skill: ## Execute a skill workflow (SKILL=name TASK="..." [MODEL=x])
	@test -n "$(SKILL)" || (echo "Error: SKILL is required. Usage: make execute-skill SKILL=general-debug TASK=\"...\"" && exit 1)
	@test -n "$(TASK)" || (echo "Error: TASK is required." && exit 1)
	uv run python -m src.main execute --skill $(SKILL) $(if $(MODEL),--model $(MODEL),) "$(TASK)"

execute-orch: ## Execute an orchestrator pipeline (AGENT=name TASK="..." [MODEL=x])
	@test -n "$(AGENT)" || (echo "Error: AGENT is required. Usage: make execute-orch AGENT=react-orchestrator TASK=\"...\"" && exit 1)
	@test -n "$(TASK)" || (echo "Error: TASK is required." && exit 1)
	uv run python -m src.main execute --agent $(AGENT) $(if $(MODEL),--model $(MODEL),) "$(TASK)"

execute-ni: ## Execute non-interactive (AGENT or SKILL, TASK="..." — auto-approves)
	@test -n "$(TASK)" || (echo "Error: TASK is required." && exit 1)
	uv run python -m src.main execute $(if $(AGENT),--agent $(AGENT),) $(if $(SKILL),--skill $(SKILL),) --no-interactive $(if $(MODEL),--model $(MODEL),) "$(TASK)"

# --- Artifact Creation ---

run: ## Create a new artifact via supervisor (TASK="...")
	@test -n "$(TASK)" || (echo "Error: TASK is required. Usage: make run TASK=\"Create a skill for...\"" && exit 1)
	uv run python -m src.main run "$(TASK)"

# --- Model & Provider Management ---

provider-test: ## Test provider connection (MODEL=llama3.1:8b)
	uv run python -m src.main provider-test --model $(or $(MODEL),llama3.1:8b)

profile: ## Profile/calibrate a model (MODEL=llama3.1:8b)
	uv run python -m src.main profile --model $(or $(MODEL),llama3.1:8b)

budget: ## Show token budget report (MODEL=llama3.1:8b)
	uv run python -m src.main budget-report --model $(or $(MODEL),llama3.1:8b)

providers: ## List configured providers and models
	uv run python -m src.main providers

tools: ## List tools for a phase (PHASE=full)
	uv run python -m src.main tools --phase $(or $(PHASE),full)

disclose: ## Show progressive disclosure for a query (MODEL=x QUERY="...")
	uv run python -m src.main disclose --model $(or $(MODEL),llama3.1:8b) --query "$(or $(QUERY),skill schema)"

# --- Server ---

serve: ## Start REST + WebSocket server (PORT=8765)
	uv run python -m src.main serve --port $(or $(PORT),8765)

# --- Testing ---

test: ## Run all tests (unit + integration)
	uv run pytest tests/ -v --ignore=tests/integration/test_tools_live.py

test-unit: ## Run unit tests only (no external services needed)
	uv run pytest tests/unit/ -v

test-integration: ## Run integration tests (requires Ollama)
	uv run pytest tests/integration/ -v -m integration

test-live: ## Run live tool tests (requires Postgres, Prometheus, etc.)
	uv run pytest tests/integration/test_tools_live.py -v -m integration

test-runtime: ## Run runtime-specific tests
	uv run pytest tests/unit/test_loader.py tests/unit/test_model_mapper.py tests/unit/test_hooks.py tests/unit/test_skill_runtime.py tests/unit/test_orchestrator.py -v

# --- Code Quality ---

lint: ## Run linter (ruff check + format check)
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format: ## Auto-format code
	uv run ruff check src/ tests/ --fix
	uv run ruff format src/ tests/

# --- Code Generation ---

generate-models: ## Generate Pydantic models from JSON schemas
	uv run python -m src.models.generate

# --- Infrastructure ---

infra-up: ## Start infrastructure services (Postgres, Redis via docker-compose)
	docker compose up -d --wait

infra-down: ## Stop and remove infrastructure containers + volumes
	docker compose down -v

infra-logs: ## Tail infrastructure service logs
	docker compose logs -f

# --- Maintenance ---

clean: ## Remove caches and compiled files
	rm -rf .pytest_cache __pycache__ src/__pycache__ tests/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-output: ## Remove all generated artifacts in output/
	rm -rf output/skills/* output/agents/* output/steering/*/* output/tools/*
	@echo "Cleaned output/ directory"

setup: ## Initial setup (sync deps, copy env, verify ollama)
	uv sync
	@test -f .env || cp .env.example .env
	@echo "✓ Dependencies synced"
	@echo "✓ .env file ready (edit if needed)"
	@curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && echo "✓ Ollama is running" || echo "⚠ Ollama not detected — start it with: ollama serve"
