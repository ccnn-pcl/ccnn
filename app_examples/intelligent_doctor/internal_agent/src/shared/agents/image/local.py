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
本地影像分析智能体 (LocalImageAgent)
===================================

专门处理本地医院的影像分析任务。

主要功能：
1. 本地医院影像分析
2. 医院特定影像处理
3. 本地数据访问
4. 隐私保护

作者: QSIR
版本: 1.0
"""

import logging
from typing import Dict, Any, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.base_agent import BaseAgent


class LocalImageAgent(BaseAgent):
    """
    本地影像分析智能体
    
    专门处理本地医院的影像分析任务，包括：
    - 本地医院影像分析
    - 医院特定影像处理
    - 本地数据访问
    - 隐私保护
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        初始化本地影像分析智能体
        
        参数：
            model_config (Dict[str, Any]): 模型配置
        """
        super().__init__(model_config)
        self.agent_id = "local_image"
        self.name = "本地影像分析智能体"
        self.specialization = "本地影像分析"
        
        self.logger.info(f"[{self.name}] 初始化完成")
    
    async def execute(self, user_input: str, user_id: str, user_info: Optional[Dict] = None) -> Any:
        """
        执行本地影像分析
        
        参数：
            user_input (str): 用户输入
            user_id (str): 用户ID
            user_info (Dict, optional): 用户信息，包含影像数据
            
        返回：
            Any: 本地影像分析结果
        """
        try:
            # 验证输入
            if not self.validate_input(user_input):
                return "[ERROR] 输入无效，请提供有效的影像分析请求。"
            
            # 获取影像数据
            images = user_info.get("images", []) if user_info else []
            if not images:
                return "[ERROR] 没有可分析的本地影像数据。"
            
            # 获取对话历史
            context = self.get_context_from_memory(user_id)
            
            # 构建本地影像分析提示
            analysis_prompt = self._build_local_analysis_prompt(user_input, images, context)
            
            # 调用LLM进行分析
            analysis = await self.caller(analysis_prompt, self.model_config)
            
            # 记录对话轮次
            self.add_turn_to_memory(user_id, user_input, self.name, f"本地分析了{len(images)}张影像")
            
            # 构建分析结果
            result = {
                "analysis": analysis,
                "specialization": self.specialization,
                "analysis_type": "local",
                "hospital_info": self._extract_hospital_info(images),
                "privacy_status": await self._check_privacy_status(images),
                "recommendations": await self._generate_local_recommendations(analysis)
            }
            
            self.logger.info(f"[{self.name}] 本地影像分析完成")
            return result
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 执行错误：{str(e)}")
            return f"[ERROR] 本地影像分析错误：{str(e)}"
    
    def _build_local_analysis_prompt(self, user_input: str, images: List[Dict[str, Any]], context: str) -> str:
        """
        构建本地影像分析提示
        
        参数：
            user_input (str): 用户输入
            images (List[Dict[str, Any]]): 影像数据
            context (str): 对话上下文
            
        返回：
            str: 分析提示
        """
        # 格式化医院信息
        hospital_info = ""
        for i, img in enumerate(images):
            hospital_info += f"\n影像 {i+1} (来自 {img.get('hospital_name', '未知医院')}):\n"
            hospital_info += f"- 医院ID: {img.get('hospital_id', '未知')}\n"
            hospital_info += f"- 影像类型: {img.get('image_type', '未知')}\n"
            hospital_info += f"- 数据格式: {type(img.get('image', None)).__name__}\n"
        
        prompt = f"""作为专业的本地医院影像分析专家，请分析以下本地影像：

用户请求：{user_input}

对话历史：
{context}

本地影像信息：
{hospital_info}

请提供详细的本地影像分析，包括：
1. 本地影像质量评估：评估本地影像的清晰度和质量
2. 医院特定分析：基于医院特点的影像分析
3. 本地数据特征：分析本地数据的特征
4. 异常发现：识别可能的异常或病变
5. 本地诊断建议：基于本地影像的诊断建议
6. 本地检查建议：建议的本地检查项目
7. 隐私保护状态：评估数据隐私保护状态
8. 本地随访建议：建议的本地随访安排

请用专业但易懂的语言回答，特别关注本地医院的特点和数据隐私。"""
        
        return prompt
    
    def _extract_hospital_info(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        提取医院信息
        
        参数：
            images (List[Dict[str, Any]]): 影像数据
            
        返回：
            Dict[str, Any]: 医院信息
        """
        try:
            hospitals = set()
            for img in images:
                hospital_name = img.get('hospital_name', '未知医院')
                hospital_id = img.get('hospital_id', '未知')
                hospitals.add((hospital_id, hospital_name))
            
            return {
                "hospital_count": len(hospitals),
                "hospitals": list(hospitals),
                "image_count": len(images)
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 提取医院信息失败: {str(e)}")
            return {
                "hospital_count": 0,
                "hospitals": [],
                "image_count": len(images)
            }
    
    async def _check_privacy_status(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        检查隐私保护状态
        
        参数：
            images (List[Dict[str, Any]]): 影像数据
            
        返回：
            Dict[str, Any]: 隐私状态
        """
        try:
            privacy_prompt = f"""基于以下本地影像信息，请评估隐私保护状态：

影像数量：{len(images)}
医院数量：{len(set(img.get('hospital_id', '未知') for img in images))}

请评估：
1. 数据隐私保护等级
2. 本地存储安全性
3. 访问控制状态
4. 数据加密状态
5. 隐私风险等级

请用简洁明了的语言回答。"""
            
            privacy_status = await self.caller(privacy_prompt, self.model_config)
            
            return {
                "content": privacy_status,
                "category": "隐私保护状态",
                "risk_level": "需要专业评估"
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 隐私状态检查失败: {str(e)}")
            return {
                "content": "隐私状态检查失败，建议重新评估",
                "category": "隐私保护状态",
                "risk_level": "需要专业评估"
            }
    
    async def _generate_local_recommendations(self, analysis: str) -> Dict[str, Any]:
        """
        生成本地分析建议
        
        参数：
            analysis (str): 分析结果
            
        返回：
            Dict[str, Any]: 本地分析建议
        """
        try:
            recommendations_prompt = f"""基于以下本地影像分析结果，请提供建议：

分析结果：{analysis}

请提供：
1. 本地诊断建议
2. 本地治疗建议
3. 本地复查建议
4. 本地注意事项
5. 隐私保护建议

请用简洁明了的语言回答。"""
            
            recommendations = await self.caller(recommendations_prompt, self.model_config)
            
            return {
                "content": recommendations,
                "category": "本地影像分析建议",
                "priority": "high"
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 生成本地建议失败: {str(e)}")
            return {
                "content": "建议咨询本地专业医生获取详细建议",
                "category": "本地影像分析建议",
                "priority": "high"
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "description": "本地影像分析智能体，专门处理本地医院的影像分析任务",
            "capabilities": [
                "本地医院影像分析",
                "医院特定影像处理",
                "本地数据访问",
                "隐私保护"
            ]
        }
