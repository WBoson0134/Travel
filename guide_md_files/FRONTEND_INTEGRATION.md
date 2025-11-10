# 前端集成说明

## 更新内容

前端已更新以接入新的FastAPI后端：

### 1. 设置页面 (`Settings.jsx`)

**更新内容：**
- 使用新的 `/api/ai/providers` 端点获取AI提供商状态
- 动态显示所有支持的AI提供商（aliyun, openai, openrouter, ollama, dify）
- 显示每个提供商的配置状态（已配置/未配置）
- 标记默认提供商

**关键代码：**
```javascript
// 加载配置状态
const res = await fetch('/api/ai/providers').then(r => r.json());

// 渲染状态标签
{aiProviders?.providers?.map((provider) => (
  <StatusChip configured={provider.configured} />
))}
```

### 2. AI助手页面 (`AIAssistant.jsx`)

**更新内容：**
- 使用新的 `/api/ai/chat` 端点进行对话
- 支持OpenAI格式的消息数组
- 自动构建消息历史（包含系统消息）
- 从响应中提取 `answer` 字段

**关键代码：**
```javascript
const payload = {
  provider: 'aliyun', // 或用户在设置里选择的默认
  model: 'qwen2.5-7b-instruct',
  messages: [
    { role: 'system', content: 'You are TripApp assistant.' },
    { role: 'user', content: '请按我偏好推荐大阪1日游' }
  ]
};

const res = await fetch('/api/ai/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(payload)
}).then(r => r.json());

// res.answer 即展示内容
```

### 3. 代理配置 (`vite.config.js`)

**更新内容：**
- 代理目标从 `localhost:5001` 更新为 `localhost:8000`

## 使用方式

### 启动服务

1. **启动后端（FastAPI）**：
```bash
bash run_backend.sh
# 服务运行在 http://localhost:8000
```

2. **启动前端**：
```bash
bash run_frontend.sh
# 前端运行在 http://localhost:3000
```

### 测试功能

1. **访问设置页面**：
   - 打开 `http://localhost:3000/settings`
   - 查看AI提供商配置状态
   - 应该看到所有提供商的"已配置/未配置"状态

2. **访问AI助手**：
   - 打开 `http://localhost:3000/ai-assistant`
   - 发送消息测试对话功能
   - 应该能收到AI回复

## API接口对比

### 旧接口（Flask）
- `POST /api/ai/chat` - 需要 `user_id`, `message`, `context`
- `GET /api/ai/history/<user_id>` - 获取对话历史
- `DELETE /api/ai/history/<user_id>` - 清除对话历史

### 新接口（FastAPI）
- `GET /api/ai/providers` - 获取AI提供商状态
- `POST /api/ai/chat` - 统一对话接口，使用OpenAI格式消息

## 注意事项

1. **对话历史**：新接口不包含对话历史功能，历史由前端本地管理
2. **消息格式**：必须使用OpenAI格式的消息数组
3. **错误处理**：FastAPI返回的错误在 `detail` 字段中
4. **端口配置**：确保后端运行在8000端口，前端代理配置正确

## 配置要求

在 `.env` 文件中配置API密钥后，设置页面会显示"已配置"状态：

```env
LLM_PRIMARY=aliyun
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=qwen2.5-7b-instruct
```

## 故障排除

### 问题1：设置页面显示所有提供商未配置

**原因**：`.env` 文件中未配置API密钥

**解决**：在 `.env` 文件中添加API密钥配置

### 问题2：AI助手无法发送消息

**原因**：后端服务未启动或端口不匹配

**解决**：
1. 确认后端服务运行在8000端口
2. 检查 `vite.config.js` 中的代理配置
3. 查看浏览器控制台的错误信息

### 问题3：收到 "No LLM providers configured" 错误

**原因**：API密钥配置错误或无效

**解决**：
1. 检查 `.env` 文件中的配置
2. 确认API密钥有效
3. 重启后端服务

