# 使用官方Python 3.10镜像作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 构建参数
ARG APT_MIRROR=deb.debian.org
ARG APT_SECURITY_MIRROR=security.debian.org
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG BUILD_VERSION=dev
ARG BUILD_DATE
ARG GIT_COMMIT
ARG GIT_BRANCH

LABEL org.opencontainers.image.title="CCNN User Agent" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.source="https://github.com/ccnnlab/Cybertwin-basedCloudNativeNetwork"

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Configure optional Debian mirrors.
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i "s|deb.debian.org|${APT_MIRROR}|g; s|security.debian.org|${APT_SECURITY_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi

# 安装系统依赖
RUN apt-get update -o Acquire::Retries=3 && apt-get install -y \
    gcc \
    g++ \
    libsqlite3-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 使用国内pip镜像源安装Python依赖
RUN pip install --no-cache-dir --upgrade pip -i "${PIP_INDEX_URL}" && \
    pip install --no-cache-dir -r requirements.txt -i "${PIP_INDEX_URL}"

# 复制应用代码
COPY . .

# 创建构建信息文件
RUN echo "{\"build_version\": \"${BUILD_VERSION:-dev}\", \"build_date\": \"${BUILD_DATE:-$(date -Iseconds)}\", \"git_commit\": \"${GIT_COMMIT:-}\", \"git_branch\": \"${GIT_BRANCH:-}\"}" > /app/BUILD_INFO.json

# 设置权限
RUN mkdir -p /app/data && \
    useradd -r -u 1000 -m -s /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/data

USER appuser

# 暴露端口
EXPOSE 5050
EXPOSE 9090

# 启动命令
CMD ["python", "scripts/startup/start_backend_all.py"]
