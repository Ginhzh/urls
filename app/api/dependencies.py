from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from app.database.connection import get_database_session, get_cache_manager, CacheManager
from app.database.repository import URLRepository
from app.services.url_service import URLService


async def get_url_repository(
    session: AsyncSession = Depends(get_database_session),
    cache: CacheManager = Depends(get_cache_manager)
) -> URLRepository:
    """获取URL仓储实例"""
    return URLRepository(session, cache)


async def get_url_service(
    repository: URLRepository = Depends(get_url_repository),
    cache: CacheManager = Depends(get_cache_manager)
) -> URLService:
    """获取URL服务实例"""
    return URLService(repository, cache)


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """获取用户代理"""
    return request.headers.get("User-Agent", "unknown") 