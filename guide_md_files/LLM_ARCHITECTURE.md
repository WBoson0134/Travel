# LLM服务架构说明

## 概述

新的LLM服务架构提供了统一的接口来支持多种LLM提供商，包括：
- 阿里云百炼（DashScope）
- OpenAI（标准接口）
- Dify
- OpenRouter
- Ollama
- 其他OpenAI兼容的服务

## 目录结构

```
backend/
  settings.py                     # LLM配置（从.env读取）
  services/
    llm/
      __init__.py                 # 模块导出
      base.py                     # 抽象基类
      openai_compat.py            # OpenAI兼容适配器
      dify.py                     # Dify原生适配器
      factory.py                  # 工厂模式创建客户端
```

## 配置

在 `.env` 文件中配置：

```env
# 主要LLM提供商（aliyun, openai, dify等）
LLM_PRIMARY=aliyun

# OpenAI兼容接口（包括阿里云百炼）
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Dify原生接口
DIFY_API_BASE=https://api.dify.ai/v1
DIFY_API_KEY=your_dify_api_key
DIFY_APP_USER=web-user
```

## 使用方法

### 基本使用

```python
from backend.services.llm import pick_client

# 自动选择配置的LLM提供商
client = pick_client()

# 发送消息
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"}
]

reply = await client.chat(messages)
```

### 指定提供商

```python
from backend.services.llm import pick_client

# 指定使用某个提供商
client = pick_client(prefer="aliyun")  # 或 "dify", "openai" 等
```

### 查看所有可用的客户端

```python
from backend.services.llm import build_clients

clients = build_clients()
for name, client in clients.items():
    print(f"{name}: {client.name}")
```

## 架构优势

1. **统一接口**：所有LLM提供商使用相同的接口
2. **易于扩展**：添加新的提供商只需实现`LLMClient`接口
3. **灵活配置**：通过环境变量轻松切换提供商
4. **自动回退**：如果首选提供商不可用，自动选择其他可用提供商

## 适配器说明

### OpenAICompat

支持所有OpenAI兼容的接口，包括：
- 阿里云百炼（DashScope）
- OpenAI官方API
- OpenRouter
- Ollama
- 其他兼容服务

自动检测API路径并处理不同的响应格式。

### DifyClient

专门为Dify平台设计的客户端，使用Dify的原生API接口。

## 集成到现有服务

AI助手服务已经更新为使用新的LLM架构：

```python
from backend.services.llm import pick_client

class AIAssistantService:
    def __init__(self):
        self.llm_client = pick_client()
    
    def chat(self, user_id, message, context=None):
        messages = self._build_messages(user_id, system_prompt)
        reply = asyncio.run(self.llm_client.chat(messages))
        return {"reply": reply}
```

## 注意事项

1. **异步函数**：LLM客户端的`chat`方法是异步的，需要使用`asyncio.run()`或`await`
2. **错误处理**：如果所有提供商都不可用，`pick_client()`会抛出`RuntimeError`
3. **消息格式**：所有消息必须遵循`{"role": "user|assistant|system", "content": "..."}`格式

## 故障排除

### 问题1：找不到LLM提供商

**原因**：`.env`文件中未配置任何LLM提供商

**解决**：至少配置一个LLM提供商的API密钥

### 问题2：异步调用错误

**原因**：在同步函数中直接调用异步方法

**解决**：使用`asyncio.run()`包装异步调用

### 问题3：API调用失败

**原因**：API密钥无效或网络问题

**解决**：检查API密钥和网络连接，查看后端日志

