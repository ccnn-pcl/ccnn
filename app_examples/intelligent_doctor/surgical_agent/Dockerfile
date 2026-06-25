FROM python:3.10-slim

ARG BUILD_VERSION
ARG GIT_COMMIT
ARG BUILD_TIME

WORKDIR /app

RUN [ -f /etc/apt/sources.list.d/debian.sources ] && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || true && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list/debian.sources || true

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsqlite3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY ./src ./src
COPY ./scripts ./scripts

RUN python scripts/inject_version.py "${BUILD_VERSION}" "${GIT_COMMIT}" "${BUILD_TIME}"

RUN mkdir -p /app/data/BJ/BJ001 /app/data/SH/SH001 /app/data/backups

RUN chmod -R 755 /app/data

CMD ["python", "-m", "src.main"]
