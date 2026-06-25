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
协议选择器
==========

封装协议选择逻辑，支持协议优先级配置和协议降级策略。

作者: QSIR
版本: 1.0
"""

import logging
from enum import Enum
from typing import Protocol, Optional, Dict, Any, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """协议类型"""
    ENTRY_AGENT = "entry_agent"  # 标准A2A SDK EntryAgent
    HTTP = "http"                # HTTP协议


class ProtocolHandler(ABC):
    """协议处理器接口"""
    
    @abstractmethod
    async def call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用协议"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查协议是否可用"""
        pass
    
    @abstractmethod
    def get_protocol_type(self) -> ProtocolType:
        """获取协议类型"""
        pass


class EntryAgentHandler(ProtocolHandler):
    """EntryAgent协议处理器"""
    
    def __init__(self, adapter):
        self.adapter = adapter
        self._available = adapter is not None
    
    async def call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用EntryAgent协议"""
        if not self.is_available():
            raise RuntimeError("EntryAgent适配器不可用")
        return await self.adapter.invoke(request_data)
    
    def is_available(self) -> bool:
        """检查EntryAgent是否可用"""
        return self._available and self.adapter is not None
    
    def get_protocol_type(self) -> ProtocolType:
        """获取协议类型"""
        return ProtocolType.ENTRY_AGENT


class HTTPHandler(ProtocolHandler):
    """HTTP协议处理器"""
    
    def __init__(self, session, base_url: str, api_key: str = "", timeout: int = 30):
        self.session = session
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self._available = bool(base_url)
    
    async def call(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用HTTP协议"""
        if not self.is_available():
            raise RuntimeError("HTTP协议不可用：未配置base_url")
        
        import aiohttp
        
        url = f"{self.base_url}/api/v1/data-proxy/request"
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with self.session.post(url, json=request_data, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise RuntimeError(f"HTTP请求失败: {response.status} - {error_text}")
    
    def is_available(self) -> bool:
        """检查HTTP协议是否可用"""
        return self._available
    
    def get_protocol_type(self) -> ProtocolType:
        """获取协议类型"""
        return ProtocolType.HTTP


class ProtocolSelector:
    """协议选择器"""
    
    def __init__(self, handlers: Dict[ProtocolType, ProtocolHandler]):
        """
        初始化协议选择器
        
        参数:
            handlers: 协议处理器字典
        """
        self.handlers = handlers
        # 协议优先级：EntryAgent > HTTP
        self.priority = [
            ProtocolType.ENTRY_AGENT,
            ProtocolType.HTTP
        ]
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def select_and_call(
        self, 
        request_data: Dict[str, Any],
        fallback: bool = True
    ) -> Dict[str, Any]:
        """
        选择协议并调用
        
        参数:
            request_data: 请求数据
            fallback: 是否允许降级到下一个协议
            
        返回:
            Dict[str, Any]: 响应数据
            
        异常:
            RuntimeError: 所有协议都不可用
        """
        last_error = None
        
        for protocol_type in self.priority:
            handler = self.handlers.get(protocol_type)
            if handler and handler.is_available():
                try:
                    self.logger.info(f"[ProtocolSelector] 使用协议: {protocol_type.value}")
                    return await handler.call(request_data)
                except Exception as e:
                    last_error = e
                    self.logger.warning(f"[ProtocolSelector] 协议 {protocol_type.value} 调用失败: {str(e)}")
                    if not fallback:
                        raise
                    continue
        
        # 所有协议都失败
        error_msg = "所有协议都不可用或调用失败"
        if last_error:
            error_msg += f"，最后错误: {str(last_error)}"
        raise RuntimeError(error_msg)
    
    def get_available_protocols(self) -> List[ProtocolType]:
        """获取可用的协议列表"""
        available = []
        for protocol_type in self.priority:
            handler = self.handlers.get(protocol_type)
            if handler and handler.is_available():
                available.append(protocol_type)
        return available
    
    def get_protocol_status(self) -> Dict[str, bool]:
        """获取协议状态"""
        status = {}
        for protocol_type in ProtocolType:
            handler = self.handlers.get(protocol_type)
            status[protocol_type.value] = handler.is_available() if handler else False
        return status

