from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import logging

from app.models.url import URLModel
from app.schemas.url import URLCreateRequest, URLResponse, URLStatsResponse, URLListResponse
from app.database.repository import URLRepository
from app.database.connection import CacheManager
from app.utils.short_url_generator import ShortURLGenerator
from app.utils.validators import URLValidator
from app.exceptions.custom_exceptions import (
    URLNotFoundError,
    URLExpiredError,
    InvalidURLError,
    URLTooLongError,
    ShortURLExistsError,
    ShortURLGenerationError
)
from app.config import settings

logger = logging.getLogger(__name__)


class URLService:
    """URL短链接服务类"""
    
    def __init__(
        self, 
        repository: URLRepository, 
        cache: Optional[CacheManager] = None
    ):
        self.repository = repository
        self.cache = cache
        self.url_validator = URLValidator(max_length=settings.max_url_length)
        self.short_url_generator = ShortURLGenerator(length=settings.short_url_length)
    
    async def create_short_url(
        self, 
        request: URLCreateRequest,
        creator_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> URLResponse:
        """
        创建短链接
        
        Args:
            request: 创建请求
            creator_ip: 创建者IP
            user_agent: 用户代理
            
        Returns:
            URLResponse: 短链接响应
            
        Raises:
            InvalidURLError: 无效URL
            URLTooLongError: URL过长
            ShortURLExistsError: 短链接已存在
        """
        # 验证原始URL
        original_url = str(request.original_url)
        
        if not self.url_validator.is_valid_url(original_url):
            raise InvalidURLError(original_url)
        
        if len(original_url) > settings.max_url_length:
            raise URLTooLongError(settings.max_url_length)
        
        # 标准化URL
        normalized_url = self.url_validator.normalize_url(original_url)
        
        # 检查是否已存在相同的URL
        existing_url = await self._find_existing_url(normalized_url)
        if existing_url and existing_url.is_active and not existing_url.is_expired:
            return await self._build_url_response(existing_url)
        
        # 生成短链接代码
        short_code = await self._generate_unique_short_code(request.custom_alias)
        
        # 计算过期时间
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)
        elif settings.url_expiry_days > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.url_expiry_days)
        
        # 创建URL记录
        url_data = {
            "original_url": normalized_url,
            "short_code": short_code,
            "expires_at": expires_at,
            "creator_ip": creator_ip,
            "user_agent": user_agent,
            "description": request.description,
            "custom_alias": request.custom_alias
        }
        
        url_model = await self.repository.create_url(url_data)
        logger.info(f"创建短链接成功: {short_code} -> {normalized_url}")
        
        return await self._build_url_response(url_model)
    
    async def resolve_short_url(self, short_code: str) -> str:
        """
        解析短链接获取原始URL
        
        Args:
            short_code: 短链接代码
            
        Returns:
            str: 原始URL
            
        Raises:
            URLNotFoundError: 短链接不存在
            URLExpiredError: 短链接已过期
        """
        # 获取URL记录
        url_model = await self.repository.get_url_by_short_code(short_code)
        
        if not url_model:
            # 检查是否是自定义别名
            url_model = await self.repository.get_url_by_custom_alias(short_code)
            
        if not url_model:
            raise URLNotFoundError(short_code)
        
        if not url_model.is_active:
            raise URLNotFoundError(short_code)
        
        if url_model.is_expired:
            raise URLExpiredError(short_code)
        
        # 增加点击次数（异步执行，不影响重定向性能）
        await self.repository.increment_click_count(short_code)
        
        logger.info(f"短链接访问: {short_code} -> {url_model.original_url}")
        return url_model.original_url
    
    async def get_url_info(self, short_code: str) -> URLStatsResponse:
        """
        获取URL详细信息
        
        Args:
            short_code: 短链接代码
            
        Returns:
            URLStatsResponse: URL统计信息
            
        Raises:
            URLNotFoundError: 短链接不存在
        """
        url_model = await self.repository.get_url_by_short_code(short_code)
        
        if not url_model:
            url_model = await self.repository.get_url_by_custom_alias(short_code)
            
        if not url_model:
            raise URLNotFoundError(short_code)
        
        return URLStatsResponse(
            id=url_model.id,
            original_url=url_model.original_url,
            short_url=f"{settings.base_url}/{url_model.short_code}",
            short_code=url_model.short_code,
            created_at=url_model.created_at,
            updated_at=url_model.updated_at,
            expires_at=url_model.expires_at,
            is_active=url_model.is_active,
            click_count=url_model.click_count,
            last_accessed_at=url_model.last_accessed_at,
            description=url_model.description,
            custom_alias=url_model.custom_alias,
            is_expired=url_model.is_expired
        )
    
    async def list_urls(
        self,
        page: int = 1,
        size: int = 10,
        is_active: Optional[bool] = None,
        creator_ip: Optional[str] = None
    ) -> URLListResponse:
        """
        获取URL列表
        
        Args:
            page: 页码
            size: 每页大小
            is_active: 是否激活过滤
            creator_ip: 创建者IP过滤
            
        Returns:
            URLListResponse: URL列表响应
        """
        result = await self.repository.list_urls(
            page=page,
            size=size,
            is_active=is_active,
            creator_ip=creator_ip
        )
        
        url_responses = []
        for url_model in result["urls"]:
            url_response = await self._build_url_response(url_model)
            url_responses.append(url_response)
        
        return URLListResponse(
            urls=url_responses,
            total=result["total"],
            page=result["page"],
            size=result["size"],
            pages=result["pages"]
        )
    
    async def deactivate_url(self, short_code: str) -> bool:
        """
        停用短链接
        
        Args:
            short_code: 短链接代码
            
        Returns:
            bool: 是否成功
            
        Raises:
            URLNotFoundError: 短链接不存在
        """
        url_model = await self.repository.get_url_by_short_code(short_code)
        if not url_model:
            raise URLNotFoundError(short_code)
        
        success = await self.repository.deactivate_url(short_code)
        if success:
            logger.info(f"停用短链接: {short_code}")
        
        return success
    
    async def delete_url(self, short_code: str) -> bool:
        """
        删除短链接
        
        Args:
            short_code: 短链接代码
            
        Returns:
            bool: 是否成功
            
        Raises:
            URLNotFoundError: 短链接不存在
        """
        url_model = await self.repository.get_url_by_short_code(short_code)
        if not url_model:
            raise URLNotFoundError(short_code)
        
        success = await self.repository.delete_url(short_code)
        if success:
            logger.info(f"删除短链接: {short_code}")
        
        return success
    
    async def cleanup_expired_urls(self) -> int:
        """
        清理过期的URL
        
        Returns:
            int: 清理的URL数量
        """
        count = await self.repository.cleanup_expired_urls()
        logger.info(f"清理过期URL数量: {count}")
        return count
    
    async def get_url_analytics(self, short_code: str) -> Dict[str, Any]:
        """
        获取URL分析数据
        
        Args:
            short_code: 短链接代码
            
        Returns:
            Dict: 分析数据
            
        Raises:
            URLNotFoundError: 短链接不存在
        """
        stats = await self.repository.get_url_stats(short_code)
        if not stats:
            raise URLNotFoundError(short_code)
        
        # 添加一些分析指标
        now = datetime.now(timezone.utc)
        created_at = stats["created_at"]
        days_active = (now - created_at).days + 1
        
        analytics = {
            **stats,
            "days_active": days_active,
            "avg_clicks_per_day": stats["click_count"] / days_active if days_active > 0 else 0,
            "performance_rating": self._calculate_performance_rating(
                stats["click_count"], 
                days_active
            )
        }
        
        return analytics
    
    # 私有方法
    async def _find_existing_url(self, url: str) -> Optional[URLModel]:
        """查找是否存在相同的URL"""
        # 这里可以实现更复杂的查找逻辑
        # 例如根据URL哈希查找等
        return None
    
    async def _generate_unique_short_code(self, custom_alias: Optional[str] = None) -> str:
        """生成唯一的短链接代码"""
        if custom_alias:
            # 检查自定义别名是否已存在
            existing = await self.repository.get_url_by_custom_alias(custom_alias)
            if existing:
                raise ShortURLExistsError(custom_alias)
            return custom_alias
        
        # 生成随机短代码
        max_attempts = 100
        for attempt in range(max_attempts):
            short_code = self.short_url_generator.generate_random()
            
            # 检查是否已存在
            existing = await self.repository.get_url_by_short_code(short_code)
            if not existing:
                return short_code
        
        # 如果无法生成唯一代码，尝试更长的代码
        self.short_url_generator.length += 1
        for attempt in range(max_attempts):
            short_code = self.short_url_generator.generate_random()
            existing = await self.repository.get_url_by_short_code(short_code)
            if not existing:
                return short_code
        
        raise ShortURLGenerationError()
    
    async def _build_url_response(self, url_model: URLModel) -> URLResponse:
        """构建URL响应对象"""
        return URLResponse(
            id=url_model.id,
            original_url=url_model.original_url,
            short_url=f"{settings.base_url}/{url_model.short_code}",
            short_code=url_model.short_code,
            created_at=url_model.created_at,
            expires_at=url_model.expires_at,
            is_active=url_model.is_active,
            click_count=url_model.click_count,
            description=url_model.description,
            custom_alias=url_model.custom_alias
        )
    
    def _calculate_performance_rating(self, click_count: int, days_active: int) -> str:
        """计算性能评级"""
        if days_active == 0:
            return "new"
        
        avg_clicks = click_count / days_active
        
        if avg_clicks >= 10:
            return "excellent"
        elif avg_clicks >= 5:
            return "good"
        elif avg_clicks >= 1:
            return "average"
        else:
            return "low" 