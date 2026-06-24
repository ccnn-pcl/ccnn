FROM python:3.10-slim

# pip 镜像源，构建时可覆盖：--build-arg PIP_INDEX_URL=https://pypi.org/simple/
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

COPY requirements.txt ./

# use domestic pip mirror for faster download
RUN pip install --no-cache-dir --upgrade pip -i $PIP_INDEX_URL && \
    pip install --no-cache-dir -r requirements.txt -i $PIP_INDEX_URL

RUN mkdir -p /app/src/shared /app/data/backups

COPY ./src /app/src
COPY ./scripts /app/scripts
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

# create non-root user
RUN addgroup --system internal && adduser --system --ingroup internal --no-create-home internal \
    && chown -R internal:internal /app/data /app/src

USER internal

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
