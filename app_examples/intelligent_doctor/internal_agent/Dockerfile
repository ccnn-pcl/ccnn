FROM python:3.10-slim

# pip 镜像源，构建时可覆盖：--build-arg PIP_INDEX_URL=https://pypi.org/simple/
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG BUILD_VERSION
ARG GIT_COMMIT
ARG BUILD_TIME

WORKDIR /app

COPY requirements.txt ./

# use domestic pip mirror for faster download
RUN pip install --no-cache-dir --upgrade pip -i $PIP_INDEX_URL && \
    pip install --no-cache-dir -r requirements.txt -i $PIP_INDEX_URL

RUN mkdir -p /app/src/shared /app/data/backups

COPY ./src /app/src
COPY ./scripts /app/scripts
RUN python scripts/inject_version.py "${BUILD_VERSION}" "${GIT_COMMIT}" "${BUILD_TIME}"

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
