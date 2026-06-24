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
MySQL数据库管理器
================

支持MySQL的数据库管理器
"""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple

import aiomysql

from src.config.database_config import db_config
from src.logger.logger import get_logger

logger = get_logger(__name__)


class MySQLConnectionPool:
    """MySQL连接池管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool = None
        self.logger = logger.bind(module=self.__class__.__name__)

    async def initialize(self):
        """初始化连接池"""
        try:
            # aiomysql的create_pool不支持read_timeout和write_timeout参数
            pool_config = {
                "host": self.config["host"],
                "port": self.config["port"],
                "db": self.config["database"],
                "user": self.config["user"],
                "password": self.config["password"],
                "minsize": 5,
                "maxsize": self.config.get("pool_size", 10),
                "autocommit": True,
            }
            # 只添加connect_timeout（如果aiomysql支持）
            if "connect_timeout" in self.config:
                pool_config["connect_timeout"] = self.config.get("connect_timeout", 10)
            self.pool = await aiomysql.create_pool(**pool_config)
            self.logger.info("MySQL连接池初始化成功")
        except Exception as e:
            self.logger.error(f"MySQL连接池初始化失败: {str(e)}")
            raise

    async def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.logger.info("MySQL连接池已关闭")

    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        if not self.pool:
            await self.initialize()

        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            self.pool.release(conn)


