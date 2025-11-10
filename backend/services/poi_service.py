import json
import os
from typing import List, Dict, Optional
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path
from backend.services.travel_api_service import TravelAPIService
import logging

logger = logging.getLogger(__name__)


class POIService:
    """POI服务：通过外部API获取POI数据和时间估算"""
    
    def __init__(self):
        # 使用外部旅游API服务
        self.travel_api_service = TravelAPIService()
    
    def get_pois_by_city(self, city: str, preferences: List[str] = None) -> List[Dict]:
        """根据城市从外部API获取POI列表"""
        # 调用外部API获取景点
        attractions = self.travel_api_service.search_attractions(city, preferences)
        
        if not attractions:
            logger.warning(f"无法从外部API获取{city}的景点信息，尝试使用内置POI数据")
            attractions = self._load_local_pois(city)
        
        if not attractions:
            return []
        
        # 如果没有偏好，返回所有景点
        if not preferences:
            return attractions
        
        # 根据偏好筛选
        filtered_pois = []
        for poi in attractions:
            poi_type = poi.get('type', '').lower()
            poi_tags = [tag.lower() for tag in poi.get('tags', [])]
            preferences_lower = [p.lower() for p in preferences]
            
            # 如果POI类型或标签匹配任何偏好，则包含
            if any(pref in poi_type for pref in preferences_lower) or \
               any(pref in tag for pref in preferences_lower for tag in poi_tags):
                filtered_pois.append(poi)
        
        # 如果没有匹配的，返回所有POI
        return filtered_pois if filtered_pois else attractions

    def _load_local_pois(self, city: str) -> List[Dict]:
        """从本地数据集中加载POI，作为外部API的回退方案"""
        data_path = Path(__file__).resolve().parent.parent / 'data' / 'poi_data.json'
        if not data_path.exists():
            return []
        try:
            with open(data_path, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            normalized = city.strip()
            candidates = [normalized, normalized.title(), normalized.lower(), normalized.upper()]
            for key in candidates:
                if key in data:
                    return data[key]
            return []
        except Exception as exc:
            logger.error('加载本地POI数据失败: %s', exc)
            return []

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """使用Haversine公式计算两点间距离（公里）"""
        R = 6371  # 地球半径（公里）
        
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def estimate_travel_time(self, distance_km: float, transport_mode: str = 'driving') -> int:
        """估算旅行时间（分钟）"""
        # 不同交通方式的平均速度（公里/小时）
        speed_kmh = {
            'driving': 50,
            'walking': 5,
            'transit': 30,
            'bicycling': 15,
            'taxi': 45
        }.get(transport_mode, 30)
        
        # 计算时间（分钟），加上10%的缓冲时间
        time_hours = distance_km / speed_kmh
        time_minutes = int(time_hours * 60 * 1.1)  # 增加10%缓冲
        
        return max(5, time_minutes)  # 最少5分钟
    
    def estimate_activity_time(self, poi: Dict, pace: str = '中庸') -> int:
        """估算活动时间（分钟），根据节奏调整"""
        base_duration = poi.get('duration_minutes', 120)
        
        # 根据节奏调整时间
        pace_multiplier = {
            '佛系': 1.3,  # 更慢，增加30%时间
            '中庸': 1.0,  # 正常
            '硬核': 0.7   # 更快，减少30%时间
        }.get(pace, 1.0)
        
        return int(base_duration * pace_multiplier)
    
    def generate_itinerary(self, city: str, days: int, preferences: List[str] = None, 
                          pace: str = '中庸', transport_mode: str = 'driving') -> Dict:
        """生成行程计划"""
        # 获取POI列表
        pois = self.get_pois_by_city(city, preferences)
        
        if not pois:
            return {
                'error': f'未找到{city}的POI数据',
                'days': []
            }
        
        # 根据节奏决定每天的活动数量
        activities_per_day = {
            '佛系': 2,
            '中庸': 3,
            '硬核': 4
        }.get(pace, 3)
        
        # 生成行程
        itinerary = {
            'city': city,
            'total_days': days,
            'pace': pace,
            'transport_mode': transport_mode,
            'days': []
        }
        
        poi_index = 0
        total_pois = len(pois)
        
        for day in range(1, days + 1):
            day_activities = []
            current_time = 9 * 60  # 从9:00开始（以分钟为单位）
            
            for activity_num in range(activities_per_day):
                if poi_index >= total_pois:
                    # 如果POI用完了，可以重复使用或结束
                    break
                
                poi = pois[poi_index % total_pois]  # 循环使用POI
                poi_index += 1
                
                # 估算活动时间
                activity_duration = self.estimate_activity_time(poi, pace)
                
                # 计算开始和结束时间
                start_hour = current_time // 60
                start_minute = current_time % 60
                end_time = current_time + activity_duration
                end_hour = end_time // 60
                end_minute = end_time % 60
                
                # 格式化时间
                start_time_str = f"{start_hour:02d}:{start_minute:02d}"
                end_time_str = f"{end_hour:02d}:{end_minute:02d}"
                
                # 创建活动对象
                activity = {
                    'name': poi['name'],
                    'type': poi.get('type', '文化'),
                    'address': poi.get('address', ''),
                    'latitude': poi.get('latitude'),
                    'longitude': poi.get('longitude'),
                    'start_time': start_time_str,
                    'end_time': end_time_str,
                    'duration_minutes': activity_duration,
                    'description': f"{poi['name']}是{city}的著名景点，{', '.join(poi.get('tags', []))}。",
                    'rating': poi.get('rating', 4.5),
                    'price_range': poi.get('price_range', '$'),
                    'price_estimate': poi.get('price_estimate', 50),
                    'tags': poi.get('tags', []),
                    'order': activity_num + 1
                }
                
                day_activities.append(activity)
                
                # 更新当前时间（活动时间 + 30分钟缓冲/用餐时间）
                current_time = end_time + 30
                
                # 如果还有下一个活动，计算旅行时间
                if activity_num < activities_per_day - 1 and poi_index < total_pois:
                    next_poi = pois[poi_index % total_pois]
                    if poi.get('latitude') and next_poi.get('latitude'):
                        distance = self.calculate_distance(
                            poi['latitude'], poi['longitude'],
                            next_poi['latitude'], next_poi['longitude']
                        )
                        travel_time = self.estimate_travel_time(distance, transport_mode)
                        current_time += travel_time
            
            # 添加一天的计划
            itinerary['days'].append({
                'day_number': day,
                'description': f'第{day}天的行程安排，包含{len(day_activities)}个景点',
                'activities': day_activities
            })
        
        return itinerary

