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
直接医疗数据优化功能测试
========================

测试在第二次请求时，数据代理返回健康监测数据，医疗应用直接处理而不请求数据存储服务的功能。

作者: QSIR
版本: 1.0
"""

import asyncio
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DirectMedicalDataOptimizationTest:
    """直接医疗数据优化功能测试类"""
    
    def __init__(self):
        self.medical_app_url = "http://localhost:8000"
        self.data_proxy_url = "http://localhost:9000"
        self.data_storage_url = "http://localhost:8001"
        self.test_results = []
        
    async def check_services_health(self) -> bool:
        """检查所有服务的健康状态"""
        print("\n" + "=" * 80)
        print("步骤1: 检查服务健康状态")
        print("=" * 80)
        
        services = [
            ("数据存储服务", self.data_storage_url, "/health"),
            ("数据代理应用", self.data_proxy_url, "/health"),
            ("医疗应用", self.medical_app_url, "/health")
        ]
        
        all_ok = True
        async with aiohttp.ClientSession() as session:
            for name, base_url, endpoint in services:
                try:
                    url = f"{base_url}{endpoint}"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            print(f"[PASS] {name}健康检查")
                            self.test_results.append({"test": f"{name}健康检查", "status": "PASS"})
                        else:
                            print(f"[FAIL] {name}健康检查 - HTTP {response.status}")
                            self.test_results.append({"test": f"{name}健康检查", "status": "FAIL", "error": f"HTTP {response.status}"})
                            all_ok = False
                except Exception as e:
                    print(f"[FAIL] {name}健康检查 - {str(e)}")
                    self.test_results.append({"test": f"{name}健康检查", "status": "FAIL", "error": str(e)})
                    all_ok = False
        
        return all_ok
    
    async def test_first_round_request(self) -> bool:
        """测试第一轮请求（应该只返回数据地址，不返回直接数据）"""
        print("\n" + "=" * 80)
        print("步骤2: 测试第一轮请求（应该只返回数据地址）")
        print("=" * 80)
        
        try:
            async with aiohttp.ClientSession() as session:
                # 模拟第一轮请求
                url = f"{self.data_proxy_url}/api/v1/data-proxy/request"
                payload = {
                    "intent_type": "内科咨询",
                    "specialty": "内科",
                    "user_id": "test_user_001",
                    "symptoms": ["多饮多尿", "乏力"],
                    "context": {
                        "conversation_round": 1,
                        "symptom_description": "最近多饮多尿，感觉乏力"
                    },
                    "request_id": f"req_test_{int(datetime.now().timestamp())}",
                    "priority": "medium"
                }
                
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 验证响应格式
                        has_direct_data = result.get("has_direct_data", False)
                        medical_data = result.get("medical_data")
                        
                        if has_direct_data:
                            print(f"[FAIL] 第一轮请求不应该包含直接数据")
                            self.test_results.append({
                                "test": "第一轮请求验证",
                                "status": "FAIL",
                                "error": "第一轮请求包含了直接数据，不符合预期"
                            })
                            return False
                        else:
                            print(f"[PASS] 第一轮请求只返回数据地址（符合预期）")
                            print(f"   数据地址数量: {len(result.get('data_addresses', []))}")
                            self.test_results.append({
                                "test": "第一轮请求验证",
                                "status": "PASS"
                            })
                            return True
                    else:
                        error_text = await response.text()
                        print(f"[FAIL] 第一轮请求失败 - HTTP {response.status}: {error_text}")
                        self.test_results.append({
                            "test": "第一轮请求验证",
                            "status": "FAIL",
                            "error": f"HTTP {response.status}: {error_text}"
                        })
                        return False
        except Exception as e:
            print(f"[FAIL] 第一轮请求异常: {str(e)}")
            self.test_results.append({
                "test": "第一轮请求验证",
                "status": "FAIL",
                "error": str(e)
            })
            return False
    
    async def test_second_round_with_health_monitoring(self) -> bool:
        """测试第二轮请求健康监测数据（应该返回直接数据）"""
        print("\n" + "=" * 80)
        print("步骤3: 测试第二轮请求健康监测数据（应该返回直接数据）")
        print("=" * 80)
        
        try:
            async with aiohttp.ClientSession() as session:
                # 模拟第二轮请求，请求健康监测数据
                url = f"{self.data_proxy_url}/api/v1/data-proxy/request"
                payload = {
                    "intent_type": "内科咨询",
                    "specialty": "内科",
                    "user_id": "test_user_001",
                    "symptoms": ["多饮多尿", "乏力"],
                    "context": {
                        "conversation_round": 2,
                        "symptom_description": "需要补充近期实时健康监测数据",
                        "specialist_requests": [
                            {
                                "location": "beijing",
                                "data_types": ["健康监测数据"],
                                "reason": "需要实时健康监测数据以提高诊断准确性",
                                "priority": "high"
                            }
                        ]
                    },
                    "request_id": f"req_test_{int(datetime.now().timestamp())}",
                    "priority": "high"
                }
                
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 验证响应格式
                        has_direct_data = result.get("has_direct_data", False)
                        medical_data = result.get("medical_data")
                        
                        if has_direct_data and medical_data:
                            print(f"[PASS] 第二轮请求包含直接医疗数据（符合预期）")
                            print(f"   数据类型: {medical_data.get('available_data_types', [])}")
                            print(f"   数据来源: {medical_data.get('sources', [])}")
                            
                            # 验证数据格式
                            if "health_monitoring" in medical_data:
                                print(f"   [OK] 包含健康监测数据")
                            else:
                                print(f"   [WARN] 健康监测数据格式可能不完整")
                            
                            self.test_results.append({
                                "test": "第二轮请求直接数据验证",
                                "status": "PASS",
                                "data_types": medical_data.get('available_data_types', [])
                            })
                            return True
                        else:
                            print(f"[FAIL] 第二轮请求未包含直接数据（不符合预期）")
                            print(f"   has_direct_data: {has_direct_data}")
                            print(f"   medical_data: {medical_data is not None}")
                            self.test_results.append({
                                "test": "第二轮请求直接数据验证",
                                "status": "FAIL",
                                "error": "未包含直接医疗数据"
                            })
                            return False
                    else:
                        error_text = await response.text()
                        print(f"[FAIL] 第二轮请求失败 - HTTP {response.status}: {error_text}")
                        self.test_results.append({
                            "test": "第二轮请求直接数据验证",
                            "status": "FAIL",
                            "error": f"HTTP {response.status}: {error_text}"
                        })
                        return False
        except Exception as e:
            print(f"[FAIL] 第二轮请求异常: {str(e)}")
            self.test_results.append({
                "test": "第二轮请求直接数据验证",
                "status": "FAIL",
                "error": str(e)
            })
            return False
    
    async def test_shared_context_integration(self) -> bool:
        """测试共享上下文集成（验证直接数据是否正确传递）"""
        print("\n" + "=" * 80)
        print("步骤4: 测试共享上下文集成")
        print("=" * 80)
        
        try:
            # 测试SharedContext类
            from shared.agents.utils.shared_context import SharedContext
            
            # 创建共享上下文
            context = SharedContext(
                user_id="test_user_001",
                intent="内科咨询",
                user_input="多饮多尿，感觉乏力",
                user_info={}
            )
            
            # 模拟直接医疗数据
            direct_data = {
                "health_monitoring": {
                    "blood_pressure": {"systolic": 120, "diastolic": 80},
                    "blood_glucose": {"value": 5.5}
                },
                "sources": ["北京医院"],
                "available_data_types": ["健康监测数据"]
            }
            
            # 设置直接数据
            context.direct_medical_data = direct_data
            
            # 验证数据存储
            if context.direct_medical_data == direct_data:
                print(f"[PASS] 共享上下文可以正确存储直接医疗数据")
                
                # 测试序列化
                context_dict = context.to_dict()
                if "direct_medical_data" in context_dict:
                    print(f"[PASS] 共享上下文序列化包含直接医疗数据")
                    
                    # 测试反序列化
                    restored_context = SharedContext.from_dict(context_dict)
                    if restored_context.direct_medical_data == direct_data:
                        print(f"[PASS] 共享上下文反序列化正确")
                        self.test_results.append({
                            "test": "共享上下文集成验证",
                            "status": "PASS"
                        })
                        return True
                    else:
                        print(f"[FAIL] 共享上下文反序列化失败")
                        self.test_results.append({
                            "test": "共享上下文集成验证",
                            "status": "FAIL",
                            "error": "反序列化失败"
                        })
                        return False
                else:
                    print(f"[FAIL] 共享上下文序列化未包含直接医疗数据")
                    self.test_results.append({
                        "test": "共享上下文集成验证",
                        "status": "FAIL",
                        "error": "序列化未包含直接医疗数据"
                    })
                    return False
            else:
                print(f"[FAIL] 共享上下文无法正确存储直接医疗数据")
                self.test_results.append({
                    "test": "共享上下文集成验证",
                    "status": "FAIL",
                    "error": "无法存储直接医疗数据"
                })
                return False
        except Exception as e:
            print(f"[FAIL] 共享上下文集成测试异常: {str(e)}")
            self.test_results.append({
                "test": "共享上下文集成验证",
                "status": "FAIL",
                "error": str(e)
            })
            return False
    
    async def test_specialist_agent_integration(self) -> bool:
        """测试专科医生集成（验证是否能正确使用直接数据）"""
        print("\n" + "=" * 80)
        print("步骤5: 测试专科医生集成")
        print("=" * 80)
        
        try:
            # 测试InternalMedicineAgent
            from shared.agents.specialists.internal_medicine_agent import InternalMedicineAgent
            from shared.agents.utils.shared_context import SharedContext
            
            # 创建专科医生（需要model_config）
            from shared.agents.base_agent import BaseAgent
            model_config = {
                "model_name": "test_model",
                "api_key": "test_key"
            }
            agent = InternalMedicineAgent(
                model_config=model_config,
                location="beijing"
            )
            
            # 创建共享上下文，包含直接数据
            context = SharedContext(
                user_id="test_user_001",
                intent="内科咨询",
                user_input="多饮多尿",
                user_info={}
            )
            
            direct_data = {
                "health_monitoring": {
                    "blood_pressure": {"systolic": 120, "diastolic": 80},
                    "blood_glucose": {"value": 5.5}
                },
                "sources": ["北京医院"],
                "available_data_types": ["健康监测数据"]
            }
            context.direct_medical_data = direct_data
            
            # 测试_read_data_from_addresses方法
            medical_data = await agent._read_data_from_addresses(
                data_addresses=[],
                user_id="test_user_001",
                direct_medical_data=direct_data
            )
            
            if medical_data == direct_data:
                print(f"[PASS] 专科医生可以正确使用直接医疗数据")
                self.test_results.append({
                    "test": "专科医生集成验证",
                    "status": "PASS"
                })
                return True
            else:
                print(f"[FAIL] 专科医生无法正确使用直接医疗数据")
                self.test_results.append({
                    "test": "专科医生集成验证",
                    "status": "FAIL",
                    "error": "返回的数据与直接数据不匹配"
                })
                return False
        except Exception as e:
            print(f"[FAIL] 专科医生集成测试异常: {str(e)}")
            import traceback
            traceback.print_exc()
            self.test_results.append({
                "test": "专科医生集成验证",
                "status": "FAIL",
                "error": str(e)
            })
            return False
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = total - passed
        
        print(f"\n总测试数: {total}")
        print(f"[PASS] 通过: {passed}")
        print(f"[FAIL] 失败: {failed}")
        
        if failed > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result.get('error', '未知错误')}")
        
        print("\n" + "=" * 80)
        
        return failed == 0
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("直接医疗数据优化功能自动化测试")
        print("=" * 80)
        print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"医疗应用: {self.medical_app_url}")
        print(f"数据代理应用: {self.data_proxy_url}")
        print(f"数据存储服务: {self.data_storage_url}")
        
        # 运行测试
        tests = [
            ("服务健康检查", self.check_services_health),
            ("第一轮请求验证", self.test_first_round_request),
            ("第二轮请求直接数据验证", self.test_second_round_with_health_monitoring),
            ("共享上下文集成", self.test_shared_context_integration),
            ("专科医生集成", self.test_specialist_agent_integration)
        ]
        
        for test_name, test_func in tests:
            try:
                await test_func()
            except Exception as e:
                print(f"\n[ERROR] {test_name}测试异常: {str(e)}")
                self.test_results.append({
                    "test": test_name,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        # 打印总结
        success = self.print_summary()
        
        return success


async def main():
    """主函数"""
    test = DirectMedicalDataOptimizationTest()
    success = await test.run_all_tests()
    
    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

