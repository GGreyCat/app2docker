#!/usr/bin/env python3
"""
测试 Git 源码编译功能
使用 https://gitee.com/numen06/jar2docker.git 仓库进行测试
"""
import sys
import time
import requests
import json

BASE_URL = "http://localhost:8000"

def login():
    """登录获取 token"""
    print("🔑 正在登录...")
    response = requests.post(
        f"{BASE_URL}/api/login",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        result = response.json()
        token = result.get("access_token")
        print(f"✅ 登录成功")
        return token
    else:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return None

def test_git_build(token):
    """测试 Git 源码构建"""
    print("\n" + "=" * 60)
    print("🧪 开始测试 Git 源码构建")
    print("=" * 60)
    
    # 1. 触发构建
    print("\n📝 步骤1: 创建构建任务...")
    build_data = {
        "project_type": "go",  # jar2docker 是 Go 项目
        "template": "go1.23",
        "git_url": "https://gitee.com/numen06/jar2docker.git",
        "imagename": "test-jar2docker",
        "tag": f"test-{int(time.time())}",
        "push": "off",
        "use_project_dockerfile": True  # 使用项目中的 Dockerfile
    }
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        # 设置 Content-Type 为表单格式
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        resp = requests.post(
            f"{BASE_URL}/api/build-from-source",
            data=build_data,
            headers=headers
        )
        print(f"📡 响应状态码: {resp.status_code}")
        print(f"📄 响应内容: {resp.text}")
        
        if resp.status_code != 200:
            print(f"❌ 创建任务失败: {resp.status_code}")
            print(f"响应: {resp.text}")
            return False
        
        result = resp.json()
        task_id = result.get("task_id")
        print(f"✅ 任务已创建: {task_id}")
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. 轮询任务状态和日志
    print(f"\n📊 步骤2: 监控任务执行...")
    print("-" * 60)
    
    last_log_length = 0
    check_count = 0
    max_checks = 300  # 最多检查5分钟
    
    while check_count < max_checks:
        check_count += 1
        time.sleep(2)
        
        try:
            # 获取任务状态
            task_resp = requests.get(f"{BASE_URL}/api/build-tasks/{task_id}", headers=headers)
            if task_resp.status_code == 200:
                task = task_resp.json()
                status = task.get("status", "unknown")
                
                # 获取日志
                log_resp = requests.get(f"{BASE_URL}/api/build-tasks/{task_id}/logs", headers=headers)
                if log_resp.status_code == 200:
                    logs = log_resp.text
                    
                    # 打印新日志
                    if len(logs) > last_log_length:
                        new_logs = logs[last_log_length:]
                        print(new_logs, end='')
                        last_log_length = len(logs)
                
                # 检查任务是否完成
                if status in ["completed", "failed"]:
                    print(f"\n{'=' * 60}")
                    print(f"📊 任务状态: {status}")
                    print(f"⏱️  总耗时: {check_count * 2} 秒")
                    print("=" * 60)
                    
                    if status == "completed":
                        print("✅ 测试通过：构建成功！")
                        return True
                    else:
                        error_msg = task.get("error", "未知错误")
                        print(f"❌ 测试失败：构建失败 - {error_msg}")
                        return False
                        
        except Exception as e:
            print(f"⚠️ 检查任务状态失败: {e}")
    
    print("\n⏰ 测试超时（5分钟）")
    return False

def main():
    """主函数"""
    # 先尝试不登录
    print("🚀 开始测试 Git 源码编译功能")
    print(f"🔗 测试仓库: https://gitee.com/numen06/jar2docker.git")
    
    # 先尝试获取 token
    token = login()
    
    # 执行测试
    success = test_git_build(token)
    
    if success:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n💔 测试失败，请检查日志")
        sys.exit(1)

if __name__ == "__main__":
    main()
