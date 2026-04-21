# =============================================================================
# Carputer Makefile
# =============================================================================
# Common commands for development, testing, and deployment
#
# Usage: make <target>
# Run `make` or `make help` to see available targets
# =============================================================================

.PHONY: help check-ports up down build rebuild logs shell db-shell test lint clean deploy \
        buildx-setup buildx-api buildx-frontend buildx-backend buildx-all

# Default target
.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DOCKER_COMPOSE := docker compose
PI_HOST ?= emb_usr@10.200.110.128
PI_DIR := /opt/carputer

# Multi-arch build configuration
REGISTRY ?= ghcr.io/odometer-labs
PLATFORMS := linux/amd64,linux/arm64
BUILDX_BUILDER := carputer-builder
VERSION ?= latest

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
help: ## Show this help message
	@echo ""
	@echo "$(CYAN)Carputer Development Commands$(RESET)"
	@echo "=============================="
	@echo ""
	@echo "$(GREEN)Docker:$(RESET)"
	@grep -E '^(up|down|build|rebuild|logs|logs-api|logs-frontend|ps|clean):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@grep -E '^(dev|dev-frontend|dev-api|shell-api|shell-frontend|test|test-api|test-frontend|test-backend|lint|setup|install-frontend|install-backend):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Database:$(RESET)"
	@grep -E '^db-' $(MAKEFILE_LIST) | grep '## ' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Deployment:$(RESET)"
	@grep -E '^(deploy|deploy-prod|pi-ssh|pi-logs|pi-status|pi-restart):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Multi-arch Builds:$(RESET)"
	@grep -E '^buildx-' $(MAKEFILE_LIST) | grep '## ' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# -----------------------------------------------------------------------------
# Docker Commands
# -----------------------------------------------------------------------------
check-ports: ## Check if required ports are available
	@if command -v ss >/dev/null 2>&1; then \
		if ss -tlnp 2>/dev/null | grep -q ':5432 '; then \
			echo "$(RED)ERROR: Port 5432 is already in use!$(RESET)"; \
			echo ""; \
			echo "Something is already listening on the PostgreSQL port."; \
			echo "Docker cannot start the database container."; \
			echo ""; \
			echo "$(YELLOW)To fix on Linux/Pi:$(RESET)"; \
			echo "  sudo systemctl stop postgresql"; \
			echo "  sudo systemctl disable postgresql"; \
			echo ""; \
			echo "$(YELLOW)To fix on macOS:$(RESET)"; \
			echo "  brew services stop postgresql"; \
			echo ""; \
			exit 1; \
		fi; \
	elif command -v lsof >/dev/null 2>&1; then \
		if lsof -i :5432 >/dev/null 2>&1; then \
			echo "$(RED)ERROR: Port 5432 is already in use!$(RESET)"; \
			echo ""; \
			lsof -i :5432 2>/dev/null || true; \
			echo ""; \
			echo "$(YELLOW)Stop the process above before running 'make up'$(RESET)"; \
			exit 1; \
		fi; \
	fi

up: check-ports ## Start all services (api, frontend, db, adminer)
	$(DOCKER_COMPOSE) up -d
	@echo ""
	@echo "$(GREEN)Services started:$(RESET)"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API:      http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Adminer:  http://localhost:8080"

down: ## Stop all services
	$(DOCKER_COMPOSE) down

build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

rebuild: ## Rebuild all images from scratch (no cache)
	$(DOCKER_COMPOSE) build --no-cache

logs: ## Follow logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-api: ## Follow API logs only
	$(DOCKER_COMPOSE) logs -f api

logs-frontend: ## Follow frontend logs only
	$(DOCKER_COMPOSE) logs -f frontend

ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

clean: ## Stop services and remove volumes (WARNING: deletes database!)
	@echo "$(YELLOW)WARNING: This will delete all data including the database!$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_COMPOSE) down -v

# -----------------------------------------------------------------------------
# Development
# -----------------------------------------------------------------------------
dev: up ## Start services and open frontend in browser
	@sleep 2
	@command -v open >/dev/null && open http://localhost:3000 || echo "Open http://localhost:3000 in your browser"

