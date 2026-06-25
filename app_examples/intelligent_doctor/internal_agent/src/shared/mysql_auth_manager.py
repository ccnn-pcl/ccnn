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
MySQL 认证适配器
================

为 AuthManager 提供 MySQL 支持
使用同步 pymysql 库避免异步问题
"""

from datetime import datetime
from typing import Any, Dict, Optional

import pymysql
from pymysql.cursors import DictCursor

from src.logger.logger import get_logger
from src.shared.auth_manager import LoginAttempt, User

logger = get_logger(__name__)


class MySQLAuthAdapter:
    """MySQL 认证适配器 - 提供与 SQLite AuthDatabaseManager 相同的接口"""

    def __init__(self, config: dict[str, Any]):
        """初始化 MySQL 认证适配器"""
        self.logger = logger.bind(name=self.__class__.__name__)
        self.config = config
        self.connection = None

    def _init_database(self):
        """初始化数据库（保持兼容性，实际不执行）"""
        self.logger.Info(f"db config: {self.config}")

    def _get_connection(self):
        """获取数据库连接"""
        try:
            return pymysql.connect(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                charset=self.config.get("charset", "utf8mb4"),
                cursorclass=DictCursor,
            )
        except Exception as e:
            self.logger.error(f"Failed to get MySQL connection: {str(e)}")
            raise

    def create_user(
        self,
        user: User,
        password_hash: str,
        role: str = "patient",
    ) -> bool:
        """创建用户"""
        try:
            conn = self._get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
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
                        (user.user_id, user.username, user.email, password_hash, role),
                    )
                    conn.commit()
                return True
            finally:
                conn.close()
        except Exception as e:
            self.logger.error(f"创建用户失败: {str(e)}")
            return False

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        try:
            conn = self._get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM users WHERE username = %s", (username,)
                    )
                    row = cursor.fetchone()
                    return User(**row) if row else None
            finally:
                conn.close()
        except Exception as e:
            self.logger.error(f"获取用户失败: {str(e)}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户"""
        try:
            conn = self._get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                    row = cursor.fetchone()
                    return User(**row) if row else None
            finally:
                conn.close()
        except Exception as e:
            self.logger.error(f"获取用户失败: {str(e)}")
            return None

    def update_user(self, user: User) -> bool:
        """更新用户信息"""
        try:
            conn = self._get_connection()
            try:
                with conn.cursor() as cursor:
                    # 构建更新语句
                    updates = []
                    values = []
                    if user.username:
                        updates.append(f"{'username'} = %s")
                        values.append(user.username)
                    if user.email:
                        updates.append(f"{'email'} = %s")
                        values.append(user.username)
                    if user.password_hash:
                        updates.append(f"{'password_hash'} = %s")
                        values.append(user.password_hash)
                    if user.role:
                        updates.append(f"{'role'} = %s")
                        values.append(user.role)
                    if user.status:
                        updates.append(f"{'status'} = %s")
                        values.append(user.status)

                    if not updates:
                        return True
                    values.append(user.user_id)
                    sql = f"UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s"
                    cursor.execute(sql, values)
                    conn.commit()
                return True
            finally:
                conn.close()
        except Exception as e:
            self.logger.error(f"更新用户失败: {str(e)}")
            return False

    def verify_password(self, user_id: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            user = self.get_user_by_id(user_id)
            if user and user.password_hash == password_hash:
                return True
            return False
        except Exception as e:
            self.logger.error(f"验证密码失败: {str(e)}")
            return False

    def update_password(self, user_id: str, new_password_hash: str) -> bool:
        """更新密码"""
        try:
            conn = self._get_connection()
            try:
                with conn.cursor() as cursor:
                    # 构建更新语句

                    sql = "UPDATE users SET password_hash=%s WHERE user_id = %s"
                    cursor.execute(sql, (new_password_hash, user_id))
                    conn.commit()
                return True
            finally:
                conn.close()
        except Exception as e:
            self.logger.error(f"更新用户密码失败: {str(e)}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        return True

    def log_audit_event(
        self,
        user_id: str,
        action: str,
        resource: str | None = None,
        details: Dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """记录审计日志"""
        try:
            conn = self._get_connection()
            try:
                with conn.cursor() as cursor:
                    import json

                    details_json = json.dumps(details) if details else None
                    cursor.execute(
                        """
                        INSERT INTO audit_logs (user_id, action, resource, details, ip_address, user_agent)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (
                            user_id,
                            action,
                            resource,
                            details_json,
                            ip_address,
                            user_agent,
                        ),
                    )
                    conn.commit()
                return True
            finally:
                conn.close()
        except Exception as e:
            self.logger.error(f"记录审计日志失败: {str(e)}")
            return False

    def create_session(
        self,
        session_id: str,
        user_id: str,
        token: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """创建会话"""
        return True

    def record_login_attempt(self, attempt: LoginAttempt) -> bool:
        """记录登录尝试"""
        return True
