#!/usr/bin/env python3
"""MCP 旅游服务服务器

提供以下工具：
- search_attractions: 搜索景点
- search_hotels: 搜索酒店
- search_flights: 搜索航班
- geocode_address: 地理编码
- calculate_route: 计算路线
- get_places_nearby: 获取附近地点

使用现有的 API 服务（Amadeus、Geoapify）
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise ImportError(
        'model-context-protocol package not found. Install via '
        '"pip install git+https://github.com/modelcontextprotocol/python.git#egg=model-context-protocol"'
    ) from exc

from backend.services.travel_api_service import TravelAPIService
from backend.services.map_service import MapService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 创建 MCP 服务器
server = FastMCP("travel-mcp-server")

# 初始化服务
travel_service = TravelAPIService()
map_service = MapService()


@server.tool()
async def search_attractions(
    city: str,
    preferences: str | list[str] | None = None,
) -> str:
    """搜索景点/POI
    
    Parameters
    ----------
    city: str
        城市名称（必填）
    preferences: str | list[str]
        偏好列表，如 "文化,历史" 或 ["文化", "历史"]
    
    Returns
    -------
    str
        JSON 字符串，包含景点列表
    """
    logger.info(f"MCP tool search_attractions called: city={city}, preferences={preferences}")
    
    # 解析偏好
    if isinstance(preferences, str):
        pref_list = [p.strip() for p in preferences.split(",") if p.strip()]
    elif isinstance(preferences, list):
        pref_list = [str(p).strip() for p in preferences if p]
    else:
        pref_list = []
    
    try:
        attractions = travel_service.search_attractions(city, pref_list)
        result = {
            "city": city,
            "count": len(attractions),
            "attractions": attractions
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"搜索景点失败: {e}", exc_info=True)
        return json.dumps({"error": str(e), "city": city, "count": 0, "attractions": []}, ensure_ascii=False)


@server.tool()
async def search_hotels(
    city: str,
    check_in: str | None = None,
    check_out: str | None = None,
    adults: int = 2,
    rooms: int = 1,
) -> str:
    """搜索酒店
    
    Parameters
    ----------
    city: str
        城市名称（必填）
    check_in: str
        入住日期 YYYY-MM-DD（可选）
    check_out: str
        退房日期 YYYY-MM-DD（可选）
    adults: int
        成人数量，默认2
    rooms: int
        房间数量，默认1
    
    Returns
    -------
    str
        JSON 字符串，包含酒店列表
    """
    logger.info(f"MCP tool search_hotels called: city={city}, check_in={check_in}, check_out={check_out}")
    
    try:
        hotels = travel_service.search_hotels(city, check_in, check_out, adults, rooms)
        result = {
            "city": city,
            "count": len(hotels),
            "hotels": hotels
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"搜索酒店失败: {e}", exc_info=True)
        return json.dumps({"error": str(e), "city": city, "count": 0, "hotels": []}, ensure_ascii=False)


@server.tool()
async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
) -> str:
    """搜索航班
    
    Parameters
    ----------
    origin: str
        出发城市代码（必填，如：PEK）
    destination: str
        目的地城市代码（必填，如：SHA）
    departure_date: str
        出发日期 YYYY-MM-DD（必填）
    return_date: str
        返程日期 YYYY-MM-DD（可选）
    adults: int
        成人数量，默认1
    
    Returns
    -------
    str
        JSON 字符串，包含航班列表
    """
    logger.info(f"MCP tool search_flights called: {origin} -> {destination}, {departure_date}")
    
    try:
        flights = travel_service.search_flights(origin, destination, departure_date, return_date, adults)
        result = {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "count": len(flights),
            "flights": flights
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"搜索航班失败: {e}", exc_info=True)
        return json.dumps({"error": str(e), "count": 0, "flights": []}, ensure_ascii=False)


@server.tool()
async def geocode_address(address: str) -> str:
    """地理编码：将地址转换为坐标
    
    Parameters
    ----------
    address: str
        地址（必填）
    
    Returns
    -------
    str
        JSON 字符串，包含坐标和格式化地址
    """
    logger.info(f"MCP tool geocode_address called: {address}")
    
    try:
        result = map_service.geocode_address(address)
        if result:
            return json.dumps(result, ensure_ascii=False)
        else:
            return json.dumps({"error": "未找到地址", "address": address}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"地理编码失败: {e}", exc_info=True)
        return json.dumps({"error": str(e), "address": address}, ensure_ascii=False)


@server.tool()
async def calculate_route(
    from_lat: float,
    from_lng: float,
    to_lat: float,
    to_lng: float,
    mode: str = "driving",
) -> str:
    """计算路线
    
    Parameters
    ----------
    from_lat: float
        起点纬度
    from_lng: float
        起点经度
    to_lat: float
        终点纬度
    to_lng: float
        终点经度
    mode: str
        交通方式：driving/walking/transit/bicycling，默认driving
    
    Returns
    -------
    str
        JSON 字符串，包含路线信息（距离、时间）
    """
    logger.info(f"MCP tool calculate_route called: ({from_lat}, {from_lng}) -> ({to_lat}, {to_lng}), mode={mode}")
    
    try:
        result = map_service.calculate_route(from_lat, from_lng, to_lat, to_lng, mode)
        if result:
            return json.dumps(result, ensure_ascii=False)
        else:
            return json.dumps({"error": "无法计算路线"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"计算路线失败: {e}", exc_info=True)
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@server.tool()
async def get_places_nearby(
    lat: float,
    lng: float,
    radius: int = 1000,
    type_filter: str | None = None,
) -> str:
    """获取附近地点
    
    Parameters
    ----------
    lat: float
        纬度
    lng: float
        经度
    radius: int
        搜索半径（米），默认1000
    type_filter: str
        地点类型过滤（可选）
    
    Returns
    -------
    str
        JSON 字符串，包含附近地点列表
    """
    logger.info(f"MCP tool get_places_nearby called: ({lat}, {lng}), radius={radius}")
    
    try:
        places = map_service.get_places_nearby(lat, lng, radius, type_filter)
        result = {
            "location": {"latitude": lat, "longitude": lng},
            "radius": radius,
            "count": len(places),
            "places": places
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"获取附近地点失败: {e}", exc_info=True)
        return json.dumps({"error": str(e), "count": 0, "places": []}, ensure_ascii=False)


if __name__ == "__main__":
    logger.info("Starting MCP travel server with tools: search_attractions, search_hotels, search_flights, geocode_address, calculate_route, get_places_nearby")
    server.run()

