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
Markdown格式化工具
=================

用于将LLM输入输出格式化为Markdown格式，提高可读性。

作者: QSIR
版本: 1.0
"""

import json
import re
from typing import Optional


def format_as_markdown(
    content: str,
    content_type: str = "auto",
    max_length: int = 5000,
    title: Optional[str] = None,
) -> str:
    """
    将内容格式化为Markdown格式

    参数:
        content: 要格式化的内容
        content_type: 内容类型 ("auto", "json", "text", "markdown")
        max_length: 最大显示长度（超过会截断并显示提示）
        title: 可选的标题（会在Markdown中添加标题）

    返回:
        str: Markdown格式化的内容
    """
    if not content:
        return ""

    # 自动检测内容类型
    if content_type == "auto":
        content_stripped = content.strip()
        # 尝试检测JSON格式
        if (content_stripped.startswith("{") and content_stripped.endswith("}")) or (
            content_stripped.startswith("[") and content_stripped.endswith("]")
        ):
            try:
                json.loads(content_stripped)
                content_type = "json"
            except (json.JSONDecodeError, ValueError):
                # 检查是否包含JSON代码块
                if re.search(r"```(?:json)?\s*\{", content, re.DOTALL):
                    content_type = "json"
                else:
                    content_type = "text"
        else:
            content_type = "text"

    # 处理长内容
    original_length = len(content)
    is_truncated = False
    display_content = content

    if original_length > max_length:
        display_content = content[:max_length]
        is_truncated = True

    # 根据类型选择代码块语言
    if content_type == "json":
        lang = "json"
    elif content_type == "markdown":
        lang = "markdown"
    elif content_type == "text":
        lang = "text"
    else:
        lang = "text"

    # 构建Markdown代码块
    markdown_parts = []

    # 添加标题（如果有）
    if title:
        markdown_parts.append(f"## {title}\n")

    # 添加代码块
    markdown_parts.append(f"```{lang}\n{display_content}")

    # 添加截断提示
    if is_truncated:
        markdown_parts.append(
            f"\n\n... (内容过长，已截断，总长度: {original_length} 字符)"
        )

    markdown_parts.append("\n```")

    return "\n".join(markdown_parts)


def print_markdown(
    content: str,
    content_type: str = "auto",
    max_length: int = 5000,
    title: Optional[str] = None,
    separator: str = "=" * 80,
):
    """
    打印Markdown格式化的内容

    参数:
        content: 要格式化的内容
        content_type: 内容类型 ("auto", "json", "text", "markdown")
        max_length: 最大显示长度
        title: 可选的标题
        separator: 分隔符（默认80个等号）
    """
    if separator:
        print(f"\n{separator}")

    markdown = format_as_markdown(content, content_type, max_length, title)
    print(markdown)

    if separator:
        print(f"{separator}\n")
