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
经验丰富的医生智能体 (CybertwinAgent) - 重构版
============================================

重构后的CybertwinAgent，实现两层级架构：
- 全科医生层：CybertwinAgent（协调器）
- 专科医生层：按地域划分的专科医生（InternalMedicineAgent, SurgicalAgent）
# 简化：ImageAnalysisAgent 暂时已注释掉

主要功能：
1. 意图识别
2. 智能路由到地域专科医生
3. 多轮协调（简化版）
4. 综合诊断报告生成

作者: QSIR
版本: 2.0 - 重构版
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import os
import asyncio

# 导入基础智能体类
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.base_agent import BaseAgent
from agents.llm.intent_recognition import IntentRecognition, IntentType
from agents.utils.shared_context import SharedContext
from agents.coordinator.location_router import LocationRouter
from agents.specialists import (
    InternalMedicineAgent,
    SurgicalAgent,
    # ImageAnalysisAgent  # 暂时注释掉影像分析智能体
)
from shared.config.model_config import get_config


@dataclass
class DemoModeConfig:
    """演示模式配置"""
    enable_demo_mode: bool = True  # 是否启用演示模式
    force_data_proxy_for_diabetes: bool = True  # 是否强制触发数据代理（糖尿病）
    enable_two_round_diagnosis: bool = True  # 是否启用两轮诊断
    random_route_for_non_diabetes: bool = True  # 非糖尿病内容是否随机路由
    use_generic_specialist: bool = True  # 是否使用通用专科医生（无地域限制）


@dataclass
class CybertwinConfig:
    """经验丰富的医生智能体配置（重构版）"""
    model_config: Dict[str, Any]
    enable_auth: bool = True
    enable_audit: bool = True
    max_context_length: int = 4000
    intent_threshold: float = 0.7
    max_rounds: int = 5  # 多轮协调最大轮次
    doctor_persona: str = "温柔亲切的专业医生"
    demo_mode: DemoModeConfig = None  # 演示模式配置


