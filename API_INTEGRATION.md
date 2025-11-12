# 外部API集成文档

本文档说明如何配置和使用外部旅游API以及AI助手功能。

## 配置外部API

在项目根目录的 `.env` 文件中添加以下配置：

```env
# 外部旅游API配置
# Booking.com API (需要合作伙伴认证)
BOOKING_API_KEY=your_booking_api_key
BOOKING_API_URL=https://api.booking.com/v1

# Amadeus API (用于酒店和航班搜索)
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_api_secret
AMADEUS_API_URL=https://api.amadeus.com/v1

# TripAdvisor API (用于景点搜索)
TRIPADVISOR_API_KEY=your_tripadvisor_api_key
TRIPADVISOR_API_URL=https://api.tripadvisor.com/api

# AI API配置（用于AI助手）
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1
# 或使用Dify
DIFY_API_KEY=your_dify_api_key
DIFY_API_BASE=https://api.dify.ai/v1
```

## 获取API密钥

### 1. Amadeus API
1. 访问 [Amadeus for Developers](https://developers.amadeus.com/)
2. 注册账户并创建应用
3. 获取 API Key 和 API Secret

### 2. 
1. 访问 [TripAdvisor Content API](https://developer.tripadvisor.com/)
2. 注册并申请API访问权限
3. 获取 API Key

### 3. Booking.com API
- 注意：Booking.com API 通常需要成为合作伙伴
- 访问 [Booking.com Affiliate Partner](https://www.booking.com/affiliate-program/) 了解更多

## API端点

### 1. AI助手对话

**POST** `/api/ai/chat`

与AI助手进行对话。

**请求体：**
```json
{
  "user_id": "user123",
  "message": "我想去北京旅游，有什么推荐吗？",
  "context": {
    "city": "北京",
    "days": 3,
    "preferences": ["文化", "历史"]
  }
}
```

**响应：**
```json
{
  "reply": "北京是一个充满历史文化的城市，我推荐您参观...",
  "suggestions": ["搜索酒店", "查看景点", "生成行程"]
}
```

### 2. 获取对话历史

**GET** `/api/ai/history/<user_id>`

获取指定用户的对话历史。

**响应：**
```json
{
  "history": [
    {
      "role": "user",
      "content": "我想去北京旅游"
    },
    {
      "role": "assistant",
      "content": "北京是一个很好的选择..."
    }
  ]
}
```

### 3. 清除对话历史

**DELETE** `/api/ai/history/<user_id>`

清除指定用户的对话历史。

### 4. 搜索酒店

**GET** `/api/travel/hotels`

搜索酒店信息。

**查询参数：**
- `city` (必填): 城市名称
- `check_in` (可选): 入住日期 YYYY-MM-DD
- `check_out` (可选): 退房日期 YYYY-MM-DD
- `adults` (可选): 成人数量，默认2
- `rooms` (可选): 房间数量，默认1

**示例：**
```
GET /api/travel/hotels?city=北京&check_in=2024-06-01&check_out=2024-06-03&adults=2
```

**响应：**
```json
{
  "city": "北京",
  "count": 10,
  "hotels": [
    {
      "name": "北京饭店",
      "hotel_id": "12345",
      "latitude": 39.9042,
      "longitude": 116.4074,
      "rating": 4.5,
      "price_range": "$$$",
      "address": "北京市东城区..."
    }
  ]
}
```

### 5. 搜索航班

**GET** `/api/travel/flights`

搜索航班信息。

**查询参数：**
- `origin` (必填): 出发城市代码，如：PEK
- `destination` (必填): 目的地城市代码，如：SHA
- `departure_date` (必填): 出发日期 YYYY-MM-DD
- `return_date` (可选): 返程日期 YYYY-MM-DD
- `adults` (可选): 成人数量，默认1

**示例：**
```
GET /api/travel/flights?origin=PEK&destination=SHA&departure_date=2024-06-01&adults=1
```

**响应：**
```json
{
  "origin": "PEK",
  "destination": "SHA",
  "departure_date": "2024-06-01",
  "count": 5,
  "flights": [
    {
      "price": "800",
      "currency": "CNY",
      "departure": {
        "airport": "PEK",
        "time": "2024-06-01T08:00:00"
      },
      "arrival": {
        "airport": "SHA",
        "time": "2024-06-01T10:30:00"
      },
      "duration": "PT2H30M",
      "stops": 0
    }
  ]
}
```

### 6. 生成行程（使用外部API）

**POST** `/api/generate_itinerary`

生成行程计划，现在会从外部API获取景点信息。

**请求体：**
```json
{
  "city": "北京",
  "days": 3,
  "preferences": ["文化", "历史"],
  "pace": "中庸",
  "transport_mode": "driving"
}
```

**响应：**
与之前相同，但现在景点数据来自外部API。

## 使用说明

1. **配置API密钥**：在 `.env` 文件中配置所需的API密钥。

2. **调用API**：系统会自动尝试使用配置的API。如果没有配置或API调用失败，会返回空结果或使用回退方案。

3. **AI助手**：AI助手可以回答用户关于旅游的各种问题，并维护对话历史。

4. **外部数据**：所有旅游数据（酒店、景点、航班）都从外部API获取，不再使用本地存储的数据。

## 注意事项

1. **API限制**：不同的API提供商有不同的调用限制和定价策略，请查看相应的文档。

2. **错误处理**：如果外部API调用失败，系统会记录警告并返回空结果。在生产环境中，建议实现更完善的错误处理和重试机制。

3. **数据格式**：不同API返回的数据格式可能不同，系统会尝试统一格式，但某些字段可能因API而异。

4. **认证**：某些API（如Booking.com）需要特殊的合作伙伴认证，可能需要额外的申请流程。

