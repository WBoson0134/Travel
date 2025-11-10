# AI API 测试指南

## 启动服务

```bash
./run_backend.sh
```

服务将在 `http://localhost:8000` 启动。

## 测试步骤

### 测试1：查看配置状态（设置页用）

```bash
curl -s http://localhost:8000/api/ai/providers | jq
```

或者使用Python格式化：

```bash
curl -s http://localhost:8000/api/ai/providers | python3 -m json.tool
```

**预期响应：**
```json
{
  "primary": "aliyun",
  "providers": [
    {"name": "aliyun", "configured": true},
    {"name": "openai", "configured": false},
    ...
  ]
}
```

### 测试2：对话（OpenAI兼容类 - 阿里云百炼）

```bash
curl -s http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aliyun",
    "model": "qwen2.5-7b-instruct",
    "messages": [
      {"role":"system","content":"You are TripApp assistant."},
      {"role":"user","content":"用一句话介绍你自己"}
    ]
  }' | jq
```

**预期响应：**
```json
{
  "provider": "openai_compat",
  "answer": "我是TripApp助手，可以帮助您规划旅行..."
}
```

### 测试3：对话（Dify原生）

```bash
curl -s http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "dify",
    "messages": [
      {"role":"system","content":"你是TripApp助手"},
      {"role":"user","content":"简要介绍一下京都两日游"}
    ]
  }' | jq
```

**预期响应：**
```json
{
  "provider": "dify",
  "answer": "京都两日游可以这样安排..."
}
```

## 快速测试脚本

使用提供的测试脚本：

```bash
./test_ai_api.sh
```

## 常见问题

### 问题1：返回 "No LLM providers configured"

**原因**：`.env` 文件中未配置API密钥

**解决方法**：
1. 在项目根目录创建或编辑 `.env` 文件
2. 添加以下配置：

```env
# 阿里云百炼配置
LLM_PRIMARY=aliyun
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=qwen2.5-7b-instruct

# 或Dify配置
DIFY_API_BASE=https://api.dify.ai/v1
DIFY_API_KEY=your_dify_api_key
DIFY_APP_USER=web-user
```

3. 重启后端服务

### 问题2：API调用失败，返回500错误

**可能原因**：
- API密钥无效
- BASE_URL路径错误
- 网络连接问题

**解决方法**：
1. 检查API密钥是否正确
2. 确认BASE_URL路径：
   - 阿里云百炼：`https://dashscope.aliyun.com/api/v1`
   - Dify：`https://api.dify.ai/v1`
3. 查看后端日志获取详细错误信息

### 问题3：OpenAI兼容接口返回404

**原因**：BASE_URL路径不正确

**解决方法**：
- 确保BASE_URL以 `/v1` 结尾
- 确保路径中存在 `/chat/completions` 路由
- 对于阿里云百炼，系统会自动处理特殊路径

### 问题4：服务无法启动

**可能原因**：
- 端口8000已被占用
- 依赖包未安装

**解决方法**：
```bash
# 检查端口占用
lsof -ti:8000

# 安装依赖
pip install -r requirements.txt

# 使用不同端口启动
uvicorn backend.app:app --host 0.0.0.0 --port 8001 --reload
```

## 验证配置

### 检查.env文件

```bash
# 查看.env文件（不显示敏感信息）
grep -E "^(OPENAI|DIFY|LLM)" .env | sed 's/=.*/=***/'
```

### 检查服务状态

```bash
# 检查服务是否运行
curl -s http://localhost:8000/api/ai/providers

# 检查健康状态（如果有健康检查端点）
curl -s http://localhost:8000/api/health
```

## 成功标志

如果看到以下响应，说明配置成功：

1. **配置状态**：`"configured": true` 出现在提供商列表中
2. **对话响应**：返回包含 `"answer"` 字段的JSON，且内容不为空
3. **无错误**：HTTP状态码为200，没有错误信息

## 下一步

配置成功后，可以：
1. 在前端设置页面查看配置状态
2. 使用AI助手进行对话
3. 测试不同的LLM提供商

