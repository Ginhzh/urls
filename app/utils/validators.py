import re
import urllib.parse
from typing import List, Set
from urllib.parse import urlparse
import socket
import ipaddress


class URLValidator:
    """URL验证器"""
    
    # 危险的域名后缀
    DANGEROUS_TLDS = {
        'tk', 'ml', 'ga', 'cf'  # 常见的免费域名
    }
    
    # 不允许的协议
    BLOCKED_SCHEMES = {
        'javascript', 'data', 'vbscript', 'file', 'ftp'
    }
    
    # 允许的协议
    ALLOWED_SCHEMES = {
        'http', 'https'
    }
    
    # 黑名单域名（示例）
    BLACKLISTED_DOMAINS = {
        'malicious-site.com',
        'phishing-example.com'
    }
    
    # 私有IP地址范围
    PRIVATE_IP_RANGES = [
        '10.0.0.0/8',
        '172.16.0.0/12',
        '192.168.0.0/16',
        '127.0.0.0/8',
        '169.254.0.0/16'
    ]
    
    def __init__(self, max_length: int = 2048):
        """
        初始化URL验证器
        
        Args:
            max_length: URL最大长度
        """
        self.max_length = max_length
    
    def is_valid_url(self, url: str) -> bool:
        """
        验证URL是否有效
        
        Args:
            url: 要验证的URL
            
        Returns:
            bool: URL是否有效
        """
        try:
            # 基本长度检查
            if not self._check_length(url):
                return False
            
            # 解析URL
            parsed = urlparse(url)
            
            # 检查协议
            if not self._check_scheme(parsed.scheme):
                return False
            
            # 检查域名
            if not self._check_domain(parsed.netloc):
                return False
            
            # 检查是否在黑名单中
            if self._is_blacklisted(parsed.netloc):
                return False
            
            # 检查是否指向私有IP
            if self._points_to_private_ip(parsed.netloc):
                return False
            
            return True
            
        except Exception:
            return False
    
    def is_safe_url(self, url: str) -> bool:
        """
        检查URL是否安全（更严格的检查）
        
        Args:
            url: 要检查的URL
            
        Returns:
            bool: URL是否安全
        """
        if not self.is_valid_url(url):
            return False
        
        parsed = urlparse(url)
        
        # 检查是否使用HTTPS
        if parsed.scheme != 'https':
            # 对于HTTP协议，进行额外检查
            pass
        
        # 检查域名是否可疑
        if self._is_suspicious_domain(parsed.netloc):
            return False
        
        # 检查URL路径是否包含可疑内容
        if self._has_suspicious_path(parsed.path):
            return False
        
        return True
    
    def normalize_url(self, url: str) -> str:
        """
        标准化URL
        
        Args:
            url: 原始URL
            
        Returns:
            str: 标准化后的URL
        """
        # 移除空白字符
        url = url.strip()
        
        # 如果没有协议，默认添加https
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # 解析并重构URL
        parsed = urlparse(url)
        
        # 标准化域名（转为小写）
        netloc = parsed.netloc.lower()
        
        # 移除默认端口
        if netloc.endswith(':80') and parsed.scheme == 'http':
            netloc = netloc[:-3]
        elif netloc.endswith(':443') and parsed.scheme == 'https':
            netloc = netloc[:-4]
        
        # 重构URL
        normalized = urllib.parse.urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return normalized
    
    def extract_domain(self, url: str) -> str:
        """
        从URL中提取域名
        
        Args:
            url: URL字符串
            
        Returns:
            str: 域名
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""
    
    def _check_length(self, url: str) -> bool:
        """检查URL长度"""
        return 0 < len(url) <= self.max_length
    
    def _check_scheme(self, scheme: str) -> bool:
        """检查URL协议"""
        scheme = scheme.lower()
        
        # 检查是否是被禁止的协议
        if scheme in self.BLOCKED_SCHEMES:
            return False
        
        # 检查是否是允许的协议
        return scheme in self.ALLOWED_SCHEMES
    
    def _check_domain(self, netloc: str) -> bool:
        """检查域名格式"""
        if not netloc:
            return False
        
        # 移除端口号
        domain = netloc.split(':')[0]
        
        # 基本格式检查
        if not domain or domain.startswith('.') or domain.endswith('.'):
            return False
        
        # 检查是否是IP地址
        try:
            ipaddress.ip_address(domain)
            return True  # IP地址格式正确
        except ValueError:
            pass
        
        # 检查域名格式
        domain_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        )
        
        return bool(domain_pattern.match(domain))
    
    def _is_blacklisted(self, netloc: str) -> bool:
        """检查域名是否在黑名单中"""
        domain = netloc.split(':')[0].lower()
        return domain in self.BLACKLISTED_DOMAINS
    
    def _points_to_private_ip(self, netloc: str) -> bool:
        """检查域名是否指向私有IP"""
        domain = netloc.split(':')[0]
        
        try:
            # 尝试解析域名
            ip = socket.gethostbyname(domain)
            ip_obj = ipaddress.ip_address(ip)
            
            # 检查是否是私有IP
            for range_str in self.PRIVATE_IP_RANGES:
                if ip_obj in ipaddress.ip_network(range_str):
                    return True
            
            return False
            
        except (socket.gaierror, ValueError):
            # 无法解析域名或IP格式错误
            return False
    
    def _is_suspicious_domain(self, netloc: str) -> bool:
        """检查域名是否可疑"""
        domain = netloc.split(':')[0].lower()
        
        # 检查顶级域名
        domain_parts = domain.split('.')
        if len(domain_parts) > 1:
            tld = domain_parts[-1]
            if tld in self.DANGEROUS_TLDS:
                return True
        
        # 检查域名长度（过长的域名可能是可疑的）
        if len(domain) > 100:
            return True
        
        # 检查是否包含过多的连字符
        if domain.count('-') > 5:
            return True
        
        return False
    
    def _has_suspicious_path(self, path: str) -> bool:
        """检查URL路径是否包含可疑内容"""
        suspicious_patterns = [
            r'\.\./',  # 路径遍历
            r'<script',  # XSS攻击
            r'javascript:',  # JavaScript协议
            r'data:',  # Data协议
        ]
        
        path_lower = path.lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, path_lower):
                return True
        
        return False


# 全局验证器实例
default_validator = URLValidator()


def validate_url(url: str, max_length: int = 2048) -> bool:
    """验证URL的便捷函数"""
    validator = URLValidator(max_length)
    return validator.is_valid_url(url)


def is_safe_url(url: str) -> bool:
    """检查URL安全性的便捷函数"""
    return default_validator.is_safe_url(url)


def normalize_url(url: str) -> str:
    """标准化URL的便捷函数"""
    return default_validator.normalize_url(url) 