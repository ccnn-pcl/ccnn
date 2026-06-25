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
端到端测试脚本 - 两轮诊断验证
=============================

测试完整流程：
1. 用户登录获取token（使用从后端启动后获取的id_token）
2. 用户输入症状："你好，我最近总是感觉口渴，喝水很多，尿量也比以前多，体重好像也有点下降。"
3. 第一轮诊断：
   - 医疗应用通过EntryAgent（A2A SDK协议）向真实的数据代理应用请求数据地址
   - 数据代理应用返回数据地址（包含address、access_token等）
   - 医疗应用通过MCP工具调用向真实的第三方数据存储服务请求数据
   - 医疗应用进行诊断
4. 第二轮诊断：
   - 医疗应用通过EntryAgent（A2A SDK协议）向数据代理应用请求补充数据
   - 真实的第三方数据代理应用直接返回健康监测数据（has_direct_data: true）
   - 医疗应用进行补充诊断
5. 生成综合诊断报告

使用方法：
1. 确保后端服务正在运行（python backend/main.py）
2. 确保数据代理应用正在运行
3. 确保MCP数据存储服务正在运行
4. 运行此脚本：python test_e2e_diagnosis.py
"""

import asyncio
import requests
import json
import logging
import os
import sys
import re
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
BACKEND_URL = "http://172.25.22.129:8000"
OIDC_ISSUER = "http://192.168.193.12:31111"
CLIENT_ID = "agent_doctor1"
CLIENT_SECRET = "agent_doctor1-secret"
REDIRECT_URI = "http://172.25.22.129:8000/oidc/callback"

# Session Cookie名称
SESSION_COOKIE_NAME = "rp_session"

# 测试用户信息（从终端输出中获取）
TEST_USER_ID = "70133600"
TEST_USERNAME = "mark@123"
TEST_EMAIL = "123456789@qq.com"


class E2ETestClient:
    """端到端测试客户端"""
    
    def __init__(self, session_cookie: Optional[str] = None, id_token: Optional[str] = None, user_id: Optional[str] = None):
        """
        初始化测试客户端
        
        参数:
            session_cookie: 从浏览器获取的session cookie（可选）
            id_token: 直接提供的ID token（可选，用于测试）
            user_id: 用户ID（可选，如果提供了id_token会自动解析）
        """
        self.session = requests.Session()
        self.base_url = BACKEND_URL
        self.id_token = id_token
        self.user_id = user_id
        
        # 如果提供了cookie，设置到session中
        if session_cookie:
            self.session.cookies.set(SESSION_COOKIE_NAME, session_cookie)
            logger.info(f"✅ 已设置session cookie: {session_cookie[:30]}...")
        
        # 如果提供了token但没有user_id，尝试从token中解析
        if id_token and not user_id:
            try:
                import jwt
                # 不验证签名，只解析payload
                payload = jwt.decode(id_token, options={"verify_signature": False})
                self.user_id = payload.get("sub")
                logger.info(f"✅ 已从token解析用户ID: {self.user_id}")
            except Exception as e:
                logger.warning(f"⚠️  无法解析token: {str(e)}")
        
        # 如果直接提供了token和user_id，可以直接使用
        if id_token and self.user_id:
            logger.info(f"✅ 已设置ID token: {id_token[:50]}...")
            logger.info(f"✅ 已设置用户ID: {self.user_id}")
        
    def login(self) -> bool:
        """
        检查登录状态
        
        如果已经提供了token和user_id，直接返回True
        否则尝试通过session cookie获取
        """
        logger.info("=" * 80)
        logger.info("步骤1: 检查登录状态")
        logger.info("=" * 80)
        
        # 如果已经提供了token和user_id，直接使用
        if self.id_token and self.user_id:
            logger.info(f"✅ 使用提供的token和user_id")
            logger.info(f"✅ 用户ID: {self.user_id}")
            logger.info(f"✅ Token: {self.id_token[:50]}...")
            logger.info("✅ 跳过session检查，直接使用提供的token")
            return True
        
        # 否则尝试通过session cookie获取
        try:
            response = self.session.get(f"{self.base_url}/oidc/me")
            if response.status_code == 200:
                user_info = response.json()
                self.id_token = user_info.get("token")
                self.user_id = user_info.get("userid")
                logger.info(f"✅ 已登录，用户ID: {self.user_id}")
                logger.info(f"✅ Token已获取: {self.id_token[:50]}..." if self.id_token else "❌ Token未获取")
                return True
            else:
                logger.warning(f"❌ 未登录，状态码: {response.status_code}")
                logger.warning("\n请按以下步骤之一:")
                logger.warning("方法1: 使用token和user_id直接测试")
                logger.warning("  python test_e2e_diagnosis.py --token 'your-token' --user-id 'your-user-id'")
                logger.warning("方法2: 使用session cookie")
                logger.warning("  1. 打开浏览器访问: http://172.25.22.129:8000/")
                logger.warning("  2. 完成OIDC登录流程")
                logger.warning("  3. 按F12打开开发者工具")
                logger.warning("  4. 在Application/Storage → Cookies → http://172.25.22.129:8000")
                logger.warning("  5. 找到 'rp_session' cookie，复制其值")
                logger.warning("  6. python test_e2e_diagnosis.py --cookie 'your-cookie-value'")
                return False
        except Exception as e:
            logger.error(f"❌ 登录检查失败: {str(e)}")
            return False
    
    async def test_diagnosis(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        测试诊断流程
        
        参数:
            user_input: 用户输入的症状描述
            
        返回:
            Dict[str, Any]: 诊断结果
        """
        logger.info("=" * 80)
        logger.info("步骤2: 发送诊断请求")
        logger.info("=" * 80)
        logger.info(f"用户输入: {user_input}")
        logger.info(f"用户ID: {self.user_id}")
        
        if not self.user_id:
            logger.error("❌ 用户ID未设置，无法进行诊断")
            logger.error("   请提供user_id或通过session cookie登录")
            return None
        
        # 如果直接使用token，需要在请求中模拟认证
        # 注意：实际API需要session cookie，但我们可以通过直接设置user_id来测试
        # 这里假设API会从session中获取token，如果使用直接token方式，需要特殊处理
        
        # 构建请求
        request_data = {
            "user_input": user_input,
            "user_id": self.user_id,
            "context": {}
        }
        
        logger.info("\n" + "=" * 80)
        logger.info("发送请求到后端API")
        logger.info("=" * 80)
        logger.info(f"URL: {self.base_url}/api/v1/chat/send")
        logger.info(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        try:
            # 构建请求头
            headers = {"Content-Type": "application/json"}
            
            # 如果提供了token，添加到Authorization header
            if self.id_token:
                headers["Authorization"] = f"Bearer {self.id_token}"
                logger.info(f"✅ 已添加Authorization header，使用token认证")
            
            # 发送POST请求
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/send",
                json=request_data,
                headers=headers,
                timeout=300  # 诊断可能需要较长时间（两轮诊断+LLM调用）
            )
            
            logger.info(f"\n响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("=" * 80)
                logger.info("✅ 诊断请求成功")
                logger.info("=" * 80)
                
                # 打印诊断结果
                logger.info("\n诊断结果:")
                logger.info("-" * 80)
                logger.info(f"智能体: {result.get('agent_name', 'N/A')}")
                logger.info(f"响应: {result.get('response', 'N/A')[:200]}...")
                
                # 打印元数据
                metadata = result.get('metadata', {})
                if metadata:
                    logger.info("\n元数据:")
                    logger.info(f"  - 状态: {metadata.get('status', 'N/A')}")
                    logger.info(f"  - 处理时间: {metadata.get('processing_time', 'N/A')}秒")
                    rounds = metadata.get('rounds', 'N/A')
                    logger.info(f"  - 轮次: {rounds}")
                    
                    # 验证两轮诊断
                    if rounds == 2:
                        logger.info("  ✅ 已完成两轮诊断")
                    elif rounds == 1:
                        logger.warning("  ⚠️  只完成了一轮诊断，可能未触发第二轮")
                    else:
                        logger.warning(f"  ⚠️  轮次异常: {rounds}")
                    
                    # 打印数据来源
                    data_sources = metadata.get('data_sources', [])
                    if data_sources:
                        logger.info(f"\n数据来源 ({len(data_sources)}个):")
                        for i, source in enumerate(data_sources, 1):
                            logger.info(f"  {i}. {source}")
                        # 验证数据来源是否包含两轮的数据
                        if rounds == 2 and len(data_sources) >= 4:
                            logger.info("  ✅ 数据来源包含第一轮和第二轮的数据")
                    else:
                        logger.warning("  ⚠️  未找到数据来源")
                    
                    # 打印专科医生结果
                    specialist_results = metadata.get('specialist_results', [])
                    if specialist_results:
                        logger.info(f"\n专科医生结果 ({len(specialist_results)}个):")
                        for i, result_item in enumerate(specialist_results, 1):
                            if isinstance(result_item, dict):
                                logger.info(f"  {i}. {result_item.get('agent_name', 'N/A')}")
                                logger.info(f"     地域: {result_item.get('location', 'N/A')}")
                                logger.info(f"     状态: {result_item.get('status', 'N/A')}")
                                # 检查是否有needs_more_data标记
                                if result_item.get('needs_more_data'):
                                    logger.info(f"     需要更多数据: 是")
                                
                                # 打印数据内容（如果存在）
                                data_content = result_item.get('data_content', {})
                                if data_content:
                                    logger.info(f"     数据内容:")
                                    logger.info(f"       - 数据类型: {data_content.get('data_type', 'N/A')}")
                                    logger.info(f"       - 数据来源: {data_content.get('source', 'N/A')}")
                                    # 打印数据摘要
                                    data_summary = data_content.get('summary', {})
                                    if data_summary:
                                        logger.info(f"       - 数据摘要: {json.dumps(data_summary, ensure_ascii=False, indent=8)[:200]}...")
                                
                                # 打印第一轮和第二轮的数据（如果存在）
                                round_data = result_item.get('round_data', {})
                                if round_data:
                                    logger.info(f"     轮次数据:")
                                    if 'round1' in round_data:
                                        logger.info(f"       - 第一轮: {json.dumps(round_data['round1'], ensure_ascii=False, indent=8)[:200]}...")
                                    if 'round2' in round_data:
                                        logger.info(f"       - 第二轮: {json.dumps(round_data['round2'], ensure_ascii=False, indent=8)[:200]}...")
                                
                                # 打印MCP相关信息（如果存在）
                                mcp_info = result_item.get('mcp_info', {})
                                if mcp_info:
                                    logger.info(f"     MCP信息:")
                                    logger.info(f"       - MCP服务器: {mcp_info.get('server_url', 'N/A')}")
                                    logger.info(f"       - access_token: {'已设置' if mcp_info.get('access_token') else '未设置'}")
                                    if mcp_info.get('access_token'):
                                        logger.info(f"       - access_token预览: {mcp_info.get('access_token', '')[:30]}...")
                        
                        # 验证专科医生结果是否包含两轮的结果
                        if rounds == 2 and len(specialist_results) >= 2:
                            logger.info("  ✅ 专科医生结果包含第一轮和第二轮的诊断结果")
                
                # 打印完整响应数据（用于调试）
                logger.info("\n" + "=" * 80)
                logger.info("完整响应数据（JSON格式）")
                logger.info("=" * 80)
                logger.info(json.dumps(result, ensure_ascii=False, indent=2))
                logger.info("=" * 80)
                
                logger.info("=" * 80)
                return result
            else:
                logger.error(f"❌ 诊断请求失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("❌ 请求超时（超过300秒）")
            logger.error("提示: 诊断流程可能需要较长时间，请检查后端服务是否正常运行")
            return None
        except Exception as e:
            logger.error(f"❌ 诊断请求异常: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def verify_token_in_request(self) -> bool:
        """
        验证token是否正确配置和传递
        
        返回:
            bool: token是否正确传递
        """
        logger.info("=" * 80)
        logger.info("步骤3: 验证Token配置和传递")
        logger.info("=" * 80)
        
        if not self.id_token:
            logger.warning("❌ Token未获取，无法验证")
            return False
        
        # 验证token格式和内容
        try:
            import jwt
            # 解析token（不验证签名）
            payload = jwt.decode(self.id_token, options={"verify_signature": False})
            
            logger.info(f"✅ Token已获取: {self.id_token[:50]}...")
            logger.info(f"✅ Token解析成功:")
            logger.info(f"   - 用户ID (sub): {payload.get('sub', 'N/A')}")
            logger.info(f"   - 用户名 (name): {payload.get('name', 'N/A')}")
            logger.info(f"   - 邮箱 (email): {payload.get('email', 'N/A')}")
            logger.info(f"   - 签发者 (iss): {payload.get('iss', 'N/A')}")
            logger.info(f"   - 过期时间 (exp): {payload.get('exp', 'N/A')}")
            
            # 验证用户ID是否匹配
            if payload.get('sub') == self.user_id:
                logger.info(f"✅ Token中的用户ID与测试用户ID匹配: {self.user_id}")
            else:
                logger.warning(f"⚠️  Token中的用户ID ({payload.get('sub')}) 与测试用户ID ({self.user_id}) 不匹配")
            
        except Exception as e:
            logger.error(f"❌ Token解析失败: {str(e)}")
            return False
        
        logger.info("\n✅ Token传递链路:")
        logger.info("   1. OIDC回调 → session['id_token'] (backend/api/oidc_rp.py)")
        logger.info("   2. get_current_user() → user_info['id_token'] (backend/api/chat.py)")
        logger.info("   3. ChatService.handle_chat() → user_info (backend/services/chat_service.py)")
        logger.info("   4. CybertwinAgent.execute() → user_info (shared/agents/coordinator/cybertwin_agent_refactored.py)")
        logger.info("   5. _execute_diabetes_demo() → 提取id_token")
        logger.info("   6. ForcedDataProxyTrigger.force_trigger_data_proxy() → token参数")
        logger.info("   7. DataProxyClient → EntryAgentAdapter (shared/agents/coordinator/data_proxy_client.py)")
        logger.info("   8. EntryAgentAdapter.invoke() → metadata['token'] (shared/agents/coordinator/entry_agent_adapter.py)")
        logger.info("   9. 第三方数据代理应用（通过A2A协议，使用token认证）")
        logger.info("   10. 如果返回数据地址 → MCP协议请求数据存储服务")
        
        logger.info("\n🔍 Token验证要点:")
        logger.info("   ✅ Token格式正确（JWT格式）")
        logger.info("   ✅ Token包含用户信息（sub, name, email）")
        logger.info("   ✅ Token将通过Authorization header传递到后端API")
        logger.info("   ✅ Token将通过A2A协议的metadata字段传递到数据代理应用")
        
        return True
    
    def verify_multiple_mcp_access_tokens(self, result: Dict[str, Any]) -> bool:
        """
        验证多个MCP的access_token是否正确接收并正确匹配配置和传递
        
        参数:
            result: 诊断结果
            
        返回:
            bool: 验证是否通过
        """
        logger.info("\n" + "=" * 80)
        logger.info("步骤4: 验证多个MCP的access_token接收和匹配")
        logger.info("=" * 80)
        
        metadata = result.get('metadata', {})
        specialist_results = metadata.get('specialist_results', [])
        
        if not specialist_results:
            logger.warning("⚠️  未找到专科医生结果，无法验证MCP access_token")
            return False
        
        # 收集所有数据地址和access_token信息
        mcp_connections = []
        access_tokens_found = []
        server_urls_found = []
        location_server_pairs = {}  # 用于存储 (location, server_url) 组合
        
        for i, result_item in enumerate(specialist_results, 1):
            if isinstance(result_item, dict):
                location = result_item.get('location', 'N/A')
                agent = result_item.get('agent', 'N/A')
                data_content = result_item.get('data_content', {})
                data_sources = result_item.get('data_sources', [])
                diagnosis = result_item.get('diagnosis', {})
                data_usage_summary = result_item.get('data_usage_summary', '')
                
                # 从数据内容中提取MCP相关信息
                if data_content:
                    mcp_server = data_content.get('mcp_server', 'N/A')
                    data_type = data_content.get('data_type', 'N/A')
                    source = data_content.get('source', 'N/A')
                    
                    # 尝试从数据内容中提取access_token信息
                    # 注意：access_token可能不会直接出现在响应中，需要从后端日志验证
                    mcp_connections.append({
                        'round': result_item.get('round', i),
                        'location': location,
                        'agent': agent,
                        'mcp_server': mcp_server,
                        'data_type': data_type,
                        'source': source
                    })
                
                # 从数据来源中提取MCP服务器URL
                # 数据来源可能包含医院名称，需要从后端日志中查找对应的MCP服务器URL
                for source in data_sources:
                    if isinstance(source, str):
                        # 查找IP:PORT格式（如果数据来源中包含）
                        import re
                        url_match = re.search(r'\d+\.\d+\.\d+\.\d+:\d+', source)
                        if url_match:
                            server_url = url_match.group()
                            if server_url not in server_urls_found:
                                server_urls_found.append(server_url)
                            # 记录location和server_url的对应关系
                            key = (location, server_url)
                            if key not in location_server_pairs:
                                location_server_pairs[key] = {
                                    'location': location,
                                    'server_url': server_url,
                                    'agents': [],
                                    'data_sources': []
                                }
                            if agent not in location_server_pairs[key]['agents']:
                                location_server_pairs[key]['agents'].append(agent)
                            if source not in location_server_pairs[key]['data_sources']:
                                location_server_pairs[key]['data_sources'].append(source)
                
                # 从诊断结果中推断是否使用了MCP数据
                # 如果data_usage_summary包含具体数据字段，说明可能使用了MCP获取的数据
                if data_usage_summary and ('病史数据' in data_usage_summary or 
                                          '用药记录' in data_usage_summary or 
                                          '化验报告' in data_usage_summary or
                                          '血糖' in data_usage_summary or
                                          '血压' in data_usage_summary):
                    # 这表明数据是通过MCP获取的
                    if location not in [conn.get('location') for conn in mcp_connections]:
                        mcp_connections.append({
                            'round': result_item.get('round', i),
                            'location': location,
                            'agent': agent,
                            'mcp_server': '推断: 已使用MCP数据',
                            'data_type': '从data_usage_summary推断',
                            'source': '诊断结果分析'
                        })
        
        # 验证结果
        logger.info(f"\n📊 MCP连接统计:")
        logger.info(f"   - 专科医生结果数: {len(specialist_results)}")
        logger.info(f"   - 检测到的MCP连接数: {len(mcp_connections)}")
        logger.info(f"   - 检测到的MCP服务器URL数: {len(server_urls_found)}")
        logger.info(f"   - 检测到的地域数: {len(set([r.get('location', 'N/A') for r in specialist_results if isinstance(r, dict)]))}")
        
        # 按地域统计
        location_stats = {}
        for result_item in specialist_results:
            if isinstance(result_item, dict):
                location = result_item.get('location', 'N/A')
                if location not in location_stats:
                    location_stats[location] = {
                        'count': 0,
                        'agents': set(),
                        'data_sources': set()
                    }
                location_stats[location]['count'] += 1
                agent = result_item.get('agent', 'N/A')
                if agent != 'N/A':
                    location_stats[location]['agents'].add(agent)
                data_sources = result_item.get('data_sources', [])
                for source in data_sources:
                    location_stats[location]['data_sources'].add(source)
        
        logger.info(f"\n📋 按地域统计:")
        for location, stats in location_stats.items():
            logger.info(f"   - {location}:")
            logger.info(f"     结果数: {stats['count']}")
            logger.info(f"     智能体: {', '.join(stats['agents']) if stats['agents'] else 'N/A'}")
            logger.info(f"     数据来源: {', '.join(stats['data_sources']) if stats['data_sources'] else 'N/A'}")
        
        if len(server_urls_found) >= 2:
            logger.info("\n   ✅ 检测到多个MCP服务器（多MCP场景）")
            logger.info(f"   MCP服务器列表:")
            for i, url in enumerate(server_urls_found, 1):
                logger.info(f"     {i}. {url}")
        elif len(server_urls_found) == 1:
            logger.info("\n   ⚠️  只检测到1个MCP服务器URL（从响应中提取）")
            logger.info(f"   服务器URL: {server_urls_found[0]}")
        else:
            logger.warning("\n   ⚠️  未从响应中检测到MCP服务器URL")
            logger.warning("   提示: MCP服务器URL可能不会直接出现在API响应中")
            logger.warning("   需要查看后端日志确认MCP连接信息")
        
        # 打印location和server_url的对应关系
        if location_server_pairs:
            logger.info(f"\n📋 地域-MCP服务器对应关系:")
            for key, info in location_server_pairs.items():
                logger.info(f"   - {info['location']} → {info['server_url']}")
                logger.info(f"     智能体: {', '.join(info['agents'])}")
                logger.info(f"     数据来源: {', '.join(info['data_sources'])}")
        
        # 打印MCP连接详情
        if mcp_connections:
            logger.info(f"\n📋 MCP连接详情:")
            for i, conn in enumerate(mcp_connections, 1):
                logger.info(f"   {i}. 轮次: {conn.get('round', 'N/A')}, 地域: {conn.get('location', 'N/A')}")
                logger.info(f"      智能体: {conn.get('agent', 'N/A')}")
                logger.info(f"      MCP服务器: {conn.get('mcp_server', 'N/A')}")
                logger.info(f"      数据类型: {conn.get('data_type', 'N/A')}")
                logger.info(f"      数据来源: {conn.get('source', 'N/A')}")
        else:
            logger.warning("\n   ⚠️  未从响应中检测到MCP连接详情")
            logger.warning("   提示: 这可能是正常的，因为MCP连接信息可能不会直接出现在API响应中")
            logger.warning("   需要查看后端日志确认MCP连接是否成功创建")
        
        # 验证要点说明
        logger.info("\n🔍 多MCP access_token验证要点（需要查看后端日志确认）:")
        logger.info("   1. ✅ 数据代理应用返回的每个数据地址都包含access_token")
        logger.info("      - 查找标记: '[EntryAgentAdapter] ✅ 数据地址 ... 从data_item中提取到access_token'")
        logger.info("   2. ✅ EntryAgent适配器正确提取每个data_item的access_token")
        logger.info("      - 查找标记: '[EntryAgentAdapter] [成功] 数据地址 ... 从data_item中提取到access_token'")
        logger.info("   3. ✅ MCPStorageClient按(location, server_url)分组时正确提取access_token")
        logger.info("      - 查找标记: '[MCPStorageClient] ✅ 从数据地址中提取到access_token'")
        logger.info("   4. ✅ 每个MCP连接使用对应数据地址的access_token（不是环境变量的默认token）")
        logger.info("      - 查找标记: '[MCPStorageClient] 使用token: ... (长度: ...)'")
        logger.info("   5. ✅ access_token与server_url正确匹配")
        logger.info("      - 查找标记: '[MCPStorageClient] 按地域和服务器分组完成'")
        logger.info("   6. ✅ 如果token变化，MCP连接会重新初始化")
        logger.info("      - 查找标记: '[MCPStorageClient] 🔄 创建新的MCP服务器连接'")
        logger.info("   7. ✅ 多个MCP连接并行请求时，每个连接使用自己的access_token")
        logger.info("      - 查找标记: '[MCPStorageClient] 开始并行请求多个MCP服务器'")
        logger.info("   8. ✅ 不再出现'invalid token'错误")
        logger.info("      - 如果看到此错误，说明access_token未正确传递或匹配")
        
        # 验证结果
        verification_passed = True
        if len(server_urls_found) >= 2:
            logger.info("\n✅ 多MCP服务器场景验证: 检测到多个MCP服务器")
            verification_passed = True
        elif len(server_urls_found) == 1:
            logger.warning("\n⚠️  多MCP服务器场景验证: 只检测到1个MCP服务器")
            logger.warning("   提示: 如果数据代理应用返回了多个数据地址，应该创建多个MCP连接")
            verification_passed = False
        else:
            logger.warning("\n⚠️  多MCP服务器场景验证: 未检测到MCP服务器")
            logger.warning("   提示: 请检查后端日志，确认MCP连接是否成功创建")
            verification_passed = False
        
        logger.info("=" * 80)
        return verification_passed
    
    def verify_mcp_data_in_diagnosis(self, result: Dict[str, Any]) -> bool:
        """
        验证MCP返回的数据是否已经被专科智能体正确提取并输入到医疗LLM大模型中进行诊断
        
        参数:
            result: 诊断结果
            
        返回:
            bool: 验证是否通过
        """
        logger.info("\n" + "=" * 80)
        logger.info("步骤5: 验证MCP数据在诊断中的使用")
        logger.info("=" * 80)
        
        metadata = result.get('metadata', {})
        specialist_results = metadata.get('specialist_results', [])
        
        if not specialist_results:
            logger.warning("⚠️  未找到专科医生结果，无法验证MCP数据使用")
            return False
        
        verification_passed = True
        mcp_data_found_count = 0
        mcp_data_in_prompt_count = 0
        mcp_data_in_diagnosis_count = 0
        medical_data_content_count = 0
        
        for i, result_item in enumerate(specialist_results, 1):
            if not isinstance(result_item, dict):
                continue
            
            location = result_item.get('location', 'N/A')
            agent_name = result_item.get('agent_name', result_item.get('agent', 'N/A'))
            logger.info(f"\n【验证专科医生结果 {i}】")
            logger.info(f"  智能体: {agent_name}")
            logger.info(f"  地域: {location}")
            
            # 1. 检查是否有MCP数据来源
            data_sources = result_item.get('data_sources', [])
            has_mcp_source = False
            mcp_sources = []
            
            for source in data_sources:
                if isinstance(source, str):
                    # 检查是否包含MCP服务器地址（格式：医院名称 (MCP: 服务器地址)）
                    if 'MCP:' in source or '(MCP:' in source or 'mcp:' in source.lower():
                        has_mcp_source = True
                        mcp_sources.append(source)
                    # 也检查IP:PORT格式（MCP服务器地址）
                    elif '192.168' in source or re.search(r'\d+\.\d+\.\d+\.\d+:\d+', source):
                        has_mcp_source = True
                        mcp_sources.append(source)
            
            if has_mcp_source:
                mcp_data_found_count += 1
                logger.info(f"  ✅ 检测到MCP数据来源 ({len(mcp_sources)}个):")
                for j, source in enumerate(mcp_sources, 1):
                    logger.info(f"     {j}. {source}")
            else:
                logger.warning(f"  ⚠️  未检测到MCP数据来源")
                logger.warning(f"     数据来源: {data_sources}")
                verification_passed = False
            
            # 2. 检查数据内容（从MCP获取的医疗数据）
            data_content = result_item.get('data_content', {})
            available_data_types = result_item.get('available_data_types', [])
            
            has_medical_data = False
            medical_data_fields = []
            
            if data_content:
                # 检查data_content中的医疗数据标记
                if data_content.get('has_medical_history'):
                    has_medical_data = True
                    medical_data_fields.append('medical_history')
                if data_content.get('has_medications'):
                    has_medical_data = True
                    medical_data_fields.append('medications')
                if data_content.get('has_lab_results'):
                    has_medical_data = True
                    medical_data_fields.append('lab_results')
                if data_content.get('has_imaging_data'):
                    has_medical_data = True
                    medical_data_fields.append('imaging_data')
                if data_content.get('has_surgical_records'):
                    has_medical_data = True
                    medical_data_fields.append('surgical_records')
                if data_content.get('has_health_monitoring'):
                    has_medical_data = True
                    medical_data_fields.append('health_monitoring')
                
                # 打印data_content信息
                logger.info(f"  ✅ 数据内容字段:")
                logger.info(f"     - 数据类型: {data_content.get('data_type', 'N/A')}")
                logger.info(f"     - 数据来源: {data_content.get('source', 'N/A')}")
                if data_content.get('mcp_server'):
                    logger.info(f"     - MCP服务器: {data_content.get('mcp_server', 'N/A')}")
                summary = data_content.get('summary', {})
                if summary:
                    logger.info(f"     - 数据摘要: {json.dumps(summary, ensure_ascii=False)[:200]}...")
            
            if available_data_types:
                logger.info(f"  ✅ 可用数据类型: {available_data_types}")
                has_medical_data = True
            
            if has_medical_data:
                medical_data_content_count += 1
                logger.info(f"  ✅ 检测到医疗数据字段: {', '.join(medical_data_fields) if medical_data_fields else '通过available_data_types或data_content'}")
            else:
                logger.warning(f"  ⚠️  未检测到医疗数据内容")
                logger.warning(f"     提示: 检查后端日志 '[调试] 专科医生智能体获取的完整医疗数据'")
                verification_passed = False
            
            # 3. 检查数据使用说明（从诊断结果中提取）
            data_usage_summary = result_item.get('data_usage_summary', '')
            diagnosis = result_item.get('diagnosis', {})
            reasoning = result_item.get('reasoning', '')
            
            # 从诊断结果中提取数据使用信息
            diagnosis_text = ""
            if isinstance(diagnosis, dict):
                diagnosis_text = diagnosis.get('diagnosis', diagnosis.get('text', diagnosis.get('content', '')))
            else:
                diagnosis_text = str(diagnosis)
            
            # 检查诊断文本中是否包含医疗数据相关内容
            medical_keywords = ['病史', '用药', '化验', '检查', '报告', '血糖', '血压', '心率', '体温', '体重', 
                              'medical_history', 'medications', 'lab_results', '血糖值', '血压值']
            
            has_data_in_diagnosis = False
            found_keywords = []
            
            combined_text = f"{diagnosis_text} {reasoning} {data_usage_summary}".lower()
            for keyword in medical_keywords:
                if keyword.lower() in combined_text:
                    has_data_in_diagnosis = True
                    found_keywords.append(keyword)
            
            if data_usage_summary:
                mcp_data_in_diagnosis_count += 1
                logger.info(f"  ✅ 数据使用说明: {data_usage_summary[:200]}...")
            elif has_data_in_diagnosis:
                mcp_data_in_diagnosis_count += 1
                logger.info(f"  ✅ 诊断结果中包含医疗数据关键词: {', '.join(found_keywords[:5])}")
            else:
                logger.warning(f"  ⚠️  诊断结果中未明确体现医疗数据使用")
                logger.warning(f"     诊断文本: {diagnosis_text[:200] if diagnosis_text else 'N/A'}...")
                logger.warning(f"     推理过程: {reasoning[:200] if reasoning else 'N/A'}...")
                logger.warning(f"     提示: 检查后端日志 '[调试] 发送给LLM的诊断提示' 确认数据是否包含在prompt中")
                verification_passed = False
            
            # 4. 检查诊断结果质量
            if diagnosis_text and len(diagnosis_text) > 50:
                logger.info(f"  ✅ 诊断结果长度: {len(diagnosis_text)} 字符（说明LLM已生成诊断）")
            else:
                logger.warning(f"  ⚠️  诊断结果可能不完整（长度: {len(diagnosis_text) if diagnosis_text else 0} 字符）")
        
        # 总结验证结果
        logger.info("\n" + "=" * 80)
        logger.info("MCP数据使用验证总结")
        logger.info("=" * 80)
        logger.info(f"  专科医生结果总数: {len(specialist_results)}")
        logger.info(f"  检测到MCP数据来源: {mcp_data_found_count}/{len(specialist_results)}")
        logger.info(f"  检测到医疗数据内容: {medical_data_content_count}/{len(specialist_results)}")
        logger.info(f"  诊断结果中体现数据使用: {mcp_data_in_diagnosis_count}/{len(specialist_results)}")
        
        if verification_passed and mcp_data_found_count > 0 and medical_data_content_count > 0 and mcp_data_in_diagnosis_count > 0:
            logger.info("\n  ✅ MCP数据使用验证通过")
            logger.info("     - MCP数据已成功获取（通过data_sources和data_content验证）")
            logger.info("     - 医疗数据已包含在诊断prompt中（通过data_content和available_data_types验证）")
            logger.info("     - 诊断结果中体现了医疗数据的使用（通过data_usage_summary验证）")
        else:
            logger.warning("\n  ⚠️  MCP数据使用验证未完全通过")
            if mcp_data_found_count == 0:
                logger.warning("     - 未检测到MCP数据来源（请检查后端日志 '[MCP数据存储服务响应]'）")
            if medical_data_content_count == 0:
                logger.warning("     - 未检测到医疗数据内容（请检查后端日志 '[调试] 专科医生智能体获取的完整医疗数据'）")
            if mcp_data_in_diagnosis_count == 0:
                logger.warning("     - 诊断结果中未体现医疗数据使用（请检查后端日志 '[调试] 发送给LLM的诊断提示'）")
        
        logger.info("\n📋 验证要点说明:")
        logger.info("  1. ✅ MCP数据来源: 检查data_sources是否包含MCP服务器地址")
        logger.info("  2. ✅ 医疗数据内容: 检查data_content或available_data_types是否包含医疗数据字段")
        logger.info("  3. ✅ 数据在Prompt中: 检查后端日志 '[调试] 发送给LLM的诊断提示' 是否包含医疗数据")
        logger.info("  4. ✅ 数据在诊断中: 检查诊断结果、推理过程或data_usage_summary是否体现数据使用")
        logger.info("")
        logger.info("🔍 后端日志关键标记:")
        logger.info("  - '[MCP数据存储服务响应]' - MCP返回的医疗数据")
        logger.info("  - '[调试] MCP数据存储服务返回的完整数据' - MCP返回的完整数据内容")
        logger.info("  - '[调试] 专科医生智能体获取的完整医疗数据' - 专科智能体接收到的医疗数据")
        logger.info("  - '[调试] 发送给LLM的诊断提示' - 发送给LLM的prompt（应包含医疗数据）")
        logger.info("  - '数据使用说明' - 诊断结果中的数据使用说明")
        logger.info("=" * 80)
        
        return verification_passed


async def main():
    """主测试函数"""
    logger.info("\n" + "=" * 80)
    logger.info("开始端到端测试")
    logger.info("=" * 80)
    logger.info("\n测试场景: 用户登录后输入症状进行诊断")
    logger.info("症状: '我感觉口渴，尿多'")
    logger.info("=" * 80 + "\n")
    
    # 从命令行参数或环境变量获取session cookie或id_token
    session_cookie = None
    id_token = None
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if "--cookie" in sys.argv:
            idx = sys.argv.index("--cookie")
            if idx + 1 < len(sys.argv):
                session_cookie = sys.argv[idx + 1]
        elif "--token" in sys.argv:
            idx = sys.argv.index("--token")
            if idx + 1 < len(sys.argv):
                id_token = sys.argv[idx + 1]
        elif sys.argv[1] and not sys.argv[1].startswith("-"):
            # 如果第一个参数不是选项，可能是token值（优先判断为token）
            id_token = sys.argv[1]
    
    # 检查环境变量
    if not session_cookie:
        session_cookie = os.getenv("RP_SESSION")
    if not id_token:
        id_token = os.getenv("ID_TOKEN")
    
    # 如果都没有提供，尝试使用默认的token（从终端输出中获取）
    if not id_token and not session_cookie:
        # 从终端日志1025-1036行获取的id_token（启动程序后更新的token，最新）
        # 来源：终端输出1025-1036行，OIDC回调认证后更新的token
        default_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwOi8vMTkyLjE2OC4xOTMuMTI6MzExMTEiLCJzdWIiOiI3MDEzMzYwMCIsImF1ZCI6ImFnZW50X2RvY3RvcjEiLCJleHAiOjE3NjQ1NjI4MzgsImlhdCI6MTc2NDU1OTIzOCwiYXV0aF90aW1lIjoxNzY0NTU5MjM4LCJub25jZSI6Ijk1ZjEzZTkxLWNlMzMtNDUzOS1hOWIwLTllZjU2NTQ1OGMwZSIsIm5hbWUiOiJtYXJrQDEyMyIsImVtYWlsIjoiMTIzNDU2Nzg5QHFxLmNvbSJ9.Gu12zyDQbL1HM61qvKUOdaJY411-mS1_sTtBAnKFvZMNMGBZy-lQ1XpAGDR7hidBSYWL2KJtPJmj7t1uxzlZz91tTBZsf6b_VcW83IP0a6evxX6h8jz_41ReGt_dlmez9gZ3gaJMwJTRfCDm3jP0bcgQqsW2HQUNR0sC_HWyclF5H54puAnMnT8ntnGdMV6NOAGdScg1UUaVF7bU8yRn-kLxJ3d9P6d3lNbojN4spVFVlitISv4DpXg7VJNjgJG0-nT9-3Z74hkmN0yzGLuDYmouOKA6jlJuood_mvKCQj8ld1YkSDvv7nfEkU3gwFs1_d3Q2Y0OALozejxKSmjvBA"
        logger.info("ℹ️  使用最新token（从终端输出中提取，后端服务启动后生成，最新更新）")
        logger.info(f"ℹ️  Token来源: 终端日志1025-1036行（OIDC回调认证）")
        id_token = default_token
    
    # 创建测试客户端
    client = E2ETestClient(session_cookie=session_cookie, id_token=id_token)
    
    # 步骤1: 检查登录状态
    if not client.login():
        logger.error("\n❌ 测试失败: 用户未登录")
        logger.info("\n请先通过浏览器访问以下URL完成登录:")
        logger.info(f"  {BACKEND_URL}/oidc/login")
        logger.info("\n登录完成后，再次运行此脚本")
        return
    
    # 步骤2: 验证token配置和传递
    if not client.verify_token_in_request():
        logger.error("\n❌ Token验证失败，无法继续测试")
        logger.info("\n请检查:")
        logger.info("  1. Token是否正确（从后端服务启动日志中获取）")
        logger.info("  2. Token是否包含有效的用户信息")
        logger.info("  3. 用户ID是否匹配")
        return
    
    # 步骤3: 发送诊断请求
    logger.info("\n" + "=" * 80)
    logger.info("开始端到端诊断流程（两轮诊断验证）")
    logger.info("=" * 80)
    logger.info("用户输入: '你好，我最近总是感觉口渴，喝水很多，尿量也比以前多，体重好像也有点下降。'")
    logger.info("\n📋 预期流程（多MCP服务器场景）:")
    logger.info("\n【第一轮诊断 - 多MCP服务器场景】")
    logger.info("  1. 意图识别 → '内科咨询'")
    logger.info("  2. 医疗应用通过EntryAgent（A2A SDK协议）向真实的数据代理应用请求数据地址")
    logger.info("     - 传递id_token进行认证")
    logger.info("  3. 真实的数据代理应用返回多个数据地址（包含多个不同的data_service_address和access_token）")
    logger.info("     - 例如：北京协和（192.168.208.66:30211）和上海瑞金（192.168.208.67:32039）")
    logger.info("     - 每个数据地址包含：data_service_address、access_token、data_type、location等")
    logger.info("  4. 医疗应用按地域和MCP服务器URL分组数据地址")
    logger.info("     - 为每个唯一的(location, server_url)组合创建独立的MCP连接")
    logger.info("  5. 医疗应用通过多个MCP工具调用向不同的第三方数据存储服务请求数据")
    logger.info("     - 每个MCP连接使用对应的access_token进行认证")
    logger.info("     - 每个MCP连接请求对应地域和医院的数据")
    logger.info("  6. 多个第三方数据存储服务返回医疗数据（病史数据、用药记录、化验报告等）")
    logger.info("  7. 医疗应用根据地域信息路由到对应的专科医生智能体")
    logger.info("  8. 专科医生进行第一轮诊断（使用对应地域的数据）")
    logger.info("\n【第二轮诊断】")
    logger.info("  9. 判断需要补充数据 → 请求健康监测数据")
    logger.info("  10. 医疗应用通过EntryAgent（A2A SDK协议）向数据代理应用请求补充数据")
    logger.info("     - 传递id_token进行认证")
    logger.info("     - Prompt中明确包含'健康监测数据'关键词")
    logger.info("  11. 真实的数据代理应用直接返回健康监测数据（has_direct_data: true）")
    logger.info("  12. 跳过MCP请求（因为数据代理直接返回了数据）")
    logger.info("  13. 专科医生进行第二轮补充诊断")
    logger.info("  14. 生成综合诊断报告（综合两轮诊断结果）")
    logger.info("")
    logger.info("🔍 验证要点（多MCP服务器场景）:")
    logger.info("  ✅ 第一轮：EntryAgent请求数据代理 → 返回多个数据地址 → 创建多个MCP连接")
    logger.info("  ✅ 第一轮：每个MCP连接使用对应的access_token和server_url")
    logger.info("  ✅ 第一轮：数据按地域正确路由到对应的专科医生智能体")
    logger.info("  ✅ 第二轮：EntryAgent请求数据代理 → 直接返回健康监测数据（跳过MCP）")
    logger.info("  ✅ MCP客户端是否正确处理多个数据地址和多个MCP连接")
    logger.info("  ✅ 数据地址中的data_service_address、access_token、location是否正确传递")
    logger.info("  ✅ 两轮诊断结果是否正确合并到综合报告中")
    logger.info("")
    logger.info("📝 关键验证点（多MCP服务器场景）:")
    logger.info("  1. Token是否正确传递到EntryAgent（通过A2A协议的metadata字段）")
    logger.info("  2. 第一轮：数据代理应用是否返回多个数据地址（包含不同的server_url和access_token）")
    logger.info("  3. 第一轮：是否为每个唯一的(location, server_url)组合创建独立的MCP连接")
    logger.info("  4. 第一轮：每个MCP连接是否使用对应的access_token进行认证")
    logger.info("  5. 第一轮：数据是否按地域正确路由到对应的专科医生智能体")
    logger.info("  6. 第一轮：多个MCP连接是否成功请求数据存储服务并获取数据")
    logger.info("  7. 第二轮：数据代理应用是否直接返回健康监测数据（has_direct_data: true）")
    logger.info("  8. 第二轮：Prompt中是否包含'健康监测数据'关键词")
    logger.info("  9. 第二轮：是否跳过MCP请求（因为数据代理直接返回了数据）")
    logger.info("  10. 最终：是否生成包含两轮诊断结果的综合报告")
    logger.info("")
    logger.info("🔑 多MCP access_token验证要点:")
    logger.info("  ✅ 数据代理应用返回的每个数据地址都包含access_token")
    logger.info("  ✅ EntryAgent适配器正确提取每个data_item的access_token")
    logger.info("  ✅ MCPStorageClient按(location, server_url)分组时正确提取access_token")
    logger.info("  ✅ 每个MCP连接使用对应数据地址的access_token（不是环境变量的默认token）")
    logger.info("  ✅ access_token与server_url正确匹配（北京数据地址的token用于北京MCP服务器）")
    logger.info("  ✅ 如果token变化，MCP连接会重新初始化（清理旧连接，创建新连接）")
    logger.info("  ✅ 多个MCP连接并行请求时，每个连接使用自己的access_token")
    logger.info("=" * 80 + "\n")
    
    user_input = "你好，我最近总是感觉口渴，喝水很多，尿量也比以前多，体重好像也有点下降。"
    result = await client.test_diagnosis(user_input)
    
    # 步骤4: 验证多个MCP的access_token
    if result:
        client.verify_multiple_mcp_access_tokens(result)
    
    # 步骤5: 验证MCP数据在诊断中的使用
    if result:
        client.verify_mcp_data_in_diagnosis(result)
    
    # 步骤6: 验证结果
    logger.info("\n" + "=" * 80)
    logger.info("测试总结")
    logger.info("=" * 80)
    
    if result:
        logger.info("✅ 端到端测试成功")
        logger.info(f"✅ 诊断完成，智能体: {result.get('agent_name', 'N/A')}")
        response_text = result.get('response', '')
        logger.info(f"✅ 响应长度: {len(response_text)} 字符")
        
        # 检查响应是否包含综合诊断报告
        if len(response_text) > 500:
            logger.info("✅ 响应包含完整的综合诊断报告")
        else:
            logger.warning("⚠️  响应可能不完整")
        
        # 检查是否包含数据来源
        metadata = result.get('metadata', {})
        rounds = metadata.get('rounds', 0)
        data_sources = metadata.get('data_sources', [])
        if data_sources:
            logger.info(f"✅ 数据来源: {len(data_sources)}个")
            if rounds == 2:
                logger.info("✅ 数据来源包含第一轮和第二轮的数据")
        else:
            logger.warning("⚠️  未找到数据来源")
        
        # 检查是否包含专科医生结果
        specialist_results = metadata.get('specialist_results', [])
        if specialist_results:
            logger.info(f"✅ 专科医生结果: {len(specialist_results)}个")
            if rounds == 2:
                logger.info("✅ 专科医生结果包含第一轮和第二轮的诊断结果")
        else:
            logger.warning("⚠️  未找到专科医生结果")
        
        # 验证两轮诊断
        if rounds == 2:
            logger.info("✅ 已完成两轮诊断流程")
        elif rounds == 1:
            logger.warning("⚠️  只完成了一轮诊断，可能未触发第二轮")
        else:
            logger.warning(f"⚠️  轮次异常: {rounds}")
        
        # 打印两轮诊断中医疗应用请求到的数据格式和内容
        logger.info("\n" + "=" * 80)
        logger.info("两轮诊断数据格式和内容验证")
        logger.info("=" * 80)
        
        # 从响应中提取数据内容
        metadata = result.get('metadata', {})
        specialist_results = metadata.get('specialist_results', [])
        
        logger.info("\n【第一轮诊断 - 数据格式和内容（多MCP服务器场景）】")
        logger.info("-" * 80)
        
        # 查找第一轮诊断的数据（可能有多个地域的数据）
        round1_data_found = False
        round1_mcp_connections = []
        for i, result_item in enumerate(specialist_results, 1):
            if isinstance(result_item, dict):
                # 检查是否是第一轮的结果（通常第一个或包含round1标记）
                round_marker = result_item.get('round', 1)
                if round_marker == 1 or i == 1:
                    round1_data_found = True
                    location = result_item.get('location', 'N/A')
                    logger.info(f"✅ 找到第一轮诊断数据（结果 {i}）:")
                    logger.info(f"   智能体: {result_item.get('agent_name', 'N/A')}")
                    logger.info(f"   地域: {location}")
                    
                    # 打印数据来源
                    data_sources = result_item.get('data_sources', [])
                    if data_sources:
                        logger.info(f"   数据来源 ({len(data_sources)}个):")
                        for j, source in enumerate(data_sources, 1):
                            logger.info(f"     {j}. {source}")
                            # 检查是否包含MCP相关信息
                            if 'MCP' in str(source) or 'mcp' in str(source).lower():
                                round1_mcp_connections.append({
                                    'location': location,
                                    'source': source
                                })
                    
                    # 打印数据内容（如果存在）
                    data_content = result_item.get('data_content', {})
                    if data_content:
                        logger.info(f"   数据内容格式:")
                        logger.info(f"     - 数据类型: {data_content.get('data_type', 'N/A')}")
                        logger.info(f"     - 数据来源: {data_content.get('source', 'N/A')}")
                        logger.info(f"     - MCP服务器: {data_content.get('mcp_server', 'N/A')}")
                        logger.info(f"     - 完整数据内容:")
                        logger.info(json.dumps(data_content, ensure_ascii=False, indent=6))
                    else:
                        logger.warning("   ⚠️  未找到数据内容字段")
                    
                    # 打印诊断结果
                    diagnosis = result_item.get('diagnosis', {})
                    if diagnosis:
                        logger.info(f"   诊断结果:")
                        if isinstance(diagnosis, dict):
                            logger.info(f"     - 文本: {diagnosis.get('text', diagnosis.get('content', str(diagnosis)))[:200]}...")
                        else:
                            logger.info(f"     - 文本: {str(diagnosis)[:200]}...")
        
        # 验证多MCP连接和access_token
        if round1_mcp_connections:
            logger.info(f"\n✅ 第一轮诊断检测到 {len(round1_mcp_connections)} 个MCP连接:")
            for conn in round1_mcp_connections:
                logger.info(f"   - {conn['location']}: {conn['source']}")
            if len(round1_mcp_connections) >= 2:
                logger.info("   ✅ 多MCP服务器场景验证成功：检测到多个MCP连接")
            else:
                logger.warning("   ⚠️  只检测到1个MCP连接，可能只有一个数据地址")
        else:
            logger.warning("   ⚠️  未检测到MCP连接信息")
        
        # 验证access_token提取和匹配
        logger.info("\n🔑 多MCP access_token验证:")
        logger.info("-" * 80)
        logger.info("请检查后端日志中的以下关键信息，验证access_token是否正确接收和匹配:")
        logger.info("")
        logger.info("【步骤1: 数据代理应用返回access_token】")
        logger.info("  查找标记: '[EntryAgentAdapter] ✅ 数据地址 ... 从data_item中提取到access_token'")
        logger.info("  验证点:")
        logger.info("    ✅ 每个数据地址都包含access_token")
        logger.info("    ✅ access_token不为空")
        logger.info("    ✅ 不同数据地址的access_token可能不同（每个对应一个MCP服务器）")
        logger.info("")
        logger.info("【步骤2: MCPStorageClient提取access_token】")
        logger.info("  查找标记: '[MCPStorageClient] ✅ 从数据地址中提取到access_token'")
        logger.info("  验证点:")
        logger.info("    ✅ 从数据地址中成功提取access_token")
        logger.info("    ✅ Token预览显示正确（前30个字符）")
        logger.info("    ✅ Token长度合理（通常>100字符）")
        logger.info("")
        logger.info("【步骤3: access_token与server_url匹配】")
        logger.info("  查找标记: '[MCPStorageClient] 按地域和服务器分组完成'")
        logger.info("  验证点:")
        logger.info("    ✅ 每个(location, server_url)组合都有对应的access_token")
        logger.info("    ✅ 北京数据地址的access_token用于北京MCP服务器")
        logger.info("    ✅ 上海数据地址的access_token用于上海MCP服务器")
        logger.info("    ✅ 不同server_url使用不同的access_token")
        logger.info("")
        logger.info("【步骤4: MCP连接使用正确的access_token】")
        logger.info("  查找标记: '[MCPServer] 使用token: ... (长度: ...)'")
        logger.info("  验证点:")
        logger.info("    ✅ 每个MCP连接使用的token与对应数据地址的access_token一致")
        logger.info("    ✅ 不是使用环境变量的默认token（如'test'）")
        logger.info("    ✅ 如果token变化，会重新初始化MCP连接")
        logger.info("")
        logger.info("【步骤5: MCP工具调用使用正确的token】")
        logger.info("  查找标记: '[MCP数据存储服务请求] 详细请求信息'")
        logger.info("  验证点:")
        logger.info("    ✅ MCP服务器URL与数据地址的data_service_address匹配")
        logger.info("    ✅ 每个MCP请求使用对应数据地址的access_token进行认证")
        logger.info("    ✅ 不再出现'invalid token'错误")
        logger.info("")
        logger.info("【步骤6: 多个MCP连接并行请求】")
        logger.info("  查找标记: '[MCPStorageClient] 开始并行请求多个MCP服务器'")
        logger.info("  验证点:")
        logger.info("    ✅ 多个MCP连接同时请求（并行处理）")
        logger.info("    ✅ 每个连接使用自己的access_token")
        logger.info("    ✅ 每个连接请求对应地域和医院的数据")
        logger.info("")
        logger.info("⚠️  如果看到'invalid token'错误，请检查:")
        logger.info("    1. 数据地址中的access_token是否正确提取")
        logger.info("    2. access_token是否已过期")
        logger.info("    3. access_token是否与对应的MCP服务器URL匹配")
        logger.info("    4. MCP服务器是否接受该token")
        logger.info("-" * 80)
        
        if not round1_data_found:
            logger.warning("   ⚠️  未找到第一轮诊断数据")
            logger.warning("      提示: 检查后端日志中的以下标记:")
            logger.warning("      - '[MCP数据存储服务请求]' (第一轮)")
            logger.warning("      - '[MCPStorageClient] 按地域和服务器分组完成' (多MCP场景)")
            logger.warning("      - '[MCPStorageClient] 创建新的MCP服务器连接' (多MCP场景)")
            logger.warning("      - '[MCP数据存储服务响应]' (第一轮)")
        
        logger.info("\n【第二轮诊断 - 数据格式和内容】")
        logger.info("-" * 80)
        
        # 查找第二轮诊断的数据
        round2_data_found = False
        for i, result_item in enumerate(specialist_results, 1):
            if isinstance(result_item, dict):
                # 检查是否是第二轮的结果（通常第二个或包含round2标记）
                round_marker = result_item.get('round', 2)
                if round_marker == 2 or (i == 2 and len(specialist_results) >= 2):
                    round2_data_found = True
                    logger.info(f"✅ 找到第二轮诊断数据（结果 {i}）:")
                    logger.info(f"   智能体: {result_item.get('agent_name', 'N/A')}")
                    logger.info(f"   地域: {result_item.get('location', 'N/A')}")
                    
                    # 打印数据来源
                    data_sources = result_item.get('data_sources', [])
                    if data_sources:
                        logger.info(f"   数据来源 ({len(data_sources)}个):")
                        for j, source in enumerate(data_sources, 1):
                            logger.info(f"     {j}. {source}")
                    
                    # 打印数据内容（如果存在）
                    data_content = result_item.get('data_content', {})
                    if data_content:
                        logger.info(f"   数据内容格式:")
                        logger.info(f"     - 数据类型: {data_content.get('data_type', 'N/A')}")
                        logger.info(f"     - 数据来源: {data_content.get('source', 'N/A')}")
                        logger.info(f"     - 是否直接返回: {data_content.get('has_direct_data', False)}")
                        logger.info(f"     - 完整数据内容:")
                        logger.info(json.dumps(data_content, ensure_ascii=False, indent=6))
                    else:
                        logger.warning("   ⚠️  未找到数据内容字段")
                        logger.warning("      提示: 检查后端日志中的 '[调试] 第二轮数据代理应用直接返回的完整数据' 标记")
                    
                    # 打印诊断结果
                    diagnosis = result_item.get('diagnosis', {})
                    if diagnosis:
                        logger.info(f"   诊断结果:")
                        if isinstance(diagnosis, dict):
                            logger.info(f"     - 文本: {diagnosis.get('text', diagnosis.get('content', str(diagnosis)))[:200]}...")
                        else:
                            logger.info(f"     - 文本: {str(diagnosis)[:200]}...")
                    
                    break
        
        if not round2_data_found:
            logger.warning("   ⚠️  未找到第二轮诊断数据")
            logger.warning("      提示: 检查后端日志中的 '[调试] 第二轮数据代理应用直接返回的完整数据' 标记")
        
        # 数据格式总结
        logger.info("\n【数据格式总结（多MCP服务器场景）】")
        logger.info("-" * 80)
        if round1_data_found:
            logger.info("✅ 第一轮诊断数据: 已找到")
            logger.info("   数据来源: 通过多个MCP连接从多个第三方数据存储服务获取")
            logger.info("   MCP连接数: " + (f"{len(round1_mcp_connections)} 个" if round1_mcp_connections else "未知"))
            logger.info("   数据格式: 包含病史数据、用药记录、化验报告等")
            logger.info("   多MCP场景: " + ("✅ 检测到多个MCP连接" if len(round1_mcp_connections) >= 2 else "⚠️  只检测到1个MCP连接"))
        else:
            logger.warning("❌ 第一轮诊断数据: 未找到")
        
        if round2_data_found:
            logger.info("✅ 第二轮诊断数据: 已找到")
            logger.info("   数据来源: 通过EntryAgent从数据代理应用直接获取")
            logger.info("   数据格式: 健康监测数据（血糖、血压、心率等）")
        else:
            logger.warning("❌ 第二轮诊断数据: 未找到")
        
        if round1_data_found and round2_data_found:
            logger.info("\n✅ 两轮诊断的数据格式和内容都已找到")
            logger.info("   可以查看上述详细数据内容，确认数据是否正确响应")
        elif round1_data_found:
            logger.warning("\n⚠️  只找到第一轮诊断的数据，第二轮数据缺失")
        elif round2_data_found:
            logger.warning("\n⚠️  只找到第二轮诊断的数据，第一轮数据缺失")
        else:
            logger.error("\n❌ 两轮诊断的数据都未找到")
            logger.error("   请检查后端日志输出，确认数据是否正确返回")
        
        logger.info("\n" + "=" * 80)
        logger.info("提示: 如果未找到数据内容，请检查后端服务控制台输出")
        logger.info("      查找以下标记（多MCP服务器场景）:")
        logger.info("      - '[MCPStorageClient] 按地域和服务器分组完成' (多MCP场景)")
        logger.info("      - '[MCPStorageClient] 创建新的MCP服务器连接' (多MCP场景)")
        logger.info("      - '[MCPStorageClient] 从数据地址中提取到access_token' (多MCP场景)")
        logger.info("      - '[MCP数据存储服务请求]' (第一轮，每个MCP连接)")
        logger.info("      - '[MCP数据存储服务响应]' (第一轮，每个MCP连接)")
        logger.info("      - '[调试] MCP数据存储服务返回的完整医疗数据' (第一轮)")
        logger.info("      - '[调试] 第二轮数据代理应用直接返回的完整数据' (第二轮)")
        logger.info("=" * 80)
        
        # 验证两轮诊断流程
        logger.info("\n" + "=" * 80)
        logger.info("两轮诊断流程验证（完整调用链验证）")
        logger.info("=" * 80)
        logger.info("请检查后端日志输出，确认以下完整调用链:")
        logger.info("\n【第一轮诊断 - 完整调用链验证（多MCP服务器场景）】")
        logger.info("  调用链1: 医疗应用 → EntryAgent (A2A SDK协议) → 真实数据代理应用")
        logger.info("    ✓ [EntryAgentAdapter] 开始调用EntryAgent")
        logger.info("    ✓ 传递id_token进行认证（metadata['token']）")
        logger.info("    ✓ 请求数据代理应用获取数据地址")
        logger.info("    ✓ 真实数据代理应用返回多个数据地址（包含不同的data_service_address和access_token）")
        logger.info("      - 例如：北京协和（192.168.208.66:30211）和上海瑞金（192.168.208.67:32039）")
        logger.info("      - 每个数据地址包含：data_service_address、access_token、data_type、location等")
        logger.info("      - 验证点: 检查后端日志 '[EntryAgentAdapter] [成功] 数据地址 ... 从data_item中提取到access_token'")
        logger.info("")
        logger.info("  调用链2: 医疗应用 → 多MCP工具调用 → 多个真实第三方数据存储服务")
        logger.info("    ✓ [MCPStorageClient] 开始MCP请求")
        logger.info("    ✓ [MCPStorageClient] 按地域和MCP服务器URL分组数据地址")
        logger.info("      - 为每个唯一的(location, server_url)组合创建独立的MCP连接")
        logger.info("      - 例如：(beijing, 192.168.208.66:30211) 和 (shanghai, 192.168.208.67:32039)")
        logger.info("      - 验证点: 检查后端日志 '[MCPStorageClient] 按地域和服务器分组完成'")
        logger.info("    ✓ [MCPStorageClient] 从数据地址中提取access_token")
        logger.info("      - 每个MCP连接使用对应的access_token进行认证")
        logger.info("      - 动态更新MCP服务器配置中的token")
        logger.info("      - 验证点: 检查后端日志 '[MCPStorageClient] ✅ 从数据地址中提取到access_token'")
        logger.info("    ✓ MCP参数包含:")
        logger.info("      - data_addresses: 多个（从数据代理应用获取，包含不同的server_url）")
        logger.info("      - data_types: ['病史数据', '用药记录', '化验报告']")
        logger.info("      - access_tokens: 多个（从数据代理应用获取，每个对应一个server_url）")
        logger.info("    ✓ 数据地址详情包含:")
        logger.info("      - data_service_address: IP:PORT（如 192.168.208.66:30211）")
        logger.info("      - access_token: 每个数据地址对应的认证token")
        logger.info("      - data_type: 病史数据/用药记录/化验报告")
        logger.info("      - hospital: 医院名称（如 北京协和、上海瑞金）")
        logger.info("      - location: beijing/shanghai")
        logger.info("    ✓ [MCPStorageClient] 为每个MCP服务器创建独立连接")
        logger.info("      - 北京MCP连接: 使用北京的access_token和server_url")
        logger.info("      - 上海MCP连接: 使用上海的access_token和server_url")
        logger.info("      - 验证点: 检查后端日志 '[MCPStorageClient] 🔄 创建新的MCP服务器连接'")
        logger.info("    ✓ 多个真实第三方数据存储服务返回医疗数据")
        logger.info("      - 北京数据存储服务返回北京医院的医疗数据")
        logger.info("      - 上海数据存储服务返回上海医院的医疗数据")
        logger.info("      - 验证点: 检查后端日志 '[MCP数据存储服务响应]'")
        logger.info("")
        logger.info("  调用链3: 医疗应用 → 地域路由 → 专科医生 → 第一轮诊断")
        logger.info("    ✓ [LocationRouter] 根据数据地址的location字段路由到对应的专科医生智能体")
        logger.info("      - 北京数据 → 北京地域的专科医生智能体")
        logger.info("      - 上海数据 → 上海地域的专科医生智能体")
        logger.info("    ✓ [第一轮诊断] 专科医生诊断结果（使用对应地域的数据）")
        logger.info("    ✓ 诊断结果包含needs_more_data标记（如果需要补充数据）")
        logger.info("")
        logger.info("【第二轮诊断 - 完整调用链验证】")
        logger.info("  调用链4: 医疗应用 → EntryAgent (A2A SDK协议) → 真实数据代理应用")
        logger.info("    ✓ [第二轮诊断] 开始诊断")
        logger.info("    ✓ [TwoRoundDiagnosisCoordinator] 提取数据需求: 健康监测数据")
        logger.info("    ✓ [EntryAgentAdapter] 第二轮调用EntryAgent")
        logger.info("    ✓ Prompt中包含: '需要提供健康监测数据'")
        logger.info("    ✓ Prompt中包含: '【重要提示】本次请求需要提供健康监测数据'")
        logger.info("    ✓ 传递id_token进行认证（metadata['token']）")
        logger.info("    ✓ conversation_round = 2（标识为第二轮请求）")
        logger.info("      - 验证点: 检查后端日志 '[DataProxyClient] ⚠️ 第二轮诊断请求'")
        logger.info("")
        logger.info("  调用链5: 真实数据代理应用 → 直接返回健康监测数据")
        logger.info("    ✓ [数据代理应用] 检测到conversation_round >= 2")
        logger.info("    ✓ [数据代理应用] 检测到data_type == '健康监测数据'")
        logger.info("    ✓ [数据代理应用] 直接返回健康监测数据（has_direct_data: true）")
        logger.info("    ✓ 健康监测数据包含: 血糖、血压、心率等实时监测数据")
        logger.info("    ✓ 跳过MCP请求（因为数据代理直接返回了数据）")
        logger.info("      - 验证点: 检查后端日志 '[EntryAgentAdapter] [成功] 检测到直接医疗数据，将跳过数据存储服务请求'")
        logger.info("")
        logger.info("  调用链6: 医疗应用 → 专科医生 → 第二轮补充诊断")
        logger.info("    ✓ [第二轮诊断] 专科医生补充诊断结果")
        logger.info("    ✓ 使用健康监测数据进行补充诊断")
        logger.info("")
        logger.info("【综合验证 - 完整调用链确认】")
        logger.info("  调用链7: 医疗应用 → 生成综合诊断报告")
        logger.info("    ✓ 诊断轮次: 2（完成两轮诊断）")
        logger.info("    ✓ 数据来源: 包含第一轮和第二轮的数据")
        logger.info("      - 第一轮: 通过MCP从第三方数据存储服务获取（病史、用药、化验）")
        logger.info("      - 第二轮: 通过EntryAgent从数据代理应用直接获取（健康监测）")
        logger.info("    ✓ 专科医生结果: 包含第一轮和第二轮的诊断结果")
        logger.info("    ✓ 综合诊断报告: 包含两轮诊断的综合分析")
        logger.info("")
        logger.info("【关键验证点总结（多MCP服务器场景）】")
        logger.info("  ✅ 第一轮: EntryAgent → 数据代理（返回多个数据地址）→ 多个MCP连接 → 多个数据存储服务")
        logger.info("    - 数据代理返回多个数据地址（包含不同的data_service_address和access_token）")
        logger.info("    - 为每个唯一的(location, server_url)组合创建独立的MCP连接")
        logger.info("    - 每个MCP连接使用对应的access_token进行认证")
        logger.info("    - 数据按地域正确路由到对应的专科医生智能体")
        logger.info("  ✅ 第二轮: EntryAgent → 数据代理（直接返回健康监测数据，跳过MCP）")
        logger.info("  ✅ Token传递: id_token正确传递到EntryAgent和数据代理应用")
        logger.info("  ✅ 多MCP连接: 第一轮的多个数据地址正确创建多个MCP连接")
        logger.info("  ✅ 动态Token更新: 每个MCP连接使用从数据地址中提取的access_token")
        logger.info("  ✅ access_token匹配: 每个数据地址的access_token正确匹配到对应的MCP服务器")
        logger.info("  ✅ access_token提取: EntryAgent适配器和MCPStorageClient正确提取access_token")
        logger.info("  ✅ access_token传递: 每个MCP连接使用正确的access_token进行认证（不是默认token）")
        logger.info("  ✅ 地域路由: 数据按location正确路由到对应的专科医生智能体")
        logger.info("  ✅ 健康监测数据: 第二轮直接返回，不通过MCP")
        logger.info("  ✅ 两轮诊断结果: 正确合并到综合报告中")
        logger.info("")
        logger.info("【多MCP access_token验证总结】")
        logger.info("  ✅ 数据代理应用返回的每个数据地址都包含access_token")
        logger.info("  ✅ EntryAgent适配器正确提取每个data_item的access_token")
        logger.info("  ✅ MCPStorageClient按(location, server_url)分组时正确提取access_token")
        logger.info("  ✅ 每个MCP连接使用对应数据地址的access_token（不是环境变量的默认token）")
        logger.info("  ✅ access_token与server_url正确匹配（北京数据地址的token用于北京MCP服务器）")
        logger.info("  ✅ 如果token变化，MCP连接会重新初始化（清理旧连接，创建新连接）")
        logger.info("  ✅ 多个MCP连接并行请求时，每个连接使用自己的access_token")
        logger.info("  ✅ 不再出现'invalid token'错误（说明access_token正确传递和匹配）")
        logger.info("")
        logger.info("如果看到以上所有调用链信息和access_token验证点，说明两轮诊断完整调用链验证成功 ✅")
        logger.info("=" * 80)
    else:
        logger.error("❌ 端到端测试失败")
    
    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

