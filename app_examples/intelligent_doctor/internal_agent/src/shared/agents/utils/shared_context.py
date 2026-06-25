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
共享上下文管理
==============

用于多轮协调机制的共享上下文信息管理。
全科医生、专科医生和第三方数据代理应用共享此上下文。

作者: QSIR
版本: 2.0 - 重构版
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class SharedContext:
    """
    共享上下文信息（全科、专科、第三方数据代理共享）
    
    用于在整个诊断流程中共享信息，支持多轮协调机制。
    """
    
    # 基础信息
    user_id: str
    intent: str
    user_input: str
    user_info: Dict[str, Any]
    
    # 轮次信息
    round_number: int = 0
    max_rounds: int = 5
    
    # 数据地址历史（每轮获取的数据地址）
    data_addresses_history: List[Dict] = field(default_factory=list)
    
    # 诊断结果历史（每轮专科医生的诊断结果）
    diagnosis_results_history: List[Dict] = field(default_factory=list)
    
    # 专科医生数据需求（专科医生反馈的数据需求）
    specialist_requests: List[Dict] = field(default_factory=list)
    
    # 第三方数据代理对话历史
    data_proxy_conversation_history: List[Dict] = field(default_factory=list)
    
    # 直接医疗数据（数据代理直接返回的数据，无需通过数据存储服务）
    direct_medical_data: Optional[Dict[str, Any]] = None
    
    # 诊断状态
    diagnosis_status: str = "in_progress"  # in_progress, completed, needs_more_data
    
    def get_current_data_addresses(self) -> List[Dict]:
        """
        获取当前轮次的数据地址
        
        返回:
            List[Dict]: 当前轮次的数据地址列表
        """
        if self.data_addresses_history:
            return self.data_addresses_history[-1].get("data_addresses", [])
        return []
    
    def get_all_data_addresses(self) -> List[Dict]:
        """
        获取所有轮次的数据地址
        
        返回:
            List[Dict]: 所有轮次的数据地址列表
        """
        all_addresses = []
        for history_item in self.data_addresses_history:
            all_addresses.extend(history_item.get("data_addresses", []))
        return all_addresses
    
    def update_diagnosis_status(self, status: str):
        """
        更新诊断状态
        
        参数:
            status (str): 新的诊断状态 (in_progress, completed, needs_more_data)
        """
        self.diagnosis_status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将SharedContext转换为字典（用于序列化）
        
        返回:
            Dict[str, Any]: 字典表示
        """
        return {
            "user_id": self.user_id,
            "intent": self.intent,
            "user_input": self.user_input,
            "user_info": self.user_info,
            "round_number": self.round_number,
            "max_rounds": self.max_rounds,
            "data_addresses_history": self.data_addresses_history,
            "diagnosis_results_history": self.diagnosis_results_history,
            "specialist_requests": self.specialist_requests,
            "data_proxy_conversation_history": self.data_proxy_conversation_history,
            "direct_medical_data": self.direct_medical_data,
            "diagnosis_status": self.diagnosis_status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SharedContext":
        """
        从字典创建SharedContext（用于反序列化）
        
        参数:
            data (Dict[str, Any]): 字典数据
            
        返回:
            SharedContext: 共享上下文实例
        """
        return cls(
            user_id=data.get("user_id", ""),
            intent=data.get("intent", ""),
            user_input=data.get("user_input", ""),
            user_info=data.get("user_info", {}),
            round_number=data.get("round_number", 0),
            max_rounds=data.get("max_rounds", 5),
            data_addresses_history=data.get("data_addresses_history", []),
            diagnosis_results_history=data.get("diagnosis_results_history", []),
            specialist_requests=data.get("specialist_requests", []),
            data_proxy_conversation_history=data.get("data_proxy_conversation_history", []),
            direct_medical_data=data.get("direct_medical_data"),
            diagnosis_status=data.get("diagnosis_status", "in_progress")
        )

