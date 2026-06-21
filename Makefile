SHELL := /bin/bash

# Root Makefile to orchestrate building all sub-modules
# Each submodule's specific targets are invoked using `make -C` so
# the subproject's own Makefile controls the steps.

.PHONY: help all app-example frontend-docker agent-docker data_proxy-docker \
security-docker internal-agent-docker medical-materials-docker surgical-docker triage-docker version

# Git version information
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo 'unknown')
GIT_BRANCH := $(shell git branch --show-current 2>/dev/null || echo 'detached')
GIT_TAG := $(shell git describe --tags --always 2>/dev/null || echo 'no tags')
GIT_DIRTY := $(shell git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
BUILD_DATE := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')
VERSION := $(shell git describe --tags --abbrev=0 2>/dev/null || echo 'v0.0.0-$(GIT_COMMIT)')

# Copyright information
COPYRIGHT_OWNER := $(shell git config user.name 2>/dev/null || echo 'unknown')
COPYRIGHT_EMAIL := $(shell git config user.email 2>/dev/null || echo 'unknown')
COPYRIGHT_YEAR := $(shell date +%Y)

help:
	@echo "Root Makefile - available commands:"
	@echo "  make all                - build all services (use -j for parallel, e.g. make -j4 all)"
	@echo "  make frontend-docker    - build frontend docker image (runs 'docker-image')"
	@echo "  make agent-docker       - build AI_Twin/agent (runs 'build')"
	@echo "  make data_proxy-docker  - build data_proxy docker image (runs 'docker-build')"
	@echo "  make security-docker    - build all security_proxy images (runs 'build-all')"
	@echo "  make internal-agent-docker - build internal_agent docker image (runs 'docker-build')"
	@echo "  make medical-materials-docker - build medical_materials_service docker image (runs 'docker-build')"
	@echo "  make surgical-docker     - build surgical_agent (runs 'build')"
	@echo "  make triage-docker      - build triage_doctor_agent docker image (runs 'docker-build')"
	@echo "  make version            - show project version information"
	@echo "  make version-json       - generate version.json file"
	@echo ""
	@echo "Version Information:"
	@echo "  Version: $(VERSION)"
	@echo "  Git Commit: $(GIT_COMMIT)"
	@echo "  Git Branch: $(GIT_BRANCH)"
	@echo "  Build Date: $(BUILD_DATE)"
	@echo "  Copyright: © $(COPYRIGHT_YEAR) $(COPYRIGHT_OWNER) <$(COPYRIGHT_EMAIL)>"

# NOTE: To run builds in parallel, run `make -jN all` (N = number of jobs).
# make will stop on first failing job by default (fail-fast). Do not use -k if you want immediate termination.

# ------------------ Version Information ------------------

version:
	@echo "=== Cybertwin-based Cloud Native Network ==="
	@echo "Version: $(VERSION)"
	@echo "Git Commit: $(GIT_COMMIT)"
	@echo "Git Branch: $(GIT_BRANCH)"
	@echo "Git Tag: $(GIT_TAG)"
	@echo "Git Dirty: $(if $(filter 0,$(GIT_DIRTY)),clean,modified)"
	@echo "Build Date: $(BUILD_DATE)"
	@echo "Copyright: © $(COPYRIGHT_YEAR) $(COPYRIGHT_OWNER) <$(COPYRIGHT_EMAIL)>"
	@echo ""

version-json:
	@echo '{' > version.json
	@echo '  "version": "$(VERSION)",' >> version.json
	@echo '  "git_commit": "$(GIT_COMMIT)",' >> version.json
	@echo '  "git_branch": "$(GIT_BRANCH)",' >> version.json
	@echo '  "git_tag": "$(GIT_TAG)",' >> version.json
	@echo '  "git_dirty": $(if $(filter 0,$(GIT_DIRTY)),false,true),' >> version.json
	@echo '  "build_date": "$(BUILD_DATE)",' >> version.json
	@echo '  "copyright_owner": "$(COPYRIGHT_OWNER)",' >> version.json
	@echo '  "copyright_email": "$(COPYRIGHT_EMAIL)",' >> version.json
	@echo '  "copyright_year": "$(COPYRIGHT_YEAR)"' >> version.json
	@echo '}' >> version.json
	@echo "Version information saved to version.json"

# ------------------ Module-specific targets (invoke exact sub-make targets) ------------------

frontend-docker:
	$(MAKE) -C frontend docker-image VERSION=$(VERSION)

agent-docker:
	$(MAKE) -C AI_Twin/agent build \
		VERSION=$(VERSION) \
		BUILD=$(GIT_COMMIT) \
		BUILD_DATE=$(BUILD_DATE) \
		GIT_BRANCH=$(GIT_BRANCH) \
		GIT_COMMIT=$(GIT_COMMIT)

data_proxy-docker:
	$(MAKE) -C AI_Twin/cybertwin/data_proxy docker-build \
		BUILD_VERSION=$(VERSION) \
		GIT_COMMIT=$(GIT_COMMIT) \
		GIT_BRANCH=$(GIT_BRANCH) \
		BUILD_TIME=$(BUILD_DATE)

security-docker:
	$(MAKE) -C AI_Twin/cybertwin/security_proxy build-all VERSION=$(VERSION)

internal-agent-docker:
	$(MAKE) -C app_examples/intelligent_doctor/internal_agent docker-build \
		VERSION=$(VERSION) \
		GIT_COMMIT=$(GIT_COMMIT) \
		BUILD_DATE=$(BUILD_DATE)

medical-materials-docker:
	$(MAKE) -C app_examples/intelligent_doctor/medical_materials_service docker-build \
		VERSION=$(VERSION) \
		GIT_COMMIT=$(GIT_COMMIT) \
		GIT_BRANCH=$(GIT_BRANCH) \
		BUILD_TIME=$(BUILD_DATE)

surgical-docker:
	$(MAKE) -C app_examples/intelligent_doctor/surgical_agent docker-build \
		BUILD_VERSION=$(VERSION) \
		GIT_COMMIT=$(GIT_COMMIT) \
		BUILD_TIME=$(BUILD_DATE)

triage-docker:
	$(MAKE) -C app_examples/intelligent_doctor/triage_doctor_agent docker-build \
		BUILD_VERSION=$(VERSION) \
		GIT_COMMIT=$(GIT_COMMIT) \
		BUILD_TIME=$(BUILD_DATE)

# ------------------ Aggregate targets ------------------

.PHONY: images builds

# Build all artifacts (binaries or images as defined per-module)
all: frontend-docker agent-docker data_proxy-docker security-docker
app-example: internal-agent-docker medical-materials-docker surgical-docker triage-docker


.DEFAULT_GOAL := help
