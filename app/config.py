from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """应用程序配置设置"""
    
    # 应用基本配置
    app_name: str = Field(default="URL Shortener Service", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    
    # MySQL数据库配置
    mysql_host: str = Field(default=os.environ.get("MYSQL_HOST", "10.3.80.24"), description="MySQL主机")
    mysql_port: int = Field(default=int(os.environ.get("MYSQL_PORT", "32647")), description="MySQL端口")
    mysql_user: str = Field(default=os.environ.get("MYSQL_USER", "knowledge"), description="MySQL用户名")
    mysql_password: str = Field(default=os.environ.get("MYSQL_PASSWORD", "Weichai@123"), description="MySQL密码")
    mysql_database: str = Field(default=os.environ.get("MYSQL_DATABASE", "knowledge_db"), description="MySQL数据库名")
    mysql_charset: str = Field(default=os.environ.get("MYSQL_CHARSET", "utf8mb4"), description="MySQL字符集")
    
    @property
    def database_url(self) -> str:
        """构建数据库连接URL"""
        # 对密码进行 URL 编码，确保特殊字符被正确处理
        encoded_password = quote_plus(self.mysql_password)
        return (
            f"mysql+aiomysql://{self.mysql_user}:{encoded_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset={self.mysql_charset}"
        )
    
    database_pool_size: int = Field(default=20, description="数据库连接池大小")
    database_max_overflow: int = Field(default=30, description="数据库连接池最大溢出")
    
    # Redis配置
    redis_host: str = Field(default=os.environ.get("REDIS_HOST", "10.3.80.24"), description="Redis主机")
    redis_port: int = Field(default=int(os.environ.get("REDIS_PORT", "30223")), description="Redis端口")
    redis_password: str = Field(default=os.environ.get("REDIS_PASSWORD", ""), description="Redis密码")
    redis_db: int = Field(default=int(os.environ.get("REDIS_DB", "0")), description="Redis数据库")
    
    @property
    def redis_url(self) -> str:
        """构建Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    redis_ttl: int = Field(default=3600, description="Redis缓存过期时间(秒)")
    
    # URL短链接配置
    base_url: str = Field(default="http://localhost:8000", description="短链接基础URL")
    short_url_length: int = Field(default=6, description="短链接长度")
    max_url_length: int = Field(default=2048, description="原始URL最大长度")
    url_expiry_days: int = Field(default=365, description="URL过期天数")
    
    # 速率限制配置
    rate_limit_requests: int = Field(default=100, description="速率限制请求数")
    rate_limit_window: int = Field(default=3600, description="速率限制时间窗口(秒)")
    
    # 安全配置
    secret_key: str = Field(default="your-super-secret-key-change-in-production", description="密钥")
    algorithm: str = Field(default="HS256", description="加密算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局设置实例
settings = Settings() 