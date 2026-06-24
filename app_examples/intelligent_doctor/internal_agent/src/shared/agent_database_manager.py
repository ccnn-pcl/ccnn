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
智能体数据库访问管理器 - 安全的数据库访问控制
===============================================

这个模块为智能体提供安全的数据库访问控制，包括：

1. 权限验证
   - 智能体访问权限验证
   - 数据访问权限验证
   - 操作权限验证
   - 目标用户数据访问权限验证

2. 安全数据库操作
   - 自动权限检查
   - 访问日志记录
   - 错误处理
   - 数据隔离

3. 审计功能
   - 数据库访问日志
   - 权限验证记录
   - 异常操作监控

作者: QSIR
版本: 1.0
"""

import functools
import logging
import sqlite3
from datetime import datetime
from typing import Callable, Dict, Tuple

from auth_manager import User, audit_manager, authz_manager
from database_auth import db_auth_manager

logger = logging.getLogger(__name__)


class AgentDatabaseManager:
    """智能体数据库访问管理器"""

    def __init__(self, user: User, agent_name: str):
        self.user = user
        self.agent_name = agent_name
        self.authz_manager = authz_manager
        self.db_auth_manager = db_auth_manager
        self.audit_manager = audit_manager

    def _verify_permissions(
        self, data_type: str, operation: str, target_user_id: str = None
    ) -> Tuple[bool, str]:
        """验证权限"""
        try:
            # 1. 验证智能体访问权限
            if not self.authz_manager.check_agent_access(
                self.user.role, self.agent_name, self.user.user_id
            ):
                return False, f"智能体 {self.agent_name} 访问权限不足"

            # 2. 验证数据访问权限
            if not self.authz_manager.check_data_access(
                self.user.role, data_type, self.user.user_id
            ):
                return False, f"数据 {data_type} 访问权限不足"

            # 3. 验证操作权限
            if not self.authz_manager.check_action_permission(
                self.user.role, operation, self.user.user_id
            ):
                return False, f"操作 {operation} 权限不足"

            # 4. 验证目标用户数据访问权限
            if target_user_id and target_user_id != self.user.user_id:
                if not self.authz_manager.check_data_access(
                    self.user.role, "patient_data", self.user.user_id
                ):
                    return False, "无权限访问其他用户数据"

            return True, "权限验证通过"

        except Exception as e:
            logger.error(f"权限验证失败: {str(e)}")
            return False, f"权限验证失败: {str(e)}"

    def _log_database_operation(
        self,
        operation: str,
        table_name: str,
        target_user_id: str = None,
        details: str = None,
    ):
        """记录数据库操作日志"""
        try:
            # 记录到数据库权限管理器
            self.db_auth_manager.log_database_operation(
                user_id=self.user.user_id,
                operation=operation,
                table_name=table_name,
                data_id=target_user_id,
                details=details or f"智能体 {self.agent_name} 执行 {operation} 操作",
            )

            # 记录到审计管理器
            self.audit_manager.log_user_action(
                user_id=self.user.user_id,
                action=f"AGENT_DB_{operation.upper()}",
                resource=f"{self.agent_name}.{table_name}",
                details={
                    "agent_name": self.agent_name,
                    "operation": operation,
                    "table_name": table_name,
                    "target_user_id": target_user_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"记录数据库操作日志失败: {str(e)}")

    def get_medical_data(self, target_user_id: str) -> Dict:
        """安全获取医疗数据"""
        try:
            # 验证权限
            has_permission, message = self._verify_permissions(
                "medical_records", "read", target_user_id
            )
            if not has_permission:
                logger.warning(f"[{self.agent_name}] 权限验证失败: {message}")
                return {"error": f"权限不足: {message}"}

            # 记录访问日志
            self._log_database_operation(
                operation="read",
                table_name="medical_records",
                target_user_id=target_user_id,
                details=f"获取用户 {target_user_id} 医疗数据",
            )

            # 执行数据库查询
            return self._execute_medical_query(target_user_id)

        except Exception as e:
            logger.error(f"[{self.agent_name}] 获取医疗数据失败: {str(e)}")
            return {"error": f"数据访问失败: {str(e)}"}

    def store_medical_data(self, target_user_id: str, data: Dict) -> bool:
        """安全存储医疗数据"""
        try:
            # 验证权限
            has_permission, message = self._verify_permissions(
                "medical_records", "write", target_user_id
            )
            if not has_permission:
                logger.warning(f"[{self.agent_name}] 权限验证失败: {message}")
                return False

            # 记录操作日志
            self._log_database_operation(
                operation="write",
                table_name="medical_records",
                target_user_id=target_user_id,
                details=f"存储用户 {target_user_id} 医疗数据",
            )

            # 执行数据库操作
            return self._execute_medical_insert(target_user_id, data)

        except Exception as e:
            logger.error(f"[{self.agent_name}] 存储医疗数据失败: {str(e)}")
            return False

    def get_lab_reports(self, target_user_id: str) -> Dict:
        """安全获取化验单数据"""
        try:
            # 验证权限
            has_permission, message = self._verify_permissions(
                "lab_reports", "read", target_user_id
            )
            if not has_permission:
                logger.warning(f"[{self.agent_name}] 权限验证失败: {message}")
                return {"error": f"权限不足: {message}"}

            # 记录访问日志
            self._log_database_operation(
                operation="read",
                table_name="lab_reports",
                target_user_id=target_user_id,
                details=f"获取用户 {target_user_id} 化验单数据",
            )

            # 执行数据库查询
            return self._execute_lab_query(target_user_id)

        except Exception as e:
            logger.error(f"[{self.agent_name}] 获取化验单数据失败: {str(e)}")
            return {"error": f"数据访问失败: {str(e)}"}

    def store_lab_reports(self, target_user_id: str, data: Dict) -> bool:
        """安全存储化验单数据"""
        try:
            # 验证权限
            has_permission, message = self._verify_permissions(
                "lab_reports", "write", target_user_id
            )
            if not has_permission:
                logger.warning(f"[{self.agent_name}] 权限验证失败: {message}")
                return False

            # 记录操作日志
            self._log_database_operation(
                operation="write",
                table_name="lab_reports",
                target_user_id=target_user_id,
                details=f"存储用户 {target_user_id} 化验单数据",
            )

            # 执行数据库操作
            return self._execute_lab_insert(target_user_id, data)

        except Exception as e:
            logger.error(f"[{self.agent_name}] 存储化验单数据失败: {str(e)}")
            return False

    def _execute_medical_query(self, target_user_id: str) -> Dict:
        """执行医疗数据查询"""
        try:
            conn = sqlite3.connect("data/medical_records.db")
            c = conn.cursor()

            # 获取病历数据
            c.execute(
                """
                SELECT record_data, record_type, timestamp 
                FROM medical_records 
                WHERE user_id = ? 
                ORDER BY examination_date DESC 
                LIMIT 1
            """,
                (target_user_id,),
            )
            medical_record = c.fetchone()

            # 获取化验单数据
            c.execute(
                """
                SELECT report_data, report_type, timestamp 
                FROM lab_reports 
                WHERE user_id = ? 
                ORDER BY examination_date DESC 
                LIMIT 1
            """,
                (target_user_id,),
            )
            lab_report = c.fetchone()

            conn.close()

            return {
                "medical_records": medical_record[0] if medical_record else None,
                "lab_reports": lab_report[0] if lab_report else None,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"执行医疗数据查询失败: {str(e)}")
            return {"error": f"数据库查询失败: {str(e)}"}

    def _execute_medical_insert(self, target_user_id: str, data: Dict) -> bool:
        """执行医疗数据插入"""
        try:
            conn = sqlite3.connect("data/medical_records.db")
            c = conn.cursor()

            # 插入医疗记录
            if "medical_record" in data:
                c.execute(
                    """
                    INSERT OR REPLACE INTO medical_records 
                    (user_id, record_data, record_type, examination_date, timestamp) 
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        target_user_id,
                        data["medical_record"],
                        data.get("record_type", "general"),
                        data.get("examination_date", datetime.now().date()),
                        datetime.now(),
                    ),
                )

            # 插入化验单数据
            if "lab_report" in data:
                c.execute(
                    """
                    INSERT OR REPLACE INTO lab_reports 
                    (user_id, report_data, report_type, examination_date, timestamp) 
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        target_user_id,
                        data["lab_report"],
                        data.get("report_type", "general"),
                        data.get("examination_date", datetime.now().date()),
                        datetime.now(),
                    ),
                )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"执行医疗数据插入失败: {str(e)}")
            return False

    def _execute_lab_query(self, target_user_id: str) -> Dict:
        """执行化验单数据查询"""
        try:
            conn = sqlite3.connect("data/medical_records.db")
            c = conn.cursor()

            c.execute(
                """
                SELECT report_data, report_type, timestamp 
                FROM lab_reports 
                WHERE user_id = ? 
                ORDER BY examination_date DESC 
                LIMIT 10
            """,
                (target_user_id,),
            )
            lab_reports = c.fetchall()

            conn.close()

            return {
                "lab_reports": [
                    {"data": report[0], "type": report[1], "timestamp": report[2]}
                    for report in lab_reports
                ],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"执行化验单数据查询失败: {str(e)}")
            return {"error": f"数据库查询失败: {str(e)}"}

    def _execute_lab_insert(self, target_user_id: str, data: Dict) -> bool:
        """执行化验单数据插入"""
        try:
            conn = sqlite3.connect("data/medical_records.db")
            c = conn.cursor()

            c.execute(
                """
                INSERT OR REPLACE INTO lab_reports 
                (user_id, report_data, report_type, examination_date, timestamp) 
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    target_user_id,
                    data.get("report_data", ""),
                    data.get("report_type", "general"),
                    data.get("examination_date", datetime.now().date()),
                    datetime.now(),
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"执行化验单数据插入失败: {str(e)}")
            return False


