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
意图识别系统 (IntentRecognition)
===============================

提供智能的意图识别功能。

主要功能：
1. 用户意图识别
2. 医疗需求分类
3. 意图置信度评估
4. 上下文感知识别

作者: QSIR
版本: 1.0
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class IntentType(Enum):
    """意图类型枚举（简化版）"""
    INTERNAL_MEDICINE_CONSULTATION = "内科咨询"
    SURGERY_CONSULTATION = "外科咨询"
    IMAGE_ANALYSIS = "影像分析"
    MEDICATION_QUERY = "药物查询"
    GENERAL_QUESTION = "一般问题"
    UNKNOWN = "未知"


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
    GENERAL = "general"


@dataclass
class IntentResult:
    """意图识别结果"""
    intent_type: IntentType
    confidence: float
    specialty: Optional[MedicalSpecialty] = None
    keywords: List[str] = None
    entities: Dict[str, Any] = None
    context: str = ""
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.entities is None:
            self.entities = {}


class IntentRecognition:
    """
    意图识别系统
    
    提供智能的意图识别功能，包括医疗需求分类和上下文感知识别。
    """
    
    def __init__(self, llm_caller=None, model_config=None):
        """
        初始化意图识别系统
        
        参数：
            llm_caller: LLM调用器
            model_config: 模型配置
        """
        self.llm_caller = llm_caller
        self.model_config = model_config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 意图关键词映射（简化版）
        self.intent_keywords = {
            IntentType.INTERNAL_MEDICINE_CONSULTATION: [
                "内科", "症状", "疼痛", "不舒服", "生病", "治疗", "咨询",
                "头痛", "发烧", "咳嗽", "胸闷", "腹痛", "恶心", "呕吐",
                "消化", "呼吸", "心血管", "内分泌", "肾脏", "心脏", "心悸",
                # ✅ 添加常见症状关键词
                "口渴", "多饮", "多尿", "尿频", "尿量", "体重下降", "体重减轻", "消瘦",
                "多食", "乏力", "疲劳", "头晕", "眩晕", "失眠", "焦虑", "抑郁",
                "腹泻", "便秘", "便血", "黑便", "黄疸", "水肿", "浮肿",
                "皮疹", "瘙痒", "脱发", "关节痛", "肌肉痛", "背痛", "腰痛",
                "感觉", "最近", "总是", "好像", "有点"  # 症状描述常用词
            ],
            IntentType.SURGERY_CONSULTATION: [
                "外科", "手术", "切除", "缝合", "创伤", "骨折",
                "骨科", "关节", "骨骼", "肌肉", "韧带"
            ],
            IntentType.IMAGE_ANALYSIS: [
                "影像", "X光", "CT", "MRI", "超声", "检查", "片子",
                "分析", "诊断", "报告", "结果", "胸部影像", "胸部检查", "影像诊断",
                "放射", "扫描"
            ],
            IntentType.MEDICATION_QUERY: [
                "药物", "药品", "用药", "剂量", "副作用", "禁忌",
                "药", "服药", "吃药", "用药指导"
            ],
            IntentType.GENERAL_QUESTION: [
                "什么", "怎么", "如何", "为什么", "是否", "能否",
                "了解", "知道", "介绍", "说明", "解释"
            ]
        }
        
        # 专科关键词映射
        self.specialty_keywords = {
            MedicalSpecialty.INTERNAL_MEDICINE: [
                "内科", "消化", "呼吸", "心血管", "内分泌", "肾脏"
            ],
            MedicalSpecialty.SURGERY: [
                "外科", "手术", "切除", "缝合", "创伤", "骨折"
            ],
            MedicalSpecialty.CARDIOLOGY: [
                "心脏", "心血管", "胸痛", "心悸", "心律不齐"
            ],
            MedicalSpecialty.NEUROLOGY: [
                "神经", "头痛", "头晕", "癫痫", "中风", "瘫痪"
            ],
            MedicalSpecialty.ONCOLOGY: [
                "肿瘤", "癌症", "化疗", "放疗", "转移"
            ],
            MedicalSpecialty.PEDIATRICS: [
                "儿科", "儿童", "婴儿", "新生儿", "发育"
            ],
            MedicalSpecialty.GYNECOLOGY: [
                "妇科", "女性", "月经", "怀孕", "分娩"
            ],
            MedicalSpecialty.ORTHOPEDICS: [
                "骨科", "关节", "骨骼", "肌肉", "韧带"
            ],
            MedicalSpecialty.RADIOLOGY: [
                "影像", "放射", "X光", "CT", "MRI", "超声"
            ],
            MedicalSpecialty.EMERGENCY: [
                "急诊", "急救", "紧急", "危险", "严重"
            ]
        }
        
        self.logger.info(f"[{self.__class__.__name__}] 初始化完成")
    
    async def recognize_intent(self, user_input: str, context: str = "") -> IntentResult:
        """
        识别用户意图
        
        参数：
            user_input (str): 用户输入
            context (str): 对话上下文
            
        返回：
            IntentResult: 意图识别结果
        """
        try:
            # 预处理输入
            processed_input = self._preprocess_input(user_input)
            
            # 基于关键词的快速识别
            keyword_result = self._recognize_by_keywords(processed_input)
            
            # 基于LLM的深度识别
            if self.llm_caller and keyword_result.confidence < 0.8:
                llm_result = await self._recognize_by_llm(processed_input, context)
                if llm_result.confidence > keyword_result.confidence:
                    keyword_result = llm_result
            
            # 提取实体信息
            entities = self._extract_entities(processed_input)
            keyword_result.entities = entities
            
            # 识别医疗专科
            specialty = self._identify_specialty(processed_input)
            keyword_result.specialty = specialty
            
            self.logger.info(f"[{self.__class__.__name__}] 识别到意图: {keyword_result.intent_type.value}, 置信度: {keyword_result.confidence}")
            
            return keyword_result
            
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 意图识别失败: {str(e)}")
            return IntentResult(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                context=context
            )
    
    def _preprocess_input(self, user_input: str) -> str:
        """
        预处理用户输入
        
        参数：
            user_input (str): 用户输入
            
        返回：
            str: 预处理后的输入
        """
        # 转换为小写
        processed = user_input.lower()
        
        # 移除标点符号
        processed = re.sub(r'[^\w\s]', '', processed)
        
        # 移除多余空格
        processed = ' '.join(processed.split())
        
        return processed
    
    def _recognize_by_keywords(self, user_input: str) -> IntentResult:
        """
        基于关键词识别意图
        
        参数：
            user_input (str): 用户输入
            
        返回：
            IntentResult: 意图识别结果
        """
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        matched_keywords = []
        
        # 定义关键词权重（简化版）
        keyword_weights = {
            IntentType.INTERNAL_MEDICINE_CONSULTATION: {
                "内科": 4.0, "症状": 3.0, "疼痛": 3.0, "不舒服": 3.0, "生病": 3.0,
                "治疗": 2.0, "咨询": 2.0, "诊断": 1.0,
                "头痛": 3.0, "发烧": 3.0, "咳嗽": 3.0, "胸闷": 3.0,
                "腹痛": 3.0, "恶心": 3.0, "呕吐": 3.0,
                "消化": 2.0, "呼吸": 2.0, "心血管": 3.0, "内分泌": 2.0, "肾脏": 2.0,
                "心脏": 3.0, "心悸": 3.0,
                # ✅ 添加常见症状关键词权重
                "口渴": 3.5, "多饮": 3.5, "多尿": 3.5, "尿频": 3.0, "尿量": 2.5,
                "体重下降": 3.5, "体重减轻": 3.5, "消瘦": 3.0,
                "多食": 3.0, "乏力": 2.5, "疲劳": 2.5, "头晕": 2.5, "眩晕": 2.5,
                "失眠": 2.5, "焦虑": 2.0, "抑郁": 2.0,
                "腹泻": 3.0, "便秘": 2.5, "便血": 3.5, "黑便": 3.5, "黄疸": 3.5,
                "水肿": 3.0, "浮肿": 3.0, "皮疹": 3.0, "瘙痒": 2.5, "脱发": 2.0,
                "关节痛": 2.5, "肌肉痛": 2.5, "背痛": 2.5, "腰痛": 2.5,
                "感觉": 1.5, "最近": 1.0, "总是": 1.5, "好像": 1.0, "有点": 1.0
            },
            IntentType.SURGERY_CONSULTATION: {
                "外科": 4.0, "手术": 4.0, "切除": 3.0, "缝合": 2.0, "创伤": 3.0, "骨折": 3.0,
                "骨科": 3.0, "关节": 2.0, "骨骼": 2.0, "肌肉": 2.0, "韧带": 2.0
            },
            IntentType.IMAGE_ANALYSIS: {
                "影像": 4.0, "胸部影像": 5.0, "影像诊断": 4.0, "胸部检查": 4.0,
                "X光": 3.0, "CT": 4.0, "MRI": 4.0, "超声": 3.0, "检查": 2.0,
                "片子": 3.0, "分析": 3.0, "诊断": 2.0, "报告": 2.0, "结果": 1.0,
                "放射": 2.0, "扫描": 3.0
            },
            IntentType.MEDICATION_QUERY: {
                "药物": 4.0, "药品": 4.0, "用药": 3.0, "剂量": 3.0, "副作用": 3.0, "禁忌": 3.0,
                "药": 2.0, "服药": 2.0, "吃药": 2.0, "用药指导": 3.0
            },
            IntentType.GENERAL_QUESTION: {
                "什么": 2.0, "怎么": 2.0, "如何": 2.0, "为什么": 2.0, "是否": 1.0, "能否": 1.0,
                "了解": 1.0, "知道": 1.0, "介绍": 1.0, "说明": 1.0, "解释": 1.0
                # ✅ 注意：症状描述词（如"感觉"、"最近"、"总是"、"好像"、"有点"）不应该匹配"一般问题"
                # 这些词只有在没有症状关键词时才可能是"一般问题"
            }
        }
        
        # ✅ 优先检查医疗相关意图（内科、外科、影像、药物），避免被"一般问题"误判
        # 医疗意图优先级更高
        medical_intents = [
            IntentType.INTERNAL_MEDICINE_CONSULTATION,
            IntentType.SURGERY_CONSULTATION,
            IntentType.IMAGE_ANALYSIS,
            IntentType.MEDICATION_QUERY
        ]
        general_intent = IntentType.GENERAL_QUESTION
        
        # 先检查医疗相关意图
        for intent_type in medical_intents:
            keywords = self.intent_keywords.get(intent_type, [])
            matches = []
            total_weight = 0.0
            
            for keyword in keywords:
                if keyword in user_input:
                    matches.append(keyword)
                    # 使用权重计算置信度
                    weight = keyword_weights.get(intent_type, {}).get(keyword, 1.0)
                    total_weight += weight
            
            if matches:
                # 使用加权平均计算置信度
                total_possible_weight = sum(keyword_weights.get(intent_type, {}).values())
                if total_possible_weight > 0:
                    confidence = total_weight / total_possible_weight
                else:
                    confidence = len(matches) / len(keywords) if keywords else 0.0
                
                # ✅ 如果匹配到医疗相关关键词，提高置信度
                if len(matches) >= 2:  # 匹配到2个或以上关键词，提高置信度
                    confidence = min(confidence * 1.2, 1.0)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent_type
                    matched_keywords = matches
        
        # ✅ 只有在没有匹配到医疗相关意图时，才检查"一般问题"
        if best_intent == IntentType.UNKNOWN or best_confidence < 0.3:
            keywords = self.intent_keywords.get(general_intent, [])
            matches = []
            total_weight = 0.0
            
            for keyword in keywords:
                if keyword in user_input:
                    matches.append(keyword)
                    weight = keyword_weights.get(general_intent, {}).get(keyword, 1.0)
                    total_weight += weight
            
            if matches:
                total_possible_weight = sum(keyword_weights.get(general_intent, {}).values())
                if total_possible_weight > 0:
                    confidence = total_weight / total_possible_weight
                else:
                    confidence = len(matches) / len(keywords) if keywords else 0.0
                
                # ✅ 如果用户输入包含症状描述词但没有医疗关键词，才可能是"一般问题"
                # 如果包含症状关键词（如"口渴"、"多尿"等），不应该被识别为"一般问题"
                symptom_keywords = ["口渴", "多饮", "多尿", "体重下降", "疼痛", "不舒服", "生病", "症状"]
                has_symptom_keywords = any(keyword in user_input for keyword in symptom_keywords)
                
                if has_symptom_keywords:
                    # 如果包含症状关键词，降低"一般问题"的置信度
                    confidence = confidence * 0.3
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = general_intent
                    matched_keywords = matches
        
        return IntentResult(
            intent_type=best_intent,
            confidence=best_confidence,
            keywords=matched_keywords
        )
    
    async def _recognize_by_llm(self, user_input: str, context: str) -> IntentResult:
        """
        基于LLM识别意图
        
        参数：
            user_input (str): 用户输入
            context (str): 对话上下文
            
        返回：
            IntentResult: 意图识别结果
        """
        try:
            prompt = f"""请分析用户输入，识别医疗意图：

用户输入：{user_input}
对话上下文：{context}

请识别以下意图类型之一：
1. 内科咨询 - 内科相关症状、疾病咨询（包括：口渴、多饮、多尿、体重下降、疼痛、不舒服、发烧、咳嗽等任何身体症状的描述）
2. 外科咨询 - 外科手术、创伤、骨科相关问题
3. 影像分析 - 医学影像（X光、CT、MRI等）分析
4. 药物查询 - 药物使用、剂量、副作用等问题
5. 一般问题 - 一般性医疗知识咨询（不包含具体症状描述的问题，如"什么是糖尿病？"）
6. 未知 - 无法识别的意图

**重要提示**：
- 如果用户输入包含任何身体症状描述（如：口渴、多饮、多尿、体重下降、疼痛、不舒服等），应该识别为"内科咨询"
- "一般问题"只适用于不包含具体症状的医疗知识咨询
- 用户描述"感觉"、"最近"、"总是"、"好像"、"有点"等词配合症状时，应该识别为"内科咨询"

请返回格式：意图类型|置信度(0-1)|关键词(用逗号分隔)

例如：内科咨询|0.9|口渴,多尿,体重下降"""
            
            print(f"[意图识别] 开始调用LLM进行意图识别...")
            response = await self.llm_caller(prompt, self.model_config)
            print(f"[意图识别] LLM意图识别调用完成，结果长度: {len(str(response))} 字符")
            
            # 解析响应
            parts = response.strip().split('|')
            if len(parts) >= 2:
                intent_type_str = parts[0].strip()
                confidence = float(parts[1].strip())
                keywords = parts[2].strip().split(',') if len(parts) > 2 else []
                
                # 转换意图类型
                try:
                    intent_type = IntentType(intent_type_str)
                except ValueError:
                    intent_type = IntentType.UNKNOWN
                
                return IntentResult(
                    intent_type=intent_type,
                    confidence=confidence,
                    keywords=keywords
                )
            
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] LLM意图识别失败: {str(e)}")
        
        return IntentResult(
            intent_type=IntentType.UNKNOWN,
            confidence=0.0
        )
    
    def _extract_entities(self, user_input: str) -> Dict[str, Any]:
        """
        提取实体信息
        
        参数：
            user_input (str): 用户输入
            
        返回：
            Dict[str, Any]: 实体信息
        """
        entities = {
            "symptoms": [],
            "body_parts": [],
            "time_expressions": [],
            "numbers": []
        }
        
        # 提取症状
        symptom_patterns = [
            r'头痛', r'发烧', r'咳嗽', r'胸闷', r'腹痛', r'恶心', r'呕吐',
            r'头晕', r'乏力', r'失眠', r'食欲不振'
        ]
        
        for pattern in symptom_patterns:
            matches = re.findall(pattern, user_input)
            entities["symptoms"].extend(matches)
        
        # 提取身体部位
        body_part_patterns = [
            r'头部', r'胸部', r'腹部', r'腰部', r'腿部', r'手臂', r'背部'
        ]
        
        for pattern in body_part_patterns:
            matches = re.findall(pattern, user_input)
            entities["body_parts"].extend(matches)
        
        # 提取时间表达式
        time_patterns = [
            r'\d+天', r'\d+周', r'\d+月', r'\d+年', r'昨天', r'今天', r'明天'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, user_input)
            entities["time_expressions"].extend(matches)
        
        # 提取数字
        number_patterns = [
            r'\d+', r'\d+\.\d+'
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, user_input)
            entities["numbers"].extend(matches)
        
        return entities
    
    def _identify_specialty(self, user_input: str) -> Optional[MedicalSpecialty]:
        """
        识别医疗专科
        
        参数：
            user_input (str): 用户输入
            
        返回：
            Optional[MedicalSpecialty]: 医疗专科
        """
        best_specialty = None
        best_confidence = 0.0
        
        for specialty, keywords in self.specialty_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in user_input)
            if matches > 0:
                confidence = matches / len(keywords)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_specialty = specialty
        
        return best_specialty if best_confidence > 0.3 else None
    
    def get_intent_statistics(self) -> Dict[str, Any]:
        """获取意图识别统计信息"""
        return {
            "supported_intents": len(IntentType),
            "supported_specialties": len(MedicalSpecialty),
            "keyword_mappings": {
                intent.value: len(keywords) 
                for intent, keywords in self.intent_keywords.items()
            }
        }
