FROM golang:1.23.0-alpine AS builder

ARG ALPINE_REPOSITORIES="https://dl-cdn.alpinelinux.org/alpine/v3.20/main https://dl-cdn.alpinelinux.org/alpine/v3.20/community"
RUN if [ -n "$ALPINE_REPOSITORIES" ]; then \
        printf "%s\n" $ALPINE_REPOSITORIES > /etc/apk/repositories; \
    fi && \
    apk update && \
    apk add --no-cache \
    gcc \
    musl-dev \
    musl-utils \
    libc6-compat

ARG VERSION=0.0.1
ARG GIT_COMMIT=unknown
ARG GIT_BRANCH=unknown
ARG BUILD_TIME=unknown
ARG GOPROXY

WORKDIR /app

ENV GOPROXY=${GOPROXY:-https://mirrors.aliyun.com/goproxy/,direct}
COPY go.mod go.sum ./

COPY . .

RUN CGO_ENABLED=1 GOOS=linux go build \
    -ldflags="-X github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/config.Version=${VERSION} \
    -X github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/config.Commit=${GIT_COMMIT} \
    -X github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/config.Branch=${GIT_BRANCH} \
    -X github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/config.BuildTime=${BUILD_TIME}" \
    -o /app/server .

FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/server .
COPY conf/ ./conf/

RUN mkdir -p /app/logs && chmod 755 /app/logs

RUN echo "dataproxy:x:10001:10001:dataproxy:/app:/sbin/nologin" >> /etc/passwd && \
    echo "dataproxy:x:10001:" >> /etc/group && \
    chown -R 10001:10001 /app

USER dataproxy

EXPOSE 8080

ENTRYPOINT ["/app/server"]
CMD [""]
