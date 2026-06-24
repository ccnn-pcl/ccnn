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
数据代理客户端（重构版）
========================

负责与第三方数据代理应用进行多轮对话，获取数据地址。

主要功能：
1. 多轮对话管理
2. 上下文感知的请求构建
3. 对话状态管理
4. 错误处理和重试

作者: QSIR
版本: 2.0 - 重构版（支持多轮协调）
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import os

from agents.utils.shared_context import SharedContext

# 统一配置管理器（可选）
try:
    from config.third_party_unified_config import ThirdPartyUnifiedConfig, get_config
    from config.validator import ConfigValidator
    UNIFIED_CONFIG_AVAILABLE = True
except ImportError:
    UNIFIED_CONFIG_AVAILABLE = False
    logging.warning("[DataProxyClient] 统一配置管理器未找到，将使用传统配置方式")

# 标准A2A SDK EntryAgent支持
try:
    from shared.agents.coordinator.entry_agent_adapter import EntryAgentAdapter
    ENTRY_AGENT_AVAILABLE = True
except ImportError:
    ENTRY_AGENT_AVAILABLE = False
    logging.warning("[DataProxyClient] EntryAgent适配器未找到，将使用自定义A2A协议")


@dataclass
class DataProxyConfig:
    """数据代理客户端配置"""
    base_url: str = os.getenv("DATA_PROXY_APP_URL", "http://localhost:9000")
    api_key: str = os.getenv("DATA_PROXY_API_KEY", "")
    timeout: int = int(os.getenv("DATA_PROXY_TIMEOUT", "30"))
    max_rounds: int = 3  # 最大对话轮次
    retry_count: int = 2  # 重试次数
    enable_logging: bool = True
    
    # 标准A2A SDK EntryAgent配置（使用标准TOKEN实现）
    use_entry_agent: bool = os.getenv("USE_ENTRY_AGENT", "false").lower() == "true"
    # Token 用于 EntryAgent 认证（优先使用传入的 token，否则从 URL 或环境变量获取）
    token: Optional[str] = None
    
    # 统一配置管理器（可选，如果提供则优先使用）
    unified_config: Optional[Any] = None


@dataclass
class ConversationState:
    """对话状态"""
    round: int = 0
    state: str = "initial"  # initial, requesting, needs_more_info, collecting_info, completed
    data_addresses: List[Dict] = field(default_factory=list)
    conversation_history: List[Dict] = field(default_factory=list)
    
    STATES = {
        "initial": "初始状态",
        "requesting": "请求中",
        "needs_more_info": "需要更多信息",
        "collecting_info": "收集信息中",
        "completed": "完成"
    }