class MySQLDatabaseManager:
    """MySQL数据库管理器"""

    def __init__(self):
        self.config = db_config._get_mysql_config()
        self.pool = MySQLConnectionPool(self.config)
        self.logger = logger.bind(module=self.__class__.__name__)

    async def initialize(self):
        """初始化数据库管理器"""
        await self.pool.initialize()
        self.logger.info("MySQL数据库管理器初始化完成")

    async def close(self):
        """关闭数据库管理器"""
        await self.pool.close()

    # 用户相关操作
    async def create_user(
        self,
        user_id: str,
        username: str,
        email: str,
        password_hash: str,
        role: str = "patient",
    ) -> bool:
        """创建用户"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO users (user_id, username, email, password_hash, role)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            username = VALUES(username),
                            email = VALUES(email),
                            password_hash = VALUES(password_hash),
                            role = VALUES(role),
                            updated_at = CURRENT_TIMESTAMP
                    """,
                        (user_id, username, email, password_hash, role),
                    )
                    await conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"创建用户失败: {str(e)}")
            return False

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT * FROM users WHERE user_id = %s", (user_id,)
                    )
                    row = await cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"获取用户信息失败: {str(e)}")
            return None

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取所有用户失败: {str(e)}")
            return []

    # 聊天历史操作
    async def store_chat_message(
        self,
        user_id: str,
        role: str,
        content: str,
        session_id: str | None = None,
        agent_name: str | None = None,
    ) -> bool:
        """存储聊天消息"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO chat_history (user_id, role, content, session_id, agent_name)
                        VALUES (%s, %s, %s, %s, %s)
                    """,
                        (user_id, role, content, session_id, agent_name),
                    )
                    await conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"存储聊天消息失败: {str(e)}")
            return False

    async def get_chat_history(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取聊天历史"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """
                        SELECT * FROM chat_history 
                        WHERE user_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """,
                        (user_id, limit),
                    )
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取聊天历史失败: {str(e)}")
            return []

    async def get_all_chat_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有聊天历史"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """
                        SELECT * FROM chat_history 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """,
                        (limit,),
                    )
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取所有聊天历史失败: {str(e)}")
            return []

    # 医疗影像操作
    async def store_medical_image(
        self,
        user_id: str,
        hospital_id: str,
        image_type: str,
        image_category: str,
        examination_date: str,
        description: str | None = None,
        filename: str | None = None,
        file_size: int | None = None,
        file_path: str | None = None,
        image_data: bytes | None = None,
    ) -> bool:
        """存储医疗影像"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO medical_images (user_id, hospital_id, image_type, 
                                                  image_category, examination_date, 
                                                  description, filename, file_size, file_path, image_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            user_id,
                            hospital_id,
                            image_type,
                            image_category,
                            examination_date,
                            description,
                            filename,
                            file_size,
                            file_path,
                            image_data,
                        ),
                    )
                    await conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"存储医疗影像失败: {str(e)}")
            return False

    async def get_medical_images(
        self, user_id: str, hospital_id: str | None = None
    ) -> List[Dict[str, Any]]:
        """获取医疗影像"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if hospital_id:
                        await cursor.execute(
                            """
                            SELECT * FROM medical_images 
                            WHERE user_id = %s AND hospital_id = %s
                            ORDER BY created_at DESC
                        """,
                            (user_id, hospital_id),
                        )
                    else:
                        await cursor.execute(
                            """
                            SELECT * FROM medical_images 
                            WHERE user_id = %s
                            ORDER BY created_at DESC
                        """,
                            (user_id,),
                        )
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取医疗影像失败: {str(e)}")
            return []

    async def get_all_medical_images(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有医疗影像"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """
                        SELECT * FROM medical_images 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """,
                        (limit,),
                    )
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取所有医疗影像失败: {str(e)}")
            return []

    # 医疗记录操作
    async def store_medical_record(
        self,
        user_id: str,
        hospital_id: str,
        record_data: str,
        record_type: str,
        description: str | None = None,
    ) -> bool:
        """存储医疗记录"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO medical_records (user_id, hospital_id, record_data, record_type, description)
                        VALUES (%s, %s, %s, %s, %s)
                    """,
                        (user_id, hospital_id, record_data, record_type, description),
                    )
                    await conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"存储医疗记录失败: {str(e)}")
            return False

    async def get_medical_records(
        self, user_id: str, hospital_id: str | None = None
    ) -> List[Dict[str, Any]]:
        """获取医疗记录"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if hospital_id:
                        await cursor.execute(
                            """
                            SELECT * FROM medical_records 
                            WHERE user_id = %s AND hospital_id = %s
                            ORDER BY created_at DESC
                        """,
                            (user_id, hospital_id),
                        )
                    else:
                        await cursor.execute(
                            """
                            SELECT * FROM medical_records 
                            WHERE user_id = %s
                            ORDER BY created_at DESC
                        """,
                            (user_id,),
                        )
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取医疗记录失败: {str(e)}")
            return []

    async def get_all_medical_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有医疗记录"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """
                        SELECT * FROM medical_records 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """,
                        (limit,),
                    )
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取所有医疗记录失败: {str(e)}")
            return []

    # 医院信息操作
    async def get_hospitals(self) -> List[Dict[str, Any]]:
        """获取所有医院信息"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT * FROM hospitals ORDER BY created_at")
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取医院信息失败: {str(e)}")
            return []

    # 统计信息
    async def get_statistics(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor() as cursor:
                    stats = {}

                    # 用户数量
                    await cursor.execute("SELECT COUNT(*) FROM users")
                    stats["users"] = (await cursor.fetchone())[0]

                    # 聊天记录数量
                    await cursor.execute("SELECT COUNT(*) FROM chat_history")
                    stats["chat_history"] = (await cursor.fetchone())[0]

                    # 医疗影像数量
                    await cursor.execute("SELECT COUNT(*) FROM medical_images")
                    stats["medical_images"] = (await cursor.fetchone())[0]

                    # 医疗记录数量
                    await cursor.execute("SELECT COUNT(*) FROM medical_records")
                    stats["medical_records"] = (await cursor.fetchone())[0]

                    # 医院数量
                    await cursor.execute("SELECT COUNT(*) FROM hospitals")
                    stats["hospitals"] = (await cursor.fetchone())[0]

                    return stats
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {}

    async def execute_query(
        self, sql: str, params: Tuple | None = None, database: str | None = None
    ):
        if sql == "":
            return None
        try:
            async with self.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if params is None:
                        await cursor.execute(sql)
                    else:
                        await cursor.execute(sql, params)

                    if sql.strip().upper().startswith("SELECT"):
                        return await cursor.fetchall()
                    elif sql.strip().upper().startswith(("UPDATE", "INSERT")):
                        await conn.commit()
                        return cursor.rowcount
                    else:
                        return cursor.rowcount
        except Exception as e:
            self.logger.error(f"{sql} 执行失败: {str(e)}")
            return None


# 全局数据库管理器实例
mysql_db_manager = MySQLDatabaseManager()
