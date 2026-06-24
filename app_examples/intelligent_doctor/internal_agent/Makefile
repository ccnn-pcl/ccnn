.PHONY: help install build docker-build docker-clean clean run test dev-run docker-run lint format _version_inject

# project config
PROJECT_NAME := internal-agent
PYTHON := python3
PYTHON_VERSION := $(shell $(PYTHON) --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
IMAGE_NAME := $(PROJECT_NAME)

# version
VERSION_FILE := src/version.py
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_DATE := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')
VERSION := $(shell git describe --tags --always 2>/dev/null || echo "0.1.0")
DOCKER_TAG := $(VERSION)

# color output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show help information
	@echo "$(BLUE)$(PROJECT_NAME) - Makefile commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Dependency management:$(NC)"
	@echo "  $(GREEN)make install$(NC)          - Install project dependencies"
	@echo ""
	@echo "$(YELLOW)Build:$(NC)"
	@echo "  $(GREEN)make build$(NC)            - Build project"
	@echo "  $(GREEN)make docker-build$(NC)     - Build Docker image"
	@echo "  $(GREEN)make docker-push$(NC)      - Push Docker image to registry"
	@echo "  $(GREEN)make docker-clean$(NC)     - Clean Docker images and containers"
	@echo ""
	@echo "$(YELLOW)Run:$(NC)"
	@echo "  $(GREEN)make run$(NC)              - Run application (production mode)"
	@echo "  $(GREEN)make dev-run$(NC)          - Run application (dev mode, hot-reload)"
	@echo "  $(GREEN)make docker-run$(NC)       - Run Docker container"
	@echo ""
	@echo "$(YELLOW)Test & quality:$(NC)"
	@echo "  $(GREEN)make test$(NC)             - Run tests"
	@echo "  $(GREEN)make test-cov$(NC)         - Run tests with coverage report"
	@echo "  $(GREEN)make lint$(NC)             - Lint code"
	@echo "  $(GREEN)make format$(NC)           - Format code"
	@echo ""
	@echo "$(YELLOW)Maintenance:$(NC)"
	@echo "  $(GREEN)make clean$(NC)            - Clean build artifacts and caches"
	@echo "  $(GREEN)make clean-all$(NC)        - Deep clean (including build caches)"
	@echo "  $(GREEN)make version$(NC)          - Show version info"

# ============================================================================
# Dependency management
# ============================================================================

install: ## Install dependencies
	@echo "$(BLUE)Installing project dependencies...$(NC)"
	$(PYTHON) -m pip install -q --break-system-packages -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

# ============================================================================
# Version management & injection
# ============================================================================

_version_inject:
	@echo "$(BLUE)Injecting version info...$(NC)"
	@mkdir -p $$(dirname $(VERSION_FILE))
	@scripts/inject_version.sh "$(VERSION)" "$(GIT_COMMIT)" "$(BUILD_DATE)" "$(VERSION_FILE)"
	@echo "$(GREEN)✓ Version info injected: $(VERSION_FILE)$(NC)"
	@echo "  Version: $(GREEN)$(VERSION)$(NC)"
	@echo "  Commit: $(GREEN)$(GIT_COMMIT)$(NC)"

version: ## Show version info
	@echo "$(BLUE)Version info:$(NC)"
	@echo "  Project version: $(GREEN)$(VERSION)$(NC)"
	@echo "  Git commit: $(GREEN)$(GIT_COMMIT)$(NC)"
	@echo "  Build date: $(GREEN)$(BUILD_DATE)$(NC)"

# ============================================================================
# Build
# ============================================================================

build: _version_inject ## Build project
	@echo "$(BLUE)Building project...$(NC)"
	$(PYTHON) -m py_compile src/main.py
	@echo "$(GREEN)✓ Project built$(NC)"

# ============================================================================
# Docker build
# ============================================================================

docker-build: _version_inject ## Build Docker image
	@echo "$(BLUE)Building Docker image: $(IMAGE_NAME):$(DOCKER_TAG)$(NC)"
	docker build \
		-t $(IMAGE_NAME):$(DOCKER_TAG) \
		-t $(IMAGE_NAME):$(VERSION) \
		.
	@echo "$(GREEN)✓ Docker image built$(NC)"
	@echo "  Image: $(GREEN)$(IMAGE_NAME):$(DOCKER_TAG)$(NC)"
	@echo "  Tag: $(GREEN)$(IMAGE_NAME):$(VERSION)$(NC)"

docker-clean: ## Clean Docker images and containers
	@echo "$(BLUE)Cleaning Docker images and containers...$(NC)"
	@echo "  Stopping related containers..."
	@docker ps -a --filter "ancestor=$(IMAGE_NAME)" -q | xargs -r docker stop 2>/dev/null || true
	@echo "  Removing related containers..."
	@docker ps -a --filter "ancestor=$(IMAGE_NAME)" -q | xargs -r docker rm 2>/dev/null || true
	@echo "  Removing images..."
	@docker images | grep "$(PROJECT_NAME)" | awk '{print $$3}' | xargs -r docker rmi -f 2>/dev/null || true
	@echo "$(GREEN)✓ Docker cleanup done$(NC)"

# ============================================================================
# Run
# ============================================================================

run: ## Run application (production mode)
	@echo "$(BLUE)Starting application...$(NC)"
	$(PYTHON) -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level info

dev-run: ## Run application (dev mode, hot-reload)
	@echo "$(BLUE)Starting application (dev mode)...$(NC)"
	$(PYTHON) -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

docker-run: ## Run Docker container
	@echo "$(BLUE)Starting Docker container...$(NC)"
	docker run -it --rm \
		-p 8000:8000 \
		--name $(PROJECT_NAME) \
		$(IMAGE_NAME):$(DOCKER_TAG)

# ============================================================================
# Tests
# ============================================================================

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTHON) -m pytest tests/ -v --tb=short
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests (with coverage)...$(NC)"
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated: htmlcov/index.html$(NC)"

# ============================================================================
# Code quality
# ============================================================================

lint: ## Lint code
	@echo "$(BLUE)Running linter...$(NC)"
	@if command -v pylint &> /dev/null; then \
		pylint src/ --disable=all --enable=E,F || true; \
	else \
		echo "$(YELLOW)pylint not found, skipping$(NC)"; \
	fi
	@echo "$(GREEN)✓ Lint completed$(NC)"

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@if command -v black &> /dev/null; then \
		black src/ tests/; \
		echo "$(GREEN)✓ Formatted with black$(NC)"; \
	else \
		echo "$(YELLOW)black not found, skipping$(NC)"; \
	fi

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean build artifacts and caches
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup done$(NC)"

clean-all: clean ## Deep clean (including build caches)
	@echo "$(BLUE)Deep cleaning...$(NC)"
	rm -rf build dist
	@echo "$(GREEN)✓ Deep clean done$(NC)"

# Default target
.DEFAULT_GOAL := help
