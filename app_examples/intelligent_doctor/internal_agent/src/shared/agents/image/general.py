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
通用影像分析智能体 (ImageAnalysisAgent)
=====================================

提供通用的医学影像分析功能。

主要功能：
1. 通用影像分析
2. 影像特征提取
3. 异常检测
4. 诊断建议

作者: QSIR
版本: 1.0
"""

import logging
from typing import Dict, Any, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.base_agent import BaseAgent


class ImageAnalysisAgent(BaseAgent):
    """
    通用影像分析智能体
    
    提供通用的医学影像分析功能，包括：
    - 通用影像分析
    - 影像特征提取
    - 异常检测
    - 诊断建议
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        初始化通用影像分析智能体
        
        参数：
            model_config (Dict[str, Any]): 模型配置
        """
        super().__init__(model_config)
        self.agent_id = "image_analysis"
        self.name = "通用影像分析智能体"
        self.specialization = "通用影像分析"
        
        self.logger.info(f"[{self.name}] 初始化完成")
    
    async def execute(self, user_input: str, user_id: str, user_info: Optional[Dict] = None) -> Any:
        """
        执行通用影像分析
        
        参数：
            user_input (str): 用户输入
            user_id (str): 用户ID
            user_info (Dict, optional): 用户信息，包含影像数据
            
        返回：
            Any: 影像分析结果
        """
        try:
            # 验证输入
            if not self.validate_input(user_input):
                return "[ERROR] 输入无效，请提供有效的影像分析请求。"
            
            # 获取影像数据
            images = user_info.get("images", []) if user_info else []
            if not images:
                return "[ERROR] 没有可分析的影像数据。"
            
            # 获取对话历史
            context = self.get_context_from_memory(user_id)
            
            # 构建影像分析提示
            analysis_prompt = self._build_analysis_prompt(user_input, images, context)
            
            # 调用LLM进行分析
            analysis = await self.caller(analysis_prompt, self.model_config)
            
            # 过滤掉"Thinking"内容，只保留最终分析结果
            analysis = self._filter_thinking_content(analysis)
            
            # 记录对话轮次
            self.add_turn_to_memory(user_id, user_input, self.name, f"分析了{len(images)}张影像")
            
            # 构建分析结果
            result = {
                "analysis": analysis,
                "specialization": self.specialization,
                "image_count": len(images),
                "features": await self._extract_features(images),
                "recommendations": await self._generate_recommendations(analysis)
            }
            
            self.logger.info(f"[{self.name}] 影像分析完成")
            return result
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 执行错误：{str(e)}")
            return f"[ERROR] 影像分析错误：{str(e)}"
    
    def _build_analysis_prompt(self, user_input: str, images: List[Dict[str, Any]], context: str) -> str:
        """
        构建影像分析提示
        
        参数：
            user_input (str): 用户输入
            images (List[Dict[str, Any]]): 影像数据
            context (str): 对话上下文
            
        返回：
            str: 分析提示
        """
        # 格式化影像信息
        images_info = ""
        for i, img in enumerate(images):
            images_info += f"\n影像 {i+1}:\n"
            images_info += f"- 医院: {img.get('hospital_name', '未知')}\n"
            images_info += f"- 类型: {img.get('image_type', '未知')}\n"
            images_info += f"- 数据: {type(img.get('image', None)).__name__}\n"
        
        prompt = f"""作为专业的医学影像分析专家，请以医生对患者对话的方式，分析以下影像。

重要要求：
1. 必须严格按照指定格式，包含所有标记（[影像质量评估]、[影像特征描述]、[诊断建议]、[进一步检查]）
2. 每个部分都要有具体内容，不能为空
3. 语言要温暖、专业、条理清晰
4. 报告长度控制在700字以内
5. 使用适当的分段和标记

用户请求：{user_input}

对话历史：
{context}

影像信息：
{images_info}

请严格按照以下格式生成影像分析报告：

**[影像质量评估]**
- 评估影像的清晰度和质量
- 对影像质量的整体评价

**[影像特征描述]**
- 描述影像中的主要特征
- 识别可能的异常或病变
- 用患者能理解的语言解释

**[诊断建议]**
- 基于影像的初步诊断建议
- 生活方式调整建议
- 注意事项说明

