#===============================================================
# Surgical Agent - Makefile
#===============================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

PROJECT_NAME = surgical-agent
PROJECT_DIR := $(shell pwd)
PYTHON := python3
PIP := pip3
VENV_DIR := .venv

BUILD_VERSION ?= 0.1.0
VERSION_MAJOR ?= 0
VERSION_MINOR ?= 1
VERSION_PATCH ?= 0
BUILD_TIME := $(shell date '+%Y-%m-%d %H:%M:%S')
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

IMAGE_NAME ?= surgical-agent
IMAGE_TAG = $(IMAGE_NAME):$(BUILD_VERSION)
PLATFORM ?= linux/amd64
REMOTE_REPO = 192.168.64.60:31304
REMOTE_GROUP = medical-app
REMOTE_IMAGE = $(REMOTE_REPO)/$(REMOTE_GROUP)/$(IMAGE_NAME):$(BUILD_VERSION)

SERVICE_PORT ?= 8004
SERVICE_NAME ?= surgical

#===============================================================
# Phony targets definition
#===============================================================
.PHONY: help install dev test run clean build push version inject-version \
        lint format check-env docker-build docker-push poetry-install

#===============================================================
# Help target - Show all avaliable make commands
#===============================================================
help:
	@echo "=================================="
	@echo "$(PROJECT_NAME) - Makefile commands"
	@echo "=================================="
	@echo ""
	@echo " Basic commands:"
	@echo "  make help               "
	@echo "  make version            "
	@echo ""
	@echo "  Build and Push:"
	@echo "  make install            "
	@echo "  make build              "
	@echo "  make push               "
	@echo ""
	@echo "  Run and test:"
	@echo "  make run                "
	@echo "  make dev                "
	@echo "  make test               "
	@echo ""
	@echo "  Cleanup and lint:"
	@echo "  make clean              "
	@echo "  make lint               "
	@echo "  make format             "
	@echo ""
	@echo "  Tools:"
	@echo "  make inject-version     "
	@echo ""
	@echo "version: $(BUILD_VERSION) (Git commit: $(GIT_COMMIT))"
	@echo "platform: $(PLATFORM)"
	@echo ""

#===============================================================
# Version Info
#===============================================================
version:
	@echo "=================================="
	@echo "$(PROJECT_NAME) Version Information"
	@echo "=================================="
	@echo "Version: $(BUILD_VERSION)"
	@echo "Major: $(VERSION_MAJOR)"
	@echo "Minor: $(VERSION_MINOR)"
	@echo "Patch: $(VERSION_PATCH)"
	@echo "Git commit: $(GIT_COMMIT)"
	@echo "Build time: $(BUILD_TIME)"
	@echo ""

inject-version:
	@echo "Injecting version info into src/version.py ..."
	@mkdir -p src
	@python3 scripts/inject_version.py $(BUILD_VERSION) $(VERSION_MAJOR) $(VERSION_MINOR) $(VERSION_PATCH) "$(GIT_COMMIT)" "$(BUILD_TIME)"
	@echo "Version injection completed"

#===============================================================
# Environment and dependencies
#===============================================================
check-env:
	@echo "Checking environment..."
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo " Python3 not installed"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo " Docker not installed"; }
	@echo "Environment check passed"

install: check-env
	@echo "Installing dependencies..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "Virtual environment created"; \
	fi
	@. $(VENV_DIR)/bin/activate && $(PIP) install --upgrade pip setuptools wheel
	@. $(VENV_DIR)/bin/activate && $(PIP) install -r requirements.txt
	@echo "Dependency installation completed"

poetry-install: check-env
	@echo "Installing dependencies with Poetry..."
	@command -v poetry >/dev/null 2>&1 || { echo " Poetry not installed"; exit 1; }
	poetry install
	@echo "Poetry dependency installation completed"

#===============================================================
# Development and testing
#===============================================================
run: install inject-version
	@echo "Starting application (port: $(SERVICE_PORT))..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) -m uvicorn src.main:app \
		--host 0.0.0.0 --port $(SERVICE_PORT) --reload

dev: install inject-version
	@echo " Starting application in development mode (with hot reload, port: $(SERVICE_PORT))..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) -m uvicorn src.main:app \
		--host 0.0.0.0 --port $(SERVICE_PORT) --reload --log-level debug

test: install
	@echo "Running tests..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) -m pytest tests/ -v --cov=src
	@echo "Tests completed"

#===============================================================
# Code quality
#===============================================================
lint: install
	@echo "Running code linting..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) -m pylint src/ || true
	@echo "Code linting completed"

format: install
	@echo "Formatting code..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) -m black src/ tests/ || true
	@. $(VENV_DIR)/bin/activate && $(PYTHON) -m isort src/ tests/ || true
	@echo "Code formatting completed"

#===============================================================
# Docker build and push
#===============================================================
docker-build: check-env
	@echo "   Building Docker image..."
	@echo "   Image tag: $(IMAGE_TAG)"
	@echo "   Platform: $(PLATFORM)"
	docker build \
		--platform $(PLATFORM) \
		--build-arg BUILD_VERSION=$(BUILD_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_TIME="$(BUILD_TIME)" \
		-t $(IMAGE_TAG) .
	@echo "Docker image built successfully"

build: docker-build
	@echo "Build successful: $(IMAGE_TAG)"

docker-push: docker-build
	@echo "Pushing image to remote registry..."
	@echo "   Target: $(REMOTE_IMAGE)"
	docker tag $(IMAGE_TAG) $(REMOTE_IMAGE)
	docker push $(REMOTE_IMAGE)
	@echo "Image pushed successfully"

push: docker-push
	@echo "Push successful"

#===============================================================
# Cleanup
#===============================================================
clean:
	@echo "Cleaning temporary files..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup completed"

#===============================================================
# Default target
#===============================================================
all: clean install test build
	@echo "Full build process completed"