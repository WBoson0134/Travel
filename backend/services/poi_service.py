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
        # 尝试使用 MCP 客户端（优先）
        try:
            from backend.services.mcp_travel_client import MCPTravelClient
            self.mcp_client = MCPTravelClient()
            logger.info("MCP 旅游客户端已启用")
        except Exception as e:
            logger.warning(f"MCP 客户端初始化失败，使用回退方案: {e}")
            self.mcp_client = None
        
        # 尝试导入 Google Places 服务
        try:
            from backend.services.google_places_service import GooglePlacesService
            self.google_places = GooglePlacesService()
            if self.google_places.is_available():
                logger.info("Google Places 服务已启用")
            else:
                logger.warning("Google Places API key 未配置")
                self.google_places = None
        except ImportError:
            logger.warning("Google Places 服务未找到，跳过")
            self.google_places = None
    
    def get_pois_by_city(self, city: str, preferences: List[str] = None) -> List[Dict]:
        """根据城市从外部API获取POI列表"""
        # 1. 优先使用 MCP 客户端（如果可用）
        if self.mcp_client:
            try:
                attractions = self.mcp_client.search_attractions(city, preferences)
                if attractions:
                    logger.info(f"从 MCP 客户端获取到 {len(attractions)} 个景点")
                    return attractions
            except Exception as e:
                logger.warning(f"MCP 客户端调用失败，回退到其他数据源: {e}")
        
        # 2. 使用 Google Places API（如果可用）
        if self.google_places and self.google_places.is_available():
            try:
                places = self.google_places.search_by_preferences(
                    city=city,
                    preferences=preferences or [],
                    max_results_per_pref=5
                )
                if places:
                    # 转换 Google Places 格式到内部格式
                    attractions = self._convert_google_places_to_pois(places)
                    logger.info(f"从 Google Places 获取到 {len(attractions)} 个景点")
                    return attractions
            except Exception as e:
                logger.warning(f"Google Places API 调用失败，回退到其他数据源: {e}")
        
        # 3. 回退到原有的外部API
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
    
    def _convert_google_places_to_pois(self, places: List[Dict]) -> List[Dict]:
        """将 Google Places 格式转换为内部 POI 格式"""
        pois = []
        for place in places:
            # 价格级别转换
            price_level_map = {0: "$", 1: "$$", 2: "$$$", 3: "$$$$", 4: "$$$$$"}
            price_range = price_level_map.get(place.get("price_level", 0), "$$")
            
            # 估算价格（基于价格级别）
            price_estimate_map = {0: 0, 1: 50, 2: 150, 3: 300, 4: 500}
            price_estimate = price_estimate_map.get(place.get("price_level", 0), 100)
            
            # 类型转换
            place_type = place.get("type", "tourist_attraction")
            type_mapping = {
                "tourist_attraction": "景点",
                "museum": "博物馆",
                "park": "公园",
                "restaurant": "餐厅",
                "shopping_mall": "购物",
                "church": "宗教",
                "temple": "宗教",
            }
            poi_type = type_mapping.get(place_type, "景点")
            
            # 构建标签
            tags = []
            if place.get("rating", 0) >= 4.5:
                tags.append("热门")
            if place.get("user_ratings_total", 0) > 1000:
                tags.append("推荐")
            matched_pref = place.get("matched_preference")
            if matched_pref:
                tags.append(matched_pref)
            
            poi = {
                "name": place.get("name", ""),
                "type": poi_type,
                "address": place.get("formatted_address", ""),
                "latitude": place.get("latitude"),
                "longitude": place.get("longitude"),
                "rating": place.get("rating", 0),
                "user_ratings_total": place.get("user_ratings_total", 0),
                "price_range": price_range,
                "price_estimate": price_estimate,
                "tags": tags,
                "description": place.get("description", ""),
                "place_id": place.get("place_id", ""),
                "source": "google_places"
            }
            pois.append(poi)
        
        return pois

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

    def _generate_placeholder_itinerary(self, city: str, days: int, pace: str, transport_mode: str) -> Dict:
        """生成占位行程，供 AI 后续优化。"""
        pace = pace or '中庸'
        activities_per_day = {
            '佛系': 2,
            '中庸': 3,
            '硬核': 4
        }.get(pace, 3)

        itinerary = {
            'city': city,
            'total_days': days,
            'pace': pace,
            'transport_mode': transport_mode,
            'source': 'placeholder',
            'notice': f'未找到{city}的POI数据，已生成占位行程供AI优化',
            'days': []
        }

        for day in range(1, days + 1):
            current_time = 9 * 60
            activities = []
            for idx in range(activities_per_day):
                start_hour = current_time // 60
                start_minute = current_time % 60
                end_time = current_time + 90
                end_hour = end_time // 60
                end_minute = end_time % 60
                activities.append({
                    'name': f'{city} 精选体验 {idx + 1}',
                    'type': '体验',
                    'address': '',
                    'latitude': None,
                    'longitude': None,
                    'start_time': f"{start_hour:02d}:{start_minute:02d}",
                    'end_time': f"{end_hour:02d}:{end_minute:02d}",
                    'duration_minutes': 90,
                    'description': '占位活动，等待AI进一步优化。',
                    'rating': 4.5,
                    'price_range': '$$',
                    'price_estimate': 80,
                    'tags': ['待优化'],
                    'order': idx + 1
                })
                current_time = end_time + 30

            itinerary['days'].append({
                'day_number': day,
                'description': f'{city} 第{day}天占位行程，等待AI优化。',
                'activities': activities
            })

        return itinerary

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
            logger.warning(f"未找到{city}的POI数据，使用占位行程")
            return self._generate_placeholder_itinerary(city, int(days) if days else 1, pace, transport_mode)
        
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

