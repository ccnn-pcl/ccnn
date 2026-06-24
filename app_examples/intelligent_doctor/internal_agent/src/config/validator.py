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
配置验证器
==========

验证配置完整性，提供友好的错误提示和建议修复方案。

作者: QSIR
版本: 1.0
"""

import logging
from typing import List, Tuple, Dict, Any
from config.third_party_unified_config import ThirdPartyUnifiedConfig

logger = logging.getLogger(__name__)


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate(config: ThirdPartyUnifiedConfig) -> Tuple[bool, List[str], List[str]]:
        """
        验证配置
        
        参数:
            config: 配置对象
            
        返回:
            Tuple[bool, List[str], List[str]]: (是否有效, 错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        # 验证EntryAgent配置
        if config.entry_agent.enabled:
            if not config.entry_agent.base_url:
                errors.append("EntryAgent已启用但未配置base_url")
            elif not config.entry_agent.base_url.startswith(('http://', 'https://')):
                errors.append(f"EntryAgent base_url格式错误: {config.entry_agent.base_url}")
            
            if not config.entry_agent.token:
                warnings.append("EntryAgent未配置token，可能无法认证（如果URL中包含token则忽略此警告）")
            
            if config.entry_agent.timeout <= 0:
                errors.append(f"EntryAgent timeout必须大于0，当前值: {config.entry_agent.timeout}")
        
        # 验证MCP配置
        if config.mcp.enabled:
            if not config.mcp.beijing_url:
                errors.append("MCP已启用但未配置beijing_url")
            elif ':' not in config.mcp.beijing_url:
                warnings.append(f"MCP beijing_url格式可能不正确（应为host:port格式）: {config.mcp.beijing_url}")
            
            if not config.mcp.token:
                errors.append("MCP已启用但未配置token")
            
            if config.mcp.transport_type not in ['streamable-http', 'sse']:
                errors.append(f"MCP transport_type必须是'streamable-http'或'sse'，当前值: {config.mcp.transport_type}")
            
            if config.mcp.timeout <= 0:
                errors.append(f"MCP timeout必须大于0，当前值: {config.mcp.timeout}")
        
        # 验证HTTP配置（如果EntryAgent和MCP都未启用，HTTP应该配置）
        if not config.entry_agent.enabled and not config.mcp.enabled:
            if not config.http.beijing_url:
                warnings.append("EntryAgent和MCP都未启用，建议配置HTTP beijing_url作为降级方案")
        
        return len(errors) == 0, errors, warnings
    
    @staticmethod
    def get_suggestions(config: ThirdPartyUnifiedConfig) -> List[str]:
        """
        获取配置建议
        
        参数:
            config: 配置对象
            
        返回:
            List[str]: 建议列表
        """
        suggestions = []
        
        if config.entry_agent.enabled and not config.entry_agent.base_url:
            suggestions.append("设置环境变量: DATA_PROXY_APP_URL=http://your-server:port?token=your_token")
        
        if config.entry_agent.enabled and not config.entry_agent.token:
            suggestions.append("在DATA_PROXY_APP_URL中包含token参数，或设置环境变量: DATA_PROXY_TOKEN=your_token")
        
        if config.mcp.enabled and not config.mcp.beijing_url:
            suggestions.append("设置环境变量: MCP_SERVER_BEIJING_URL=your-server:port")
        
        if config.mcp.enabled and not config.mcp.token:
            suggestions.append("设置环境变量: MCP_SERVER_TOKEN=your_token")
        
        if not config.entry_agent.enabled and not config.mcp.enabled:
            suggestions.append("建议启用EntryAgent或MCP协议，设置USE_ENTRY_AGENT=true或USE_MCP_PROTOCOL=true")
        
        return suggestions
    
    @staticmethod
    def validate_and_report(config: ThirdPartyUnifiedConfig) -> Dict[str, Any]:
        """
        验证配置并生成报告
        
        参数:
            config: 配置对象
            
        返回:
            Dict[str, Any]: 验证报告
        """
        valid, errors, warnings = ConfigValidator.validate(config)
        suggestions = ConfigValidator.get_suggestions(config)
        
        report = {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "summary": {
                "entry_agent_enabled": config.entry_agent.enabled,
                "mcp_enabled": config.mcp.enabled,
                "http_fallback_available": bool(config.http.beijing_url)
            }
        }
        
        return report
    
    @staticmethod
    def print_report(report: Dict[str, Any]) -> None:
        """打印验证报告"""
        print("\n" + "=" * 80)
        print("配置验证报告")
        print("=" * 80)
        
        print(f"\n状态: {'✅ 有效' if report['valid'] else '❌ 无效'}")
        
        print(f"\n配置摘要:")
        summary = report['summary']
        print(f"  - EntryAgent启用: {summary['entry_agent_enabled']}")
        print(f"  - MCP启用: {summary['mcp_enabled']}")
        print(f"  - HTTP降级可用: {summary['http_fallback_available']}")
        
        if report['errors']:
            print(f"\n❌ 错误 ({len(report['errors'])}):")
            for i, error in enumerate(report['errors'], 1):
                print(f"  {i}. {error}")
        
        if report['warnings']:
            print(f"\n⚠️  警告 ({len(report['warnings'])}):")
            for i, warning in enumerate(report['warnings'], 1):
                print(f"  {i}. {warning}")
        
        if report['suggestions']:
            print(f"\n💡 建议 ({len(report['suggestions'])}):")
            for i, suggestion in enumerate(report['suggestions'], 1):
                print(f"  {i}. {suggestion}")
        
        print("=" * 80 + "\n")


if __name__ == "__main__":
    # 测试配置验证器
    print("=== 配置验证器测试 ===")
    
    from config.third_party_unified_config import ThirdPartyUnifiedConfig
    
    # 创建测试配置
    config = ThirdPartyUnifiedConfig.from_env()
    
    # 验证配置
    report = ConfigValidator.validate_and_report(config)
    ConfigValidator.print_report(report)

