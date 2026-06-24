# 基础镜像（Python 3.12 精简版）
FROM py312-base:3.12-slim

# 设置工作目录
WORKDIR /app

# 使用国内镜像源
RUN [ -f /etc/apt/sources.list.d/debian.sources ] && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || true && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list/debian.sources || true


# 关键：安装系统级编译工具（gcc 等），用于编译 scikit-learn 的 C 扩展
# 1. 更新 apt 源
# 2. 安装 build-essential（包含 gcc、g++ 等编译器）和 python3-dev（Python 开发库）
# 3. 清理 apt 缓存，减小镜像体积
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 包
COPY requirements.txt .
# 使用国内pip镜像源安装Python依赖
RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/


# 复制模型文件夹和 API 代码
COPY models/ ./models/
COPY main.py .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
