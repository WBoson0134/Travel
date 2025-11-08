from flask import Blueprint, request, jsonify, send_file
from backend.models import db, Trip, DayPlan, Activity, Route
from backend.services.ai_service import AIService
from backend.services.map_service import MapService
from backend.services.price_service import PriceService
from backend.services.export_service import ExportService
from datetime import datetime, timedelta
import json
import io

api = Blueprint('api', __name__, url_prefix='/api')

ai_service = AIService()
map_service = MapService()
price_service = PriceService()
export_service = ExportService()

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

@api.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})

