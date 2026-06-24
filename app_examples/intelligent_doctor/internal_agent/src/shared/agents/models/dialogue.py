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
对话相关数据模型
================

定义对话相关的数据结构。

作者: QSIR
版本: 1.0
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class DialogueTurn:
    """
    对话轮次数据类
    
    用于存储单次对话的完整信息，包括时间戳、用户输入、
    智能体名称和智能体响应。
    """
    timestamp: datetime      # 对话时间戳
    user_input: str         # 用户输入内容
    agent_name: str         # 智能体名称
    agent_response: str     # 智能体响应内容
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'user_input': self.user_input,
            'agent_name': self.agent_name,
            'agent_response': self.agent_response
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DialogueTurn':
        """从字典创建实例"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            user_input=data['user_input'],
            agent_name=data['agent_name'],
            agent_response=data['agent_response']
        )


@dataclass
class ConversationContext:
    """
    对话上下文数据类
    
    用于存储对话的上下文信息。
    """
    user_id: str
    session_id: str
    current_topic: Optional[str] = None
    conversation_history: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DialogueMemory:
    """
    对话记忆数据类
    
    用于存储和管理对话记忆。
    """
    user_id: str
    turns: list = None
    max_turns: int = 100
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.turns is None:
            self.turns = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def add_turn(self, turn: DialogueTurn):
        """添加对话轮次"""
        self.turns.append(turn)
        self.updated_at = datetime.now()
        
        # 保持最大轮次限制
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
    
    def get_recent_turns(self, n: int = 10) -> list:
        """获取最近的N轮对话"""
        return self.turns[-n:] if self.turns else []
    
    def clear(self):
        """清空对话记忆"""
        self.turns = []
        self.updated_at = datetime.now()