class CybertwinAgent(BaseAgent):
    """
    经验丰富的医生智能体（重构版）
    
    作为全科医生，负责：
    1. 意图识别
    2. 智能路由到地域专科医生
    3. 多轮协调（简化版）
    4. 综合诊断报告生成
    """
    
    def __init__(self, config: CybertwinConfig):
        """
        初始化经验丰富的医生智能体（重构版）
        
        参数：
            config (CybertwinConfig): 智能体配置
        """
        super().__init__(config.model_config)
        self.config = config
        self.agent_id = "cybertwin"
        self.name = "经验丰富的医生"
        
        # 初始化地域专科医生实例
        self._init_specialists()
        
        # 初始化路由引擎
        self.location_router = LocationRouter()
        
        # 初始化意图识别系统
        self._init_intent_recognition()
        
        # 初始化认证授权系统（可选）
        self._init_auth_system()
        
        # 初始化演示模式组件（如果启用）
        self._init_demo_mode()
        
        self.logger.info(f"[{self.name}] 初始化完成（重构版）")
    
    def _init_specialists(self):
        """
        初始化地域专科医生实例
        
        为每个专科类型创建北京和上海两个地域实例
        """
        self.specialists = {
            "internal_medicine": {},
            "surgical": {},
            # "image_analysis": {}  # 暂时注释掉影像分析专科
        }
        
        try:
            # 内科医生 - 北京（使用huatuogpt-2）
            internal_medicine_bj_config = get_config("huatuo2").to_dict()
            self.specialists["internal_medicine"]["beijing"] = InternalMedicineAgent(
                internal_medicine_bj_config, location="beijing"
            )
            
            # 内科医生 - 上海（使用huatuogpt）
            internal_medicine_sh_config = get_config("huatuo").to_dict()
            self.specialists["internal_medicine"]["shanghai"] = InternalMedicineAgent(
                internal_medicine_sh_config, location="shanghai"
            )
            
            # 外科医生 - 北京
            surgical_bj_config = get_config("huatuo2").to_dict()
            self.specialists["surgical"]["beijing"] = SurgicalAgent(
                surgical_bj_config, location="beijing"
            )
            
            # 外科医生 - 上海
            surgical_sh_config = get_config("huatuo").to_dict()
            self.specialists["surgical"]["shanghai"] = SurgicalAgent(
                surgical_sh_config, location="shanghai"
            )
            
            # 影像分析医生 - 北京（暂时注释掉）
            # image_bj_config = get_config("huatuo2").to_dict()
            # self.specialists["image_analysis"]["beijing"] = ImageAnalysisAgent(
            #     image_bj_config, location="beijing"
            # )
            
            # 影像分析医生 - 上海（暂时注释掉）
            # image_sh_config = get_config("huatuo").to_dict()
            # self.specialists["image_analysis"]["shanghai"] = ImageAnalysisAgent(
            #     image_sh_config, location="shanghai"
            # )
            
            self.logger.info(f"[{self.name}] 地域专科医生实例初始化完成")
            self.logger.info(f"  - 内科: 北京、上海")
            self.logger.info(f"  - 外科: 北京、上海")
            # self.logger.info(f"  - 影像分析: 北京、上海")  # 暂时注释掉
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 专科医生实例初始化失败: {str(e)}", exc_info=True)
            raise
    
    def _init_intent_recognition(self):
        """初始化意图识别系统"""
        try:
            self.intent_recognition = IntentRecognition(self.caller, self.model_config)
            self.logger.info(f"[{self.name}] 意图识别系统初始化完成")
        except Exception as e:
            self.logger.warning(f"[{self.name}] 意图识别系统初始化失败: {str(e)}")
            self.intent_recognition = None
    
    def _init_auth_system(self):
        """初始化认证授权系统"""
        if not self.config.enable_auth:
            self.authz_manager = None
            self.audit_manager = None
            self.logger.info(f"[{self.name}] 认证授权系统已禁用")
            return
        
        try:
            from auth_manager import authz_manager, audit_manager
            self.authz_manager = authz_manager
            self.audit_manager = audit_manager
            self.logger.info(f"[{self.name}] 认证授权系统初始化完成")
        except ImportError as e:
            self.logger.warning(f"[{self.name}] 认证授权模块未找到: {str(e)}")
            self.authz_manager = None
            self.audit_manager = None
    
    def _init_demo_mode(self):
        """初始化演示模式组件"""
        # 如果没有配置演示模式，使用默认配置
        if self.config.demo_mode is None:
            self.config.demo_mode = DemoModeConfig()
        
        if not self.config.demo_mode.enable_demo_mode:
            self.demo_detector = None
            self.forced_trigger = None
            self.two_round_coordinator = None
            self.default_handler = None
            self.logger.info(f"[{self.name}] 演示模式已禁用")
            return
        
        try:
            from agents.coordinator.demo_mode_detector import DemoModeDetector
            from agents.coordinator.forced_data_proxy_trigger import ForcedDataProxyTrigger
            from agents.coordinator.two_round_diagnosis_coordinator import TwoRoundDiagnosisCoordinator
            from agents.coordinator.default_strategy_handler import DefaultStrategyHandler
            
            self.demo_detector = DemoModeDetector()
            # 注意：ForcedDataProxyTrigger 和 TwoRoundDiagnosisCoordinator 的 token 将在 execute 方法中动态设置
            # 因为 token 来自 user_info，而 user_info 在 execute 时才能获取
            self.forced_trigger = ForcedDataProxyTrigger()
            self.two_round_coordinator = TwoRoundDiagnosisCoordinator(self.specialists)
            self.default_handler = DefaultStrategyHandler(self.specialists)
            
            self.logger.info(f"[{self.name}] 演示模式组件初始化完成")
        except Exception as e:
            self.logger.error(f"[{self.name}] 演示模式组件初始化失败: {str(e)}", exc_info=True)
            self.demo_detector = None
            self.forced_trigger = None
            self.two_round_coordinator = None
            self.default_handler = None
    
    def clear_memory(self, user_id: str):
        """
        清除用户对话记忆（重写父类方法）
        
        不仅清除 CybertwinAgent 自己的对话记忆，还要清除所有子智能体（specialists）的对话记忆
        
        参数：
            user_id (str): 用户ID
        """
        try:
            # 1. 清除 CybertwinAgent 自己的对话记忆
            super().clear_memory(user_id)
            
            # 2. 清除所有子智能体（specialists）的对话记忆
            if hasattr(self, 'specialists') and self.specialists:
                cleared_count = 0
                for specialty_type, locations in self.specialists.items():
                    if isinstance(locations, dict):
                        for location, agent in locations.items():
                            if agent and hasattr(agent, 'clear_memory'):
                                try:
                                    agent.clear_memory(user_id)
                                    cleared_count += 1
                                    self.logger.debug(f"[{self.name}] 已清除 {specialty_type}_{location} 的对话记忆")
                                except Exception as e:
                                    self.logger.warning(f"[{self.name}] 清除 {specialty_type}_{location} 对话记忆失败: {str(e)}")
                
                self.logger.info(f"[{self.name}] 已清除用户 {user_id} 的所有对话记忆（包括 {cleared_count} 个子智能体）")
            else:
                self.logger.warning(f"[{self.name}] 未找到子智能体实例，仅清除主智能体对话记忆")
                
        except Exception as e:
            self.logger.error(f"[{self.name}] 清除对话记忆失败: {str(e)}", exc_info=True)
    
    async def execute(
        self, 
        user_input: str, 
        user_id: str, 
        user_info: Optional[Dict] = None
    ) -> Tuple[str, Any]:
        """
        执行完整诊断流程（重构版，支持演示模式）
        
        参数：
            user_input (str): 用户输入
            user_id (str): 用户ID
            user_info (Dict, optional): 用户信息
            
        返回：
            Tuple[str, Any]: (智能体名称, 结果)
        """
        try:
            self.logger.info(f"[{self.name}] 开始执行诊断流程")
            
            # 1. 权限验证（如果启用）
            if self.config.enable_auth and self.authz_manager:
                auth_result = await self._verify_permissions(user_id, user_info)
                if auth_result is not None:
                    return auth_result
            
            # 2. 检测是否为演示模式
            if self.config.demo_mode and self.config.demo_mode.enable_demo_mode and self.demo_detector:
                # 检测是否与糖尿病相关
                is_diabetes = self.demo_detector.is_diabetes_related(user_input)
                
                if is_diabetes:
                    # 糖尿病相关：强制触发两轮诊断流程
                    self.logger.info(f"[{self.name}] 检测到糖尿病相关内容，使用演示模式（两轮诊断）")
                    return await self._execute_diabetes_demo(user_input, user_id, user_info)
                else:
                    # 非糖尿病相关：使用默认策略
                    self.logger.info(f"[{self.name}] 非糖尿病相关内容，使用默认策略（快速诊断）")
                    return await self._execute_default_strategy(user_input, user_id, user_info)
            
            # 3. 原有流程（非演示模式）
            intent = await self._recognize_intent(user_input)
            self.logger.info(f"[{self.name}] 识别到意图: {intent}")
            
            result = await self._basic_diagnosis_flow(
                intent, user_input, user_id, user_info
            )
            
            return self.name, result
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 执行错误：{str(e)}", exc_info=True)
            return self.name, f"[ERROR] 抱歉，我在处理您的咨询时遇到了问题，请稍后再试。{str(e)}"
    
    async def _recognize_intent(self, user_input: str) -> str:
        """
        识别用户意图（简化版）
        
        参数：
            user_input (str): 用户输入
            
        返回：
            str: 意图类型（内科咨询、外科咨询、影像分析、药物查询、一般问题、未知）
        """
        if not self.intent_recognition:
            # 如果没有意图识别系统，使用简单规则
            if "影像" in user_input or "CT" in user_input or "MRI" in user_input or "X光" in user_input:
                return "影像分析"
            elif "药物" in user_input or "药品" in user_input or "用药" in user_input:
                return "药物查询"
            elif "外科" in user_input or "手术" in user_input:
                return "外科咨询"
            else:
                return "内科咨询"
        
        try:
            # 使用IntentRecognition的recognize_intent方法
            intent_result = await self.intent_recognition.recognize_intent(user_input)
            intent_type = intent_result.intent_type if hasattr(intent_result, 'intent_type') else intent_result
            
            # 直接使用intent_type的值（已经是中文名称）
            from agents.llm.intent_recognition import IntentType
            
            if isinstance(intent_type, IntentType):
                # IntentType枚举的值已经是中文名称
                return intent_type.value
            elif isinstance(intent_type, str):
                # 如果已经是字符串，直接返回
                return intent_type
            else:
                # 默认返回未知
                return "未知"
            
        except Exception as e:
            self.logger.warning(f"[{self.name}] 意图识别失败: {str(e)}，使用默认意图")
            return "未知"
    
    async def _basic_diagnosis_flow(
        self,
        intent: str,
        user_input: str,
        user_id: str,
        user_info: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        基础诊断流程（简化版）
        
        注意：这是第一阶段的简化版本，不包含：
        - 第三方数据代理交互
        - 完整的多轮协调机制
        
        这些功能将在第二阶段实现
        """
        # 初始化共享上下文
        context = SharedContext(
            user_id=user_id,
            intent=intent,
            user_input=user_input,
            user_info=user_info or {}
        )
        
        # ============================================================
        # 【已禁用】模拟测试代码 - 真实测试时已注释
        # ============================================================
        # 在真实第三方应用测试时，应该通过 EntryAgent 从真实数据代理应用获取数据地址
        # 注意：演示模式使用 forced_trigger.force_trigger_data_proxy 获取数据地址
        # ============================================================
        
        # 【已注释】以下模拟数据地址获取代码已禁用（真实测试时）
        # data_addresses = self._get_mock_data_addresses(user_id, intent)
        # if data_addresses:
        #     context.data_addresses_history.append({
        #         "round": 1,
        #         "data_addresses": data_addresses
        #     })
        
        # 【✅ 真实第三方应用调用】通过 EntryAgent 从真实数据代理应用获取数据地址
        # 注意：在演示模式下，数据地址通过 forced_trigger.force_trigger_data_proxy 获取
        # 在非演示模式下，应该使用 DataProxyClient 获取数据地址
        data_addresses = []  # 真实测试时应该通过 EntryAgent 获取
        
        # 路由到专科医生
        specialist_results = await self._route_to_specialists_with_context(
            intent, user_input, user_id, data_addresses, context, user_info
        )
        
        # 更新上下文
        context.diagnosis_results_history.extend(specialist_results)
        
        # 生成综合报告（简化版）
        report = await self._generate_comprehensive_report_simple(
            user_input, specialist_results, user_info, context
        )
        
        return {
            "status": "success",
            "report": report,
            "specialist_results": specialist_results,
            "rounds": context.round_number,
            "data_sources": [r.get("data_sources", []) for r in specialist_results]
        }
    
    async def _route_to_specialists_with_context(
        self,
        intent: str,
        user_input: str,
        user_id: str,
        data_addresses: List[Dict],
        shared_context: SharedContext,
        user_info: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        智能路由到专科医生（传递共享上下文）
        
        参数：
            intent (str): 意图类型
            user_input (str): 用户输入
            user_id (str): 用户ID
            data_addresses (List[Dict]): 数据地址列表
            shared_context (SharedContext): 共享上下文
            user_info (Dict, optional): 用户信息
            
        返回：
            List[Dict[str, Any]]: 专科医生诊断结果列表
        """
        # 使用LocationRouter进行路由
        routing_results = self.location_router.route_to_specialists(
            intent, data_addresses, self.specialists
        )
        
        # 验证路由结果
        if not self.location_router.validate_routing(routing_results, self.specialists):
            self.logger.error(f"[{self.name}] 路由验证失败")
            return []
        
        # 并行调用各地域的专科医生
        tasks = []
        for location, specialty, addresses in routing_results:
            specialist = self.specialists[specialty][location]
            task = specialist.execute(
                user_input,
                user_id,
                data_addresses=addresses,
                shared_context=shared_context,
                user_info=user_info
            )
            tasks.append(task)
        
        # 等待所有诊断完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"[{self.name}] 专科医生诊断失败: {str(result)}")
                location, specialty, _ = routing_results[i]
                valid_results.append({
                    "agent": f"{specialty}_{location}",
                    "location": location,
                    "specialization": specialty,
                    "error": str(result),
                    "confidence": 0.0
                })
            else:
                valid_results.append(result)
        
        return valid_results
    
    # ============================================================
    # 【已禁用】模拟数据地址方法 - 真实测试时已注释
    # ============================================================
    # 在真实第三方应用测试时，应该通过 EntryAgent 从真实数据代理应用获取数据地址
    # 演示模式使用 forced_trigger.force_trigger_data_proxy 获取数据地址
    # ============================================================
    # def _get_mock_data_addresses(self, user_id: str, intent: str) -> List[Dict]:
    #     """
    #     【模拟测试方法】获取模拟数据地址（第一阶段简化版）
    #     
    #     ════════════════════════════════════════════════════════════
    #     【生产环境替换说明】
    #     ════════════════════════════════════════════════════════════
    #     
    #     生产环境请替换为真实的第三方数据代理应用调用：
    #     
    #     1. 使用 DataProxyClient.interact_with_context() 方法
    #     2. 配置真实的数据代理应用URL和API密钥（通过环境变量）
    #     3. 删除此方法，在 _basic_diagnosis_flow 中直接调用：
    #     
    #     ```python
    #     from shared.agents.coordinator.data_proxy_client import DataProxyClient, DataProxyConfig
    #     import os
    #     
    #     data_proxy_config = DataProxyConfig(
    #         base_url=os.getenv("DATA_PROXY_APP_URL", "http://localhost:9000"),
    #         api_key=os.getenv("DATA_PROXY_API_KEY", ""),
    #         timeout=int(os.getenv("DATA_PROXY_TIMEOUT", "30")),
    #         max_rounds=5
    #     )
    #     
    #     async with DataProxyClient(data_proxy_config) as client:
    #         data_addresses = await client.interact_with_context(
    #             intent=intent,
    #             user_input=user_input,
    #             user_id=user_id,
    #             shared_context=shared_context
    #         )
    #     ```
    #     
    #     详细说明请参考：docs/第三方应用模拟测试与真实切换指南.md
    #     ════════════════════════════════════════════════════════════
    #     """
    #     # 根据意图返回模拟的数据地址
    #     if "影像" in intent:
    #         return [
    #             {
    #                 "data_type": "影像数据",
    #                 "location": "beijing",
    #                 "address": f"db://hospital_beijing/medical_images/{user_id}",
    #                 "hospital": "北京医院"
    #             }
    #         ]
    #     else:
    #         return [
    #             {
    #                 "data_type": "病史数据",
    #                 "location": "beijing",
    #                 "address": f"db://hospital_beijing/medical_records/{user_id}",
    #                 "hospital": "北京医院"
    #             },
    #             {
    #                 "data_type": "用药记录",
    #                 "location": "shanghai",
    #                 "address": f"db://hospital_shanghai/medications/{user_id}",
    #                 "hospital": "上海医院"
    #             }
    #         ]
    
    async def _generate_comprehensive_report_simple(
        self,
        user_input: str,
        specialist_results: List[Dict[str, Any]],
        user_info: Optional[Dict],
        shared_context: SharedContext
    ) -> str:
        """
        生成综合诊断报告（简化版）
        
        TODO: 第三阶段将实现完整的报告综合生成，包括冲突检测等
        """
        if not specialist_results:
            return "[ERROR] 未能获取到专科医生的诊断结果。"
        
        # 构建报告提示
        results_summary = []
        for result in specialist_results:
            location = result.get("location", "未知")
            specialization = result.get("specialization", "未知")
            diagnosis = result.get("diagnosis", {})
            confidence = result.get("confidence", 0.0)
            
            if isinstance(diagnosis, dict):
                diagnosis_text = diagnosis.get("diagnosis", "无诊断结果")
            else:
                diagnosis_text = str(diagnosis)
            
            results_summary.append(
                f"【{location} - {specialization}医生】\n"
                f"诊断: {diagnosis_text}\n"
                f"置信度: {confidence:.2f}\n"
            )
        
        prompt = f"""作为一位经验丰富的全科医生，请根据以下专科医生的诊断结果，生成一份综合诊断报告。

患者症状描述：{user_input}

专科医生诊断结果：
{''.join(results_summary)}

请生成一份温柔亲切、专业负责的综合诊断报告，包括：
1. 症状分析总结
2. 综合诊断结论
3. 治疗建议

报告要求：
- 语言温暖亲切，让患者感到被理解和关怀
- 专业准确，避免引起不必要的担心
- 条理清晰，便于患者理解
- **签名要求**：报告结尾请使用"您的智慧医生 小白"，不要使用"此致 敬礼 [您的医生姓名] [您的医院名称] [日期]"这样的格式
"""
        
        try:
            print(f"\n[{self.name}] 开始调用LLM生成综合诊断报告...")
            report = await self.caller(prompt, self.model_config)
            print(f"[{self.name}] 综合诊断报告LLM调用完成，结果长度: {len(str(report))} 字符")
            return report
        except Exception as e:
            self.logger.error(f"[{self.name}] 生成综合报告失败: {str(e)}")
            return "\n".join(results_summary)
    
    async def _verify_permissions(self, user_id: str, user_info: Optional[Dict]) -> Optional[Tuple[str, str]]:
        """
        验证用户权限
        
        参数：
            user_id (str): 用户ID
            user_info (Dict, optional): 用户信息
            
        返回：
            Optional[Tuple[str, str]]: 如果权限验证失败，返回错误信息
        """
        if not self.authz_manager:
            return None
        
        try:
            # 这里可以实现具体的权限验证逻辑
            # 目前简化处理
            return None
        except Exception as e:
            self.logger.error(f"[{self.name}] 权限验证错误: {str(e)}")
            return None
    
    async def _execute_diabetes_demo(
        self,
        user_input: str,
        user_id: str,
        user_info: Optional[Dict]
    ) -> Tuple[str, Any]:
        """
        执行糖尿病演示流程（A2A协议，两轮诊断）
        
        流程：
        1. 意图识别
        2. 强制触发数据代理请求（第一轮）
        3. 第一轮诊断
        4. 判断是否需要第二轮（如果需要，请求补充数据）
        5. 第二轮诊断（如果需要）
        6. 生成综合诊断报告（综合多轮诊断结果）
        
        返回：
        - report: 综合诊断报告（综合多轮诊断结果），不是单个专科医生的诊断结果
        - report_type: "comprehensive_report"（标识这是综合报告）
        - 与默认策略的区别：默认策略返回单个专科医生的诊断结果
        """
        try:
            # 1. 先进行意图识别
            intent = await self._recognize_intent(user_input)
            self.logger.info(f"[{self.name}] 糖尿病演示流程，识别到意图: {intent}")
            
            # 2. 初始化共享上下文
            shared_context = SharedContext(
                user_id=user_id,
                intent=intent,
                user_input=user_input,
                user_info=user_info or {}
            )
            
            # 3. 强制触发数据代理请求（第一轮，使用识别的意图）
            print(f"\n[演示模式] 第一轮诊断 - 开始请求数据")
            print(f"  识别的意图: {intent}")
            print(f"  用户输入: {user_input[:100]}..." if len(user_input) > 100 else f"  用户输入: {user_input}")
            
            # 从 user_info 中提取 id_token（如果存在）
            id_token = None
            if user_info and isinstance(user_info, dict):
                id_token = user_info.get("id_token") or user_info.get("token")
            
            data_addresses_round1 = await self.forced_trigger.force_trigger_data_proxy(
                user_input=user_input,
                user_id=user_id,
                intent=intent,  # 使用识别的意图，而不是固定值
                shared_context=shared_context,
                token=id_token  # 传递 id_token
            )
            
            print(f"[演示模式] 第一轮诊断 - 数据请求完成，获取到 {len(data_addresses_round1)} 个数据地址\n")
            
            if not data_addresses_round1:
                self.logger.warning(f"[{self.name}] 第一轮未获取到数据地址")
                return self.name, {
                    "status": "error",
                    "error": "抱歉，未能获取到相关医疗数据，请稍后再试。",
                    "report": "抱歉，未能获取到相关医疗数据，请稍后再试。",
                    "specialist_results": [],
                    "rounds": 0,
                    "data_sources": []
                }
            
            # 4. 第一轮诊断（传递意图信息）
            round1_results = await self.two_round_coordinator.first_round_diagnosis(
                user_input=user_input,
                user_id=user_id,
                data_addresses=data_addresses_round1,
                shared_context=shared_context,
                intent=intent  # 传递识别的意图
            )
            
            # 保存意图到结果中，供第二轮使用
            round1_results["intent"] = intent
            
            # 5. 判断是否需要第二轮
            # 添加详细的调试信息
            print(f"\n" + "=" * 80)
            print(f"[调试] 第二轮诊断判断条件检查")
            print(f"=" * 80)
            print(f"  needs_more_data: {round1_results.get('needs_more_data', 'N/A')}")
            print(f"  enable_two_round_diagnosis: {self.config.demo_mode.enable_two_round_diagnosis}")
            print(f"  第一轮诊断结果数量: {len(round1_results.get('diagnosis_results', []))}")
            print(f"  第一轮诊断结果详情:")
            for idx, result in enumerate(round1_results.get('diagnosis_results', []), 1):
                if isinstance(result, dict):
                    print(f"    结果 {idx}:")
                    print(f"      - agent: {result.get('agent', 'N/A')}")
                    print(f"      - confidence: {result.get('confidence', 'N/A')}")
                    print(f"      - needs_more_data: {result.get('needs_more_data', 'N/A')}")
                else:
                    print(f"    结果 {idx}: {type(result)}")
            print(f"=" * 80)
            
            if round1_results["needs_more_data"] and self.config.demo_mode.enable_two_round_diagnosis:
                print(f"\n[演示模式] 第一轮诊断完成，需要补充数据，开始第二轮诊断...")
                print(f"  第一轮诊断结果数量: {len(round1_results.get('diagnosis_results', []))}")
                
                # 6. 第二轮诊断（请求补充数据，使用原始意图）
                # 从 user_info 中提取 id_token（如果存在）
                id_token = None
                if user_info and isinstance(user_info, dict):
                    id_token = user_info.get("id_token") or user_info.get("token")
                
                round2_results = await self.two_round_coordinator.second_round_diagnosis(
                    user_input=user_input,
                    user_id=user_id,
                    first_round_results=round1_results,
                    shared_context=shared_context,
                    token=id_token  # 传递 id_token
                )
                
                print(f"[演示模式] 第二轮诊断完成")
                print(f"  第二轮诊断结果数量: {len(round2_results.get('diagnosis_results', []))}\n")
                
                # 7. 生成综合诊断报告（包含两轮结果）
                report = await self._generate_comprehensive_report_demo(
                    user_input=user_input,
                    round1_results=round1_results,
                    round2_results=round2_results,
                    user_info=user_info
                )
                
                # 收集所有专科医生结果
                specialist_results = round1_results.get("diagnosis_results", [])
                specialist_results.extend(round2_results.get("diagnosis_results", []))
                rounds = 2
            else:
                # 只使用第一轮结果
                print(f"\n[警告] 第二轮诊断未执行，原因:")
                if not round1_results.get("needs_more_data", False):
                    print(f"  - needs_more_data 为 False（第一轮诊断结果可能为空或不需要补充数据）")
                if not self.config.demo_mode.enable_two_round_diagnosis:
                    print(f"  - enable_two_round_diagnosis 为 False（两轮诊断功能未启用）")
                print(f"  将只使用第一轮诊断结果生成报告\n")
                
                report = await self._generate_comprehensive_report_demo(
                    user_input=user_input,
                    round1_results=round1_results,
                    round2_results=None,
                    user_info=user_info
                )
                
                # 收集专科医生结果
                specialist_results = round1_results.get("diagnosis_results", [])
                rounds = 1
            
            # 返回标准格式的字典，包含 status、report、specialist_results 和 rounds 字段
            # 注意：演示模式返回的是综合报告（综合多轮诊断结果），不是单个专科医生的诊断结果
            return self.name, {
                "status": "success",
                "report": report,  # 综合诊断报告（综合多轮诊断结果）
                "report_type": "comprehensive_report",  # 标识这是综合报告，不是单个专科医生诊断
                "specialist_results": specialist_results,
                "rounds": rounds,
                "data_sources": []  # 可以从 specialist_results 中提取
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 糖尿病演示流程失败: {str(e)}", exc_info=True)
            return self.name, {
                "status": "error",
                "error": f"抱歉，在处理您的咨询时遇到了问题：{str(e)}",
                "report": f"抱歉，在处理您的咨询时遇到了问题：{str(e)}",
                "specialist_results": [],
                "rounds": 0,
                "data_sources": []
            }
    
    async def _execute_default_strategy(
        self,
        user_input: str,
        user_id: str,
        user_info: Optional[Dict]
    ) -> Tuple[str, Any]:
        """
        执行默认策略流程（非糖尿病相关问题）
        
        流程：
        1. 意图识别
        2. 随机路由到通用专科医生（无地域限制）
        3. 快速诊断（不使用数据代理）
        
        返回：
        - report: 专科医生的诊断结果（final response），不是综合报告
        - report_type: "specialist_diagnosis"（标识这是专科医生诊断）
        - 与演示模式的区别：演示模式返回综合报告（综合多轮诊断结果）
        """
        try:
            # 1. 意图识别
            intent = await self._recognize_intent(user_input)
            self.logger.info(f"[{self.name}] 默认策略流程，识别到意图: {intent}")
            
            # 2. 随机路由到通用专科医生
            specialty, location = self.default_handler.random_route_to_specialist(intent)
            
            # 3. 快速诊断（不使用数据代理）
            diagnosis = await self.default_handler.quick_diagnosis(
                user_input=user_input,
                user_id=user_id,
                specialist_type=specialty,
                location=location,
                intent=intent  # 传递识别的意图
            )
            
            # 统一返回格式，与演示模式保持一致
            # 注意：默认策略返回的是专科医生的诊断结果（final response），不是综合报告
            # 演示模式返回的是综合报告（综合多轮诊断结果）
            if isinstance(diagnosis, str):
                # 如果是字符串，包装成标准格式
                return self.name, {
                    "status": "success",
                    "report": diagnosis,  # 专科医生的诊断结果（final response），不是综合报告
                    "report_type": "specialist_diagnosis",  # 标识这是专科医生诊断，不是综合报告
                    "specialist_results": [],
                    "rounds": 1,
                    "data_sources": []
                }
            elif isinstance(diagnosis, dict):
                # 如果已经是字典，检查是否有status字段
                if diagnosis.get("status") == "success":
                    return self.name, diagnosis
                else:
                    # 包装成标准格式
                    return self.name, {
                        "status": "success",
                        "report": diagnosis.get("report", diagnosis.get("diagnosis", str(diagnosis))),
                        "report_type": "specialist_diagnosis",  # 标识这是专科医生诊断，不是综合报告
                        "specialist_results": [],
                        "rounds": 1,
                        "data_sources": []
                    }
            else:
                # 其他类型，转换为字符串
                return self.name, {
                    "status": "success",
                    "report": str(diagnosis),
                    "report_type": "specialist_diagnosis",  # 标识这是专科医生诊断，不是综合报告
                    "specialist_results": [],
                    "rounds": 1,
                    "data_sources": []
                }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 默认策略流程失败: {str(e)}", exc_info=True)
            return self.name, {
                "status": "error",
                "error": f"抱歉，在处理您的咨询时遇到了问题：{str(e)}",
                "report": f"抱歉，在处理您的咨询时遇到了问题：{str(e)}"
            }
    
    async def _generate_comprehensive_report_demo(
        self,
        user_input: str,
        round1_results: Dict[str, Any],
        round2_results: Optional[Dict[str, Any]],
        user_info: Optional[Dict]
    ) -> str:
        """
        生成演示模式的综合诊断报告
        
        参数:
            user_input: 用户输入
            round1_results: 第一轮诊断结果
            round2_results: 第二轮诊断结果（可选）
            user_info: 用户信息
            
        返回:
            str: 综合诊断报告
        """
        try:
            # 构建报告提示
            results_summary = []
            
            # 第一轮结果
            round1_diagnosis = round1_results.get("diagnosis_results", [])
            results_summary.append("【第一轮诊断结果】\n")
            round1_data_sources = set()  # 收集第一轮的数据来源
            for result in round1_diagnosis:
                if isinstance(result, dict):
                    location = result.get("location", "未知")
                    specialization = result.get("specialization", "未知")
                    diagnosis = result.get("diagnosis", {})
                    confidence = result.get("confidence", 0.0)
                    
                    # ✅ 提取数据来源信息
                    data_sources = result.get("data_sources", [])
                    available_data_types = result.get("available_data_types", [])
                    data_content = result.get("data_content", {})
                    data_usage_summary = result.get("data_usage_summary", "")
                    
                    # 收集数据来源
                    if data_sources:
                        round1_data_sources.update(data_sources)
                    
                    if isinstance(diagnosis, dict):
                        diagnosis_text = diagnosis.get("diagnosis", "无诊断结果")
                    else:
                        diagnosis_text = str(diagnosis)
                    
                    # ✅ 构建包含数据来源的诊断结果描述
                    result_line = f"  - {location} - {specialization}医生: {diagnosis_text} (置信度: {confidence:.2f})"
                    
                    # 添加数据来源信息
                    if data_sources:
                        result_line += f"\n    数据来源: {', '.join(data_sources)}"
                    if available_data_types:
                        result_line += f"\n    数据类型: {', '.join(available_data_types)}"
                    if data_usage_summary:
                        result_line += f"\n    数据使用: {data_usage_summary[:100]}..." if len(data_usage_summary) > 100 else f"\n    数据使用: {data_usage_summary}"
                    
                    results_summary.append(result_line + "\n")
            
            # 第二轮结果
            round2_data_sources = set()  # 收集第二轮的数据来源
            if round2_results:
                round2_diagnosis = round2_results.get("diagnosis_results", [])
                results_summary.append("\n【第二轮诊断结果（补充数据后）】\n")
                for result in round2_diagnosis:
                    if isinstance(result, dict):
                        location = result.get("location", "未知")
                        specialization = result.get("specialization", "未知")
                        diagnosis = result.get("diagnosis", {})
                        confidence = result.get("confidence", 0.0)
                        
                        # ✅ 提取数据来源信息
                        data_sources = result.get("data_sources", [])
                        available_data_types = result.get("available_data_types", [])
                        data_content = result.get("data_content", {})
                        data_usage_summary = result.get("data_usage_summary", "")
                        
                        # 收集数据来源
                        if data_sources:
                            round2_data_sources.update(data_sources)
                        
                        if isinstance(diagnosis, dict):
                            diagnosis_text = diagnosis.get("diagnosis", "无诊断结果")
                        else:
                            diagnosis_text = str(diagnosis)
                        
                        # ✅ 构建包含数据来源的诊断结果描述
                        result_line = f"  - {location} - {specialization}医生: {diagnosis_text} (置信度: {confidence:.2f})"
                        
                        # 添加数据来源信息
                        if data_sources:
                            result_line += f"\n    数据来源: {', '.join(data_sources)}"
                        if available_data_types:
                            result_line += f"\n    数据类型: {', '.join(available_data_types)}"
                        if data_usage_summary:
                            result_line += f"\n    数据使用: {data_usage_summary[:100]}..." if len(data_usage_summary) > 100 else f"\n    数据使用: {data_usage_summary}"
                        
                        results_summary.append(result_line + "\n")
            
            # ✅ 构建数据来源汇总信息
            data_sources_summary = []
            if round1_data_sources:
                # 第一轮诊断：通过MCP从数据存储服务获取
                round1_sources_text = ', '.join(sorted(round1_data_sources))
                data_sources_summary.append(f"第一轮诊断数据来源（通过MCP从数据存储服务获取）: {round1_sources_text}")
            if round2_data_sources:
                # 第二轮诊断：从数据代理应用直接返回
                # ✅ 检查是否是健康监测数据
                is_health_monitoring = any("健康监测" in str(source) for source in round2_data_sources)
                
                # 检查是否包含"数据代理应用直接返回"标识
                round2_sources_clean = []
                has_direct_data_indicator = False
                for source in sorted(round2_data_sources):
                    if "数据代理应用直接返回" in source:
                        has_direct_data_indicator = True
                        # 提取原始来源（去掉"（数据代理应用直接返回）"后缀）
                        clean_source = source.replace("（数据代理应用直接返回）", "").strip()
                        if clean_source:
                            round2_sources_clean.append(clean_source)
                    else:
                        round2_sources_clean.append(source)
                
                if is_health_monitoring:
                    # ✅ 健康监测数据：明确标识为健康监测数据
                    round2_sources_text = "健康监测数据"
                    data_sources_summary.append(f"第二轮诊断数据来源（健康监测数据）: {round2_sources_text}")
                elif has_direct_data_indicator or not round2_sources_clean:
                    # 如果包含直接数据标识或没有来源，说明是数据代理应用直接返回
                    round2_sources_text = ', '.join(round2_sources_clean) if round2_sources_clean else "数据代理应用直接返回"
                    data_sources_summary.append(f"第二轮诊断数据来源（数据代理应用直接返回）: {round2_sources_text}")
                else:
                    # 如果没有直接数据标识，可能是其他情况
                    round2_sources_text = ', '.join(round2_sources_clean)
                    data_sources_summary.append(f"第二轮诊断数据来源: {round2_sources_text}")
            
            data_sources_text = "\n".join(data_sources_summary) if data_sources_summary else "数据来源: 未提供"
            
            prompt = f"""作为一位经验丰富的全科医生，请根据以下专科医生的诊断结果，生成一份综合诊断报告。

患者症状描述：{user_input}

专科医生诊断结果：
{''.join(results_summary)}

数据来源汇总：
{data_sources_text}

请生成一份温柔亲切、专业负责的综合诊断报告，包括：
1. 症状分析总结
2. 综合诊断结论（结合两轮诊断结果）
   - 请说明第一轮诊断使用了哪些医院的数据（如：北京协和、上海瑞金等）
   - 请说明第二轮诊断补充了哪些数据（如：健康监测数据等）
   - 请明确区分两轮诊断的数据来源方式
   - **重要**：第二轮诊断使用的是"健康监测数据"（如血糖、血压、心率等实时监测数据），而不是医院名称。请在报告中明确说明"第二轮诊断使用了健康监测数据"，不要写成"症状和健康监测数据：XX医院"这样的格式
3. 治疗建议


报告要求：
- 语言温暖亲切，让患者感到被理解和关怀
- 专业准确，避免引起不必要的担心
- 条理清晰，便于患者理解
- 如果有多轮诊断，请说明诊断的演进过程
- 请在报告中明确说明使用了哪些医院的数据或者哪些健康监测数据进行诊断，让患者了解诊断依据的来源
- **重要**：对于第二轮诊断，必须明确说明使用的是"健康监测数据"，而不是医院名称。例如："第二轮诊断补充了健康监测数据（包括血糖、血压、心率等）"，而不是"症状和健康监测数据：XX医院"
- **签名要求**：报告结尾请使用"您的智慧医生 小白"，不要使用"此致 敬礼 [您的医生姓名] [您的医院名称] [日期]"这样的格式
"""
            
            print(f"\n[{self.name}] 开始调用LLM生成演示模式综合诊断报告...")
            report = await self.caller(prompt, self.model_config)
            print(f"[{self.name}] 演示模式综合诊断报告LLM调用完成，结果长度: {len(str(report))} 字符")
            return report
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 生成演示模式综合报告失败: {str(e)}")
            return f"诊断结果：{''.join(results_summary)}"

