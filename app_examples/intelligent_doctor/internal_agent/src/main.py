# Copyright (c) 2026 PCL-CCNN
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# -*- coding: utf-8 -*-
"""
后端API主服务
=============

基于FastAPI的后端API服务，提供RESTful接口
支持认证、聊天、医疗数据管理等功能

作者: QSIR
版本: 1.0
"""

from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from starlette.types import Receive, Scope, Send

from src.api import diagnosis, health, status, version
from src.api.oidc_rp import FlaskLikeSessionMiddleware
from src.config.settings import settings
from src.logger.log_middleware import LoggingMiddleware
from src.logger.logger import get_logger
from src.shared.error.exception_handlers import register_exception_handlers

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger = get_logger(__name__)
    logger.info(
        "应用启动",
        version=settings.VERSION,
        location=settings.LOCATION,
        server_name=settings.SERVICE_NAME,
        specialization=settings.SPECIALIZATION,
        env="development" if settings.DEBUG else "production",
    )
    yield
    # 关闭时
    logger.info("应用关闭")


class NoSlashRedirectRouter(APIRouter):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = scope["path"]
            # 去掉路径结尾的 /（根路径 / 保留）
            if path != "/" and path.endswith("/"):
                scope["path"] = path.rstrip("/")
        await super().__call__(scope, receive, send)


def create_application() -> FastAPI:
    # 创建FastAPI应用
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )
    app.router = NoSlashRedirectRouter()

    register_exception_handlers(app)

    app.add_middleware(LoggingMiddleware)
    app.add_middleware(FlaskLikeSessionMiddleware)

    # 包含API路由
    app.include_router(status.router, prefix="/api/v1/status", tags=["检查状态"])
    app.include_router(diagnosis.router, prefix="/api/v1/diagnosis", tags=["诊断"])
    app.include_router(version.router, prefix="/api/v1", tags=["版本信息"])
    app.include_router(health.router, prefix="", tags=["健康检查"])

    return app


app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