**[进一步检查]**
- 建议的进一步检查项目
- 复查时间安排
- 随访计划
- 后续随访建议"""
        
        return prompt
    
    def _filter_thinking_content(self, content: str) -> str:
        """
        过滤掉"Thinking"内容和提示要求，只保留最终分析结果
        
        参数：
            content (str): 原始LLM响应内容
            
        返回：
            str: 过滤后的内容
        """
        try:
            if not content:
                return content
            
            lines = content.split('\n')
            filtered_lines = []
            in_thinking = False
            in_final_response = False
            in_requirements = False
            
            for line in lines:
                original_line = line  # 保留原始行（包含换行符）
                line = line.strip()
                
                # 检测Thinking开始
                if "Thinking" in line or "思考" in line:
                    in_thinking = True
                    continue
                
                # 检测Final Response开始
                if "Final Response" in line or "最终响应" in line or "最终回答" in line:
                    in_thinking = False
                    in_final_response = True
                    continue
                
                # 检测重要要求开始
                if "重要要求" in line or "**重要要求**" in line:
                    in_requirements = True
                    continue
                
                # 检测分析报告格式开始（跳过提示要求部分）
                if ("**影像质量评估**" in line or
                    "**影像特征描述**" in line or
                    "**诊断建议**" in line or
                    "**进一步检查**" in line or
                    "**关怀话语**" in line or
                    "**[影像质量评估]**" in line or
                    "**[影像特征描述]**" in line or
                    "**[诊断建议]**" in line or
                    "**[进一步检查]**" in line or
                    "**[关怀话语]**" in line):
                    in_requirements = False
                    in_final_response = True
                    # 保留格式标题行，确保有换行符
                    if not line.startswith("**"):
                        filtered_lines.append("")  # 添加空行
                    filtered_lines.append(line)
                    continue
                
                # 如果还在Thinking阶段，跳过
                if in_thinking and not in_final_response:
                    continue
                
                # 如果在重要要求阶段，跳过
                if in_requirements:
                    continue
                
                # 保留最终响应内容
                if in_final_response or (not in_thinking and not in_requirements):
                    # 如果是空行，保留空行以维持格式
                    if not line:
                        filtered_lines.append("")
                    else:
                        filtered_lines.append(line)
            
            # 如果成功提取到最终响应，返回
            if filtered_lines:
                result = '\n'.join(filtered_lines)
                # 确保格式标题前后有适当的空行
                import re
                # 处理格式标题（带或不带方括号）
                result = re.sub(r'\*\*影像质量评估\*\*', '\n**影像质量评估**', result)
                result = re.sub(r'\*\*\[影像质量评估\]\*\*', '\n**[影像质量评估]**', result)
                result = re.sub(r'\*\*影像特征描述\*\*', '\n\n**影像特征描述**', result)
                result = re.sub(r'\*\*\[影像特征描述\]\*\*', '\n\n**[影像特征描述]**', result)
                result = re.sub(r'\*\*诊断建议\*\*', '\n\n**诊断建议**', result)
                result = re.sub(r'\*\*\[诊断建议\]\*\*', '\n\n**[诊断建议]**', result)
                result = re.sub(r'\*\*进一步检查\*\*', '\n\n**进一步检查**', result)
                result = re.sub(r'\*\*\[进一步检查\]\*\*', '\n\n**[进一步检查]**', result)
                result = re.sub(r'\*\*关怀话语\*\*', '\n\n**关怀话语**', result)
                result = re.sub(r'\*\*\[关怀话语\]\*\*', '\n\n**[关怀话语]**', result)
                # 清理多余的空行
                result = re.sub(r'\n{3,}', '\n\n', result)
                return result.strip()
            else:
                # 如果没有找到最终响应，返回空内容
                return "分析结果生成中，请稍候..."
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 过滤thinking内容失败: {str(e)}")
            return content
    
    async def _extract_features(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        提取影像特征
        
        参数：
            images (List[Dict[str, Any]]): 影像数据
            
        返回：
            Dict[str, Any]: 特征信息
        """
        try:
            features_prompt = f"""基于以下影像信息，请提取关键特征：

影像数量：{len(images)}
影像类型：{', '.join(set(img.get('image_type', '未知') for img in images))}

请提取：
1. 主要解剖结构
2. 影像技术参数
3. 影像质量指标
4. 关键特征点
5. 异常征象

请用简洁明了的语言回答。"""
            
            features = await self.caller(features_prompt, self.model_config)
            
            return {
                "content": features,
                "category": "影像特征提取",
                "image_count": len(images)
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 特征提取失败: {str(e)}")
            return {
                "content": "特征提取失败，建议重新分析",
                "category": "影像特征提取",
                "image_count": len(images)
            }
    
    async def _generate_recommendations(self, analysis: str) -> Dict[str, Any]:
        """
        生成分析建议
        
        参数：
            analysis (str): 分析结果
            
        返回：
            Dict[str, Any]: 分析建议
        """
        try:
            recommendations_prompt = f"""基于以下影像分析结果，请提供建议：

分析结果：{analysis}

请提供：
1. 诊断建议
2. 治疗建议
3. 复查建议
4. 注意事项
5. 紧急情况处理

请用简洁明了的语言回答。"""
            
            recommendations = await self.caller(recommendations_prompt, self.model_config)
            
            return {
                "content": recommendations,
                "category": "影像分析建议",
                "priority": "high"
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 生成建议失败: {str(e)}")
            return {
                "content": "建议咨询专业医生获取详细建议",
                "category": "影像分析建议",
                "priority": "high"
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "description": "通用的影像分析智能体，提供基础的医学影像分析功能",
            "capabilities": [
                "通用影像分析",
                "影像特征提取",
                "异常检测",
                "诊断建议"
            ]
        }
