from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func, text
from datetime import datetime, timezone
from typing import Optional

Base = declarative_base()


class URLModel(Base):
    """URL数据模型"""
    
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 原始URL
    original_url = Column(Text, nullable=False)
    
    # 短链接代码（不包含域名）
    short_code = Column(String(20), unique=True, nullable=False, index=True)
    
    # 创建时间
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(),
        server_default=func.now()
    )
    
    # 更新时间
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now()
    )
    
    # 过期时间
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 是否激活
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 点击次数
    click_count = Column(Integer, default=0, nullable=False)
    
    # 最后访问时间
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 创建者IP（可选）
    creator_ip = Column(String(45), nullable=True)
    
    # 用户代理（可选）
    user_agent = Column(Text, nullable=True)
    
    # 描述（可选）
    description = Column(Text, nullable=True)
    
    # 自定义别名（可选）
    custom_alias = Column(String(50), nullable=True, unique=True)
    
    # 索引配置 - 为TEXT字段指定索引长度
    __table_args__ = (
        Index('ix_urls_original_url_prefix', text('original_url(255)')),  # 为TEXT字段指定索引长度
        Index('ix_urls_created_at', 'created_at'),
        Index('ix_urls_expires_at', 'expires_at'),
        Index('ix_urls_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<URLModel(id={self.id}, short_code='{self.short_code}', original_url='{self.original_url[:50]}...')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "original_url": self.original_url,
            "short_code": self.short_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "click_count": self.click_count,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "creator_ip": self.creator_ip,
            "user_agent": self.user_agent,
            "description": self.description,
            "custom_alias": self.custom_alias
        }
    
    @property
    def is_expired(self) -> bool:
        """检查URL是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def increment_click_count(self):
        """增加点击次数"""
        self.click_count += 1
        self.last_accessed_at = datetime.now(timezone.utc) 