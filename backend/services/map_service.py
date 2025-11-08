import os
import requests
from geopy.geocoders import Nominatim
from backend.config import Config

class MapService:
    """地图服务：处理地理编码、路线计算等"""
    
    def __init__(self):
        self.google_maps_key = Config.GOOGLE_MAPS_API_KEY
        self.geocoder = Nominatim(user_agent="travel_planner")
    
    def geocode_address(self, address):
        """地址转坐标"""
        try:
            location = self.geocoder.geocode(address)
            if location:
                return {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "formatted_address": location.address
                }
        except Exception as e:
            print(f"地理编码失败: {e}")
        
        return None
    
    def calculate_route(self, from_lat, from_lng, to_lat, to_lng, mode="driving"):
        """计算路线（使用Google Maps API）"""
        if not self.google_maps_key:
            # 如果没有API key，返回简单估算
            return self._estimate_route(from_lat, from_lng, to_lat, to_lng, mode)
        
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{from_lat},{from_lng}",
            "destination": f"{to_lat},{to_lng}",
            "mode": mode,
            "key": self.google_maps_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] == "OK" and data["routes"]:
                route = data["routes"][0]
                leg = route["legs"][0]
                
                return {
                    "duration_minutes": leg["duration"]["value"] // 60,
                    "distance_km": leg["distance"]["value"] / 1000,
                    "route_data": [step["polyline"]["points"] for step in leg["steps"]],
                    "polyline": route["overview_polyline"]["points"]
                }
        except Exception as e:
            print(f"路线计算失败: {e}")
        
        return self._estimate_route(from_lat, from_lng, to_lat, to_lng, mode)
    
    def _estimate_route(self, from_lat, from_lng, to_lat, to_lng, mode):
        """简单估算路线（当没有API时）"""
        # 使用Haversine公式估算距离
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # 地球半径（公里）
        
        lat1, lon1 = radians(from_lat), radians(from_lng)
        lat2, lon2 = radians(to_lat), radians(to_lng)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        distance_km = R * c
        
        # 估算时间（根据交通方式）
        speed_kmh = {
            "driving": 50,
            "walking": 5,
            "transit": 30,
            "bicycling": 15
        }.get(mode, 30)
        
        duration_minutes = int((distance_km / speed_kmh) * 60)
        
        return {
            "duration_minutes": duration_minutes,
            "distance_km": round(distance_km, 2),
            "route_data": None,
            "polyline": None
        }
    
    def get_places_nearby(self, lat, lng, radius=1000, type_filter=None):
        """获取附近地点（使用Google Places API）"""
        if not self.google_maps_key:
            return []
        
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "key": self.google_maps_key
        }
        
        if type_filter:
            params["type"] = type_filter
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] == "OK":
                return [
                    {
                        "name": place["name"],
                        "latitude": place["geometry"]["location"]["lat"],
                        "longitude": place["geometry"]["location"]["lng"],
                        "rating": place.get("rating", 0),
                        "types": place.get("types", [])
                    }
                    for place in data.get("results", [])
                ]
        except Exception as e:
            print(f"获取附近地点失败: {e}")
        
        return []

