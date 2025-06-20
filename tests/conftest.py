import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import redis.asyncio as redis

from app.main import app
from app.models.url import Base
from app.database.connection import get_database_session, get_redis_client
from app.config import settings


# 配置测试数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """创建测试数据库会话"""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with session_factory() as session:
        yield session


@pytest.fixture
async def test_redis():
    """创建测试Redis客户端"""
    # 使用假的Redis客户端进行测试
    import fakeredis.aioredis
    
    redis_client = fakeredis.aioredis.FakeRedis(
        decode_responses=True,
        encoding="utf-8"
    )
    
    yield redis_client
    
    await redis_client.flushall()
    await redis_client.close()


@pytest.fixture
async def test_client(test_session, test_redis):
    """创建测试客户端"""
    
    # 覆盖依赖
    async def override_get_database_session():
        yield test_session
    
    async def override_get_redis_client():
        return test_redis
    
    app.dependency_overrides[get_database_session] = override_get_database_session
    app.dependency_overrides[get_redis_client] = override_get_redis_client
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture
def sample_url_data():
    """示例URL数据"""
    return {
        "original_url": "https://www.example.com/very/long/url/path",
        "description": "测试链接",
        "expires_in_days": 30
    }


@pytest.fixture
def sample_url_with_alias():
    """带自定义别名的示例URL数据"""
    return {
        "original_url": "https://www.google.com",
        "custom_alias": "test-link",
        "description": "Google首页"
    }


@pytest.fixture
def invalid_url_data():
    """无效URL数据"""
    return [
        {"original_url": "not-a-url"},
        {"original_url": "ftp://example.com"},
        {"original_url": "javascript:alert('xss')"},
        {"original_url": ""},
    ]


# 标记异步测试
pytest_plugins = ("pytest_asyncio",) 