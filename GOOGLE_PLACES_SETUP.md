# Google Places API 集成指南

## 已完成的工作

✅ 创建了 `GooglePlacesService` 服务类
✅ 集成到 `POIService`，优先使用 Google Places 数据
✅ 自动回退机制（Google Places → 其他API → 本地数据）

## 配置步骤

### 1. 获取 Google Places API Key

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 **Places API**：
   - 导航到 "APIs & Services" > "Library"
   - 搜索 "Places API"
   - 点击 "Enable"
4. 创建 API Key：
   - 导航到 "APIs & Services" > "Credentials"
   - 点击 "Create Credentials" > "API Key"
   - 复制 API Key

### 2. 配置 API Key

在你的 `.env` 文件中添加（如果还没有）：

```env
GOOGLE_MAPS_API_KEY=your_google_places_api_key_here
```

**注意**：Google Places API 使用与 Google Maps API 相同的 API Key，所以如果你已经有 `GOOGLE_MAPS_API_KEY`，就不需要额外配置。

### 3. 设置 API 限制（推荐）

为了安全，建议限制 API Key 的使用：

1. 在 Google Cloud Console 中，点击你的 API Key
2. 在 "API restrictions" 中，选择 "Restrict key"
3. 只选择 "Places API"
4. 在 "Application restrictions" 中，可以设置 IP 限制或 HTTP referrer 限制

### 4. 重启后端服务

```bash
# 停止当前服务
pkill -f "python.*app_flask.py"

# 重新启动
cd /path/to/Travel
PYTHONPATH=. python3 backend/app_flask.py
```

## 使用效果

### 之前（占位数据）
```json
{
  "name": "北京 精选体验 1",
  "type": "体验",
  "description": "占位活动，等待AI进一步优化。",
  "rating": 4.5
}
```

### 现在（真实数据）
```json
{
  "name": "故宫博物院",
  "type": "博物馆",
  "address": "北京市东城区景山前街4号",
  "rating": 4.7,
  "user_ratings_total": 125000,
  "price_range": "$$",
  "tags": ["热门", "推荐", "文化"]
}
```

## API 费用

- **免费额度**：每月 $200（约 14,000 次 Text Search 请求）
- **超出后**：$0.032 每次 Text Search 请求
- **详情**：查看 [Google Places API 定价](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing)

## 功能特性

### 1. 智能搜索
- 根据城市和偏好自动搜索相关景点
- 支持偏好关键词映射（文化、历史、美食等）

### 2. 数据丰富
- 真实景点名称和地址
- 用户评分和评论数
- 价格级别估算
- 地理位置坐标

### 3. 自动回退
- Google Places 不可用时，自动使用其他数据源
- 确保服务稳定性

## 测试

测试 Google Places 集成是否正常工作：

```bash
# 测试 API
curl -X POST http://localhost:5001/api/generate_trip \
  -H "Content-Type: application/json" \
  -d '{
    "city": "北京",
    "days": 3,
    "preferences": ["文化", "历史"]
  }'
```

检查日志：
```bash
tail -f backend_server.log | grep -i "google places"
```

应该看到：
```
INFO: Google Places 服务已启用
INFO: 从 Google Places 获取到 X 个景点
```

## 下一步优化建议

### 1. 添加景点详情获取（可选）
当前只获取了基本信息，可以调用 `get_place_details()` 获取：
- 详细评论
- 营业时间
- 网站链接
- 电话号码

### 2. 集成 Wikipedia（推荐）
为景点添加文化背景和历史信息，让 AI 生成更丰富的内容。

### 3. 缓存优化
Google Places 数据可以缓存，减少 API 调用：
- 相同城市+偏好的查询可以缓存 24 小时
- 景点详情可以缓存更长时间

### 4. 批量获取详情
如果需要更详细的景点信息，可以批量调用 `get_place_details()`，但要注意 API 配额。

## 故障排查

### 问题：没有获取到景点数据

**检查清单**：
1. ✅ API Key 是否正确配置在 `.env` 文件中
2. ✅ Places API 是否已启用
3. ✅ API Key 是否有使用限制（IP/Referrer）
4. ✅ 查看后端日志中的错误信息

### 问题：API 配额超限

**解决方案**：
1. 检查 Google Cloud Console 中的配额使用情况
2. 考虑添加缓存减少 API 调用
3. 升级到付费计划

### 问题：某些城市没有结果

**可能原因**：
1. 城市名称需要更精确（如 "北京市" 而不是 "北京"）
2. 该地区 Google Places 数据较少
3. 会自动回退到其他数据源

## 相关文件

- `backend/services/google_places_service.py` - Google Places 服务实现
- `backend/services/poi_service.py` - POI 服务（已集成 Google Places）
- `MCP_INTEGRATION_PLAN.md` - MCP 集成总体方案

