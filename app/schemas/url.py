from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional
from datetime import datetime
import re


class URLCreateRequest(BaseModel):
    """创建短链接请求模式"""
    
    original_url: HttpUrl = Field(
        ..., 
        description="原始URL",
        example="https://www.example.com/very/long/url/path"
    )
    
    custom_alias: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description="自定义别名（可选）",
        example="my-custom-link"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="链接描述（可选）",
        example="这是一个示例链接"
    )
    
    expires_in_days: Optional[int] = Field(
        None,
        ge=1,
        le=3650,  # 最多10年
        description="过期天数（可选）",
        example=30
    )
    
    @validator('custom_alias')
    def validate_custom_alias(cls, v):
        if v is not None:
            # 只允许字母、数字、连字符和下划线
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('自定义别名只能包含字母、数字、连字符和下划线')
            # 不能以连字符开头或结尾
            if v.startswith('-') or v.endswith('-'):
                raise ValueError('自定义别名不能以连字符开头或结尾')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_url": "https://www.example.com/very/long/url/path",
                "custom_alias": "my-link",
                "description": "这是一个示例链接",
                "expires_in_days": 30
            }
        }


class URLResponse(BaseModel):
    """短链接响应模式"""
    
    id: int = Field(..., description="URL ID")
    original_url: str = Field(..., description="原始URL")
    short_url: str = Field(..., description="短链接")
    short_code: str = Field(..., description="短链接代码")
    created_at: datetime = Field(..., description="创建时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: bool = Field(..., description="是否激活")
    click_count: int = Field(..., description="点击次数")
    description: Optional[str] = Field(None, description="描述")
    custom_alias: Optional[str] = Field(None, description="自定义别名")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "original_url": "https://www.example.com/very/long/url/path",
                "short_url": "http://localhost:8000/abc123",
                "short_code": "abc123",
                "created_at": "2024-01-01T12:00:00Z",
                "expires_at": "2024-02-01T12:00:00Z",
                "is_active": True,
                "click_count": 0,
                "description": "这是一个示例链接",
                "custom_alias": "my-link"
            }
        }


class URLStatsResponse(BaseModel):
    """URL统计信息响应模式"""
    
    id: int = Field(..., description="URL ID")
    original_url: str = Field(..., description="原始URL")
    short_url: str = Field(..., description="短链接")
    short_code: str = Field(..., description="短链接代码")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: bool = Field(..., description="是否激活")
    click_count: int = Field(..., description="点击次数")
    last_accessed_at: Optional[datetime] = Field(None, description="最后访问时间")
    description: Optional[str] = Field(None, description="描述")
    custom_alias: Optional[str] = Field(None, description="自定义别名")
    is_expired: bool = Field(..., description="是否已过期")
    
    class Config:
        from_attributes = True


class URLListResponse(BaseModel):
    """URL列表响应模式"""
    
    urls: list[URLResponse] = Field(..., description="URL列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "urls": [
                    {
                        "id": 1,
                        "original_url": "https://www.example.com",
                        "short_url": "http://localhost:8000/abc123",
                        "short_code": "abc123",
                        "created_at": "2024-01-01T12:00:00Z",
                        "expires_at": None,
                        "is_active": True,
                        "click_count": 5,
                        "description": None,
                        "custom_alias": None
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10,
                "pages": 1
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模式"""
    
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="详细信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "URL_NOT_FOUND",
                "message": "短链接不存在",
                "detail": "短链接 'abc123' 不存在"
            }
        } 