#!/usr/bin/env python3
"""
调试服务器启动问题
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print(f"🔍 当前工作目录: {os.getcwd()}")
print(f"🔍 脚本目录: {current_dir}")
print(f"🔍 Python路径: {sys.path[:3]}...")

# 测试模块导入
try:
    print("📦 测试导入app模块...")
    import app
    print("✅ app模块导入成功")
    
    print("📦 测试导入app.main...")
    from app.main import app as fastapi_app
    print("✅ app.main导入成功")
    
    print("📦 测试导入app.config...")
    from app.config import settings
    print(f"✅ 配置导入成功，数据库: {settings.database_url}")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"❌ 错误类型: {type(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试基本FastAPI功能
try:
    print("🌐 创建简单的HTTP客户端测试...")
    from fastapi.testclient import TestClient
    
    client = TestClient(fastapi_app)
    
    print("🔍 测试根路径...")
    response = client.get("/")
    print(f"✅ 根路径响应: {response.status_code}")
    
    print("🔍 测试健康检查...")
    response = client.get("/health")
    print(f"✅ 健康检查响应: {response.status_code}")
    if response.status_code == 200:
        print(f"📋 健康检查内容: {response.json()}")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("🎉 所有测试完成！") 