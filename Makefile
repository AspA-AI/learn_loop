.PHONY: help install-backend install-frontend run-backend run-frontend migrate remigrate clean-db clean-db-force seed seed-test migrate-topics test-backend test-frontend lint-backend lint-frontend format-backend format-frontend setup reset-db

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Directories
API_DIR := api
CLIENT_DIR := client
DB_DIR := $(API_DIR)/database

# Python and Node commands
# Check if venv exists in api/venv from the learn_loop directory
# When we cd into API_DIR, we use relative paths (venv/bin/python)
HAS_VENV := $(shell if [ -f $(API_DIR)/venv/bin/python ]; then echo "yes"; else echo "no"; fi)
ifeq ($(HAS_VENV),yes)
	PYTHON := venv/bin/python
	PIP := venv/bin/pip
	UVICORN := venv/bin/uvicorn
else
	PYTHON := python3
	PIP := pip3
	UVICORN := uvicorn
endif
NPM := npm

help: ## Show this help message
	@echo "$(BLUE)Learn Loop - Makefile Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make setup              - Full project setup (backend + frontend)"
	@echo "  make install-backend    - Install Python dependencies"
	@echo "  make install-frontend   - Install Node dependencies"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make run-backend        - Start FastAPI backend server"
	@echo "  make run-frontend        - Start React frontend dev server"
	@echo "  make run                - Run both backend and frontend (parallel)"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make migrate            - Run database migrations"
	@echo "  make remigrate          - Drop all tables and re-run migrations"
	@echo "  make clean-db           - Delete all data from tables (keeps schema)"
	@echo "  make clean-db-force     - Delete all data without confirmation"
	@echo "  make seed               - Seed database with test data"
	@echo "  make seed-test          - Seed test children (Leo & Mia)"
	@echo "  make migrate-topics     - Migrate topics from children.target_topic to child_topics"
	@echo "  make reset-db           - Full database reset (remigrate + seed)"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test-backend       - Run backend tests"
	@echo "  make test-frontend      - Run frontend tests"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make lint-backend       - Lint backend code"
	@echo "  make lint-frontend      - Lint frontend code"
	@echo "  make format-backend     - Format backend code"
	@echo "  make format-frontend    - Format frontend code"
	@echo ""

# ============================================================================
# Setup Commands
# ============================================================================

setup: install-backend install-frontend ## Full project setup
	@echo "$(GREEN)✓ Project setup complete!$(NC)"

install-backend: ## Install Python dependencies
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd $(API_DIR) && $(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: ## Install Node dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd $(CLIENT_DIR) && $(NPM) install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

# ============================================================================
# Development Commands
# ============================================================================

run-backend: ## Start FastAPI backend server
	@echo "$(BLUE)Starting backend server...$(NC)"
	cd $(API_DIR) && $(UVICORN) main:app --reload --host 0.0.0.0 --port 8000

run-frontend: ## Start React frontend dev server
	@echo "$(BLUE)Starting frontend dev server...$(NC)"
	cd $(CLIENT_DIR) && $(NPM) run dev

run: ## Run both backend and frontend (parallel)
	@echo "$(BLUE)Starting both backend and frontend...$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:5173$(NC)"
	@make -j2 run-backend run-frontend

# ============================================================================
# Database Commands
# ============================================================================

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) database/migrate.py
	@echo "$(GREEN)✓ Migrations complete$(NC)"

remigrate: ## Drop all tables and re-run migrations
	@echo "$(YELLOW)⚠️  Dropping all tables and re-running migrations...$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) database/migrate.py
	@echo "$(GREEN)✓ Re-migration complete$(NC)"

clean-db: ## Delete all data from tables (keeps schema)
	@echo "$(YELLOW)⚠️  Cleaning all database data...$(NC)"
	@echo "$(RED)This will delete all data but keep the schema$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) database/clean.py
	@echo "$(GREEN)✓ Database cleaned$(NC)"

clean-db-force: ## Delete all data without confirmation
	@echo "$(YELLOW)⚠️  Cleaning all database data (no confirmation)...$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) database/clean.py --yes
	@echo "$(GREEN)✓ Database cleaned$(NC)"

seed: ## Seed database with test data
	@echo "$(BLUE)Seeding database...$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) database/seed.py
	@echo "$(GREEN)✓ Database seeded$(NC)"

seed-test: ## Seed test children (Leo & Mia)
	@echo "$(BLUE)Seeding test children...$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) database/seed_test_child.py
	@echo "$(GREEN)✓ Test children seeded$(NC)"

migrate-topics: ## Migrate topics from children.target_topic to child_topics
	@echo "$(BLUE)Migrating topics...$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) database/migrate_topics.py
	@echo "$(GREEN)✓ Topics migrated$(NC)"

reset-db: remigrate seed-test migrate-topics ## Full database reset (remigrate + seed)
	@echo "$(GREEN)✓ Database reset complete$(NC)"

# ============================================================================
# Testing Commands
# ============================================================================

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) -m pytest tests/ -v
	@echo "$(GREEN)✓ Backend tests complete$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd $(CLIENT_DIR) && $(NPM) test
	@echo "$(GREEN)✓ Frontend tests complete$(NC)"

# ============================================================================
# Code Quality Commands
# ============================================================================

lint-backend: ## Lint backend code
	@echo "$(BLUE)Linting backend code...$(NC)"
	@echo "$(YELLOW)Note: Install flake8 or pylint for linting$(NC)"
	@cd $(API_DIR) && $(PYTHON) -m flake8 . --exclude=venv,__pycache__ || echo "$(YELLOW)flake8 not installed$(NC)"

lint-frontend: ## Lint frontend code
	@echo "$(BLUE)Linting frontend code...$(NC)"
	cd $(CLIENT_DIR) && $(NPM) run lint || echo "$(YELLOW)lint script not configured$(NC)"

format-backend: ## Format backend code
	@echo "$(BLUE)Formatting backend code...$(NC)"
	@echo "$(YELLOW)Note: Install black for formatting$(NC)"
	@cd $(API_DIR) && $(PYTHON) -m black . --exclude=venv || echo "$(YELLOW)black not installed$(NC)"

format-frontend: ## Format frontend code
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	cd $(CLIENT_DIR) && $(NPM) run format || echo "$(YELLOW)format script not configured$(NC)"

# ============================================================================
# Utility Commands
# ============================================================================

check-env: ## Check if .env file exists
	@if [ ! -f $(API_DIR)/.env ]; then \
		echo "$(RED)✗ .env file not found in $(API_DIR)/$(NC)"; \
		echo "$(YELLOW)Please create a .env file with required environment variables$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ .env file found$(NC)"; \
	fi

init-weaviate: ## Initialize Weaviate schema
	@echo "$(BLUE)Initializing Weaviate schema...$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) scripts/init_weaviate.py
	@echo "$(GREEN)✓ Weaviate initialized$(NC)"

verify-logic: ## Verify agent logic
	@echo "$(BLUE)Verifying agent logic...$(NC)"
	cd $(API_DIR) && PYTHONPATH=. $(PYTHON) scripts/verify_logic.py
	@echo "$(GREEN)✓ Logic verification complete$(NC)"

