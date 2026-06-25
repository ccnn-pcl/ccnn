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
强制数据代理触发器 (ForcedDataProxyTrigger)
==========================================

对于演示模式，强制触发数据代理请求。

作者: QSIR
版本: 1.0
"""

import logging
from typing import Dict, Any, List, Optional
from agents.utils.shared_context import SharedContext
from agents.coordinator.data_proxy_client import DataProxyClient, DataProxyConfig


class ForcedDataProxyTrigger:
    """强制数据代理触发器"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化强制数据代理触发器
        
        参数:
            token (str, optional): JWT token，用于 EntryAgent 认证
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化数据代理客户端配置
        config = DataProxyConfig(token=token)  # 传递 token 到配置
        self.data_proxy_client = DataProxyClient(config)
        
        if token:
            self.logger.info(f"[ForcedDataProxyTrigger] 初始化完成，已设置 token: {token[:20]}...")
        else:
            self.logger.info(f"[ForcedDataProxyTrigger] 初始化完成（未设置 token）")
    
    async def force_trigger_data_proxy(
        self,
        user_input: str,
        user_id: str,
        intent: str,
        shared_context: Optional[SharedContext] = None,
        token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        强制触发数据代理请求（使用识别的意图）
        
        参数:
            user_input: 用户输入
            user_id: 用户ID
            intent: 识别的意图（如：内科咨询、外科咨询等）
            shared_context: 共享上下文（可选）
            token: JWT token，用于 EntryAgent 认证（可选，如果提供则更新配置）
            
        返回:
            List[Dict[str, Any]]: 数据地址列表
        """
        try:
            # 如果提供了 token，更新 DataProxyClient 的配置
            if token and token != self.data_proxy_client.config.token:
                self.logger.info(f"[ForcedDataProxyTrigger] 更新 token: {token[:20]}...")
                self.data_proxy_client.config.token = token
                # 如果 EntryAgent 适配器已初始化，更新其 token
                if self.data_proxy_client.entry_agent_adapter:
                    self.data_proxy_client.entry_agent_adapter.token = token
                    self.logger.info(f"[ForcedDataProxyTrigger] 已更新 EntryAgent 适配器的 token")
            
            self.logger.info(f"[ForcedDataProxyTrigger] 强制触发数据代理请求，意图: {intent}")
            
            # 打印请求信息
            print("\n" + "=" * 80)
            print("[演示模式] 强制触发数据代理请求")
            print("=" * 80)
            print(f"意图: {intent}")
            print(f"用户ID: {user_id}")
            print(f"用户输入: {user_input[:100]}..." if len(user_input) > 100 else f"用户输入: {user_input}")
            print(f"数据代理URL: {self.data_proxy_client.config.base_url}")
            if token:
                print(f"Token: {token[:30]}...")
            print("-" * 80)
            
            # 如果没有共享上下文，创建一个新的
            if shared_context is None:
                shared_context = SharedContext()
            
            # 使用识别的意图，而不是固定意图
            # 根据意图请求对应专科的数据
            # 例如：
            # - "内科咨询" → 请求内科相关数据（病史、用药、化验等）
            # - "外科咨询" → 请求外科相关数据（手术记录、影像等）
            # - "影像分析" → 请求影像相关数据  # 暂时注释掉影像分析
            
            # 调用数据代理客户端
            print(f"[演示模式] 正在向数据代理应用发送请求...")
            async with self.data_proxy_client:
                data_addresses = await self.data_proxy_client.interact_with_context(
                    intent=intent,  # 使用识别的意图
                    user_input=user_input,
                    user_id=user_id,
                    shared_context=shared_context,
                    ask_user_callback=None  # 演示模式不需要用户交互
                )
            
            # 打印响应信息（详细调试）
            print("-" * 80)
            print(f"[演示模式] 数据代理请求完成")
            print(f"获取到数据地址数量: {len(data_addresses)}")
            if data_addresses:
                print("\n[调试] 第一轮数据地址详细信息:")
                print("=" * 80)
                try:
                    import json
                    for i, addr in enumerate(data_addresses, 1):
                        print(f"\n数据地址 {i}:")
                        print(json.dumps(addr, ensure_ascii=False, indent=2))
                except Exception as e:
                    print(f"  [错误] 打印数据地址失败: {e}")
                    print("数据地址列表:")
                    for i, addr in enumerate(data_addresses, 1):
                        print(f"  {i}. 类型: {addr.get('data_type', 'N/A')}, 地域: {addr.get('location', 'N/A')}, 地址: {addr.get('address', 'N/A')[:50]}...")
                print("=" * 80)
            else:
                print("  [警告] 未获取到数据地址")
            print("=" * 80 + "\n")
            
            self.logger.info(f"[ForcedDataProxyTrigger] 获取到 {len(data_addresses)} 个数据地址")
            return data_addresses
            
        except Exception as e:
            self.logger.error(f"[ForcedDataProxyTrigger] 强制触发数据代理请求失败: {str(e)}", exc_info=True)
            return []

