# MCP 旅游服务器使用指南

## 已完成的工作

✅ 修复了 Amadeus API 调用问题（添加详细错误日志）
✅ 创建了 MCP 旅游服务器 (`tools/mcp_travel_server.py`)
✅ 创建了 MCP 客户端 (`backend/services/mcp_travel_client.py`)

## MCP 服务器提供的工具

1. **search_attractions** - 搜索景点
2. **search_hotels** - 搜索酒店
3. **search_flights** - 搜索航班
4. **geocode_address** - 地理编码
5. **calculate_route** - 计算路线
6. **get_places_nearby** - 获取附近地点

## 启动 MCP 服务器

### 方式 1：作为独立进程运行（用于测试）

```bash
cd /path/to/Travel
PYTHONPATH=. python3 tools/mcp_travel_server.py
```

### 方式 2：通过 MCP 客户端调用（推荐）

客户端会自动导入工具函数，无需单独启动服务器。

## 使用 MCP 客户端

```python
from backend.services.mcp_travel_client import MCPTravelClient

client = MCPTravelClient()

# 搜索景点
attractions = client.search_attractions("北京", ["文化", "历史"])

# 搜索酒店
hotels = client.search_hotels("北京", "2024-12-01", "2024-12-03")

# 搜索航班
flights = client.search_flights("PEK", "SHA", "2024-12-01")

# 地理编码
location = client.geocode_address("北京市天安门广场")

# 计算路线
route = client.calculate_route(39.9042, 116.4074, 39.9163, 116.3972, "driving")

# 获取附近地点
places = client.get_places_nearby(39.9042, 116.4074, 1000)
```

## 集成到现有代码

### 更新 POIService 使用 MCP

可以修改 `backend/services/poi_service.py`，使用 MCP 客户端：

```python
from backend.services.mcp_travel_client import MCPTravelClient

class POIService:
    def __init__(self):
        self.mcp_client = MCPTravelClient()
        # ... 其他初始化
    
    def get_pois_by_city(self, city: str, preferences: List[str] = None):
        # 使用 MCP 客户端搜索景点
        attractions = self.mcp_client.search_attractions(city, preferences)
        return attractions
```

## 测试

### 测试 MCP 服务器

```bash
# 直接运行服务器
PYTHONPATH=. python3 tools/mcp_travel_server.py
```

### 测试 MCP 客户端

```python
from backend.services.mcp_travel_client import MCPTravelClient

client = MCPTravelClient()
result = client.search_attractions("北京", ["文化"])
print(result)
```

## 注意事项

1. **API Key 配置**：确保 `.env` 文件中配置了：
   - `AMADEUS_API_KEY`
   - `AMADEUS_API_SECRET`
   - `GEOAPIFY_API_KEY`

2. **错误处理**：MCP 客户端会自动处理错误，返回空列表或 None

3. **日志**：查看后端日志了解详细的调用情况

## 下一步

1. 将 MCP 客户端集成到现有服务中
2. 测试所有工具是否正常工作
3. 优化错误处理和日志记录

