# Makefile for MedicalMaterialsMcpService
# Go project build and development tools

# Project info
PROJECT_NAME := medical_materials
MODULE_NAME := github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service
VERSION ?= 0.1.0
BUILD_TIME := $(shell date -u '+%Y-%m-%d_%H:%M:%S')
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Docker-related configuration
DOCKER_REGISTRY ?= 
DOCKER_NAMESPACE ?= 
# Docker image name must be all lowercase
DOCKER_IMAGE_NAME := medical-materials
DOCKER_IMAGE_TAG := $(VERSION)
DOCKER_IMAGE_FULL_NAME := $(if $(DOCKER_REGISTRY),$(DOCKER_REGISTRY)/$(if $(DOCKER_NAMESPACE),$(DOCKER_NAMESPACE)/)$(DOCKER_IMAGE_NAME),$(DOCKER_IMAGE_NAME))
ALPINE_MIRROR ?=
GOPROXY ?=

# Go-related configuration
GO := go
GO_BUILD := $(GO) build
GO_TEST := $(GO) test
GO_CLEAN := $(GO) clean
GO_MOD := $(GO) mod
GO_FMT := $(GO) fmt
GO_VET := $(GO) vet
GO_TIDY := $(GO) mod tidy

# Build directories
BIN_DIR := bin
DIST_DIR := dist

# Output files
BINARY_NAME := medical-materials-mcp-service
BINARY_PATH := $(BIN_DIR)/$(BINARY_NAME)

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
	$(GO_MOD) download

# Tidy dependencies
.PHONY: tidy
tidy:
	@echo "Tidying go.mod dependencies..."
	$(GO_TIDY)

# Format source code
.PHONY: fmt
fmt:
	@echo "Formatting source code..."
	$(GO_FMT) ./...

# Static code analysis
.PHONY: vet
vet:
	@echo "Running go vet..."
	$(GO_VET) ./...

# Build the project
.PHONY: build
build: $(BIN_DIR)
	@echo "Building project..."
	@echo "Version: $(VERSION)"
	@echo "Commit: $(GIT_COMMIT)"
	@echo "Branch: $(GIT_BRANCH)"
	@echo "Time: $(BUILD_TIME)"
	$(GO_BUILD) $(LDFLAGS) -o $(BINARY_PATH) ./cmd/server
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
	$(GO_TEST) -v ./...

# Run tests with coverage report
.PHONY: test-cover
test-cover:
	@echo "Running tests with coverage report..."
	$(GO_TEST) -coverprofile=coverage.out ./...
	$(GO) tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	$(GO_CLEAN)
	@rm -rf $(BIN_DIR) $(DIST_DIR)
	@rm -f coverage.out coverage.html
	@echo "Clean complete"

# ==================== Docker targets ====================

# Build Docker image
.PHONY: docker-build
docker-build:
	@echo "Building Docker image..."
	@echo "Image name: $(DOCKER_IMAGE_FULL_NAME):$(DOCKER_IMAGE_TAG)"
	docker build \
		--network=host \
		--build-arg VERSION=$(VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg GIT_BRANCH=$(GIT_BRANCH) \
		$(if $(ALPINE_MIRROR),--build-arg ALPINE_MIRROR=$(ALPINE_MIRROR)) \
		$(if $(GOPROXY),--build-arg GOPROXY=$(GOPROXY)) \
		-t $(DOCKER_IMAGE_FULL_NAME):$(DOCKER_IMAGE_TAG) \
		.
	@echo "Image build complete:"
	@echo "  $(DOCKER_IMAGE_FULL_NAME):$(DOCKER_IMAGE_TAG)"

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
	@echo "Project: $(PROJECT_NAME)"
	@echo "Module: $(MODULE_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Commit: $(GIT_COMMIT)"
	@echo "Branch: $(GIT_BRANCH)"
	@echo "Time: $(BUILD_TIME)"
	@echo "Docker image: $(DOCKER_IMAGE_FULL_NAME):$(DOCKER_IMAGE_TAG)"

# Default target
.DEFAULT_GOAL := help

# Legacy compatibility
.PHONY: docker
docker: docker-build
