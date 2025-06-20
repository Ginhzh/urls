from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
import structlog
import time
import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes.urls import router as urls_router
from app.database.connection import database
from app.models.url import Base
from app.exceptions.custom_exceptions import BaseCustomException

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    # 启动时
    logger.info("应用程序启动中...")
    
    try:
        # 连接数据库
        await database.connect()
        logger.info("数据库连接成功")
        
        # 连接Redis
        await database.connect_redis()
        logger.info("Redis连接成功")
        
        # 创建数据库表
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表已创建")
        
        logger.info("应用程序启动完成")
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        raise
    
    yield
    
    # 关闭时
    logger.info("应用程序关闭中...")
    
    try:
        await database.disconnect()
        await database.disconnect_redis()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")
    
    logger.info("应用程序已关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    description="一个高性能的URL短链接生成器微服务，基于FastAPI构建",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置受信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # 在生产环境中应该限制具体主机
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    # 记录请求开始
    logger.info(
        "请求开始",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "")
    )
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录请求结束
    logger.info(
        "请求结束",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=round(process_time * 1000, 2)  # 毫秒
    )
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# 异常处理器
@app.exception_handler(BaseCustomException)
async def custom_exception_handler(request: Request, exc: BaseCustomException):
    """自定义异常处理器"""
    logger.error(
        "自定义异常",
        exception=exc.__class__.__name__,
        detail=exc.detail,
        status_code=exc.status_code,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "detail": exc.detail
        },
        headers=exc.headers
    )


@app.exception_handler(HTTPException)
async def http_exception_custom_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.error(
        "HTTP异常",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )
    
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        "未处理的异常",
        exception=exc.__class__.__name__,
        detail=str(exc),
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "服务器内部错误",
            "detail": "请稍后重试或联系系统管理员"
        }
    )


# 注册路由
app.include_router(
    urls_router,
    prefix="/api/v1/urls",
    tags=["URLs"]
)

# 根路径
@app.get("/", include_in_schema=False)
async def root():
    """根路径"""
    return {
        "message": "Welcome to URL Shortener Service",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/urls/health"
    }


# 健康检查端点
@app.get("/health", include_in_schema=False)
async def health_check():
    """应用健康检查"""
    from app.database.connection import check_database_health, check_redis_health
    
    db_healthy = await check_database_health()
    redis_healthy = await check_redis_health()
    
    return {
        "status": "healthy" if db_healthy and redis_healthy else "unhealthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "database": "healthy" if db_healthy else "unhealthy",
        "redis": "healthy" if redis_healthy else "unhealthy",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"启动服务器: {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )