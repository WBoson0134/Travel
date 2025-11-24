"""
MCP 旅游服务客户端
通过 stdio 连接到 MCP 服务器，调用旅游相关工具
"""
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPTravelClient:
    """MCP 旅游服务客户端"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.server_process = None
        self.server_path = Path(__file__).resolve().parent.parent.parent / "tools" / "mcp_travel_server.py"
        
    def _call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """调用 MCP 工具（简化实现：直接导入工具函数）"""
        try:
            # 直接导入工具函数（简化实现）
            sys.path.insert(0, str(self.server_path.parent))
            from tools.mcp_travel_server import (
                search_attractions,
                search_hotels,
                search_flights,
                geocode_address,
                calculate_route,
                get_places_nearby,
            )
            
            tool_map = {
                "search_attractions": search_attractions,
                "search_hotels": search_hotels,
                "search_flights": search_flights,
                "geocode_address": geocode_address,
                "calculate_route": calculate_route,
                "get_places_nearby": get_places_nearby,
            }
            
            if tool_name not in tool_map:
                raise ValueError(f"未知工具: {tool_name}")
            
            tool_func = tool_map[tool_name]
            result_str = tool_func(**kwargs)
            return json.loads(result_str)
            
        except Exception as e:
            self.logger.error(f"调用 MCP 工具 {tool_name} 失败: {e}", exc_info=True)
            return {"error": str(e)}
    
    def search_attractions(self, city: str, preferences: Optional[List[str]] = None) -> List[Dict]:
        """搜索景点"""
        pref_str = ",".join(preferences) if preferences else None
        result = self._call_tool("search_attractions", city=city, preferences=pref_str)
        if "error" in result:
            return []
        return result.get("attractions", [])
    
    def search_hotels(self, city: str, check_in: str = None, check_out: str = None,
                     adults: int = 2, rooms: int = 1) -> List[Dict]:
        """搜索酒店"""
        result = self._call_tool("search_hotels", city=city, check_in=check_in, 
                                 check_out=check_out, adults=adults, rooms=rooms)
        if "error" in result:
            return []
        return result.get("hotels", [])
    
    def search_flights(self, origin: str, destination: str, departure_date: str,
                      return_date: str = None, adults: int = 1) -> List[Dict]:
        """搜索航班"""
        result = self._call_tool("search_flights", origin=origin, destination=destination,
                                 departure_date=departure_date, return_date=return_date, adults=adults)
        if "error" in result:
            return []
        return result.get("flights", [])
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """地理编码"""
        result = self._call_tool("geocode_address", address=address)
        if "error" in result:
            return None
        return result
    
    def calculate_route(self, from_lat: float, from_lng: float, to_lat: float, to_lng: float,
                       mode: str = "driving") -> Optional[Dict]:
        """计算路线"""
        result = self._call_tool("calculate_route", from_lat=from_lat, from_lng=from_lng,
                                 to_lat=to_lat, to_lng=to_lng, mode=mode)
        if "error" in result:
            return None
        return result
    
    def get_places_nearby(self, lat: float, lng: float, radius: int = 1000,
                         type_filter: str = None) -> List[Dict]:
        """获取附近地点"""
        result = self._call_tool("get_places_nearby", lat=lat, lng=lng, radius=radius,
                                type_filter=type_filter)
        if "error" in result:
            return []
        return result.get("places", [])

