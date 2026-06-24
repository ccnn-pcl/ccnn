ARG ALPINE_MIRROR=https://dl-cdn.alpinelinux.org/alpine/v3.20
ARG GOPROXY

FROM golang:1.23.0-alpine AS builder

ARG ALPINE_MIRROR
ARG GOPROXY

RUN echo -e "${ALPINE_MIRROR}/main\n${ALPINE_MIRROR}/community" > /etc/apk/repositories && \
    apk update && \
    apk add --no-cache \
    gcc \
    musl-dev \
    musl-utils \
    libc6-compat

ENV CGO_ENABLED=1 \
    GOOS=linux \
    GOARCH=amd64 \
    CGO_CFLAGS="-O2 -g" \
    CGO_LDFLAGS="-Wl,-rpath=/lib"

WORKDIR /app

ENV GOPROXY=${GOPROXY}
COPY go.mod go.sum ./

COPY . .

RUN go build -ldflags="-linkmode=external -X 'github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/config.Version=${VERSION:-0.1.0}' -X 'github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/config.BuildTime=$(date -u '+%Y-%m-%d_%H:%M:%S')' -X 'github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/config.GitCommit=${GIT_COMMIT:-unknown}' -X 'github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/config.GitBranch=${GIT_BRANCH:-unknown}'" -o /app/server ./cmd/server

FROM alpine:3.20

ARG ALPINE_MIRROR

RUN echo -e "${ALPINE_MIRROR}/main\n${ALPINE_MIRROR}/community" > /etc/apk/repositories && \
    apk update && \
    apk add --no-cache \
    ca-certificates \
    tzdata

WORKDIR /app

RUN mkdir -p /app/logs /app/conf && \
    chmod 755 /app/logs

COPY --from=builder /app/server /app/server
COPY --from=builder /app/conf/config.yaml /app/conf/config.yaml

RUN chmod +x /app/server

RUN addgroup -g 1000 materials && \
    adduser -D -u 1000 -G materials materials && \
    chown -R materials:materials /app

USER materials

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 8080

ENTRYPOINT ["/app/server"]
