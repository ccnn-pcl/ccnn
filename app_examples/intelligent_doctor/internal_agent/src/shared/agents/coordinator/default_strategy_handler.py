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
默认策略处理器 (DefaultStrategyHandler)
======================================

对于非糖尿病相关内容，使用默认策略：
- 随机路由到通用专科医生（无地域限制）
- 快速诊断（不使用数据代理）

作者: QSIR
版本: 1.0
"""

import logging
import random
from typing import Dict, Any, Optional, Tuple


class DefaultStrategyHandler:
    """默认策略处理器"""
    
    # 意图到专科类型的映射
    INTENT_TO_SPECIALTY = {
        "内科咨询": "internal_medicine",
        "外科咨询": "surgical",
        #"影像分析": "internal_medicine",  # 影像分析暂时路由到内科
        "药物查询": "internal_medicine",  # 药物查询路由到内科
        "一般问题": "internal_medicine",  # 一般问题路由到内科
        "未知": "internal_medicine"       # 未知意图路由到内科
    }
    
    def __init__(self, specialists: Dict[str, Dict[str, Any]]):
        """
        初始化默认策略处理器
        
        参数:
            specialists: 专科医生实例字典
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.specialists = specialists
        self.logger.info(f"[DefaultStrategyHandler] 初始化完成")
    
    def _map_intent_to_specialty(self, intent: str) -> str:
        """
        将意图映射到专科类型
        
        参数:
            intent: 意图类型
            
        返回:
            str: 专科类型
        """
        return self.INTENT_TO_SPECIALTY.get(intent, "internal_medicine")
    
    def random_route_to_specialist(
        self,
        intent: str
    ) -> Tuple[str, Optional[str]]:
        """
        随机路由到通用专科医生（无地域限制）
        
        参数:
            intent: 意图类型
            
        返回:
            Tuple[str, Optional[str]]: (专科类型, 地域) - 地域为None表示无地域限制
        """
        # 映射意图到专科类型
        specialty = self._map_intent_to_specialty(intent)
        
        # 随机选择地域（演示模式：随机选择beijing或shanghai，或使用通用）
        locations = ["beijing", "shanghai"]
        # 演示模式：50%概率使用通用（无地域限制）
        if random.random() < 0.5:
            location = None  # 无地域限制
        else:
            location = random.choice(locations)
        
        self.logger.info(f"[DefaultStrategyHandler] 随机路由: {specialty} - {location if location else '通用'}")
        
        return specialty, location
    
    def _get_specialist(self, specialist_type: str, location: Optional[str]):
        """
        获取专科医生实例
        
        参数:
            specialist_type: 专科类型
            location: 地域（None表示无地域限制，使用第一个可用的）
            
        返回:
            专科医生实例或None
        """
        try:
            if location:
                return self.specialists.get(specialist_type, {}).get(location)
            else:
                # 无地域限制：使用第一个可用的专科医生
                specialty_dict = self.specialists.get(specialist_type, {})
                if specialty_dict:
                    # 随机选择一个地域的专科医生
                    locations = list(specialty_dict.keys())
                    if locations:
                        selected_location = random.choice(locations)
                        return specialty_dict[selected_location]
            return None
        except Exception as e:
            self.logger.error(f"[DefaultStrategyHandler] 获取专科医生失败: {str(e)}")
            return None
    
    async def quick_diagnosis(
        self,
        user_input: str,
        user_id: str,
        specialist_type: str,
        location: Optional[str],
        intent: Optional[str] = None  # 添加意图参数
    ) -> str:
        """
        快速诊断（不使用数据代理）
        
        参数:
            user_input: 用户输入
            user_id: 用户ID
            specialist_type: 专科类型
            location: 地域（None表示无地域限制）
            
        返回:
            str: 诊断结果
        """
        try:
            self.logger.info(f"[DefaultStrategyHandler] 开始快速诊断: {specialist_type} - {location if location else '通用'}")
            
            # 获取专科医生实例
            specialist = self._get_specialist(specialist_type, location)
            
            if not specialist:
                return "抱歉，暂时无法为您提供诊断服务。"
            
            # 直接使用LLM进行诊断（不使用数据）
            # 注意：传入空的数据地址列表，表示不使用数据
            from agents.utils.shared_context import SharedContext
            
            # 创建共享上下文，需要提供必需的参数
            # 使用传入的意图，如果没有则使用默认值
            context_intent = intent if intent else "内科咨询"
            shared_context = SharedContext(
                user_id=user_id,
                intent=context_intent,
                user_input=user_input,
                user_info={}  # 默认策略不需要用户信息
            )
            
            result = await specialist.execute(
                user_input=user_input,
                user_id=user_id,
                data_addresses=[],  # 空的数据地址列表，表示不使用数据
                shared_context=shared_context
            )
            
            # 提取诊断结果文本
            if isinstance(result, dict):
                # 检查是否有错误
                if "error" in result:
                    error_msg = result.get("error", "诊断失败")
                    self.logger.error(f"[DefaultStrategyHandler] 专科医生返回错误: {error_msg}")
                    return f"抱歉，诊断过程中出现了错误：{error_msg}"
                
                # 提取诊断内容
                diagnosis = result.get("diagnosis")
                if isinstance(diagnosis, dict):
                    # 如果diagnosis是字典，提取其中的文本内容
                    diagnosis_text = diagnosis.get("text", diagnosis.get("content", diagnosis.get("diagnosis", str(diagnosis))))
                elif isinstance(diagnosis, str):
                    diagnosis_text = diagnosis
                else:
                    # 尝试从其他字段提取
                    diagnosis_text = result.get("summary", result.get("reasoning", str(result)))
            else:
                diagnosis_text = str(result)
            
            # 确保返回的是非空字符串
            if not diagnosis_text or not diagnosis_text.strip():
                diagnosis_text = "抱歉，未能生成有效的诊断结果。"
            
            self.logger.info(f"[DefaultStrategyHandler] 快速诊断完成，结果长度: {len(diagnosis_text)} 字符")
            
            return diagnosis_text
            
        except Exception as e:
            self.logger.error(f"[DefaultStrategyHandler] 快速诊断失败: {str(e)}", exc_info=True)
            return f"抱歉，诊断过程中出现了错误：{str(e)}"

