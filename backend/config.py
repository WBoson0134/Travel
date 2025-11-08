import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///travel.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyun.com/api/v1')
    DIFY_API_KEY = os.getenv('DIFY_API_KEY')
    DIFY_API_BASE = os.getenv('DIFY_API_BASE')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    TRIPADVISOR_API_KEY = os.environ.get('TRIPADVISOR_API_KEY')
    
    # CORS
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']

