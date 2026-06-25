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
数据库存储服务客户端（重构版）
============================

负责从第三方数据库存储服务读取医疗数据。

主要功能：
1. 根据数据地址读取医疗数据
2. 支持多地域数据读取
3. 错误处理和重试
4. 数据格式转换
5. 支持MCP协议和HTTP协议（可通过配置切换）

作者: QSIR
版本: 2.1 - 支持MCP协议
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# MCP协议支持
try:
    from src.shared.agents.utils.mcp_storage_client import MCPStorageClient

    MCP_STORAGE_AVAILABLE = True
except ImportError:
    MCP_STORAGE_AVAILABLE = False
    logging.warning("[DatabaseStorageClient] MCP存储客户端未找到，将仅支持HTTP协议")


class DatabaseStorageConfig(BaseSettings):
    """数据库存储服务配置"""

    beijing_url: str = Field(
        default="http://database-storage-beijing:8000",
        alias="DATABASE_STORAGE_BEIJING_URL",
    )
    shanghai_url: str = Field(
        default="http://database-storage-shanghai:8000",
        alias="DATABASE_STORAGE_SHANGHAI_URL",
    )

    timeout: int = Field(
        default=30,
        alias="DATABASE_STORAGE_TIMEOUT",
    )
    retry_count: int | None = 2
    enable_logging: bool | None = True
    # MCP协议配置
    use_mcp: bool = Field(
        default=False,
        alias="USE_MCP_PROTOCOL",
    )
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",  # 默认为 ignore，可改为 allow/forbid
    )


