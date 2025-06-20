from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import IntegrityError, NoResultFound
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime, timezone, timedelta

from app.models.url import URLModel
from app.database.connection import CacheManager
from app.exceptions.custom_exceptions import (
    URLNotFoundError, 
    ShortURLExistsError, 
    DatabaseError
)

logger = logging.getLogger(__name__)


class URLRepository:
    """URL数据仓储类"""
    
    def __init__(self, session: AsyncSession, cache: Optional[CacheManager] = None):
        self.session = session
        self.cache = cache
    
    async def create_url(self, url_data: Dict[str, Any]) -> URLModel:
        """
        创建新的URL记录
        
        Args:
            url_data: URL数据字典
            
        Returns:
            URLModel: 创建的URL模型
            
        Raises:
            ShortURLExistsError: 短链接已存在
            DatabaseError: 数据库操作错误
        """
        try:
            url_model = URLModel(**url_data)
            self.session.add(url_model)
            await self.session.commit()
            await self.session.refresh(url_model)
            
            # 缓存新创建的URL
            if self.cache:
                await self._cache_url(url_model)
            
            logger.info(f"创建URL记录: {url_model.short_code}")
            return url_model
            
        except IntegrityError as e:
            await self.session.rollback()
            if "short_code" in str(e):
                raise ShortURLExistsError(url_data.get("short_code", ""))
            elif "custom_alias" in str(e):
                raise ShortURLExistsError(url_data.get("custom_alias", ""))
            else:
                raise DatabaseError(f"数据库约束违反: {str(e)}")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"创建URL记录失败: {e}")
            raise DatabaseError(f"创建URL记录失败: {str(e)}")
    
    async def get_url_by_short_code(self, short_code: str) -> Optional[URLModel]:
        """
        根据短链接代码获取URL记录
        
        Args:
            short_code: 短链接代码
            
        Returns:
            URLModel: URL模型，如果不存在则返回None
        """
        try:
            # 首先尝试从缓存获取
            if self.cache:
                cached_url = await self._get_cached_url(short_code)
                if cached_url:
                    return cached_url
            
            # 从数据库查询
            stmt = select(URLModel).where(URLModel.short_code == short_code)
            result = await self.session.execute(stmt)
            url_model = result.scalar_one_or_none()
            
            if url_model and self.cache:
                # 缓存查询结果
                await self._cache_url(url_model)
            
            return url_model
            
        except Exception as e:
            logger.error(f"获取URL记录失败: {e}")
            return None
    
    async def get_url_by_custom_alias(self, custom_alias: str) -> Optional[URLModel]:
        """
        根据自定义别名获取URL记录
        
        Args:
            custom_alias: 自定义别名
            
        Returns:
            URLModel: URL模型，如果不存在则返回None
        """
        try:
            stmt = select(URLModel).where(URLModel.custom_alias == custom_alias)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"根据别名获取URL记录失败: {e}")
            return None
    
    async def get_url_by_id(self, url_id: int) -> Optional[URLModel]:
        """根据ID获取URL记录"""
        try:
            stmt = select(URLModel).where(URLModel.id == url_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"根据ID获取URL记录失败: {e}")
            return None
    
    async def update_url(self, url_id: int, update_data: Dict[str, Any]) -> Optional[URLModel]:
        """
        更新URL记录
        
        Args:
            url_id: URL ID
            update_data: 更新数据
            
        Returns:
            URLModel: 更新后的URL模型
        """
        try:
            stmt = (
                update(URLModel)
                .where(URLModel.id == url_id)
                .values(**update_data)
                .returning(URLModel)
            )
            result = await self.session.execute(stmt)
            url_model = result.scalar_one_or_none()
            
            if url_model:
                await self.session.commit()
                
                # 更新缓存
                if self.cache:
                    await self._cache_url(url_model)
                
                logger.info(f"更新URL记录: {url_model.short_code}")
                return url_model
            else:
                return None
                
        except Exception as e:
            await self.session.rollback()
            logger.error(f"更新URL记录失败: {e}")
            raise DatabaseError(f"更新URL记录失败: {str(e)}")
    
    async def increment_click_count(self, short_code: str) -> bool:
        """
        增加点击次数
        
        Args:
            short_code: 短链接代码
            
        Returns:
            bool: 是否成功
        """
        try:
            now = datetime.now(timezone.utc)
            stmt = (
                update(URLModel)
                .where(URLModel.short_code == short_code)
                .values(
                    click_count=URLModel.click_count + 1,
                    last_accessed_at=now
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            # 清除缓存，让下次查询获取最新数据
            if self.cache:
                await self._invalidate_cache(short_code)
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"更新点击次数失败: {e}")
            return False
    
    async def deactivate_url(self, short_code: str) -> bool:
        """停用URL"""
        try:
            stmt = (
                update(URLModel)
                .where(URLModel.short_code == short_code)
                .values(is_active=False)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            if self.cache:
                await self._invalidate_cache(short_code)
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"停用URL失败: {e}")
            return False
    
    async def delete_url(self, short_code: str) -> bool:
        """删除URL记录"""
        try:
            stmt = delete(URLModel).where(URLModel.short_code == short_code)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            if self.cache:
                await self._invalidate_cache(short_code)
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"删除URL记录失败: {e}")
            return False
    
    async def list_urls(
        self, 
        page: int = 1, 
        size: int = 10,
        is_active: Optional[bool] = None,
        creator_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分页获取URL列表
        
        Args:
            page: 页码
            size: 每页大小
            is_active: 是否激活状态过滤
            creator_ip: 创建者IP过滤
            
        Returns:
            Dict: 包含URLs列表和分页信息
        """
        try:
            # 构建查询条件
            conditions = []
            if is_active is not None:
                conditions.append(URLModel.is_active == is_active)
            if creator_ip:
                conditions.append(URLModel.creator_ip == creator_ip)
            
            # 计算总数
            count_stmt = select(func.count(URLModel.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar()
            
            # 获取分页数据
            offset = (page - 1) * size
            stmt = select(URLModel).order_by(URLModel.created_at.desc())
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.offset(offset).limit(size)
            result = await self.session.execute(stmt)
            urls = result.scalars().all()
            
            return {
                "urls": urls,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
            
        except Exception as e:
            logger.error(f"获取URL列表失败: {e}")
            raise DatabaseError(f"获取URL列表失败: {str(e)}")
    
    async def cleanup_expired_urls(self) -> int:
        """清理过期的URL记录"""
        try:
            now = datetime.now(timezone.utc)
            stmt = (
                update(URLModel)
                .where(
                    and_(
                        URLModel.expires_at.isnot(None),
                        URLModel.expires_at < now,
                        URLModel.is_active == True
                    )
                )
                .values(is_active=False)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            logger.info(f"清理了 {result.rowcount} 个过期URL")
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"清理过期URL失败: {e}")
            return 0
    
    async def get_url_stats(self, short_code: str) -> Optional[Dict[str, Any]]:
        """获取URL统计信息"""
        url_model = await self.get_url_by_short_code(short_code)
        if not url_model:
            return None
        
        return {
            "id": url_model.id,
            "short_code": url_model.short_code,
            "original_url": url_model.original_url,
            "click_count": url_model.click_count,
            "created_at": url_model.created_at,
            "last_accessed_at": url_model.last_accessed_at,
            "is_expired": url_model.is_expired,
            "is_active": url_model.is_active
        }
    
    # 缓存相关私有方法
    async def _cache_url(self, url_model: URLModel):
        """缓存URL数据"""
        if not self.cache:
            return
        
        try:
            cache_key = f"url:{url_model.short_code}"
            cache_data = url_model.to_dict()
            await self.cache.set(
                cache_key, 
                json.dumps(cache_data, default=str),
                expire=3600  # 1小时过期
            )
        except Exception as e:
            logger.error(f"缓存URL数据失败: {e}")
    
    async def _get_cached_url(self, short_code: str) -> Optional[URLModel]:
        """从缓存获取URL数据"""
        if not self.cache:
            return None
        
        try:
            cache_key = f"url:{short_code}"
            cached_data = await self.cache.get(cache_key)
            
            if cached_data:
                url_dict = json.loads(cached_data)
                # 重建URLModel对象
                url_model = URLModel(**{
                    k: v for k, v in url_dict.items() 
                    if k != 'id'  # 排除ID，因为它是自动生成的
                })
                url_model.id = url_dict['id']
                return url_model
            
            return None
            
        except Exception as e:
            logger.error(f"从缓存获取URL数据失败: {e}")
            return None
    
    async def _invalidate_cache(self, short_code: str):
        """使缓存失效"""
        if not self.cache:
            return
        
        try:
            cache_key = f"url:{short_code}"
            await self.cache.delete(cache_key)
        except Exception as e:
            logger.error(f"使缓存失效失败: {e}") 