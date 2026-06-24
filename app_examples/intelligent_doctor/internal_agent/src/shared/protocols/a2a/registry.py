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
A2A协议智能体注册客户端
======================

负责与智能体注册中心交互，实现智能体的注册和发现。

作者: QSIR
版本: 1.0
"""

import logging
import aiohttp
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from .message import AgentInfo

logger = logging.getLogger(__name__)


class A2ARegistryClient:
    """A2A智能体注册客户端"""
    
    def __init__(
        self,
        registry_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化注册客户端
        
        参数:
            registry_url: 注册中心URL
            api_key: API密钥
            timeout: 超时时间（秒）
        """
        self.registry_url = registry_url or os.getenv("A2A_REGISTRY_URL", "")
        self.api_key = api_key or os.getenv("A2A_API_KEY", "")
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._agent_cache: Dict[str, AgentInfo] = {}
        self._cache_ttl = 300  # 缓存5分钟
        
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
    
    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        endpoint: str,
        capabilities: List[str],
        location: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        注册智能体
        
        参数:
            agent_id: 智能体ID
            agent_type: 智能体类型
            endpoint: 智能体端点URL
            capabilities: 能力列表
            location: 位置信息
            metadata: 元数据
            
        返回:
            bool: 是否注册成功
        """
        if not self.registry_url:
            logger.warning("[A2ARegistryClient] 未配置注册中心URL，跳过注册")
            return False
        
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        
        url = f"{self.registry_url}/a2a/v1/agents/register"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "endpoint": endpoint,
            "capabilities": capabilities,
            "location": location or "default",
            "metadata": metadata or {},
            "status": "active",
            "version": "1.0.0"
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    logger.info(f"[A2ARegistryClient] 智能体 {agent_id} 注册成功")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"[A2ARegistryClient] 智能体注册失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"[A2ARegistryClient] 智能体注册异常: {str(e)}")
            return False
    
    async def discover_agent(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[AgentInfo]:
        """
        发现智能体
        
        参数:
            agent_id: 智能体ID（可选）
            agent_type: 智能体类型（可选）
            location: 位置信息（可选）
            
        返回:
            AgentInfo: 智能体信息，如果未找到返回None
        """
        # 检查缓存
        cache_key = f"{agent_id or ''}_{agent_type or ''}_{location or ''}"
        if cache_key in self._agent_cache:
            return self._agent_cache[cache_key]
        
        if not self.registry_url:
            logger.warning("[A2ARegistryClient] 未配置注册中心URL，无法发现智能体")
            return None
        
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        
        # 构建查询参数
        params = {}
        if agent_id:
            params["agent_id"] = agent_id
        if agent_type:
            params["agent_type"] = agent_type
        if location:
            params["location"] = location
        
        url = f"{self.registry_url}/a2a/v1/agents/discover"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    agents = result.get("agents", [])
                    if agents:
                        agent_data = agents[0]
                        agent_info = AgentInfo.from_dict(agent_data)
                        # 更新缓存
                        self._agent_cache[cache_key] = agent_info
                        logger.info(f"[A2ARegistryClient] 发现智能体: {agent_info.agent_id}")
                        return agent_info
                    else:
                        logger.warning(f"[A2ARegistryClient] 未找到匹配的智能体")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"[A2ARegistryClient] 智能体发现失败: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"[A2ARegistryClient] 智能体发现异常: {str(e)}")
            return None
    
    def clear_cache(self):
        """清除缓存"""
        self._agent_cache.clear()
        logger.info("[A2ARegistryClient] 缓存已清除")

