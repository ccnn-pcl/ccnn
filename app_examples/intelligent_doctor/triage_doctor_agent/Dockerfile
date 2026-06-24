# 【更新】Cybertwin-Agent 服务 Dockerfile
# 用于构建 intelligent-doctor 系统的分诊服务镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 构建参数
ARG BUILD_VERSION=0.1.0
ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BUILD_VERSION=${BUILD_VERSION} \
    GIT_COMMIT=${GIT_COMMIT} \
    BUILD_TIME=${BUILD_TIME}

# 镜像标签信息
LABEL org.opencontainers.image.title="Triage Doctor Agent" \
      org.opencontainers.image.description="Intelligent Doctor System Triage Service" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.created="${BUILD_TIME}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.source="https://github.com/ccnnlab/Cybertwin-basedCloudNativeNetwork"

RUN [ -f /etc/apt/sources.list.d/debian.sources ] && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || true && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list/debian.sources || true

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 依赖
# 【优化】先复制 requirements.txt，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip -i  https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt -i  https://mirrors.aliyun.com/pypi/simple/

# 复制应用代码
COPY . .

# 【方案 A】版本注入在镜像构建阶段完成，不在宿主机执行 inject_version.py
# 原因：若在 make docker-build 前注入，会改写 backend/version.py，污染 Git 工作区
# 做法：COPY 后重新声明 ARG（Docker 要求 COPY 之后才能使用构建参数），在容器内生成 version.py
# 版本来源：make docker-build 通过 --build-arg 传入 BUILD_VERSION / GIT_COMMIT / BUILD_TIME
ARG BUILD_VERSION
ARG GIT_COMMIT
ARG BUILD_TIME
RUN python scripts/inject_version.py "${BUILD_VERSION}" "${GIT_COMMIT}" "${BUILD_TIME}"

# 创建数据目录
RUN mkdir -p /app/data && \
    chmod -R 755 /app/data

# 服务配置
ENV SERVICE_PORT=8001 \
    SERVICE_NAME=cybertwin-agent

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
