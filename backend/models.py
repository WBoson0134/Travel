from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Trip(db.Model):
    """行程主表"""
    __tablename__ = 'trips'
    
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    preferences = db.Column(db.Text)  # JSON格式存储偏好
    pace = db.Column(db.String(20))  # 佛系/中庸/硬核
    transport_mode = db.Column(db.String(50))
    priority = db.Column(db.String(50))  # 价格优先/效率优先/风景优先等
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    days_plans = db.relationship('DayPlan', backref='trip', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'days': self.days,
            'preferences': json.loads(self.preferences) if self.preferences else {},
            'pace': self.pace,
            'transport_mode': self.transport_mode,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'days_plans': [dp.to_dict() for dp in self.days_plans]
        }

class DayPlan(db.Model):
    """每日行程计划"""
    __tablename__ = 'day_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date)
    description = db.Column(db.Text)  # AI生成的描述
    
    # 关联
    activities = db.relationship('Activity', backref='day_plan', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'day_number': self.day_number,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'activities': [a.to_dict() for a in self.activities]
        }

class Activity(db.Model):
    """活动/景点"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    day_plan_id = db.Column(db.Integer, db.ForeignKey('day_plans.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))  # 自然/美食/文化/购物等
    address = db.Column(db.String(500))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    duration_minutes = db.Column(db.Integer)
    description = db.Column(db.Text)
    rating = db.Column(db.Float)  # 星级评价
    price_range = db.Column(db.String(20))  # $, $$, $$$, $$$$
    tags = db.Column(db.Text)  # JSON格式存储标签
    price_estimate = db.Column(db.Float)  # 价格估算
    order = db.Column(db.Integer)  # 当天的顺序
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'description': self.description,
            'rating': self.rating,
            'price_range': self.price_range,
            'tags': json.loads(self.tags) if self.tags else [],
            'price_estimate': self.price_estimate,
            'order': self.order
        }

class Route(db.Model):
    """路线信息"""
    __tablename__ = 'routes'
    
    id = db.Column(db.Integer, primary_key=True)
    from_activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'))
    to_activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'))
    transport_mode = db.Column(db.String(50))
    duration_minutes = db.Column(db.Integer)
    distance_km = db.Column(db.Float)
    route_data = db.Column(db.Text)  # JSON格式存储路线坐标
    
    def to_dict(self):
        return {
            'id': self.id,
            'from_activity_id': self.from_activity_id,
            'to_activity_id': self.to_activity_id,
            'transport_mode': self.transport_mode,
            'duration_minutes': self.duration_minutes,
            'distance_km': self.distance_km,
            'route_data': json.loads(self.route_data) if self.route_data else None
        }