class DatabaseStorageClient:
    """
    数据库存储服务客户端（重构版）

    支持多地域数据读取，根据数据地址的location字段选择对应的服务端点。
    支持MCP协议和HTTP协议，可通过配置切换。
    """

    def __init__(self, config: DatabaseStorageConfig):
        """
        初始化数据库存储服务客户端

        参数：
            config (DatabaseStorageConfig): 客户端配置
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session: Optional[aiohttp.ClientSession] = None

        # 地域URL映射（HTTP协议）
        self.location_urls = {
            "beijing": self.config.beijing_url,
            "shanghai": self.config.shanghai_url,
        }

        # MCP客户端（如果启用）
        self.mcp_client: Optional[MCPStorageClient] = None
        if self.config.use_mcp and MCP_STORAGE_AVAILABLE:
            try:
                self.mcp_client = MCPStorageClient()
                self.logger.info("[DatabaseStorageClient] MCP协议已启用")
            except Exception as e:
                self.logger.warning(
                    f"[DatabaseStorageClient] MCP客户端初始化失败: {e}，将使用HTTP协议"
                )
                self.mcp_client = None
        elif self.config.use_mcp and not MCP_STORAGE_AVAILABLE:
            self.logger.warning(
                "[DatabaseStorageClient] MCP协议已配置但库不可用，将使用HTTP协议"
            )

    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 如果使用MCP协议，延迟初始化MCP客户端（等待获取access_token）
        # 注意：MCP客户端将在retrieve_medical_data时，使用数据地址中的access_token进行初始化
        if self.mcp_client:
            # ✅ 延迟初始化：不在这里初始化，等待获取到access_token后再初始化
            self.logger.info(
                "[DatabaseStorageClient] MCP协议已启用，将在获取access_token后初始化连接"
            )
        else:
            # 如果使用HTTP协议，初始化HTTP会话
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # 清理MCP客户端
        if self.mcp_client:
            await self.mcp_client.cleanup()
        # 清理HTTP会话
        if self.session:
            await self.session.close()

    async def retrieve_medical_data(
        self, data_addresses: List[Dict[str, Any]], user_id: str
    ) -> Dict[str, Any]:
        """
        【✅ 真实第三方应用调用】从数据地址读取医疗数据

        ════════════════════════════════════════════════════════════
        【配置说明】
        ════════════════════════════════════════════════════════════

        此方法调用真实的第三方数据库存储服务，支持MCP协议和HTTP协议。

        MCP协议配置（优先）：
        - USE_MCP_PROTOCOL: 是否使用MCP协议（默认: false）
        - MCP_SERVER_BEIJING_URL: 北京地域MCP服务器URL（如: 192.168.208.66:30211）
        - MCP_SERVER_SHANGHAI_URL: 上海地域MCP服务器URL
        - MCP_SERVER_TOKEN: MCP服务器认证令牌
        - MCP_TRANSPORT_TYPE: 传输类型（streamable-http 或 sse，默认: streamable-http）
        - MCP_TIMEOUT: 超时时间（默认: 60秒）

        HTTP协议配置（降级）：
        - DATABASE_STORAGE_BEIJING_URL: 北京地域存储服务URL
        - DATABASE_STORAGE_SHANGHAI_URL: 上海地域存储服务URL
        - DATABASE_STORAGE_TIMEOUT: 超时时间（默认: 30秒）
        - DATABASE_STORAGE_API_KEY: API密钥（从数据地址中的access_token获取）

        模拟测试模式：
        - 如果使用模拟模式，请通过 backend/api/third_party_reserve.py 的
          ThirdPartyClient 进行模拟测试
        - 设置环境变量 THIRD_PARTY_MODE=simulation

        详细说明请参考：docs/第三方应用模拟测试与真实切换指南.md
        ════════════════════════════════════════════════════════════

        参数：
            data_addresses (List[Dict[str, Any]]): 数据地址列表，包含：
                - data_type: 数据类型
                - address: 数据地址
                - location: 地域信息（beijing/shanghai）
                - access_token: 访问令牌
                - hospital: 医院名称
            user_id (str): 用户ID

        返回：
            Dict[str, Any]: 医疗数据字典，包含：
                - medical_history: 病史数据
                - medications: 用药记录
                - lab_results: 化验报告
                - imaging_data: 影像数据
                - surgical_records: 手术记录
                - sources: 数据来源列表
                - available_data_types: 可用数据类型列表
        """
        if not data_addresses:
            self.logger.info("[DatabaseStorageClient] 没有数据地址，返回空数据")
            print("\n[数据存储服务] 没有数据地址，返回空数据\n")
            return {
                "medical_history": None,
                "medications": None,
                "lab_results": None,
                "imaging_data": None,
                "surgical_records": None,
                "sources": [],
                "available_data_types": [],
            }

        # 打印开始读取数据的信息
        print("\n[数据存储服务] ========================================")
        print("  开始读取医疗数据")
        print(f"  协议: {'MCP' if self.mcp_client else 'HTTP'}")
        print(f"  用户ID: {user_id}")
        print(f"  数据地址总数: {len(data_addresses)}")
        print("[数据存储服务] ========================================\n")

        # 如果使用MCP协议，调用MCP客户端
        if self.mcp_client:
            self.logger.info("[DatabaseStorageClient] 使用MCP协议读取数据")
            return await self.mcp_client.retrieve_medical_data(data_addresses, user_id)

        # 否则使用HTTP协议
        self.logger.info("[DatabaseStorageClient] 使用HTTP协议读取数据")

        # 按地域分组数据地址
        location_groups = self._group_by_location(data_addresses)

        # 打印地域分组信息
        if location_groups:
            print("[数据存储服务] 按地域分组:")
            for location, addresses in location_groups.items():
                print(f"  - {location}: {len(addresses)} 个数据地址")
            print()

        # 并行读取各地域的数据
        tasks = []
        for location, addresses in location_groups.items():
            task = self._retrieve_from_location(location, addresses, user_id)
            tasks.append(task)

        # 等待所有读取完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        merged_data = self._merge_results(results)

        # 打印合并后的数据摘要
        print("\n[数据存储服务] ========================================")
        print("  数据读取完成，合并结果:")
        print(
            f"    - 病史数据: {len(merged_data.get('medical_history', []))} 条"
            if isinstance(merged_data.get("medical_history"), list)
            else f"    - 病史数据: {'有' if merged_data.get('medical_history') else '无'}"
        )
        print(
            f"    - 用药记录: {len(merged_data.get('medications', []))} 条"
            if isinstance(merged_data.get("medications"), list)
            else f"    - 用药记录: {'有' if merged_data.get('medications') else '无'}"
        )
        print(
            f"    - 化验报告: {len(merged_data.get('lab_results', []))} 条"
            if isinstance(merged_data.get("lab_results"), list)
            else f"    - 化验报告: {'有' if merged_data.get('lab_results') else '无'}"
        )
        print(
            f"    - 影像数据: {len(merged_data.get('imaging_data', []))} 条"
            if isinstance(merged_data.get("imaging_data"), list)
            else f"    - 影像数据: {'有' if merged_data.get('imaging_data') else '无'}"
        )
        print(
            f"    - 手术记录: {len(merged_data.get('surgical_records', []))} 条"
            if isinstance(merged_data.get("surgical_records"), list)
            else f"    - 手术记录: {'有' if merged_data.get('surgical_records') else '无'}"
        )
        if merged_data.get("sources"):
            print(f"    - 数据来源: {merged_data.get('sources')}")
        if merged_data.get("available_data_types"):
            print(f"    - 可用数据类型: {merged_data.get('available_data_types')}")
        print("[数据存储服务] ========================================\n")

        # 打印详细调试信息（第一轮数据存储服务返回的完整数据）
        print("\n" + "=" * 80)
        print("[调试] 第一轮数据存储服务返回的完整数据")
        print("=" * 80)
        try:
            import json

            # 打印完整数据（限制长度以避免输出过长）
            data_str = json.dumps(merged_data, ensure_ascii=False, indent=2)
            if len(data_str) > 5000:
                print(data_str[:5000])
                print(f"\n... (数据过长，已截断，总长度: {len(data_str)} 字符)")
            else:
                print(data_str)
        except Exception as e:
            print(f"[错误] 打印数据失败: {e}")
            print(f"数据类型: {type(merged_data)}")
            print(
                f"数据键: {list(merged_data.keys()) if isinstance(merged_data, dict) else 'N/A'}"
            )
        print("=" * 80 + "\n")

        return merged_data

    def _group_by_location(
        self, data_addresses: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        按地域分组数据地址

        参数：
            data_addresses (List[Dict[str, Any]]): 数据地址列表

        返回：
            Dict[str, List[Dict[str, Any]]]: 按地域分组的数据地址
        """
        groups = {}
        for addr in data_addresses:
            location = addr.get("location", "unknown")
            if location not in groups:
                groups[location] = []
            groups[location].append(addr)
        return groups

    async def _retrieve_from_location(
        self, location: str, data_addresses: List[Dict[str, Any]], user_id: str
    ) -> Dict[str, Any]:
        """
        从指定地域的数据库存储服务读取数据

        参数：
            location (str): 地域（beijing/shanghai）
            data_addresses (List[Dict[str, Any]]): 该地域的数据地址列表
            user_id (str): 用户ID

        返回：
            Dict[str, Any]: 该地域的医疗数据
        """
        # 获取该地域的服务URL
        base_url = self.location_urls.get(location)
        if not base_url:
            self.logger.warning(f"[DatabaseStorageClient] 未知地域: {location}")
            return {}

        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )

        url = f"{base_url}/api/v1/storage/retrieve"

        # 构建请求
        request_data = {
            "data_addresses": data_addresses,
            "user_id": user_id,
            "request_id": f"req_{user_id}_{location}_{int(asyncio.get_event_loop().time())}",
            "timeout": self.config.timeout,
        }

        headers = {"Content-Type": "application/json"}

        # 从数据地址中提取access_token（如果有）
        # 注意：实际实现中，access_token应该由数据代理应用提供
        access_token = None
        for addr in data_addresses:
            if addr.get("access_token"):
                access_token = addr.get("access_token")
                break

        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        try:
            self.logger.info(
                f"[DatabaseStorageClient] 从{location}读取数据，地址数量: {len(data_addresses)}"
            )

            # 打印数据存储服务请求信息
            print("\n[数据存储服务请求] ========================================")
            print(f"  地域: {location}")
            print(f"  URL: {url}")
            print(f"  用户ID: {user_id}")
            print(f"  请求ID: {request_data.get('request_id', 'N/A')}")
            print(f"  数据地址数量: {len(data_addresses)}")
            print("  数据地址列表:")
            for i, addr in enumerate(data_addresses, 1):
                print(f"    {i}. 类型: {addr.get('data_type', 'N/A')}")
                print(f"       地域: {addr.get('location', 'N/A')}")
                print(f"       医院: {addr.get('hospital', 'N/A')}")
                print(
                    f"       地址: {addr.get('address', 'N/A')[:80]}..."
                    if len(addr.get("address", "")) > 80
                    else f"       地址: {addr.get('address', 'N/A')}"
                )
                if addr.get("parameters"):
                    print(f"       参数: {addr.get('parameters')}")
            print("[数据存储服务请求] ========================================\n")

            async with self.session.post(
                url, json=request_data, headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        medical_data = result.get("medical_data", {})
                        self.logger.info(
                            f"[DatabaseStorageClient] {location}数据读取成功"
                        )

                        # 打印数据存储服务响应信息
                        print(
                            "\n[数据存储服务响应] ========================================"
                        )
                        print(f"  地域: {location}")
                        print(f"  状态码: {response.status}")
                        print(f"  成功: {result.get('success', False)}")
                        print(f"  消息: {result.get('message', 'N/A')}")
                        print("  医疗数据:")
                        if medical_data:
                            print(
                                f"    - 病史数据: {len(medical_data.get('medical_history', []))} 条"
                                if isinstance(medical_data.get("medical_history"), list)
                                else f"    - 病史数据: {'有' if medical_data.get('medical_history') else '无'}"
                            )
                            print(
                                f"    - 用药记录: {len(medical_data.get('medications', []))} 条"
                                if isinstance(medical_data.get("medications"), list)
                                else f"    - 用药记录: {'有' if medical_data.get('medications') else '无'}"
                            )
                            print(
                                f"    - 化验报告: {len(medical_data.get('lab_results', []))} 条"
                                if isinstance(medical_data.get("lab_results"), list)
                                else f"    - 化验报告: {'有' if medical_data.get('lab_results') else '无'}"
                            )
                            print(
                                f"    - 影像数据: {len(medical_data.get('imaging_data', []))} 条"
                                if isinstance(medical_data.get("imaging_data"), list)
                                else f"    - 影像数据: {'有' if medical_data.get('imaging_data') else '无'}"
                            )
                            print(
                                f"    - 手术记录: {len(medical_data.get('surgical_records', []))} 条"
                                if isinstance(
                                    medical_data.get("surgical_records"), list
                                )
                                else f"    - 手术记录: {'有' if medical_data.get('surgical_records') else '无'}"
                            )
                            if medical_data.get("sources"):
                                print(f"    - 数据来源: {medical_data.get('sources')}")
                            if medical_data.get("available_data_types"):
                                print(
                                    f"    - 可用数据类型: {medical_data.get('available_data_types')}"
                                )

                            # 打印部分数据内容（用于调试）
                            if medical_data.get("medical_history"):
                                history = medical_data["medical_history"]
                                if isinstance(history, list) and len(history) > 0:
                                    print("    - 病史数据示例:")
                                    first_item = history[0]
                                    if isinstance(first_item, dict):
                                        for key in list(first_item.keys())[
                                            :5
                                        ]:  # 只打印前5个字段
                                            value = first_item[key]
                                            if (
                                                isinstance(value, str)
                                                and len(value) > 100
                                            ):
                                                print(f"      {key}: {value[:100]}...")
                                            else:
                                                print(f"      {key}: {value}")
                                elif isinstance(history, dict):
                                    print("    - 病史数据示例:")
                                    for key in list(history.keys())[:5]:
                                        value = history[key]
                                        if isinstance(value, str) and len(value) > 100:
                                            print(f"      {key}: {value[:100]}...")
                                        else:
                                            print(f"      {key}: {value}")
                        else:
                            print("    - 无数据")
                        print(
                            "[数据存储服务响应] ========================================\n"
                        )

                        return medical_data
                    else:
                        self.logger.warning(
                            f"[DatabaseStorageClient] {location}数据读取失败: {result.get('message')}"
                        )

                        # 打印错误信息
                        print(
                            "\n[数据存储服务响应] ========================================"
                        )
                        print(f"  地域: {location}")
                        print(f"  状态码: {response.status}")
                        print(f"  成功: {result.get('success', False)}")
                        print(f"  错误消息: {result.get('message', 'N/A')}")
                        print(
                            "[数据存储服务响应] ========================================\n"
                        )

                        return {}
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"[DatabaseStorageClient] {location}HTTP错误: {response.status} - {error_text}"
                    )

                    # 打印错误信息
                    print(
                        "\n[数据存储服务响应] ========================================"
                    )
                    print(f"  地域: {location}")
                    print(f"  状态码: {response.status}")
                    print(
                        f"  错误信息: {error_text[:500]}..."
                        if len(error_text) > 500
                        else f"  错误信息: {error_text}"
                    )
                    print(
                        "[数据存储服务响应] ========================================\n"
                    )

                    return {}

        except asyncio.TimeoutError:
            self.logger.error(f"[DatabaseStorageClient] {location}读取超时")

            # 打印超时信息
            print("\n[数据存储服务响应] ========================================")
            print(f"  地域: {location}")
            print("  错误: 请求超时")
            print("[数据存储服务响应] ========================================\n")

            return {}

        except Exception as e:
            self.logger.error(f"[DatabaseStorageClient] {location}读取异常: {str(e)}")

            # 打印异常信息
            print("\n[数据存储服务响应] ========================================")
            print(f"  地域: {location}")
            print(f"  错误: 请求异常 - {str(e)}")
            print("[数据存储服务响应] ========================================\n")

            return {}

    def _merge_results(self, results: List[Any]) -> Dict[str, Any]:
        """
        合并多个地域的读取结果

        参数：
            results (List[Any]): 各地域的读取结果列表

        返回：
            Dict[str, Any]: 合并后的医疗数据
        """
        merged = {
            "medical_history": [],
            "medications": [],
            "lab_results": [],
            "imaging_data": [],
            "surgical_records": [],
            "sources": [],
            "available_data_types": [],
        }

        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(
                    f"[DatabaseStorageClient] 读取结果包含异常: {str(result)}"
                )
                continue

            if not isinstance(result, dict):
                continue

            # 合并医疗数据
            if result.get("medical_history"):
                if isinstance(result["medical_history"], list):
                    merged["medical_history"].extend(result["medical_history"])
                else:
                    merged["medical_history"].append(result["medical_history"])

            if result.get("medications"):
                if isinstance(result["medications"], list):
                    merged["medications"].extend(result["medications"])
                else:
                    merged["medications"].append(result["medications"])

            if result.get("lab_results"):
                if isinstance(result["lab_results"], list):
                    merged["lab_results"].extend(result["lab_results"])
                else:
                    merged["lab_results"].append(result["lab_results"])

            if result.get("imaging_data"):
                if isinstance(result["imaging_data"], list):
                    merged["imaging_data"].extend(result["imaging_data"])
                else:
                    merged["imaging_data"].append(result["imaging_data"])

            if result.get("surgical_records"):
                if isinstance(result["surgical_records"], list):
                    merged["surgical_records"].extend(result["surgical_records"])
                else:
                    merged["surgical_records"].append(result["surgical_records"])

            # 合并数据来源
            if result.get("sources"):
                merged["sources"].extend(result["sources"])

            # 合并可用数据类型
            if result.get("available_data_types"):
                merged["available_data_types"].extend(result["available_data_types"])

        # 去重数据类型
        merged["available_data_types"] = list(set(merged["available_data_types"]))

        return merged


