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

### 后端

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入API密钥
```

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

### 前端

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
npm start
```

## API文档

后端API运行在 `http://localhost:5000`

主要端点：
- `POST /api/trips/generate` - 生成行程
- `GET /api/trips/:id` - 获取行程详情
- `PUT /api/trips/:id/adjust` - 调整行程
- `GET /api/trips/:id/map` - 获取地图数据
- `POST /api/trips/:id/export` - 导出行程

## 技术栈

- **后端**：Flask, SQLAlchemy, OpenAI API
- **前端**：React, Leaflet/Google Maps
- **数据库**：SQLite (开发) / PostgreSQL (生产)

