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
第三方应用统一配置管理
====================

统一管理EntryAgent和MCP相关配置，支持环境变量和配置文件两种方式。

功能特性：
1. 环境变量配置：支持通过环境变量设置配置参数
2. 配置文件支持：支持通过配置文件设置参数
3. 默认值管理：提供合理的默认配置值
4. 配置验证：验证配置参数的有效性
5. 动态更新：支持运行时配置更新

作者: QSIR
版本: 1.0
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


@dataclass
class EntryAgentConfig:
    """EntryAgent配置（标准A2A SDK）"""
    enabled: bool = False
    base_url: str = ""
    token: Optional[str] = None
    timeout: int = 60
    
    @classmethod
    def _extract_token_from_url(cls, url: str) -> Optional[str]:
        """从URL中提取token参数"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            token_list = query_params.get('token', [])
            if token_list:
                return token_list[0]
        except Exception:
            pass
        return None
    
    @classmethod
    def from_env(cls) -> 'EntryAgentConfig':
        """从环境变量创建配置"""
        base_url = os.getenv("DATA_PROXY_APP_URL", "")
        token = cls._extract_token_from_url(base_url)
        
        # 如果URL中没有token，尝试从环境变量获取
        if not token:
            token = os.getenv("DATA_PROXY_TOKEN", None)
        
        return cls(
            enabled=os.getenv("USE_ENTRY_AGENT", "false").lower() == "true",
            base_url=base_url,
            token=token,
            timeout=int(os.getenv("DATA_PROXY_TIMEOUT", "60"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def validate(self) -> tuple[bool, list[str]]:
        """验证配置"""
        errors = []
        if self.enabled:
            if not self.base_url:
                errors.append("EntryAgent已启用但未配置base_url")
        return len(errors) == 0, errors


@dataclass
class MCPConfig:
    """MCP协议配置"""
    enabled: bool = False
    beijing_url: str = ""
    shanghai_url: str = ""
    token: str = ""
    transport_type: str = "streamable-http"  # streamable-http 或 sse
    timeout: int = 60
    
    @classmethod
    def from_env(cls) -> 'MCPConfig':
        """从环境变量创建配置"""
        return cls(
            enabled=os.getenv("USE_MCP_PROTOCOL", "false").lower() == "true",
            beijing_url=os.getenv("MCP_SERVER_BEIJING_URL", ""),
            shanghai_url=os.getenv("MCP_SERVER_SHANGHAI_URL", ""),
            token=os.getenv("MCP_SERVER_TOKEN", ""),
            transport_type=os.getenv("MCP_TRANSPORT_TYPE", "streamable-http"),
            timeout=int(os.getenv("MCP_TIMEOUT", "60"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置
        
        注意：在多MCP服务器场景下，URL和Token可以从数据地址中动态获取。
        因此，如果环境变量中未配置，只给出警告，不视为错误。
        """
        errors = []
        warnings = []
        if self.enabled:
            if not self.beijing_url:
                warnings.append("MCP已启用但未配置beijing_url（将使用数据地址中的server_url）")
            if not self.token or self.token == "test":
                warnings.append("MCP已启用但token为默认值（将使用数据地址中的access_token）")
        # 只返回错误，警告通过日志输出
        return len(errors) == 0, errors


@dataclass
class HTTPConfig:
    """HTTP协议配置（降级方案）"""
    beijing_url: str = ""
    shanghai_url: str = ""
    api_key: str = ""
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'HTTPConfig':
        """从环境变量创建配置"""
        return cls(
            beijing_url=os.getenv("DATABASE_STORAGE_BEIJING_URL", ""),
            shanghai_url=os.getenv("DATABASE_STORAGE_SHANGHAI_URL", ""),
            api_key=os.getenv("DATABASE_STORAGE_API_KEY", ""),
            timeout=int(os.getenv("DATABASE_STORAGE_TIMEOUT", "30"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ThirdPartyUnifiedConfig:
    """第三方应用统一配置"""
    entry_agent: EntryAgentConfig
    mcp: MCPConfig
    http: HTTPConfig
    
    @classmethod
    def from_env(cls) -> 'ThirdPartyUnifiedConfig':
        """从环境变量创建配置"""
        return cls(
            entry_agent=EntryAgentConfig.from_env(),
            mcp=MCPConfig.from_env(),
            http=HTTPConfig.from_env()
        )
    
    @classmethod
    def from_file(cls, config_file: str) -> 'ThirdPartyUnifiedConfig':
        """从配置文件创建配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return cls(
                entry_agent=EntryAgentConfig(**config_data.get("entry_agent", {})),
                mcp=MCPConfig(**config_data.get("mcp", {})),
                http=HTTPConfig(**config_data.get("http", {}))
            )
        except Exception as e:
            logger.error(f"从配置文件加载配置失败: {str(e)}")
            return cls.from_env()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "entry_agent": self.entry_agent.to_dict(),
            "mcp": self.mcp.to_dict(),
            "http": self.http.to_dict()
        }
    
    def validate(self) -> tuple[bool, list[str]]:
        """验证配置"""
        all_errors = []
        
        # 验证EntryAgent配置
        entry_valid, entry_errors = self.entry_agent.validate()
        all_errors.extend(entry_errors)
        
        # 验证MCP配置
        mcp_valid, mcp_errors = self.mcp.validate()
        all_errors.extend(mcp_errors)
        
        return len(all_errors) == 0, all_errors
    
    def save_to_file(self, config_file: str) -> bool:
        """保存配置到文件"""
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到文件: {config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置到文件失败: {str(e)}")
            return False


# 全局配置实例
_config: Optional[ThirdPartyUnifiedConfig] = None


def get_config() -> ThirdPartyUnifiedConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = ThirdPartyUnifiedConfig.from_env()
        valid, errors = _config.validate()
        if not valid:
            logger.warning(f"配置验证失败: {errors}")
    return _config


def update_config(**kwargs) -> bool:
    """更新配置"""
    global _config
    try:
        if _config is None:
            _config = ThirdPartyUnifiedConfig.from_env()
        
        # 更新配置参数
        for key, value in kwargs.items():
            if hasattr(_config, key):
                setattr(_config, key, value)
            elif hasattr(_config.entry_agent, key):
                setattr(_config.entry_agent, key, value)
            elif hasattr(_config.mcp, key):
                setattr(_config.mcp, key, value)
            elif hasattr(_config.http, key):
                setattr(_config.http, key, value)
            else:
                logger.warning(f"未知的配置参数: {key}")
        
        # 验证更新后的配置
        valid, errors = _config.validate()
        if valid:
            logger.info("配置更新成功")
            return True
        else:
            logger.error(f"配置更新失败，验证不通过: {errors}")
            return False
            
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        return False


def reset_config():
    """重置配置"""
    global _config
    _config = None
    logger.info("配置已重置")


if __name__ == "__main__":
    # 测试配置管理
    print("=== 第三方应用统一配置管理测试 ===")
    
    # 创建配置
    config = ThirdPartyUnifiedConfig.from_env()
    print(f"当前配置: {json.dumps(config.to_dict(), ensure_ascii=False, indent=2)}")
    
    # 验证配置
    valid, errors = config.validate()
    if valid:
        print("✅ 配置验证通过")
    else:
        print(f"❌ 配置验证失败: {errors}")
    
    # 更新配置
    if update_config():
        print("✅ 配置更新成功")
    else:
        print("❌ 配置更新失败")

