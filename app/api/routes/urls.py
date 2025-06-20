from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from typing import Optional

from app.schemas.url import (
    URLCreateRequest, 
    URLResponse, 
    URLStatsResponse, 
    URLListResponse,
    ErrorResponse
)
from app.services.url_service import URLService
from app.api.dependencies import get_url_service, get_client_ip, get_user_agent
from app.exceptions.custom_exceptions import (
    URLNotFoundError,
    URLExpiredError,
    InvalidURLError,
    URLTooLongError,
    ShortURLExistsError,
    ShortURLGenerationError
)

router = APIRouter()


@router.post(
    "/shorten",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建短链接",
    description="创建一个新的短链接",
    responses={
        201: {"description": "短链接创建成功"},
        400: {"model": ErrorResponse, "description": "请求无效"},
        409: {"model": ErrorResponse, "description": "短链接已存在"},
        422: {"description": "验证错误"}
    }
)
async def create_short_url(
    request_data: URLCreateRequest,
    request: Request,
    url_service: URLService = Depends(get_url_service),
    client_ip: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent)
):
    """创建短链接"""
    try:
        result = await url_service.create_short_url(
            request=request_data,
            creator_ip=client_ip,
            user_agent=user_agent
        )
        return result
    except (InvalidURLError, URLTooLongError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail
        )
    except ShortURLExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except ShortURLGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail
        )


@router.get(
    "/{short_code}",
    summary="重定向到原始URL",
    description="根据短链接代码重定向到原始URL",
    responses={
        302: {"description": "重定向到原始URL"},
        404: {"model": ErrorResponse, "description": "短链接不存在"},
        410: {"model": ErrorResponse, "description": "短链接已过期"}
    }
)
async def redirect_to_original_url(
    short_code: str,
    url_service: URLService = Depends(get_url_service)
):
    """重定向到原始URL"""
    try:
        original_url = await url_service.resolve_short_url(short_code)
        return RedirectResponse(
            url=original_url,
            status_code=status.HTTP_302_FOUND
        )
    except URLNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except URLExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=e.detail
        )


@router.get(
    "/info/{short_code}",
    response_model=URLStatsResponse,
    summary="获取短链接信息",
    description="获取短链接的详细信息和统计数据",
    responses={
        200: {"description": "短链接信息"},
        404: {"model": ErrorResponse, "description": "短链接不存在"}
    }
)
async def get_url_info(
    short_code: str,
    url_service: URLService = Depends(get_url_service)
):
    """获取短链接信息"""
    try:
        return await url_service.get_url_info(short_code)
    except URLNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )


@router.get(
    "/analytics/{short_code}",
    summary="获取短链接分析数据",
    description="获取短链接的详细分析数据",
    responses={
        200: {"description": "分析数据"},
        404: {"model": ErrorResponse, "description": "短链接不存在"}
    }
)
async def get_url_analytics(
    short_code: str,
    url_service: URLService = Depends(get_url_service)
):
    """获取短链接分析数据"""
    try:
        return await url_service.get_url_analytics(short_code)
    except URLNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )


@router.get(
    "/list",
    response_model=URLListResponse,
    summary="获取短链接列表",
    description="分页获取短链接列表",
    responses={
        200: {"description": "短链接列表"}
    }
)
async def list_urls(
    page: int = 1,
    size: int = 10,
    is_active: Optional[bool] = None,
    request: Request = None,
    url_service: URLService = Depends(get_url_service),
    client_ip: str = Depends(get_client_ip)
):
    """获取短链接列表"""
    # 限制每页大小
    size = min(size, 100)
    
    return await url_service.list_urls(
        page=page,
        size=size,
        is_active=is_active,
        creator_ip=client_ip  # 只显示当前IP创建的短链接
    )


@router.patch(
    "/deactivate/{short_code}",
    summary="停用短链接",
    description="停用指定的短链接",
    responses={
        200: {"description": "短链接已停用"},
        404: {"model": ErrorResponse, "description": "短链接不存在"}
    }
)
async def deactivate_url(
    short_code: str,
    url_service: URLService = Depends(get_url_service)
):
    """停用短链接"""
    try:
        success = await url_service.deactivate_url(short_code)
        if success:
            return {"message": "短链接已停用"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="停用失败"
            )
    except URLNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )


@router.delete(
    "/{short_code}",
    summary="删除短链接",
    description="删除指定的短链接",
    responses={
        200: {"description": "短链接已删除"},
        404: {"model": ErrorResponse, "description": "短链接不存在"}
    }
)
async def delete_url(
    short_code: str,
    url_service: URLService = Depends(get_url_service)
):
    """删除短链接"""
    try:
        success = await url_service.delete_url(short_code)
        if success:
            return {"message": "短链接已删除"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除失败"
            )
    except URLNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )


@router.post(
    "/cleanup-expired",
    summary="清理过期链接",
    description="清理所有过期的短链接",
    responses={
        200: {"description": "清理完成"}
    }
)
async def cleanup_expired_urls(
    url_service: URLService = Depends(get_url_service)
):
    """清理过期链接"""
    count = await url_service.cleanup_expired_urls()
    return {
        "message": f"已清理 {count} 个过期短链接",
        "count": count
    }


# 健康检查端点
@router.get(
    "/health",
    summary="健康检查",
    description="检查服务健康状态",
    include_in_schema=False
)
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "url-shortener",
        "timestamp": "2024-01-01T00:00:00Z"  # 在实际应用中应该使用真实时间戳
    } 