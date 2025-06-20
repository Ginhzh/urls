from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import redis.asyncio as redis
from typing import AsyncGenerator, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class Database:
    """数据库连接管理器"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.redis_client = None
    
    async def connect(self):
        """建立数据库连接"""
        try:
            # 创建异步数据库引擎
            self.engine = create_async_engine(
                settings.database_url,
                echo=settings.debug,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_pre_ping=True,  # 验证连接有效性
                pool_recycle=3600,   # 1小时后回收连接
            )
            
            # 创建会话工厂
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("数据库连接已建立")
            
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("数据库连接已关闭")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if not self.session_factory:
            raise RuntimeError("数据库未连接")
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def connect_redis(self):
        """建立Redis连接"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis连接已建立")
            
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    async def disconnect_redis(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis连接已关闭")
    
    async def get_redis(self) -> redis.Redis:
        """获取Redis客户端"""
        if not self.redis_client:
            raise RuntimeError("Redis未连接")
        return self.redis_client


# 全局数据库实例
database = Database()


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：获取数据库会话"""
    async for session in database.get_session():
        yield session


async def get_redis_client() -> redis.Redis:
    """依赖注入：获取Redis客户端"""
    return await database.get_redis()


# 缓存管理器
class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[str]:
        """从缓存获取值"""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        expire: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            if expire is None:
                expire = settings.redis_ttl
            
            return await self.redis.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存键"""
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在"""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"缓存检查失败: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增缓存值"""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"缓存递增失败: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置缓存键过期时间"""
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"设置过期时间失败: {e}")
            return False


async def get_cache_manager() -> CacheManager:
    """依赖注入：获取缓存管理器"""
    redis_client = await get_redis_client()
    return CacheManager(redis_client)


# 数据库健康检查
async def check_database_health() -> bool:
    """检查数据库连接健康状态"""
    try:
        async for session in database.get_session():
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False


async def check_redis_health() -> bool:
    """检查Redis连接健康状态"""
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis健康检查失败: {e}")
        return False 