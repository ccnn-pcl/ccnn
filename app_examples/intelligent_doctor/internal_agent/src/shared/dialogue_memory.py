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
对话记忆管理模块 - 用户对话历史记录管理
====================================

这个模块提供了对话记忆管理功能，用于存储和管理用户的对话历史记录。

主要功能：
1. 对话轮次记录
   - 记录每次对话的完整信息
   - 包含时间戳、用户输入、智能体响应
   - 支持多用户对话隔离

2. 对话历史管理
   - 按用户ID组织对话历史
   - 支持获取最近N轮对话
   - 提供对话历史查询接口

3. 数据结构设计
   - 使用数据类定义对话轮次结构
   - 类型安全的对话历史管理
   - 清晰的数据组织方式

设计模式：
- 数据类模式：使用@dataclass装饰器
- 简单工厂模式：对话记忆管理器

作者: QSIR
版本: 1.0
"""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class DialogueTurn:
    """
    对话轮次数据类
    
    用于存储单次对话的完整信息，包括时间戳、用户输入、
    智能体名称和智能体响应。
    
    设计模式：数据类模式，使用@dataclass装饰器
    """
    timestamp: datetime      # 对话时间戳
    user_input: str         # 用户输入内容
    agent_name: str         # 智能体名称
    agent_response: str     # 智能体响应内容

class DialogueMemory:
    """
    对话记忆管理器
    
    功能：
    - 存储和管理用户的对话历史
    - 按用户ID组织对话数据
    - 提供对话历史查询接口
    - 支持获取最近N轮对话
    
    数据结构：
        conversations: Dict[str, List[DialogueTurn]]
        - 键：用户ID
        - 值：该用户的对话轮次列表
    """
    
    def __init__(self):
        """
        初始化对话记忆管理器
        
        功能：
        - 初始化对话存储字典
        - 为每个用户创建独立的对话历史列表
        """
        self.conversations: Dict[str, List[DialogueTurn]] = {}
    
    def add_turn(self, user_id: str, user_input: str, agent_name: str, agent_response: str):
        """
        添加对话轮次
        
        功能：
        - 创建新的对话轮次记录
        - 将轮次添加到指定用户的对话历史
        - 自动创建用户对话历史（如果不存在）
        
        参数：
            user_id (str): 用户ID
            user_input (str): 用户输入内容
            agent_name (str): 智能体名称
            agent_response (str): 智能体响应内容
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        turn = DialogueTurn(
            timestamp=datetime.now(),
            user_input=user_input,
            agent_name=agent_name,
            agent_response=agent_response
        )
        self.conversations[user_id].append(turn)
    
    def get_conversation_history(self, user_id: str, last_n_turns: int = None) -> List[DialogueTurn]:
        """
        获取对话历史
        
        功能：
        - 获取指定用户的对话历史
        - 支持获取最近N轮对话
        - 如果用户不存在，返回空列表
        
        参数：
            user_id (str): 用户ID
            last_n_turns (int, optional): 获取最近N轮对话，None表示获取全部
            
        返回：
            List[DialogueTurn]: 对话历史列表，按时间顺序排列
        """
        if user_id not in self.conversations:
            return []
        
        history = self.conversations[user_id]
        if last_n_turns:
            return history[-last_n_turns:]
        return history
    
    def get_formatted_history(self, user_id: str, last_n_turns: int = None) -> str:
        """
        获取格式化的对话历史
        
        功能：
        - 获取指定用户的对话历史
        - 将对话历史格式化为字符串
        - 支持获取最近N轮对话
        
        参数：
            user_id (str): 用户ID
            last_n_turns (int, optional): 获取最近N轮对话，None表示获取全部
            
        返回：
            str: 格式化的对话历史字符串
        """
        history = self.get_conversation_history(user_id, last_n_turns)
        
        if not history:
            return ""
        
        formatted_lines = []
        for turn in history:
            formatted_lines.append(f"用户: {turn.user_input}")
            formatted_lines.append(f"{turn.agent_name}: {turn.agent_response}")
            formatted_lines.append("")  # 空行分隔
        
        return "\n".join(formatted_lines)
    
    def clear_user_memory(self, user_id: str):
        """
        清除指定用户的对话记忆
        
        功能：
        - 清除指定用户的所有对话历史
        - 用于用户登出或会话结束时清理内存
        
        参数：
            user_id (str): 用户ID
        """
        if user_id in self.conversations:
            del self.conversations[user_id]