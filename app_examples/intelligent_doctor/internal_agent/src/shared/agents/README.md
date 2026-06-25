# 智能体模块说明

## 概述

这个目录包含了重构后的智能体模块，按照功能进行了清晰的分离和模块化设计。

## 目录结构

```
agents/
├── __init__.py
├── base_agent.py              # 基础智能体类
├── coordinator/               # 协调器智能体
│   ├── __init__.py
│   └── cybertwin_agent.py     # 数字孪生智能体
├── medical/                   # 医疗智能体
│   ├── __init__.py
│   ├── internal_medicine.py   # 内科智能体
│   ├── surgical.py            # 外科智能体
│   ├── history.py             # 病史智能体
│   ├── summary.py             # 总结智能体
│   ├── triage.py              # 分诊智能体
│   └── comprehensive.py       # 综合智能体
├── image/                     # 影像分析智能体
│   ├── __init__.py
│   ├── coordinator.py         # 影像分析协调器
│   ├── general.py             # 通用影像分析
│   ├── local.py               # 本地影像分析
│   └── distributed.py         # 分布式影像分析
└── README.md                  # 本文件
```

## 主要特性

### 1. 模块化设计
- 每个智能体都有独立的文件
- 清晰的职责分离
- 易于维护和扩展

### 2. 统一接口
- 所有智能体都继承自 `BaseAgent`
- 统一的 `execute` 方法接口
- 标准化的错误处理

### 3. 配置管理
- 支持灵活的配置选项
- 可配置的模型参数
- 可开关的功能模块

### 4. 日志记录
- 完整的日志记录
- 分级日志输出
- 便于调试和监控

## 使用方法

### 1. 基础使用

```python
from agents.coordinator.cybertwin_agent import CybertwinAgent, CybertwinConfig

# 创建配置
config = CybertwinConfig(
    model_config={
        "provider": "qwen",
        "api_key": "your-api-key",
        "model": "qwen-turbo"
    },
    enable_auth=True,
    enable_audit=True
)

# 初始化智能体
agent = CybertwinAgent(config)

# 执行任务
result = await agent.execute(
    user_input="我最近经常头痛",
    user_id="user_001",
    user_info={"role": "patient"}
)
```

### 2. 医疗智能体使用

```python
from agents.medical.internal_medicine import InternalMedicineAgent

# 初始化内科智能体
agent = InternalMedicineAgent(model_config)

# 执行内科诊断
result = await agent.execute(
    user_input="我最近经常头痛，有时候还会恶心",
    user_id="user_001",
    user_info={"age": 35, "gender": "male"}
)
```

### 3. 影像分析智能体使用

```python
from agents.image.coordinator import ImageAnalysisCoordinator

# 初始化影像分析协调器
coordinator = ImageAnalysisCoordinator(model_config)

# 执行影像分析
result = await coordinator.analyze_images(
    user_id="user_001",
    user_input="请帮我分析一下这张X光片"
)
```

## 配置选项

### CybertwinConfig

```python
@dataclass
class CybertwinConfig:
    model_config: Dict[str, Any]      # 模型配置
    enable_auth: bool = True          # 启用认证
    enable_audit: bool = True         # 启用审计
    max_context_length: int = 4000    # 最大上下文长度
    intent_threshold: float = 0.7     # 意图识别阈值
```

### 模型配置

```python
model_config = {
    "provider": "qwen",               # 模型提供商
    "api_key": "your-api-key",        # API密钥
    "model": "qwen-turbo",            # 模型名称
    "temperature": 0.7,               # 温度参数
    "max_tokens": 2000                # 最大令牌数
}
```

## 错误处理

所有智能体都包含完整的错误处理机制：

```python
try:
    result = await agent.execute(user_input, user_id, user_info)
except Exception as e:
    logging.error(f"智能体执行失败: {str(e)}")
    result = f"⚠️ 执行错误：{str(e)}"
```

## 日志记录

每个智能体都有独立的日志记录器：

```python
# 获取智能体日志
logger = logging.getLogger(agent.__class__.__name__)
logger.info("智能体执行完成")
logger.error("执行失败")
```

## 扩展指南

### 添加新的智能体

1. 在相应的目录下创建新的智能体文件
2. 继承 `BaseAgent` 类
3. 实现 `execute` 方法
4. 在 `__init__.py` 中导出新智能体

### 添加新的功能

1. 在 `BaseAgent` 中添加通用功能
2. 在具体智能体中实现特定功能
3. 更新配置选项
4. 添加相应的测试

## 测试

运行测试示例：

```bash
python cybertwin_agent_example.py
```

## 注意事项

1. 确保所有依赖模块都已正确安装
2. 配置正确的模型API密钥
3. 根据实际需求调整配置参数
4. 定期检查日志输出
5. 保持代码的向后兼容性

## 故障排除

### 常见问题

1. **导入错误**: 检查Python路径和模块结构
2. **配置错误**: 验证模型配置参数
3. **权限错误**: 检查认证授权设置
4. **内存错误**: 调整上下文长度限制

### 调试技巧

1. 启用详细日志记录
2. 使用断点调试
3. 检查智能体状态
4. 验证输入参数

## 更新日志

- v1.0: 初始版本，包含基础智能体模块
- 后续版本将根据需求持续更新

## 贡献指南

1. 遵循现有的代码风格
2. 添加适当的注释和文档
3. 编写单元测试
4. 更新相关文档
