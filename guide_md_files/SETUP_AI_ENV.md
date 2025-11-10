# AI助手环境配置指南

## 当前状态

✅ **后端服务已运行**（端口8000）  
❌ **前端服务未运行**（需要启动）  
❌ **API密钥未配置**（需要创建.env文件）

## 快速开始（3步）

### 步骤1：启动前端服务

打开新的终端窗口，运行：

```bash
cd /Users/zhiruiwang/Desktop/Project/travel
bash run_frontend.sh
```

或者：

```bash
cd /Users/zhiruiwang/Desktop/Project/travel/frontend
npm run dev
```

前端服务将在 `http://localhost:3000` 启动。

### 步骤2：配置API密钥（可选，但推荐）

创建 `.env` 文件并添加API密钥：

```bash
cd /Users/zhiruiwang/Desktop/Project/travel
cat > .env << 'EOF'
# AI配置
LLM_PRIMARY=aliyun
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1
OPENAI_API_KEY=你的API密钥
OPENAI_MODEL=qwen2.5-7b-instruct
EOF
```

**获取API密钥：**
1. 访问 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录账户
3. 创建应用并获取 API Key
4. 将 API Key 填入 `.env` 文件

配置完成后，重启后端服务：
```bash
# 停止当前后端服务（Ctrl+C）
# 然后重新启动
bash run_backend.sh
```

### 步骤3：访问网站

1. 打开浏览器访问：`http://localhost:3000`
2. 点击导航栏的 **"AI助手"** 按钮
3. 开始使用！

## 使用方式

### 方式1：使用AI助手（需要配置API密钥）

1. 访问 `http://localhost:3000/ai-assistant`
2. 在输入框中输入问题
3. 点击"发送"或按Enter
4. 查看AI回复

### 方式2：查看配置状态（无需API密钥）

1. 访问 `http://localhost:3000/settings`
2. 查看AI提供商配置状态
3. 绿色=已配置，红色=未配置

## 注意事项

- **不配置API密钥也可以访问页面**，但无法进行对话
- **配置API密钥后**，AI助手才能正常工作
- **前端和后端都需要运行**才能使用完整功能

## 验证

运行以下命令验证：

```bash
# 检查后端
curl -s http://localhost:8000/api/ai/providers

# 检查前端（在浏览器中打开）
open http://localhost:3000
```

## 完成！

现在您可以：
- ✅ 访问网站界面
- ✅ 查看AI配置状态
- ⚠️ 配置API密钥后可以使用AI对话功能

