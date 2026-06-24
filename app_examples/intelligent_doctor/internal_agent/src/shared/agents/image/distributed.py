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
分布式影像分析智能体 (DistributedImageAnalysisAgent)
=================================================

专门处理分布式环境下的影像分析任务。

主要功能：
1. 分布式影像分析
2. 多节点协调
3. 负载均衡
4. 结果聚合

作者: QSIR
版本: 1.0
"""

import logging
from typing import Dict, Any, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.base_agent import BaseAgent


class DistributedImageAnalysisAgent(BaseAgent):
    """
    分布式影像分析智能体
    
    专门处理分布式环境下的影像分析任务，包括：
    - 分布式影像分析
    - 多节点协调
    - 负载均衡
    - 结果聚合
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        初始化分布式影像分析智能体
        
        参数：
            model_config (Dict[str, Any]): 模型配置
        """
        super().__init__(model_config)
        self.agent_id = "distributed_image"
        self.name = "分布式影像分析智能体"
        self.specialization = "分布式影像分析"
        
        self.logger.info(f"[{self.name}] 初始化完成")
    
    async def execute(self, user_input: str, user_id: str, user_info: Optional[Dict] = None) -> Any:
        """
        执行分布式影像分析
        
        参数：
            user_input (str): 用户输入
            user_id (str): 用户ID
            user_info (Dict, optional): 用户信息，包含影像数据
            
        返回：
            Any: 分布式影像分析结果
        """
        try:
            # 验证输入
            if not self.validate_input(user_input):
                return "[ERROR] 输入无效，请提供有效的影像分析请求。"
            
            # 获取影像数据
            images = user_info.get("images", []) if user_info else []
            if not images:
                return "[ERROR] 没有可分析的分布式影像数据。"
            
            # 获取对话历史
            context = self.get_context_from_memory(user_id)
            
            # 构建分布式影像分析提示
            analysis_prompt = self._build_distributed_analysis_prompt(user_input, images, context)
            
            # 调用LLM进行分析
            analysis = await self.caller(analysis_prompt, self.model_config)
            
            # 过滤掉"Thinking"内容，只保留最终分析结果
            analysis = self._filter_thinking_content(analysis)
            
            # 记录对话轮次
            self.add_turn_to_memory(user_id, user_input, self.name, f"分布式分析了{len(images)}张影像")
            
            # 构建分析结果
            result = {
                "analysis": analysis,
                "specialization": self.specialization,
                "analysis_type": "distributed",
                "node_info": self._extract_node_info(images),
                "load_balance_status": await self._check_load_balance_status(images),
                "aggregation_result": await self._aggregate_results(analysis),
                "recommendations": await self._generate_distributed_recommendations(analysis)
            }
            
            self.logger.info(f"[{self.name}] 分布式影像分析完成")
            return result
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 执行错误：{str(e)}")
            return f"[ERROR] 分布式影像分析错误：{str(e)}"
    
    def _build_distributed_analysis_prompt(self, user_input: str, images: List[Dict[str, Any]], context: str) -> str:
        """
        构建分布式影像分析提示
        
        参数：
            user_input (str): 用户输入
            images (List[Dict[str, Any]]): 影像数据
            context (str): 对话上下文
            
        返回：
            str: 分析提示
        """
        # 格式化节点信息
        node_info = ""
        for i, img in enumerate(images):
            node_info += f"\n节点 {i+1} (医院: {img.get('hospital_name', '未知医院')}):\n"
            node_info += f"- 节点ID: {img.get('hospital_id', '未知')}\n"
            node_info += f"- 影像类型: {img.get('image_type', '未知')}\n"
            node_info += f"- 数据大小: {len(str(img.get('image', ''))) if img.get('image') else 0} 字符\n"
        
        prompt = f"""作为专业的分布式影像分析专家，请以医生对患者对话的方式，分析以下分布式影像：

重要要求：
1. 必须严格按照指定格式，包含所有emoji标记（📋、🔍、💊、🏥）
2. 每个部分都要有具体内容，不能为空
3. 语言要温暖、专业、条理清晰
4. 报告长度控制在700字以内
5. 使用适当的emoji和分段

用户请求：{user_input}

对话历史：
{context}

分布式节点信息：
{node_info}

请生成一份条理清晰、温暖专业的分布式影像分析报告，包含以下内容：

**📋 分布式分析概述**
- 分布式环境下的分析策略
- 各节点间的协调情况评估

**[影像特征分析]**
- 分析数据的分布特征
- 识别可能的异常或病变
- 用患者能理解的语言解释

**💊 诊断建议**
- 基于分布式分析的诊断建议
- 生活方式调整建议
- 注意事项说明

