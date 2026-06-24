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
LLM调用器 (LLMCaller)
====================

提供统一的LLM调用接口。

主要功能：
1. 统一的LLM调用接口
2. 多模型支持
3. 错误处理和重试
4. 调用统计和监控

作者: QSIR
版本: 1.0
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import time


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0


class LLMCaller:
    """
    LLM调用器
    
    提供统一的LLM调用接口，支持多种模型提供商。
    """
    
    def __init__(self, config: LLMConfig):
        """
        初始化LLM调用器
        
        参数：
            config (LLMConfig): LLM配置
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.call_count = 0
        self.total_tokens = 0
        self.total_time = 0.0
        
        # 初始化模型调用函数
        self._init_model_caller()
        
        self.logger.info(f"[{self.__class__.__name__}] 初始化完成，提供商: {config.provider}")
    
    def _init_model_caller(self):
        """初始化模型调用函数"""
        try:
            # 尝试导入现有的LLM调用函数
            from llm_caller import call_llm
            self.caller = call_llm
            self.logger.info(f"[{self.__class__.__name__}] 使用现有LLM调用函数")
        except ImportError:
            # 如果导入失败，创建基础实现
            self.caller = self._default_caller
            self.logger.warning(f"[{self.__class__.__name__}] 使用默认LLM调用实现")
    
    async def call(self, prompt: str, model_config: Optional[Dict[str, Any]] = None) -> str:
        """
        调用LLM
        
        参数：
            prompt (str): 提示词
            model_config (Dict[str, Any], optional): 模型配置
            
        返回：
            str: LLM响应
        """
        start_time = time.time()
        
        try:
            # 使用提供的配置或默认配置
            config = model_config or self.config.__dict__
            
            # 调用LLM
            response = await self._call_with_retry(prompt, config)
            
            # 更新统计信息
            self._update_stats(start_time)
            
            return response
            
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] LLM调用失败: {str(e)}")
            raise
    
    async def _call_with_retry(self, prompt: str, config: Dict[str, Any]) -> str:
        """
        带重试的LLM调用
        
        参数：
            prompt (str): 提示词
            config (Dict[str, Any]): 配置
            
        返回：
            str: LLM响应
        """
        last_error = None
        
        for attempt in range(self.config.retry_count):
            try:
                if asyncio.iscoroutinefunction(self.caller):
                    response = await self.caller(prompt, config)
                else:
                    response = self.caller(prompt, config)
                
                return response
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"[{self.__class__.__name__}] 第{attempt + 1}次调用失败: {str(e)}")
                
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        # 所有重试都失败
        raise Exception(f"LLM调用失败，已重试{self.config.retry_count}次: {str(last_error)}")
    
    async def _default_caller(self, prompt: str, config: Dict[str, Any]) -> str:
        """
        默认LLM调用实现
        
        参数：
            prompt (str): 提示词
            config (Dict[str, Any]): 配置
            
        返回：
            str: 模拟响应
        """
        # 模拟LLM调用
        await asyncio.sleep(0.1)
        
        # 根据提示词生成模拟响应
        if "诊断" in prompt or "分析" in prompt:
            return "基于您提供的信息，建议您咨询专业医生进行详细诊断。"
        elif "影像" in prompt:
            return "影像分析需要专业设备，建议到正规医院进行检查。"
        else:
            return "感谢您的咨询，建议您咨询专业医生获取详细建议。"
    
    def _update_stats(self, start_time: float):
        """更新统计信息"""
        self.call_count += 1
        self.total_time += time.time() - start_time
    
    def get_stats(self) -> Dict[str, Any]:
        """获取调用统计信息"""
        return {
            "call_count": self.call_count,
            "total_tokens": self.total_tokens,
            "total_time": self.total_time,
            "average_time": self.total_time / self.call_count if self.call_count > 0 else 0,
            "provider": self.config.provider,
            "model": self.config.model
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.call_count = 0
        self.total_tokens = 0
        self.total_time = 0.0
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置信息"""
        return self.config.__dict__.copy()
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"[{self.__class__.__name__}] 配置更新: {key} = {value}")


# 全局LLM调用器实例
_global_llm_caller = None


def get_llm_caller(config: Optional[LLMConfig] = None) -> LLMCaller:
    """
    获取全局LLM调用器实例
    
    参数：
        config (LLMConfig, optional): 配置
        
    返回：
        LLMCaller: LLM调用器实例
    """
    global _global_llm_caller
    
    if _global_llm_caller is None:
        if config is None:
            # 使用默认配置
            config = LLMConfig(
                provider="qwen",
                api_key="default",
                model="qwen-turbo"
            )
        _global_llm_caller = LLMCaller(config)
    
    return _global_llm_caller


async def call_llm(prompt: str, model_config: Dict[str, Any]) -> str:
    """
    全局LLM调用函数
    
    参数：
        prompt (str): 提示词
        model_config (Dict[str, Any]): 模型配置
        
    返回：
        str: LLM响应
    """
    caller = get_llm_caller()
    return await caller.call(prompt, model_config)
