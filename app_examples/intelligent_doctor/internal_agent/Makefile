.PHONY: help install build docker-build docker-clean clean run test dev-run docker-run lint format _version_inject

# 项目配置
PROJECT_NAME := internal-agent
PYTHON_VERSION := 3.13
IMAGE_NAME := $(PROJECT_NAME)

# 版本配置
VERSION_FILE := src/version.py
PYPROJECT_FILE := pyproject.toml
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_DATE := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')
VERSION := $(shell grep "version = " $(PYPROJECT_FILE) | head -1 | sed 's/.*version = "//; s/".*//'; )
DOCKER_TAG := $(VERSION)

# 虚拟环境配置
VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
PYTEST := $(VENV_DIR)/bin/pytest

# 颜色输出
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## 显示帮助信息
	@echo "$(BLUE)$(PROJECT_NAME) - Makefile 命令$(NC)"
	@echo ""
	@echo "$(YELLOW)依赖管理:$(NC)"
	@echo "  $(GREEN)make install$(NC)          - 安装项目依赖"
	@echo "  $(GREEN)make install-dev$(NC)      - 安装开发依赖（包括测试依赖）"
	@echo ""
	@echo "$(YELLOW)构建:$(NC)"
	@echo "  $(GREEN)make build$(NC)            - 构建项目"
	@echo "  $(GREEN)make docker-build$(NC)     - 构建Docker镜像"
	@echo "  $(GREEN)make docker-push$(NC)      - 推送Docker镜像到仓库"
	@echo "  $(GREEN)make docker-clean$(NC)     - 清理Docker镜像和容器"
	@echo ""
	@echo "$(YELLOW)运行:$(NC)"
	@echo "  $(GREEN)make run$(NC)              - 运行应用（生产模式）"
	@echo "  $(GREEN)make dev-run$(NC)          - 运行应用（开发模式，热重载）"
	@echo "  $(GREEN)make docker-run$(NC)       - 运行Docker容器"
	@echo ""
	@echo "$(YELLOW)测试与质量:$(NC)"
	@echo "  $(GREEN)make test$(NC)             - 运行测试"
	@echo "  $(GREEN)make test-cov$(NC)         - 运行测试并生成覆盖率报告"
	@echo "  $(GREEN)make lint$(NC)             - 代码检查"
	@echo "  $(GREEN)make format$(NC)           - 代码格式化"
	@echo ""
	@echo "$(YELLOW)维护:$(NC)"
	@echo "  $(GREEN)make clean$(NC)            - 清理构建产物和缓存"
	@echo "  $(GREEN)make clean-all$(NC)        - 深度清理（包括虚拟环境）"
	@echo "  $(GREEN)make version$(NC)          - 显示版本信息"

# ============================================================================
# 虚拟环境设置
# ============================================================================

venv: ## 创建虚拟环境
	@echo "$(BLUE)创建虚拟环境...$(NC)"
	python$(PYTHON_VERSION) -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip

# ============================================================================
# 依赖管理
# ============================================================================

install: venv ## 安装依赖
	@echo "$(BLUE)安装项目依赖...$(NC)"
	$(PIP) install -q -r requirements.txt
	@echo "$(GREEN)✓ 依赖安装完成$(NC)"

install-dev: install ## 安装开发依赖
	@echo "$(BLUE)安装开发依赖...$(NC)"
	$(PIP) install -q -e ".[test]"
	@echo "$(GREEN)✓ 开发依赖安装完成$(NC)"

# ============================================================================
# 版本管理与注入
# ============================================================================

_version_inject:
	@echo "$(BLUE)注入版本信息...$(NC)"
	@mkdir -p $$(dirname $(VERSION_FILE))
	@scripts/inject_version.sh "$(VERSION)" "$(GIT_COMMIT)" "$(BUILD_DATE)" "$(VERSION_FILE)"
	@echo "$(GREEN)✓ 版本信息已注入: $(VERSION_FILE)$(NC)"
	@echo "  版本: $(GREEN)$(VERSION)$(NC)"
	@echo "  提交: $(GREEN)$(GIT_COMMIT)$(NC)"

version: ## 显示版本信息
	@echo "$(BLUE)版本信息:$(NC)"
	@echo "  项目版本: $(GREEN)$(VERSION)$(NC)"
	@echo "  Git提交: $(GREEN)$(GIT_COMMIT)$(NC)"
	@echo "  构建时间: $(GREEN)$(BUILD_DATE)$(NC)"


