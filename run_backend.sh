#!/bin/bash

# 激活虚拟环境（如果使用）
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
export FLASK_APP=backend/app.py
flask db init 2>/dev/null || true
flask db migrate -m "Initial migration" 2>/dev/null || true
flask db upgrade

# 运行后端服务器（FastAPI）
# 如果需要运行Flask应用，使用: python backend/app_flask.py
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

