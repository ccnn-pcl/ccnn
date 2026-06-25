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
内科专科医生智能体（重构版）
============================

支持地域参数（beijing/shanghai），根据地域选择不同的模型配置。

主要功能：
1. 内科症状分析
2. 病史关联分析
3. 内科诊断建议
4. 治疗方案推荐
5. 数据需求评估

作者: QSIR
版本: 2.0 - 重构版（支持地域）
"""

import json
from typing import Any, Dict, List, Optional

from src.shared.agents.base_agent import BaseAgent
from src.shared.agents.utils.shared_context import SharedContext
from src.shared.agents.utils.user_info_helper import auto_complete_user_info


class InternalMedicineAgent(BaseAgent):
    """
    内科专科医生智能体（重构版）

    支持地域参数，根据地域选择不同的模型配置：
    - beijing: 使用huatuogpt-2模型
    - shanghai: 使用huatuogpt模型

    专门处理内科相关的医疗咨询，包括：
    - 内科症状分析
    - 病史关联分析
    - 内科诊断建议
    - 治疗方案推荐
    - 数据需求评估（用于多轮协调）
    """

    def __init__(self, model_config: Dict[str, Any], location: str = "beijing"):
        """
        初始化内科专科医生智能体

        参数：
            model_config (Dict[str, Any]): 模型配置
            location (str): 地域信息（beijing/shanghai）
        """
        super().__init__(model_config)
        self.location = location
        self.agent_id = f"internal_medicine_{location}"
        self.name = f"内科专家智能体_{location}"
        self.specialization = "内科"

        self.logger.info(f"[{self.name}] 初始化完成，地域: {location}")

    async def execute(
        self,
        user_input: str,
        user_id: str,
        data_addresses: Optional[List[Dict]] = None,
        shared_context: Optional[SharedContext] = None,
        user_info: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        执行内科诊断（重构版）

        参数：
            user_input (str): 用户输入的症状描述
            user_id (str): 用户ID
            data_addresses (List[Dict], optional): 数据地址列表（包含地域信息）
            shared_context (SharedContext, optional): 共享上下文
            user_info (Dict, optional): 用户信息

        返回：
            Dict[str, Any]: 诊断结果，包含数据需求信息
        """
        try:
            self.logger.info(f"[{self.name}] 开始执行内科诊断")
            self.logger.info(f"[{self.name}] 地域: {self.location}")

            # 验证输入
            if not self.validate_input(user_input):
                self.logger.warning(f"[{self.name}] 输入验证失败")
                return {
                    "agent": self.agent_id,
                    "location": self.location,
                    "specialization": self.specialization,
                    "error": "输入无效，请提供有效的症状描述。",
                    "confidence": 0.0,
                    "needs_more_data": False,
                }

            # 1. 读取医疗数据（优先使用直接数据，否则从数据地址读取）
            # 检查共享上下文中是否有直接医疗数据（数据代理直接返回的）
            direct_medical_data = None
            is_direct_data = False  # ✅ 标记数据是否来自数据代理应用直接返回
            if shared_context and shared_context.direct_medical_data:
                direct_medical_data = shared_context.direct_medical_data
                is_direct_data = True  # ✅ 标记为直接数据
                self.logger.info(
                    f"[{self.name}] 使用共享上下文中的直接医疗数据（跳过数据存储服务请求）"
                )

            # 保存shared_context到实例变量，供_read_data_from_addresses使用
            self._shared_context = shared_context

            medical_data = await self._read_data_from_addresses(
                data_addresses, user_id, direct_medical_data=direct_medical_data
            )

            # ✅ 在medical_data中标记数据来源类型
            if is_direct_data:
                medical_data["_is_direct_data"] = True  # 标记为数据代理应用直接返回
                medical_data["_data_source_type"] = "数据代理应用直接返回"
            else:
                medical_data["_is_direct_data"] = False  # 标记为通过MCP获取
                medical_data["_data_source_type"] = "MCP数据存储服务"

            # 2. 获取对话历史
            context = self.get_context_from_memory(user_id)

            # 3. 利用历史诊断结果优化（如果有共享上下文）
            if shared_context and shared_context.diagnosis_results_history:
                previous_results = [
                    r
                    for r in shared_context.diagnosis_results_history
                    if r.get("location") == self.location
                ]
                if previous_results:
                    medical_data["previous_diagnoses"] = [
                        r.get("diagnosis") for r in previous_results
                    ]
                    self.logger.info(
                        f"[{self.name}] 利用历史诊断结果优化，历史结果数: {len(previous_results)}"
                    )

            # 4. 自动补全用户信息（从医疗档案）
            if user_info:
                user_info = await auto_complete_user_info(user_id, user_info)

            # 5. 进行病史分析（内化功能）
            history_analysis = await self._analyze_history(
                user_input, context, user_info, medical_data
            )

            # 6. 构建诊断提示
            diagnosis_prompt = self._build_diagnosis_prompt(
                user_input, context, history_analysis, medical_data, shared_context
            )

            # 7. 调用LLM进行诊断
            print(f"\n[{self.name}] 开始调用LLM进行内科诊断...")

            # 打印调试信息：发送给LLM的诊断提示（包含医疗数据）
            print("\n" + "=" * 80)
            print(f"[调试] 发送给LLM的诊断提示（{self.name}, {self.location}）")
            print("=" * 80)
            print(f"  提示长度: {len(diagnosis_prompt)} 字符")
            print(
                f"  是否包含医疗数据: {'是' if '医疗数据' in diagnosis_prompt or str(medical_data) in diagnosis_prompt else '否'}"
            )
            # 检查医疗数据的关键字段是否在提示中
            medical_data_keys = ["medical_history", "medications", "lab_results"]
            found_keys = [
                key
                for key in medical_data_keys
                if key in str(medical_data) and key in diagnosis_prompt
            ]
            print(f"  医疗数据字段检查: {found_keys}")
            try:
                # 使用Markdown格式打印诊断提示
                try:
                    from src.shared.utils.markdown_formatter import print_markdown

                    print_markdown(
                        content=diagnosis_prompt,
                        content_type="markdown",
                        max_length=5000,
                        title=f"📝 诊断提示 (Prompt) - {self.name}",
                        separator="=" * 80,
                    )
                except ImportError:
                    # 如果导入失败，使用原有格式
                    if len(diagnosis_prompt) > 2000:
                        print("\n诊断提示（前2000字符）:")
                        print(diagnosis_prompt[:2000])
                        print(
                            f"\n... (提示过长，已截断，总长度: {len(diagnosis_prompt)} 字符)"
                        )
                    else:
                        print("\n诊断提示:")
                        print(diagnosis_prompt)
                    print("=" * 80 + "\n")
            except Exception as e:
                print(f"[错误] 打印诊断提示失败: {e}")
                print("=" * 80 + "\n")

            try:
                diagnosis = await self.caller(diagnosis_prompt, self.model_config)
                print(
                    f"[{self.name}] LLM诊断调用完成，结果长度: {len(str(diagnosis))} 字符"
                )
            except Exception as e:
                print(f"[{self.name}] LLM诊断调用失败: {type(e).__name__}: {str(e)}")
                raise
            # ==============hzl================
            from pathlib import Path

            api_dir = Path(__file__).resolve().parents[3] / "api"
            api_dir.mkdir(exist_ok=True)
            log_file = api_dir / "diagnosis.log.md"
            with log_file.open("a", encoding="utf-8") as f:
                f.write(str(diagnosis))
            # ==============hzl================

            diagnosis = self._filter_thinking_content(diagnosis)

            # 8. 解析诊断结果（提取置信度等）
            diagnosis_result = self._parse_diagnosis_result(diagnosis)
            print(
                f"[{self.name}] 诊断结果解析完成，置信度: {diagnosis_result.get('confidence', 'N/A')}"
            )

            # 9. 评估数据需求
            data_needs = await self._assess_data_needs(diagnosis_result, medical_data)
            print(
                f"[{self.name}] 数据需求评估完成，需要更多数据: {len(data_needs) > 0}"
            )

            # 10. 记录对话轮次
            self.add_turn_to_memory(user_id, user_input, self.name, diagnosis)

            # 11. 构建返回结果
            # ✅ 构建data_sources，区分数据来源类型
            is_direct_data = medical_data.get("_is_direct_data", False)
            data_source_type = medical_data.get("_data_source_type", "未知")
            data_sources_list = medical_data.get("sources", [])

            if is_direct_data:
                # ✅ 第二轮诊断：数据来自数据代理应用直接返回
                # 检查是否是健康监测数据
                available_data_types = medical_data.get("available_data_types", [])
                is_health_monitoring = any(
                    "健康监测" in str(dt) for dt in available_data_types
                ) or medical_data.get("health_monitoring")

                if is_health_monitoring:
                    # ✅ 健康监测数据：使用"健康监测数据"作为数据来源
                    data_sources_list = ["健康监测数据"]
                elif not data_sources_list:
                    # 如果没有sources，设置为数据代理应用
                    data_sources_list = ["数据代理应用直接返回"]
                else:
                    # 如果有sources，添加标识说明数据来源
                    # 格式：原始来源（数据代理应用直接返回）
                    data_sources_list = [
                        f"{source}（数据代理应用直接返回）"
                        for source in data_sources_list
                    ]
            else:
                # ✅ 第一轮诊断：数据来自MCP数据存储服务
                # 从data_addresses中提取MCP服务器地址
                if data_addresses:
                    for addr in data_addresses:
                        server_url = addr.get("address", "") or addr.get(
                            "data_service_address", ""
                        )
                        hospital = addr.get("hospital", "")
                        if server_url and hospital:
                            # 格式：医院名称 (MCP: 服务器地址)
                            source_with_url = f"{hospital} (MCP: {server_url})"
                            if source_with_url not in data_sources_list:
                                data_sources_list.append(source_with_url)
                        elif hospital and hospital not in data_sources_list:
                            data_sources_list.append(hospital)

            # 构建data_content，包含医疗数据摘要
            data_content = {}
            if medical_data:
                # ✅ 对于健康监测数据，确保source字段使用"健康监测数据"而不是医院名称
                available_data_types = medical_data.get("available_data_types", [])
                is_health_monitoring = any(
                    "健康监测" in str(dt) for dt in available_data_types
                ) or medical_data.get("health_monitoring")

                # 确定source字段的值
                if is_direct_data and is_health_monitoring:
                    # ✅ 健康监测数据：使用"健康监测数据"作为source
                    source_text = "健康监测数据"
                else:
                    # 其他情况：使用data_sources_list
                    source_text = (
                        ", ".join(data_sources_list) if data_sources_list else "未知"
                    )

                # 提取医疗数据的关键字段
                data_content = {
                    "data_type": ", ".join(medical_data.get("available_data_types", []))
                    if medical_data.get("available_data_types")
                    else "未知",
                    "source": source_text,  # ✅ 使用处理后的source_text
                    "has_medical_history": bool(medical_data.get("medical_history")),
                    "has_medications": bool(medical_data.get("medications")),
                    "has_lab_results": bool(medical_data.get("lab_results")),
                    "has_imaging_data": bool(medical_data.get("imaging_data")),
                    "has_surgical_records": bool(medical_data.get("surgical_records")),
                    "has_health_monitoring": bool(
                        medical_data.get("health_monitoring")
                    ),
                }

                # ✅ 区分数据来源类型
                if is_direct_data:
                    # 第二轮诊断：数据来自数据代理应用直接返回
                    data_content["data_source_type"] = "数据代理应用直接返回"
                    data_content["has_direct_data"] = True
                    # 不包含MCP服务器地址
                else:
                    # 第一轮诊断：数据来自MCP数据存储服务
                    data_content["data_source_type"] = "MCP数据存储服务"
                    data_content["has_direct_data"] = False
                    # 从data_addresses中提取MCP服务器地址
                    if data_addresses:
                        mcp_servers = []
                        for addr in data_addresses:
                            server_url = addr.get("address", "") or addr.get(
                                "data_service_address", ""
                            )
                            if server_url:
                                mcp_servers.append(server_url)
                        if mcp_servers:
                            data_content["mcp_server"] = ", ".join(set(mcp_servers))

                # 添加医疗数据摘要（不包含完整数据，只包含摘要信息）
                summary = {}
                if medical_data.get("medical_history"):
                    if isinstance(medical_data.get("medical_history"), list):
                        summary["medical_history_count"] = len(
                            medical_data.get("medical_history")
                        )
                    elif isinstance(medical_data.get("medical_history"), dict):
                        summary["medical_history_fields"] = list(
                            medical_data.get("medical_history").keys()
                        )[:5]  # 只取前5个字段
                    else:
                        summary["medical_history"] = "有数据"

                if medical_data.get("medications"):
                    if isinstance(medical_data.get("medications"), list):
                        summary["medications_count"] = len(
                            medical_data.get("medications")
                        )
                    else:
                        summary["medications"] = "有数据"

                if medical_data.get("lab_results"):
                    if isinstance(medical_data.get("lab_results"), list):
                        summary["lab_results_count"] = len(
                            medical_data.get("lab_results")
                        )
                    else:
                        summary["lab_results"] = "有数据"

                if medical_data.get("health_monitoring"):
                    if isinstance(medical_data.get("health_monitoring"), dict):
                        summary["health_monitoring_fields"] = list(
                            medical_data.get("health_monitoring").keys()
                        )[:5]  # 只取前5个字段
                    else:
                        summary["health_monitoring"] = "有数据"

                if summary:
                    data_content["summary"] = summary

            result = {
                "agent": self.agent_id,
                "location": self.location,
                "specialization": self.specialization,
                "diagnosis": diagnosis_result,
                "data_sources": data_sources_list,
                "available_data_types": medical_data.get("available_data_types", []),
                "data_content": data_content,  # ✅ 添加data_content字段，包含MCP数据摘要
                "data_usage_summary": diagnosis_result.get("data_usage_summary"),
                "confidence": diagnosis_result.get("confidence", 0.0),
                "needs_more_data": len(data_needs) > 0,
                "data_requirements": data_needs,
                "reasoning": diagnosis_result.get("reasoning", ""),
            }

            # 打印诊断完成信息
            print(f"\n[{self.name}] ========================================")
            print(f"[{self.name}] 诊断完成")
            print(f"[{self.name}] ========================================")
            print(f"  - 智能体ID: {result['agent']}")
            print(f"  - 地域: {result['location']}")
            print(f"  - 专科: {result['specialization']}")
            print(f"  - 置信度: {result['confidence']}")
            print(f"  - 数据来源: {result.get('data_sources', [])}")
            print(f"  - 可用数据类型: {result.get('available_data_types', [])}")
            if result.get("data_content"):
                data_content = result.get("data_content", {})
                print("  - 数据内容摘要:")
                print(f"     - 数据类型: {data_content.get('data_type', 'N/A')}")
                print(f"     - 数据来源: {data_content.get('source', 'N/A')}")
                if data_content.get("mcp_server"):
                    print(f"     - MCP服务器: {data_content.get('mcp_server', 'N/A')}")
                summary = data_content.get("summary", {})
                if summary:
                    print(f"     - 数据摘要: {summary}")
            if result.get("data_usage_summary"):
                print(f"  - 数据使用说明: {result['data_usage_summary']}")
            else:
                print("  - 数据使用说明: [未提供]")
            print(f"  - 需要更多数据: {result['needs_more_data']}")
            print(f"  - 数据需求数量: {len(data_needs)}")
            if data_needs:
                print("  - 数据需求列表:")
                for i, need in enumerate(data_needs, 1):
                    print(f"    {i}. {need}")
            if diagnosis_result.get("diagnosis"):
                diagnosis_text = str(diagnosis_result.get("diagnosis", ""))
                print("  - 完整诊断结果:")
                print(f"    {diagnosis_text}")
            if diagnosis_result.get("reasoning"):
                reasoning_text = str(diagnosis_result.get("reasoning", ""))
                print("  - 推理过程:")
                print(f"    {reasoning_text}")
            print(f"[{self.name}] ========================================\n")

            self.logger.info(
                f"[{self.name}] 诊断完成，置信度: {result['confidence']}, 需要更多数据: {result['needs_more_data']}"
            )
            return result

        except Exception as e:
            self.logger.error(f"[{self.name}] 执行错误：{str(e)}", exc_info=True)
            return {
                "agent": self.agent_id,
                "location": self.location,
                "specialization": self.specialization,
                "error": f"内科诊断错误：{str(e)}",
                "confidence": 0.0,
                "needs_more_data": False,
            }

    async def _read_data_from_addresses(
        self,
        data_addresses: Optional[List[Dict]],
        user_id: str,
        direct_medical_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        从数据地址读取医疗数据

        参数：
            data_addresses (List[Dict]): 数据地址列表
            user_id (str): 用户ID
            direct_medical_data (Dict[str, Any], optional): 直接医疗数据（数据代理直接返回的）

        返回：
            Dict[str, Any]: 医疗数据
        """
        # 如果提供了直接数据，优先使用（跳过数据存储服务请求）
        if direct_medical_data:
            self.logger.info(f"[{self.name}] 使用直接医疗数据，跳过数据存储服务请求")
            # 确保数据格式正确
            if "sources" not in direct_medical_data:
                direct_medical_data["sources"] = []
            if "available_data_types" not in direct_medical_data:
                direct_medical_data["available_data_types"] = []
                # 从数据中推断数据类型
                if direct_medical_data.get("health_monitoring"):
                    direct_medical_data["available_data_types"].append("健康监测数据")
                if direct_medical_data.get("medical_history"):
                    direct_medical_data["available_data_types"].append("病史数据")
                if direct_medical_data.get("medications"):
                    direct_medical_data["available_data_types"].append("用药记录")
                if direct_medical_data.get("lab_results"):
                    direct_medical_data["available_data_types"].append("化验报告")

            # 打印调试信息：直接医疗数据（第二轮数据代理应用直接返回的数据）
            # 确定轮次信息（从shared_context获取，如果不可用则根据数据来源推断）
            round_info = "第二轮诊断"
            if hasattr(self, "_shared_context") and self._shared_context:
                round_num = self._shared_context.round_number
                if round_num >= 2:
                    round_info = f"第二轮诊断（轮次: {round_num}）"
                elif round_num == 1:
                    round_info = f"第一轮诊断（轮次: {round_num}）"

            print("\n" + "=" * 80)
            print(
                f"[调试] 【{round_info}】专科医生智能体获取的直接医疗数据（{self.name}, {self.location}）"
            )
            print("=" * 80)
            print(f"  数据来源: {direct_medical_data.get('sources', [])}")
            print(
                f"  可用数据类型: {direct_medical_data.get('available_data_types', [])}"
            )
            print("  数据获取方式: 数据代理应用直接返回（跳过数据存储服务请求）")
            try:
                import json

                # 打印完整数据（限制长度以避免输出过长）
                data_str = json.dumps(direct_medical_data, ensure_ascii=False, indent=2)
                if len(data_str) > 5000:
                    print("\n医疗数据（前5000字符）:")
                    print(data_str[:5000])
                    print(f"\n... (数据过长，已截断，总长度: {len(data_str)} 字符)")
                else:
                    print("\n医疗数据:")
                    print(data_str)
            except Exception as e:
                print(f"[错误] 打印医疗数据失败: {e}")
                print(f"数据类型: {type(direct_medical_data)}")
                print(
                    f"数据键: {list(direct_medical_data.keys()) if isinstance(direct_medical_data, dict) else 'N/A'}"
                )
            print("=" * 80 + "\n")

            # ✅ 标记为直接医疗数据
            direct_medical_data["_is_direct_data"] = True
            direct_medical_data["_data_source_type"] = "数据代理应用直接返回"

            return direct_medical_data

        if not data_addresses:
            self.logger.info(f"[{self.name}] 没有数据地址，返回空数据")
            return {
                "medical_history": None,
                "medications": None,
                "lab_results": None,
                "sources": [],
            }

        # 过滤出当前地域的数据地址
        location_addresses = [
            addr for addr in data_addresses if addr.get("location") == self.location
        ]

        if not location_addresses:
            self.logger.info(
                f"[{self.name}] 没有匹配当前地域({self.location})的数据地址"
            )
            return {
                "medical_history": None,
                "medications": None,
                "lab_results": None,
                "sources": [],
            }

        self.logger.info(f"[{self.name}] 找到 {len(location_addresses)} 个数据地址")

        # ============================================================
        # 【✅ 真实第三方应用调用】数据库存储服务数据读取
        # ============================================================
        # 当前实现：优先使用真实的 DatabaseStorageClient
        # 如果导入失败，会降级到模拟数据（兼容模式）
        # ============================================================
        try:
            from src.shared.agents.utils.database_storage_client import (
                DatabaseStorageClient,
                DatabaseStorageConfig,
            )

            # 【✅ 生产环境配置】从环境变量读取真实服务URL和密钥
            config = DatabaseStorageConfig(
                retry_count=2,
                enable_logging=True,
            )
            # 调用真实的数据库存储服务API
            async with DatabaseStorageClient(config) as client:
                # 读取医疗数据（只读取当前地域的数据）
                medical_data = await client.retrieve_medical_data(
                    location_addresses, user_id
                )

                # 添加数据来源信息（包含医院名称和MCP服务器地址）
                sources = []
                for addr in location_addresses:
                    hospital = addr.get("hospital", f"{self.location}_hospital")
                    server_url = addr.get("address", "") or addr.get(
                        "data_service_address", ""
                    )
                    if server_url:
                        # 格式：医院名称 (MCP: 服务器地址)
                        source = f"{hospital} (MCP: {server_url})"
                    else:
                        source = hospital
                    if source not in sources:
                        sources.append(source)
                medical_data["sources"] = sources

                # 确保available_data_types存在
                if "available_data_types" not in medical_data:
                    medical_data["available_data_types"] = []
                    for addr in location_addresses:
                        data_type = addr.get("data_type", "未知")
                        if (
                            data_type
                            and data_type not in medical_data["available_data_types"]
                        ):
                            medical_data["available_data_types"].append(data_type)

                # 如果medical_data中没有数据类型，尝试从数据中推断
                if not medical_data["available_data_types"]:
                    if medical_data.get("medical_history"):
                        medical_data["available_data_types"].append("病史数据")
                    if medical_data.get("medications"):
                        medical_data["available_data_types"].append("用药记录")
                    if medical_data.get("lab_results"):
                        medical_data["available_data_types"].append("化验报告")
                    if medical_data.get("health_monitoring"):
                        medical_data["available_data_types"].append("健康监测数据")

                self.logger.info(
                    f"[{self.name}] 成功读取医疗数据，数据类型: {medical_data.get('available_data_types', [])}"
                )

                # 打印调试信息：通过MCP获取的完整医疗数据
                # 确定轮次信息（从shared_context获取，如果不可用则根据数据来源推断）
                round_info = "第一轮诊断"
                if hasattr(self, "_shared_context") and self._shared_context:
                    round_num = self._shared_context.round_number
                    if round_num >= 2:
                        round_info = f"第二轮诊断（轮次: {round_num}）"
                    elif round_num == 1:
                        round_info = f"第一轮诊断（轮次: {round_num}）"

                print("\n" + "=" * 80)
                print(
                    f"[调试] 【{round_info}】专科医生智能体获取的完整医疗数据（{self.name}, {self.location}）"
                )
                print("=" * 80)
                print(f"  数据来源: {medical_data.get('sources', [])}")
                print(f"  可用数据类型: {medical_data.get('available_data_types', [])}")
                print("  数据获取方式: 通过MCP协议从数据存储服务获取")
                try:
                    import json

                    # 打印完整数据（限制长度以避免输出过长）
                    data_str = json.dumps(medical_data, ensure_ascii=False, indent=2)
                    if len(data_str) > 5000:
                        print("\n医疗数据（前5000字符）:")
                        print(data_str[:5000])
                        print(f"\n... (数据过长，已截断，总长度: {len(data_str)} 字符)")
                    else:
                        print("\n医疗数据:")
                        print(data_str)
                except Exception as e:
                    print(f"[错误] 打印医疗数据失败: {e}")
                    print(f"数据类型: {type(medical_data)}")
                    print(
                        f"数据键: {list(medical_data.keys()) if isinstance(medical_data, dict) else 'N/A'}"
                    )
                print("=" * 80 + "\n")

                return medical_data

        except ImportError:
            # ============================================================
            # 【已禁用】模拟测试降级代码 - 真实测试时已注释
            # ============================================================
            # 在真实第三方应用测试时，如果导入失败应该抛出异常，
            # 而不是降级到模拟数据，以确保测试的真实性
            # ============================================================
            self.logger.error(
                f"[{self.name}] DatabaseStorageClient未找到，无法继续执行"
            )
            raise ImportError(
                f"[{self.name}] DatabaseStorageClient未找到，请确保已正确安装和配置"
            )

            # 【已注释】以下模拟数据代码已禁用（真实测试时）
            # self.logger.warning(f"[{self.name}] DatabaseStorageClient未找到，使用模拟数据（兼容模式）")
            # medical_data = {
            #     "medical_history": {
            #         "chronic_diseases": ["高血压", "心脏病"],
            #         "past_illnesses": []
            #     },
            #     "medications": [
            #         {"name": "降压药", "dosage": "10mg", "frequency": "每日一次"}
            #     ],
            #     "lab_results": [],
            #     "sources": [addr.get("hospital") for addr in location_addresses],
            #     "available_data_types": ["病史数据", "用药记录"]
            # }
            return medical_data

        except Exception as e:
            self.logger.error(f"[{self.name}] 读取医疗数据失败: {str(e)}")
            # 返回空数据结构
            return {
                "medical_history": None,
                "medications": None,
                "lab_results": None,
                "sources": [addr.get("hospital") for addr in location_addresses],
                "available_data_types": [],
            }

    def _build_diagnosis_prompt(
        self,
        user_input: str,
        context: str,
        history_analysis: Any,
        medical_data: Dict[str, Any],
        shared_context: Optional[SharedContext] = None,
    ) -> str:
        """
        构建内科诊断提示（重构版）

        参数：
            user_input (str): 用户输入
            context (str): 对话上下文
            history_analysis (Any): 病史分析结果（内化功能）
            medical_data (Dict[str, Any]): 医疗数据
            shared_context (SharedContext, optional): 共享上下文

        返回：
            str: 诊断提示
        """
        prompt = f"""作为一位经验丰富的内科医生，请根据以下信息进行诊断：

患者症状描述：{user_input}

对话历史：
{context}

医疗数据：
{json.dumps(medical_data, ensure_ascii=False, indent=2)}

"""

        if history_analysis:
            prompt += f"""
病史分析：
{history_analysis}

"""

        if shared_context and medical_data.get("previous_diagnoses"):
            prompt += f"""
历史诊断结果（用于参考）：
{medical_data.get("previous_diagnoses")}

"""

        # 生成数据摘要，便于LLM理解可用的数据类型
        data_summary = self._generate_data_summary(medical_data)

        # 检查是否包含健康监测数据
        has_health_monitoring = bool(medical_data.get("health_monitoring"))

        # 如果包含健康监测数据，明确提示
        health_monitoring_prompt = ""
        if has_health_monitoring:
            health_monitoring_prompt = """
【重要提示 - 健康监测数据】
本次诊断包含健康监测数据（血糖、血压、心率、体温、体重等实时监测数据），这些数据对于诊断非常重要。
请在诊断推理过程中：
1. 明确说明使用了哪些健康监测数据（例如：血糖值、血压值、心率等）
2. 分析这些健康监测数据与患者症状的关系
3. 在诊断结论中体现健康监测数据的影响
4. 在数据使用说明中明确列出使用的健康监测数据字段

示例：
- "根据健康监测数据中的血糖值（7.2 mmol/L，高于正常范围）和血压值（130/80 mmHg），结合患者多饮、多尿、体重下降的症状..."
- "健康监测数据显示血糖偏高（7.2 mmol/L），这与患者的症状高度一致，进一步支持糖尿病的诊断..."

"""

        prompt += f"""
请以温柔亲切、专业负责的医生身份进行诊断，让患者感到被理解和关怀：

{health_monitoring_prompt}
## [症状分析]
- 详细分析患者的症状表现
- 评估症状的严重程度和紧急程度

## [可能病因分析]
- 基于症状和病史分析可能的疾病原因
- 按可能性从高到低排序
- {"**如果包含健康监测数据，请结合健康监测数据进行分析**" if has_health_monitoring else ""}

## [诊断建议]
- 基于所有信息的综合诊断建议
- {"**如果包含健康监测数据，请在诊断建议中明确说明健康监测数据的作用**" if has_health_monitoring else ""}

## [检查建议]
- 建议进行的检查项目

## [治疗建议]
- 提供初步的治疗方案

## [数据使用说明]
- 请在诊断推理过程中，明确说明使用了哪些医疗数据字段
- 例如："根据病史数据中的慢性疾病信息（高血压、糖尿病）和化验报告中的血糖值（7.2 mmol/L），结合患者症状..."
- {"**必须明确说明使用了哪些健康监测数据字段（例如：血糖值、血压值、心率等）**" if has_health_monitoring else ""}

可用数据类型：
{data_summary}

请返回JSON格式的诊断结果，包含：
- diagnosis: 诊断结论
- reasoning: 诊断推理过程（请在推理中明确说明使用了哪些数据字段）
- data_usage_summary: 数据使用说明（简要说明使用了哪些医疗数据字段。{"如果包含健康监测数据，必须明确列出使用的健康监测数据字段（例如：血糖值、血压值、心率、体温等）" if has_health_monitoring else ""}例如："使用了病史数据中的慢性疾病信息（高血压、糖尿病）、用药记录中的药物名称和剂量（二甲双胍 500mg）、化验报告中的血糖值（7.2 mmol/L）"{"、健康监测数据中的血糖值（7.2 mmol/L）和血压值（130/80 mmHg）" if has_health_monitoring else ""}）
- confidence: 诊断置信度（0-1之间的浮点数，可选）

示例JSON格式（如果包含健康监测数据）：
{{
  "diagnosis": "根据症状和健康监测数据，初步诊断为II型糖尿病",
  "reasoning": "患者出现多饮、多尿、体重下降等症状。根据健康监测数据中的血糖值（7.2 mmol/L，高于正常范围）和血压值（130/80 mmHg），结合患者症状，初步诊断为II型糖尿病。",
  "data_usage_summary": "使用了健康监测数据中的血糖值（7.2 mmol/L）、血压值（130/80 mmHg）、心率（72 bpm）",
  "confidence": 0.8
}}

示例JSON格式（如果不包含健康监测数据）：
{{
  "diagnosis": "根据症状和病史，初步诊断为II型糖尿病",
  "reasoning": "患者出现多饮、多尿、体重下降等症状。根据病史数据中的慢性疾病信息（高血压、糖尿病）和化验报告中的血糖值（7.2 mmol/L），结合患者症状，初步诊断为II型糖尿病。",
  "data_usage_summary": "使用了病史数据中的慢性疾病信息（高血压、糖尿病）、用药记录中的药物名称和剂量（二甲双胍 500mg）、化验报告中的血糖值（7.2 mmol/L）",
  "confidence": 0.8
}}
"""

        return prompt

    def _generate_data_summary(self, medical_data: Dict[str, Any]) -> str:
        """
        生成医疗数据摘要

        参数:
            medical_data: 医疗数据字典

        返回:
            str: 数据摘要文本
        """
        summary_parts = []

        # 检查各个数据字段
        if medical_data.get("medical_history"):
            summary_parts.append("病史数据")
        if medical_data.get("medications"):
            med_count = (
                len(medical_data.get("medications", []))
                if isinstance(medical_data.get("medications"), list)
                else 1
            )
            summary_parts.append(f"用药记录（{med_count}条）")
        if medical_data.get("lab_results"):
            lab_count = (
                len(medical_data.get("lab_results", []))
                if isinstance(medical_data.get("lab_results"), list)
                else 1
            )
            summary_parts.append(f"化验报告（{lab_count}条）")
        if medical_data.get("health_monitoring"):
            summary_parts.append("健康监测数据")
        if medical_data.get("imaging_data"):
            img_count = (
                len(medical_data.get("imaging_data", []))
                if isinstance(medical_data.get("imaging_data"), list)
                else 1
            )
            summary_parts.append(f"影像数据（{img_count}条）")

        if summary_parts:
            return f"可用数据类型：{', '.join(summary_parts)}"
        else:
            return "可用数据类型：无"

    def _parse_diagnosis_result(self, diagnosis: str) -> Dict[str, Any]:
        """
        解析诊断结果，提取结构化信息

        参数：
            diagnosis (str): LLM返回的诊断结果

        返回：
            Dict[str, Any]: 结构化的诊断结果，包含：
                - diagnosis: 诊断结论
                - reasoning: 诊断推理过程
                - data_usage_summary: 数据使用说明（如果LLM提供了）
                - confidence: 置信度
        """
        result = {
            "diagnosis": diagnosis,
            "reasoning": diagnosis,
            "confidence": 0.7,
            "data_usage_summary": None,
        }

        # 尝试解析JSON格式
        try:
            import json
            import re

            # 尝试提取JSON部分（可能包含在markdown代码块中）
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", diagnosis, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个字符串（如果整个字符串是JSON）
                json_str = diagnosis.strip()
                # 如果以 { 开头且以 } 结尾，尝试解析
                if json_str.startswith("{") and json_str.endswith("}"):
                    pass  # 直接使用
                else:
                    # 尝试查找第一个 { 到最后一个 } 之间的内容
                    first_brace = json_str.find("{")
                    last_brace = json_str.rfind("}")
                    if first_brace >= 0 and last_brace > first_brace:
                        json_str = json_str[first_brace : last_brace + 1]
                    else:
                        raise ValueError("未找到JSON格式")

            parsed = json.loads(json_str)

            # 提取字段
            if isinstance(parsed, dict):
                result["diagnosis"] = parsed.get("diagnosis", diagnosis)
                result["reasoning"] = parsed.get("reasoning", diagnosis)
                result["data_usage_summary"] = parsed.get("data_usage_summary")
                # 如果提供了置信度，使用它；否则保持默认值
                if "confidence" in parsed:
                    result["confidence"] = float(parsed.get("confidence", 0.7))

        except (
            json.JSONDecodeError,
            AttributeError,
            KeyError,
            ValueError,
            TypeError,
        ) as e:
            # 如果解析失败，使用原有逻辑（向后兼容）
            self.logger.debug(f"[{self.name}] JSON解析失败，使用原始诊断结果: {str(e)}")
            pass

        return result

    async def _assess_data_needs(
        self, diagnosis_result: Dict[str, Any], medical_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        评估是否需要更多数据（用于多轮协调）

        参数：
            diagnosis_result (Dict[str, Any]): 诊断结果
            medical_data (Dict[str, Any]): 当前可用的医疗数据

        返回：
            List[Dict[str, Any]]: 数据需求列表
        """
        data_needs = []

        # 检查置信度
        confidence = diagnosis_result.get("confidence", 0.0)
        if confidence < 0.7:
            # 置信度较低，需要更多数据
            available_types = medical_data.get("available_data_types", [])

            # 定义内科诊断通常需要的数据类型
            required_types = ["病史数据", "用药记录", "化验报告"]
            missing_types = [t for t in required_types if t not in available_types]

            if missing_types:
                data_needs.append(
                    {
                        "location": self.location,
                        "data_types": missing_types,
                        "reason": f"诊断置信度较低({confidence:.2f})，需要以下数据以提高准确性: {', '.join(missing_types)}",
                        "priority": "high",
                    }
                )

        # 检查数据质量
        if not medical_data.get("medical_history") and not medical_data.get(
            "medications"
        ):
            data_needs.append(
                {
                    "location": self.location,
                    "data_types": ["病史数据", "用药记录"],
                    "reason": "缺少关键的病史和用药记录",
                    "priority": "high",
                }
            )

        return data_needs

    async def _analyze_history(
        self,
        user_input: str,
        context: str,
        user_info: Optional[Dict],
        medical_data: Dict[str, Any],
    ) -> str:
        """
        病史分析（内化功能）

        分析用户病史，包括：
        - 病史信息提取
        - 症状关联分析
        - 病史风险评估
        - 病史模式识别

        参数：
            user_input (str): 用户输入
            context (str): 对话上下文
            user_info (Dict, optional): 用户信息（已自动补全）
            medical_data (Dict[str, Any]): 医疗数据

        返回：
            str: 病史分析结果
        """
        try:
            # 构建用户信息字符串
            user_info_str = ""
            if user_info:
                user_info_str = f"""
用户信息：
- 年龄：{user_info.get("age", "未知")}
- 性别：{user_info.get("gender", "未知")}
- 既往病史：{user_info.get("medical_history", "无")}
- 家族病史：{user_info.get("family_history", "无")}
- 过敏史：{user_info.get("allergies", "无")}
"""

            # 构建病史分析提示
            history_prompt = f"""作为一位经验丰富的内科医生，请进行病史分析：

当前症状：{user_input}

对话历史：
{context}
{user_info_str}

医疗数据：
- 病史记录：{medical_data.get("medical_history", "无")}
- 用药记录：{medical_data.get("medications", "无")}
- 检查结果：{medical_data.get("lab_results", "无")}

请进行系统性的病史分析，重点关注：

## [病史信息提取]
- 从患者描述和医疗数据中提取关键病史信息
- 识别既往疾病、慢性病史、急性病史等
- 提取家族病史和遗传因素
- 整理用药史、过敏史和疫苗接种史

## [症状关联分析]
- 分析当前症状与既往病史的关联性
- 识别可能的疾病进展模式
- 分析症状的复发或加重因素
- 评估既往治疗的效果

## [时间线分析]
- 构建详细的症状发展时间线
- 分析症状的急慢性特征
- 识别症状的诱发和缓解因素
- 评估症状的发展趋势

## [风险因素识别]
- 识别可能的危险因素和预警信号
- 评估疾病的严重程度和紧急程度
- 分析并发症的风险
- 识别需要紧急处理的情况

## [病史模式识别]
- 识别病史中的典型模式和规律
- 分析疾病的发展轨迹
- 识别可能的疾病关联
- 评估病史的完整性和可靠性

请用简洁明了的语言进行病史分析，重点突出对当前内科诊断有帮助的信息。"""

            # 调用LLM进行病史分析
            print(f"[{self.name}] 开始调用LLM进行病史分析...")
            history_analysis = await self.caller(history_prompt, self.model_config)
            print(
                f"[{self.name}] 病史分析LLM调用完成，结果长度: {len(str(history_analysis))} 字符"
            )
            history_analysis = self._filter_thinking_content(history_analysis)

            self.logger.info(f"[{self.name}] 病史分析完成")
            return history_analysis

        except Exception as e:
            self.logger.warning(f"[{self.name}] 病史分析失败: {str(e)}")
            return "病史信息不完整，建议进一步了解患者病史。"

    def _filter_thinking_content(self, content: str) -> str:
        """
        过滤掉"Thinking"内容，只保留最终诊断结果

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
                lines = content.split("\n")
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
                    if (
                        "Final Response" in line
                        or "最终响应" in line
                        or "最终回答" in line
                    ):
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
                    return "\n".join(filtered_lines)

            # 如果没有Thinking标记，直接返回原内容
            return content

        except Exception as e:
            self.logger.error(f"[{self.name}] 过滤Thinking内容失败: {str(e)}")
            return content
