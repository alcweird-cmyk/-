#!/usr/bin/env python3
"""
测试图片上传和检测功能
"""

import requests
import json
import os
from pathlib import Path

def test_upload_and_detect():
    """测试上传和检测功能"""
    
    # 测试图片路径（需要替换为实际的测试图片）
    test_image_path = "test/test_image.tif"  # 请替换为实际的测试图片路径
    
    if not os.path.exists(test_image_path):
        print(f"测试图片不存在: {test_image_path}")
        print("请将测试图片放在 test/test_image.tif 或修改路径")
        return
    
    # 准备上传数据
    files = {
        'image': open(test_image_path, 'rb')
    }
    
    data = {
        'categories': json.dumps([
            "forest", "meadow", "bare_land", "farm_land", "lake", "river",
            "road", "bank", "pond", "house", "dam", "barrage", "bridge", "large_greenhouse"
        ]),
        'is_change_detection': 'true',
        'is_only_change_detection': 'false',
        'legend_required': 'false'
    }
    
    try:
        print("开始测试上传和检测功能...")
        print(f"上传图片: {test_image_path}")
        
        # 发送请求
        response = requests.post(
            "http://localhost:8086/api/upload-and-detect",
            files=files,
            data=data,
            timeout=600  # 10分钟超时
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 上传检测成功!")
            print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 上传检测失败: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")
    finally:
        files['image'].close()

def test_upload_page():
    """测试上传页面是否可访问"""
    try:
        response = requests.get("http://localhost:8086/upload")
        if response.status_code == 200:
            print("✅ 上传页面可正常访问")
        else:
            print(f"❌ 上传页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 访问上传页面失败: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("图片上传检测功能测试")
    print("=" * 50)
    
    # 测试页面访问
    test_upload_page()
    print()
    
    # 测试上传功能
    test_upload_and_detect() 