dev-frontend: ## Run frontend dev server locally (hot reload)
	cd frontend/carputer-web-app && npm run dev

dev-api: ## Run API locally (requires db running)
	cd api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

shell-api: ## Open shell in API container
	$(DOCKER_COMPOSE) exec api /bin/sh

shell-frontend: ## Open shell in frontend container
	$(DOCKER_COMPOSE) exec frontend /bin/sh

# -----------------------------------------------------------------------------
# Testing & Linting
# -----------------------------------------------------------------------------
test: ## Run all tests
	@echo "$(CYAN)Running API tests...$(RESET)"
	$(DOCKER_COMPOSE) exec api pytest || true
	@echo ""
	@echo "$(CYAN)Running frontend tests...$(RESET)"
	cd frontend/carputer-web-app && npm test || true
	@echo ""
	@echo "$(CYAN)Running backend tests...$(RESET)"
	cd backend/geotracker && uv run pytest || true

test-api: ## Run API tests only
	$(DOCKER_COMPOSE) exec api pytest

test-frontend: ## Run frontend tests only
	cd frontend/carputer-web-app && npm test

test-backend: ## Run backend/geotracker tests only
	cd backend/geotracker && uv run pytest

lint: ## Run linters on all code
	@echo "$(CYAN)Linting frontend...$(RESET)"
	cd frontend/carputer-web-app && npm run lint || true
	@echo ""
	@echo "$(CYAN)Type-checking frontend...$(RESET)"
	cd frontend/carputer-web-app && npm run type-check || true

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
db-shell: ## Open psql shell in database container
	$(DOCKER_COMPOSE) exec db psql -U $${POSTGRES_USER:-carputer} -d $${POSTGRES_DB:-carputer}

db-logs: ## Follow database logs
	$(DOCKER_COMPOSE) logs -f db

db-backup: ## Backup database to ./backups/
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec db pg_dump -U $${POSTGRES_USER:-carputer} $${POSTGRES_DB:-carputer} > backups/carputer_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup saved to backups/$(RESET)"

db-restore: ## Restore database from backup (usage: make db-restore FILE=backups/xxx.sql)
	@test -n "$(FILE)" || (echo "$(YELLOW)Usage: make db-restore FILE=backups/xxx.sql$(RESET)" && exit 1)
	$(DOCKER_COMPOSE) exec -T db psql -U $${POSTGRES_USER:-carputer} -d $${POSTGRES_DB:-carputer} < $(FILE)
	@echo "$(GREEN)Database restored from $(FILE)$(RESET)"

# -----------------------------------------------------------------------------
# Deployment (Raspberry Pi)
# -----------------------------------------------------------------------------
deploy: ## Deploy to Pi (builds on device)
	@echo "$(CYAN)Deploying to $(PI_HOST) (building on device)...$(RESET)"
	ssh $(PI_HOST) "cd $(PI_DIR) && git pull && docker compose build && docker compose up -d"
	@echo "$(GREEN)Deployment complete!$(RESET)"

deploy-prod: ## Deploy to Pi using pre-built images (faster!)
	@echo "$(CYAN)Deploying to $(PI_HOST) (using pre-built images)...$(RESET)"
	ssh $(PI_HOST) "cd $(PI_DIR) && git pull && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d"
	@echo "$(GREEN)Deployment complete!$(RESET)"

pi-ssh: ## SSH into the Raspberry Pi
	ssh $(PI_HOST)

pi-logs: ## View Docker logs on Pi
	ssh $(PI_HOST) "cd $(PI_DIR) && docker compose logs -f"

pi-status: ## Check service status on Pi
	ssh $(PI_HOST) "cd $(PI_DIR) && docker compose ps"

pi-restart: ## Restart all services on Pi
	ssh $(PI_HOST) "cd $(PI_DIR) && docker compose restart"

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
setup: ## Initial setup: copy .env.example and install deps
	@test -f .env || cp .env.example .env
	@echo "$(GREEN).env file ready - edit it with your credentials$(RESET)"
	@echo ""
	@echo "Installing frontend dependencies..."
	cd frontend/carputer-web-app && npm install
	@echo ""
	@echo "$(GREEN)Setup complete! Run 'make up' to start services.$(RESET)"