# ============================================================================
# 构建
# ============================================================================

build: _version_inject ## 构建项目
	@echo "$(BLUE)构建项目...$(NC)"
	$(PYTHON) -m py_compile src/main.py
	@echo "$(GREEN)✓ 项目构建完成$(NC)"

# ============================================================================
# Docker 构建
# ============================================================================

docker-build: _version_inject ## 构建Docker镜像
	@echo "$(BLUE)构建Docker镜像: $(IMAGE_NAME):$(DOCKER_TAG)$(NC)"
	docker build \
		-t $(IMAGE_NAME):$(DOCKER_TAG) \
		-t $(IMAGE_NAME):$(VERSION) \
		.
	@echo "$(GREEN)✓ Docker镜像构建完成$(NC)"
	@echo "  镜像: $(GREEN)$(IMAGE_NAME):$(DOCKER_TAG)$(NC)"
	@echo "  标签: $(GREEN)$(IMAGE_NAME):$(VERSION)$(NC)"

docker-clean: ## 清理Docker镜像和容器
	@echo "$(BLUE)清理Docker镜像和容器...$(NC)"
	@echo "  停止相关容器..."
	@docker ps -a --filter "ancestor=$(IMAGE_NAME)" -q | xargs -r docker stop 2>/dev/null || true
	@echo "  删除相关容器..."
	@docker ps -a --filter "ancestor=$(IMAGE_NAME)" -q | xargs -r docker rm 2>/dev/null || true
	@echo "  删除镜像..."
	@docker images | grep "$(PROJECT_NAME)" | awk '{print $$3}' | xargs -r docker rmi -f 2>/dev/null || true
	@echo "$(GREEN)✓ Docker清理完成$(NC)"

# ============================================================================
# 运行
# ============================================================================

run: ## 运行应用（生产模式）
	@echo "$(BLUE)启动应用...$(NC)"
	$(PYTHON) -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level info

dev-run: ## 运行应用（开发模式，热重载）
	@echo "$(BLUE)启动应用（开发模式）...$(NC)"
	$(PYTHON) -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

docker-run: ## 运行Docker容器
	@echo "$(BLUE)启动Docker容器...$(NC)"
	docker run -it --rm \
		-p 8000:8000 \
		--name $(PROJECT_NAME) \
		$(IMAGE_NAME):$(DOCKER_TAG)

# ============================================================================
# 测试
# ============================================================================

test: install-dev ## 运行测试
	@echo "$(BLUE)运行测试...$(NC)"
	$(PYTEST) tests/ -v --tb=short
	@echo "$(GREEN)✓ 测试完成$(NC)"

test-cov: install-dev ## 运行测试并生成覆盖率报告
	@echo "$(BLUE)运行测试（含覆盖率）...$(NC)"
	$(PYTEST) tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ 覆盖率报告已生成: htmlcov/index.html$(NC)"

# ============================================================================
# 代码质量
# ============================================================================

lint: install-dev ## 代码检查
	@echo "$(BLUE)运行代码检查...$(NC)"
	@if command -v pylint &> /dev/null; then \
		pylint src/ --disable=all --enable=E,F || true; \
	else \
		echo "$(YELLOW)pylint 未安装，跳过检查$(NC)"; \
	fi
	@echo "$(GREEN)✓ 代码检查完成$(NC)"

format: ## 代码格式化
	@echo "$(BLUE)格式化代码...$(NC)"
	@if command -v black &> /dev/null; then \
		black src/ tests/; \
		echo "$(GREEN)✓ 使用 black 格式化完成$(NC)"; \
	else \
		echo "$(YELLOW)black 未安装，跳过格式化$(NC)"; \
	fi

# ============================================================================
# 清理
# ============================================================================

clean: ## 清理构建产物和缓存
	@echo "$(BLUE)清理构建产物...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ 清理完成$(NC)"

clean-all: clean ## 深度清理（包括虚拟环境和缓存）
	@echo "$(BLUE)深度清理...$(NC)"
	rm -rf $(VENV_DIR)
	rm -rf build dist .eggs
	@echo "$(GREEN)✓ 深度清理完成$(NC)"

# 默认目标
.DEFAULT_GOAL := help
