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
医疗相关数据模型
================

定义医疗相关的数据结构。

作者: QSIR
版本: 1.0
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class MedicalSpecialty(Enum):
    """医疗专科枚举"""
    INTERNAL_MEDICINE = "internal_medicine"
    SURGERY = "surgery"
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    PEDIATRICS = "pediatrics"
    GYNECOLOGY = "gynecology"
    ORTHOPEDICS = "orthopedics"
    RADIOLOGY = "radiology"
    EMERGENCY = "emergency"


class UrgencyLevel(Enum):
    """紧急程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ExpertAdvice:
    """
    专家建议数据类
    
    用于存储医疗专家的诊断建议和后续处理建议。
    """
    diagnosis: str                    # 诊断建议
    treatment_plan: str              # 治疗方案
    follow_up_instructions: str      # 随访指导
    medication_recommendations: str  # 用药建议
    lifestyle_advice: str            # 生活方式建议
    warning_signs: str               # 危险信号
    specialist_referral: str         # 专科转诊建议
    urgency_level: UrgencyLevel      # 紧急程度
    confidence_score: float          # 置信度分数 (0-1)
    created_at: datetime             # 创建时间
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'diagnosis': self.diagnosis,
            'treatment_plan': self.treatment_plan,
            'follow_up_instructions': self.follow_up_instructions,
            'medication_recommendations': self.medication_recommendations,
            'lifestyle_advice': self.lifestyle_advice,
            'warning_signs': self.warning_signs,
            'specialist_referral': self.specialist_referral,
            'urgency_level': self.urgency_level.value,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class MedicalRecord:
    """
    医疗记录数据类
    
    用于存储患者的医疗记录信息。
    """
    record_id: str
    patient_id: str
    doctor_id: str
    specialty: MedicalSpecialty
    chief_complaint: str             # 主诉
    present_illness: str             # 现病史
    past_history: str                # 既往史
    family_history: str              # 家族史
    physical_examination: str        # 体格检查
    diagnosis: str                   # 诊断
    treatment_plan: str              # 治疗方案
    follow_up_plan: str              # 随访计划
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'record_id': self.record_id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'specialty': self.specialty.value,
            'chief_complaint': self.chief_complaint,
            'present_illness': self.present_illness,
            'past_history': self.past_history,
            'family_history': self.family_history,
            'physical_examination': self.physical_examination,
            'diagnosis': self.diagnosis,
            'treatment_plan': self.treatment_plan,
            'follow_up_plan': self.follow_up_plan,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class Symptom:
    """
    症状数据类
    
    用于存储症状信息。
    """
    symptom_id: str
    name: str
    description: str
    severity: int                     # 严重程度 (1-10)
    duration: str                     # 持续时间
    frequency: str                    # 频率
    triggers: List[str]               # 触发因素
    associated_symptoms: List[str]    # 伴随症状
    created_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'symptom_id': self.symptom_id,
            'name': self.name,
            'description': self.description,
            'severity': self.severity,
            'duration': self.duration,
            'frequency': self.frequency,
            'triggers': self.triggers,
            'associated_symptoms': self.associated_symptoms,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TreatmentPlan:
    """
    治疗方案数据类
    
    用于存储治疗方案信息。
    """
    plan_id: str
    patient_id: str
    doctor_id: str
    specialty: MedicalSpecialty
    diagnosis: str
    medications: List[Dict[str, Any]]  # 药物信息
    procedures: List[Dict[str, Any]]   # 手术/程序信息
    lifestyle_changes: List[str]       # 生活方式改变
    follow_up_schedule: List[Dict[str, Any]]  # 随访安排
    expected_outcome: str              # 预期结果
    risks_and_side_effects: str        # 风险和副作用
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'plan_id': self.plan_id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'specialty': self.specialty.value,
            'diagnosis': self.diagnosis,
            'medications': self.medications,
            'procedures': self.procedures,
            'lifestyle_changes': self.lifestyle_changes,
            'follow_up_schedule': self.follow_up_schedule,
            'expected_outcome': self.expected_outcome,
            'risks_and_side_effects': self.risks_and_side_effects,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
