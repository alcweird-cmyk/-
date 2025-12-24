#!/usr/bin/env python3
"""
UI布局和性能测试脚本
"""

import requests
import time
import json

def test_api_performance():
    """测试API性能"""
    base_url = "http://localhost:8086"
    
    print("=== API性能测试 ===")
    
    # 测试系统统计API
    start_time = time.time()
    response = requests.get(f"{base_url}/api/stats")
    stats_time = time.time() - start_time
    print(f"系统统计API响应时间: {stats_time:.3f}秒")
    
    # 测试当前任务API
    start_time = time.time()
    response = requests.get(f"{base_url}/api/tasks/current")
    task_time = time.time() - start_time
    print(f"当前任务API响应时间: {task_time:.3f}秒")
    
    # 测试日志API
    start_time = time.time()
    response = requests.get(f"{base_url}/api/logs?limit=50")
    logs_time = time.time() - start_time
    print(f"日志API响应时间: {logs_time:.3f}秒")
    
    # 测试历史记录API
    start_time = time.time()
    response = requests.get(f"{base_url}/api/tasks/history")
    history_time = time.time() - start_time
    print(f"历史记录API响应时间: {history_time:.3f}秒")
    
    print(f"\n平均响应时间: {(stats_time + task_time + logs_time + history_time) / 4:.3f}秒")

def test_page_load():
    """测试页面加载"""
    base_url = "http://localhost:8086"
    
    print("\n=== 页面加载测试 ===")
    
    pages = [
        ("主页", "/"),
        ("历史记录", "/history"),
        ("检测结果", "/results"),
        ("上传页面", "/upload")
    ]
    
    for page_name, page_path in pages:
        start_time = time.time()
        response = requests.get(f"{base_url}{page_path}")
        load_time = time.time() - start_time
        print(f"{page_name}加载时间: {load_time:.3f}秒 (状态码: {response.status_code})")

def check_system_status():
    """检查系统状态"""
    base_url = "http://localhost:8086"
    
    print("\n=== 系统状态检查 ===")
    
    try:
        response = requests.get(f"{base_url}/api/stats")
        stats = response.json()
        print(f"系统状态: {stats['system_status']}")
        print(f"总任务数: {stats['total_tasks']}")
        print(f"已完成任务: {stats['completed_tasks']}")
        print(f"处理图片数: {stats['total_images']}")
    except Exception as e:
        print(f"获取系统状态失败: {e}")

if __name__ == "__main__":
    print("开始UI布局和性能测试...")
    print("=" * 50)
    
    check_system_status()
    test_api_performance()
    test_page_load()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("请访问 http://localhost:8086 查看UI布局")
    print("如果UI仍然有问题，请检查浏览器控制台是否有错误") 