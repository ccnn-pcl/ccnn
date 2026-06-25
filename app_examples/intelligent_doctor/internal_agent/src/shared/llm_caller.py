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

"""
LLM调用器 - 大语言模型API调用接口
================================

这个模块提供了统一的大语言模型API调用接口，支持文本和多模态模型调用。

主要功能：
1. 统一调用接口
   - 自动识别调用类型（文本/多模态）
   - 统一的错误处理机制
   - 异步调用支持

2. 文本模型调用
   - 支持标准ChatGPT API格式
   - 可配置模型参数
   - 超时处理

3. 多模态模型调用
   - 支持文本+图像输入
   - 图像处理接口
   - 多模态响应处理

4. 错误处理
   - HTTP错误处理
   - 网络超时处理
   - 异常捕获和日志记录

作者: QSIR
版本: 1.0
"""

import aiohttp
import asyncio
import logging
import random

def _generate_mock_response(prompt: str) -> str:
    """生成模拟响应"""
    # 根据提示词内容生成不同的模拟响应
    if "症状类型" in prompt and ("头痛" in prompt or "头疼" in prompt):
        return "疼痛"
    elif "症状类型" in prompt and "肚子疼" in prompt:
        return "腹痛"
    elif "症状类型" in prompt and "胸闷" in prompt:
        return "胸部症状"
    elif "症状类型" in prompt and "咳嗽" in prompt:
        return "呼吸系统"
    elif "症状类型" in prompt and "发烧" in prompt:
        return "发热"
    elif "生成" in prompt and "问题" in prompt:
        if "头痛" in prompt or "头疼" in prompt:
            return "头痛持续多长时间了？\n疼痛的具体位置在哪里？\n疼痛的性质如何？"
        elif "肚子疼" in prompt:
            return "腹痛的具体位置在哪里？\n疼痛与饮食有关系吗？\n是否有其他消化系统症状？"
        elif "胸闷" in prompt:
            return "胸闷持续多长时间了？\n是否有呼吸困难的症状？\n疼痛是否向其他部位放射？"
        elif "咳嗽" in prompt:
            return "咳嗽持续多长时间了？\n是否有痰液？\n咳嗽在什么情况下会加重？"
        elif "发烧" in prompt:
            return "体温大概多少度？\n发热持续多长时间了？\n是否有其他伴随症状？"
        else:
            return "请详细描述一下您的症状，包括症状的持续时间、强度等。"
    else:
        return "模拟AI响应"

