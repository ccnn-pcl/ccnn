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
聊天服务
========

提供智能体对话、聊天历史管理等服务

作者: QSIR
版本: 1.0
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# 添加项目根目录到Python路径
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# 【✅ 重构后】使用重构后的CybertwinAgent
from app.utils.database import get_database
from shared.agents.coordinator.cybertwin_agent_refactored import (
    CybertwinAgent,
    CybertwinConfig,
    DemoModeConfig,
)
from shared.config.model_config import get_config

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务类"""

    def __init__(self):
        """初始化聊天服务"""
        logger.info("=" * 80)
        logger.info("[ChatService] 开始初始化聊天服务...")
        self.cybertwin_agent = None
        self._init_cybertwin_agent()
        logger.info("[ChatService] 聊天服务初始化完成")
        logger.info("=" * 80)

    def _init_cybertwin_agent(self):
        """初始化Cybertwin智能体"""
        try:
            logger.info("[ChatService] 开始初始化Cybertwin智能体...")

            # 创建CybertwinAgent配置
            logger.info("[ChatService] 获取模型配置...")
            model_config = get_config("qwen")  # 使用qwen-3b模型
            logger.info(f"[ChatService] 模型配置获取成功: {model_config.model_name}")

            # 演示模式配置（从环境变量读取，默认启用）
            demo_mode_enabled = os.getenv("DEMO_MODE_ENABLED", "true").lower() == "true"
            demo_mode_config = DemoModeConfig(
                enable_demo_mode=demo_mode_enabled,
                force_data_proxy_for_diabetes=True,
                enable_two_round_diagnosis=True,
                random_route_for_non_diabetes=True,
                use_generic_specialist=True,
            )

            cybertwin_config = CybertwinConfig(
                model_config=model_config.to_dict(),
                enable_auth=False,  # 在服务层处理认证
                enable_audit=False,  # 在服务层处理审计
                max_context_length=4000,
                intent_threshold=0.7,
                demo_mode=demo_mode_config,  # 演示模式配置
            )
            logger.info("[ChatService] 创建CybertwinAgent配置成功")

            # 初始化智能体
            logger.info("[ChatService] 创建CybertwinAgent实例...")
            self.cybertwin_agent = CybertwinAgent(cybertwin_config)
            logger.info("=" * 80)
            logger.info("[OK] Cybertwin智能体初始化完成")
            logger.info("=" * 80)
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"[ERROR] Cybertwin智能体初始化失败: {str(e)}")
            logger.error("=" * 80)
            import traceback

            logger.error(traceback.format_exc())
            self.cybertwin_agent = None

    async def handle_chat(
        self,
        user_input: str,
        user_id: str,
        user_info: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        处理聊天消息

        参数:
            user_input: 用户输入
            user_id: 用户ID
            user_info: 用户信息
            context: 对话上下文

        返回:
            Optional[Dict[str, Any]]: 聊天响应
        """
        try:
            print("\n" + "[聊天服务]" * 40)
            print("[聊天服务] 开始处理消息...")
            print(f"[聊天服务] 用户ID: {user_id}")
            print(f"[聊天服务] 消息: {user_input[:50]}...")
            print("[聊天服务]" * 40 + "\n")

            if not self.cybertwin_agent:
                logger.error("Cybertwin智能体未初始化")
                print("[ERROR] Cybertwin智能体未初始化")
                return None

            logger.info(
                f"[聊天服务] 开始处理用户 {user_id} 的聊天消息: {user_input[:50]}..."
            )
            logger.info(f"[聊天服务] 用户信息: {user_info}")

            # 记录开始时间
            import time

            start_time = time.time()

            # 【✅ 重构后】调用重构后的CybertwinAgent.execute()方法
            # 注意：重构后的execute方法仍返回元组 (agent_name, result)，但result是字典格式
            print("[准备调用] CybertwinAgent（重构版）处理聊天...")
            logger.info("[聊天服务] 开始调用CybertwinAgent.execute()（重构版）")
            agent_name, result = await self.cybertwin_agent.execute(
                user_input, user_id, user_info
            )
            print("[OK] CybertwinAgent（重构版）处理完成！")

            # 记录处理时间
            processing_time = time.time() - start_time
            logger.info(
                f"[聊天服务] CybertwinAgent处理完成，耗时: {processing_time:.2f}秒"
            )

            # 【✅ 适配重构后的返回格式】
            # 重构后的result格式: {"status": "success", "report": "...", "specialist_results": [...], ...}
            # 或者: {"status": "error", "error": "...", "report": "..."}
            if result and isinstance(result, dict):
                # 检查是否有 report 字段且 status 为 success
                if result.get("status") == "success" and result.get("report"):
                    # 提取综合诊断报告
                    report = result.get("report", "")
                    specialist_results = result.get("specialist_results", [])
                    rounds = result.get("rounds", 1)

                    # 提取数据来源（从专科医生结果中提取）
                    data_sources = []
                    for r in specialist_results:
                        if isinstance(r, dict):
                            sources = r.get("data_sources", [])
                            if isinstance(sources, list):
                                data_sources.extend(sources)
                            elif sources:
                                data_sources.append(sources)

                    logger.info(
                        f"[聊天服务] 诊断成功，报告长度: {len(report)}, 专科医生数: {len(specialist_results)}, 轮次: {rounds}"
                    )

                    # 清理metadata中的异常对象，确保可以序列化
                    cleaned_specialist_results = self._clean_serializable_data(
                        specialist_results
                    )
                    cleaned_data_sources = self._clean_serializable_data(data_sources)

                    # 存储聊天记录
                    logger.info("[聊天服务] 开始存储聊天记录")
                    await self._store_chat_message(
                        user_id, "user", user_input, user_info
                    )
                    await self._store_chat_message(
                        user_id, "assistant", report, user_info
                    )

                    # 构建响应（保持与前端API兼容）
                    response = {
                        "agent_name": "CybertwinAgent",
                        "response": report,  # 综合诊断报告
                        "metadata": {
                            "specialist_results": cleaned_specialist_results,
                            "rounds": rounds,
                            "data_sources": cleaned_data_sources,
                            "status": "success",
                            "processing_time": processing_time,
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    # 错误处理：result是字典但status不是success，或者没有report字段
                    error_msg = result.get("error", result.get("report", "诊断失败"))

                    logger.error(f"[聊天服务] 诊断失败: {error_msg}")

                    # 存储错误记录
                    await self._store_chat_message(
                        user_id, "user", user_input, user_info
                    )
                    await self._store_chat_message(
                        user_id, "assistant", f"诊断失败: {error_msg}", user_info
                    )

                    response = {
                        "agent_name": "CybertwinAgent",
                        "response": f"抱歉，诊断过程中出现错误: {error_msg}",
                        "metadata": {
                            "status": "error",
                            "error": error_msg,
                            "processing_time": processing_time,
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
            else:
                # 错误处理：result不是字典（可能是字符串或其他类型）
                if isinstance(result, str):
                    error_msg = result
                else:
                    error_msg = "诊断失败"

                logger.error(f"[聊天服务] 诊断失败: {error_msg}")

                # 存储错误记录
                await self._store_chat_message(user_id, "user", user_input, user_info)
                await self._store_chat_message(
                    user_id, "assistant", f"诊断失败: {error_msg}", user_info
                )

                response = {
                    "agent_name": "CybertwinAgent",
                    "response": f"抱歉，诊断过程中出现错误: {error_msg}",
                    "metadata": {
                        "status": "error",
                        "error": error_msg,
                        "processing_time": processing_time,
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            logger.info(f"[聊天服务] 聊天处理完成，总耗时: {processing_time:.2f}秒")
            return response

        except Exception as e:
            logger.error(f"[聊天服务] 聊天处理失败: {str(e)}", exc_info=True)
            return None

    def _clean_serializable_data(self, data: Any) -> Any:
        """
        清理数据中无法序列化的对象（如异常对象）

        参数:
            data: 需要清理的数据

        返回:
            清理后的可序列化数据
        """

        if data is None:
            return None

        # 如果是异常对象，转换为字符串
        if isinstance(data, Exception):
            return {"error_type": type(data).__name__, "error_message": str(data)}

        # 如果是列表，递归清理每个元素
        if isinstance(data, list):
            cleaned = []
            for item in data:
                cleaned_item = self._clean_serializable_data(item)
                if cleaned_item is not None:
                    cleaned.append(cleaned_item)
            return cleaned

        # 如果是字典，递归清理每个值
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # 跳过异常对象
                if isinstance(value, (Exception, asyncio.CancelledError)):
                    logger.warning(
                        f"[ChatService] 跳过无法序列化的异常对象: {type(value).__name__} at key '{key}'"
                    )
                    continue
                cleaned_value = self._clean_serializable_data(value)
                if cleaned_value is not None:
                    cleaned[key] = cleaned_value
            return cleaned

        # 其他类型直接返回（字符串、数字、布尔值等）
        return data

    # 流式聊天功能已禁用
    # async def handle_chat_stream(self, user_input: str, user_id: str, user_info: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
    #     """
    #     处理流式聊天消息
    #
    #     参数:
    #         user_input: 用户输入
    #         user_id: 用户ID
    #         user_info: 用户信息
    #         context: 对话上下文
    #
    #     返回:
    #         AsyncGenerator[Dict[str, Any], None]: 流式响应生成器
    #     """
    #     try:
    #         if not self.cybertwin_agent:
    #             logger.error("Cybertwin智能体未初始化")
    #             yield {"type": "error", "message": "智能体未初始化"}
    #             return
    #
    #         logger.info(f"[流式聊天服务] 开始处理用户 {user_id} 的流式聊天消息: {user_input[:50]}...")
    #
    #         # 发送开始处理信号
    #         yield {
    #             "type": "processing",
    #             "message": "正在分析您的问题...",
    #             "agent_name": "系统",
    #             "timestamp": datetime.now().isoformat()
    #         }
    #
    #         # 模拟流式处理过程
    #         processing_steps = [
    #             "正在理解您的症状描述...",
    #             "正在匹配最适合的医疗智能体...",
    #             "正在生成专业诊断建议...",
    #             "正在整理医疗建议..."
    #         ]
    #
    #         for i, step in enumerate(processing_steps):
    #             yield {
    #                 "type": "processing",
    #                 "message": step,
    #                 "agent_name": "系统",
    #                 "timestamp": datetime.now().isoformat(),
    #                 "progress": (i + 1) / len(processing_steps) * 100
    #             }
    #             await asyncio.sleep(0.5)  # 模拟处理时间
    #
    #         # 调用CybertwinAgent处理聊天
    #         logger.info(f"[流式聊天服务] 开始调用CybertwinAgent.execute()")
    #         start_time = time.time()
    #         intent, result = await self.cybertwin_agent.execute(user_input, user_id, user_info)
    #         processing_time = time.time() - start_time
    #
    #         # 发送智能体信息
    #         yield {
    #             "type": "agent_info",
    #             "message": f"已匹配到 {intent} 智能体",
    #             "agent_name": intent,
    #             "timestamp": datetime.now().isoformat()
    #         }
    #
    #         # 模拟流式输出响应内容
    #         response_text = self._format_response_for_frontend(intent, result)
    #         words = response_text.split()
    #         current_response = ""
    #
    #         for i, word in enumerate(words):
    #             current_response += word + " "
    #             yield {
    #                 "type": "content",
    #                 "message": word,
    #                 "agent_name": intent,
    #                 "timestamp": datetime.now().isoformat(),
    #                 "is_partial": i < len(words) - 1
    #             }
    #             await asyncio.sleep(0.05)  # 控制输出速度
    #
    #         # 发送完整响应
    #         yield {
    #             "type": "complete",
    #             "message": response_text,
    #             "agent_name": intent,
    #             "metadata": self._build_metadata(intent, result, user_id),
    #             "timestamp": datetime.now().isoformat(),
    #             "processing_time": processing_time
    #         }
    #
    #         # 存储聊天记录
    #         logger.info(f"[流式聊天服务] 开始存储聊天记录")
    #         await self._store_chat_message(user_id, "user", user_input)
    #         await self._store_chat_message(user_id, "assistant", response_text)
    #
    #         logger.info(f"[流式聊天服务] 流式聊天处理完成: {intent}, 总耗时: {processing_time:.2f}秒")
    #
    #     except Exception as e:
    #         logger.error(f"[流式聊天服务] 流式聊天处理失败: {str(e)}", exc_info=True)
    #         yield {
    #             "type": "error",
    #             "message": f"处理失败: {str(e)}",
    #             "agent_name": "系统",
    #             "timestamp": datetime.now().isoformat()
    #         }

    async def get_chat_history(
        self, user_id: str, page: int = 1, page_size: int = 50
    ) -> Dict[str, Any]:
        """
        获取聊天历史（支持MySQL和SQLite）

        参数:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小

        返回:
            Dict[str, Any]: 聊天历史
        """
        try:
            db = get_database()
            if not db or not db.db_manager:
                logger.error("数据库连接失败")
                return {"messages": [], "total_count": 0}

            # 检查是否是MySQL/PostgreSQL数据库管理器（支持异步方法）
            if hasattr(db.db_manager, "get_chat_history"):
                # MySQL/PostgreSQL: 使用异步方法
                # 计算limit（MySQL/PostgreSQL的get_chat_history只支持limit，不支持分页）
                limit = page_size * page  # 获取足够多的记录
                all_messages = await db.db_manager.get_chat_history(user_id, limit)

                # 手动分页
                offset = (page - 1) * page_size
                messages = all_messages[offset : offset + page_size]

                # 格式化消息
                formatted_messages = []
                for msg in messages:
                    formatted_messages.append(
                        {
                            "role": msg.get("role", ""),
                            "content": msg.get("content", ""),
                            "timestamp": msg.get("timestamp", ""),
                        }
                    )

                return {
                    "messages": formatted_messages,
                    "total_count": len(all_messages),
                }
            else:
                # SQLite: 使用同步方法
                import sqlite3

                conn = sqlite3.connect("data/chat_history.db")
                cursor = conn.cursor()

                # 计算偏移量
                offset = (page - 1) * page_size

                # 查询聊天历史
                cursor.execute(
                    """
                    SELECT role, content, timestamp 
                    FROM history 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """,
                    (user_id, page_size, offset),
                )
                messages = cursor.fetchall()

                # 查询总数
                cursor.execute(
                    "SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,)
                )
                total_count = cursor.fetchone()[0]

                conn.close()

                # 格式化消息
                formatted_messages = []
                for role, content, timestamp in messages:
                    formatted_messages.append(
                        {"role": role, "content": content, "timestamp": timestamp}
                    )

                return {"messages": formatted_messages, "total_count": total_count}

        except Exception as e:
            logger.error(f"获取聊天历史失败: {str(e)}")
            return {"messages": [], "total_count": 0}

    async def clear_chat_history(self, user_id: str) -> bool:
        """
        清空聊天历史（支持MySQL和SQLite）

        参数:
            user_id: 用户ID

        返回:
            bool: 清空结果
        """
        try:
            db = get_database()
            if not db or not db.db_manager:
                logger.error("数据库连接失败")
                return False

            # 检查是否是MySQL数据库管理器（支持异步方法）
            if hasattr(db.db_manager, "pool"):
                # MySQL: 使用异步方法
                async with db.db_manager.pool.get_connection() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            "DELETE FROM chat_history WHERE user_id = %s", (user_id,)
                        )
                        await conn.commit()
                logger.info(f"用户 {user_id} 的聊天历史已清空")
                return True
            else:
                # SQLite: 使用同步方法
                import sqlite3

                conn = sqlite3.connect("data/chat_history.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                logger.info(f"用户 {user_id} 的聊天历史已清空")
                return True

        except Exception as e:
            logger.error(f"清空聊天历史失败: {str(e)}")
            return False

    def clear_dialogue_memory(self, user_id: str) -> bool:
        """
        清除用户的对话记忆（内存中的对话历史）

        参数:
            user_id: 用户ID

        返回:
            bool: 清除结果
        """
        try:
            if self.cybertwin_agent and hasattr(self.cybertwin_agent, "clear_memory"):
                self.cybertwin_agent.clear_memory(user_id)
                logger.info(f"[聊天服务] 用户 {user_id} 的对话记忆已清除")
                return True
            else:
                logger.warning(
                    "[聊天服务] CybertwinAgent未初始化或没有clear_memory方法"
                )
                return False
        except Exception as e:
            logger.error(f"[聊天服务] 清除对话记忆失败: {str(e)}")
            return False

    async def get_available_agents(self, user_role: str) -> List[Dict[str, Any]]:
        """
        获取可用智能体列表

        参数:
            user_role: 用户角色

        返回:
            List[Dict[str, Any]]: 智能体列表
        """
        try:
            # 根据用户角色返回可用智能体
            agents = []

            # 基础智能体（所有角色都可访问）
            agents.extend(
                [
                    {
                        "agent_id": "cybertwin",
                        "name": "数字孪生智能体",
                        "description": "意图识别和任务分发",
                        "available": True,
                    },
                    {
                        "agent_id": "internal_medicine",
                        "name": "内科智能体",
                        "description": "内科诊断和建议",
                        "available": True,
                    },
                    {
                        "agent_id": "surgical",
                        "name": "外科智能体",
                        "description": "外科诊断和建议",
                        "available": True,
                    },
                ]
            )

            # 根据角色添加特殊智能体
            if user_role in ["doctor", "admin"]:
                agents.extend(
                    [
                        # {
                        #     "agent_id": "image_analysis",
                        #     "name": "影像分析智能体",
                        #     "description": "医疗影像分析",
                        #     "available": True
                        # },  # 暂时注释掉影像分析智能体
                        {
                            "agent_id": "permission_admin",
                            "name": "权限管理智能体",
                            "description": "权限管理功能",
                            "available": True,
                        }
                    ]
                )

            return agents

        except Exception as e:
            logger.error(f"获取智能体列表失败: {str(e)}")
            return []

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取智能体状态

        参数:
            agent_id: 智能体ID

        返回:
            Optional[Dict[str, Any]]: 智能体状态
        """
        try:
            if agent_id == "cybertwin" and self.cybertwin_agent:
                return {
                    "agent_id": agent_id,
                    "status": "active",
                    "name": self.cybertwin_agent.name,
                    "description": "数字孪生智能体，负责意图识别和任务分发",
                    "capabilities": [
                        "意图识别",
                        "任务分发",
                        "权限控制",
                        "结果汇总",
                        "分诊建议",
                    ],
                    "last_activity": datetime.now().isoformat(),
                }
            else:
                return {
                    "agent_id": agent_id,
                    "status": "inactive",
                    "message": "智能体不可用",
                }

        except Exception as e:
            logger.error(f"获取智能体状态失败: {str(e)}")
            return None

    def _format_response_for_frontend(self, intent: str, result: Any) -> str:
        """
        格式化响应内容供前端显示

        参数:
            intent: 智能体名称
            result: 智能体返回结果

        返回:
            str: 格式化后的响应内容
        """
        try:
            logger.info(f"[格式化响应] 意图: {intent}, 结果类型: {type(result)}")
            logger.info(f"[格式化响应] 结果内容: {result}")

            # 如果result是字典类型，根据intent进行格式化
            if isinstance(result, dict):
                if intent == "DoctorQuestioning":
                    # 追问阶段：只显示问候语和问题
                    greeting = result.get("greeting", "")
                    questions = result.get("questions", [])

                    # 构建用户友好的响应
                    response_parts = [greeting] if greeting else []

                    if questions:
                        response_parts.append(
                            "\n为了更好地帮助您，我需要了解一些详细信息："
                        )
                        for i, question in enumerate(questions, 1):
                            response_parts.append(f"{i}. {question}")

                    return "\n".join(response_parts)

                elif intent == "DoctorConsultation":
                    # 初次问诊：只显示问候语和问题
                    greeting = result.get("greeting", "")
                    questions = result.get("questions", [])

                    response_parts = [greeting] if greeting else []

                    if questions:
                        response_parts.append(
                            "\n为了更好地帮助您，我需要了解一些详细信息："
                        )
                        for i, question in enumerate(questions, 1):
                            response_parts.append(f"{i}. {question}")

                    return "\n".join(response_parts)

                elif intent == "InternalMedicineAgent":
                    # 内科诊断结果：优先显示医生报告，更友好和条理化
                    logger.info("[格式化响应] 处理内科诊断结果")
                    if "doctor_report" in result and result["doctor_report"]:
                        logger.info("[格式化响应] 找到doctor_report字段，使用医生报告")
                        return result["doctor_report"]
                    elif "diagnosis" in result and result["diagnosis"]:
                        logger.info("[格式化响应] 使用diagnosis字段")
                        return result["diagnosis"]
                    else:
                        logger.info("[格式化响应] 未找到有效字段，使用默认消息")
                        return "感谢您的咨询，建议您及时就医进行详细检查。"

                elif intent == "SurgicalAgent":
                    # 外科诊断结果：优先显示医生报告，更友好和条理化
                    logger.info("[格式化响应] 处理外科诊断结果")
                    if "doctor_report" in result and result["doctor_report"]:
                        logger.info("[格式化响应] 找到doctor_report字段，使用医生报告")
                        return result["doctor_report"]
                    elif "summary" in result and result["summary"]:
                        logger.info("[格式化响应] 使用summary字段")
                        return result["summary"]
                    elif "diagnosis" in result and result["diagnosis"]:
                        logger.info("[格式化响应] 使用diagnosis字段")
                        return result["diagnosis"]
                    else:
                        logger.info("[格式化响应] 未找到有效字段，使用默认消息")
                        return "感谢您的咨询，建议您及时就医进行详细检查。"

                # elif intent in ["ImageAnalysis", "MedicalAnalysis"]:  # 暂时注释掉影像分析
                #     # 分析结果：显示主要分析内容
                #     logger.info(f"[格式化响应] 处理影像分析结果，查找comprehensive_analysis字段")
                #     if "comprehensive_analysis" in result:
                #         # 跨医院协作分析结果
                #         logger.info(f"[格式化响应] 找到comprehensive_analysis字段: {result['comprehensive_analysis'][:100]}...")
                #         return result["comprehensive_analysis"]
                #     elif "analysis_result" in result:
                #         logger.info(f"[格式化响应] 找到analysis_result字段")
                #         return result["analysis_result"]

                # 通用处理：查找常见字段
                if "diagnosis" in result:
                    logger.info("[格式化响应] 找到diagnosis字段")
                    return result["diagnosis"]
                elif "summary" in result:
                    logger.info("[格式化响应] 找到summary字段")
                    return result["summary"]
                elif "analysis" in result:
                    logger.info("[格式化响应] 找到analysis字段")
                    return result["analysis"]
                else:
                    # 如果没有找到标准字段，返回第一个字符串值
                    logger.info("[格式化响应] 未找到标准字段，查找其他字符串值")
                    for key, value in result.items():
                        if isinstance(value, str) and len(value) > 10:
                            logger.info(
                                f"[格式化响应] 找到字符串字段 {key}: {value[:100]}..."
                            )
                            return value

                # 其他情况：尝试提取主要信息
                if "message" in result:
                    return result["message"]
                elif "response" in result:
                    return result["response"]
                elif "content" in result:
                    return result["content"]
                else:
                    # 如果都没有，返回第一个字符串值
                    for key, value in result.items():
                        if isinstance(value, str) and len(value) > 10:
                            return value

            # 如果result不是字典，直接转换为字符串
            return str(result)

        except Exception as e:
            logger.error(f"格式化响应失败: {str(e)}")
            return str(result)

    def _build_metadata(self, intent: str, result: Any, user_id: str) -> Dict[str, Any]:
        """
        构建元数据

        参数:
            intent: 智能体名称
            result: 智能体返回结果
            user_id: 用户ID

        返回:
            Dict[str, Any]: 元数据
        """
        try:
            metadata = {
                "intent": intent,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            }

            # 如果result是字典，提取有用的元数据
            if isinstance(result, dict):
                # 提取阶段信息
                if "phase" in result:
                    metadata["phase"] = result["phase"]

                # 提取完整性分析（用于内部处理）
                if "completeness_analysis" in result:
                    metadata["completeness_analysis"] = result["completeness_analysis"]

                # 提取其他有用的元数据
                for key in ["round", "max_rounds", "encouragement", "needs_more_info"]:
                    if key in result:
                        metadata[key] = result[key]

            return metadata

        except Exception as e:
            logger.error(f"构建元数据失败: {str(e)}")
            return {
                "intent": intent,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            }

    async def _store_chat_message(
        self,
        user_id: str,
        role: str,
        content: str,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        存储聊天消息（支持MySQL和SQLite）

        参数:
            user_id: 用户ID
            role: 消息角色
            content: 消息内容
            user_info: 可选的用户信息（用于自动创建用户）

        返回:
            bool: 存储结果
        """
        try:
            db = get_database()
            if not db or not db.db_manager:
                logger.error("数据库连接失败")
                return False

            # 检查是否是MySQL数据库管理器（支持异步方法）
            if hasattr(db.db_manager, "store_chat_message"):
                # MySQL: 先确保用户存在
                if hasattr(db.db_manager, "get_user"):
                    existing_user = await db.db_manager.get_user(user_id)
                    if not existing_user:
                        # 用户不存在，尝试创建用户
                        logger.info(
                            f"[存储聊天消息] 用户 {user_id} 不存在，尝试创建用户记录"
                        )
                        if user_info:
                            username = user_info.get(
                                "username", user_info.get("name", user_id)
                            )
                            email = user_info.get("email", "")
                            # 对于OIDC用户，使用占位符密码哈希
                            password_hash = user_info.get(
                                "password_hash", "oidc_user_no_password"
                            )
                        else:
                            # 如果没有user_info，使用默认值
                            username = user_id
                            email = ""
                            password_hash = "oidc_user_no_password"

                        # 创建用户
                        if hasattr(db.db_manager, "create_user"):
                            success = await db.db_manager.create_user(
                                user_id=user_id,
                                username=username,
                                email=email,
                                password_hash=password_hash,
                                role="patient",
                            )
                            if success:
                                logger.info(f"[存储聊天消息] 用户 {user_id} 创建成功")
                            else:
                                logger.warning(
                                    f"[存储聊天消息] 用户 {user_id} 创建失败，但继续尝试存储消息"
                                )
                        else:
                            logger.warning(
                                "[存储聊天消息] 数据库管理器不支持创建用户，跳过用户创建"
                            )

                # 存储聊天消息
                return await db.db_manager.store_chat_message(user_id, role, content)
            else:
                # SQLite: 使用同步方法
                import sqlite3

                conn = sqlite3.connect("data/chat_history.db")
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO history (user_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                """,
                    (user_id, role, content, datetime.now()),
                )
                conn.commit()
                conn.close()
                return True

        except Exception as e:
            logger.error(f"存储聊天消息失败: {str(e)}")
            return False
