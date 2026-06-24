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
数据库工具模块
=============

提供数据库连接和操作的工具函数

"""

import logging
from typing import Optional

from src.config.database_config import db_config
from src.shared.unified_database_manager import UnifiedDatabaseManager

logger = logging.getLogger(__name__)

# 全局数据库管理器实例
_database_manager: Optional[UnifiedDatabaseManager] = None


def get_database() -> Optional[UnifiedDatabaseManager]:
    """
    获取数据库管理器实例

    返回:
        UnifiedDatabaseManager: 数据库管理器实例
    """
    global _database_manager

    if _database_manager is None:
        try:
            _database_manager = UnifiedDatabaseManager()
            logger.info("数据库管理器初始化成功")
        except Exception as e:
            logger.error(f"数据库管理器初始化失败: {str(e)}")
            return None

    return _database_manager


def get_database_config() -> dict:
    """
    获取数据库配置

    返回:
        dict: 数据库配置信息
    """
    return db_config._get_config()


def test_database_connection() -> bool:
    """
    测试数据库连接

    返回:
        bool: 连接是否成功
    """
    try:
        db = get_database()
        if db is None:
            return False

        # 执行简单的查询测试连接
        # PostgreSQL支持已迁移到MySQL，相关代码已注释
        # if db_config.database_type == 'postgresql':
        #     result = db.execute_query("SELECT 1")
        # else:
        if db_config._get_database_type() == "mysql":
            result = db.execute_query("SELECT 1")
        else:
            result = db.execute_query("SELECT 1", database_name="auth")

        return result is not None
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False


def close_database_connection():
    """
    关闭数据库连接
    """
    global _database_manager

    if _database_manager is not None:
        try:
            _database_manager.close_all_connections()
            _database_manager = None
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {str(e)}")


# 数据库健康检查
def health_check() -> dict:
    """
    数据库健康检查

    返回:
        dict: 健康检查结果
    """
    try:
        db = get_database()
        if db is None:
            return {"status": "unhealthy", "error": "数据库管理器初始化失败"}

        # 测试连接
        if test_database_connection():
            return {
                "status": "healthy",
                "database_type": db_config._get_database_type(),
                "connection": "active",
            }
        else:
            return {"status": "unhealthy", "error": "数据库连接测试失败"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