# 便捷函数：通过内部API调用（兼容现有系统）
async def retrieve_medical_data_via_internal_api(
    data_addresses: List[Dict[str, Any]],
    user_id: str,
    base_url: str = "http://localhost:8000",
) -> Dict[str, Any]:
    """
    通过内部API调用数据库存储服务（兼容现有系统）

    参数：
        data_addresses (List[Dict[str, Any]]): 数据地址列表
        user_id (str): 用户ID
        base_url (str): 内部API基础URL

    返回：
        Dict[str, Any]: 医疗数据
    """
    async with aiohttp.ClientSession() as session:
        # 构建请求
        request_data = {
            "data_addresses": data_addresses,
            "user_id": user_id,
            "request_id": f"req_{user_id}_{int(asyncio.get_event_loop().time())}",
            "timeout": 30,
        }

        # 调用内部API
        url = f"{base_url}/api/v1/third-party/retrieve-medical-data"

        try:
            async with session.post(url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        return result.get("medical_data", {})
                    else:
                        logging.warning(
                            f"[retrieve_medical_data_via_internal_api] 请求失败: {result.get('message')}"
                        )
                        return {}
                else:
                    error_text = await response.text()
                    logging.error(
                        f"[retrieve_medical_data_via_internal_api] HTTP错误: {response.status} - {error_text}"
                    )
                    return {}

        except Exception as e:
            logging.error(
                f"[retrieve_medical_data_via_internal_api] 调用异常: {str(e)}"
            )
            return {}
