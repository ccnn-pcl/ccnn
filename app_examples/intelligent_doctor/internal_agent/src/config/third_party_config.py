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
第三方应用交互配置管理
====================

管理第三方应用交互的各种配置参数，支持环境变量和配置文件两种方式。

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
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ThirdPartyMode(str, Enum):
    """第三方应用模式"""
    SIMULATION = "simulation"  # 模拟模式
    REAL_API = "real_api"      # 真实API模式
    HYBRID = "hybrid"          # 混合模式

@dataclass
class ThirdPartyConfig:
    """第三方应用配置"""
    
    # 基础配置
    mode: str = "simulation"
    enable_third_party: bool = True
    enable_logging: bool = True
    
    # API配置
    data_proxy_url: str = "http://data-proxy-app:9000"
    database_storage_url: str = "http://database-storage:8000"
    data_proxy_api_key: str = ""
    database_storage_api_key: str = ""
    
    # 超时和重试配置
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    
    # 数据增强配置
    enable_data_enhancement: bool = True
    data_enhancement_threshold: float = 0.7
    fallback_to_local: bool = True
    
    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 缓存生存时间（秒）
    cache_size: int = 1000  # 缓存大小
    
    # 监控配置
    enable_monitoring: bool = True
    monitoring_interval: int = 60  # 监控间隔（秒）
    
    @classmethod
    def from_env(cls) -> 'ThirdPartyConfig':
        """从环境变量创建配置"""
        return cls(
            mode=os.getenv("THIRD_PARTY_MODE", "simulation"),
            enable_third_party=os.getenv("THIRD_PARTY_ENABLE", "true").lower() == "true",
            enable_logging=os.getenv("THIRD_PARTY_ENABLE_LOGGING", "true").lower() == "true",
            
            data_proxy_url=os.getenv("DATA_PROXY_APP_URL", "http://data-proxy-app:9000"),
            database_storage_url=os.getenv("DATABASE_STORAGE_URL", "http://database-storage:8000"),
            data_proxy_api_key=os.getenv("DATA_PROXY_API_KEY", ""),
            database_storage_api_key=os.getenv("DATABASE_STORAGE_API_KEY", ""),
            
            timeout=int(os.getenv("THIRD_PARTY_TIMEOUT", "30")),
            retry_count=int(os.getenv("THIRD_PARTY_RETRY_COUNT", "3")),
            retry_delay=float(os.getenv("THIRD_PARTY_RETRY_DELAY", "1.0")),
            
            enable_data_enhancement=os.getenv("THIRD_PARTY_ENABLE_DATA_ENHANCEMENT", "true").lower() == "true",
            data_enhancement_threshold=float(os.getenv("THIRD_PARTY_DATA_ENHANCEMENT_THRESHOLD", "0.7")),
            fallback_to_local=os.getenv("THIRD_PARTY_FALLBACK_TO_LOCAL", "true").lower() == "true",
            
            enable_cache=os.getenv("THIRD_PARTY_ENABLE_CACHE", "true").lower() == "true",
            cache_ttl=int(os.getenv("THIRD_PARTY_CACHE_TTL", "3600")),
            cache_size=int(os.getenv("THIRD_PARTY_CACHE_SIZE", "1000")),
            
            enable_monitoring=os.getenv("THIRD_PARTY_ENABLE_MONITORING", "true").lower() == "true",
            monitoring_interval=int(os.getenv("THIRD_PARTY_MONITORING_INTERVAL", "60"))
        )
    
    @classmethod
    def from_file(cls, config_file: str) -> 'ThirdPartyConfig':
        """从配置文件创建配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return cls(**config_data)
        except Exception as e:
            logger.error(f"从配置文件加载配置失败: {str(e)}")
            return cls.from_env()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def validate(self) -> bool:
        """验证配置"""
        try:
            # 验证模式
            if self.mode not in [mode.value for mode in ThirdPartyMode]:
                logger.error(f"无效的第三方应用模式: {self.mode}")
                return False
            
            # 验证URL
            if not self.data_proxy_url.startswith(('http://', 'https://')):
                logger.error(f"无效的数据代理URL: {self.data_proxy_url}")
                return False
            
            if not self.database_storage_url.startswith(('http://', 'https://')):
                logger.error(f"无效的数据库存储URL: {self.database_storage_url}")
                return False
            
            # 验证超时时间
            if self.timeout <= 0:
                logger.error(f"无效的超时时间: {self.timeout}")
                return False
            
            # 验证重试次数
            if self.retry_count < 0:
                logger.error(f"无效的重试次数: {self.retry_count}")
                return False
            
            # 验证阈值
            if not 0 <= self.data_enhancement_threshold <= 1:
                logger.error(f"无效的数据增强阈值: {self.data_enhancement_threshold}")
                return False
            
            logger.info("配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return False
    
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
_config: Optional[ThirdPartyConfig] = None

def get_config() -> ThirdPartyConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = ThirdPartyConfig.from_env()
        if not _config.validate():
            logger.warning("配置验证失败，使用默认配置")
            _config = ThirdPartyConfig()
    return _config

def update_config(**kwargs) -> bool:
    """更新配置"""
    global _config
    try:
        if _config is None:
            _config = ThirdPartyConfig.from_env()
        
        # 更新配置参数
        for key, value in kwargs.items():
            if hasattr(_config, key):
                setattr(_config, key, value)
            else:
                logger.warning(f"未知的配置参数: {key}")
        
        # 验证更新后的配置
        if _config.validate():
            logger.info("配置更新成功")
            return True
        else:
            logger.error("配置更新失败，验证不通过")
            return False
            
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        return False

def reset_config():
    """重置配置"""
    global _config
    _config = None
    logger.info("配置已重置")

# 环境变量示例
ENV_EXAMPLE = """
# 第三方应用交互配置示例
# 复制到 .env 文件中使用

