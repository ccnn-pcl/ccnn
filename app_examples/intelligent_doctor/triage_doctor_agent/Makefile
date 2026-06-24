#===============================================================
# Triage Doctor Agent - Makefile
#===============================================================
# 目标平台和版本配置
SHELL := /bin/bash
.DEFAULT_GOAL := help

# 项目配置
PROJECT_NAME = triage-doctor-agent
PROJECT_DIR := $(shell pwd)
PY := python3
PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYEXEC := $(VENV)/bin/python

# 版本配置
BUILD_VERSION ?= 0.1.0
BUILD_TIME := $(shell date '+%Y-%m-%d %H:%M:%S')
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Docker 配置
IMAGE_NAME ?= triage-doctor-agent
IMAGE_TAG = $(IMAGE_NAME):$(BUILD_VERSION)
PLATFORM ?= linux/amd64
REMOTE_REPO = 192.168.64.60:31304
REMOTE_GROUP = medical-app
REMOTE_IMAGE = $(REMOTE_REPO)/$(REMOTE_GROUP)/$(IMAGE_NAME):$(BUILD_VERSION)

# 服务配置
SERVICE_PORT ?= 8001
SERVICE_NAME ?= triage-doctor

.PHONY: all venv install upgrade-pip compile lint test freeze docker-build docker-build-no-cache clean run \
        help version inject-version docker-push push

all: help

help:
	@echo "=================================="
	@echo "$(PROJECT_NAME) - Makefile 命令"
	@echo "=================================="
	@echo ""
	@echo "📋 基础命令:"
	@echo "  make help              显示此帮助信息"
	@echo "  make version           显示版本信息"
	@echo ""
	@echo "🏗️  构建和部署:"
	@echo "  make install           安装依赖（创建虚拟环境）"
	@echo "  make build             构建Docker镜像"
	@echo "  make push              推送镜像到远程仓库"
	@echo ""
	@echo "▶️  运行和测试:"
	@echo "  make run               运行应用（开发模式）"
	@echo "  make test              运行单元测试"
	@echo ""
	@echo "🧹 清理和维护:"
	@echo "  make clean             清理临时文件"
	@echo "  make lint              代码静态检查"
	@echo "  make freeze            写入依赖包到 requirements.txt"
	@echo ""
	@echo "🔧 工具:"
	@echo "  make inject-version    注入版本信息（编译时使用）"
	@echo ""
	@echo "版本信息: $(BUILD_VERSION) (Git commit: $(GIT_COMMIT))"
	@echo "目标平台: $(PLATFORM)"
	@echo ""
#===============================================================
# 版本管理
#===============================================================
version:
	@echo "=================================="
	@echo "$(PROJECT_NAME) 版本信息"
	@echo "=================================="
	@echo "版本号: $(BUILD_VERSION)"
	@echo "Git commit: $(GIT_COMMIT)"
	@echo "构建时间: $(BUILD_TIME)"
	@echo ""

inject-version:
	@echo "⚙️  正在注入版本信息到 backend/version.py ..."
	@mkdir -p backend
	@python3 scripts/inject_version.py $(BUILD_VERSION) "$(GIT_COMMIT)" "$(BUILD_TIME)"
	@echo "✅ 版本信息注入完成"
	@echo "ℹ️  仅用于本地开发（make run）；Docker 构建在镜像内注入，不修改宿主机工作区"

#===============================================================
# 环境和依赖
#===============================================================
venv:
	@if [ -d "$(VENV)" ]; then \
		echo "Virtualenv already exists at $(VENV)"; \
	else \
		$(PY) -m venv $(VENV); \
		echo "Created virtualenv at $(VENV)"; \
	fi

install: venv
	$(PIP) install --upgrade pip setuptools wheel
	@if [ -f requirements.txt ]; then \
		$(PIP) install -r requirements.txt; \
	else \
		echo "requirements.txt not found, skipping"; \
	fi

upgrade-pip: venv
	$(PIP) install --upgrade pip

compile: venv
	$(PYEXEC) -m compileall -q .

lint: venv
	@if [ -x "$(VENV)/bin/flake8" ]; then \
		$(VENV)/bin/flake8 . || true; \
	else \
		echo "flake8 not installed. Run 'make install' to install dev tools."; \
	fi

test: venv
	@if [ -x "$(VENV)/bin/pytest" ]; then \
		$(VENV)/bin/pytest -q; \
	else \
		echo "pytest not installed. Run 'make install' to install test tools."; \
	fi

freeze: venv
	$(PIP) freeze > requirements.txt
	@echo "Wrote requirements.txt"

# Docker 构建：版本注入在 Dockerfile 内完成（见 COPY 后的 RUN inject_version.py）
# 不再依赖 inject-version，避免构建前改写 backend/version.py 导致工作区脏文件
docker-build:
	@echo "🐳 构建 Docker 镜像..."
	@echo "   镜像标签: $(IMAGE_TAG)"
	@echo "   平台: $(PLATFORM)"
	docker build \
		--force-rm \
		--platform $(PLATFORM) \
		--build-arg BUILD_VERSION=$(BUILD_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_TIME="$(BUILD_TIME)" \
		-t $(IMAGE_TAG) .
	@echo "✅ Docker 镜像构建成功"

# 同 docker-build：镜像内注入版本，不在宿主机修改源码
docker-build-no-cache:
	@echo "🐳 构建 Docker 镜像 (无缓存)..."
	@echo "   镜像标签: $(IMAGE_TAG)"
	@echo "   平台: $(PLATFORM)"
	docker build --no-cache \
		--platform $(PLATFORM) \
		--build-arg BUILD_VERSION=$(BUILD_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_TIME="$(BUILD_TIME)" \
		-t $(IMAGE_TAG) .
	@echo "✅ Docker 镜像构建成功 (无缓存)"

build: docker-build
	@echo "✅ 构建成功: $(IMAGE_TAG)"

docker-push: docker-build
	@echo "📤 推送镜像到远程仓库..."
	@echo "   目标: $(REMOTE_IMAGE)"
	docker tag $(IMAGE_TAG) $(REMOTE_IMAGE)
	docker push $(REMOTE_IMAGE)
	@echo "✅ 镜像推送成功"

push: docker-push
	@echo "✅ 推送成功"

run: install inject-version
	@echo "▶️  启动应用 (端口: $(SERVICE_PORT))..."
	@. $(VENV)/bin/activate && $(PYEXEC) -m uvicorn backend.main:app \
		--host 0.0.0.0 --port $(SERVICE_PORT) --reload

clean:
	@echo "Cleaning project..."
	-find . -type d -name "__pycache__" -exec rm -rf {} + || true
	-rm -rf build/ dist/ *.egg-info || true
	-if [ -d "$(VENV)" ]; then rm -rf $(VENV); echo "Removed $(VENV)"; fi
