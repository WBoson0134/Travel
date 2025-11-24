# MCP 集成方案

## 当前状态分析

目前你的系统：
- ✅ 已有基础的 MCP 架构（`tools/mcp_server.py` 和 `backend/services/mcp_client.py`）
- ✅ 但只是封装了内部服务，没有真正使用外部 MCP
- ⚠️ 生成质量较低，主要依赖本地 POI 数据和基础 LLM

## 推荐的 MCP 工具

### 1. **Google Places MCP** (推荐 ⭐⭐⭐⭐⭐)
- **功能**：获取真实景点数据、评分、评论、营业时间
- **优势**：数据准确、覆盖全球、实时更新
- **集成难度**：中等
- **成本**：需要 Google Cloud API Key（有免费额度）

### 2. **Wikipedia MCP** (推荐 ⭐⭐⭐⭐)
- **功能**：获取景点历史、文化背景、详细描述
- **优势**：内容丰富、免费、多语言
- **集成难度**：简单
- **成本**：免费

### 3. **Weather MCP** (推荐 ⭐⭐⭐⭐)
- **功能**：获取目的地天气信息
- **优势**：帮助规划户外活动、建议最佳出行时间
- **集成难度**：简单
- **成本**：免费（如 OpenWeatherMap）

### 4. **Translation MCP** (推荐 ⭐⭐⭐)
- **功能**：多语言支持
- **优势**：国际化、本地化内容
- **集成难度**：简单
- **成本**：免费（如 Google Translate API）

### 5. **Currency Exchange MCP** (推荐 ⭐⭐⭐)
- **功能**：实时汇率、价格转换
- **优势**：帮助预算规划
- **集成难度**：简单
- **成本**：免费（如 exchangerate-api.com）

## 集成方案

### 方案 A：使用官方 MCP SDK 连接外部服务器（推荐）

```python
# 安装依赖
pip install mcp
```

**优点**：
- 标准化接口
- 支持多个 MCP 服务器
- 易于维护

**缺点**：
- 需要配置外部 MCP 服务器
- 可能需要网络连接

### 方案 B：直接调用外部 API（快速实现）

**优点**：
- 实现简单
- 不依赖外部 MCP 服务器
- 完全控制

**缺点**：
- 需要自己封装
- 代码耦合度较高

## 推荐实现路径

### 阶段 1：快速提升（1-2天）
1. **集成 Google Places API**
   - 替换占位 POI 数据
   - 获取真实景点信息、评分、照片
   - 提升数据质量 80%

2. **集成 Wikipedia API**
   - 为景点添加文化背景
   - 丰富描述内容
   - 提升内容深度

### 阶段 2：增强体验（3-5天）
3. **集成 Weather API**
   - 根据天气调整行程
   - 建议最佳出行时间

4. **优化 LLM 提示词**
   - 使用真实数据增强提示词
   - 让 AI 基于真实信息生成

### 阶段 3：高级功能（可选）
5. **集成多个 MCP 服务器**
   - 使用官方 MCP SDK
   - 构建工具链（Places → Weather → Wikipedia）

## 具体实现建议

### 1. 优先集成 Google Places API

**为什么**：
- 数据最准确、最全面
- 有免费额度（每月 $200）
- 覆盖全球主要城市

**实现步骤**：
1. 在 `.env` 添加 `GOOGLE_PLACES_API_KEY`
2. 创建 `backend/services/google_places_service.py`
3. 修改 `POIService` 优先使用 Google Places
4. 更新 `AIService` 使用真实数据

### 2. 增强 LLM 提示词

**当前问题**：
- 提示词中只有占位数据
- AI 无法基于真实信息生成

**解决方案**：
- 在调用 LLM 前，先获取真实 POI 数据
- 将真实数据（名称、评分、地址、描述）放入提示词
- 让 AI 基于真实信息生成行程

### 3. 使用 MCP 工具链

**架构**：
```
用户请求 → MCP Client → 
  ├─ Google Places MCP (获取景点)
  ├─ Wikipedia MCP (获取背景)
  ├─ Weather MCP (获取天气)
  └─ LLM (基于真实数据生成)
```

## 代码示例

### 示例 1：集成 Google Places

```python
# backend/services/google_places_service.py
import requests
from backend.config import Config

class GooglePlacesService:
    def __init__(self):
        self.api_key = Config.GOOGLE_PLACES_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def search_places(self, city: str, query: str, type_filter: str = "tourist_attraction"):
        """搜索景点"""
        url = f"{self.base_url}/textsearch/json"
        params = {
            "query": f"{query} in {city}",
            "type": type_filter,
            "key": self.api_key,
            "language": "zh-CN"
        }
        response = requests.get(url, params=params)
        return response.json()
    
    def get_place_details(self, place_id: str):
        """获取景点详情"""
        url = f"{self.base_url}/details/json"
        params = {
            "place_id": place_id,
            "key": self.api_key,
            "language": "zh-CN",
            "fields": "name,rating,formatted_address,geometry,photos,reviews,opening_hours"
        }
        response = requests.get(url, params=params)
        return response.json()
```

### 示例 2：增强 POI Service

```python
# 修改 backend/services/poi_service.py
def generate_itinerary(self, ...):
    # 1. 先尝试从 Google Places 获取真实数据
    if self.google_places_service and self.google_places_service.api_key:
        places = self.google_places_service.search_places(city, "景点")
        if places.get('results'):
            # 使用真实数据
            return self._build_itinerary_from_places(places['results'], days)
    
    # 2. 回退到本地数据
    return self._generate_placeholder_itinerary(...)
```

## 下一步行动

1. **立即开始**：集成 Google Places API（最大收益）
2. **本周完成**：集成 Wikipedia + Weather
3. **下周优化**：使用 MCP SDK 重构架构

## 资源链接

- [Google Places API 文档](https://developers.google.com/maps/documentation/places/web-service)
- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

