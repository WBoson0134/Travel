# 快速启动指南

## 一键启动（推荐）

### 方式1：使用脚本

**终端1 - 启动后端：**
```bash
./run_backend.sh
```

**终端2 - 启动前端：**
```bash
./run_frontend.sh
```

### 方式2：手动启动

**步骤1：设置后端**

```bash
# 安装Python依赖
pip install -r requirements.txt

# 配置环境变量（可选，用于AI和地图功能）
cp .env.example .env
# 编辑 .env 文件填入API密钥

# 初始化数据库
export FLASK_APP=backend/app.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 启动后端
python backend/app.py
```

**步骤2：设置前端**

```bash
cd frontend
npm install
npm run dev
```

## 访问应用

- 前端界面：http://localhost:3000
- 后端API：http://localhost:5000
- API健康检查：http://localhost:5000/api/health

## 测试功能

1. **生成行程**
   - 访问 http://localhost:3000
   - 填写城市、天数、偏好等信息
   - 点击"生成行程"

2. **查看地图**
   - 在行程详情页点击"查看地图"
   - 查看路线和标记点

3. **导出行程**
   - 在行程详情页点击"导出PDF"或"导出日历"
   - 下载文件

4. **调整行程**
   - 在行程详情页点击"调整行程"
   - 输入新的需求
   - 系统会重新生成方案

## 注意事项

- 如果没有配置API密钥，系统会使用模拟数据
- 首次运行需要安装依赖，可能需要几分钟
- 确保端口5000和3000未被占用