install-frontend: ## Install frontend npm dependencies
	cd frontend/carputer-web-app && npm install

install-backend: ## Install backend Python dependencies
	cd backend/geotracker && uv sync
# -----------------------------------------------------------------------------
# Multi-arch Builds (for Raspberry Pi arm64 + Mac/CI amd64)
# -----------------------------------------------------------------------------
# These targets use docker buildx to create images for both architectures.
# Images are pushed to the container registry (default: ghcr.io/odometer-labs)
#
# Prerequisites:
#   - Docker with buildx support (Docker Desktop or buildx plugin)
#   - Logged into registry: docker login ghcr.io
#
# Usage:
#   make buildx-setup              # One-time setup
#   make buildx-all VERSION=v1.0   # Build and push all images
# -----------------------------------------------------------------------------

buildx-setup: ## Set up docker buildx for multi-arch builds (one-time)
	@echo "$(CYAN)Setting up docker buildx for multi-platform builds...$(RESET)"
	@docker buildx inspect $(BUILDX_BUILDER) >/dev/null 2>&1 || \
		docker buildx create --name $(BUILDX_BUILDER) --driver docker-container --bootstrap
	@docker buildx use $(BUILDX_BUILDER)
	@echo "$(GREEN)Buildx ready! Builder: $(BUILDX_BUILDER)$(RESET)"
	@echo "Platforms: $(PLATFORMS)"

buildx-api: ## Build and push API image for amd64+arm64
	@echo "$(CYAN)Building API image for $(PLATFORMS)...$(RESET)"
	docker buildx build \
		--platform $(PLATFORMS) \
		--tag $(REGISTRY)/carputer-api:$(VERSION) \
		--tag $(REGISTRY)/carputer-api:latest \
		--push \
		./api
	@echo "$(GREEN)API image pushed: $(REGISTRY)/carputer-api:$(VERSION)$(RESET)"

buildx-frontend: ## Build and push frontend image for amd64+arm64
	@echo "$(CYAN)Building frontend image for $(PLATFORMS)...$(RESET)"
	docker buildx build \
		--platform $(PLATFORMS) \
		--tag $(REGISTRY)/carputer-frontend:$(VERSION) \
		--tag $(REGISTRY)/carputer-frontend:latest \
		--push \
		./frontend/carputer-web-app
	@echo "$(GREEN)Frontend image pushed: $(REGISTRY)/carputer-frontend:$(VERSION)$(RESET)"

buildx-backend: ## Build and push geotracker backend image for amd64+arm64
	@echo "$(CYAN)Building backend image for $(PLATFORMS)...$(RESET)"
	docker buildx build \
		--platform $(PLATFORMS) \
		--tag $(REGISTRY)/carputer-backend:$(VERSION) \
		--tag $(REGISTRY)/carputer-backend:latest \
		--push \
		./backend
	@echo "$(GREEN)Backend image pushed: $(REGISTRY)/carputer-backend:$(VERSION)$(RESET)"

buildx-all: buildx-api buildx-frontend buildx-backend ## Build and push all images for amd64+arm64
	@echo ""
	@echo "$(GREEN)All images built and pushed!$(RESET)"
	@echo "  $(REGISTRY)/carputer-api:$(VERSION)"
	@echo "  $(REGISTRY)/carputer-frontend:$(VERSION)"
	@echo "  $(REGISTRY)/carputer-backend:$(VERSION)"

buildx-local: ## Build multi-arch images locally (no push, for testing)
	@echo "$(CYAN)Building all images locally for $(PLATFORMS)...$(RESET)"
	docker buildx build --platform $(PLATFORMS) --tag carputer-api:local ./api
	docker buildx build --platform $(PLATFORMS) --tag carputer-frontend:local ./frontend/carputer-web-app
	docker buildx build --platform $(PLATFORMS) --tag carputer-backend:local ./backend
	@echo "$(GREEN)Local multi-arch build complete!$(RESET)"