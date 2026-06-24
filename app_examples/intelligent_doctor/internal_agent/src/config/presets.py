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
配置预设
========

定义常用配置预设（开发、测试、生产），支持一键切换配置。

作者: QSIR
版本: 1.0
"""

import os
import logging
from typing import Optional
from config.third_party_unified_config import (
    ThirdPartyUnifiedConfig,
    EntryAgentConfig,
    MCPConfig,
    HTTPConfig
)

logger = logging.getLogger(__name__)


class ConfigPresets:
    """配置预设"""
    
    @staticmethod
    def development() -> ThirdPartyUnifiedConfig:
        """
        开发环境配置
        
        特点：
        - 使用本地服务
        - EntryAgent启用
        - MCP禁用（使用HTTP降级）
        """
        return ThirdPartyUnifiedConfig(
            entry_agent=EntryAgentConfig(
                enabled=True,
                base_url=os.getenv("DATA_PROXY_APP_URL", "http://localhost:9090?token=dev_token"),
                token=None,  # 从URL中提取
                timeout=60
            ),
            mcp=MCPConfig(
                enabled=False,
                beijing_url="",
                shanghai_url="",
                token="",
                transport_type="streamable-http",
                timeout=60
            ),
            http=HTTPConfig(
                beijing_url=os.getenv("DATABASE_STORAGE_BEIJING_URL", "http://localhost:8001"),
                shanghai_url=os.getenv("DATABASE_STORAGE_SHANGHAI_URL", "http://localhost:8002"),
                api_key="dev_api_key",
                timeout=30
            )
        )
    
    @staticmethod
    def testing() -> ThirdPartyUnifiedConfig:
        """
        测试环境配置
        
        特点：
        - 使用测试服务器
        - EntryAgent启用
        - MCP可选启用
        """
        return ThirdPartyUnifiedConfig(
            entry_agent=EntryAgentConfig(
                enabled=True,
                base_url=os.getenv("DATA_PROXY_APP_URL", "http://test-server:9090?token=test_token"),
                token=None,
                timeout=60
            ),
            mcp=MCPConfig(
                enabled=os.getenv("USE_MCP_PROTOCOL", "false").lower() == "true",
                beijing_url=os.getenv("MCP_SERVER_BEIJING_URL", ""),
                shanghai_url=os.getenv("MCP_SERVER_SHANGHAI_URL", ""),
                token=os.getenv("MCP_SERVER_TOKEN", "test_token"),
                transport_type="streamable-http",
                timeout=60
            ),
            http=HTTPConfig(
                beijing_url=os.getenv("DATABASE_STORAGE_BEIJING_URL", "http://test-storage:8001"),
                shanghai_url=os.getenv("DATABASE_STORAGE_SHANGHAI_URL", "http://test-storage:8002"),
                api_key=os.getenv("DATABASE_STORAGE_API_KEY", "test_api_key"),
                timeout=30
            )
        )
    
    @staticmethod
    def production() -> ThirdPartyUnifiedConfig:
        """
        生产环境配置
        
        特点：
        - 使用生产服务器
        - EntryAgent启用
        - MCP启用
        - 所有配置从环境变量读取
        """
        return ThirdPartyUnifiedConfig(
            entry_agent=EntryAgentConfig(
                enabled=True,
                base_url=os.getenv("DATA_PROXY_APP_URL", ""),
                token=None,  # 从URL中提取或从环境变量获取
                timeout=int(os.getenv("DATA_PROXY_TIMEOUT", "60"))
            ),
            mcp=MCPConfig(
                enabled=True,
                beijing_url=os.getenv("MCP_SERVER_BEIJING_URL", ""),
                shanghai_url=os.getenv("MCP_SERVER_SHANGHAI_URL", ""),
                token=os.getenv("MCP_SERVER_TOKEN", ""),
                transport_type=os.getenv("MCP_TRANSPORT_TYPE", "streamable-http"),
                timeout=int(os.getenv("MCP_TIMEOUT", "60"))
            ),
            http=HTTPConfig(
                beijing_url=os.getenv("DATABASE_STORAGE_BEIJING_URL", ""),
                shanghai_url=os.getenv("DATABASE_STORAGE_SHANGHAI_URL", ""),
                api_key=os.getenv("DATABASE_STORAGE_API_KEY", ""),
                timeout=int(os.getenv("DATABASE_STORAGE_TIMEOUT", "30"))
            )
        )
    
    @staticmethod
    def custom() -> ThirdPartyUnifiedConfig:
        """
        自定义配置
        
        完全从环境变量读取，不设置默认值
        """
        from config.third_party_unified_config import ThirdPartyUnifiedConfig
        return ThirdPartyUnifiedConfig.from_env()
    
    @staticmethod
    def from_env_name(env_name: Optional[str] = None) -> ThirdPartyUnifiedConfig:
        """
        根据环境名称获取配置
        
        参数:
            env_name: 环境名称，可选值：
                - "development": 开发环境
                - "testing": 测试环境
                - "production": 生产环境
                - "custom": 自定义（从环境变量读取）
                - None: 从环境变量THIRD_PARTY_ENV读取，如果未设置则使用custom
        
        返回:
            ThirdPartyUnifiedConfig: 配置对象
        """
        if env_name is None:
            env_name = os.getenv("THIRD_PARTY_ENV", "custom")
        
        presets = {
            "development": ConfigPresets.development,
            "dev": ConfigPresets.development,
            "testing": ConfigPresets.testing,
            "test": ConfigPresets.testing,
            "production": ConfigPresets.production,
            "prod": ConfigPresets.production,
            "custom": ConfigPresets.custom,
        }
        
        preset_func = presets.get(env_name.lower())
        if preset_func:
            logger.info(f"使用配置预设: {env_name}")
            return preset_func()
        else:
            logger.warning(f"未知的环境名称: {env_name}，使用custom预设")
            return ConfigPresets.custom()
    
    @staticmethod
    def list_presets() -> list[str]:
        """列出所有可用的预设名称"""
        return ["development", "testing", "production", "custom"]


if __name__ == "__main__":
    # 测试配置预设
    print("=== 配置预设测试 ===")
    
    # 列出所有预设
    print(f"可用预设: {ConfigPresets.list_presets()}")
    
    # 测试各个预设
    for preset_name in ConfigPresets.list_presets():
        print(f"\n--- {preset_name} 预设 ---")
        config = ConfigPresets.from_env_name(preset_name)
        print(f"EntryAgent启用: {config.entry_agent.enabled}")
        print(f"MCP启用: {config.mcp.enabled}")
        print(f"EntryAgent URL: {config.entry_agent.base_url[:50]}..." if len(config.entry_agent.base_url) > 50 else f"EntryAgent URL: {config.entry_agent.base_url}")

