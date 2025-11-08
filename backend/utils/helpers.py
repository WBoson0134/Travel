"""工具函数"""

def format_time(time_obj):
    """格式化时间对象为字符串"""
    if time_obj:
        return time_obj.strftime('%H:%M')
    return None

def calculate_total_price(activities):
    """计算总价格"""
    return sum(act.get('price_estimate', 0) or 0 for act in activities)

def sort_activities_by_priority(activities, priority):
    """根据优先级排序活动"""
    if priority == "价格优先":
        return sorted(activities, key=lambda x: x.get('price_estimate', 0))
    elif priority == "效率优先":
        return sorted(activities, key=lambda x: x.get('order', 0))
    elif priority == "风景优先":
        return sorted(activities, key=lambda x: x.get('rating', 0), reverse=True)
    elif priority == "娱乐设施优先":
        return sorted(activities, key=lambda x: 1 if "娱乐" in x.get('type', '') else 0, reverse=True)
    return activities

