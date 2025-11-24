"""
Google Places API 服务
用于获取真实的景点数据、评分、评论等信息
"""
import requests
import logging
from typing import List, Dict, Optional
from backend.config import Config

logger = logging.getLogger(__name__)


class GooglePlacesService:
    """Google Places API 服务"""
    
    def __init__(self):
        self.api_key = Config.GOOGLE_MAPS_API_KEY  # 使用现有的 Google Maps API Key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return bool(self.api_key)
    
    def search_places(
        self, 
        city: str, 
        query: str = None, 
        type_filter: str = "tourist_attraction",
        max_results: int = 20
    ) -> List[Dict]:
        """
        搜索景点
        
        Args:
            city: 城市名称
            query: 搜索关键词（可选）
            type_filter: 地点类型（tourist_attraction, museum, park 等）
            max_results: 最大返回数量
            
        Returns:
            景点列表
        """
        if not self.api_key:
            logger.warning("Google Places API key not configured")
            return []
        
        try:
            # 构建搜索查询
            search_query = f"{query} in {city}" if query else f"tourist attractions in {city}"
            
            url = f"{self.base_url}/textsearch/json"
            params = {
                "query": search_query,
                "type": type_filter,
                "key": self.api_key,
                "language": "zh-CN",
                "region": "cn"  # 优先中国地区结果
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                logger.warning(f"Google Places API error: {data.get('status')}")
                return []
            
            places = []
            for result in data.get("results", [])[:max_results]:
                place = {
                    "name": result.get("name", ""),
                    "type": result.get("types", [type_filter])[0] if result.get("types") else type_filter,
                    "rating": result.get("rating", 0),
                    "user_ratings_total": result.get("user_ratings_total", 0),
                    "formatted_address": result.get("formatted_address", ""),
                    "latitude": result.get("geometry", {}).get("location", {}).get("lat"),
                    "longitude": result.get("geometry", {}).get("location", {}).get("lng"),
                    "place_id": result.get("place_id", ""),
                    "photos": result.get("photos", [])[:1],  # 只取第一张照片
                    "price_level": result.get("price_level", 0),  # 0-4, 0=免费, 4=最贵
                }
                
                # 获取详细信息的占位符（可选，需要额外 API 调用）
                place["description"] = f"{place['name']}是{city}的一个热门景点，评分{place['rating']}分。"
                
                places.append(place)
            
            logger.info(f"从 Google Places 获取到 {len(places)} 个景点")
            return places
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Places API 请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"Google Places API 处理失败: {e}")
            return []
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        获取景点详细信息
        
        Args:
            place_id: Google Places place_id
            
        Returns:
            景点详细信息
        """
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}/details/json"
            params = {
                "place_id": place_id,
                "key": self.api_key,
                "language": "zh-CN",
                "fields": "name,rating,formatted_address,geometry,photos,reviews,opening_hours,website,international_phone_number"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                return None
            
            result = data.get("result", {})
            return {
                "name": result.get("name", ""),
                "rating": result.get("rating", 0),
                "formatted_address": result.get("formatted_address", ""),
                "reviews": result.get("reviews", [])[:5],  # 前5条评论
                "opening_hours": result.get("opening_hours", {}),
                "website": result.get("website", ""),
                "phone": result.get("international_phone_number", ""),
            }
            
        except Exception as e:
            logger.error(f"获取景点详情失败: {e}")
            return None
    
    def search_by_preferences(
        self, 
        city: str, 
        preferences: List[str],
        max_results_per_pref: int = 5
    ) -> List[Dict]:
        """
        根据偏好搜索景点
        
        Args:
            city: 城市名称
            preferences: 偏好列表（如：["文化", "历史", "美食"]）
            max_results_per_pref: 每个偏好的最大结果数
            
        Returns:
            景点列表
        """
        all_places = []
        seen_place_ids = set()
        
        # 偏好关键词映射
        preference_keywords = {
            "文化": "museum cultural center",
            "历史": "historical site monument",
            "美食": "restaurant food market",
            "自然": "park nature reserve",
            "艺术": "art gallery museum",
            "购物": "shopping mall market",
            "娱乐": "entertainment center theme park",
            "宗教": "temple church mosque",
        }
        
        for pref in preferences:
            keywords = preference_keywords.get(pref, pref)
            places = self.search_places(
                city=city,
                query=keywords,
                max_results=max_results_per_pref
            )
            
            # 去重
            for place in places:
                place_id = place.get("place_id")
                if place_id and place_id not in seen_place_ids:
                    seen_place_ids.add(place_id)
                    place["matched_preference"] = pref
                    all_places.append(place)
        
        # 如果没有偏好或没有结果，搜索通用景点
        if not all_places:
            all_places = self.search_places(city=city, max_results=max_results_per_pref * 2)
        
        return all_places

