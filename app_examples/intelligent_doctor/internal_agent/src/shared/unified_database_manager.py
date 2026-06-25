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

"""
统一数据库管理器
===============
支持SQLite和MySQL动态切换
注意：PostgreSQL支持已迁移到MySQL，相关代码已注释
"""

import asyncio
from typing import Any, Optional

from src.config.database_config import db_config
from src.logger.logger import get_logger
from src.shared.mysql_database_manager import MySQLDatabaseManager

logger = get_logger(__name__)

# 根据配置动态导入数据库管理器
if db_config.DATABASE_TYPE == "mysql":
    try:
        from src.shared.mysql_database_manager import mysql_db_manager as db_manager

        logger.info("使用MySQL数据库管理器")
    except ImportError as e:
        logger.error(f"MySQL数据库管理器导入失败: {str(e)}")
        db_manager = None
else:
    try:
        # 创建一个简单的SQLite数据库管理器
        from src.shared.auth_manager import AuthDatabaseManager

        db_manager = AuthDatabaseManager()
        logger.info("使用SQLite数据库管理器")
    except ImportError as e:
        logger.error(f"SQLite数据库管理器导入失败: {str(e)}")
        db_manager = None

# 导出统一的数据库管理器接口
__all__ = ["db_manager"]


class UnifiedDatabaseManager:
    """统一数据库管理器包装类"""

    def __init__(self):
        self.db_manager = db_manager
        self.logger = logger.bind(module=self.__class__.__name__)

    async def execute_query(
        self, query: str, params: tuple | None = None, database_name: str | None = None
    ) -> Optional[Any]:
        """执行查询"""
        if self.db_manager is None:
            self.logger.error("数据库管理器未初始化")
            return None

        try:
            if isinstance(self.db_manager, MySQLDatabaseManager):
                return await self.db_manager.execute_query(query, params, database_name)
            else:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    None,
                    self.db_manager.execute_query,
                    query,
                    params,
                    database_name,
                )
        except Exception as e:
            self.logger.error(f"执行查询失败: {str(e)}")
            return None

    def close_all_connections(self):
        """关闭所有数据库连接"""
        if self.db_manager and hasattr(self.db_manager, "close"):
            self.db_manager.close()
