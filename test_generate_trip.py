#!/usr/bin/env python3
"""
测试脚本：测试 /api/generate_trip 接口
"""
import requests
import json

def test_generate_trip():
    """测试生成行程接口"""
    url = "http://localhost:5001/api/generate_trip"
    
    # 请求数据
    data = {
        "city": "San Diego",
        "days": 2,
        "preferences": ["自然", "美食"]
    }
    
    # 发送 POST 请求
    try:
        print(f"正在向 {url} 发送请求...")
        print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print("-" * 50)
        
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # 打印响应状态码
        print(f"响应状态码: {response.status_code}")
        print("-" * 50)
        
        # 解析响应
        result = response.json()
        
        # 打印返回结果
        print("返回结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("-" * 50)
        
        # 检查是否有错误
        if "error" in result:
            print(f"❌ 错误信息: {result['error']}")
            return False
        else:
            print("✅ 请求成功")
            return True
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误：请确保后端服务正在运行 (http://localhost:5001)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return False
    except json.JSONDecodeError:
        print("❌ 响应不是有效的 JSON 格式")
        print(f"原始响应: {response.text}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("测试 /api/generate_trip 接口")
    print("=" * 50)
    test_generate_trip()

