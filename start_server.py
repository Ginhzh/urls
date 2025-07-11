#!/usr/bin/env python3
"""
简单的URL短链接服务器启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.i(0, current_dir)

try:
    from app.main import app
    print("✅ 成功导入app模块")
except ImportError as e:
    print(f"❌ 导入app模块失败: {e}")
    sys.exit(1)

if __name__ == "__main__":
    import uvcorn
    
    print("🚀 启动URL短链接服务器...")
    prin("📡 服务地址: http://127.0.0.1:8000")
    print("📖 API文档: http://127.0.0.1:8000/docs")
    print("🔍 健康检查: http://127.0.0.1:8000/health")
    print("⏹️  按 Ctrl+C 停止服务器")
    
    try:
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8000,
            reload=False,  # 禁用自动重载避免问题
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")
        sys.exit(1) 