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
智能体相关数据模型
==================

定义智能体相关的数据结构。

作者: QSIR
版本: 1.0
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class AgentType(Enum):
    """智能体类型枚举"""
    COORDINATOR = "coordinator"
    MEDICAL = "medical"
    IMAGE = "image"
    LLM = "llm"
    UTILITY = "utility"


class AgentStatus(Enum):
    """智能体状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class AgentResponse:
    """
    智能体响应数据类
    
    用于存储智能体的响应信息。
    """
    response_id: str
    agent_id: str
    agent_name: str
    user_id: str
    task_id: str
    response_type: str              # 响应类型 (success, error, warning)
    content: str                    # 响应内容
    metadata: Dict[str, Any]        # 元数据
    confidence_score: float         # 置信度分数 (0-1)
    processing_time: float          # 处理时间 (秒)
    created_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'response_id': self.response_id,
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'user_id': self.user_id,
            'task_id': self.task_id,
            'response_type': self.response_type,
            'content': self.content,
            'metadata': self.metadata,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class AgentTask:
    """
    智能体任务数据类
    
    用于存储智能体任务的信息。
    """
    task_id: str
    agent_id: str
    user_id: str
    task_type: str
    input_data: Dict[str, Any]
    status: TaskStatus
    priority: int                    # 优先级 (1-5)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'user_id': self.user_id,
            'task_type': self.task_type,
            'input_data': self.input_data,
            'status': self.status.value,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'result': self.result
        }


@dataclass
class AgentCapability:
    """
    智能体能力数据类
    
    用于存储智能体的能力信息。
    """
    capability_id: str
    agent_id: str
    name: str
    description: str
    input_types: List[str]          # 支持的输入类型
    output_types: List[str]         # 支持的输出类型
    parameters: Dict[str, Any]      # 能力参数
    is_available: bool              # 是否可用
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'capability_id': self.capability_id,
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'input_types': self.input_types,
            'output_types': self.output_types,
            'parameters': self.parameters,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class AgentMetrics:
    """
    智能体指标数据类
    
    用于存储智能体的性能指标。
    """
    agent_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_processing_time: float
    success_rate: float
    last_active: datetime
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'agent_id': self.agent_id,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'average_processing_time': self.average_processing_time,
            'success_rate': self.success_rate,
            'last_active': self.last_active.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
