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
A2A协议客户端
=============

实现A2A协议的客户端，用于发送请求和处理响应。

作者: QSIR
版本: 1.0
"""

import logging
import aiohttp
import os
from typing import Dict, Any, Optional
from datetime import datetime

from .message import A2ARequest, A2AResponse, AgentInfo, TaskInfo, A2AError, A2AErrorCode
from .registry import A2ARegistryClient

logger = logging.getLogger(__name__)


class A2AClient:
    """A2A协议客户端"""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        registry_client: Optional[A2ARegistryClient] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化A2A客户端
        
        参数:
            agent_id: 当前智能体ID
            agent_type: 当前智能体类型
            registry_client: 注册客户端（可选）
            api_key: API密钥
            timeout: 超时时间（秒）
        """
        self.agent_id = agent_id or os.getenv("AGENT_ID", "medical_app_coordinator")
        self.agent_type = agent_type or os.getenv("AGENT_TYPE", "coordinator")
        self.registry_client = registry_client
        self.api_key = api_key or os.getenv("A2A_API_KEY", "")
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def invoke_agent(
        self,
        target_agent_id: str,
        task_type: str,
        input_data: Dict[str, Any],
        target_agent_type: Optional[str] = None,
        target_endpoint: Optional[str] = None,
        priority: str = "medium",
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> A2AResponse:
        """
        调用远程智能体
        
        参数:
            target_agent_id: 目标智能体ID
            task_type: 任务类型
            input_data: 输入数据
            target_agent_type: 目标智能体类型（可选）
            target_endpoint: 目标智能体端点（可选，如果不提供则通过注册中心发现）
            priority: 优先级
            timeout: 超时时间（秒）
            metadata: 元数据
            
        返回:
            A2AResponse: 响应消息
        """
        # 1. 发现目标智能体（如果未提供端点）
        if not target_endpoint:
            if self.registry_client:
                agent_info = await self.registry_client.discover_agent(
                    agent_id=target_agent_id,
                    agent_type=target_agent_type
                )
                if agent_info and agent_info.endpoint:
                    target_endpoint = agent_info.endpoint
                else:
                    return self._create_error_response(
                        A2AErrorCode.AGENT_NOT_FOUND,
                        f"智能体 {target_agent_id} 未找到"
                    )
            else:
                return self._create_error_response(
                    A2AErrorCode.AGENT_NOT_FOUND,
                    "未配置注册中心，无法发现智能体"
                )
        
        # 2. 构建请求消息
        request = self._build_request(
            target_agent_id=target_agent_id,
            target_agent_type=target_agent_type or "unknown",
            target_endpoint=target_endpoint,
            task_type=task_type,
            input_data=input_data,
            priority=priority,
            timeout=timeout or self.timeout,
            metadata=metadata
        )
        
        # 3. 发送请求
        return await self._send_request(request, target_endpoint)
    
    def _build_request(
        self,
        target_agent_id: str,
        target_agent_type: str,
        target_endpoint: str,
        task_type: str,
        input_data: Dict[str, Any],
        priority: str,
        timeout: int,
        metadata: Optional[Dict[str, Any]]
    ) -> A2ARequest:
        """构建A2A请求消息"""
        source_agent = AgentInfo(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            capabilities=["intent_recognition", "diagnosis"],
            location="default"
        )
        
        target_agent = AgentInfo(
            agent_id=target_agent_id,
            agent_type=target_agent_type,
            endpoint=target_endpoint
        )
        
        task = TaskInfo(
            task_id=f"task_{datetime.now().timestamp()}",
            task_type=task_type,
            priority=priority,
            timeout=timeout,
            input_data=input_data
        )
        
        return A2ARequest(
            source_agent=source_agent,
            target_agent=target_agent,
            task=task,
            metadata=metadata or {}
        )
    
    async def _send_request(self, request: A2ARequest, endpoint: str) -> A2AResponse:
        """发送A2A请求"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        
        # 构建URL（如果endpoint不包含完整路径，添加默认路径）
        if "/a2a/v1/execute" not in endpoint:
            url = f"{endpoint.rstrip('/')}/a2a/v1/execute"
        else:
            url = endpoint
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            logger.info(f"[A2AClient] 发送A2A请求到 {url}")
            logger.debug(f"[A2AClient] 请求消息: {request.to_dict()}")
            
            # 打印A2A协议请求信息
            request_dict = request.to_dict()
            print(f"\n[A2A协议请求] ========================================")
            print(f"  目标端点: {url}")
            print(f"  消息ID: {request_dict.get('message_id', 'N/A')}")
            print(f"  源智能体: {request_dict.get('source_agent', {}).get('agent_id', 'N/A')} ({request_dict.get('source_agent', {}).get('agent_type', 'N/A')})")
            print(f"  目标智能体: {request_dict.get('target_agent', {}).get('agent_id', 'N/A')} ({request_dict.get('target_agent', {}).get('agent_type', 'N/A')})")
            print(f"  任务类型: {request_dict.get('task', {}).get('task_type', 'N/A')}")
            print(f"  任务ID: {request_dict.get('task', {}).get('task_id', 'N/A')}")
            print(f"  优先级: {request_dict.get('task', {}).get('priority', 'N/A')}")
            input_data = request_dict.get('task', {}).get('input_data', {})
            print(f"  输入数据:")
            print(f"    - 意图类型: {input_data.get('intent_type', 'N/A')}")
            print(f"    - 专科: {input_data.get('specialty', 'N/A')}")
            print(f"    - 用户ID: {input_data.get('user_id', 'N/A')}")
            print(f"    - 症状: {input_data.get('symptoms', [])}")
            print(f"    - 请求ID: {input_data.get('context', {}).get('request_id', request_dict.get('metadata', {}).get('request_id', 'N/A'))}")
            print(f"  时间戳: {request_dict.get('timestamp', 'N/A')}")
            print(f"[A2A协议请求] ========================================\n")
            
            async with self.session.post(url, json=request.to_dict(), headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    a2a_response = A2AResponse.from_dict(result)
                    logger.info(f"[A2AClient] A2A请求成功")
                    
                    # 打印A2A协议响应信息
                    print(f"\n[A2A协议响应] ========================================")
                    print(f"  状态码: {response.status}")
                    print(f"  消息ID: {result.get('message_id', 'N/A')}")
                    print(f"  源智能体: {result.get('source_agent', {}).get('agent_id', 'N/A')} ({result.get('source_agent', {}).get('agent_type', 'N/A')})")
                    print(f"  目标智能体: {result.get('target_agent', {}).get('agent_id', 'N/A')} ({result.get('target_agent', {}).get('agent_type', 'N/A')})")
                    if result.get('task') and result['task'].get('result'):
                        task_result = result['task']['result']
                        print(f"  任务结果:")
                        print(f"    - 成功: {task_result.get('success', False)}")
                        print(f"    - 消息: {task_result.get('message', 'N/A')}")
                        data_addresses = task_result.get('data_addresses', [])
                        print(f"    - 数据地址数量: {len(data_addresses)}")
                        if data_addresses:
                            print(f"    - 数据地址列表:")
                            for i, addr in enumerate(data_addresses[:3], 1):  # 只打印前3个
                                print(f"      {i}. 类型: {addr.get('data_type', 'N/A')}, 地域: {addr.get('location', 'N/A')}, 医院: {addr.get('hospital', 'N/A')}")
                            if len(data_addresses) > 3:
                                print(f"      ... 还有 {len(data_addresses) - 3} 个数据地址")
                    if result.get('error'):
                        error = result['error']
                        print(f"  错误信息:")
                        print(f"    - 错误码: {error.get('error_code', 'N/A')}")
                        print(f"    - 错误类型: {error.get('error_type', 'N/A')}")
                        print(f"    - 错误消息: {error.get('message', 'N/A')}")
                    print(f"  时间戳: {result.get('timestamp', 'N/A')}")
                    print(f"[A2A协议响应] ========================================\n")
                    
                    return a2a_response
                else:
                    error_text = await response.text()
                    logger.error(f"[A2AClient] A2A请求失败: {response.status} - {error_text}")
                    
                    # 打印A2A协议错误信息
                    print(f"\n[A2A协议错误] ========================================")
                    print(f"  状态码: {response.status}")
                    print(f"  错误信息: {error_text[:500]}..." if len(error_text) > 500 else f"  错误信息: {error_text}")
                    print(f"[A2A协议错误] ========================================\n")
                    
                    return self._create_error_response(
                        A2AErrorCode.INTERNAL_ERROR,
                        f"HTTP错误: {response.status}",
                        {"error_text": error_text}
                    )
        except aiohttp.ClientError as e:
            logger.error(f"[A2AClient] A2A请求网络错误: {str(e)}")
            return self._create_error_response(
                A2AErrorCode.AGENT_UNAVAILABLE,
                f"网络错误: {str(e)}"
            )
        except Exception as e:
            logger.error(f"[A2AClient] A2A请求异常: {str(e)}")
            return self._create_error_response(
                A2AErrorCode.INTERNAL_ERROR,
                f"内部错误: {str(e)}"
            )
    
    def _create_error_response(
        self,
        error_code: A2AErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> A2AResponse:
        """创建错误响应"""
        error = A2AError(
            error_code=error_code.value,
            error_type=error_code.name.lower(),
            message=message,
            details=details or {}
        )
        
        return A2AResponse(
            source_agent=AgentInfo(
                agent_id="system",
                agent_type="system"
            ),
            target_agent=AgentInfo(
                agent_id=self.agent_id,
                agent_type=self.agent_type
            ),
            error=error
        )

