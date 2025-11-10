# 404错误排查指南

## 错误信息

```
Client error '404 Not Found' for url 'https://api.openai.com/v1/chat/completions'
```

## 可能的原因

### 1. API密钥问题

您的API密钥格式是 `sk-proj-...`，这是OpenAI的**项目密钥**（Project API Key）。

**可能的问题：**
- 项目密钥可能需要特定的配置
- 密钥可能已过期或无效
- 密钥可能没有访问chat/completions端点的权限

### 2. 配额问题

从测试来看，您的账户可能遇到了配额限制：
- **429错误**：请求频率过高
- **insufficient_quota**：账户余额不足或配额已用完

### 3. API端点问题

虽然URL构建看起来正确，但可能：
- OpenAI API端点有变化
- 需要特定的请求头
- 模型名称不正确

## 解决方案

### 方案1：检查API密钥和账户状态

1. **访问OpenAI平台**：https://platform.openai.com/
2. **检查账户状态**：
   - 查看账户余额
   - 检查API使用配额
   - 确认密钥是否有效

3. **获取新的API密钥**：
   - 如果配额已用完，需要充值
   - 或者创建新的API密钥

### 方案2：使用其他AI服务

如果OpenAI有问题，可以切换到其他服务：

**选项A：阿里云百炼（推荐国内用户）**

1. 访问：https://dashscope.console.aliyun.com/
2. 获取API密钥
3. 更新.env文件：
```env
LLM_PRIMARY=aliyun
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1
OPENAI_API_KEY=你的阿里云API密钥
OPENAI_MODEL=qwen-turbo
```

**选项B：使用OpenRouter（OpenAI代理）**

1. 访问：https://openrouter.ai/
2. 获取API密钥
3. 更新.env文件：
```env
LLM_PRIMARY=openrouter
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=你的OpenRouter API密钥
OPENAI_MODEL=openai/gpt-3.5-turbo
```

### 方案3：检查错误详情

我已经更新了错误处理代码，现在会显示更详细的错误信息。重启后端服务后，错误信息会更清晰。

## 立即检查

运行以下命令检查API密钥状态：

```bash
curl -s -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer 你的API密钥" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}' \
  | python3 -m json.tool
```

**可能的响应：**
- `401` - API密钥无效
- `429` - 请求频率过高
- `insufficient_quota` - 配额不足
- `404` - 端点不存在（较少见）

## 下一步

1. **检查OpenAI账户**：确认余额和配额
2. **等待一段时间**：如果是429错误，等待几分钟后重试
3. **考虑切换服务**：如果OpenAI持续有问题，可以尝试其他AI服务

## 临时解决方案

如果急需使用，可以：
1. 使用阿里云百炼（国内用户推荐）
2. 或者等待OpenAI配额恢复
3. 或者检查是否有其他可用的API密钥

