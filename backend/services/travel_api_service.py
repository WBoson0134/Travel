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
        
        # 尝试使用 MCP 客户端（优先）
        try:
            from backend.services.mcp_travel_client import MCPTravelClient
            self.mcp_client = MCPTravelClient()
            logger.info("TravelAPIService: MCP 客户端已启用")
        except Exception as e:
            logger.warning(f"TravelAPIService: MCP 客户端初始化失败: {e}")
            self.mcp_client = None
        
    def _get_amadeus_token(self) -> Optional[str]:
        """获取Amadeus API访问令牌"""
        if not self.amadeus_api_key or not self.amadeus_api_secret:
            logger.warning("Amadeus API key 或 secret 未配置")
            return None
        
        try:
            # Amadeus API token 端点（注意：不需要 /v1 前缀）
            base_url = self.amadeus_api_url.rstrip("/v1").rstrip("/")
            url = f"{base_url}/v1/security/oauth2/token"
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "client_credentials",
                "client_id": self.amadeus_api_key,
                "client_secret": self.amadeus_api_secret
            }
            
            logger.info(f"请求 Amadeus token: {url}")
            response = requests.post(url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    logger.info("成功获取 Amadeus token")
                    return token
                else:
                    logger.error("Amadeus token 响应中未找到 access_token")
            else:
                logger.error(f"Amadeus token 请求失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Amadeus token 请求异常: {e}")
        except Exception as e:
            logger.error(f"获取Amadeus token失败: {e}", exc_info=True)
        
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
        
        # 1. 优先使用 MCP 客户端
        if self.mcp_client:
            try:
                hotels = self.mcp_client.search_hotels(city, check_in, check_out, adults, rooms)
                if hotels:
                    logger.info(f"从 MCP 客户端获取到 {len(hotels)} 个酒店")
                    return hotels
            except Exception as e:
                logger.warning(f"MCP 客户端调用失败: {e}")
        
        # 2. 尝试使用Booking.com API
        if self.booking_api_key:
            try:
                hotels = self._search_hotels_booking(city, check_in, check_out, adults, rooms)
                if hotels:
                    return hotels
            except Exception as e:
                logger.warning(f"Booking.com API调用失败: {e}")
        
        # 3. 尝试使用Amadeus API
        if self.amadeus_api_key and self.amadeus_api_secret:
            try:
                hotels = self._search_hotels_amadeus(city, check_in, check_out, adults, rooms)
                if hotels:
                    logger.info(f"从 Amadeus API 获取到 {len(hotels)} 个酒店")
                    return hotels
            except Exception as e:
                logger.warning(f"Amadeus API调用失败: {e}", exc_info=True)
        
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
            logger.info(f"搜索 Amadeus 酒店: city={city}, cityCode={city_code}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                hotels_data = data.get("data", [])
                logger.info(f"Amadeus 返回 {len(hotels_data)} 个酒店")
                
                hotels = []
                for hotel in hotels_data[:10]:  # 限制返回10个
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
            else:
                logger.error(f"Amadeus 酒店搜索失败: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Amadeus API 请求异常: {e}")
        except Exception as e:
            logger.error(f"Amadeus API错误: {e}", exc_info=True)
        
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
            logger.info(f"获取 Amadeus 城市代码: {city}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                locations = data.get("data", [])
                if locations:
                    city_code = locations[0].get("iataCode")
                    logger.info(f"找到城市代码: {city_code}")
                    return city_code
                else:
                    logger.warning(f"未找到城市 {city} 的代码")
            else:
                logger.error(f"获取城市代码失败: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"获取城市代码请求异常: {e}")
        except Exception as e:
            logger.error(f"获取城市代码失败: {e}", exc_info=True)
        
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
        
        # 1. 优先使用 MCP 客户端
        if self.mcp_client:
            try:
                attractions = self.mcp_client.search_attractions(city, preferences)
                if attractions:
                    logger.info(f"从 MCP 客户端获取到 {len(attractions)} 个景点")
                    return attractions
            except Exception as e:
                logger.warning(f"MCP 客户端调用失败: {e}")
        
        # 2. 尝试使用TripAdvisor API
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
        
        # 1. 优先使用 MCP 客户端
        if self.mcp_client:
            try:
                flights = self.mcp_client.search_flights(origin, destination, departure_date, return_date, adults)
                if flights:
                    logger.info(f"从 MCP 客户端获取到 {len(flights)} 个航班")
                    return flights
            except Exception as e:
                logger.warning(f"MCP 客户端调用失败: {e}")
        
        # 2. 使用Amadeus API搜索航班
        if self.amadeus_api_key and self.amadeus_api_secret:
            try:
                flights = self._search_flights_amadeus(origin, destination, departure_date, return_date, adults)
                if flights:
                    logger.info(f"从 Amadeus API 获取到 {len(flights)} 个航班")
                    return flights
            except Exception as e:
                logger.warning(f"Amadeus API调用失败: {e}", exc_info=True)
        
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
            logger.info(f"搜索 Amadeus 航班: {origin} -> {destination}, {departure_date}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get("data", [])
                logger.info(f"Amadeus 返回 {len(offers)} 个航班")
                
                flights = []
                for offer in offers:
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
            else:
                logger.error(f"Amadeus 航班搜索失败: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Amadeus 航班搜索请求异常: {e}")
        except Exception as e:
            logger.error(f"Amadeus航班搜索错误: {e}", exc_info=True)
        
        return []

