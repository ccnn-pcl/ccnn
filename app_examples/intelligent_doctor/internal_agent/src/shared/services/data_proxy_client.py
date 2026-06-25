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
数据代理客户端
============

实现与第三方数据代理应用通信的客户端。

主要功能：
1. 发送医疗数据请求到第三方数据代理应用
2. 处理响应和错误
3. 实现请求重试和缓存机制
4. 健康检查和连接监控

作者: QSIR
版本: 1.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp


class DataProxyClient:
    """
    数据代理客户端

    负责与第三方数据代理应用进行通信，获取医疗数据。
    """

    def __init__(self, proxy_config: Dict[str, Any]):
        """
        初始化数据代理客户端

        参数:
            proxy_config (Dict[str, Any]): 数据代理配置
                - proxy_url: 代理应用URL
                - api_key: API密钥
                - timeout: 请求超时时间（秒）
                - retry_count: 重试次数
                - cache_enabled: 是否启用缓存
                - cache_ttl: 缓存存活时间（秒）
        """
        self.proxy_url = proxy_config.get("proxy_url", "http://localhost:9000")
        self.api_key = proxy_config.get("api_key", "")
        self.timeout = proxy_config.get("timeout", 30)
        self.retry_count = proxy_config.get("retry_count", 3)
        self.cache_enabled = proxy_config.get("cache_enabled", True)
        self.cache_ttl = proxy_config.get("cache_ttl", 3600)

        # 数据缓存
        self.cache: Dict[str, Dict[str, Any]] = {}

        # 日志记录
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info(
            f"[{self.__class__.__name__}] 初始化完成 - URL: {self.proxy_url}"
        )

    async def request_medical_data(
        self,
        intent_type: str,
        specialty: str,
        user_id: str,
        context: Dict[str, Any],
        priority: str = "medium",
    ) -> Dict[str, Any]:
        """
        请求医疗数据

        参数:
            intent_type (str): 意图类型
            specialty (str): 专科类型
            user_id (str): 用户ID
            context (Dict[str, Any]): 上下文信息
            priority (str): 请求优先级

        返回:
            Dict[str, Any]: 医疗数据
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(intent_type, specialty, user_id)

            # 检查缓存
            if self.cache_enabled:
                cached_data = self._get_from_cache(cache_key)
                if cached_data:
                    self.logger.info(f"[{self.__class__.__name__}] 从缓存获取数据")
                    return cached_data

            # 构建请求数据
            request_data = {
                "intent_type": intent_type,
                "specialty": specialty,
                "user_id": user_id,
                "context": context,
                "data_types": self._determine_data_types(specialty),
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
            }

            # 发送请求
            response = await self._send_request_with_retry(
                "/api/medical-data", request_data
            )

            # 缓存响应
            if self.cache_enabled and response.get("success"):
                self._save_to_cache(cache_key, response)

            return response

        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 请求医疗数据失败: {str(e)}")
            return {"success": False, "message": f"请求失败: {str(e)}", "data": {}}

    async def _send_request_with_retry(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送请求（带重试机制）"""
        last_exception = None

        for attempt in range(self.retry_count):
            try:
                self.logger.info(
                    f"[{self.__class__.__name__}] 发送请求 (尝试 {attempt + 1}/{self.retry_count})"
                )
                response = await self._send_request(endpoint, data)
                return response

            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"[{self.__class__.__name__}] 请求失败 (尝试 {attempt + 1}/{self.retry_count}): {str(e)}"
                )

                # 如果不是最后一次尝试，等待后重试
                if attempt < self.retry_count - 1:
                    wait_time = (attempt + 1) * 2  # 指数退避
                    await asyncio.sleep(wait_time)

        # 所有重试都失败
        raise Exception(
            f"请求失败，已重试 {self.retry_count} 次: {str(last_exception)}"
        )

    async def _send_request(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送HTTP请求到数据代理应用"""
        url = f"{self.proxy_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"[{self.__class__.__name__}] 请求成功")
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"请求失败: {response.status} - {error_text}")

    async def health_check(self) -> bool:
        """
        健康检查

        返回:
            bool: 服务是否健康
        """
        try:
            url = f"{self.proxy_url}/api/health"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        self.logger.info(f"[{self.__class__.__name__}] 健康检查成功")
                        return True
                    return False
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 健康检查失败: {str(e)}")
            return False

    async def get_specialties(self) -> List[Dict[str, Any]]:
        """
        获取支持的专科列表

        返回:
            List[Dict[str, Any]]: 专科列表
        """
        try:
            url = f"{self.proxy_url}/api/specialties"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("specialties", [])
                    return []
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 获取专科列表失败: {str(e)}")
            return []

    async def get_data_types(self) -> List[Dict[str, Any]]:
        """
        获取支持的数据类型

        返回:
            List[Dict[str, Any]]: 数据类型列表
        """
        try:
            url = f"{self.proxy_url}/api/data-types"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("data_types", [])
                    return []
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 获取数据类型失败: {str(e)}")
            return []

    def _determine_data_types(self, specialty: str) -> List[str]:
        """根据专科确定需要的数据类型"""
        data_type_mapping = {
            "内科": ["病史数据", "用药记录", "体检报告", "实验室检查"],
            "外科": ["病史数据", "影像数据", "手术记录", "体检报告"],
            "心血管": ["病史数据", "心电图", "心脏超声", "用药记录"],
            "神经科": ["神经检查", "影像数据", "病史数据", "认知评估"],
            "骨科": ["病史数据", "影像数据", "体检报告", "手术记录"],
        }
        return data_type_mapping.get(specialty, ["病史数据", "基础检查"])

    def _generate_cache_key(
        self, intent_type: str, specialty: str, user_id: str
    ) -> str:
        """生成缓存键"""
        return f"{intent_type}:{specialty}:{user_id}"

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            cache_time = cache_entry.get("timestamp", 0)
            current_time = datetime.now().timestamp()

            # 检查缓存是否过期
            if current_time - cache_time < self.cache_ttl:
                return cache_entry.get("data")
            else:
                # 缓存已过期，删除
                del self.cache[cache_key]

        return None

    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """保存数据到缓存"""
        self.cache[cache_key] = {"data": data, "timestamp": datetime.now().timestamp()}

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.logger.info(f"[{self.__class__.__name__}] 缓存已清空")
