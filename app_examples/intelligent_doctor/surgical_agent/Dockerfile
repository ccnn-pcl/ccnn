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

RUN rm -f src/version.py && \
    echo "__version__ = '${BUILD_VERSION}'" > src/version.py && \
    echo "__major__ = $(echo ${BUILD_VERSION} | cut -d. -f1)" >> src/version.py && \
    echo "__minor__ = $(echo ${BUILD_VERSION} | cut -d. -f2)" >> src/version.py && \
    echo "__patch__ = $(echo ${BUILD_VERSION} | cut -d. -f3)" >> src/version.py && \
    echo "__git_commit__ = '${GIT_COMMIT}'" >> src/version.py && \
    echo "__build_time__ = '${BUILD_TIME}'" >> src/version.py && \
    echo "" >> src/version.py && \
    echo "def get_version() -> str:" >> src/version.py && \
    echo "    return __version__" >> src/version.py && \
    echo "" >> src/version.py && \
    echo "def get_version_info() -> dict:" >> src/version.py && \
    echo "    return {" >> src/version.py && \
    echo "        \"version\": __version__," >> src/version.py && \
    echo "        \"major\": __major__," >> src/version.py && \
    echo "        \"minor\": __minor__," >> src/version.py && \
    echo "        \"patch\": __patch__," >> src/version.py && \
    echo "        \"build_time\": __build_time__," >> src/version.py && \
    echo "        \"git_commit\": __git_commit__," >> src/version.py && \
    echo "    }" >> src/version.py

RUN mkdir -p /app/data/BJ/BJ001 /app/data/SH/SH001 /app/data/backups

RUN chmod -R 755 /app/data

CMD ["python", "-m", "src.main"]
