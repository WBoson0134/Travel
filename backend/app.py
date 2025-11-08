from flask import Flask
from flask_cors import CORS
from backend.config import Config
from backend.models import db
from backend.routes import api
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    CORS(app, origins=Config.CORS_ORIGINS)
    
    # 注册蓝图
    app.register_blueprint(api)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)

