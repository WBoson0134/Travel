# 项目设置指南

## 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

## 快速开始

### 1. 后端设置

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的API密钥

# 初始化数据库
export FLASK_APP=backend/app.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 运行后端
python backend/app.py
```

后端将在 `http://localhost:5000` 运行

### 2. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

前端将在 `http://localhost:3000` 运行

## API密钥配置

在 `.env` 文件中配置以下API密钥（可选，但某些功能需要）：

1. **OpenAI API Key** - 用于AI生成行程和润色描述
   - 获取地址：https://platform.openai.com/api-keys
   - 功能：智能行程生成、描述润色、评价生成

2. **Google Maps API Key** - 用于地图和地理编码
   - 获取地址：https://console.cloud.google.com/google/maps-apis
   - 功能：地图可视化、路线计算、地理编码

3. **TripAdvisor API Key** - 用于获取景点评价（可选）
   - 功能：用户评价数据

**注意**：如果没有配置API密钥，系统会使用模拟数据，功能仍然可用但质量会降低。

## 项目结构

```
travel/
├── backend/                 # 后端代码
│   ├── app.py              # Flask应用入口
│   ├── config.py           # 配置文件
│   ├── models.py           # 数据库模型
│   ├── routes.py           # API路由
│   └── services/           # 业务逻辑服务
│       ├── ai_service.py   # AI服务
│       ├── map_service.py  # 地图服务
│       ├── price_service.py # 价格服务
│       └── export_service.py # 导出服务
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── App.jsx         # 主应用组件
│   │   └── main.jsx        # 入口文件
│   └── package.json        # 前端依赖
├── requirements.txt        # Python依赖
└── README.md              # 项目说明
```

## 主要功能

### 1. 智能行程生成
- 输入城市、天数、偏好等信息
- AI自动生成详细行程

### 2. 地图可视化
- 查看行程路线
- 交互式地图标记

### 3. 行程导出
- PDF格式导出
- ICS日历格式导出

### 4. 个性化调整
- 根据用户反馈实时调整行程

### 5. 价格和评价
- 自动价格估算
- 景点评价和标签

## 开发说明

### 数据库迁移

```bash
# 创建迁移
flask db migrate -m "描述"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

### 前端构建

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录

## 常见问题

1. **端口被占用**
   - 后端：修改 `backend/app.py` 中的端口号
   - 前端：修改 `frontend/vite.config.js` 中的端口号

2. **数据库错误**
   - 删除 `travel.db` 文件重新初始化
   - 检查 `DATABASE_URL` 配置

3. **API调用失败**
   - 检查API密钥是否正确
   - 检查网络连接
   - 查看控制台错误信息

## 下一步

- 添加用户认证系统
- 集成更多第三方API
- 优化AI生成质量
- 添加更多导出格式
- 实现行程分享功能

