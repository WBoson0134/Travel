#!/usr/bin/env python3
"""
测试 /api/generate_itinerary 接口
"""
import requests
import json

def test_generate_itinerary():
    """测试生成行程接口"""
    url = "http://localhost:5001/api/generate_itinerary"
    
    # 测试数据
    test_cases = [
        {
            "name": "北京3日游",
            "data": {
                "city": "北京",
                "days": 3,
                "preferences": ["文化", "历史"],
                "pace": "中庸",
                "transport_mode": "driving"
            }
        },
        {
            "name": "杭州2日游（自然偏好）",
            "data": {
                "city": "杭州",
                "days": 2,
                "preferences": ["自然"],
                "pace": "佛系",
                "transport_mode": "walking"
            }
        },
        {
            "name": "上海1日游（硬核节奏）",
            "data": {
                "city": "上海",
                "days": 1,
                "preferences": [],
                "pace": "硬核",
                "transport_mode": "driving"
            }
        }
    ]
    
    print("=" * 60)
    print("测试 /api/generate_itinerary 接口")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\n测试用例: {test_case['name']}")
        print(f"请求数据: {json.dumps(test_case['data'], ensure_ascii=False, indent=2)}")
        print("-" * 60)
        
        try:
            response = requests.post(url, json=test_case['data'], timeout=10)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"成功！生成 {result.get('total_days', 0)} 天行程")
                print(f"城市: {result.get('city')}")
                print(f"节奏: {result.get('pace')}")
                print(f"交通方式: {result.get('transport_mode')}")
                
                days = result.get('days', [])
                print(f"共 {len(days)} 天的行程:")
                
                for day in days:
                    print(f"\n  第 {day['day_number']} 天: {day['description']}")
                    activities = day.get('activities', [])
                    for activity in activities:
                        print(f"    - {activity['start_time']}-{activity['end_time']} "
                              f"{activity['name']} ({activity['duration_minutes']}分钟)")
            else:
                print(f"错误: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("错误: 无法连接到服务器，请确保后端服务正在运行 (http://localhost:5001)")
        except Exception as e:
            print(f"错误: {str(e)}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_generate_itinerary()

