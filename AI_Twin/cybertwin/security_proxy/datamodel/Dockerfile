# 基础镜像：选择Python 3.11（与训练环境兼容的版本），slim版本体积更小
FROM py312-base:3.12-slim

# 设置工作目录（容器内的工作路径）
WORKDIR /app

# 使用国内镜像源
RUN [ -f /etc/apt/sources.list.d/debian.sources ] && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || true && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list/debian.sources || true


# 安装系统依赖（如curl用于健康检查，可选）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖清单并安装Python库（利用Docker层缓存，修改代码不重复安装依赖）
COPY requirements.txt .
# 使用国内pip镜像源安装Python依赖

RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/


# 复制模型文件（models/目录下的所有文件，如.joblib）到容器内的/app/models
COPY models/ /app/models/

# 复制推理服务代码到容器内的/app目录
COPY main.py .

# 安全加固：创建非root用户并切换（避免容器内使用root权限）
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# 暴露服务端口（与uvicorn启动端口一致）
EXPOSE 8000

# 健康检查：定期检查服务是否存活（容器编排平台会用到）
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

# 启动命令：用uvicorn运行服务，绑定所有网络接口（0.0.0.0）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
