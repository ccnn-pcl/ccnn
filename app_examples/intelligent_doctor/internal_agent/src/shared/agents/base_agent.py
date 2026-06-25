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
基础智能体类
============

提供所有智能体的基础功能和通用接口。

主要功能：
1. 对话记忆管理
2. 上下文处理
3. 错误处理
4. 日志记录
5. LLM调用接口

作者: QSIR
版本: 1.0
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

# 导入对话记忆管理
try:
    from src.shared.dialogue_memory import DialogueMemory
except ImportError:
    # 如果导入失败，创建基础实现
    class DialogueMemory:
        def __init__(self):
            self.memory = {}

        def add_turn(
            self, user_id: str, user_input: str, agent_name: str, agent_response: str
        ):
            if user_id not in self.memory:
                self.memory[user_id] = []
            self.memory[user_id].append(
                {
                    "timestamp": datetime.now(),
                    "user_input": user_input,
                    "agent_name": agent_name,
                    "agent_response": agent_response,
                }
            )

        def get_recent_turns(self, user_id: str, max_turns: int = 10):
            if user_id not in self.memory:
                return []
            return self.memory[user_id][-max_turns:]

        def get_user_turns(self, user_id: str):
            return self.memory.get(user_id, [])

        def clear_user_memory(self, user_id: str):
            if user_id in self.memory:
                del self.memory[user_id]

        def get_formatted_history(self, user_id: str, last_n_turns: int = 3) -> str:
            turns = self.get_recent_turns(user_id, last_n_turns)
            if not turns:
                return ""

            context_parts = []
            for turn in turns:
                context_parts.append(f"用户: {turn['user_input']}")
                context_parts.append(f"智能体: {turn['agent_response']}")

            return "\n".join(context_parts)

        def get_current_timestamp(self):
            return datetime.now()


@dataclass
class AgentConfig:
    """智能体配置"""

    model_config: Dict[str, Any]
    max_context_length: int = 4000
    enable_memory: bool = True
    enable_logging: bool = True


