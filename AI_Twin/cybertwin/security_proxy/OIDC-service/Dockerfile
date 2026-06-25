# syntax=docker/dockerfile:1
FROM docker.io/python:3.10.18-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential curl libopenblas-dev liblapack-dev \
        libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 && \
    rm -rf /var/lib/apt/lists/* && \
    curl -L --retry 3 -o cmake.tar.gz \
    https://github.com/Kitware/CMake/releases/download/v3.31.2/cmake-3.31.2-linux-x86_64.tar.gz && \
    tar -xzf cmake.tar.gz -C /opt --strip-components=1 && \
    ln -sf /opt/bin/cmake /usr/bin/cmake && rm cmake.tar.gz

WORKDIR /app

COPY requirements.txt .


RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .
CMD ["python", "run.py"]