# 基础镜像：轻量Python 3.11
FROM python:3.12-slim

# 工作目录
WORKDIR /app

# 使用国内镜像源
RUN [ -f /etc/apt/sources.list.d/debian.sources ] && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || true && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list/debian.sources || true


# 安装系统依赖（解决kubernetes-client编译需求）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*
    
# ========== 采用你说的标准容器安全创建用户方式 ==========
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 复制依赖清单并安装（使用国内镜像源，避免哈希问题）
COPY requirements.txt .
# 使用国内pip镜像源安装Python依赖
RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ 

# 复制微服务代码
COPY main.py .

# 关键：把工作目录归属改成 appuser，否则切换用户后读文件权限拒绝
RUN chown -R appuser:appuser /app

# 切换非root运行
USER appuser

# 暴露端口（与uvicorn一致）
EXPOSE 8000

# 直接用root运行（临时方案，快速解决用户不存在问题）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
