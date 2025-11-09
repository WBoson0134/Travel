"""
外部旅游API服务
集成Booking.com、Amadeus等外部API来获取旅游信息
"""
import os
import requests
from typing import List, Dict, Optional
from backend.config import Config
import logging

logger = logging.getLogger(__name__)


class TravelAPIService:
    """外部旅游API服务：调用第三方API获取旅游信息"""
    
    def __init__(self):
        self.booking_api_key = Config.BOOKING_API_KEY
        self.booking_api_url = Config.BOOKING_API_URL or "https://api.booking.com/v1"
        self.amadeus_api_key = Config.AMADEUS_API_KEY
        self.amadeus_api_secret = Config.AMADEUS_API_SECRET
        self.amadeus_api_url = Config.AMADEUS_API_URL or "https://api.amadeus.com/v1"
        self.tripadvisor_api_key = Config.TRIPADVISOR_API_KEY
        self.tripadvisor_api_url = Config.TRIPADVISOR_API_URL or "https://api.tripadvisor.com/api"
        
    def _get_amadeus_token(self) -> Optional[str]:
        """获取Amadeus API访问令牌"""
        if not self.amadeus_api_key or not self.amadeus_api_secret:
            return None
        
        try:
            url = f"{self.amadeus_api_url}/security/oauth2/token"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "client_credentials",
                "client_id": self.amadeus_api_key,
                "client_secret": self.amadeus_api_secret
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                return response.json().get("access_token")
        except Exception as e:
            logger.error(f"获取Amadeus token失败: {e}")
        
        return None
    
    def search_hotels(self, city: str, check_in: str = None, check_out: str = None, 
                     adults: int = 2, rooms: int = 1) -> List[Dict]:
        """
        搜索酒店
        
        Args:
            city: 城市名称
            check_in: 入住日期 (YYYY-MM-DD)
            check_out: 退房日期 (YYYY-MM-DD)
            adults: 成人数量
            rooms: 房间数量
        
        Returns:
            酒店列表
        """
        hotels = []
        
        # 尝试使用Booking.com API
        if self.booking_api_key:
            try:
                hotels = self._search_hotels_booking(city, check_in, check_out, adults, rooms)
                if hotels:
                    return hotels
            except Exception as e:
                logger.warning(f"Booking.com API调用失败: {e}")
        
        # 尝试使用Amadeus API
        if self.amadeus_api_key:
            try:
                hotels = self._search_hotels_amadeus(city, check_in, check_out, adults, rooms)
                if hotels:
                    return hotels
            except Exception as e:
                logger.warning(f"Amadeus API调用失败: {e}")
        
        # 如果没有API或调用失败，返回空列表
        logger.warning(f"无法获取{city}的酒店信息，请配置API密钥")
        return []
    
    def _search_hotels_booking(self, city: str, check_in: str, check_out: str, 
                               adults: int, rooms: int) -> List[Dict]:
        """使用Booking.com API搜索酒店"""
        # 注意：这是示例实现，实际需要根据Booking.com API文档调整
        # Booking.com API通常需要合作伙伴认证
        url = f"{self.booking_api_url}/hotels/search"
        headers = {
            "Authorization": f"Bearer {self.booking_api_key}",
            "Content-Type": "application/json"
        }
        params = {
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "adults": adults,
            "rooms": rooms
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("hotels", [])
        except Exception as e:
            logger.error(f"Booking.com API错误: {e}")
        
        return []
    
    def _search_hotels_amadeus(self, city: str, check_in: str, check_out: str,
                               adults: int, rooms: int) -> List[Dict]:
        """使用Amadeus API搜索酒店"""
        token = self._get_amadeus_token()
        if not token:
            return []
        
        # 首先获取城市代码
        city_code = self._get_city_code_amadeus(city)
        if not city_code:
            return []
        
        url = f"{self.amadeus_api_url}/reference-data/locations/hotels/by-city"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "cityCode": city_code
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                hotels = []
                for hotel in data.get("data", [])[:10]:  # 限制返回10个
                    hotels.append({
                        "name": hotel.get("name", ""),
                        "hotel_id": hotel.get("hotelId", ""),
                        "latitude": hotel.get("geoCode", {}).get("latitude"),
                        "longitude": hotel.get("geoCode", {}).get("longitude"),
                        "rating": 4.0,  # 默认评分
                        "price_range": "$$",
                        "address": hotel.get("address", {}).get("lines", [""])[0] if hotel.get("address") else ""
                    })
                return hotels
        except Exception as e:
            logger.error(f"Amadeus API错误: {e}")
        
        return []
    
    def _get_city_code_amadeus(self, city: str) -> Optional[str]:
        """获取Amadeus城市代码"""
        token = self._get_amadeus_token()
        if not token:
            return None
        
        url = f"{self.amadeus_api_url}/reference-data/locations"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "subType": "CITY",
            "keyword": city
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    return data["data"][0].get("iataCode")
        except Exception as e:
            logger.error(f"获取城市代码失败: {e}")
        
        return None
    
    def search_attractions(self, city: str, preferences: List[str] = None) -> List[Dict]:
        """
        搜索景点/POI
        
        Args:
            city: 城市名称
            preferences: 偏好列表
        
        Returns:
            景点列表
        """
        attractions = []
        
        # 尝试使用TripAdvisor API
        if self.tripadvisor_api_key:
            try:
                attractions = self._search_attractions_tripadvisor(city, preferences)
                if attractions:
                    return attractions
            except Exception as e:
                logger.warning(f"TripAdvisor API调用失败: {e}")
        
        # 如果没有API或调用失败，返回空列表
        logger.warning(f"无法获取{city}的景点信息，请配置API密钥")
        return []
    
    def _search_attractions_tripadvisor(self, city: str, preferences: List[str] = None) -> List[Dict]:
        """使用TripAdvisor API搜索景点"""
        # 注意：这是示例实现，实际需要根据TripAdvisor API文档调整
        url = f"{self.tripadvisor_api_url}/location/search"
        headers = {
            "X-TripAdvisor-API-Key": self.tripadvisor_api_key
        }
        params = {
            "query": city,
            "category": "attractions"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                attractions = []
                for item in data.get("data", [])[:20]:  # 限制返回20个
                    attractions.append({
                        "name": item.get("name", ""),
                        "type": item.get("category", "attraction"),
                        "address": item.get("address", ""),
                        "latitude": item.get("latitude"),
                        "longitude": item.get("longitude"),
                        "rating": item.get("rating", 4.0),
                        "price_range": item.get("price_level", "$"),
                        "description": item.get("description", ""),
                        "tags": item.get("tags", [])
                    })
                return attractions
        except Exception as e:
            logger.error(f"TripAdvisor API错误: {e}")
        
        return []
    
    def search_flights(self, origin: str, destination: str, departure_date: str,
                      return_date: str = None, adults: int = 1) -> List[Dict]:
        """
        搜索航班
        
        Args:
            origin: 出发城市代码
            destination: 目的地城市代码
            departure_date: 出发日期 (YYYY-MM-DD)
            return_date: 返程日期 (可选)
            adults: 成人数量
        
        Returns:
            航班列表
        """
        flights = []
        
        # 使用Amadeus API搜索航班
        if self.amadeus_api_key:
            try:
                flights = self._search_flights_amadeus(origin, destination, departure_date, return_date, adults)
                if flights:
                    return flights
            except Exception as e:
                logger.warning(f"Amadeus API调用失败: {e}")
        
        return []
    
    def _search_flights_amadeus(self, origin: str, destination: str, departure_date: str,
                               return_date: str, adults: int) -> List[Dict]:
        """使用Amadeus API搜索航班"""
        token = self._get_amadeus_token()
        if not token:
            return []
        
        url = f"{self.amadeus_api_url}/shopping/flight-offers"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "max": 10  # 限制返回10个结果
        }
        
        if return_date:
            params["returnDate"] = return_date
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                flights = []
                for offer in data.get("data", []):
                    flight = offer.get("itineraries", [{}])[0]
                    segments = flight.get("segments", [])
                    if segments:
                        first_segment = segments[0]
                        last_segment = segments[-1]
                        flights.append({
                            "price": offer.get("price", {}).get("total", "0"),
                            "currency": offer.get("price", {}).get("currency", "USD"),
                            "departure": {
                                "airport": first_segment.get("departure", {}).get("iataCode", ""),
                                "time": first_segment.get("departure", {}).get("at", "")
                            },
                            "arrival": {
                                "airport": last_segment.get("arrival", {}).get("iataCode", ""),
                                "time": last_segment.get("arrival", {}).get("at", "")
                            },
                            "duration": flight.get("duration", ""),
                            "stops": len(segments) - 1
                        })
                return flights
        except Exception as e:
            logger.error(f"Amadeus航班搜索错误: {e}")
        
        return []

