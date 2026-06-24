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
A2A协议消息格式定义
==================

定义A2A协议的消息结构、请求、响应和错误格式。

作者: QSIR
版本: 1.0
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid


class A2AErrorCode(Enum):
    """A2A错误代码"""
    AGENT_NOT_FOUND = "A2A_001"
    AGENT_UNAVAILABLE = "A2A_002"
    TASK_TIMEOUT = "A2A_003"
    INVALID_MESSAGE = "A2A_004"
    CAPABILITY_MISMATCH = "A2A_005"
    INTERNAL_ERROR = "A2A_006"


@dataclass
class AgentInfo:
    """智能体信息"""
    agent_id: str
    agent_type: str
    capabilities: List[str] = field(default_factory=list)
    location: Optional[str] = None
    endpoint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "location": self.location,
            "endpoint": self.endpoint
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentInfo":
        """从字典创建"""
        return cls(
            agent_id=data.get("agent_id", ""),
            agent_type=data.get("agent_type", ""),
            capabilities=data.get("capabilities", []),
            location=data.get("location"),
            endpoint=data.get("endpoint")
        )


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    task_type: str
    priority: str = "medium"
    timeout: int = 30
    input_data: Dict[str, Any] = field(default_factory=dict)
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    confidence_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "priority": self.priority,
            "timeout": self.timeout,
            "input_data": self.input_data,
            "status": self.status,
            "result": self.result,
            "processing_time": self.processing_time,
            "confidence_score": self.confidence_score
        }


@dataclass
class A2AError:
    """A2A错误信息"""
    error_code: str
    error_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_code": self.error_code,
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details
        }


@dataclass
class A2AMessage:
    """A2A协议基础消息"""
    a2a_version: str = "1.0"
    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:10]}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source_agent: Optional[AgentInfo] = None
    target_agent: Optional[AgentInfo] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "a2a_version": self.a2a_version,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
        if self.source_agent:
            result["source_agent"] = self.source_agent.to_dict()
        if self.target_agent:
            result["target_agent"] = self.target_agent.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """从字典创建"""
        source_agent = None
        target_agent = None
        
        if "source_agent" in data:
            source_agent = AgentInfo.from_dict(data["source_agent"])
        if "target_agent" in data:
            target_agent = AgentInfo.from_dict(data["target_agent"])
        
        return cls(
            a2a_version=data.get("a2a_version", "1.0"),
            message_id=data.get("message_id", f"msg_{uuid.uuid4().hex[:10]}"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            source_agent=source_agent,
            target_agent=target_agent,
            metadata=data.get("metadata", {})
        )


@dataclass
class A2ARequest(A2AMessage):
    """A2A请求消息"""
    task: TaskInfo = field(default_factory=lambda: TaskInfo(
        task_id=f"task_{uuid.uuid4().hex[:10]}",
        task_type="",
        input_data={}
    ))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        result["task"] = self.task.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2ARequest":
        """从字典创建"""
        message = super().from_dict(data)
        task_data = data.get("task", {})
        task = TaskInfo(
            task_id=task_data.get("task_id", f"task_{uuid.uuid4().hex[:10]}"),
            task_type=task_data.get("task_type", ""),
            priority=task_data.get("priority", "medium"),
            timeout=task_data.get("timeout", 30),
            input_data=task_data.get("input_data", {})
        )
        
        request = cls(
            a2a_version=message.a2a_version,
            message_id=message.message_id,
            timestamp=message.timestamp,
            source_agent=message.source_agent,
            target_agent=message.target_agent,
            metadata=message.metadata,
            task=task
        )
        return request


@dataclass
class A2AResponse(A2AMessage):
    """A2A响应消息"""
    response_to: Optional[str] = None
    task: Optional[TaskInfo] = None
    error: Optional[A2AError] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        if self.response_to:
            result["response_to"] = self.response_to
        if self.task:
            result["task"] = self.task.to_dict()
        if self.error:
            result["error"] = self.error.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AResponse":
        """从字典创建"""
        message = super().from_dict(data)
        
        task = None
        if "task" in data:
            task_data = data["task"]
            task = TaskInfo(
                task_id=task_data.get("task_id", ""),
                task_type=task_data.get("task_type", ""),
                status=task_data.get("status"),
                result=task_data.get("result"),
                processing_time=task_data.get("processing_time"),
                confidence_score=task_data.get("confidence_score")
            )
        
        error = None
        if "error" in data:
            error_data = data["error"]
            error = A2AError(
                error_code=error_data.get("error_code", ""),
                error_type=error_data.get("error_type", ""),
                message=error_data.get("message", ""),
                details=error_data.get("details", {})
            )
        
        return cls(
            a2a_version=message.a2a_version,
            message_id=message.message_id,
            timestamp=message.timestamp,
            source_agent=message.source_agent,
            target_agent=message.target_agent,
            metadata=message.metadata,
            response_to=data.get("response_to"),
            task=task,
            error=error
        )