# 基础配置
THIRD_PARTY_MODE=simulation
THIRD_PARTY_ENABLE=true
THIRD_PARTY_ENABLE_LOGGING=true

# API配置
DATA_PROXY_APP_URL=http://data-proxy-app:9000
DATABASE_STORAGE_URL=http://database-storage:8000
DATA_PROXY_API_KEY=your_data_proxy_api_key
DATABASE_STORAGE_API_KEY=your_database_storage_api_key

# 超时和重试配置
THIRD_PARTY_TIMEOUT=30
THIRD_PARTY_RETRY_COUNT=3
THIRD_PARTY_RETRY_DELAY=1.0

# 数据增强配置
THIRD_PARTY_ENABLE_DATA_ENHANCEMENT=true
THIRD_PARTY_DATA_ENHANCEMENT_THRESHOLD=0.7
THIRD_PARTY_FALLBACK_TO_LOCAL=true

# 缓存配置
THIRD_PARTY_ENABLE_CACHE=true
THIRD_PARTY_CACHE_TTL=3600
THIRD_PARTY_CACHE_SIZE=1000

# 监控配置
THIRD_PARTY_ENABLE_MONITORING=true
THIRD_PARTY_MONITORING_INTERVAL=60
"""

if __name__ == "__main__":
    # 测试配置管理
    print("=== 第三方应用交互配置管理测试 ===")
    
    # 创建配置
    config = ThirdPartyConfig.from_env()
    print(f"当前配置: {config.to_dict()}")
    
    # 验证配置
    if config.validate():
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败")
    
    # 更新配置
    if update_config(mode="hybrid", timeout=60):
        print("✅ 配置更新成功")
    else:
        print("❌ 配置更新失败")
    
    # 保存配置
    if config.save_to_file("third_party_config.json"):
        print("✅ 配置保存成功")
    else:
        print("❌ 配置保存失败")
    
    print("\n=== 环境变量示例 ===")
    print(ENV_EXAMPLE)
