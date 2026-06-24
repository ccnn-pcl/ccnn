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
MCP数据存储服务客户端
====================

基于MCP协议连接真实的第三方数据存储服务，替代HTTP API调用。

作者: QSIR
版本: 1.0
"""

import asyncio

# MCP相关导入
# 在导入fastmcp之前，禁用dotenv文件的自动加载以避免编码错误
# fastmcp使用pydantic-settings，会自动读取.env文件，如果文件编码不是UTF-8会报错
import os
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Generator, List, Optional

import httpx

from src.logger.logger import get_logger

logger = get_logger(__name__)

# 必须在导入fastmcp之前设置这些环境变量
# 禁用pydantic-settings的dotenv自动加载
os.environ.setdefault("PYDANTIC_SETTINGS_SOURCE_DOTENV_ENABLED", "false")
# 尝试禁用fastmcp的.env文件读取（如果支持）
os.environ.setdefault("FASTMCP_DISABLE_ENV_FILE", "true")
# 禁用pydantic-settings查找.env文件
os.environ.setdefault("PYDANTIC_SETTINGS_DOTENV_PATH", "")

try:
    from mcp.client.session import ClientSession
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamablehttp_client

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("[MCPStorageClient] MCP库未安装，将无法使用MCP协议")
except (UnicodeDecodeError, Exception) as e:
    # 处理fastmcp初始化时的编码错误或其他异常
    MCP_AVAILABLE = False
    error_msg = str(e)
    if "utf-8" in error_msg.lower() or "codec" in error_msg.lower():
        logger.warning(
            f"[MCPStorageClient] MCP库初始化失败（编码错误）: {error_msg[:100]}，将无法使用MCP协议"
        )
        logger.warning(
            "[MCPStorageClient] 建议：检查项目目录或父目录中的.env文件编码，确保为UTF-8格式"
        )
        logger.warning("[MCPStorageClient] 或者删除/重命名有问题的.env文件")
        logger.warning(
            "[MCPStorageClient] 临时解决方案：设置环境变量 PYDANTIC_SETTINGS_SOURCE_DOTENV_ENABLED=false"
        )
    else:
        logger.warning(
            f"[MCPStorageClient] MCP库初始化失败: {error_msg[:100]}，将无法使用MCP协议"
        )


@dataclass
class MCPServerConfig:
    """MCP服务器配置"""

    server_url: str
    token: str
    transport_type: str = "streamable-http"  # streamable-http 或 sse
    timeout: int = 60
    retry_count: int = 2
    retry_delay: float = 1.0


class BearerAuth(httpx.Auth):
    def __init__(self, token: str) -> None:
        self._auth_header = self._build_auth_header(token)

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = self._auth_header
        yield request

    def _build_auth_header(self, token: str) -> str:
        return f"Bearer {token}"


class MCPServer:
    """
    MCP服务器连接管理器

    基于提供的mcp_server.py实现，封装MCP服务器连接和工具调用。
    """

    def __init__(self, config: MCPServerConfig):
        """
        初始化MCP服务器连接

        参数:
            config (MCPServerConfig): MCP服务器配置
        """
        if not MCP_AVAILABLE:
            raise ImportError("MCP库未安装，请先安装: pip install mcp fastmcp")

        self.config = config
        self.logger = logger.bind(module=self.__class__.__name__)
        self.session: Optional[ClientSession] = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()
        self._initialized = False

    async def initialize(self) -> None:
        """初始化MCP服务器连接"""
        if self._initialized:
            return

        if not self.config.server_url:
            raise ValueError("MCP服务器URL不能为空")

        # 构建URL
        if self.config.transport_type == "sse":
            url = f"http://{self.config.server_url}/sse"
        else:
            url = f"http://{self.config.server_url}/mcp"

        # 验证token
        if not self.config.token or self.config.token == "":
            raise ValueError("MCP服务器token不能为空，请设置 MCP_SERVER_TOKEN 环境变量")

        if self.config.token == "test":
            self.logger.warning("[MCPServer] ⚠️  使用默认token 'test'，可能无法通过认证")
            self.logger.warning("[MCPServer] 请设置正确的 MCP_SERVER_TOKEN 环境变量")

        # 打印token信息（仅显示前10个字符，保护隐私）
        token_preview = (
            self.config.token[:10] + "..."
            if len(self.config.token) > 10
            else self.config.token
        )
        self.logger.info(
            f"[MCPServer] 使用token: {token_preview} (长度: {len(self.config.token)})"
        )

        try:
            self.logger.info(f"[MCPServer] 正在连接MCP服务器: {url}")

            if self.config.transport_type == "sse":
                self.logger.info("[MCPServer] 使用SSE传输")
                transport = await self.exit_stack.enter_async_context(
                    sse_client(
                        url=url,
                        auth=BearerAuth(self.config.token),
                        timeout=self.config.timeout,
                    )
                )
                read, write = transport
            else:
                self.logger.info("[MCPServer] 使用StreamableHTTP传输")
                read, write, get_session_id = await self.exit_stack.enter_async_context(
                    streamablehttp_client(
                        url=url,
                        auth=BearerAuth(self.config.token),
                        timeout=timedelta(seconds=self.config.timeout),
                    )
                )

            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.session = session
            self._initialized = True

            self.logger.info("[MCPServer] MCP服务器连接成功")
            print("\n[MCPServer] ✅ MCP服务器连接成功")
            print(f"  服务器URL: {url}")
            print(f"  传输类型: {self.config.transport_type}")
            print(f"  Token: {token_preview} (长度: {len(self.config.token)})")
            print()

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"[MCPServer] 连接MCP服务器失败: {error_msg}")

            # 如果是401错误，提供详细的诊断信息
            if "401" in error_msg or "Unauthorized" in error_msg:
                self.logger.error("=" * 80)
                self.logger.error("[MCPServer] MCP服务器认证失败 (401 Unauthorized)")
                self.logger.error("=" * 80)
                self.logger.error(f"服务器URL: {url}")
                self.logger.error(f"Token预览: {token_preview}")
                self.logger.error(f"Token长度: {len(self.config.token)}")
                self.logger.error("")
                self.logger.error("请检查以下项目:")
                self.logger.error("  1. MCP_SERVER_TOKEN 环境变量是否正确设置")
                self.logger.error(f"  2. Token值是否正确（当前: {token_preview}）")
                self.logger.error("  3. Token是否已过期")
                self.logger.error("  4. MCP服务器是否正常运行")
                self.logger.error("  5. 网络连接是否正常")
                self.logger.error("")
                self.logger.error("解决方案:")
                self.logger.error("  - 联系MCP服务器管理员获取正确的token")
                self.logger.error("  - 运行 verify_mcp_token.py 脚本验证token")
                self.logger.error(
                    "  - 检查 start_backend.ps1 中的 MCP_SERVER_TOKEN 配置"
                )
                self.logger.error("=" * 80)

            await self.cleanup()
            raise

    async def list_tools(self) -> List[Any]:
        """
        列出MCP服务器上的可用工具

        返回:
            List[Any]: 工具列表
        """
        if not self.session:
            raise RuntimeError("MCP服务器未初始化")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                tools.extend(item[1])

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        retries: Optional[int] = None,
        delay: Optional[float] = None,
    ) -> Any:
        """
        执行MCP工具

        参数:
            tool_name (str): 工具名称
            arguments (Dict[str, Any]): 工具参数
            retries (int, optional): 重试次数，默认使用配置值
            delay (float, optional): 重试延迟（秒），默认使用配置值

        返回:
            Any: 工具执行结果
        """
        if not self.session:
            raise RuntimeError("MCP服务器未初始化")

        retries = retries or self.config.retry_count
        delay = delay or self.config.retry_delay

        attempt = 0
        while attempt < retries:
            try:
                # 打印详细的工具调用信息
                self.logger.info(f"[MCPServer] 执行工具: {tool_name}")
                self.logger.info(
                    f"[MCPServer] 工具参数摘要: department={arguments.get('department', 'N/A')}, user_id={arguments.get('user_id', 'N/A')}, data_addresses={len(arguments.get('data_addresses', []))}个"
                )
                print("\n[MCPServer] 调用MCP工具详情:")
                print(f"  工具名称: {tool_name}")
                print(f"  服务器URL: {self.config.server_url}")
                print("  参数:")
                print(f"    - department: {arguments.get('department', 'N/A')}")
                print(f"    - user_id: {arguments.get('user_id', 'N/A')}")
                print(f"    - request_id: {arguments.get('request_id', 'N/A')}")
                print(
                    f"    - data_addresses: {len(arguments.get('data_addresses', []))} 个"
                )
                print(f"    - data_types: {arguments.get('data_types', [])}")
                print(
                    f"    - access_tokens: {len(arguments.get('access_tokens', []))} 个"
                )

                result = await self.session.call_tool(tool_name, arguments)

                # 打印详细的响应信息
                self.logger.info(f"[MCPServer] 工具执行成功: {tool_name}")
                print("\n[MCPServer] ✅ MCP工具调用成功")
                print(f"  工具名称: {tool_name}")
                print(f"  响应类型: {type(result).__name__}")
                if isinstance(result, dict):
                    print(f"  响应键: {list(result.keys())}")
                    # 如果响应包含content，显示content摘要
                    if "content" in result:
                        content = result["content"]
                        if isinstance(content, list) and len(content) > 0:
                            print(f"  响应content数量: {len(content)}")
                            if isinstance(content[0], dict) and "text" in content[0]:
                                text_data = content[0]["text"]
                                text_preview = (
                                    str(text_data)[:300]
                                    if len(str(text_data)) > 300
                                    else str(text_data)
                                )
                                print(f"  响应内容预览: {text_preview}")
                                if len(str(text_data)) > 300:
                                    print(
                                        f"  ... (内容过长，已截断，总长度: {len(str(text_data))} 字符)"
                                    )
                    # 打印完整的响应（用于调试）
                    try:
                        import json

                        result_json = json.dumps(result, ensure_ascii=False, indent=2)
                        if len(result_json) > 1000:
                            print("\n  完整响应内容（前1000字符）:")
                            print(result_json[:1000])
                            print(
                                f"  ... (响应过长，已截断，总长度: {len(result_json)} 字符)"
                            )
                        else:
                            print("\n  完整响应内容:")
                            print(result_json)
                    except Exception as e:
                        print(f"  无法序列化响应: {e}")
                elif isinstance(result, list):
                    print(f"  响应列表长度: {len(result)}")
                    if len(result) > 0:
                        print(f"  第一个元素类型: {type(result[0]).__name__}")
                print()

                return result

            except Exception as e:
                attempt += 1
                self.logger.warning(
                    f"[MCPServer] 工具执行失败 (尝试 {attempt}/{retries}): {e}"
                )
                if attempt < retries:
                    self.logger.info(f"[MCPServer] {delay}秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error("[MCPServer] 达到最大重试次数，失败")
                    raise

    async def cleanup(self) -> None:
        """清理MCP服务器连接"""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self._initialized = False
                self.logger.info("[MCPServer] MCP服务器连接已关闭")
            except Exception as e:
                self.logger.error(f"[MCPServer] 清理连接时出错: {e}")


class MCPStorageClient:
    """
    MCP数据存储服务客户端

    通过MCP协议从真实的第三方数据存储服务获取医疗数据。
    """

    def __init__(self):
        """初始化MCP存储客户端"""
        self.logger = logger.bind(module=self.__class__.__name__)

        self.use_mcp = True

        # MCP服务器配置（按 (location, server_url) 组合）
        # 支持同一地域多个不同的MCP服务器
        self.mcp_servers: Dict[tuple, MCPServer] = {}

        # 科室映射配置
        self.hospital_to_department = {
            "北京医院": "内分泌科",
            "上海医院": "内科",
            # 可以根据实际情况扩展
        }

        self.specialty_to_department = {
            "内科": "内科",
            "外科": "外科",
            "内分泌科": "内分泌科",
            "影像科": "影像科",
            # 可以根据实际情况扩展
        }

        if self.use_mcp and MCP_AVAILABLE:
            self._initialize_mcp_servers()
        elif not MCP_AVAILABLE:
            self.logger.warning("[MCPStorageClient] MCP库未安装，将无法使用MCP协议")

    def _initialize_mcp_servers(self) -> None:
        """
        从环境变量初始化MCP服务器连接（预创建）

        注意：此方法主要用于向后兼容。现在主要依赖动态创建MCP服务器连接。
        如果环境变量中配置了MCP服务器URL，会预创建连接。
        如果数据地址中有不同的URL，会在运行时动态创建。
        """
        # 北京地域
        beijing_url = os.getenv("MCP_SERVER_BEIJING_URL", "")
        if beijing_url:
            beijing_token = os.getenv("MCP_SERVER_TOKEN", "")
            beijing_config = MCPServerConfig(
                server_url=beijing_url,
                token=beijing_token,
                transport_type=os.getenv("MCP_TRANSPORT_TYPE", "streamable-http"),
                timeout=int(os.getenv("MCP_TIMEOUT", "60")),
            )
            # 使用 (location, server_url) 作为key
            server_key = ("beijing", beijing_url)
            self.mcp_servers[server_key] = MCPServer(beijing_config)
            self.logger.info(
                f"[MCPStorageClient] 预创建北京MCP服务器连接: {beijing_url}"
            )

        # 上海地域
        shanghai_url = os.getenv("MCP_SERVER_SHANGHAI_URL", "")
        if shanghai_url:
            shanghai_token = os.getenv("MCP_SERVER_TOKEN", "")
            shanghai_config = MCPServerConfig(
                server_url=shanghai_url,
                token=shanghai_token,
                transport_type=os.getenv("MCP_TRANSPORT_TYPE", "streamable-http"),
                timeout=int(os.getenv("MCP_TIMEOUT", "60")),
            )
            # 使用 (location, server_url) 作为key
            server_key = ("shanghai", shanghai_url)
            self.mcp_servers[server_key] = MCPServer(shanghai_config)
            self.logger.info(
                f"[MCPStorageClient] 预创建上海MCP服务器连接: {shanghai_url}"
            )

        self.logger.info(
            f"[MCPStorageClient] 已预配置 {len(self.mcp_servers)} 个MCP服务器（从环境变量）"
        )

    async def initialize(self) -> None:
        """
        初始化所有MCP服务器连接

        注意：此方法会立即连接MCP服务器。如果希望使用数据代理应用返回的access_token，
        可以延迟调用此方法，或者先调用 update_mcp_token_from_data_addresses() 更新token。

        如果token为默认值"test"，建议延迟初始化，等待获取到access_token后再初始化。
        """
        if not self.use_mcp:
            return

        # ✅ 检查是否有默认token，如果有，延迟初始化
        has_default_token = False
        for server_key, server in self.mcp_servers.items():
            location, server_url = (
                server_key if isinstance(server_key, tuple) else (server_key, "")
            )
            if not server.config.token or server.config.token == "test":
                has_default_token = True
                self.logger.info(
                    f"[MCPStorageClient] {location} - {server_url} 使用默认token，将延迟初始化（等待access_token）"
                )
                print(
                    f"[MCPStorageClient] ⚠️  {location} - {server_url} 使用默认token，将延迟初始化（等待从数据地址获取access_token）"
                )

        if has_default_token:
            self.logger.info(
                "[MCPStorageClient] 检测到默认token，跳过立即初始化，将在获取access_token后初始化"
            )
            print(
                "[MCPStorageClient] ✅ 延迟初始化：等待从数据代理应用获取access_token后再连接MCP服务器"
            )
            return

        # 如果token不是默认值，正常初始化
        for server_key, server in self.mcp_servers.items():
            location, server_url = (
                server_key if isinstance(server_key, tuple) else (server_key, "")
            )
            try:
                await server.initialize()
                self.logger.info(
                    f"[MCPStorageClient] {location} - {server_url} MCP服务器初始化成功"
                )
            except Exception as e:
                self.logger.error(
                    f"[MCPStorageClient] {location} - {server_url} MCP服务器初始化失败: {e}"
                )
                # ⚠️ 不立即抛出异常，允许后续使用access_token重试
                self.logger.warning(
                    f"[MCPStorageClient] {location} - {server_url} MCP服务器初始化失败，将在获取access_token后重试"
                )

    async def cleanup(self) -> None:
        """清理所有MCP服务器连接"""
        for server_key, server in self.mcp_servers.items():
            location, server_url = (
                server_key if isinstance(server_key, tuple) else (server_key, "")
            )
            try:
                await server.cleanup()
                self.logger.info(
                    f"[MCPStorageClient] {location} - {server_url} MCP服务器已清理"
                )
            except Exception as e:
                self.logger.error(
                    f"[MCPStorageClient] {location} - {server_url} MCP服务器清理失败: {e}"
                )

    def _extract_department(self, data_address: Dict[str, Any]) -> str:
        """
        从数据地址中提取科室名称

        参数:
            data_address (Dict[str, Any]): 数据地址

        返回:
            str: 科室名称

        优先级:
        1. 直接使用data_address中的department字段（如果存在且不为空）
        2. 从parameters.specialty提取
        3. 从hospital映射到科室
        4. 默认返回"内科"
        """
        # ✅ 优先：直接使用data_address中的department字段
        department = data_address.get("department", "")
        if department and department.strip():
            self.logger.info(
                f"[MCPStorageClient] 从数据地址中提取到department: {department}"
            )
            print(f"[MCPStorageClient] ✅ 从数据地址中提取到department: {department}")
            return department.strip()

        # 其次：从parameters中提取specialty
        parameters = data_address.get("parameters", {})
        specialty = parameters.get("specialty")
        if specialty and specialty in self.specialty_to_department:
            mapped_dept = self.specialty_to_department[specialty]
            self.logger.info(
                f"[MCPStorageClient] 从parameters.specialty提取到科室: {mapped_dept}"
            )
            print(
                f"[MCPStorageClient] ✅ 从parameters.specialty提取到科室: {mapped_dept}"
            )
            return mapped_dept

        # 再次：从hospital映射到科室
        hospital = data_address.get("hospital", "")
        if hospital in self.hospital_to_department:
            mapped_dept = self.hospital_to_department[hospital]
            self.logger.info(f"[MCPStorageClient] 从hospital映射到科室: {mapped_dept}")
            print(f"[MCPStorageClient] ✅ 从hospital映射到科室: {mapped_dept}")
            return mapped_dept

        # 最后：默认返回"内科"
        self.logger.warning("[MCPStorageClient] 无法确定科室，使用默认值'内科'")
        self.logger.warning(
            f"[MCPStorageClient] 数据地址详情: hospital={hospital}, department={department}, parameters={parameters}"
        )
        print("[MCPStorageClient] ⚠️  警告: 无法确定科室，使用默认值'内科'")
        print(f"  数据地址详情: hospital={hospital}, department={department}")
        return "内科"

    def _build_mcp_arguments(
        self,
        data_addresses: List[Dict[str, Any]],
        user_id: str,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        构建MCP工具调用参数

        参数:
            data_addresses (List[Dict[str, Any]]): 数据地址列表，包含：
                - address: 数据地址（真实的数据存储位置）
                - access_token: 访问令牌
                - data_type: 数据类型
                - location: 地域信息
                - hospital: 医院名称
            user_id (str): 用户ID
            request_id (str, optional): 请求ID

        返回:
            Dict[str, Any]: MCP工具参数，包含：
                - department: 科室
                - request_id: 请求ID
                - user_id: 用户ID
                - data_addresses: 数据地址信息列表
                - data_types: 需要获取的数据类型列表
                - access_tokens: 访问令牌列表
        """
        # 生成请求ID
        if not request_id:
            import time

            request_id = f"req_{user_id}_{int(time.time())}"

        # 从第一个数据地址提取科室（假设同一批数据地址属于同一科室）
        department = (
            self._extract_department(data_addresses[0]) if data_addresses else "内科"
        )

        # ✅ 提取数据地址中的关键信息
        addresses_info = []
        access_tokens = []
        data_types = []

        for addr in data_addresses:
            # 提取数据地址信息
            address = addr.get("address", "")
            access_token = addr.get("access_token", "")
            data_type = addr.get("data_type", "")

            # 记录access_token提取情况
            if not access_token:
                self.logger.warning(
                    f"[MCPStorageClient] 数据地址中缺少access_token: address={address}, data_type={data_type}"
                )

            if address:
                addresses_info.append(
                    {
                        "address": address,
                        "data_type": data_type,
                        "hospital": addr.get("hospital", ""),
                        "location": addr.get("location", ""),
                    }
                )

            if access_token:
                access_tokens.append(access_token)
                self.logger.debug(
                    f"[MCPStorageClient] 提取到access_token: {access_token[:20]}... (长度: {len(access_token)})"
                )
            else:
                self.logger.warning(
                    f"[MCPStorageClient] 数据地址中access_token为空: address={address}"
                )

            if data_type:
                data_types.append(data_type)

        # ✅ 构建包含完整信息的MCP工具参数
        # 构建MCP工具参数（只传递基础参数，MCP服务器不接受额外参数）
        # 注意：真实的MCP服务器只接受 department、user_id、request_id 三个基础参数
        # data_addresses、data_types、access_tokens 等额外参数会导致参数验证失败
        arguments = {
            "department": department,
            "request_id": request_id,
            "user_id": user_id,
            # 注意：不传递 data_addresses、data_types、access_tokens
            # 这些信息已经通过 MCP_SERVER_TOKEN（access_token）和 server_url 传递
        }

        self.logger.info(
            f"[MCPStorageClient] 构建MCP参数: department={department}, user_id={user_id}, request_id={request_id}"
        )
        self.logger.info(
            f"[MCPStorageClient] 数据地址信息（用于参考）: {len(addresses_info)}个, 数据类型: {list(set(data_types))}, access_tokens: {len(access_tokens)}个"
        )
        return arguments

    def _parse_mcp_response(self, mcp_result: Any) -> Dict[str, Any]:
        """
        解析MCP响应并转换为医疗数据格式

        参数:
            mcp_result (Any): MCP工具执行结果

        返回:
            Dict[str, Any]: 医疗数据字典
        """
        # MCP响应格式可能不同，需要根据实际情况调整
        # 假设响应格式为:
        # {
        #     "content": [
        #         {
        #             "type": "text",
        #             "text": "{医疗数据JSON字符串}"
        #         }
        #     ]
        # }

        medical_data = {
            "medical_history": None,
            "medications": None,
            "lab_results": None,
            "imaging_data": None,
            "surgical_records": None,
            "sources": [],
            "available_data_types": [],
        }

        try:
            # 处理 CallToolResult 类型（MCP SDK返回的对象）
            if hasattr(mcp_result, "content"):
                # CallToolResult 对象，访问 content 属性
                content = mcp_result.content
                if isinstance(content, list) and len(content) > 0:
                    first_item = content[0]
                    # 如果content项有text属性
                    if hasattr(first_item, "text"):
                        text_data = first_item.text
                    elif isinstance(first_item, dict) and "text" in first_item:
                        text_data = first_item["text"]
                    else:
                        text_data = str(first_item)

                    # 检查是否是错误消息
                    if isinstance(text_data, str):
                        text_lower = text_data.lower().strip()
                        # 检测常见的错误消息
                        if (
                            "invalid token" in text_lower
                            or "token无效" in text_lower
                            or "认证失败" in text_lower
                        ):
                            self.logger.error(
                                f"[MCPStorageClient] ❌ MCP服务器返回认证错误: {text_data}"
                            )
                            print(
                                f"\n[MCPStorageClient] ❌ MCP服务器返回认证错误: {text_data}"
                            )
                            print("  这通常意味着access_token无效或已过期")
                            print("  请检查:")
                            print("    1. 数据地址中的access_token是否正确")
                            print("    2. access_token是否已过期")
                            print("    3. MCP服务器是否接受该token")
                            medical_data["error"] = "认证失败"
                            medical_data["error_message"] = text_data
                            medical_data["raw_response"] = text_data
                            return medical_data

                    # 尝试解析JSON
                    import json

                    try:
                        parsed_data = (
                            json.loads(text_data)
                            if isinstance(text_data, str)
                            else text_data
                        )
                        if isinstance(parsed_data, dict):
                            # ✅ 修复：如果数据在medical_data嵌套字段中，提取到顶层
                            if "medical_data" in parsed_data and isinstance(
                                parsed_data["medical_data"], dict
                            ):
                                # MCP返回格式：{"medical_history": null, "medical_data": {"medical_history": {...}, ...}}
                                # 需要将medical_data中的内容提取到顶层
                                nested_medical_data = parsed_data["medical_data"]
                                # 先更新顶层字段（如果有非null的值）
                                for key in [
                                    "medical_history",
                                    "medications",
                                    "lab_results",
                                    "imaging_data",
                                    "surgical_records",
                                    "health_monitoring",
                                ]:
                                    if (
                                        key in parsed_data
                                        and parsed_data[key] is not None
                                    ):
                                        medical_data[key] = parsed_data[key]
                                    elif (
                                        key in nested_medical_data
                                        and nested_medical_data[key] is not None
                                    ):
                                        medical_data[key] = nested_medical_data[key]
                                # 更新其他字段（sources, available_data_types等）
                                if "sources" in nested_medical_data:
                                    medical_data["sources"] = nested_medical_data[
                                        "sources"
                                    ]
                                elif "source" in nested_medical_data:
                                    # 兼容source字段（单数形式）
                                    sources = nested_medical_data["source"]
                                    medical_data["sources"] = (
                                        sources
                                        if isinstance(sources, list)
                                        else [sources]
                                    )
                                # 更新其他字段
                                for key in ["available_data_types", "request_id"]:
                                    if key in parsed_data:
                                        medical_data[key] = parsed_data[key]
                                    elif key in nested_medical_data:
                                        medical_data[key] = nested_medical_data[key]
                                self.logger.info(
                                    "[MCPStorageClient] ✅ 从medical_data嵌套字段中提取医疗数据"
                                )
                            else:
                                # 直接更新（没有嵌套medical_data字段）
                                medical_data.update(parsed_data)
                    except (json.JSONDecodeError, TypeError):
                        # 如果不是JSON，尝试直接使用
                        if isinstance(text_data, dict):
                            # 同样处理嵌套medical_data字段
                            if "medical_data" in text_data and isinstance(
                                text_data["medical_data"], dict
                            ):
                                nested_medical_data = text_data["medical_data"]
                                for key in [
                                    "medical_history",
                                    "medications",
                                    "lab_results",
                                    "imaging_data",
                                    "surgical_records",
                                    "health_monitoring",
                                ]:
                                    if key in text_data and text_data[key] is not None:
                                        medical_data[key] = text_data[key]
                                    elif (
                                        key in nested_medical_data
                                        and nested_medical_data[key] is not None
                                    ):
                                        medical_data[key] = nested_medical_data[key]
                                if "sources" in nested_medical_data:
                                    medical_data["sources"] = nested_medical_data[
                                        "sources"
                                    ]
                                elif "source" in nested_medical_data:
                                    sources = nested_medical_data["source"]
                                    medical_data["sources"] = (
                                        sources
                                        if isinstance(sources, list)
                                        else [sources]
                                    )
                            else:
                                medical_data.update(text_data)
                        else:
                            self.logger.warning(
                                "[MCPStorageClient] MCP响应content不是JSON格式"
                            )
                            medical_data["raw_response"] = text_data
                elif isinstance(content, dict):
                    # content直接是字典
                    # ✅ 修复：检查是否有medical_data嵌套字段
                    if "medical_data" in content and isinstance(
                        content["medical_data"], dict
                    ):
                        nested_medical_data = content["medical_data"]
                        for key in [
                            "medical_history",
                            "medications",
                            "lab_results",
                            "imaging_data",
                            "surgical_records",
                            "health_monitoring",
                        ]:
                            if key in content and content[key] is not None:
                                medical_data[key] = content[key]
                            elif (
                                key in nested_medical_data
                                and nested_medical_data[key] is not None
                            ):
                                medical_data[key] = nested_medical_data[key]
                        if "sources" in nested_medical_data:
                            medical_data["sources"] = nested_medical_data["sources"]
                        elif "source" in nested_medical_data:
                            sources = nested_medical_data["source"]
                            medical_data["sources"] = (
                                sources if isinstance(sources, list) else [sources]
                            )
                        for key in ["available_data_types", "request_id"]:
                            if key in content:
                                medical_data[key] = content[key]
                            elif key in nested_medical_data:
                                medical_data[key] = nested_medical_data[key]
                        self.logger.info(
                            "[MCPStorageClient] ✅ 从medical_data嵌套字段中提取医疗数据"
                        )
                    else:
                        medical_data.update(content)
                else:
                    self.logger.warning(
                        f"[MCPStorageClient] CallToolResult.content格式未知: {type(content)}"
                    )
                    medical_data["raw_response"] = content

            # 如果结果是字典
            elif isinstance(mcp_result, dict):
                # 尝试从content中提取
                if "content" in mcp_result:
                    content = mcp_result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        first_item = content[0]
                        if isinstance(first_item, dict) and "text" in first_item:
                            import json

                            text_data = first_item["text"]
                            # 尝试解析JSON
                            try:
                                parsed_data = (
                                    json.loads(text_data)
                                    if isinstance(text_data, str)
                                    else text_data
                                )
                                if isinstance(parsed_data, dict):
                                    # ✅ 修复：如果数据在medical_data嵌套字段中，提取到顶层
                                    if "medical_data" in parsed_data and isinstance(
                                        parsed_data["medical_data"], dict
                                    ):
                                        nested_medical_data = parsed_data[
                                            "medical_data"
                                        ]
                                        for key in [
                                            "medical_history",
                                            "medications",
                                            "lab_results",
                                            "imaging_data",
                                            "surgical_records",
                                            "health_monitoring",
                                        ]:
                                            if (
                                                key in parsed_data
                                                and parsed_data[key] is not None
                                            ):
                                                medical_data[key] = parsed_data[key]
                                            elif (
                                                key in nested_medical_data
                                                and nested_medical_data[key] is not None
                                            ):
                                                medical_data[key] = nested_medical_data[
                                                    key
                                                ]
                                        if "sources" in nested_medical_data:
                                            medical_data["sources"] = (
                                                nested_medical_data["sources"]
                                            )
                                        elif "source" in nested_medical_data:
                                            sources = nested_medical_data["source"]
                                            medical_data["sources"] = (
                                                sources
                                                if isinstance(sources, list)
                                                else [sources]
                                            )
                                        for key in [
                                            "available_data_types",
                                            "request_id",
                                        ]:
                                            if key in parsed_data:
                                                medical_data[key] = parsed_data[key]
                                            elif key in nested_medical_data:
                                                medical_data[key] = nested_medical_data[
                                                    key
                                                ]
                                        self.logger.info(
                                            "[MCPStorageClient] ✅ 从medical_data嵌套字段中提取医疗数据"
                                        )
                                    else:
                                        medical_data.update(parsed_data)
                            except json.JSONDecodeError:
                                # 如果不是JSON，直接使用
                                self.logger.warning(
                                    "[MCPStorageClient] MCP响应不是JSON格式"
                                )
                                medical_data["raw_response"] = text_data

                # 如果直接包含医疗数据字段
                elif any(
                    key in mcp_result
                    for key in ["medical_history", "medications", "lab_results"]
                ):
                    # ✅ 修复：检查是否有medical_data嵌套字段
                    if "medical_data" in mcp_result and isinstance(
                        mcp_result["medical_data"], dict
                    ):
                        nested_medical_data = mcp_result["medical_data"]
                        for key in [
                            "medical_history",
                            "medications",
                            "lab_results",
                            "imaging_data",
                            "surgical_records",
                            "health_monitoring",
                        ]:
                            if key in mcp_result and mcp_result[key] is not None:
                                medical_data[key] = mcp_result[key]
                            elif (
                                key in nested_medical_data
                                and nested_medical_data[key] is not None
                            ):
                                medical_data[key] = nested_medical_data[key]
                        if "sources" in nested_medical_data:
                            medical_data["sources"] = nested_medical_data["sources"]
                        elif "source" in nested_medical_data:
                            sources = nested_medical_data["source"]
                            medical_data["sources"] = (
                                sources if isinstance(sources, list) else [sources]
                            )
                        for key in ["available_data_types", "request_id"]:
                            if key in mcp_result:
                                medical_data[key] = mcp_result[key]
                            elif key in nested_medical_data:
                                medical_data[key] = nested_medical_data[key]
                        self.logger.info(
                            "[MCPStorageClient] ✅ 从medical_data嵌套字段中提取医疗数据"
                        )
                    else:
                        medical_data.update(mcp_result)

            # 如果结果是列表，取第一个元素
            elif isinstance(mcp_result, list) and len(mcp_result) > 0:
                return self._parse_mcp_response(mcp_result[0])

            # 如果结果已经是医疗数据格式
            elif isinstance(mcp_result, dict) and "medical_history" in mcp_result:
                medical_data = mcp_result

            else:
                # 尝试将对象转换为字典（如果是Pydantic模型或其他对象）
                if hasattr(mcp_result, "__dict__"):
                    try:
                        obj_dict = mcp_result.__dict__
                        if isinstance(obj_dict, dict):
                            # 如果对象有content属性，递归处理
                            if "content" in obj_dict:
                                return self._parse_mcp_response(obj_dict)
                            # 如果直接包含医疗数据字段
                            elif any(
                                key in obj_dict
                                for key in [
                                    "medical_history",
                                    "medications",
                                    "lab_results",
                                ]
                            ):
                                medical_data.update(obj_dict)
                            else:
                                medical_data["raw_response"] = obj_dict
                    except Exception as e:
                        self.logger.warning(
                            f"[MCPStorageClient] 无法将对象转换为字典: {e}"
                        )

                if not medical_data.get("raw_response"):
                    self.logger.warning(
                        f"[MCPStorageClient] 未知的MCP响应格式: {type(mcp_result)}"
                    )
                    # 尝试获取对象的字符串表示
                    try:
                        medical_data["raw_response"] = str(mcp_result)
                    except:
                        medical_data["raw_response"] = (
                            f"<{type(mcp_result).__name__} object>"
                        )

        except Exception as e:
            self.logger.error(f"[MCPStorageClient] 解析MCP响应失败: {e}")
            print(f"[MCPStorageClient] ❌ 解析MCP响应失败: {e}")
            print(f"  原始响应类型: {type(mcp_result).__name__}")
            if isinstance(mcp_result, dict):
                print(f"  原始响应键: {list(mcp_result.keys())}")
            elif isinstance(mcp_result, list):
                print(f"  原始响应列表长度: {len(mcp_result)}")
            medical_data["error"] = str(e)
            medical_data["raw_response"] = mcp_result

        # ✅ 修复：最后检查是否有medical_data嵌套字段（处理其他路径可能遗漏的情况）
        if (
            isinstance(medical_data, dict)
            and "medical_data" in medical_data
            and isinstance(medical_data["medical_data"], dict)
        ):
            nested_medical_data = medical_data["medical_data"]
            # 如果顶层字段为空或null，但嵌套字段有数据，则提取
            for key in [
                "medical_history",
                "medications",
                "lab_results",
                "imaging_data",
                "surgical_records",
                "health_monitoring",
            ]:
                if (
                    not medical_data.get(key) or medical_data[key] is None
                ) and nested_medical_data.get(key):
                    medical_data[key] = nested_medical_data[key]
                    self.logger.info(
                        f"[MCPStorageClient] ✅ 从medical_data嵌套字段中提取{key}"
                    )
            # 更新sources
            if not medical_data.get("sources") and nested_medical_data.get("sources"):
                medical_data["sources"] = nested_medical_data["sources"]
            elif not medical_data.get("sources") and nested_medical_data.get("source"):
                sources = nested_medical_data["source"]
                medical_data["sources"] = (
                    sources if isinstance(sources, list) else [sources]
                )
            # 清理嵌套字段（避免重复）
            if medical_data.get("medical_data"):
                del medical_data["medical_data"]

        # 打印解析后的医疗数据详情（用于调试）
        self.logger.debug(
            f"[MCPStorageClient] 解析后的医疗数据键: {list(medical_data.keys())}"
        )

        return medical_data

    async def retrieve_medical_data(
        self, data_addresses: List[Dict[str, Any]], user_id: str
    ) -> Dict[str, Any]:
        """
        通过MCP协议从数据地址读取医疗数据

        参数:
            data_addresses (List[Dict[str, Any]]): 数据地址列表
            user_id (str): 用户ID

        返回:
            Dict[str, Any]: 医疗数据字典
        """
        if not self.use_mcp:
            raise RuntimeError("MCP协议未启用，请设置 USE_MCP_PROTOCOL=true")

        if not data_addresses:
            self.logger.info("[MCPStorageClient] 没有数据地址，返回空数据")
            return {
                "medical_history": None,
                "medications": None,
                "lab_results": None,
                "imaging_data": None,
                "surgical_records": None,
                "sources": [],
                "available_data_types": [],
            }

        # 按地域和MCP服务器URL组合分组数据地址
        location_server_groups = self._group_by_location_and_server(data_addresses)

        # 并行处理各地域和MCP服务器组合的数据
        tasks = []
        for (location, server_url), addresses in location_server_groups.items():
            task = self._retrieve_from_location_and_server(
                location, server_url, addresses, user_id
            )
            tasks.append(task)

        # 等待所有读取完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        merged_data = self._merge_results(results)

        return merged_data

    def _group_by_location_and_server(
        self, data_addresses: List[Dict[str, Any]]
    ) -> Dict[tuple, List[Dict[str, Any]]]:
        """
        按地域和MCP服务器URL组合分组数据地址

        参数:
            data_addresses: 数据地址列表

        返回:
            Dict[tuple, List[Dict]]: key为 (location, server_url) 元组，value为该组合的数据地址列表
        """
        groups = {}
        for addr in data_addresses:
            location = addr.get("location", "beijing")
            # 从数据地址中获取MCP服务器URL
            server_url = addr.get("address", "")  # 优先使用address字段
            if not server_url:
                # 如果没有address，尝试从data_service_address获取
                server_url = addr.get("data_service_address", "")

            if not server_url:
                self.logger.warning(
                    "[MCPStorageClient] 数据地址中缺少server_url，使用环境变量默认值"
                )
                # 使用环境变量中的默认值
                if location == "beijing":
                    server_url = os.getenv("MCP_SERVER_BEIJING_URL", "")
                elif location == "shanghai":
                    server_url = os.getenv("MCP_SERVER_SHANGHAI_URL", "")
                else:
                    server_url = os.getenv("MCP_SERVER_BEIJING_URL", "")

            if not server_url:
                self.logger.error(
                    f"[MCPStorageClient] 无法确定MCP服务器URL，跳过该数据地址: {addr}"
                )
                continue

            # 使用 (location, server_url) 作为key
            key = (location, server_url)
            if key not in groups:
                groups[key] = []
            groups[key].append(addr)

        self.logger.info(
            f"[MCPStorageClient] 按地域和服务器分组完成，共 {len(groups)} 个组合"
        )
        for (loc, url), addrs in groups.items():
            self.logger.info(
                f"[MCPStorageClient]   - {loc} - {url}: {len(addrs)} 个数据地址"
            )

        return groups

    async def _retrieve_from_location_and_server(
        self,
        location: str,
        server_url: str,
        data_addresses: List[Dict[str, Any]],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        从指定地域和MCP服务器的组合读取数据

        参数:
            location (str): 地域（beijing/shanghai）
            server_url (str): MCP服务器URL（如: 192.168.208.66:30211）
            data_addresses (List[Dict[str, Any]]): 该组合的数据地址列表
            user_id (str): 用户ID

        返回:
            Dict[str, Any]: 该组合的医疗数据
        """
        # 使用 (location, server_url) 作为key
        server_key = (location, server_url)

        # ✅ 从数据地址中提取access_token，用于更新MCP服务器配置
        access_token_from_data = None
        for addr in data_addresses:
            token = addr.get("access_token", "")
            if token:
                access_token_from_data = token
                self.logger.info(
                    f"[MCPStorageClient] 从数据地址中提取到access_token: {token[:20]}... (长度: {len(token)})"
                )
                print(
                    "[MCPStorageClient] ✅ 从数据地址中提取到access_token，将用于MCP服务器连接认证"
                )
                print(f"  Token预览: {token[:30]}... (长度: {len(token)})")
                break

        # 如果没有提取到token，记录警告
        if not access_token_from_data:
            self.logger.warning("[MCPStorageClient] ⚠️  数据地址中未找到access_token")
            print("[MCPStorageClient] ⚠️  警告: 数据地址中未找到access_token")
            print("  数据地址详情:")
            for i, addr in enumerate(data_addresses, 1):
                print(f"    {i}. address: {addr.get('address', 'N/A')}")
                print(f"       data_type: {addr.get('data_type', 'N/A')}")
                print(
                    f"       access_token: {'有' if addr.get('access_token') else '无'}"
                )
            print("  将使用环境变量中的默认token（可能无效）")

        # 获取或创建MCP服务器连接
        mcp_server = self.mcp_servers.get(server_key)
        if not mcp_server:
            # 动态创建新的MCP服务器连接
            self.logger.info(
                f"[MCPStorageClient] 创建新的MCP服务器连接: {location} - {server_url}"
            )
            print(
                f"[MCPStorageClient] 🔄 创建新的MCP服务器连接: {location} - {server_url}"
            )

            # 使用从数据地址中提取的access_token，如果没有则使用默认值
            token = access_token_from_data or os.getenv("MCP_SERVER_TOKEN", "test")

            server_config = MCPServerConfig(
                server_url=server_url,
                token=token,
                transport_type=os.getenv("MCP_TRANSPORT_TYPE", "streamable-http"),
                timeout=int(os.getenv("MCP_TIMEOUT", "60")),
            )
            mcp_server = MCPServer(server_config)
            self.mcp_servers[server_key] = mcp_server
            self.logger.info(f"[MCPStorageClient] 已创建MCP服务器连接: {server_key}")
            print(
                f"[MCPStorageClient] ✅ 已创建MCP服务器连接: {location} - {server_url}"
            )

        # ✅ 如果从数据地址中获取到access_token，更新MCP服务器配置
        if access_token_from_data:
            old_token = mcp_server.config.token
            # 如果token不同，需要更新并重新初始化
            if old_token != access_token_from_data:
                mcp_server.config.token = access_token_from_data
                self.logger.info(
                    f"[MCPStorageClient] 已使用数据代理应用返回的access_token更新MCP服务器配置: {server_url}"
                )
                self.logger.info(
                    f"[MCPStorageClient] 旧token: {old_token[:20] if old_token else 'N/A'}..."
                )
                self.logger.info(
                    f"[MCPStorageClient] 新token: {access_token_from_data[:20]}..."
                )
                print(f"[MCPStorageClient] ✅ 已更新MCP服务器token配置: {server_url}")
                print(f"  旧token: {old_token[:20] if old_token else 'N/A'}...")
                print(f"  新token: {access_token_from_data[:20]}...")

                # 如果已经初始化，需要清理并重新初始化
                if mcp_server._initialized:
                    self.logger.info(
                        "[MCPStorageClient] MCP服务器已初始化，清理旧连接并重新初始化"
                    )
                    print(
                        "[MCPStorageClient] ⚠️  MCP服务器已初始化，清理旧连接并重新初始化（使用新token）"
                    )
                    try:
                        await mcp_server.cleanup()
                    except Exception as e:
                        self.logger.warning(f"[MCPStorageClient] 清理旧连接时出错: {e}")
                    mcp_server._initialized = False
            else:
                self.logger.info(
                    f"[MCPStorageClient] Token未变化，继续使用现有连接: {server_url}"
                )
        elif not mcp_server.config.token or mcp_server.config.token == "test":
            self.logger.warning(
                f"[MCPStorageClient] ⚠️  数据地址中未找到access_token，且当前token为默认值: {server_url}"
            )
            self.logger.warning("[MCPStorageClient] 可能无法通过MCP服务器认证")
            print(
                f"[MCPStorageClient] ⚠️  警告: 数据地址中未找到access_token，使用默认token可能无法通过认证: {server_url}"
            )

        # 确保服务器已初始化（使用更新后的token）
        if not mcp_server._initialized:
            await mcp_server.initialize()

        # 构建MCP工具参数
        import time

        request_id = f"req_{user_id}_{location}_{int(time.time())}"
        arguments = self._build_mcp_arguments(data_addresses, user_id, request_id)

        # 打印详细的请求信息
        print("\n" + "=" * 80)
        print("[MCP数据存储服务请求] 详细请求信息")
        print("=" * 80)
        print(f"  地域: {location}")
        print(f"  MCP服务器URL: {server_url} (配置: {mcp_server.config.server_url})")
        print(
            f"  MCP服务器Token: {mcp_server.config.token[:20] if mcp_server.config.token else 'N/A'}... (长度: {len(mcp_server.config.token) if mcp_server.config.token else 0})"
        )
        print(f"  传输类型: {mcp_server.config.transport_type}")
        print("  工具名称: get_patient_medical_info")
        print(f"  用户ID: {user_id}")
        print(f"  请求ID: {request_id}")
        print(f"  数据地址数量: {len(data_addresses)}")
        print("\n  数据地址详情:")
        for i, addr in enumerate(data_addresses, 1):
            print(f"    {i}. 数据类型: {addr.get('data_type', 'N/A')}")
            print(f"       address: {addr.get('address', 'N/A')}")
            print(f"       医院: {addr.get('hospital', 'N/A')}")
            print(f"       地域: {addr.get('location', 'N/A')}")
            access_token = addr.get("access_token", "")
            if access_token:
                print(
                    f"       access_token: {access_token[:20]}... (长度: {len(access_token)})"
                )
            else:
                print("       access_token: (空)")
        print("\n  MCP工具调用参数（只传递基础参数）:")
        print(f"    - department: {arguments.get('department', 'N/A')}")
        print(f"    - user_id: {arguments.get('user_id', 'N/A')}")
        print(f"    - request_id: {arguments.get('request_id', 'N/A')}")
        print("\n  注意: MCP工具只接受基础参数（department、user_id、request_id）")
        print("  数据地址信息已通过 MCP_SERVER_TOKEN 和 server_url 传递")
        print("  数据地址详情（用于参考）:")
        for i, addr in enumerate(data_addresses, 1):
            print(f"    {i}. address: {addr.get('address', 'N/A')}")
            print(f"       data_type: {addr.get('data_type', 'N/A')}")
            print(f"       hospital: {addr.get('hospital', 'N/A')}")
            print(f"       location: {addr.get('location', 'N/A')}")
            access_token = addr.get("access_token", "")
            if access_token:
                print(
                    f"       access_token: {access_token[:30]}... (长度: {len(access_token)})"
                )
            else:
                print("       access_token: (空)")

        print("=" * 80)

        try:
            # 执行MCP工具
            result = await mcp_server.execute_tool(
                "get_patient_medical_info", arguments
            )

            # 解析响应
            medical_data = self._parse_mcp_response(result)

            # 检查是否有认证错误
            has_auth_error = (
                medical_data.get("error") == "认证失败"
                or "invalid token" in str(medical_data.get("error_message", "")).lower()
                or "invalid token" in str(medical_data.get("raw_response", "")).lower()
            )

            # 打印详细的响应信息
            print("\n" + "=" * 80)
            print("[MCP数据存储服务响应] 详细响应信息")
            print("=" * 80)
            print(f"  地域: {location}")
            print(f"  成功: {not has_auth_error}")
            print(f"  原始响应类型: {type(result).__name__}")
            if isinstance(result, dict):
                print(f"  原始响应键: {list(result.keys())}")
            elif isinstance(result, list):
                print(f"  原始响应列表长度: {len(result)}")
            elif hasattr(result, "content"):
                print(f"  原始响应content类型: {type(result.content)}")
                if isinstance(result.content, list) and len(result.content) > 0:
                    print(f"  content[0]类型: {type(result.content[0])}")
                    if hasattr(result.content[0], "text"):
                        text_preview = (
                            str(result.content[0].text)[:100]
                            if len(str(result.content[0].text)) > 100
                            else str(result.content[0].text)
                        )
                        print(f"  content[0].text预览: {text_preview}")

            if has_auth_error:
                print("\n  ⚠️  认证错误详情:")
                print("    - 错误类型: 认证失败")
                print(
                    f"    - 错误消息: {medical_data.get('error_message', medical_data.get('raw_response', 'N/A'))}"
                )
                print("    - 可能原因:")
                print("      1. access_token无效或已过期")
                print("      2. access_token格式不正确")
                print("      3. MCP服务器不接受该token")
                print("    - 建议:")
                print("      1. 检查数据地址中的access_token是否正确")
                print("      2. 联系MCP服务器管理员验证token有效性")
                print("      3. 确认token是否已过期")
            else:
                print("\n  医疗数据摘要:")
            print(
                f"    - 病史数据: {'有' if medical_data.get('medical_history') else '无'}"
            )
            if medical_data.get("medical_history"):
                if isinstance(medical_data.get("medical_history"), list):
                    print(f"      数量: {len(medical_data.get('medical_history'))} 条")
                elif isinstance(medical_data.get("medical_history"), dict):
                    print(
                        f"      键: {list(medical_data.get('medical_history').keys())}"
                    )
            print(
                f"    - 用药记录: {'有' if medical_data.get('medications') else '无'}"
            )
            if medical_data.get("medications"):
                if isinstance(medical_data.get("medications"), list):
                    print(f"      数量: {len(medical_data.get('medications'))} 条")
            print(
                f"    - 化验报告: {'有' if medical_data.get('lab_results') else '无'}"
            )
            if medical_data.get("lab_results"):
                if isinstance(medical_data.get("lab_results"), list):
                    print(f"      数量: {len(medical_data.get('lab_results'))} 条")
            print(
                f"    - 影像数据: {'有' if medical_data.get('imaging_data') else '无'}"
            )
            print(
                f"    - 手术记录: {'有' if medical_data.get('surgical_records') else '无'}"
            )
            if medical_data.get("sources"):
                print(f"    - 数据来源: {medical_data.get('sources')}")
            if medical_data.get("available_data_types"):
                print(f"    - 可用数据类型: {medical_data.get('available_data_types')}")
            print("=" * 80)

            # 打印详细调试信息（MCP返回的完整数据）
            print("\n" + "=" * 80)
            print(f"[调试] MCP数据存储服务返回的完整数据（地域: {location}）")
            print("=" * 80)
            try:
                import json

                # 清理可能包含不可序列化对象的数据
                clean_data = {}
                for key, value in medical_data.items():
                    if key == "raw_response":
                        # 对于raw_response，尝试转换为字符串
                        if hasattr(value, "__dict__"):
                            try:
                                clean_data[key] = str(value)
                            except:
                                clean_data[key] = f"<{type(value).__name__} object>"
                        elif hasattr(value, "content"):
                            # 如果是CallToolResult对象，提取content
                            try:
                                if hasattr(
                                    value.content, "__iter__"
                                ) and not isinstance(value.content, str):
                                    clean_data[key] = [
                                        str(item) for item in value.content
                                    ]
                                else:
                                    clean_data[key] = str(value.content)
                            except:
                                clean_data[key] = f"<{type(value).__name__} object>"
                        else:
                            clean_data[key] = (
                                str(value)
                                if not isinstance(
                                    value,
                                    (dict, list, str, int, float, bool, type(None)),
                                )
                                else value
                            )
                    else:
                        clean_data[key] = value

                # 打印完整数据（限制长度以避免输出过长）
                data_str = json.dumps(clean_data, ensure_ascii=False, indent=2)
                if len(data_str) > 5000:
                    print("\n医疗数据（前5000字符）:")
                    print(data_str[:5000])
                    print(f"\n... (数据过长，已截断，总长度: {len(data_str)} 字符)")
                else:
                    print("\n医疗数据:")
                    print(data_str)
            except Exception as e:
                print(f"[错误] 打印数据失败: {e}")
                print(f"数据类型: {type(medical_data)}")
                print(
                    f"数据键: {list(medical_data.keys()) if isinstance(medical_data, dict) else 'N/A'}"
                )
                # 尝试打印原始响应的基本信息
                if hasattr(result, "content"):
                    try:
                        print(f"原始响应content类型: {type(result.content)}")
                        if isinstance(result.content, list) and len(result.content) > 0:
                            print(f"content[0]类型: {type(result.content[0])}")
                            if hasattr(result.content[0], "text"):
                                print(
                                    f"content[0].text预览: {str(result.content[0].text)[:200]}..."
                                )
                    except Exception as e2:
                        print(f"无法访问原始响应content: {e2}")
            print("=" * 80 + "\n")

            # 根据是否有错误记录日志
            if has_auth_error:
                self.logger.error(
                    f"[MCPStorageClient] {location}地域数据读取失败: 认证错误"
                )
            else:
                self.logger.info(f"[MCPStorageClient] {location}地域数据读取成功")
            return medical_data

        except Exception as e:
            self.logger.error(f"[MCPStorageClient] {location}地域数据读取失败: {e}")

            # 打印错误信息
            print("\n[MCP数据存储服务响应] ========================================")
            print(f"  地域: {location}")
            print(f"  错误: {str(e)}")
            print("[MCP数据存储服务响应] ========================================\n")

            return {}

    def _merge_results(self, results: List[Any]) -> Dict[str, Any]:
        """合并多个地域的读取结果"""
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
                    f"[MCPStorageClient] 读取结果包含异常: {str(result)}"
                )
                continue

            if not isinstance(result, dict):
                continue

            # 合并医疗数据
            for key in [
                "medical_history",
                "medications",
                "lab_results",
                "imaging_data",
                "surgical_records",
            ]:
                if result.get(key):
                    if isinstance(result[key], list):
                        merged[key].extend(result[key])
                    else:
                        merged[key].append(result[key])

            # 合并数据来源
            if result.get("sources"):
                merged["sources"].extend(result["sources"])

            # 合并可用数据类型
            if result.get("available_data_types"):
                merged["available_data_types"].extend(result["available_data_types"])

        # 去重数据类型
        merged["available_data_types"] = list(set(merged["available_data_types"]))

        return merged
