# AI助手快速使用指南

## ✅ 安装状态检查

### 1. 检查后端服务

```bash
# 检查服务是否运行
lsof -ti:8000 && echo "✅ 后端服务正在运行" || echo "❌ 后端服务未运行"
```

如果未运行，启动服务：
```bash
bash run_backend.sh
```

### 2. 检查前端服务

```bash
# 检查服务是否运行
lsof -ti:3000 && echo "✅ 前端服务正在运行" || echo "❌ 前端服务未运行"
```

如果未运行，启动服务：
```bash
bash run_frontend.sh
```

### 3. 检查API配置

```bash
# 检查.env文件是否存在
test -f .env && echo "✅ 找到.env文件" || echo "❌ 未找到.env文件"
```

## 🚀 使用步骤

### 第一步：配置API密钥（如果还没配置）

1. 在项目根目录创建或编辑 `.env` 文件
2. 添加以下配置：

```env
# 阿里云百炼配置（推荐）
LLM_PRIMARY=aliyun
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1
OPENAI_API_KEY=你的API密钥
OPENAI_MODEL=qwen2.5-7b-instruct
```

3. 重启后端服务：
```bash
# 停止当前服务（Ctrl+C）
# 然后重新启动
bash run_backend.sh
```

### 第二步：启动服务

**终端1 - 启动后端：**
```bash
cd /Users/zhiruiwang/Desktop/Project/travel
bash run_backend.sh
```

**终端2 - 启动前端：**
```bash
cd /Users/zhiruiwang/Desktop/Project/travel
bash run_frontend.sh
```

### 第三步：访问网站

1. 打开浏览器访问：`http://localhost:3000`
2. 点击导航栏的 **"AI助手"** 按钮
3. 开始与AI助手对话！

## 📱 如何使用AI助手

### 方式1：通过网页界面

1. **访问AI助手页面**
   - 打开 `http://localhost:3000`
   - 点击导航栏的 **"AI助手"** 按钮

2. **开始对话**
   - 在输入框中输入您的问题
   - 点击 **"发送"** 按钮或按 **Enter** 键
   - AI助手会立即回复

3. **使用快速操作**
   - AI助手回复后会提供快速操作建议
   - 点击这些建议可以快速发送相关查询

### 方式2：通过设置页面查看配置

1. **访问设置页面**
   - 点击导航栏的 **"设置"** 按钮
   - 查看AI提供商配置状态

2. **检查配置**
   - 绿色"已配置"标签 = API密钥已正确配置
   - 红色"未配置"标签 = 需要配置API密钥

## 💬 使用示例

### 示例1：规划行程
```
你：我想去北京旅游3天，有什么推荐吗？
AI：北京是一个充满历史文化的城市，我推荐您...
```

### 示例2：推荐景点
```
你：上海有什么好玩的景点？
AI：上海有很多值得游览的景点，比如外滩、东方明珠...
```

### 示例3：搜索酒店
```
你：帮我搜索北京的酒店
AI：我可以帮您搜索酒店信息。请告诉我您的入住日期...
```

## 🔧 故障排除

### 问题1：AI助手无法回复

**可能原因：**
- API密钥未配置或无效
- 后端服务未启动
- 网络连接问题

**解决方法：**
1. 检查设置页面，确认API密钥已配置
2. 确认后端服务正在运行（端口8000）
3. 查看浏览器控制台的错误信息

### 问题2：设置页面显示"未配置"

**解决方法：**
1. 在 `.env` 文件中添加API密钥
2. 重启后端服务
3. 刷新设置页面

### 问题3：页面无法访问

**解决方法：**
1. 确认前端服务正在运行（端口3000）
2. 确认后端服务正在运行（端口8000）
3. 检查浏览器控制台的错误信息

## ✅ 验证安装

运行以下命令验证一切正常：

```bash
# 1. 检查后端服务
curl -s http://localhost:8000/api/ai/providers | python3 -m json.tool

# 2. 测试对话（需要配置API密钥）
curl -s http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"provider": "aliyun", "messages": [{"role":"user","content":"你好"}]}' \
  | python3 -m json.tool
```

## 🎉 完成！

如果一切正常，您现在可以：
- ✅ 在网页上使用AI助手
- ✅ 查看AI配置状态
- ✅ 与AI助手进行对话
- ✅ 获取旅游建议和推荐

享受使用AI助手吧！

