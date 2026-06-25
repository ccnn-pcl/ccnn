#!/usr/bin/env python3
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
模型配置类
==========

定义系统中使用的模型配置类
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ModelConfig:
    """模型配置类"""
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[list] = None
    api_key: Optional[str] = "sk-0otde0b7ca4d399f92200d73c345129eb9ab73766d6Y4xOy"
    base_url: Optional[str] = "https://api.gptsapi.net/v1"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        config = {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
        
        if self.stop is not None:
            config["stop"] = self.stop
            
        if self.api_key is not None:
            config["api_key"] = self.api_key
            
        if self.base_url is not None:
            config["base_url"] = self.base_url
            
        return config
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ModelConfig':
        """从字典创建配置"""
        return cls(
            model_name=config_dict.get("model", "gpt-3.5-turbo"),
            temperature=config_dict.get("temperature", 0.7),
            max_tokens=config_dict.get("max_tokens", 1000),
            top_p=config_dict.get("top_p", 1.0),
            frequency_penalty=config_dict.get("frequency_penalty", 0.0),
            presence_penalty=config_dict.get("presence_penalty", 0.0),
            stop=config_dict.get("stop"),
            api_key=config_dict.get("api_key"),
            base_url=config_dict.get("base_url")
        )

# 默认配置
DEFAULT_CONFIG = ModelConfig(
    model_name="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1000
)

# 医疗专用配置
MEDICAL_CONFIG = ModelConfig(
    model_name="huatuogpt",
    base_url="http://192.168.64.60:32508/v1",
    api_key="custom",
    temperature=0.3,  # 更保守的温度设置
    max_tokens=1500,  # 更长的回复
    top_p=0.9
)

# 对话专用配置
CHAT_CONFIG = ModelConfig(
    model_name="qwen-3b",
    base_url="http://192.168.64.60:32568/v1",
    api_key="custom",
    temperature=0.8,  # 更有创造性的对话
    max_tokens=800,
    top_p=0.95
)

# 华佗GPT-1模型配置
HUATUO_CONFIG = ModelConfig(
    model_name="huatuogpt",
    base_url="http://192.168.64.60:32508/v1",
    api_key="custom",
    temperature=0.7,
    max_tokens=1000
)

# 华佗GPT-2模型配置
HUATUO2_CONFIG = ModelConfig(
    model_name="huatuogpt-2",
    base_url="http://172.22.11.169:30466/v1",
    api_key="custom",
    temperature=0.7,
    max_tokens=1000
)

# 通义千问模型配置
QWEN_CONFIG = ModelConfig(
    model_name="qwen-3b",
    base_url="http://192.168.64.60:32568/v1",
    api_key="custom",
    temperature=0.7,
    max_tokens=1000
)

# 配置字典，方便按名称获取配置
CONFIG_DICT = {
    "default": DEFAULT_CONFIG,
    "medical": MEDICAL_CONFIG,
    "chat": CHAT_CONFIG,
    "huatuo": HUATUO_CONFIG,
    "huatuo2": HUATUO2_CONFIG,
    "qwen": QWEN_CONFIG
}

def get_config(config_name: str = "default") -> ModelConfig:
    """
    根据配置名称获取模型配置
    
    参数：
        config_name (str): 配置名称，可选值：
            - "default": 默认配置
            - "medical": 医疗专用配置
            - "chat": 对话专用配置
            - "huatuo": 华佗GPT-1配置
            - "huatuo2": 华佗GPT-2配置
            - "qwen": 通义千问配置
    
    返回：
        ModelConfig: 对应的模型配置
    """
    return CONFIG_DICT.get(config_name, DEFAULT_CONFIG)