**🏥 进一步检查**
- 建议的进一步检查项目
- 复查时间安排
- 随访计划
- 鼓励和安慰的话语"""
        
        return prompt
    
    def _filter_thinking_content(self, content: str) -> str:
        """
        过滤掉"Thinking"内容，只保留最终分析结果
        
        参数：
            content (str): 原始LLM响应内容
            
        返回：
            str: 过滤后的内容
        """
        try:
            if not content:
                return content
                
            # 如果包含Thinking标记，尝试提取最终响应
            if "Thinking" in content or "思考" in content:
                lines = content.split('\n')
                filtered_lines = []
                in_thinking = False
                in_final_response = False
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 检测Thinking开始
                    if "Thinking" in line or "思考" in line:
                        in_thinking = True
                        continue
                    
                    # 检测Final Response开始
                    if "Final Response" in line or "最终响应" in line or "最终回答" in line:
                        in_thinking = False
                        in_final_response = True
                        continue
                    
                    # 如果还在Thinking阶段，跳过
                    if in_thinking and not in_final_response:
                        continue
                    
                    # 保留最终响应内容
                    if in_final_response or not in_thinking:
                        filtered_lines.append(line)
                
                # 如果成功提取到最终响应，返回
                if filtered_lines:
                    return '\n'.join(filtered_lines)
                else:
                    # 如果没有找到最终响应，但有Thinking标记，返回空内容
                    return "分析结果生成中，请稍候..."
            
            # 如果没有Thinking标记，直接返回原内容
            return content
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 过滤thinking内容失败: {str(e)}")
            return content
    
    def _extract_node_info(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        提取节点信息
        
        参数：
            images (List[Dict[str, Any]]): 影像数据
            
        返回：
            Dict[str, Any]: 节点信息
        """
        try:
            nodes = {}
            for img in images:
                hospital_id = img.get('hospital_id', '未知')
                hospital_name = img.get('hospital_name', '未知医院')
                if hospital_id not in nodes:
                    nodes[hospital_id] = {
                        "node_id": hospital_id,
                        "node_name": hospital_name,
                        "image_count": 0,
                        "image_types": set()
                    }
                nodes[hospital_id]["image_count"] += 1
                nodes[hospital_id]["image_types"].add(img.get('image_type', '未知'))
            
            # 转换set为list
            for node in nodes.values():
                node["image_types"] = list(node["image_types"])
            
            return {
                "node_count": len(nodes),
                "nodes": list(nodes.values()),
                "total_images": len(images)
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 提取节点信息失败: {str(e)}")
            return {
                "node_count": 0,
                "nodes": [],
                "total_images": len(images)
            }
    
    async def _check_load_balance_status(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        检查负载均衡状态
        
        参数：
            images (List[Dict[str, Any]]): 影像数据
            
        返回：
            Dict[str, Any]: 负载均衡状态
        """
        try:
            load_prompt = f"""基于以下分布式节点信息，请评估负载均衡状态：

节点数量：{len(set(img.get('hospital_id', '未知') for img in images))}
影像总数：{len(images)}

请评估：
1. 负载分布均匀性
2. 节点处理能力
3. 数据分布合理性
4. 负载均衡策略

请用简洁明了的语言回答。"""
            
            load_status = await self.caller(load_prompt, self.model_config)
            
            return {
                "content": load_status,
                "category": "负载均衡状态",
                "node_count": len(set(img.get('hospital_id', '未知') for img in images))
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 负载均衡状态检查失败: {str(e)}")
            return {
                "content": "负载均衡状态检查失败，建议重新评估",
                "category": "负载均衡状态",
                "node_count": 0
            }
    
    async def _aggregate_results(self, analysis: str) -> Dict[str, Any]:
        """
        聚合分析结果
        
        参数：
            analysis (str): 分析结果
            
        返回：
            Dict[str, Any]: 聚合结果
        """
        try:
            aggregation_prompt = f"""基于以下分布式分析结果，请进行结果聚合：

分析结果：{analysis}

请聚合：
1. 主要发现汇总
2. 节点间一致性分析
3. 综合诊断结果
4. 性能指标汇总
5. 优化建议汇总

请用简洁明了的语言回答。"""
            
            aggregation = await self.caller(aggregation_prompt, self.model_config)
            
            return {
                "content": aggregation,
                "category": "分布式结果聚合",
                "priority": "high"
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 结果聚合失败: {str(e)}")
            return {
                "content": "结果聚合失败，建议重新分析",
                "category": "分布式结果聚合",
                "priority": "high"
            }
    
    async def _generate_distributed_recommendations(self, analysis: str) -> Dict[str, Any]:
        """
        生成分布式分析建议
        
        参数：
            analysis (str): 分析结果
            
        返回：
            Dict[str, Any]: 分布式分析建议
        """
        try:
            recommendations_prompt = f"""基于以下分布式影像分析结果，请提供建议：

分析结果：{analysis}

请提供：
1. 分布式诊断建议
2. 分布式随访建议

请用简洁明了的语言回答。"""
            
            recommendations = await self.caller(recommendations_prompt, self.model_config)
            
            return {
                "content": recommendations,
                "category": "分布式影像分析建议",
                "priority": "high"
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 生成分布式建议失败: {str(e)}")
            return {
                "content": "建议咨询专业医生获取详细分布式分析建议",
                "category": "分布式影像分析建议",
                "priority": "high"
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "description": "分布式影像分析智能体，专门处理分布式环境下的影像分析任务",
            "capabilities": [
                "分布式影像分析",
                "多节点协调",
                "负载均衡",
                "结果聚合"
            ]
        }