def require_agent_permission(
    agent_name: str, data_type: str = None, operation: str = "read"
):
    """智能体权限验证装饰器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, user: User, *args, **kwargs):
            try:
                # 1. 验证智能体访问权限
                if not authz_manager.check_agent_access(
                    user.role, agent_name, user.user_id
                ):
                    logger.warning(f"用户 {user.username} 无权限访问 {agent_name}")
                    return {"error": f"权限不足，无法访问 {agent_name}"}

                # 2. 验证数据访问权限
                if data_type and not authz_manager.check_data_access(
                    user.role, data_type, user.user_id
                ):
                    logger.warning(f"用户 {user.username} 无权限访问 {data_type} 数据")
                    return {"error": f"权限不足，无法访问 {data_type} 数据"}

                # 3. 验证操作权限
                if not authz_manager.check_action_permission(
                    user.role, operation, user.user_id
                ):
                    logger.warning(f"用户 {user.username} 无权限执行 {operation} 操作")
                    return {"error": f"权限不足，无法执行 {operation} 操作"}

                # 4. 记录操作日志
                db_auth_manager.log_database_operation(
                    user_id=user.user_id,
                    operation=operation,
                    table_name=data_type or "unknown",
                    details=f"智能体 {agent_name} 执行 {func.__name__}",
                )

                # 5. 执行原函数
                return func(self, user, *args, **kwargs)

            except Exception as e:
                logger.error(f"权限验证装饰器执行失败: {str(e)}")
                return {"error": f"权限验证失败: {str(e)}"}

        return wrapper

    return decorator


def create_agent_db_manager(user: User, agent_name: str) -> AgentDatabaseManager:
    """创建智能体数据库管理器实例"""
    return AgentDatabaseManager(user, agent_name)