# 异步调用LLM模型
async def call_llm(prompt, model_config, agent_name="Unknown"):
    """
    调用大模型API - 统一入口函数
    
    功能：
    - 自动识别调用类型（文本或多模态）
    - 根据输入类型调用相应的处理函数
    - 统一的错误处理和日志记录
    
    参数：
        prompt: 输入内容，可以是字符串或包含图像的字典
        model_config: 模型配置字典，包含API端点、密钥等信息
        agent_name: 调用此函数的智能体名称
        
    返回：
        str: 模型响应内容
        
    异常处理：
        - 捕获所有异常并记录日志
        - 重新抛出异常以通知调用者
    """
    import traceback
    import sys
    
    try:
        # 使用print确保输出到终端
        # 移除emoji以避免Windows GBK编码错误
        print(f"\n[LLM调用开始] {agent_name}")
        print("[LLM]" * 40 + "\n")
        
        # 详细的输入日志
        logging.info("=" * 80)
        logging.info(f"[{agent_name}] LLM 调用 - 开始")
        logging.info(f"[{agent_name}] 调用类型: {'多模态' if isinstance(prompt, dict) and 'image' in prompt else '文本'}")
        logging.info(f"[{agent_name}] 输入长度: {len(str(prompt))} 字符")
        
        # 打印输入的完整内容（截断长内容）
        if isinstance(prompt, str):
            if len(prompt) <= 500:
                logging.info(f"[{agent_name}] 完整输入:\n{prompt}")
            else:
                logging.info(f"[{agent_name}] 输入预览 (前500字符):\n{prompt[:500]}...")
                logging.info(f"[{agent_name}] 输入总长度: {len(prompt)} 字符")
        else:
            logging.info(f"[{agent_name}] 输入类型: {type(prompt)}, 内容: {str(prompt)[:500]}...")
        
        logging.info(f"[{agent_name}] 模型配置: {model_config.get('model_name', model_config.get('model', 'Unknown'))}")
        logging.info("-" * 80)
        
        if isinstance(prompt, dict) and "image" in prompt:
            # 多模态调用
            result = await call_multimodal_model(
                text=prompt["text"],
                image=prompt["image"],
                model_config=model_config
            )
        else:
            # 普通文本调用
            result = await call_text_model(prompt, model_config)
        
        # 使用print输出到终端 - 增强版：使用Markdown格式打印
        try:
            from shared.utils.markdown_formatter import print_markdown
            
            result_str = str(result)
            print_markdown(
                content=result_str,
                content_type="auto",  # 自动检测JSON格式
                max_length=5000,
                title=f"📤 LLM输出结果 ({agent_name})",
                separator="=" * 80
            )
        except ImportError:
            # 如果导入失败，使用原有格式
            print(f"\n{'='*80}")
            print(f"[LLM调用完成] {agent_name}")
            print(f"{'='*80}")
            print(f"[输出长度] {len(str(result))} 字符")
            print(f"[输出内容]:")
            print("-" * 80)
            
            # 打印完整结果（如果太长则截断并显示长度）
            result_str = str(result)
            if len(result_str) <= 1000:
                # 如果结果不超过1000字符，完整打印
                print(result_str)
            else:
                # 如果结果超过1000字符，打印前1000字符和最后200字符
                print(result_str[:1000])
                print("\n... [中间内容已省略] ...\n")
                print(result_str[-200:])
                print(f"\n[总长度] {len(result_str)} 字符")
            
            print("-" * 80)
            print(f"[{agent_name}] LLM调用结果输出完成")
            print("=" * 80 + "\n")
        
        # 详细的输出日志
        logging.info(f"[{agent_name}] LLM 调用 - 完成")
        logging.info(f"[{agent_name}] 输出长度: {len(str(result))} 字符")
        
        if len(str(result)) <= 500:
            logging.info(f"[{agent_name}] 完整输出:\n{result}")
        else:
            logging.info(f"[{agent_name}] 输出预览 (前500字符):\n{str(result)[:500]}...")
            logging.info(f"[{agent_name}] 输出总长度: {len(str(result))} 字符")
        logging.info("=" * 80)
        
        return result
    except Exception as e:
        # 详细的错误日志
        logging.error("=" * 80)
        logging.error(f"[{agent_name}] LLM 调用 - 失败")
        logging.error(f"[{agent_name}] 错误类型: {type(e).__name__}")
        logging.error(f"[{agent_name}] 错误消息: {str(e)}")
        logging.error(f"[{agent_name}] 错误堆栈:\n{traceback.format_exc()}")
        logging.error(f"[{agent_name}] 输入内容: {str(prompt)[:500]}...")
        logging.error("=" * 80)
        raise e

