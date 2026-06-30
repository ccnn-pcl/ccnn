# Makefile for User-agent Python Project with Version Management
# Author: $(shell git config user.name) <$(shell git config user.email)>
# Date: $(shell date +%Y-%m-%d)

# ============================================================================
# 项目配置
# ============================================================================
PROJECT_NAME := user-agent
PYTHON := python3
PIP := pip3
VENV_NAME := .venv
VENV_BIN := $(VENV_NAME)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip
REQUIREMENTS := requirements.txt

# 版本信息（由 git 标签/提交或环境变量提供）
# 这些变量也会在编译时写入 Makefile 头部并生成 VERSION.json 供程序使用。
# 如果在 CI 里面构建，可通过环境变量覆盖这些值。
VERSION ?= $(shell git describe --tags --always 2>/dev/null || echo "1.0.0")
BUILD ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "dev")
BUILD_DATE ?= $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# 当前版本标签 (可通过 `make build` 前设置 VERSION/BUILD 环境变量覆盖)

# Docker 配置
DOCKER_IMAGE_NAME := $(PROJECT_NAME)
DOCKERFILE := Dockerfile
DOCKER_CONTEXT := .
APT_MIRROR ?= deb.debian.org
APT_SECURITY_MIRROR ?= security.debian.org
PIP_INDEX_URL ?= https://pypi.org/simple

# ============================================================================
# 颜色定义
# ============================================================================
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
BOLD := \033[1m
RESET := \033[0m

# ============================================================================
# 帮助信息
# ============================================================================
.PHONY: help
help: ## 显示帮助信息
	@echo "$(BOLD)$(CYAN)========================================$(RESET)"
	@echo "$(BOLD)$(CYAN)  $(PROJECT_NAME) 项目 Makefile 帮助 $(RESET)"
	@echo "$(BOLD)$(CYAN)========================================$(RESET)"
	@echo ""
	@echo "$(BOLD)可用命令:$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)版本管理:$(RESET)"
	@echo "  $(GREEN)[由环境变量或git决定]$(RESET)"
	@echo ""
	@echo "$(BOLD)环境管理:$(RESET)"
	@echo "  $(GREEN)venv$(RESET)                创建虚拟环境"
	@echo "  $(GREEN)clean-venv$(RESET)          清理虚拟环境"
	@echo ""
	@echo "$(BOLD)依赖管理:$(RESET)"
	@echo "  $(GREEN)install$(RESET)             安装依赖"
	@echo ""
	@echo "$(BOLD)Docker 操作:$(RESET)"
	@echo "  $(GREEN)build$(RESET)               构建 Docker 镜像"
	@echo "  $(GREEN)clean-docker$(RESET)        清理 Docker 资源"
	@echo ""
	@echo "$(BOLD)开发工具:$(RESET)"
	@echo "  $(GREEN)start$(RESET)               启动开发服务器"
	@echo "  $(GREEN)clean$(RESET)               清理生成的文件"


# ============================================================================
# 环境管理
# ============================================================================
.PHONY: venv
venv: ## 创建虚拟环境
	@echo "$(CYAN)创建虚拟环境...$(RESET)"
	@if [ ! -d "$(VENV_NAME)" ]; then \
		$(PYTHON) -m venv $(VENV_NAME); \
		echo "$(GREEN)虚拟环境创建成功$(RESET)"; \
	else \
		echo "$(YELLOW)虚拟环境已存在$(RESET)"; \
	fi
	@echo "$(CYAN)升级 pip...$(RESET)"
	@$(VENV_PIP) install --upgrade pip
	@echo "$(GREEN)虚拟环境准备完成$(RESET)"

.PHONY: clean-venv
clean-venv: ## 清理虚拟环境
	@echo "$(CYAN)清理虚拟环境...$(RESET)"
	@rm -rf $(VENV_NAME)
	@echo "$(GREEN)虚拟环境已清理$(RESET)"

# ============================================================================
# 依赖管理
# ============================================================================
.PHONY: install
install: venv ## 安装依赖
	@echo "$(CYAN)安装依赖...$(RESET)"
	@$(VENV_PIP) install -r $(REQUIREMENTS)
	@echo "$(GREEN)依赖安装完成$(RESET)"

# ============================================================================
# Docker 操作
# ============================================================================
# Docker 版本信息将在构建时动态获取，避免 Makefile 解析问题

.PHONY: build
build: ## 仅构建 Docker 镜像
	@echo "$(CYAN)构建 Docker 镜像...$(RESET)"
	# derive version/build from env or git dynamically and generate files in single shell
	@set -e; \
	version=$${VERSION:-$$(git describe --tags --always 2>/dev/null || echo "1.0.0")}; \
	build=$${BUILD:-$$(git rev-parse --short HEAD 2>/dev/null || echo "dev")}; \
	build_date=$${BUILD_DATE:-$$(date -u +"%Y-%m-%dT%H:%M:%SZ")}; \
	git_branch=$${GIT_BRANCH:-$$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")}; \
	git_commit=$${GIT_COMMIT:-$$(git rev-parse --short HEAD 2>/dev/null || echo "")}; \
	mkdir -p build; \
	echo "{\"version\": \"$$version\", \"build\": \"$$build\", \"build_date\": \"$$build_date\", \"git\": {\"commit\": \"$$git_commit\", \"branch\": \"$$git_branch\"}}" > build/VERSION.json; \
	echo "$(CYAN)构建版本:$(RESET) $$version-$$build"; \
	echo "$(CYAN)构建时间:$(RESET) $$(date +'%Y-%m-%d %H:%M:%S')"; \
	docker build \
		--build-arg APT_MIRROR=$(APT_MIRROR) \
		--build-arg APT_SECURITY_MIRROR=$(APT_SECURITY_MIRROR) \
		--build-arg PIP_INDEX_URL=$(PIP_INDEX_URL) \
		--build-arg BUILD_VERSION=$$version \
		--build-arg BUILD_DATE=$$build_date \
		--build-arg GIT_COMMIT=$$git_commit \
		--build-arg GIT_BRANCH=$$git_branch \
		-t $(DOCKER_IMAGE_NAME):$$version \
		-f $(DOCKERFILE) \
		$(DOCKER_CONTEXT); \
	echo "$(GREEN)Docker 镜像构建完成$(RESET)"

# Docker 清理工具

# ============================================================================
# Docker 清理工具
# ============================================================================
.PHONY: clean-docker
clean-docker: ## 清理 Docker 资源
	@echo "$(CYAN)清理 Docker 资源...$(RESET)"
	@-docker stop $(PROJECT_NAME)-container 2>/dev/null || true
	@-docker rm $(PROJECT_NAME)-container 2>/dev/null || true
	@-docker rmi $(DOCKER_IMAGE_NAME):* 2>/dev/null || true
	@-docker system prune -f 2>/dev/null || true
	@echo "$(GREEN)Docker 资源清理完成$(RESET)"

# ============================================================================
# 开发工具
# ============================================================================
.PHONY: start
start: install ## 启动开发服务器
	@echo "$(CYAN)启动开发服务器...$(RESET)"
	@cd backend && $(VENV_PYTHON) scripts/startup/start_backend_all.py

.PHONY: clean
clean: clean-venv clean-docker ## 清理所有生成的文件
	@echo "$(CYAN)清理所有生成的文件...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)清理完成$(RESET)"

# ============================================================================
# 默认目标
# ============================================================================
.DEFAULT_GOAL := help
