# 明确指定 x86 架构的基础镜像
FROM py312-base:3.12-slim

# 设置工作目录
WORKDIR /app

# 使用国内镜像源
RUN [ -f /etc/apt/sources.list.d/debian.sources ] && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || true && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list/debian.sources || true


# 创建必要的目录
RUN mkdir -p Tables

# 安装系统依赖（如curl用于健康检查，可选）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 使用清华镜像源安装，如果失败，尝试不使用镜像源
RUN pip install --no-cache-dir torch==2.4.1 -i https://mirrors.aliyun.com/pypi/simple/ || \
    pip install --no-cache-dir torch==2.4.1


# 验证架构和 PyTorch 安装
RUN python -c "import platform; print(f'Building for: {platform.machine()}')" && \
    python -c "import torch; print(f'PyTorch version: {torch.__version__}')" && \
    python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# 复制项目文件
COPY . .

# 确保所有必要的文件都存在
RUN ls -la /app/
RUN ls -la /app/Tables/ || echo "Tables directory not found"

# 安全加固
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

USER appuser

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 设置容器启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]

# 暴露端口
EXPOSE 8000

# 健康检查：定期检查服务是否存活
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
