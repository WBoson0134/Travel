# FastAPI迁移说明

## 概述

项目现在支持FastAPI和Flask两种框架：

- **FastAPI** (`backend/app.py`) - 新的AI路由和现代化API
- **Flask** (`backend/app_flask.py`) - 保留原有的所有路由

## 新的FastAPI路由

### 1. 查看AI提供商状态

**GET** `/api/ai/providers`

返回已配置的AI提供商列表。

**响应示例：**
```json
{
  "primary": "aliyun",
  "providers": [
    {"name": "aliyun", "configured": true},
    {"name": "openai", "configured": false},
    {"name": "dify", "configured": false}
  ]
}
```

### 2. 统一AI对话接口

**POST** `/api/ai/chat`

统一的AI对话接口，支持多种LLM提供商。

**请求体：**
```json
{
  "messages": [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"}
  ],
  "provider": "aliyun",
  "model": "qwen-turbo",
  "temperature": 0.7
}
```

**响应：**
```json
{
  "provider": "openai_compat",
  "answer": "你好！有什么我可以帮助你的吗？"
}
```

## 运行方式

### 方式1：运行FastAPI（推荐）

```bash
# 直接运行
python backend/app.py

# 或使用uvicorn
uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload
```

### 方式2：运行Flask（保留原有功能）

```bash
python backend/app_flask.py
```

### 方式3：同时运行（需要不同端口）

```bash
# 终端1：运行FastAPI
uvicorn backend.app:app --host 0.0.0.0 --port 5001

# 终端2：运行Flask
python backend/app_flask.py --port 5002
```

## 路由对比

### FastAPI路由（新）

- `GET /api/ai/providers` - 查看AI提供商状态
- `POST /api/ai/chat` - 统一AI对话接口

### Flask路由（保留）

- `POST /api/trips/generate` - 生成行程
- `POST /api/generate_itinerary` - 使用外部API生成行程
- `POST /api/generate_trip` - 使用阿里云百炼生成行程
- `POST /api/generate_trip_dify` - 使用Dify生成行程
- `GET /api/trips/:id` - 获取行程详情
- `GET /api/trips` - 获取所有行程
- `PUT /api/trips/:id/adjust` - 调整行程
- `GET /api/trips/:id/map` - 获取地图数据
- `POST /api/trips/:id/export` - 导出行程
- `POST /api/ai/chat` - AI助手对话（旧版本）
- `GET /api/ai/history/<user_id>` - 获取对话历史
- `DELETE /api/ai/history/<user_id>` - 清除对话历史
- `GET /api/travel/hotels` - 搜索酒店
- `GET /api/travel/flights` - 搜索航班
- `GET /api/config/status` - 获取配置状态
- `GET /api/health` - 健康检查

## 迁移建议

如果需要完全迁移到FastAPI：

1. **逐步迁移路由**：将Flask路由逐个转换为FastAPI路由
2. **保持API兼容性**：确保前端调用的接口路径不变
3. **测试所有功能**：迁移后测试所有现有功能

## 注意事项

1. **数据库初始化**：FastAPI应用不会自动初始化数据库，需要手动运行或使用Flask应用初始化
2. **CORS配置**：FastAPI和Flask都配置了CORS，允许所有来源
3. **端口冲突**：如果同时运行，需要使用不同端口

## 推荐方案

**当前推荐**：使用FastAPI作为主要框架，逐步将Flask路由迁移到FastAPI。

**快速开始**：
```bash
# 启动FastAPI（包含新的AI路由）
uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload
```

如果需要使用原有的Flask路由，可以临时运行：
```bash
python backend/app_flask.py
```

