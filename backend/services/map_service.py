import os
import requests
from geopy.geocoders import Nominatim
from backend.config import Config

class MapService:
    """地图服务：处理地理编码、路线计算等"""
    
    def __init__(self):
        self.google_maps_key = Config.GOOGLE_MAPS_API_KEY
        self.geoapify_key = Config.GEOAPIFY_API_KEY
        self.geoapify_url = Config.GEOAPIFY_API_URL or "https://api.geoapify.com/v1"
        self.geocoder = Nominatim(user_agent="travel_planner")
    
    def geocode_address(self, address):
        """地址转坐标（优先使用 Geoapify，如果没有则使用 Nominatim）"""
        # 优先使用 Geoapify
        if self.geoapify_key:
            try:
                url = f"{self.geoapify_url}/geocode/search"
                params = {
                    "text": address,
                    "apiKey": self.geoapify_key,
                    "limit": 1
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("features"):
                        feature = data["features"][0]
                        geometry = feature["geometry"]
                        properties = feature["properties"]
                        return {
                            "latitude": geometry["coordinates"][1],
                            "longitude": geometry["coordinates"][0],
                            "formatted_address": properties.get("formatted", address)
                        }
            except Exception as e:
                print(f"Geoapify 地理编码失败: {e}")
        
        # 如果没有 Geoapify 或失败，使用 Nominatim
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
        """计算路线（优先使用 Geoapify，如果没有则使用 Google Maps API）"""
        # 优先使用 Geoapify
        if self.geoapify_key:
            try:
                # Geoapify 路由模式映射
                mode_map = {
                    "driving": "drive",
                    "walking": "walk",
                    "transit": "public_transport",
                    "bicycling": "bicycle"
                }
                geoapify_mode = mode_map.get(mode, "drive")
                
                url = f"{self.geoapify_url}/routing"
                params = {
                    "waypoints": f"{from_lng},{from_lat}|{to_lng},{to_lat}",
                    "mode": geoapify_mode,
                    "apiKey": self.geoapify_key
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("features"):
                        feature = data["features"][0]
                        properties = feature["properties"]
                        geometry = feature["geometry"]
                        
                        return {
                            "duration_minutes": int(properties.get("time", 0) / 60),
                            "distance_km": round(properties.get("distance", 0) / 1000, 2),
                            "route_data": None,
                            "polyline": None
                        }
            except Exception as e:
                print(f"Geoapify 路线计算失败: {e}")
        
        # 如果没有 Geoapify 或失败，使用 Google Maps API
        if self.google_maps_key:
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
        
        # 如果都没有，返回简单估算
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
        """获取附近地点（优先使用 Geoapify，如果没有则使用 Google Places API）"""
        # 优先使用 Geoapify
        if self.geoapify_key:
            try:
                url = f"{self.geoapify_url}/places/radius"
                params = {
                    "lat": lat,
                    "lon": lng,
                    "radius": radius,
                    "apiKey": self.geoapify_key,
                    "limit": 20
                }
                
                # Geoapify 类别映射
                if type_filter:
                    category_map = {
                        "restaurant": "catering.restaurant",
                        "tourist_attraction": "tourism",
                        "hotel": "accommodation",
                        "shopping_mall": "commercial.shopping_mall"
                    }
                    if type_filter in category_map:
                        params["categories"] = category_map[type_filter]
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("features"):
                        return [
                            {
                                "name": feature["properties"].get("name", "未知地点"),
                                "latitude": feature["geometry"]["coordinates"][1],
                                "longitude": feature["geometry"]["coordinates"][0],
                                "rating": feature["properties"].get("rating", 0),
                                "types": feature["properties"].get("categories", [])
                            }
                            for feature in data["features"]
                        ]
            except Exception as e:
                print(f"Geoapify 获取附近地点失败: {e}")
        
        # 如果没有 Geoapify 或失败，使用 Google Places API
        if self.google_maps_key:
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