class BaseAgent(ABC):
    """
    基础智能体类

    所有智能体的基类，提供通用功能：
    1. 对话记忆管理
    2. 上下文处理
    3. 错误处理
    4. 日志记录
    """

    def __init__(self, model_config: Dict[str, Any]):
        """
        初始化基础智能体

        参数：
            model_config (Dict[str, Any]): 模型配置
        """
        self.model_config = model_config
        self.dialogue_memory = DialogueMemory()
        # 使用完整模块路径作为logger名称，确保日志配置生效
        module_path = self.__class__.__module__.replace("agents.", "shared.agents.")
        self.logger = logging.getLogger(f"{module_path}.{self.__class__.__name__}")
        self.agent_name = self.__class__.__name__  # 智能体名称

        # 初始化LLM调用器
        self._init_llm_caller()

        self.logger.info(f"[{self.agent_name}] 初始化完成")

    def _init_llm_caller(self):
        """初始化LLM调用器"""
        try:
            from src.shared.llm_caller import call_llm as original_call_llm

            # 包装call_llm以传递智能体名称
            async def wrapped_caller(prompt, config):
                return await original_call_llm(
                    prompt, config, agent_name=self.agent_name
                )

            self.caller = wrapped_caller
            self.logger.info(f"[{self.agent_name}] LLM调用器初始化完成")
        except ImportError as e:
            self.logger.error(f"[{self.agent_name}] LLM调用器初始化失败: {str(e)}")
            # 创建备用调用器
            self.caller = self._fallback_caller
            self.logger.warning(f"[{self.agent_name}] 使用备用LLM调用器")

    async def _fallback_caller(self, prompt: str, model_config: Dict[str, Any]) -> str:
        """备用LLM调用器"""
        self.logger.warning(
            f"[{self.agent_name}] 使用备用调用器，提示: {prompt[:100]}..."
        )
        # 简单的模拟响应
        return f"模拟AI响应: {prompt[:100]}..."

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        执行智能体任务

        子类必须实现此方法
        """
        pass

    def get_context_from_memory(self, user_id: str, max_turns: int = 10) -> str:
        """
        从对话记忆中获取上下文

        参数：
            user_id (str): 用户ID
            max_turns (int): 最大对话轮次

        返回：
            str: 对话上下文
        """
        try:
            return self.dialogue_memory.get_formatted_history(user_id, max_turns)
        except Exception as e:
            self.logger.error(
                f"[{self.__class__.__name__}] 获取对话上下文失败: {str(e)}"
            )
            return ""

    def add_turn_to_memory(
        self, user_id: str, user_input: str, agent_name: str, agent_response: str
    ):
        """
        添加对话轮次到记忆

        参数：
            user_id (str): 用户ID
            user_input (str): 用户输入
            agent_name (str): 智能体名称
            agent_response (str): 智能体响应
        """
        try:
            self.dialogue_memory.add_turn(
                user_id, user_input, agent_name, agent_response
            )
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 添加对话轮次失败: {str(e)}")

    def clear_memory(self, user_id: str):
        """
        清除用户对话记忆

        参数：
            user_id (str): 用户ID
        """
        try:
            self.dialogue_memory.clear_user_memory(user_id)
            self.logger.info(
                f"[{self.__class__.__name__}] 用户 {user_id} 对话记忆已清除"
            )
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 清除对话记忆失败: {str(e)}")

    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取对话记忆统计信息

        参数：
            user_id (str): 用户ID

        返回：
            Dict[str, Any]: 统计信息
        """
        try:
            turns = self.dialogue_memory.get_user_turns(user_id)
            return {
                "total_turns": len(turns),
                "last_turn_time": turns[-1].timestamp if turns else None,
                "memory_size": len(str(turns)),
            }
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 获取记忆统计失败: {str(e)}")
            return {"total_turns": 0, "last_turn_time": None, "memory_size": 0}

    async def safe_execute(self, *args, **kwargs) -> Any:
        """
        安全执行智能体任务，包含错误处理和详细日志

        参数：
            *args: 位置参数
            **kwargs: 关键字参数

        返回：
            Any: 执行结果
        """
        import traceback

        try:
            # 使用print确保输出到终端
            print("\n" + "[智能体执行]" * 50)
            print(f"[智能体执行] 智能体开始执行: {self.agent_name}")
            print(f"[智能体执行] 位置参数数量: {len(args)}")
            print("[智能体执行]" * 50 + "\n")

            # 记录输入参数
            self.logger.info("=" * 100)
            self.logger.info(f"[{self.agent_name}] ====== 智能体执行开始 ======")
            self.logger.info(f"[{self.agent_name}] 位置参数数量: {len(args)}")
            self.logger.info(f"[{self.agent_name}] 关键字参数: {kwargs.keys()}")

            # 记录参数详情
            for i, arg in enumerate(args):
                if isinstance(arg, str):
                    preview = arg[:200] + "..." if len(arg) > 200 else arg
                    self.logger.info(f"[{self.agent_name}] 参数[{i}]: {preview}")
                else:
                    self.logger.info(
                        f"[{self.agent_name}] 参数[{i}]: {type(arg).__name__}"
                    )

            for key, value in kwargs.items():
                if isinstance(value, str):
                    preview = value[:200] + "..." if len(value) > 200 else value
                    self.logger.info(f"[{self.agent_name}] {key}: {preview}")
                else:
                    self.logger.info(
                        f"[{self.agent_name}] {key}: {type(value).__name__}"
                    )

            self.logger.info("-" * 100)

            # 执行任务
            result = await self.execute(*args, **kwargs)

            # 使用print输出到终端
            print(f"\n[OK] 智能体执行完成: {self.agent_name}\n")

            # 记录输出结果
            self.logger.info(f"[{self.agent_name}] ====== 智能体执行完成 ======")

            if isinstance(result, str):
                preview = result[:500] + "..." if len(result) > 500 else result
                self.logger.info(f"[{self.agent_name}] 输出类型: 字符串")
                self.logger.info(f"[{self.agent_name}] 输出长度: {len(result)} 字符")
                self.logger.info(f"[{self.agent_name}] 输出内容: {preview}")
            elif isinstance(result, dict):
                self.logger.info(f"[{self.agent_name}] 输出类型: 字典")
                self.logger.info(f"[{self.agent_name}] 输出键: {result.keys()}")
                for key, value in result.items():
                    if isinstance(value, str):
                        preview = value[:200] + "..." if len(value) > 200 else value
                        self.logger.info(f"[{self.agent_name}] 输出[{key}]: {preview}")
                    else:
                        self.logger.info(
                            f"[{self.agent_name}] 输出[{key}]: {type(value).__name__}"
                        )
            else:
                self.logger.info(
                    f"[{self.agent_name}] 输出类型: {type(result).__name__}"
                )
                self.logger.info(
                    f"[{self.agent_name}] 输出内容: {str(result)[:500]}..."
                )

            self.logger.info("=" * 100)

            return result
        except Exception as e:
            # 详细的错误日志
            self.logger.error("=" * 100)
            self.logger.error(f"[{self.agent_name}] ====== 智能体执行错误 ======")
            self.logger.error(f"[{self.agent_name}] 错误类型: {type(e).__name__}")
            self.logger.error(f"[{self.agent_name}] 错误消息: {str(e)}")
            self.logger.error(
                f"[{self.agent_name}] 错误堆栈:\n{traceback.format_exc()}"
            )
            self.logger.error(
                f"[{self.agent_name}] 输入参数: args={args}, kwargs={kwargs}"
            )
            self.logger.error("=" * 100)
            return f"[ERROR] 智能体执行错误：{str(e)}"

    def validate_input(self, user_input: str) -> bool:
        """
        验证用户输入

        参数：
            user_input (str): 用户输入

        返回：
            bool: 输入是否有效
        """
        if not user_input or not user_input.strip():
            return False

        if len(user_input) > 10000:  # 限制输入长度
            return False

        return True

    def format_response(self, response: Any) -> str:
        """
        格式化智能体响应

        参数：
            response (Any): 原始响应

        返回：
            str: 格式化后的响应
        """
        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            if "diagnosis" in response:
                return f"诊断结果：\n{response['diagnosis']}"
            elif "summary" in response:
                return f"汇总报告：\n{response['summary']}"
            elif "triage" in response:
                return f"分诊建议：\n{response['triage']}"
            else:
                return str(response)

        return str(response)

    def get_agent_status(self) -> Dict[str, Any]:
        """
        获取智能体状态

        返回：
            Dict[str, Any]: 智能体状态信息
        """
        return {
            "agent_name": self.__class__.__name__,
            "status": "active",
            "memory_enabled": hasattr(self, "dialogue_memory"),
            "llm_available": hasattr(self, "caller"),
            "timestamp": datetime.now().isoformat(),
        }

    def handle_error(self, error_message: str) -> str:
        """
        处理错误信息

        参数：
            error_message (str): 错误信息

        返回：
            str: 格式化的错误信息
        """
        self.logger.error(f"[{self.__class__.__name__}] 错误：{error_message}")
        return f"[ERROR] 出现错误：{error_message}"
