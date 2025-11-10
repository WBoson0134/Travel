import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///travel.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyun.com/api/v1')
    DIFY_API_KEY = os.getenv('DIFY_API_KEY')
    DIFY_API_BASE = os.getenv('DIFY_API_BASE')
    
    # 外部旅游API Keys
    BOOKING_API_KEY = os.getenv('BOOKING_API_KEY')
    BOOKING_API_URL = os.getenv('BOOKING_API_URL', 'https://api.booking.com/v1')
    AMADEUS_API_KEY = os.getenv('AMADEUS_API_KEY')
    AMADEUS_API_SECRET = os.getenv('AMADEUS_API_SECRET')
    AMADEUS_API_URL = os.getenv('AMADEUS_API_URL', 'https://api.amadeus.com/v1')
    TRIPADVISOR_API_KEY = os.environ.get('TRIPADVISOR_API_KEY')
    TRIPADVISOR_API_URL = os.getenv('TRIPADVISOR_API_URL', 'https://api.tripadvisor.com/api')
    
    # 地图API
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    GEOAPIFY_API_KEY = os.getenv('GEOAPIFY_API_KEY')
    GEOAPIFY_API_URL = os.getenv('GEOAPIFY_API_URL', 'https://api.geoapify.com/v1')
    
    # CORS
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']

