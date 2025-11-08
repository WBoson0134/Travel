# 智能行程生成系统

一个基于AI的智能旅游行程规划系统，支持个性化推荐、地图可视化、行程导出等功能。

## 功能特性

1. **智能行程生成**：根据用户输入自动生成可执行的逐日行程计划
2. **路线与时间计算**：智能计算路线时间、营业时间和合理顺序
3. **地图可视化**：交互式地图展示行程路线
4. **行程导出**：支持PDF和ICS格式导出
5. **个性化调整**：支持节奏和偏好权重调整
6. **智能润色**：AI生成自然语言描述和推荐理由
7. **用户评价**：展示景点评价、标签和星级
8. **自动比价**：提供最优价格推荐
9. **实时交互**：根据用户反馈实时调整方案

## 项目结构

```
travel/
├── backend/          # 后端代码
│   ├── app.py       # Flask应用主文件
│   ├── models.py    # 数据库模型
│   ├── routes.py    # API路由
│   ├── services/    # 业务逻辑服务
│   └── utils/       # 工具函数
├── frontend/        # 前端代码
│   ├── src/
│   ├── public/
│   └── package.json
├── requirements.txt # Python依赖
└── README.md
```

## 安装和运行

### 快速开始

1. **运行后端服务**：
```bash
bash run_backend.sh
```

2. **运行前端服务**：
```bash
bash run_frontend.sh
```

后端服务将运行在 `http://localhost:5001`，前端服务将运行在 `http://localhost:3000`

### 详细安装步骤

#### 后端

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量（见下方「AI 行程生成配置」章节）

3. 初始化数据库：
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

4. 运行后端：
```bash
python backend/app.py
```

#### 前端

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 运行开发服务器：
```bash
npm run dev
```

## AI 行程生成配置

系统支持两种 AI 服务来生成行程：

### 1. 阿里云百炼（DashScope）

在项目根目录创建 `.env` 文件，添加以下配置：

```env
# 阿里云百炼 API 配置
OPENAI_API_KEY=your_dashscope_api_key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/api/v1
```

**获取 API Key**：
1. 访问 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
2. 创建应用并获取 API Key
3. 将 API Key 填入 `.env` 文件

### 2. Dify

如果需要使用 Dify 生成行程，添加以下配置：

```env
# Dify API 配置
DIFY_API_KEY=your_dify_api_key
DIFY_API_BASE=https://api.dify.ai/v1
```

**获取 API Key**：
1. 访问 [Dify 平台](https://dify.ai/)
2. 创建应用并获取 API Key
3. 将 API Key 填入 `.env` 文件

### 完整 .env 示例

```env
# Flask 配置
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///travel.db

# 阿里云百炼 API 配置
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# Dify API 配置（可选）
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxxx
DIFY_API_BASE=https://api.dify.ai/v1

# 其他 API 配置（可选）
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
TRIPADVISOR_API_KEY=your_tripadvisor_api_key
```

## API文档

后端API运行在 `http://localhost:5001`

### 主要端点

- `POST /api/trips/generate` - 生成行程（保存到数据库）
- `POST /api/generate_trip` - 使用阿里云百炼生成行程（直接返回）
- `POST /api/generate_trip_dify` - 使用 Dify 生成行程（直接返回）
- `GET /api/trips/:id` - 获取行程详情
- `PUT /api/trips/:id/adjust` - 调整行程
- `GET /api/trips/:id/map` - 获取地图数据
- `POST /api/trips/:id/export` - 导出行程
- `GET /api/health` - 健康检查

### API 使用示例

#### 1. 使用阿里云百炼生成行程

**请求**：
```bash
curl -X POST http://localhost:5001/api/generate_trip \
  -H "Content-Type: application/json" \
  -d '{
    "city": "北京",
    "days": 3,
    "preferences": ["自然", "美食", "文化"],
    "pace": "中庸",
    "transport": "driving",
    "priority": "效率优先"
  }'
```

**响应示例**：
```json
{
  "output": {
    "choices": [
      {
        "message": {
          "content": "{\"days\": [{\"day_number\": 1, \"description\": \"第一天行程\", \"activities\": [...]}]}"
        }
      }
    ]
  }
}
```

#### 2. 使用 Dify 生成行程

**请求**：
```bash
curl -X POST http://localhost:5001/api/generate_trip_dify \
  -H "Content-Type: application/json" \
  -d '{
    "city": "北京",
    "days": 3,
    "preferences": ["自然", "美食"]
  }'
```

**响应示例**：
```json
{
  "data": {
    "workflow_run_id": "xxx",
    "outputs": {
      "result": "{\"days\": [...]}"
    }
  }
}
```

#### 3. 错误响应

当 API 调用失败时，返回格式：
```json
{
  "error": "AI generation failed"
}
```

### 测试脚本

项目根目录提供了测试脚本 `test_generate_trip.py`：

```bash
python test_generate_trip.py
```

该脚本会向 `/api/generate_trip` 发送测试请求，并打印返回结果。

## 技术栈

- **后端**：Flask, SQLAlchemy, OpenAI API
- **前端**：React, Leaflet/Google Maps
- **数据库**：SQLite (开发) / PostgreSQL (生产)

