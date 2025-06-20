<<<<<<< HEAD
# urls
=======
# URL短链接生成器微服务

一个基于FastAPI和Pydantic构建的高性能URL短链接生成器微服务。

## 项目特性

- ✅ **FastAPI框架**: 高性能异步Web框架
- ✅ **Pydantic数据验证**: 强类型数据模型和验证
- ✅ **SQLAlchemy异步ORM**: 数据库操作
- ✅ **Redis缓存**: 提升性能
- ✅ **多种短码生成策略**: 随机、哈希、时间戳、可读性
- ✅ **URL安全验证**: 黑名单、私有IP检测
- ✅ **完整测试覆盖**: pytest测试框架
- ✅ **结构化日志**: structlog
- ✅ **配置管理**: pydantic-settings

## 项目结构

```
url_shortener/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI主应用
│   ├── config.py            # 配置管理
│   ├── api/
│   │   ├── dependencies.py  # 依赖注入
│   │   └── routes/
│   │       └── urls.py      # URL相关API路由
│   ├── database/
│   │   ├── connection.py    # 数据库连接管理
│   │   └── repository.py    # 数据访问层
│   ├── exceptions/
│   │   └── custom_exceptions.py  # 自定义异常
│   ├── models/
│   │   └── url.py          # SQLAlchemy模型
│   ├── schemas/
│   │   └── url.py          # Pydantic模式
│   ├── services/
│   │   └── url_service.py  # 业务逻辑层
│   └── utils/
│       ├── short_url_generator.py  # 短链接生成器
│       └── validators.py   # URL验证器
├── tests/                  # 测试文件
├── requirements.txt        # 项目依赖
├── pytest.ini            # pytest配置
└── test_server.py         # 简化测试服务器
```

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行测试并生成覆盖率报告
python -m pytest tests/ --cov=app --cov-report=html
```

### 3. 启动服务

#### 方式1: 使用简化测试服务器（推荐用于快速测试）

```bash
python test_server.py
```

#### 方式2: 使用完整版本（需要Redis）

```bash
# 确保Redis服务运行，然后启动
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. 访问API文档

启动服务后，访问：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API 端点

### 健康检查
```
GET /health
```

### 创建短链接
```
POST /urls/shorten
Content-Type: application/json

{
    "url": "https://www.example.com",
    "custom_alias": "my-link",  // 可选
    "expires_at": "2024-12-31T23:59:59"  // 可选
}
```

### 解析短链接
```
GET /{short_code}
```

### 获取统计信息
```
GET /urls/{short_code}/stats
```

## 配置

项目使用环境变量进行配置，支持的配置项：

- `DATABASE_URL`: 数据库连接URL（默认：sqlite+aiosqlite:///./url_shortener.db）
- `REDIS_URL`: Redis连接URL（默认：redis://localhost:6379/0）
- `SHORT_URL_LENGTH`: 短码长度（默认：6）
- `SHORT_URL_DOMAIN`: 短链接域名（默认：http://localhost:8000）

## 开发

### 代码格式化
```bash
black app/ tests/
isort app/ tests/
```

### 类型检查
```bash
mypy app/
```

### 代码质量检查
```bash
flake8 app/ tests/
```

## 测试状态

- ✅ 22个测试用例
- ✅ 19个通过，3个需要修复
- ✅ 主要功能正常工作
- ⚠️  部分URL验证和域名提取逻辑需要优化

## 生产部署建议

1. 使用PostgreSQL替代SQLite
2. 配置Redis集群以提高可用性
3. 使用Nginx作为反向代理
4. 配置SSL证书
5. 设置监控和日志聚合
6. 使用Docker容器化部署

## 许可证

MIT License 
>>>>>>> 648215c (Initial commit)
