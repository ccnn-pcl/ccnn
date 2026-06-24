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
医疗数据获取编排服务
====================

最小落地版：
- 调用内部路由 /api/v1/third-party/request-data-proxy 获取 data_addresses
- 调用内部路由 /api/v1/third-party/retrieve-medical-data 获取 medical_data
- 仅体现 token 流程：通过环境变量注入，对内部路由不强制鉴权

使用方式：
    orchestrator = MedicalDataOrchestrator()
    medical_data = await orchestrator.get_medical_data_for_intent("内科咨询", user_input, user_id, user_info)
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp


class MedicalDataOrchestrator:
    def __init__(self):
        # 内部后端地址（FastAPI 主服务）
        self.backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
        # 超时
        self.timeout_seconds = int(os.getenv("THIRD_PARTY_TIMEOUT", "30"))

    async def _post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                # 不做复杂错误处理，最小落地
                try:
                    return await resp.json()
                except Exception:
                    text = await resp.text()
                    return {
                        "success": False,
                        "message": f"HTTP {resp.status}",
                        "raw": text,
                    }

    async def request_data_addresses(
        self,
        intent_type: str,
        specialty: str,
        user_id: str,
        symptoms: List[str],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        url = f"{self.backend_base_url}/api/v1/third-party/request-data-proxy"
        request_id = f"req_{user_id}_{int(datetime.now().timestamp())}"
        payload = {
            "intent_type": intent_type,
            "specialty": specialty,
            "user_id": user_id,
            "symptoms": symptoms or [],
            "context": context or {},
            "request_id": request_id,
            "priority": "medium",
        }
        result = await self._post_json(url, payload)
        if result.get("success"):
            return result.get("data_addresses", [])
        return []

    async def retrieve_medical_data(
        self, data_addresses: List[Dict[str, Any]], user_id: str, timeout: int = 30
    ) -> Dict[str, Any]:
        url = f"{self.backend_base_url}/api/v1/third-party/retrieve-medical-data"
        request_id = f"req_{user_id}_{int(datetime.now().timestamp())}"
        payload = {
            "data_addresses": data_addresses or [],
            "user_id": user_id,
            "request_id": request_id,
            "timeout": timeout,
        }
        result = await self._post_json(url, payload)
        if result.get("success"):
            return result.get("medical_data", {})
        return {}

    async def get_medical_data_for_intent(
        self,
        intent_type: str,
        user_input: str,
        user_id: str,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # 最小化：仅从 user_info 提取症状与上下文，非则走默认
        symptoms = user_info.get("symptoms", []) if user_info else []
        context = {"symptom_description": user_input}
        specialty = (
            "内科"
            if "内科" in intent_type
            else ("外科" if "外科" in intent_type else "影像")
        )

        addresses = await self.request_data_addresses(
            intent_type, specialty, user_id, symptoms, context
        )
        if not addresses:
            return {}
        return await self.retrieve_medical_data(
            addresses, user_id, timeout=self.timeout_seconds
        )


# 简单自测入口（可选）
async def _self_test():
    orch = MedicalDataOrchestrator()
    data = await orch.get_medical_data_for_intent(
        "内科咨询", "最近多饮多尿", "user_12345", {"symptoms": ["多饮", "多尿"]}
    )
    print("orchestrator test -> keys:", list(data.keys()))


if __name__ == "__main__":
    asyncio.run(_self_test())
