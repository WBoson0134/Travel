# AI配置指南

本指南将帮助您在网站中配置AI服务。

## 快速开始

### 1. 访问设置页面

在网站导航栏中点击 **"设置"** 按钮，即可查看当前的AI配置状态。

### 2. 配置AI服务

AI配置需要在服务器端的 `.env` 文件中进行。设置页面会显示哪些服务已配置，哪些未配置。

## 详细配置步骤

### 方法一：通过设置页面查看

1. 访问网站设置页面（点击导航栏的"设置"按钮）
2. 查看"AI服务配置"部分
3. 绿色"已配置"表示该服务已正确配置
4. 红色"未配置"表示需要配置

### 方法二：手动配置

#### 步骤1：创建或编辑 .env 文件

在项目根目录（`/Users/zhiruiwang/Desktop/Project/travel/`）创建或编辑 `.env` 文件。

#### 步骤2：添加AI配置

根据您要使用的AI服务，添加相应的配置：

**选项A：使用阿里云百炼（推荐）**

```env
# 阿里云百炼 API 配置
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1
```

**选项B：使用Dify**

```env
# Dify API 配置
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxxx
DIFY_API_BASE=https://api.dify.ai/v1
```

**选项C：同时配置多个服务**

```env
# 阿里云百炼（主要）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1

# Dify（备用）
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxxx
DIFY_API_BASE=https://api.dify.ai/v1
```

#### 步骤3：获取API密钥

**阿里云百炼：**
1. 访问 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录账户
3. 创建应用并获取 API Key
4. 将 API Key 复制到 `.env` 文件

**Dify：**
1. 访问 [Dify 平台](https://dify.ai/)
2. 注册/登录账户
3. 创建应用并获取 API Key
4. 将 API Key 复制到 `.env` 文件

#### 步骤4：重启后端服务

配置完成后，需要重启后端服务：

```bash
# 停止当前运行的后端服务（Ctrl+C）
# 然后重新启动
bash run_backend.sh
```

#### 步骤5：验证配置

1. 访问设置页面
2. 检查"AI服务配置"部分应该显示"已配置"
3. 访问AI助手页面，尝试发送一条消息
4. 如果收到AI回复，说明配置成功

## 配置示例

### 完整的 .env 文件示例

```env
# Flask 配置
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///travel.db

# AI API 配置（至少配置一个）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1

# Dify API 配置（可选）
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxxx
DIFY_API_BASE=https://api.dify.ai/v1

# 外部旅游API配置（可选）
BOOKING_API_KEY=your_booking_api_key
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_api_secret
TRIPADVISOR_API_KEY=your_tripadvisor_api_key

# 地图API配置（可选）
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## 故障排除

### 问题1：设置页面显示"未配置"

**可能原因：**
- `.env` 文件不存在或位置不正确
- API密钥格式错误
- 后端服务未重启

**解决方法：**
1. 确认 `.env` 文件在项目根目录
2. 检查API密钥是否正确（没有多余的空格或引号）
3. 重启后端服务

### 问题2：AI助手无法回复

**可能原因：**
- API密钥无效或过期
- 网络连接问题
- API服务不可用

**解决方法：**
1. 在设置页面检查配置状态
2. 验证API密钥是否有效
3. 检查网络连接
4. 查看后端日志中的错误信息

### 问题3：配置后仍然显示"未配置"

**可能原因：**
- 后端服务未读取到新的配置
- `.env` 文件格式错误

**解决方法：**
1. 确认 `.env` 文件格式正确（每行一个配置项）
2. 重启后端服务
3. 检查后端启动日志，确认是否加载了 `.env` 文件

## 安全提示

1. **不要提交 .env 文件到Git**
   - `.env` 文件通常已在 `.gitignore` 中
   - 确保不会意外提交敏感信息

2. **保护API密钥**
   - 不要在前端代码中硬编码API密钥
   - 不要将API密钥分享给他人

3. **使用环境变量**
   - 生产环境建议使用环境变量而不是文件
   - 使用密钥管理服务（如AWS Secrets Manager）

## 下一步

配置完成后，您可以：
- 使用AI助手进行对话
- 生成智能行程
- 获取个性化推荐

如有问题，请查看 `API_INTEGRATION.md` 获取更多信息。

