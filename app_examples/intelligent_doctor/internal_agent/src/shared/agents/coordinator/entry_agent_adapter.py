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
EntryAgent适配器
================

将用户提供的标准A2A SDK EntryAgent集成到项目中，实现通过prompt进行A2A协议下的数据交互。

作者: QSIR
版本: 1.0
"""

import logging
import sys
import os
from typing import Dict, Any, Optional, AsyncIterator
from pathlib import Path

# 尝试导入标准A2A SDK
try:
    from a2a.types import AgentCard, Message, TextPart
    from a2a.client import A2AClient, A2ACardResolver
    from a2a.types import SendMessageRequest, MessageSendParams
    A2A_SDK_AVAILABLE = True
except ImportError:
    A2A_SDK_AVAILABLE = False
    logging.warning("[EntryAgentAdapter] 标准A2A SDK未安装，将无法使用EntryAgent")

logger = logging.getLogger(__name__)


class EntryAgentAdapter:
    """
    EntryAgent适配器
    
    将项目中的请求数据转换为prompt格式，通过标准A2A SDK的EntryAgent调用第三方数据代理应用。
    """
    
    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 60):
        """
        初始化EntryAgent适配器
        
        参数:
            base_url (str): 第三方数据代理应用的base_url（可以包含token参数）
            token (str, optional): JWT token（如果base_url中未包含）
            timeout (int): 超时时间（秒），默认60秒
        """
        if not A2A_SDK_AVAILABLE:
            raise ImportError("标准A2A SDK未安装，请先安装a2a包")
        
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 从base_url中提取token（如果未提供）
        if not self.token:
            self.token = self._extract_token_from_url(base_url)
    
    def _extract_token_from_url(self, url: str) -> str:
        """
        从URL中提取token参数
        
        参数:
            url (str): 包含token参数的URL
            
        返回:
            str: 提取到的token，如果不存在则返回默认值"unknown"
        """
        try:
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            token_list = query_params.get('token', [])
            
            if token_list:
                token = token_list[0]  # 取第一个值
                self.logger.info(f"从URL中提取到token: {token[:20]}...")
                return token
            else:
                self.logger.warning("URL中未找到token参数，使用默认值'unknown'")
                return "unknown"
        except Exception as e:
            self.logger.error(f"解析URL参数失败: {e}，使用默认值'unknown'")
            return "unknown"
    
    def _remove_token_from_url(self, url: str) -> str:
        """
        从URL中移除token参数，返回干净的base_url
        
        参数:
            url (str): 原始URL
            
        返回:
            str: 移除token参数后的URL
        """
        try:
            from urllib.parse import urlparse, parse_qs, urlunparse
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # 移除token参数
            if 'token' in query_params:
                del query_params['token']
            
            # 重建查询字符串
            new_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
            
            # 重建URL
            clean_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            self.logger.info(f"清理后的URL: {clean_url}")
            return clean_url
        except Exception as e:
            self.logger.error(f"清理URL参数失败: {e}，返回原始URL")
            return url
    
    def _build_prompt_from_request(self, request_data: Dict[str, Any]) -> str:
        """
        将请求数据转换为prompt格式
        
        参数:
            request_data (Dict[str, Any]): 请求数据，包含：
                - intent_type: 意图类型
                - specialty: 专科类型
                - user_id: 用户ID
                - symptoms: 症状列表
                - context: 上下文信息
                - priority: 优先级
        
        返回:
            str: 格式化的prompt字符串
        """
        intent_type = request_data.get("intent_type", "")
        specialty = request_data.get("specialty", "")
        symptoms = request_data.get("symptoms", [])
        context = request_data.get("context", {})
        conversation_round = context.get("conversation_round", 1)
        symptom_description = context.get("symptom_description", "")
        
        # 构建prompt
        prompt_parts = []
        
        # 基本信息
        prompt_parts.append(f"用户意图: {intent_type}")
        if specialty:
            prompt_parts.append(f"专科类型: {specialty}")
        
        # 症状信息
        if symptoms:
            prompt_parts.append(f"症状: {', '.join(symptoms)}")
        if symptom_description:
            prompt_parts.append(f"症状描述: {symptom_description}")
        
        # 上下文信息
        if conversation_round > 1:
            prompt_parts.append(f"对话轮次: 第{conversation_round}轮")
            previous_addresses = context.get("previous_data_addresses", [])
            if previous_addresses:
                prompt_parts.append(f"之前已获取的数据地址数量: {len(previous_addresses)}")
        
        # 特殊请求（专科医生数据需求）
        specialist_requests = context.get("specialist_requests", [])
        if specialist_requests:
            prompt_parts.append(f"\n专科医生数据需求:")
            for i, req in enumerate(specialist_requests, 1):
                if isinstance(req, dict):
                    data_type = req.get("data_type", "")
                    description = req.get("description", "")
                    location = req.get("location", "")
                    priority = req.get("priority", "")
                    
                    # 明确标识健康监测数据需求
                    if data_type == "健康监测数据":
                        prompt_parts.append(f"  {i}. 【重要】需要提供健康监测数据")
                        prompt_parts.append(f"     数据类型: 健康监测数据")
                        if description:
                            prompt_parts.append(f"     需求说明: {description}")
                        if location:
                            prompt_parts.append(f"     地域: {location}")
                        if priority:
                            prompt_parts.append(f"     优先级: {priority}")
                    else:
                        prompt_parts.append(f"  {i}. 数据类型: {data_type}")
                        if description:
                            prompt_parts.append(f"     需求说明: {description}")
                else:
                    prompt_parts.append(f"  {i}. {req}")
            
            # 如果包含健康监测数据需求，在prompt末尾明确提示
            has_health_monitoring = any(
                isinstance(req, dict) and req.get("data_type") == "健康监测数据"
                for req in specialist_requests
            )
            if has_health_monitoring:
                prompt_parts.append(f"\n【重要提示】本次请求需要提供健康监测数据，请直接返回健康监测数据（has_direct_data: true）")
        
        # 组合prompt
        prompt = "\n".join(prompt_parts)
        
        # 打印构建的prompt（用于调试）
        self.logger.info(f"[EntryAgentAdapter] 构建的prompt长度: {len(prompt)} 字符")
        if specialist_requests:
            self.logger.info(f"[EntryAgentAdapter] 专科医生数据需求数量: {len(specialist_requests)}")
            for req in specialist_requests:
                if isinstance(req, dict) and req.get("data_type") == "健康监测数据":
                    self.logger.info(f"[EntryAgentAdapter] [成功] Prompt中包含健康监测数据需求")
        
        self.logger.debug(f"构建的prompt: {prompt}")
        return prompt
    
    def _parse_response_from_message(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        从EntryAgent的响应中解析数据地址等信息
        
        标准A2A SDK的响应格式可能是：
        1. Message对象，包含parts字段（TextPart等）
        2. 包含result字段的字典
        3. 直接包含data_addresses的字典
        4. 包含message字段的文本响应
        
        参数:
            response (Dict[str, Any]): EntryAgent返回的响应
        
        返回:
            Dict[str, Any]: 标准化的响应数据，包含：
                - success: 是否成功
                - message: 响应消息
                - data_addresses: 数据地址列表
                - needs_more_info: 是否需要更多信息
                - question: 需要询问用户的问题
        """
        result = {
            "success": False,
            "message": "",
            "data_addresses": [],
            "needs_more_info": False,
            "question": None
        }
        
        if not isinstance(response, dict):
            self.logger.warning(f"[EntryAgentAdapter] 响应格式不是字典: {type(response)}")
            return result
        
        # 尝试从Message的parts中提取文本内容
        if "parts" in response:
            parts = response.get("parts", [])
            message_texts = []
            for part in parts:
                if isinstance(part, dict):
                    if part.get("type") == "text" or "text" in part:
                        message_texts.append(part.get("text", ""))
                    elif "content" in part:
                        message_texts.append(part.get("content", ""))
            
            if message_texts:
                # 尝试解析JSON格式的文本
                combined_text = " ".join(message_texts)
                try:
                    import json
                    parsed = json.loads(combined_text)
                    if isinstance(parsed, dict):
                        response = parsed
                except:
                    # 如果不是JSON，将文本作为message
                    result["message"] = combined_text
                    result["success"] = True
                    return result
        
        # 尝试从不同位置解析响应
        # 0. 如果响应包含task.result字段（A2A协议中task包含result）
        if "task" in response:
            task = response.get("task", {})
            if isinstance(task, dict) and "result" in task:
                task_result = task.get("result", {})
                if isinstance(task_result, dict):
                    self.logger.info(f"[EntryAgentAdapter] 从task.result中提取数据")
                    # 递归处理task.result
                    return self._parse_response_from_message(task_result)
        
        # 1. 如果响应包含result字段（标准A2A协议格式）
        if "result" in response:
            result_data = response["result"]
            if isinstance(result_data, dict):
                # 1.1. 首先检查result.artifacts[].parts[].text中是否包含JSON格式的datas
                # 这是A2A协议中数据代理应用返回数据的常见格式
                if "artifacts" in result_data:
                    artifacts = result_data.get("artifacts")
                    # 处理artifacts为None的情况
                    if artifacts is None:
                        artifacts = []
                    elif not isinstance(artifacts, list):
                        self.logger.warning(f"[EntryAgentAdapter] artifacts不是列表类型: {type(artifacts)}")
                        artifacts = []
                    
                    for artifact in artifacts:
                        if isinstance(artifact, dict) and "parts" in artifact:
                            parts = artifact.get("parts", [])
                            for part in parts:
                                if isinstance(part, dict):
                                    text = part.get("text", "") or part.get("content", "")
                                    if text:
                                        # ✅ 修复：检查多种数据格式
                                        # 1. 检查datas字段（第一轮数据地址格式）
                                        has_datas = ("datas" in text or '"datas"' in text or "'datas'" in text)
                                        # 2. 检查health_monitoring字段（第二轮健康监测数据格式）
                                        has_health_monitoring = ("health_monitoring" in text or '"health_monitoring"' in text)
                                        # 3. 检查medical_data字段（直接医疗数据格式）
                                        has_medical_data = ("medical_data" in text or '"medical_data"' in text)
                                        
                                        if has_datas or has_health_monitoring or has_medical_data:
                                            try:
                                                import json
                                                # 尝试解析JSON（处理可能包含换行符的JSON字符串）
                                                text_cleaned = text.strip()
                                                parsed = json.loads(text_cleaned)
                                                
                                                if isinstance(parsed, dict):
                                                    # 情况1：包含datas字段（数据地址格式）
                                                    if "datas" in parsed:
                                                        self.logger.info(f"[EntryAgentAdapter] 从result.artifacts[].parts[].text中解析到datas字段")
                                                        print(f"[EntryAgentAdapter] [成功] 从artifacts的parts中解析到datas字段")
                                                        print(f"[EntryAgentAdapter] 解析到的datas数量: {len(parsed.get('datas', []))}")
                                                        # 递归调用自己处理解析后的数据
                                                        return self._parse_response_from_message(parsed)
                                                    
                                                    # 情况2：包含health_monitoring字段（健康监测数据格式）
                                                    elif "health_monitoring" in parsed:
                                                        self.logger.info(f"[EntryAgentAdapter] ✅ 从artifacts中解析到health_monitoring字段")
                                                        print(f"[EntryAgentAdapter] ✅ [成功] 从artifacts的parts中解析到health_monitoring字段")
                                                        # 转换为medical_data格式，保留所有字段
                                                        medical_data = {
                                                            "health_monitoring": parsed.get("health_monitoring", {}),
                                                            "available_data_types": parsed.get("available_data_types", ["健康监测数据"]),
                                                            "location": parsed.get("location", ""),
                                                            # ✅ 对于健康监测数据，sources应该标识为"健康监测数据"而不是医院名称
                                                            "sources": ["健康监测数据"]
                                                        }
                                                        result["success"] = True
                                                        result["has_direct_data"] = True
                                                        result["medical_data"] = medical_data
                                                        result["data_addresses"] = []  # 健康监测数据不需要数据地址
                                                        self.logger.info(f"[EntryAgentAdapter] ✅ 成功提取健康监测数据")
                                                        print(f"[EntryAgentAdapter] ✅ 健康监测数据已提取，has_direct_data=true")
                                                        # 打印健康监测数据预览
                                                        health_data = medical_data.get("health_monitoring", {})
                                                        if health_data:
                                                            print(f"[EntryAgentAdapter] 健康监测数据字段: {list(health_data.keys())}")
                                                        print(f"[EntryAgentAdapter] 数据来源: {medical_data.get('sources', [])}")
                                                        return result
                                                    
                                                    # 情况3：包含medical_data字段（直接医疗数据格式）
                                                    elif "medical_data" in parsed:
                                                        self.logger.info(f"[EntryAgentAdapter] 从artifacts中解析到medical_data字段")
                                                        print(f"[EntryAgentAdapter] [成功] 从artifacts的parts中解析到medical_data字段")
                                                        result["success"] = True
                                                        result["has_direct_data"] = True
                                                        result["medical_data"] = parsed.get("medical_data", {})
                                                        result["data_addresses"] = []
                                                        return result
                                                    
                                                    # 情况4：如果整个parsed就是医疗数据（包含health_monitoring等字段，但没有明确的medical_data包装）
                                                    elif "health_monitoring" in parsed or ("available_data_types" in parsed and any("健康监测" in str(dt) for dt in parsed.get("available_data_types", []))):
                                                        self.logger.info(f"[EntryAgentAdapter] ✅ 从artifacts中解析到医疗数据（直接格式）")
                                                        print(f"[EntryAgentAdapter] ✅ [成功] 从artifacts的parts中解析到医疗数据（直接格式）")
                                                        result["success"] = True
                                                        result["has_direct_data"] = True
                                                        result["medical_data"] = parsed
                                                        result["data_addresses"] = []
                                                        self.logger.info(f"[EntryAgentAdapter] ✅ 成功提取医疗数据")
                                                        print(f"[EntryAgentAdapter] ✅ 医疗数据已提取，has_direct_data=true")
                                                        return result
                                                    
                                            except (json.JSONDecodeError, ValueError) as e:
                                                self.logger.warning(f"[EntryAgentAdapter] artifacts中parts的text不是有效JSON: {e}")
                                                self.logger.debug(f"[EntryAgentAdapter] 尝试解析的text内容: {text[:200]}...")
                                                continue
                
                # 1.2. 处理服务返回的status字段（A2A协议中status包含state和message）
                if "status" in result_data:
                    status = result_data["status"]
                    if isinstance(status, dict):
                        # 处理state字段（可能为"success"、"failed"等）
                        state = status.get("state", "")
                        if state == "success" or state == "completed":
                            result["success"] = True
                        elif state == "failed" or state == "error":
                            result["success"] = False
                            # 提取错误消息
                            status_message = status.get("message", {})
                            if isinstance(status_message, dict):
                                # 如果message是Message对象，提取parts中的text
                                parts = status_message.get("parts", [])
                                if parts and isinstance(parts, list):
                                    error_texts = []
                                    for part in parts:
                                        if isinstance(part, dict) and "text" in part:
                                            error_texts.append(part.get("text", ""))
                                    if error_texts:
                                        result["message"] = " ".join(error_texts)
                                        self.logger.warning(f"[EntryAgentAdapter] 数据代理应用返回错误: {result['message']}")
                                        print(f"[EntryAgentAdapter] [错误] 数据代理应用返回错误: {result['message']}")
                                else:
                                    result["message"] = str(status_message)
                            elif isinstance(status_message, str):
                                result["message"] = status_message
                        else:
                            # 如果没有state字段，使用success字段
                            result["success"] = result_data.get("success", True)
                    else:
                        result["success"] = result_data.get("success", True)
                else:
                    # 如果没有status字段，直接处理state字段（向后兼容）
                    state = result_data.get("state", "")
                    if state == "success" or state == "completed":
                        result["success"] = True
                    elif state == "failed" or state == "error":
                        result["success"] = False
                    else:
                        # 如果没有state字段，使用success字段
                        result["success"] = result_data.get("success", True)
                
                # 处理message字段（可能是字符串或字典）
                message_value = result_data.get("message", "")
                if isinstance(message_value, dict):
                    # 如果是字典，尝试提取text字段或parts中的text
                    if "text" in message_value:
                        result["message"] = message_value.get("text", "")
                    elif "parts" in message_value:
                        parts = message_value.get("parts", [])
                        if parts and isinstance(parts, list):
                            texts = []
                            for part in parts:
                                if isinstance(part, dict) and "text" in part:
                                    texts.append(part.get("text", ""))
                            if texts:
                                result["message"] = " ".join(texts)
                    else:
                        result["message"] = str(message_value)
                else:
                    result["message"] = str(message_value) if message_value else ""
                
                # 提取data_addresses（可能在result中，也可能在history中）
                result["data_addresses"] = result_data.get("data_addresses", [])
                if not result["data_addresses"] and "history" in result_data:
                    # 尝试从history中提取数据地址
                    history = result_data.get("history", [])
                    for item in history:
                        if isinstance(item, dict) and "data_addresses" in item:
                            result["data_addresses"].extend(item.get("data_addresses", []))
                
                result["needs_more_info"] = result_data.get("needs_more_info", False)
                result["question"] = result_data.get("question")
                
                # 如果任务失败，记录错误信息
                if not result["success"] and result["message"]:
                    self.logger.warning(f"[EntryAgentAdapter] 任务失败: {result['message']}")
                
                return result
        
        # 2. 如果响应包含datas字段（数据代理应用的真实格式）
        # 注意：A2A协议可能将响应包装在parts的text中，需要先尝试解析JSON
        if "datas" in response:
            result["success"] = True
            result["message"] = response.get("message", "数据地址匹配成功")
            
            # 转换datas格式为data_addresses格式
            datas = response.get("datas", [])
            # 保留顶层access_token作为后备（向后兼容）
            fallback_access_token = response.get("access_token", "")
            
            # 增强日志：显示顶层access_token提取情况
            if fallback_access_token:
                self.logger.info(f"[EntryAgentAdapter] [成功] 从响应顶层提取到fallback access_token: {fallback_access_token[:30]}... (长度: {len(fallback_access_token)})")
                print(f"[EntryAgentAdapter] [成功] 从响应顶层提取到fallback access_token: {fallback_access_token[:30]}... (长度: {len(fallback_access_token)})")
            else:
                self.logger.warning(f"[EntryAgentAdapter] [警告] 响应顶层未找到access_token")
                print(f"[EntryAgentAdapter] [警告] 响应顶层未找到access_token")
            
            data_addresses = []
            for data_item in datas:
                # 优先使用data_item中的access_token，如果没有则使用顶层token（向后兼容）
                item_access_token = data_item.get("access_token", "") or fallback_access_token
                
                # 增强日志：显示access_token提取过程
                if data_item.get("access_token"):
                    self.logger.info(f"[EntryAgentAdapter] [成功] 数据地址 {data_item.get('hospital_name', 'N/A')} 从data_item中提取到access_token: {data_item.get('access_token')[:30]}...")
                    print(f"[EntryAgentAdapter] [成功] 数据地址 {data_item.get('hospital_name', 'N/A')} 从data_item中提取到access_token")
                elif fallback_access_token:
                    self.logger.info(f"[EntryAgentAdapter] [警告] 数据地址 {data_item.get('hospital_name', 'N/A')} 使用顶层fallback access_token: {fallback_access_token[:30]}...")
                    print(f"[EntryAgentAdapter] [警告] 数据地址 {data_item.get('hospital_name', 'N/A')} 使用顶层fallback access_token")
                else:
                    self.logger.warning(f"[EntryAgentAdapter] [失败] 数据地址 {data_item.get('hospital_name', 'N/A')} 未找到access_token（data_item和顶层都没有）")
                    print(f"[EntryAgentAdapter] [失败] 数据地址 {data_item.get('hospital_name', 'N/A')} 未找到access_token")
                
                # 转换格式：从数据代理应用的格式转换为医疗应用期望的格式
                data_address = {
                    "data_type": data_item.get("data_types", ""),
                    "address": data_item.get("data_service_address", ""),
                    "location": "beijing" if "北京" in data_item.get("hospital_location", "") else "shanghai" if "上海" in data_item.get("hospital_location", "") else "",
                    "hospital": data_item.get("hospital_name", ""),
                    "department": data_item.get("department", ""),
                    "access_token": item_access_token  # [成功] 使用每个data_item自己的access_token
                }
                data_addresses.append(data_address)
                
                # 打印最终使用的access_token
                if item_access_token:
                    self.logger.info(f"[EntryAgentAdapter] 数据地址 {data_item.get('hospital_name', 'N/A')} 最终使用access_token: {item_access_token[:30]}... (长度: {len(item_access_token)})")
                    print(f"[EntryAgentAdapter]   最终access_token: {item_access_token[:30]}... (长度: {len(item_access_token)})")
                else:
                    self.logger.warning(f"[EntryAgentAdapter] [警告] 数据地址 {data_item.get('hospital_name', 'N/A')} 的access_token为空，MCP连接可能失败")
                    print(f"[EntryAgentAdapter] [警告] access_token为空，MCP连接可能失败")
            
            result["data_addresses"] = data_addresses
            result["needs_more_info"] = response.get("needs_more_info", False)
            result["question"] = response.get("question")
            
            # 提取medical_data和has_direct_data（第二轮请求可能直接返回医疗数据）
            if "medical_data" in response:
                result["medical_data"] = response.get("medical_data")
                result["has_direct_data"] = response.get("has_direct_data", True)
                self.logger.info(f"[EntryAgentAdapter] 检测到直接医疗数据（从datas字段解析）")
                print(f"[EntryAgentAdapter] [成功] 检测到直接医疗数据，将跳过数据存储服务请求")
            
            self.logger.info(f"[EntryAgentAdapter] 解析到 {len(data_addresses)} 个数据地址（从datas字段）")
            print(f"[EntryAgentAdapter] [成功] 成功解析datas字段，转换了 {len(data_addresses)} 个数据地址")
            return result
        
        # 2.5. 如果响应在parts的text中包含JSON格式的datas（A2A协议包装的情况）
        # 检查是否在parts的text中包含了datas字段的JSON
        if "parts" in response:
            parts = response.get("parts", [])
            for part in parts:
                if isinstance(part, dict):
                    text = part.get("text", "") or part.get("content", "")
                    if text and ("datas" in text or '"datas"' in text):
                        try:
                            import json
                            # 尝试解析JSON
                            parsed = json.loads(text)
                            if isinstance(parsed, dict) and "datas" in parsed:
                                self.logger.info(f"[EntryAgentAdapter] 从parts的text中解析到datas字段")
                                # 递归调用自己处理解析后的数据
                                return self._parse_response_from_message(parsed)
                        except (json.JSONDecodeError, ValueError) as e:
                            self.logger.debug(f"[EntryAgentAdapter] parts中的text不是有效JSON: {e}")
                            continue
        
        # 3. 如果响应直接包含data_addresses（简化格式）
        if "data_addresses" in response:
            result["success"] = response.get("success", True)
            result["message"] = response.get("message", "")
            result["data_addresses"] = response.get("data_addresses", [])
            result["needs_more_info"] = response.get("needs_more_info", False)
            result["question"] = response.get("question")
            return result
        
        # 4. 如果响应包含message字段（文本响应）
        if "message" in response:
            message_text = response.get("message", "")
            # 尝试解析JSON格式的文本
            try:
                import json
                parsed = json.loads(message_text)
                if isinstance(parsed, dict):
                    result.update(parsed)
                    return result
            except:
                pass
            # 如果不是JSON，将文本作为message
            result["message"] = message_text
            result["success"] = True
            return result
        
        # 5. 如果响应包含content字段
        if "content" in response:
            content = response.get("content", "")
            try:
                import json
                parsed = json.loads(content) if isinstance(content, str) else content
                if isinstance(parsed, dict):
                    result.update(parsed)
                    return result
            except:
                result["message"] = str(content)
                result["success"] = True
                return result
        
        # 6. 提取medical_data和has_direct_data（第二轮请求可能直接返回医疗数据）
        if "medical_data" in response:
            result["medical_data"] = response.get("medical_data")
            result["has_direct_data"] = response.get("has_direct_data", True)
            self.logger.info(f"[EntryAgentAdapter] 检测到直接医疗数据（medical_data字段）")
            print(f"[EntryAgentAdapter] [成功] 检测到直接医疗数据，将跳过数据存储服务请求")
        
        # 7. 默认处理：假设整个响应就是结果
        result.update(response)
        result["success"] = result.get("success", True)  # 默认成功
        
        return result
    
    async def invoke(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用EntryAgent，通过prompt进行数据交互请求
        
        参数:
            request_data (Dict[str, Any]): 请求数据
        
        返回:
            Dict[str, Any]: 响应数据
        """
        if not A2A_SDK_AVAILABLE:
            raise ImportError("标准A2A SDK未安装")
        
        try:
            import httpx
            from uuid import uuid4
            from a2a.types import Message, TextPart
            from a2a.client import A2AClient, A2ACardResolver
            from a2a.types import SendMessageRequest, MessageSendParams
        except ImportError as e:
            raise ImportError(f"标准A2A SDK导入失败: {e}")
        
        # 构建prompt
        prompt = self._build_prompt_from_request(request_data)
        
        # 从base_url中提取token并清理URL（按照entry_agent2.py的实现方式）
        # 优先使用self.token（运行时更新的token），否则从URL提取
        if self.token and self.token != "unknown":
            token = self.token
            self.logger.info(f"[EntryAgentAdapter] 使用运行时更新的token: {token[:20]}...")
        else:
            token = self._extract_token_from_url(self.base_url)
            # 注意：_extract_token_from_url可能返回"unknown"
            if token == "unknown":
                self.logger.warning("[EntryAgentAdapter] 从URL中未找到token参数，使用默认值'unknown'")
        
        # 移除token参数，获取干净的base_url（按照entry_agent2.py）
        clean_base_url = self._remove_token_from_url(self.base_url)
        
        # 如果token是'unknown'，记录警告（但按照参考代码仍然会传递到metadata）
        if token == "unknown":
            self.logger.warning("[EntryAgentAdapter] [警告] Token为'unknown'，但按照参考代码仍然传递到metadata")
            print("\n[警告] [EntryAgentAdapter] Token为'unknown'，数据代理应用可能无法认证，但会按照参考代码传递到metadata")
        
        # ========== 打印EntryAgent调用信息 ==========
        print("\n" + "=" * 80)
        print("[EntryAgentAdapter] 开始调用EntryAgent")
        print("=" * 80)
        print(f"Base URL (清理后): {clean_base_url}")
        print(f"Token: {token[:30]}...")
        if token == "unknown":
            print("[警告] Token为'unknown'，请确保运行时已更新token")
        print(f"\n构建的Prompt:")
        print("-" * 80)
        print(prompt)
        print("-" * 80)
        print()
        
        self.logger.info(f"[EntryAgentAdapter] 调用EntryAgent，base_url: {clean_base_url}, token: {token[:20]}...")
        self.logger.info(f"[EntryAgentAdapter] Prompt: {prompt[:200]}...")
        
        try:
            # 使用配置的超时时间，默认60秒（JSON-RPC服务可能需要更长时间）
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as httpx_client:
                # 获取agent card
                resolver = A2ACardResolver(httpx_client=httpx_client, base_url=clean_base_url)
                
                try:
                    self.logger.info(f"尝试获取agent card，url为{clean_base_url}")
                    print(f"[EntryAgent] 正在获取Agent Card: {clean_base_url}/.well-known/agent-card.json")
                    agent_card = await resolver.get_agent_card()
                    
                    self.logger.info(f"已成功获取agent card")
                    # ========== 打印Agent Card信息 ==========
                    print("\n[EntryAgent] Agent Card获取成功:")
                    print("-" * 80)
                    try:
                        agent_card_json = agent_card.model_dump_json(indent=2, exclude_none=True)
                        print(agent_card_json)
                    except Exception:
                        print(str(agent_card))
                    print("-" * 80)
                    print()
                    self.logger.debug(f"Agent card: {agent_card.model_dump_json(indent=2, exclude_none=True)}")
                    
                    # 重要：覆盖agent card中的URL，使用配置的base_url
                    # 因为agent card中的URL可能是localhost或其他地址，需要使用实际配置的地址
                    try:
                        if hasattr(agent_card, 'url'):
                            original_url = agent_card.url
                            agent_card.url = clean_base_url
                            self.logger.info(f"覆盖Agent Card中的URL: {original_url} -> {clean_base_url}")
                        elif hasattr(agent_card, 'model_dump'):
                            # 如果是Pydantic模型，需要更新
                            from a2a.types import AgentCard
                            card_dict = agent_card.model_dump()
                            original_url = card_dict.get('url', 'N/A')
                            card_dict['url'] = clean_base_url
                            agent_card = AgentCard(**card_dict)
                            self.logger.info(f"覆盖Agent Card中的URL: {original_url} -> {clean_base_url}")
                    except Exception as url_update_error:
                        self.logger.warning(f"无法更新Agent Card URL: {url_update_error}，将使用原始URL")
                    
                except Exception as e:
                    self.logger.error(f"获取agent card失败，错误信息为：{e}")
                    # 不直接抛出异常，让调用者决定是否降级
                    # 记录详细错误信息以便调试
                    import traceback
                    self.logger.error(f"获取agent card失败的详细错误:\n{traceback.format_exc()}")
                    raise RuntimeError(f"获取agent card失败，无法继续运行: {e}") from e
                
                # 初始化client
                try:
                    self.logger.info(f"尝试初始化A2A client")
                    client = A2AClient(
                        httpx_client=httpx_client, agent_card=agent_card
                    )
                    self.logger.info(f"已成功初始化A2A client")
                except Exception as e:
                    self.logger.error(f"初始化client失败，错误信息为：{e}")
                    raise RuntimeError(f"初始化client失败，无法继续运行: {e}") from e
                
                # A2A协议规定的标准Message数据格式
                message_id = uuid4().hex
                # 按照entry_agent2.py的实现方式：始终传递token到metadata，即使为"unknown"
                # 这确保metadata格式始终一致，避免数据代理应用访问metadata["token"]时出错
                metadata_value = {"token": token}
                
                if token == "unknown":
                    self.logger.warning(f"[EntryAgentAdapter] 传递token='unknown'到metadata（按照参考代码）")
                    print(f"[EntryAgentAdapter] [警告] 传递token='unknown'到metadata，数据代理应用可能无法认证")
                else:
                    self.logger.info(f"[EntryAgentAdapter] 传递token到metadata: {token[:20]}...")
                
                send_message_payload: Message = Message(
                    role="user",
                    parts=[TextPart(text=prompt)],
                    message_id=message_id,
                    metadata=metadata_value  # 始终包含token字段，即使为"unknown"
                )
                
                # 请求：使用A2A SDK封装好的SendMessageRequest
                request_id = str(uuid4())
                request = SendMessageRequest(
                    id=request_id, params=MessageSendParams(message=send_message_payload)
                )
                
                # ========== 打印发送给第三方服务的请求 ==========
                print("\n" + "=" * 80)
                print("[EntryAgent] 发送给第三方数据代理应用的请求")
                print("=" * 80)
                print(f"请求ID: {request_id}")
                print(f"消息ID: {message_id}")
                print(f"目标URL: {clean_base_url}")
                print(f"Token: {token[:30]}...")
                print(f"\n构建的Prompt:")
                print("-" * 80)
                print(prompt)
                print("-" * 80)
                print(f"\nA2A Message结构:")
                print(f"  role: {send_message_payload.role}")
                print(f"  message_id: {send_message_payload.message_id}")
                print(f"  metadata: {send_message_payload.metadata}")
                if send_message_payload.metadata:
                    print(f"    - token: {send_message_payload.metadata.get('token', 'N/A')[:30]}..." if send_message_payload.metadata.get('token') else "    - token: N/A")
                print(f"  parts数量: {len(send_message_payload.parts)}")
                if send_message_payload.parts:
                    print(f"  第一个part类型: {type(send_message_payload.parts[0]).__name__}")
                    if hasattr(send_message_payload.parts[0], 'text'):
                        print(f"  文本内容长度: {len(send_message_payload.parts[0].text)} 字符")
                print(f"\nSendMessageRequest结构:")
                print(f"  id: {request.id}")
                print(f"  params.message.role: {request.params.message.role}")
                print("=" * 80)
                print()
                
                # 发送请求
                print(f"[EntryAgent] 正在发送请求到第三方服务: {clean_base_url}")
                response = await client.send_message(request)
                print(f"[EntryAgent] 已收到第三方服务的响应")
                
                # 处理响应
                if hasattr(response, 'model_dump'):
                    response_dict = response.model_dump()
                elif hasattr(response, 'dict'):
                    response_dict = response.dict()
                else:
                    response_dict = response if isinstance(response, dict) else {"response": response}
                
                # ========== 打印第三方服务返回的原始响应 ==========
                print("\n" + "=" * 80)
                print("[EntryAgent] 第三方数据代理应用返回的原始响应")
                print("=" * 80)
                try:
                    import json
                    print(json.dumps(response_dict, ensure_ascii=False, indent=2))
                except Exception:
                    print(str(response_dict))
                print("=" * 80)
                print()
                
                self.logger.debug(f"[EntryAgentAdapter] 原始响应: {response_dict}")
                
                # 解析响应
                parsed_response = self._parse_response_from_message(response_dict)
                
                # ========== 打印解析后的响应 ==========
                print("\n" + "=" * 80)
                print("[EntryAgent] 解析后的响应数据")
                print("=" * 80)
                try:
                    import json
                    print(json.dumps(parsed_response, ensure_ascii=False, indent=2))
                except Exception:
                    print(str(parsed_response))
                print("=" * 80)
                print()
                
                self.logger.info(f"[EntryAgentAdapter] 调用完成，成功: {parsed_response.get('success')}")
                
                return parsed_response
                
        except Exception as e:
            self.logger.error(f"[EntryAgentAdapter] 调用失败: {str(e)}", exc_info=True)
            raise

