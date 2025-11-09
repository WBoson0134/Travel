from flask import Blueprint, request, jsonify, send_file
from backend.models import db, Trip, DayPlan, Activity, Route
from backend.services.ai_service import AIService
from backend.services.map_service import MapService
from backend.services.price_service import PriceService
from backend.services.export_service import ExportService
from backend.services.poi_service import POIService
from backend.services.travel_api_service import TravelAPIService
from backend.services.ai_assistant_service import AIAssistantService
from backend.schemas import (
    ItineraryRequest, ItineraryResponse, ErrorResponse,
    ActivityResponse, DayPlanResponse
)
from backend.config import Config
from datetime import datetime, timedelta
from pydantic import ValidationError
import json
import io
import requests

api = Blueprint('api', __name__, url_prefix='/api')

ai_service = AIService()
map_service = MapService()
price_service = PriceService()
export_service = ExportService()
poi_service = POIService()
travel_api_service = TravelAPIService()
ai_assistant_service = AIAssistantService()

@api.route('/trips/generate', methods=['POST'])
def generate_trip():
    """生成行程"""
    try:
        data = request.json
        city = data.get('city')
        days = data.get('days')
        preferences = data.get('preferences', [])
        pace = data.get('pace', '中庸')
        transport_mode = data.get('transport_mode', 'driving')
        priority = data.get('priority', '效率优先')
        
        if not city or not days:
            return jsonify({'error': '城市和天数为必填项'}), 400
        
        # 使用AI生成行程
        trip_plan = ai_service.generate_trip_plan(
            city, days, preferences, pace, transport_mode, priority
        )
        
        # 创建Trip记录
        trip = Trip(
            city=city,
            days=days,
            preferences=json.dumps(preferences, ensure_ascii=False),
            pace=pace,
            transport_mode=transport_mode,
            priority=priority
        )
        db.session.add(trip)
        db.session.flush()
        
        # 处理地理编码和路线
        start_date = datetime.now().date()
        
        for day_data in trip_plan.get('days', []):
            day_plan = DayPlan(
                trip_id=trip.id,
                day_number=day_data['day_number'],
                date=start_date + timedelta(days=day_data['day_number'] - 1),
                description=day_data.get('description')
            )
            db.session.add(day_plan)
            db.session.flush()
            
            # 处理活动
            for act_data in day_data.get('activities', []):
                # 地理编码
                address = act_data.get('address', '')
                location = None
                if address:
                    location = map_service.geocode_address(address)
                
                # 获取评价
                reviews = ai_service.get_reviews_summary(
                    act_data.get('name', ''), city
                )
                
                # 价格估算
                price_info = price_service.estimate_activity_price(
                    act_data.get('name', ''),
                    act_data.get('type', ''),
                    city
                )
                
                activity = Activity(
                    day_plan_id=day_plan.id,
                    name=act_data.get('name', ''),
                    type=act_data.get('type', ''),
                    address=address,
                    latitude=location['latitude'] if location else None,
                    longitude=location['longitude'] if location else None,
                    start_time=datetime.strptime(act_data.get('start_time', '09:00'), '%H:%M').time(),
                    end_time=datetime.strptime(act_data.get('end_time', '12:00'), '%H:%M').time(),
                    duration_minutes=act_data.get('duration_minutes', 180),
                    description=act_data.get('description', '') or reviews.get('summary', ''),
                    rating=reviews.get('rating', 4.5),
                    price_range=price_info.get('price_range', '$$'),
                    price_estimate=price_info.get('price_estimate', 50),
                    tags=json.dumps(reviews.get('tags', []), ensure_ascii=False),
                    order=act_data.get('order', 1)
                )
                db.session.add(activity)
                db.session.flush()
                
                # 计算与前一个活动的路线
                if activity.order > 1:
                    prev_activity = Activity.query.filter_by(
                        day_plan_id=day_plan.id,
                        order=activity.order - 1
                    ).first()
                    
                    if prev_activity and prev_activity.latitude and activity.latitude:
                        route_info = map_service.calculate_route(
                            prev_activity.latitude, prev_activity.longitude,
                            activity.latitude, activity.longitude,
                            transport_mode
                        )
                        
                        route = Route(
                            from_activity_id=prev_activity.id,
                            to_activity_id=activity.id,
                            transport_mode=transport_mode,
                            duration_minutes=route_info['duration_minutes'],
                            distance_km=route_info['distance_km'],
                            route_data=json.dumps(route_info.get('polyline'), ensure_ascii=False) if route_info.get('polyline') else None
                        )
                        db.session.add(route)
        
        db.session.commit()
        
        return jsonify(trip.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/trips/<int:trip_id>', methods=['GET'])
def get_trip(trip_id):
    """获取行程详情"""
    trip = Trip.query.get_or_404(trip_id)
    return jsonify(trip.to_dict())

@api.route('/trips/<int:trip_id>/adjust', methods=['PUT'])
def adjust_trip(trip_id):
    """调整行程"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        data = request.json
        new_requirements = data.get('requirements', '')
        
        if not new_requirements:
            return jsonify({'error': '请提供调整需求'}), 400
        
        # 获取当前行程数据
        current_trip_data = trip.to_dict()
        
        # 使用AI调整行程
        adjusted_plan = ai_service.adjust_trip(current_trip_data, new_requirements)
        
        # 更新行程（简化处理，实际应该更细致地更新）
        # 这里可以重新生成或更新现有记录
        
        return jsonify({'message': '行程已调整', 'trip': adjusted_plan}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/trips/<int:trip_id>/map', methods=['GET'])
def get_trip_map(trip_id):
    """获取行程地图数据"""
    trip = Trip.query.get_or_404(trip_id)
    
    map_data = {
        'city': trip.city,
        'activities': [],
        'routes': []
    }
    
    for day_plan in trip.days_plans:
        for activity in day_plan.activities:
            if activity.latitude and activity.longitude:
                map_data['activities'].append({
                    'id': activity.id,
                    'name': activity.name,
                    'latitude': activity.latitude,
                    'longitude': activity.longitude,
                    'type': activity.type,
                    'day': day_plan.day_number,
                    'order': activity.order
                })
    
    # 获取路线
    for day_plan in trip.days_plans:
        activities = sorted(day_plan.activities, key=lambda x: x.order)
        for i in range(len(activities) - 1):
            from_act = activities[i]
            to_act = activities[i + 1]
            
            if from_act.latitude and to_act.latitude:
                route_info = map_service.calculate_route(
                    from_act.latitude, from_act.longitude,
                    to_act.latitude, to_act.longitude,
                    trip.transport_mode
                )
                
                map_data['routes'].append({
                    'from': {
                        'id': from_act.id,
                        'name': from_act.name,
                        'lat': from_act.latitude,
                        'lng': from_act.longitude
                    },
                    'to': {
                        'id': to_act.id,
                        'name': to_act.name,
                        'lat': to_act.latitude,
                        'lng': to_act.longitude
                    },
                    'duration_minutes': route_info['duration_minutes'],
                    'distance_km': route_info['distance_km'],
                    'polyline': route_info.get('polyline')
                })
    
    return jsonify(map_data)

@api.route('/trips/<int:trip_id>/export', methods=['POST'])
def export_trip(trip_id):
    """导出行程"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        export_format = request.json.get('format', 'pdf')
        
        trip_data = trip.to_dict()
        
        if export_format == 'pdf':
            pdf_buffer = export_service.export_to_pdf(trip_data)
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'{trip.city}_{trip.days}日游行程.pdf'
            )
        elif export_format == 'ics':
            ics_data = export_service.export_to_ics(trip_data)
            return send_file(
                io.BytesIO(ics_data),
                mimetype='text/calendar',
                as_attachment=True,
                download_name=f'{trip.city}_{trip.days}日游行程.ics'
            )
        else:
            return jsonify({'error': '不支持的导出格式'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/trips', methods=['GET'])
def list_trips():
    """获取所有行程列表"""
    trips = Trip.query.order_by(Trip.created_at.desc()).all()
    return jsonify([trip.to_dict() for trip in trips])

@api.route('/generate_trip', methods=['POST'])
def generate_trip_new():
    """使用阿里云百炼生成旅行计划"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 读取 POST 请求参数
        data = request.json
        city = data.get('city')
        days = data.get('days')
        preferences = data.get('preferences', [])
        pace = data.get('pace', '中庸')
        transport = data.get('transport', 'driving')
        priority = data.get('priority', '效率优先')
        
        # 参数验证
        if not city or not days:
            return jsonify({'error': 'city and days are required'}), 400
        
        # 拼接 prompt
        preferences_str = ', '.join(preferences) if isinstance(preferences, list) else preferences
        prompt = f"为用户生成一个{days}天的{city}旅行计划，兴趣偏好包括：{preferences_str}，出行节奏是{pace}，交通方式是{transport}，优先级是{priority}。返回结构化JSON。"
        
        # 检查配置
        if not Config.OPENAI_API_KEY or not Config.OPENAI_BASE_URL:
            logger.error('OPENAI_API_KEY or OPENAI_BASE_URL not configured')
            return jsonify({'error': 'OPENAI_API_KEY and OPENAI_BASE_URL must be configured'}), 500
        
        # 调用阿里云百炼 API
        api_url = f"{Config.OPENAI_BASE_URL}/services/aigc/text-generation/generation"
        headers = {
            'Authorization': f'Bearer {Config.OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'qwen-turbo',
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            },
            'parameters': {
                'temperature': 0.7,
                'max_tokens': 2000
            }
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            # 检查响应状态码
            if response.status_code != 200:
                logger.error(f'AI API returned non-200 status: {response.status_code}, Response: {response.text}')
                return jsonify({'error': 'AI generation failed'}), 500
            
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 返回完整 JSON 响应
            return jsonify(result)
            
        except requests.exceptions.Timeout:
            logger.error('AI API request timeout', exc_info=True)
            return jsonify({'error': 'AI generation failed'}), 500
        except requests.exceptions.RequestException as e:
            logger.error(f'AI API request failed: {str(e)}', exc_info=True)
            return jsonify({'error': 'AI generation failed'}), 500
        
    except Exception as e:
        logger.error(f'Unexpected error in generate_trip: {str(e)}', exc_info=True)
        return jsonify({'error': 'AI generation failed'}), 500

@api.route('/generate_trip_dify', methods=['POST'])
def generate_trip_dify():
    """使用 Dify 生成旅行计划"""
    try:
        # 读取 POST 请求参数
        data = request.json
        city = data.get('city')
        days = data.get('days')
        preferences = data.get('preferences', [])
        
        # 参数验证
        if not city or not days:
            return jsonify({'error': 'city and days are required'}), 400
        
        # 检查配置
        if not Config.DIFY_API_KEY or not Config.DIFY_API_BASE:
            return jsonify({'error': 'DIFY_API_KEY and DIFY_API_BASE must be configured'}), 500
        
        # 调用 Dify API
        api_url = f"{Config.DIFY_API_BASE}/workflows/trigger"
        headers = {
            'Authorization': f'Bearer {Config.DIFY_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # 构建请求体
        payload = {
            'inputs': {
                'city': city,
                'days': days,
                'preferences': preferences if isinstance(preferences, list) else [preferences]
            }
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        # 返回 Dify 的 JSON 输出
        return jsonify(result)
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to generate plan with Dify'}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to generate plan with Dify'}), 500

@api.route('/generate_itinerary', methods=['POST'])
def generate_itinerary():
    """
    使用本地POI数据生成行程（简单时间估算）
    
    请求体示例:
    {
        "city": "北京",
        "days": 3,
        "preferences": ["文化", "历史"],
        "pace": "中庸",
        "transport_mode": "driving"
    }
    """
    try:
        # 使用Pydantic模型验证请求数据
        try:
            request_data = ItineraryRequest(**request.json)
        except ValidationError as e:
            # 返回验证错误
            errors = []
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                errors.append(f"{field}: {error['msg']}")
            return jsonify(ErrorResponse(
                error=f"请求参数验证失败: {', '.join(errors)}"
            ).model_dump()), 400
        
        # 使用POI服务生成行程
        # Pydantic会自动将枚举转换为值（因为Config.use_enum_values=True）
        itinerary = poi_service.generate_itinerary(
            city=request_data.city,
            days=request_data.days,
            preferences=request_data.preferences,
            pace=str(request_data.pace),  # 枚举已自动转换为字符串值
            transport_mode=str(request_data.transport_mode)  # 枚举已自动转换为字符串值
        )
        
        # 检查是否有错误
        if 'error' in itinerary:
            return jsonify(ErrorResponse(error=itinerary['error']).model_dump()), 404
        
        # 使用Pydantic模型验证并序列化响应
        response = ItineraryResponse(**itinerary)
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error=f'生成行程失败: {str(e)}'
        ).model_dump()), 500

@api.route('/ai/chat', methods=['POST'])
def ai_chat():
    """
    AI助手对话接口
    
    请求体示例:
    {
        "user_id": "user123",
        "message": "我想去北京旅游，有什么推荐吗？",
        "context": {
            "city": "北京",
            "days": 3
        }
    }
    """
    try:
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '')
        context = data.get('context', {})
        
        if not message:
            return jsonify(ErrorResponse(
                error='消息内容不能为空'
            ).model_dump()), 400
        
        # 调用AI助手服务
        response = ai_assistant_service.chat(user_id, message, context)
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error=f'AI助手服务失败: {str(e)}'
        ).model_dump()), 500

@api.route('/ai/history/<user_id>', methods=['GET'])
def get_chat_history(user_id):
    """获取用户的对话历史"""
    try:
        history = ai_assistant_service.get_history(user_id)
        return jsonify({'history': history}), 200
    except Exception as e:
        return jsonify(ErrorResponse(
            error=f'获取对话历史失败: {str(e)}'
        ).model_dump()), 500

@api.route('/ai/history/<user_id>', methods=['DELETE'])
def clear_chat_history(user_id):
    """清除用户的对话历史"""
    try:
        ai_assistant_service.clear_history(user_id)
        return jsonify({'message': '对话历史已清除'}), 200
    except Exception as e:
        return jsonify(ErrorResponse(
            error=f'清除对话历史失败: {str(e)}'
        ).model_dump()), 500

@api.route('/travel/hotels', methods=['GET'])
def search_hotels():
    """
    搜索酒店
    
    查询参数:
    - city: 城市名称（必填）
    - check_in: 入住日期 YYYY-MM-DD（可选）
    - check_out: 退房日期 YYYY-MM-DD（可选）
    - adults: 成人数量（可选，默认2）
    - rooms: 房间数量（可选，默认1）
    """
    try:
        city = request.args.get('city')
        if not city:
            return jsonify(ErrorResponse(
                error='城市参数是必填的'
            ).model_dump()), 400
        
        check_in = request.args.get('check_in')
        check_out = request.args.get('check_out')
        adults = int(request.args.get('adults', 2))
        rooms = int(request.args.get('rooms', 1))
        
        hotels = travel_api_service.search_hotels(
            city=city,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            rooms=rooms
        )
        
        return jsonify({
            'city': city,
            'count': len(hotels),
            'hotels': hotels
        }), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error=f'搜索酒店失败: {str(e)}'
        ).model_dump()), 500

@api.route('/travel/flights', methods=['GET'])
def search_flights():
    """
    搜索航班
    
    查询参数:
    - origin: 出发城市代码（必填，如：PEK）
    - destination: 目的地城市代码（必填，如：SHA）
    - departure_date: 出发日期 YYYY-MM-DD（必填）
    - return_date: 返程日期 YYYY-MM-DD（可选）
    - adults: 成人数量（可选，默认1）
    """
    try:
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        departure_date = request.args.get('departure_date')
        
        if not all([origin, destination, departure_date]):
            return jsonify(ErrorResponse(
                error='origin, destination, departure_date 参数是必填的'
            ).model_dump()), 400
        
        return_date = request.args.get('return_date')
        adults = int(request.args.get('adults', 1))
        
        flights = travel_api_service.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults
        )
        
        return jsonify({
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'count': len(flights),
            'flights': flights
        }), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error=f'搜索航班失败: {str(e)}'
        ).model_dump()), 500

@api.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})