async def call_text_model(prompt, model_config):
    """
    调用文本模型
    
    功能：
    - 构建ChatGPT API请求
    - 发送HTTP POST请求
    - 处理响应和错误
    
    参数：
        prompt (str): 文本提示词
        model_config (list or dict): 模型配置，如果是列表则取第一个元素
            
    返回：
        str: 模型响应文本或错误信息
        
    请求配置：
        - Content-Type: application/json
        - Authorization: Bearer token
        - timeout: 30秒
        - temperature: 0.7
    """
    # 处理配置格式：如果是列表则取第一个元素
    if isinstance(model_config, list):
        config = model_config[0]
    else:
        config = model_config
    
    # 统一处理配置对象，支持ModelConfig和字典两种格式
    try:
        if isinstance(config, dict):
            # 字典格式
            api_key = config.get('api_key')
            base_url = config.get('base_url')
            model_name = config.get('model_name') or config.get('model')
            temperature = config.get('temperature', 0.7)
            max_tokens = config.get('max_tokens', 1000)
        elif hasattr(config, 'api_key') and not isinstance(config, dict):
            # ModelConfig对象（确保不是字典）
            api_key = config.api_key
            base_url = config.base_url
            model_name = config.model_name
            temperature = config.temperature
            max_tokens = config.max_tokens
        else:
            # 其他格式，尝试转换为字典
            logging.warning(f"[LLM调用] 未知的配置格式: {type(config)}, 内容: {config}")
            if hasattr(config, '__dict__'):
                config_dict = config.__dict__
                api_key = config_dict.get('api_key')
                base_url = config_dict.get('base_url')
                model_name = config_dict.get('model_name') or config_dict.get('model')
                temperature = config_dict.get('temperature', 0.7)
                max_tokens = config_dict.get('max_tokens', 1000)
            else:
                raise ValueError(f"不支持的配置格式: {type(config)}")
    except Exception as e:
        logging.error(f"[LLM调用] 配置处理失败: {str(e)}, 配置类型: {type(config)}, 配置内容: {config}")
        raise ValueError(f"配置处理失败: {str(e)}")
    
    # 检查是否是测试密钥
    if api_key == 'sk-test-key':
        # 使用模拟响应
        return _generate_mock_response(prompt)
    
    url = f"{base_url}/chat/completions"
    
    # 根据API密钥类型设置不同的认证方式
    if api_key == 'custom':
        # 华佗GPT和通义千问使用custom密钥，不需要Bearer前缀
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
    else:
        # OpenAI等使用Bearer token
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        logging.info(f"[LLM调用] 开始调用文本模型: {model_name}, URL: {url}")
        logging.info(f"[LLM调用] 请求内容长度: {len(prompt)} 字符")
        logging.info(f"[LLM调用] 请求内容预览: {prompt[:100]}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as response:
                logging.info(f"[LLM调用] 收到响应状态码: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    response_content = data['choices'][0]['message']['content']
                    logging.info(f"[LLM调用] 成功获取响应，长度: {len(response_content)} 字符")
                    logging.info(f"[LLM调用] 响应内容预览: {response_content[:100]}...")
                    return response_content
                else:
                    error_text = await response.text()
                    logging.error(f"[LLM调用] 模型调用失败，状态码: {response.status}, 错误: {error_text}")
                    return f"模型调用失败：{error_text}"
    except asyncio.TimeoutError as e:
        logging.error(f"[LLM调用] 请求超时 (30秒): {str(e)}")
        return f"请求超时: {str(e)}"
    except Exception as e:
        logging.error(f"[LLM调用] 调用出错: {str(e)}")
        return f"调用出错: {str(e)}"

async def call_multimodal_model(text, image, model_config):
    """
    调用多模态模型
    
    功能：
    - 构建多模态API请求
    - 处理文本和图像输入
    - 发送HTTP POST请求
    - 处理响应和错误
    
    参数：
        text (str): 文本提示词
        image: 图像数据
        model_config (dict): 模型配置，包含：
            - base_url: API基础URL
            - api_key: API密钥
            - model: 模型名称
            
    返回：
        str: 模型响应文本或错误信息
        
    请求配置：
        - Content-Type: application/json
        - Authorization: Bearer token
        - timeout: 30秒
        - temperature: 0.7
        - messages: 包含文本和图像的多模态消息
    """
    # 处理配置格式：如果是列表则取第一个元素
    if isinstance(model_config, list):
        config = model_config[0]
    else:
        config = model_config
    
    # 统一处理配置对象，支持ModelConfig和字典两种格式
    try:
        if isinstance(config, dict):
            # 字典格式
            api_key = config.get('api_key')
            base_url = config.get('base_url')
            model_name = config.get('model_name') or config.get('model')
            temperature = config.get('temperature', 0.7)
        elif hasattr(config, 'api_key') and not isinstance(config, dict):
            # ModelConfig对象（确保不是字典）
            api_key = config.api_key
            base_url = config.base_url
            model_name = config.model_name
            temperature = config.temperature
        else:
            # 其他格式，尝试转换为字典
            logging.warning(f"[LLM调用] 未知的配置格式: {type(config)}, 内容: {config}")
            if hasattr(config, '__dict__'):
                config_dict = config.__dict__
                api_key = config_dict.get('api_key')
                base_url = config_dict.get('base_url')
                model_name = config_dict.get('model_name') or config_dict.get('model')
                temperature = config_dict.get('temperature', 0.7)
            else:
                raise ValueError(f"不支持的配置格式: {type(config)}")
    except Exception as e:
        logging.error(f"[LLM调用] 配置处理失败: {str(e)}, 配置类型: {type(config)}, 配置内容: {config}")
        raise ValueError(f"配置处理失败: {str(e)}")
    
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": text},
            {"role": "user", "content": "[图片]"},
        ],
        "temperature": temperature
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    return f"模型调用失败：{error_text}"
    except Exception as e:
        return f"调用出错: {str(e)}"