class DataProxyClient:
    """
    数据代理客户端（重构版）
    
    支持多轮对话和上下文感知的请求构建
    """
    
    def __init__(self, config: Optional[DataProxyConfig] = None):
        """
        初始化数据代理客户端
        
        参数：
            config (DataProxyConfig, optional): 客户端配置，如果为None则从统一配置管理器或环境变量读取
        """
        # 如果未提供配置，尝试使用统一配置管理器
        if config is None:
            if UNIFIED_CONFIG_AVAILABLE:
                try:
                    unified_config = get_config()
                    # 从统一配置创建DataProxyConfig
                    config = DataProxyConfig(
                        base_url=unified_config.entry_agent.base_url,
                        api_key="",  # HTTP协议使用
                        timeout=unified_config.entry_agent.timeout,
                        use_entry_agent=unified_config.entry_agent.enabled,
                        token=unified_config.entry_agent.token,  # 从统一配置获取 token
                        unified_config=unified_config
                    )
                    self.logger = logging.getLogger(self.__class__.__name__)
                    self.logger.info("[DataProxyClient] 使用统一配置管理器")
                except Exception as e:
                    self.logger = logging.getLogger(self.__class__.__name__)
                    self.logger.warning(f"[DataProxyClient] 统一配置管理器初始化失败: {e}，使用默认配置")
                    config = DataProxyConfig()
            else:
                config = DataProxyConfig()
        
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 标准A2A SDK EntryAgent适配器
        self.entry_agent_adapter: Optional[EntryAgentAdapter] = None
        
        # 优先初始化EntryAgent适配器（如果启用）
        print(f"\n[DataProxyClient] 初始化EntryAgent适配器...")
        print(f"  USE_ENTRY_AGENT (环境变量): {os.getenv('USE_ENTRY_AGENT', 'false')}")
        print(f"  use_entry_agent (配置): {self.config.use_entry_agent}")
        print(f"  ENTRY_AGENT_AVAILABLE (模块可用): {ENTRY_AGENT_AVAILABLE}")
        if self.config.use_entry_agent and ENTRY_AGENT_AVAILABLE:
            try:
                # 确定使用的 token：优先使用配置中的 token，否则从 URL 或环境变量获取
                token = self.config.token
                if not token:
                    # 尝试从环境变量获取
                    token = os.getenv("DATA_PROXY_TOKEN", None)
                
                # 从base_url中提取user_id（如果URL中包含）
                # 使用配置的超时时间，JSON-RPC服务可能需要更长时间
                self.entry_agent_adapter = EntryAgentAdapter(
                    base_url=self.config.base_url,
                    token=token,  # 传递 token 参数
                    timeout=self.config.timeout
                )
                self.logger.info("[DataProxyClient] EntryAgent适配器已启用（标准A2A SDK）")
                if token:
                    self.logger.info(f"[DataProxyClient] 使用提供的 token: {token[:20]}...")
                print(f"[DataProxyClient] ✅ EntryAgent适配器初始化成功")
            except Exception as e:
                self.logger.warning(f"[DataProxyClient] EntryAgent适配器初始化失败: {str(e)}，将使用自定义A2A协议")
                print(f"[DataProxyClient] ❌ EntryAgent适配器初始化失败: {str(e)}")
                self.entry_agent_adapter = None
        else:
            if not self.config.use_entry_agent:
                print(f"[DataProxyClient] ⚠️ EntryAgent未启用（USE_ENTRY_AGENT=false）")
            if not ENTRY_AGENT_AVAILABLE:
                print(f"[DataProxyClient] ⚠️ EntryAgent模块不可用")
        print()
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def interact_with_context(
        self,
        intent: str,
        user_input: str,
        user_id: str,
        shared_context: Optional[SharedContext] = None,
        ask_user_callback: Optional[Callable[[str], str]] = None
    ) -> List[Dict[str, Any]]:
        """
        基于共享上下文与数据代理应用进行多轮交互
        
        参数：
            intent (str): 意图类型
            user_input (str): 用户输入
            user_id (str): 用户ID
            shared_context (SharedContext, optional): 共享上下文
            ask_user_callback (Callable, optional): 向用户提问的回调函数
            
        返回：
            List[Dict[str, Any]]: 数据地址列表
        """
        conversation_state = ConversationState()
        
        # 如果提供了共享上下文，从上下文中恢复状态
        if shared_context:
            conversation_state.round = shared_context.round_number
            conversation_state.data_addresses = shared_context.get_all_data_addresses()
            conversation_state.conversation_history = shared_context.data_proxy_conversation_history.copy()
        
        while conversation_state.round < self.config.max_rounds:
            conversation_state.round += 1
            
            # 打印交互开始信息
            print(f"\n[数据代理交互] 开始第 {conversation_state.round} 轮交互")
            print(f"  意图: {intent}")
            print(f"  用户输入: {user_input[:100]}..." if len(user_input) > 100 else f"  用户输入: {user_input}")
            
            # 构建请求（包含上下文信息）
            request_data = self._build_request_with_context(
                intent, user_input, user_id, shared_context, conversation_state
            )
            
            # 调用数据代理应用
            response = await self._call_data_proxy_app(request_data)
            
            # 打印交互结果
            print(f"[数据代理交互] 第 {conversation_state.round} 轮交互完成")
            if response.get("data_addresses"):
                print(f"  获取到 {len(response.get('data_addresses', []))} 个数据地址")
            if response.get("needs_more_info"):
                print(f"  需要更多信息: {response.get('question', 'N/A')}")
            print()
            
            # 更新对话历史
            conversation_state.conversation_history.append({
                "round": conversation_state.round,
                "state": conversation_state.state,
                "request": request_data,
                "response": response
            })
            
            # 如果提供了共享上下文，更新上下文
            if shared_context:
                # 更新轮次（确保轮次正确传递）
                shared_context.round_number = conversation_state.round
                
                shared_context.data_proxy_conversation_history.append({
                    "round": conversation_state.round,
                    "request": request_data,
                    "response": response
                })
                
                # 如果响应包含直接医疗数据，存储到共享上下文中
                if response.get("has_direct_data") and response.get("medical_data"):
                    medical_data = response.get("medical_data")
                    shared_context.direct_medical_data = medical_data
                    self.logger.info(f"[DataProxyClient] 将直接医疗数据存储到共享上下文")
                    
                    # 打印详细调试信息（数据代理应用直接返回的数据）
                    round_num = conversation_state.round
                    round_info = f"第{round_num}轮诊断" if round_num > 0 else "诊断"
                    print("\n" + "=" * 80)
                    print(f"[调试] 【{round_info}】数据代理应用直接返回的完整数据")
                    print("=" * 80)
                    print(f"  轮次: {round_num}")
                    print(f"  has_direct_data: {response.get('has_direct_data')}")
                    print(f"  数据地址数量: {len(response.get('data_addresses', []))}")
                    try:
                        import json
                        # 打印完整医疗数据（限制长度以避免输出过长）
                        data_str = json.dumps(medical_data, ensure_ascii=False, indent=2)
                        if len(data_str) > 5000:
                            print(f"\n医疗数据（前5000字符）:")
                            print(data_str[:5000])
                            print(f"\n... (数据过长，已截断，总长度: {len(data_str)} 字符)")
                        else:
                            print(f"\n医疗数据:")
                            print(data_str)
                    except Exception as e:
                        print(f"[错误] 打印医疗数据失败: {e}")
                        print(f"数据类型: {type(medical_data)}")
                        print(f"数据键: {list(medical_data.keys()) if isinstance(medical_data, dict) else 'N/A'}")
                    print("=" * 80 + "\n")
            
            # 处理响应
            if response.get("needs_more_info"):
                # 需要更多信息
                conversation_state.state = "needs_more_info"
                question = response.get("question", "")
                
                if ask_user_callback:
                    # 通过回调向用户提问
                    try:
                        user_answer = await ask_user_callback(question)
                        user_input += f" {user_answer}"
                        conversation_state.state = "collecting_info"
                    except Exception as e:
                        self.logger.error(f"[DataProxyClient] 用户回调失败: {str(e)}")
                        break
                else:
                    # 没有回调函数，无法继续
                    self.logger.warning("[DataProxyClient] 需要更多信息但没有提供回调函数")
                    break
            
            elif response.get("data_addresses"):
                # 获取到数据地址
                new_addresses = response.get("data_addresses", [])
                conversation_state.data_addresses.extend(new_addresses)
                
                # 如果提供了共享上下文，更新数据地址历史
                if shared_context:
                    shared_context.data_addresses_history.append({
                        "round": conversation_state.round,
                        "data_addresses": new_addresses
                    })
                
                if response.get("complete", False):
                    conversation_state.state = "completed"
                    break
            
            elif response.get("success") is False:
                # 请求失败
                self.logger.error(f"[DataProxyClient] 数据代理请求失败: {response.get('message')}")
                break
        
        return conversation_state.data_addresses
    
    def _build_request_with_context(
        self,
        intent: str,
        user_input: str,
        user_id: str,
        shared_context: Optional[SharedContext],
        conversation_state: ConversationState
    ) -> Dict[str, Any]:
        """
        构建包含上下文信息的请求
        
        参数：
            intent (str): 意图类型
            user_input (str): 用户输入
            user_id (str): 用户ID
            shared_context (SharedContext, optional): 共享上下文
            conversation_state (ConversationState): 对话状态
            
        返回：
            Dict[str, Any]: 请求数据
        """
        # 提取症状
        symptoms = self._extract_symptoms(user_input)
        
        # 构建基础请求
        request_data = {
            "intent_type": intent,
            "specialty": self._map_intent_to_specialty(intent),
            "user_id": user_id,
            "symptoms": symptoms,
            "request_id": f"req_{user_id}_{int(datetime.now().timestamp())}",
            "priority": "medium"
        }
        
        # 构建上下文信息
        context = {
            "symptom_description": user_input,
            "conversation_round": conversation_state.round
        }
        
        # 如果有共享上下文，添加更多上下文信息
        if shared_context:
            context.update({
                "previous_data_addresses": shared_context.get_all_data_addresses(),
                "specialist_requests": shared_context.specialist_requests,
                "diagnosis_results": shared_context.diagnosis_results_history[-3:] if shared_context.diagnosis_results_history else [],
                "conversation_history": conversation_state.conversation_history[-2:]  # 最近2轮对话
            })
        
        request_data["context"] = context
        
        return request_data
    
    async def _call_data_proxy_app(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        【✅ 真实第三方应用调用】调用数据代理应用API
        
        支持标准A2A SDK EntryAgent和HTTP协议，按优先级顺序尝试。
        
        ════════════════════════════════════════════════════════════
        【配置说明】
        ════════════════════════════════════════════════════════════
        
        此方法调用真实的第三方数据代理应用。
        
        标准A2A SDK EntryAgent配置（最高优先级）：
        - USE_ENTRY_AGENT: 是否使用标准A2A SDK的EntryAgent（默认: false）
        - DATA_PROXY_APP_URL: 数据代理应用URL（可包含user_id参数，如: http://localhost:9090?user_id=111）
        
        HTTP协议配置（降级）：
        - DATA_PROXY_APP_URL: 数据代理应用URL（默认: http://localhost:9000）
        - DATA_PROXY_API_KEY: API密钥（可选）
        - DATA_PROXY_TIMEOUT: 超时时间（默认: 30秒）
        
        模拟测试模式：
        - 如果使用模拟模式，请通过 backend/api/third_party_reserve.py 的
          ThirdPartyClient 进行模拟测试
        - 设置环境变量 THIRD_PARTY_MODE=simulation
        
        详细说明请参考：docs/第三方应用模拟测试与真实切换指南.md
        ════════════════════════════════════════════════════════════
        
        参数：
            request_data (Dict[str, Any]): 请求数据
            
        返回：
            Dict[str, Any]: 响应数据，包含：
                - success: 是否成功
                - data_addresses: 数据地址列表
                - needs_more_info: 是否需要更多信息
                - question: 需要询问用户的问题
        """
        # ========== 打印协议选择信息 ==========
        print("\n" + "=" * 80)
        print("[DataProxyClient] 开始调用数据代理应用")
        print("=" * 80)
        print(f"配置状态:")
        print(f"  USE_ENTRY_AGENT (环境变量): {os.getenv('USE_ENTRY_AGENT', 'false')}")
        print(f"  use_entry_agent (配置): {self.config.use_entry_agent}")
        print(f"  entry_agent_adapter (已初始化): {self.entry_agent_adapter is not None}")
        print(f"  ENTRY_AGENT_AVAILABLE (模块可用): {ENTRY_AGENT_AVAILABLE}")
        print(f"  base_url: {self.config.base_url}")
        print("=" * 80)
        print()
        
        # 最高优先级：使用标准A2A SDK的EntryAgent（通过prompt进行交互，使用标准TOKEN）
        if self.config.use_entry_agent and self.entry_agent_adapter and ENTRY_AGENT_AVAILABLE:
            print("[DataProxyClient] ✅ 使用标准A2A SDK EntryAgent协议（标准TOKEN实现）")
            print()
            try:
                return await self._call_via_entry_agent(request_data)
            except Exception as e:
                self.logger.warning(f"[DataProxyClient] EntryAgent调用失败: {str(e)}")
                print(f"[DataProxyClient] ❌ EntryAgent调用失败: {str(e)}")
                # 自动降级到HTTP协议
                self.logger.info("[DataProxyClient] 降级到HTTP协议")
                print("[DataProxyClient] 降级到HTTP协议")
        
        # 使用HTTP协议（默认或降级）
        print("[DataProxyClient] ✅ 使用HTTP协议（默认或降级）")
        print()
        return await self._call_via_http(request_data)
    
    async def _call_via_entry_agent(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """通过标准A2A SDK的EntryAgent调用数据代理应用（使用prompt）"""
        round_num = request_data.get('context', {}).get('conversation_round', 0)
        self.logger.info(f"[DataProxyClient] 使用EntryAgent调用数据代理应用，轮次: {round_num}")
        
        # 增强日志：明确标识第二轮请求
        if round_num >= 2:
            self.logger.info(f"[DataProxyClient] ⚠️ 第二轮诊断请求 - 使用EntryAgent发送到数据代理应用")
            print(f"\n[DataProxyClient] ⚠️ 第二轮诊断请求 - 使用EntryAgent发送到数据代理应用")
            print(f"  轮次: {round_num}")
            specialist_requests = request_data.get('context', {}).get('specialist_requests', [])
            if specialist_requests:
                print(f"  数据需求: {specialist_requests}")
            print()
        
        # ========== 打印医疗应用发送的请求数据 ==========
        print("\n" + "=" * 80)
        if round_num >= 2:
            print("[医疗应用] 发送给EntryAgent的请求数据（第二轮诊断 - 健康监测数据）")
        else:
            print("[医疗应用] 发送给EntryAgent的请求数据")
        print("=" * 80)
        try:
            import json
            print(json.dumps(request_data, ensure_ascii=False, indent=2))
        except Exception:
            print(str(request_data))
        print("=" * 80)
        print()
        
        # 打印数据代理请求信息（EntryAgent）
        if round_num >= 2:
            print(f"\n[数据代理请求] 第 {round_num} 轮 (标准A2A SDK EntryAgent) - ⚠️ 第二轮诊断请求")
        else:
            print(f"\n[数据代理请求] 第 {round_num} 轮 (标准A2A SDK EntryAgent)")
        print(f"  协议: 标准A2A SDK (EntryAgent)")
        print(f"  目标URL: {self.config.base_url}")
        print(f"  意图: {request_data.get('intent_type', 'N/A')}")
        print(f"  专科: {request_data.get('specialty', 'N/A')}")
        print(f"  用户ID: {request_data.get('user_id', 'N/A')}")
        print(f"  症状: {request_data.get('symptoms', [])}")
        print(f"  请求ID: {request_data.get('request_id', 'N/A')}")
        context = request_data.get('context', {})
        if context:
            print(f"  上下文:")
            print(f"    - 对话轮次: {context.get('conversation_round', 'N/A')} {'⚠️ 第二轮' if round_num >= 2 else ''}")
            print(f"    - 症状描述: {context.get('symptom_description', 'N/A')[:100]}..." if len(context.get('symptom_description', '')) > 100 else f"    - 症状描述: {context.get('symptom_description', 'N/A')}")
            specialist_requests = context.get('specialist_requests', [])
            if specialist_requests:
                print(f"    - 专科医生数据需求: {len(specialist_requests)} 个")
                for i, req in enumerate(specialist_requests, 1):
                    if isinstance(req, dict):
                        data_type = req.get('data_type', 'N/A')
                        print(f"      {i}. 数据类型: {data_type}")
                        if data_type == "健康监测数据":
                            print(f"         ⚠️ 健康监测数据需求")
        print()
        
        # 调用EntryAgent适配器
        print(f"[DataProxyClient] 开始调用EntryAgent适配器...")
        response = await self.entry_agent_adapter.invoke(request_data)
        print(f"[DataProxyClient] EntryAgent适配器调用完成")
        
        # ========== 打印EntryAgent返回的响应数据 ==========
        print("\n" + "=" * 80)
        print("[EntryAgent] 返回给医疗应用的响应数据")
        print("=" * 80)
        try:
            import json
            print(json.dumps(response, ensure_ascii=False, indent=2))
        except Exception:
            print(str(response))
        print("=" * 80)
        print()
        
        # 打印响应信息
        print(f"[数据代理响应] 第 {round_num} 轮 - 成功 (标准A2A SDK EntryAgent)")
        print(f"  成功: {response.get('success', False)}")
        print(f"  消息: {response.get('message', 'N/A')}")
        data_addresses = response.get("data_addresses", [])
        print(f"  数据地址数量: {len(data_addresses)}")
        if data_addresses:
            print(f"  数据地址详情:")
            for i, addr in enumerate(data_addresses, 1):
                access_token = addr.get('access_token', '')
                access_token_preview = access_token[:20] + "..." if access_token and len(access_token) > 20 else (access_token if access_token else "(空)")
                print(f"    {i}. 类型: {addr.get('data_type', 'N/A')}")
                print(f"       地域: {addr.get('location', 'N/A')}")
                print(f"       医院: {addr.get('hospital', 'N/A')}")
                print(f"       address: {addr.get('address', 'N/A')}")
                print(f"       access_token: {access_token_preview}")
                if not access_token:
                    print(f"       ⚠️  警告: 此数据地址缺少access_token")
        if response.get('needs_more_info'):
            print(f"  需要更多信息: {response.get('question', 'N/A')}")
        print()
        
        # 确保响应格式符合预期
        response_data = {
            "success": response.get("success", True),
            "message": response.get("message", "数据地址匹配成功"),
            "data_addresses": response.get("data_addresses", []),
            "needs_more_info": response.get("needs_more_info", False),
            "question": response.get("question"),
            "complete": response.get("complete", True),
            "request_id": request_data.get("request_id", "")
        }
        
        # 如果包含直接数据，添加到响应中
        if response.get("has_direct_data") and response.get("medical_data"):
            response_data["medical_data"] = response.get("medical_data")
            response_data["has_direct_data"] = True
            self.logger.info(f"[DataProxyClient] 检测到直接医疗数据，将跳过数据存储服务请求")
        
        # ========== 打印最终返回给医疗应用的响应 ==========
        print("\n" + "=" * 80)
        print("[医疗应用] 最终返回的响应数据")
        print("=" * 80)
        try:
            import json
            print(json.dumps(response_data, ensure_ascii=False, indent=2))
        except Exception:
            print(str(response_data))
        print("=" * 80)
        print()
        
        return response_data
    
    async def _call_via_http(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """通过HTTP协议调用数据代理应用（原有实现）"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        
        url = f"{self.config.base_url}/api/v1/data-proxy/request"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        try:
            round_num = request_data.get('context', {}).get('conversation_round', 0)
            self.logger.info(f"[DataProxyClient] 使用HTTP协议调用数据代理应用，轮次: {round_num}")
            
            # 打印请求信息
            print(f"\n[数据代理请求] 第 {round_num} 轮 (HTTP)")
            print(f"  URL: {url}")
            print(f"  意图: {request_data.get('intent_type', 'N/A')}")
            print(f"  专科: {request_data.get('specialty', 'N/A')}")
            print(f"  用户ID: {request_data.get('user_id', 'N/A')}")
            print(f"  症状: {request_data.get('symptoms', [])}")
            print(f"  请求ID: {request_data.get('request_id', 'N/A')}")
            
            async with self.session.post(url, json=request_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # 打印响应信息
                    print(f"[数据代理响应] 第 {round_num} 轮 - 成功 (HTTP)")
                    print(f"  状态码: {response.status}")
                    print(f"  成功: {result.get('success', False)}")
                    print(f"  数据地址数量: {len(result.get('data_addresses', []))}")
                    
                    # 检测是否包含直接医疗数据
                    has_direct_data = result.get("has_direct_data", False)
                    medical_data = result.get("medical_data")
                    if has_direct_data and medical_data:
                        print(f"  ✅ 包含直接医疗数据（跳过数据存储服务请求）")
                        print(f"  数据类型: {medical_data.get('available_data_types', [])}")
                    print()
                    
                    self.logger.info(f"[DataProxyClient] HTTP协议调用成功")
                    if has_direct_data and medical_data:
                        self.logger.info(f"[DataProxyClient] 检测到直接医疗数据，将跳过数据存储服务请求")
                    
                    return result
                else:
                    error_text = await response.text()
                    
                    # 打印错误信息
                    print(f"[数据代理响应] 第 {round_num} 轮 - 失败 (HTTP)")
                    print(f"  状态码: {response.status}")
                    print(f"  错误信息: {error_text[:200]}...")
                    print()
                    
                    self.logger.error(f"[DataProxyClient] HTTP协议调用失败: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "message": f"HTTP错误: {response.status}",
                        "data_addresses": []
                    }
        
        except asyncio.TimeoutError:
            print(f"[数据代理响应] 请求超时 (HTTP)")
            print()
            self.logger.error(f"[DataProxyClient] HTTP协议调用超时")
            return {
                "success": False,
                "message": "请求超时",
                "data_addresses": []
            }
        
        except Exception as e:
            print(f"[数据代理响应] 请求异常: {str(e)} (HTTP)")
            print()
            self.logger.error(f"[DataProxyClient] HTTP协议调用异常: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "data_addresses": []
            }
    
    def _extract_symptoms(self, user_input: str) -> List[str]:
        """
        从用户输入中提取症状关键词
        
        参数：
            user_input (str): 用户输入
            
        返回：
            List[str]: 症状关键词列表
        """
        # 简单的关键词提取（实际可以使用更复杂的NLP方法）
        common_symptoms = [
            "头痛", "发烧", "咳嗽", "胸闷", "腹痛", "恶心", "呕吐",
            "心慌", "心跳", "头晕", "乏力", "失眠", "食欲不振"
        ]
        
        symptoms = []
        for symptom in common_symptoms:
            if symptom in user_input:
                symptoms.append(symptom)
        
        return symptoms
    
    def _map_intent_to_specialty(self, intent: str) -> str:
        """
        将意图映射到专科类型
        
        参数：
            intent (str): 意图类型
            
        返回：
            str: 专科类型
        """
        mapping = {
            "内科咨询": "内科",
            "外科咨询": "外科",
            "影像分析": "影像科",
            "药物查询": "内科",
            "一般问题": "内科",
            "未知": "内科",
        }
        
        return mapping.get(intent, "内科")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        返回：
            Dict[str, Any]: 健康状态
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            )
        
        try:
            url = f"{self.config.base_url}/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return {"status": "healthy", "message": "数据代理应用正常"}
                else:
                    return {"status": "unhealthy", "message": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}


# 便捷函数：通过内部API调用（兼容现有系统）
async def call_data_proxy_via_internal_api(
    intent: str,
    user_input: str,
    user_id: str,
    shared_context: Optional[SharedContext] = None,
    base_url: str = "http://localhost:8000"
) -> List[Dict[str, Any]]:
    """
    通过内部API调用数据代理应用（兼容现有系统）
    
    参数：
        intent (str): 意图类型
        user_input (str): 用户输入
        user_id (str): 用户ID
        shared_context (SharedContext, optional): 共享上下文
        base_url (str): 内部API基础URL
        
    返回：
        List[Dict[str, Any]]: 数据地址列表
    """
    async with aiohttp.ClientSession() as session:
        # 构建请求
        request_data = {
            "intent_type": intent,
            "specialty": "内科" if "内科" in intent else "外科" if "外科" in intent else "影像科",
            "user_id": user_id,
            "symptoms": [],
            "context": {
                "symptom_description": user_input,
                "conversation_round": shared_context.round_number if shared_context else 1,
                "previous_data_addresses": shared_context.get_all_data_addresses() if shared_context else [],
                "specialist_requests": shared_context.specialist_requests if shared_context else []
            },
            "request_id": f"req_{user_id}_{int(datetime.now().timestamp())}",
            "priority": "medium"
        }
        
        # 调用内部API
        url = f"{base_url}/api/v1/third-party/request-data-proxy"
        
        try:
            async with session.post(url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        return result.get("data_addresses", [])
                    else:
                        logging.warning(f"[call_data_proxy_via_internal_api] 请求失败: {result.get('message')}")
                        return []
                else:
                    error_text = await response.text()
                    logging.error(f"[call_data_proxy_via_internal_api] HTTP错误: {response.status} - {error_text}")
                    return []
        
        except Exception as e:
            logging.error(f"[call_data_proxy_via_internal_api] 调用异常: {str(e)}")
            return []

