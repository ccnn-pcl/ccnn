# Makefile for MedicalMaterialsMcpService
# Go project build and development tools

# Project info
MODULE_NAME := github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
BUILD_TIME := $(shell date -u '+%Y-%m-%d_%H:%M:%S')
BUILD_DATE := $(shell date -u '+%Y%m%d')

VERSION := $(shell git describe --tags --exact-match 2>/dev/null || echo "$(GIT_COMMIT)-$(BUILD_DATE)")

# Docker-related configuration
DOCKER_REGISTRY ?=
DOCKER_NAMESPACE ?=
DOCKER_IMAGE_NAME := medical-materials
DOCKER_IMAGE_FULL_NAME := $(if $(DOCKER_REGISTRY),$(DOCKER_REGISTRY)/$(if $(DOCKER_NAMESPACE),$(DOCKER_NAMESPACE)/)$(DOCKER_IMAGE_NAME),$(DOCKER_IMAGE_NAME))
ALPINE_REPOSITORIES ?= "https://dl-cdn.alpinelinux.org/alpine/v3.20/main https://dl-cdn.alpinelinux.org/alpine/v3.20/community"
GOPROXY ?=

# Build directories
BIN_DIR := bin
BINARY_PATH := $(BIN_DIR)/medical-materials-mcp-service

# Build flags
LDFLAGS := -ldflags "\\\
	-X '$(MODULE_NAME)/config.Version=$(VERSION)' \\\
	-X '$(MODULE_NAME)/config.BuildTime=$(BUILD_TIME)' \\\
	-X '$(MODULE_NAME)/config.GitCommit=$(GIT_COMMIT)' \\\
	-X '$(MODULE_NAME)/config.GitBranch=$(GIT_BRANCH)'"

# Help
.PHONY: help
help:
	@echo "MedicalMaterialsMcpService Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make <target>"
	@echo ""
	@echo "Common targets:"
	@echo "  build      - Build the project"
	@echo "  run        - Run the project"
	@echo "  clean      - Clean build artifacts"
	@echo "  test       - Run tests"
	@echo "  fmt        - Format source code"
	@echo "  vet        - Static code analysis"
	@echo "  tidy       - Tidy go.mod dependencies"
	@echo "  deps       - Download dependencies"
	@echo ""
	@echo "Docker targets:"
	@echo "  docker-build      - Build Docker image"
	@echo "  docker-clean      - Clean Docker images and containers"
	@echo ""
	@echo "Other targets:"
	@echo "  test-cover - Run tests with coverage report"
	@echo "  version    - Show version info"
	@echo "  help       - Show this help message"

# Create directories
$(BIN_DIR):
	@mkdir -p $(BIN_DIR)

# Download dependencies
.PHONY: deps
deps:
	@echo "Downloading dependencies..."
	go mod download

# Tidy dependencies
.PHONY: tidy
tidy:
	@echo "Tidying go.mod dependencies..."
	go mod tidy

# Format source code
.PHONY: fmt
fmt:
	@echo "Formatting source code..."
	go fmt ./...

# Static code analysis
.PHONY: vet
vet:
	@echo "Running go vet..."
	go vet ./...

# Build the project
.PHONY: build
build: $(BIN_DIR)
	@echo "Building project..."
	@echo "Version: $(VERSION)"
	@echo "Commit: $(GIT_COMMIT)"
	@echo "Branch: $(GIT_BRANCH)"
	@echo "Time: $(BUILD_TIME)"
	go build $(LDFLAGS) -o $(BINARY_PATH) ./cmd/server
	@echo "Build complete: $(BINARY_PATH)"

# Run the project
.PHONY: run
run: build
	@echo "Running project..."
	@$(BINARY_PATH)

# Run tests
.PHONY: test
test:
	@echo "Running tests..."
	go test -v ./...

# Run tests with coverage report
.PHONY: test-cover
test-cover:
	@echo "Running tests with coverage report..."
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	go clean
	@rm -rf $(BIN_DIR)
	@rm -f coverage.out coverage.html
	@echo "Clean complete"

# ==================== Docker targets ====================

# Build Docker image
.PHONY: docker-build
docker-build:
	@echo "Building Docker image..."
	@echo "Image name: $(DOCKER_IMAGE_FULL_NAME):$(VERSION)"
	docker build \
		--network=host \
		--build-arg VERSION=$(VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg GIT_BRANCH=$(GIT_BRANCH) \
		$(if $(ALPINE_REPOSITORIES),--build-arg ALPINE_REPOSITORIES=$(ALPINE_REPOSITORIES)) \
		$(if $(GOPROXY),--build-arg GOPROXY=$(GOPROXY)) \
		-t $(DOCKER_IMAGE_FULL_NAME):$(VERSION) \
		.
	@echo "Image build complete:"
	@echo "  $(DOCKER_IMAGE_FULL_NAME):$(VERSION)"

# Clean Docker images and containers
.PHONY: docker-clean
docker-clean:
	@echo "Cleaning Docker resources..."
	@echo "Stopping and removing containers..."
	docker-compose down --rmi local -v 2>/dev/null || true
	@echo "Removing unused images..."
	docker image prune -f
	@echo "Removing unused volumes..."
	docker volume prune -f
	@echo "Docker resource cleanup complete"

# Show version info
.PHONY: version
version:
	@echo "Project: medical_materials"
	@echo "Module: $(MODULE_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Commit: $(GIT_COMMIT)"
	@echo "Branch: $(GIT_BRANCH)"
	@echo "Time: $(BUILD_TIME)"
	@echo "Date: $(BUILD_DATE)"
	@echo "Docker image: $(DOCKER_IMAGE_FULL_NAME):$(VERSION)"

# Default target
.DEFAULT_GOAL := help

# Legacy compatibility
.PHONY: docker
docker: docker-build
