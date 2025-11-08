import requests
from backend.config import Config

class PriceService:
    """价格服务：提供比价和价格估算"""
    
    def __init__(self):
        self.tripadvisor_key = Config.TRIPADVISOR_API_KEY
    
    def estimate_activity_price(self, activity_name, activity_type, city):
        """估算活动价格"""
        # 根据类型和名称估算价格
        base_prices = {
            "自然": 30,
            "美食": 50,
            "文化": 40,
            "购物": 100,
            "娱乐": 60,
            "历史": 35
        }
        
        base_price = base_prices.get(activity_type, 50)
        
        # 可以根据名称中的关键词调整
        if "博物馆" in activity_name or "美术馆" in activity_name:
            base_price = 40
        elif "公园" in activity_name or "广场" in activity_name:
            base_price = 0
        elif "餐厅" in activity_name or "美食" in activity_name:
            base_price = 80
        
        return {
            "price_estimate": base_price,
            "price_range": self._get_price_range(base_price),
            "currency": "CNY"
        }
    
    def compare_prices(self, activities):
        """比较多个活动的价格，返回排序结果"""
        activities_with_price = []
        
        for activity in activities:
            price_info = self.estimate_activity_price(
                activity.get("name", ""),
                activity.get("type", ""),
                activity.get("city", "")
            )
            activity["price_info"] = price_info
            activities_with_price.append(activity)
        
        # 按价格排序
        activities_with_price.sort(key=lambda x: x["price_info"]["price_estimate"])
        
        return activities_with_price
    
    def get_optimal_price_plan(self, trip_plan, priority="价格优先"):
        """根据优先级获取最优价格方案"""
        if priority == "价格优先":
            # 选择价格较低的方案
            for day in trip_plan.get("days", []):
                day["activities"].sort(key=lambda x: x.get("price_estimate", 0))
        elif priority == "效率优先":
            # 选择时间效率高的方案（已由路线优化处理）
            pass
        elif priority == "风景优先":
            # 选择评分高的方案
            for day in trip_plan.get("days", []):
                day["activities"].sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif priority == "娱乐设施优先":
            # 选择娱乐类型的活动
            for day in trip_plan.get("days", []):
                day["activities"].sort(key=lambda x: 1 if "娱乐" in x.get("type", "") else 0, reverse=True)
        
        return trip_plan
    
    def _get_price_range(self, price):
        """根据价格返回价格范围符号"""
        if price == 0:
            return "免费"
        elif price < 30:
            return "$"
        elif price < 60:
            return "$$"
        elif price < 100:
            return "$$$"
        else:
            return "$$$$"

