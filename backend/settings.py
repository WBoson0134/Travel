import os
from dotenv import load_dotenv

load_dotenv()  # 读取根目录 .env

LLM_PRIMARY = os.getenv("LLM_PRIMARY", "aliyun")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # 占位

DIFY_API_BASE = os.getenv("DIFY_API_BASE", "").rstrip("/")
DIFY_API_KEY  = os.getenv("DIFY_API_KEY", "")
DIFY_APP_USER = os.getenv("DIFY_APP_USER", "web-user")

