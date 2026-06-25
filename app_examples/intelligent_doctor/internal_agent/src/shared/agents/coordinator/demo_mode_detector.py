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
演示模式检测器 (DemoModeDetector)
===============================

用于检测用户输入是否与糖尿病相关，以触发演示模式。

作者: QSIR
版本: 1.0
"""

import logging
from typing import List


# 糖尿病关键词列表
DIABETES_KEYWORDS = [
    "糖尿病",
    "血糖",
    "血糖高",
    "血糖低",
    "高血糖",
    "低血糖",
    "糖尿病症状",
    "糖尿病并发症",
    "胰岛素",
    "糖化血红蛋白",
    "HbA1c",
    "空腹血糖",
    "餐后血糖",
    "糖尿病前期",
    "1型糖尿病",
    "2型糖尿病",
    "II型糖尿病",
    "糖尿病肾病",
    "糖尿病视网膜病变",
    "糖尿病足",
    "糖尿病神经病变",
    "多饮",
    "多食",
    "多尿",
    "体重下降",
    "糖尿病治疗",
    "降糖",
    "降血糖",
    "二甲双胍",
    "格列齐特",
    "胰岛素注射",
    # 扩展：糖尿病典型症状的同义词和描述
    "口渴",  # 多饮的同义词
    "喝水多",
    "喝水很多",
    "饮水量",
    "尿量",
    "尿量多",
    "尿量增加",
    "尿频",
    "体重减轻",
    "体重减少",
    "消瘦",
    "容易饿",
    "食量大",
    "视力模糊",
    "视力下降",
    "疲劳",
    "乏力",
    "容易疲劳",
    "伤口愈合慢",
    "皮肤瘙痒"
]


class DemoModeDetector:
    """演示模式检测器"""
    
    def __init__(self):
        """初始化演示模式检测器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.diabetes_keywords = DIABETES_KEYWORDS
        self.logger.info(f"[DemoModeDetector] 初始化完成，关键词数量: {len(self.diabetes_keywords)}")
    
    def is_diabetes_related(self, user_input: str) -> bool:
        """
        检测用户输入是否与糖尿病相关
        
        参数:
            user_input: 用户输入
            
        返回:
            bool: 是否与糖尿病相关
        """
        if not user_input:
            return False
        
        user_input_lower = user_input.lower()
        
        # 检查是否包含糖尿病关键词
        for keyword in self.diabetes_keywords:
            if keyword in user_input_lower:
                self.logger.info(f"[DemoModeDetector] 检测到糖尿病关键词: {keyword}")
                return True
        
        # 检查是否同时包含多个糖尿病典型症状（症状组合检测）
        # 糖尿病典型症状：多饮、多尿、多食、体重下降
        diabetes_symptoms = [
            ["口渴", "喝水", "饮水量", "多饮"],
            ["尿量", "多尿", "尿频", "尿量增加", "尿量多"],
            ["体重下降", "体重减轻", "体重减少", "消瘦", "下降"],  # 注意："下降"需要结合上下文
            ["容易饿", "多食", "食量大"]
        ]
        
        matched_symptom_groups = 0
        matched_symptoms = []
        for symptom_group in diabetes_symptoms:
            for symptom in symptom_group:
                if symptom in user_input_lower:
                    # 对于"下降"关键词，需要确保上下文中有"体重"相关词汇
                    if symptom == "下降":
                        if "体重" in user_input_lower or "瘦" in user_input_lower:
                            matched_symptom_groups += 1
                            matched_symptoms.append(f"体重{symptom}")
                            self.logger.info(f"[DemoModeDetector] 检测到糖尿病症状: 体重{symptom}")
                            break
                    else:
                        matched_symptom_groups += 1
                        matched_symptoms.append(symptom)
                        self.logger.info(f"[DemoModeDetector] 检测到糖尿病症状: {symptom}")
                        break
        
        # 如果同时匹配2个或以上症状组，认为是糖尿病相关
        if matched_symptom_groups >= 2:
            self.logger.info(f"[DemoModeDetector] 检测到多个糖尿病症状组合（{matched_symptom_groups}个: {matched_symptoms}），判定为糖尿病相关")
            return True
        
        return False
    
    def get_matched_keywords(self, user_input: str) -> List[str]:
        """
        获取匹配的糖尿病关键词
        
        参数:
            user_input: 用户输入
            
        返回:
            List[str]: 匹配的关键词列表
        """
        if not user_input:
            return []
        
        user_input_lower = user_input.lower()
        matched = []
        
        for keyword in self.diabetes_keywords:
            if keyword in user_input_lower:
                matched.append(keyword)
        
        return matched

