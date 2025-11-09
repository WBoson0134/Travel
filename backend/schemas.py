"""
API请求和响应的数据模型定义
使用Pydantic进行数据验证和序列化
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


class PaceEnum(str, Enum):
    """出行节奏枚举"""
    佛系 = "佛系"
    中庸 = "中庸"
    硬核 = "硬核"


class TransportModeEnum(str, Enum):
    """交通方式枚举"""
    driving = "driving"
    walking = "walking"
    transit = "transit"
    bicycling = "bicycling"
    taxi = "taxi"


# ==================== 请求模型 ====================

class ItineraryRequest(BaseModel):
    """生成行程请求模型"""
    city: str = Field(..., description="城市名称", min_length=1, max_length=100)
    days: int = Field(..., description="行程天数", ge=1, le=30)
    preferences: Optional[List[str]] = Field(
        default=[], 
        description="兴趣偏好列表，如：['文化', '自然', '美食']"
    )
    pace: Optional[PaceEnum] = Field(
        default=PaceEnum.中庸, 
        description="出行节奏：佛系/中庸/硬核"
    )
    transport_mode: Optional[TransportModeEnum] = Field(
        default=TransportModeEnum.driving,
        description="交通方式：driving/walking/transit/bicycling/taxi"
    )
    
    @field_validator('city')
    @classmethod
    def validate_city(cls, v: str) -> str:
        """验证城市名称"""
        if not v or not v.strip():
            raise ValueError('城市名称不能为空')
        return v.strip()
    
    @field_validator('preferences')
    @classmethod
    def validate_preferences(cls, v: Optional[List[str]]) -> List[str]:
        """验证偏好列表"""
        if v is None:
            return []
        # 去重并过滤空值
        return list(set(filter(lambda x: x and x.strip(), v)))
    
    class Config:
        use_enum_values = True  # 序列化时使用枚举的值而不是枚举对象
        json_schema_extra = {
            "example": {
                "city": "北京",
                "days": 3,
                "preferences": ["文化", "历史"],
                "pace": "中庸",
                "transport_mode": "driving"
            }
        }


# ==================== 响应模型 ====================

class ActivityResponse(BaseModel):
    """活动响应模型"""
    name: str = Field(..., description="活动/景点名称")
    type: str = Field(..., description="类型：文化/自然/美食/购物等")
    address: str = Field(default="", description="地址")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")
    start_time: str = Field(..., description="开始时间，格式：HH:MM")
    end_time: str = Field(..., description="结束时间，格式：HH:MM")
    duration_minutes: int = Field(..., description="持续时间（分钟）", ge=0)
    description: str = Field(default="", description="描述")
    rating: float = Field(default=4.5, description="评分", ge=0, le=5)
    price_range: str = Field(default="$", description="价格范围：$/$$/$$$/$$$$")
    price_estimate: float = Field(default=0, description="价格估算", ge=0)
    tags: List[str] = Field(default_factory=list, description="标签列表")
    order: int = Field(..., description="当天活动顺序", ge=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "天安门广场",
                "type": "文化",
                "address": "北京市东城区东长安街",
                "latitude": 39.9042,
                "longitude": 116.4074,
                "start_time": "09:00",
                "end_time": "11:00",
                "duration_minutes": 120,
                "description": "天安门广场是北京的著名景点，历史, 必游, 地标。",
                "rating": 4.6,
                "price_range": "免费",
                "price_estimate": 0,
                "tags": ["历史", "必游", "地标"],
                "order": 1
            }
        }


class DayPlanResponse(BaseModel):
    """每日行程响应模型"""
    day_number: int = Field(..., description="第几天", ge=1)
    description: str = Field(..., description="当天行程描述")
    activities: List[ActivityResponse] = Field(default_factory=list, description="活动列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "day_number": 1,
                "description": "第1天的行程安排，包含3个景点",
                "activities": []
            }
        }


class ItineraryResponse(BaseModel):
    """行程响应模型"""
    city: str = Field(..., description="城市名称")
    total_days: int = Field(..., description="总天数", ge=1)
    pace: str = Field(..., description="出行节奏")
    transport_mode: str = Field(..., description="交通方式")
    days: List[DayPlanResponse] = Field(default_factory=list, description="每日行程列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "city": "北京",
                "total_days": 3,
                "pace": "中庸",
                "transport_mode": "driving",
                "days": []
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "城市和天数为必填项"
            }
        }

