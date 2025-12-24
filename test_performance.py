#!/usr/bin/env python3
"""
性能测试脚本 - 测试监控系统的API响应速度
"""

import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import json

BASE_URL = "http://localhost:8086"

def test_api_endpoint(endpoint, iterations=10):
    """测试单个API端点的响应时间"""
    times = []
    errors = 0
    
    print(f"测试端点: {endpoint}")
    
    for i in range(iterations):
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                times.append(response_time)
                print(f"  请求 {i+1}: {response_time:.2f}ms")
            else:
                errors += 1
                print(f"  请求 {i+1}: 错误 (状态码: {response.status_code})")
                
        except Exception as e:
            errors += 1
            print(f"  请求 {i+1}: 异常 ({str(e)})")
    
    if times:
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        print(f"  结果统计:")
        print(f"    平均响应时间: {avg_time:.2f}ms")
        print(f"    最小响应时间: {min_time:.2f}ms")
        print(f"    最大响应时间: {max_time:.2f}ms")
        print(f"    标准差: {std_dev:.2f}ms")
        print(f"    成功率: {len(times)}/{iterations} ({len(times)/iterations*100:.1f}%)")
    else:
        print(f"  所有请求都失败了")
    
    print()
    return {
        'endpoint': endpoint,
        'avg_time': avg_time if times else None,
        'min_time': min_time if times else None,
        'max_time': max_time if times else None,
        'std_dev': std_dev if times else None,
        'success_rate': len(times)/iterations if times else 0,
        'errors': errors
    }

def test_concurrent_requests(endpoint, concurrent_users=5, requests_per_user=5):
    """测试并发请求性能"""
    print(f"并发测试: {concurrent_users} 用户，每个用户 {requests_per_user} 请求")
    
    def make_requests():
        times = []
        for _ in range(requests_per_user):
            try:
                start_time = time.time()
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = (end_time - start_time) * 1000
                    times.append(response_time)
            except:
                pass
        return times
    
    all_times = []
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(make_requests) for _ in range(concurrent_users)]
        for future in futures:
            all_times.extend(future.result())
    
    if all_times:
        avg_time = statistics.mean(all_times)
        print(f"并发测试结果:")
        print(f"  总请求数: {len(all_times)}")
        print(f"  平均响应时间: {avg_time:.2f}ms")
        print(f"  吞吐量: {len(all_times)/max(all_times)*1000:.1f} 请求/秒")
    
    print()
    return all_times

def main():
    """主测试函数"""
    print("=" * 60)
    print("遥感推理服务监控系统 - 性能测试")
    print("=" * 60)
    
    # 测试的API端点
    endpoints = [
        "/api/stats",
        "/api/tasks/current", 
        "/api/tasks/history",
        "/api/logs?limit=50"
    ]
    
    results = []
    
    # 测试每个端点
    for endpoint in endpoints:
        result = test_api_endpoint(endpoint, iterations=5)
        results.append(result)
    
    # 并发测试
    print("并发性能测试:")
    concurrent_results = test_concurrent_requests("/api/stats", concurrent_users=3, requests_per_user=3)
    
    # 测试缓存效果
    print("缓存效果测试:")
    print("第一次请求 (无缓存):")
    start_time = time.time()
    response1 = requests.get(f"{BASE_URL}/api/stats")
    time1 = (time.time() - start_time) * 1000
    
    print("第二次请求 (有缓存):")
    start_time = time.time()
    response2 = requests.get(f"{BASE_URL}/api/stats")
    time2 = (time.time() - start_time) * 1000
    
    print(f"  无缓存响应时间: {time1:.2f}ms")
    print(f"  有缓存响应时间: {time2:.2f}ms")
    print(f"  性能提升: {time1/time2:.1f}x")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print("=" * 60)
    
    successful_results = [r for r in results if r['avg_time'] is not None]
    if successful_results:
        avg_response_time = statistics.mean([r['avg_time'] for r in successful_results])
        print(f"平均API响应时间: {avg_response_time:.2f}ms")
        
        if avg_response_time < 100:
            print("✅ 性能优秀 (< 100ms)")
        elif avg_response_time < 500:
            print("✅ 性能良好 (< 500ms)")
        else:
            print("⚠️  性能需要优化 (> 500ms)")
    
    print(f"测试完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 