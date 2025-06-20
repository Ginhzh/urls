from fastapi import HTTPException
from typing import Optional, Dict, Any


class BaseCustomException(HTTPException):
    """自定义异常基类"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class URLNotFoundError(BaseCustomException):
    """URL不存在异常"""
    
    def __init__(self, short_url: str):
        super().__init__(
            status_code=404,
            detail=f"短链接 '{short_url}' 不存在"
        )


class URLExpiredError(BaseCustomException):
    """URL已过期异常"""
    
    def __init__(self, short_url: str):
        super().__init__(
            status_code=410,
            detail=f"短链接 '{short_url}' 已过期"
        )


class InvalidURLError(BaseCustomException):
    """无效URL异常"""
    
    def __init__(self, url: str):
        super().__init__(
            status_code=400,
            detail=f"无效的URL: '{url}'"
        )


class URLTooLongError(BaseCustomException):
    """URL过长异常"""
    
    def __init__(self, max_length: int):
        super().__init__(
            status_code=400,
            detail=f"URL长度不能超过 {max_length} 个字符"
        )


class ShortURLExistsError(BaseCustomException):
    """短链接已存在异常"""
    
    def __init__(self, short_url: str):
        super().__init__(
            status_code=409,
            detail=f"短链接 '{short_url}' 已存在"
        )


class DatabaseError(BaseCustomException):
    """数据库操作异常"""
    
    def __init__(self, detail: str = "数据库操作失败"):
        super().__init__(
            status_code=500,
            detail=detail
        )


class CacheError(BaseCustomException):
    """缓存操作异常"""
    
    def __init__(self, detail: str = "缓存操作失败"):
        super().__init__(
            status_code=500,
            detail=detail
        )


class RateLimitExceededError(BaseCustomException):
    """频率限制超出异常"""
    
    def __init__(self, retry_after: int = 3600):
        super().__init__(
            status_code=429,
            detail="请求频率过高，请稍后再试",
            headers={"Retry-After": str(retry_after)}
        )


class ShortURLGenerationError(BaseCustomException):
    """短链接生成失败异常"""
    
    def __init__(self, detail: str = "无法生成唯一的短链接"):
        super().__init__(
            status_code=500,
            detail=detail
        ) 