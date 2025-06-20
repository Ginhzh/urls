import random
import string
import hashlib
import base64
from typing import Set
import secrets


class ShortURLGenerator:
    """短链接生成器"""
    
    # 字符集合（排除容易混淆的字符）
    CHARS = string.ascii_letters + string.digits
    SAFE_CHARS = ''.join(c for c in CHARS if c not in 'il1Lo0O')
    
    def __init__(self, length: int = 6):
        """
        初始化短链接生成器
        
        Args:
            length: 生成的短链接长度
        """
        self.length = length
        self.used_codes: Set[str] = set()
    
    def generate_random(self) -> str:
        """生成随机短链接代码"""
        return ''.join(secrets.choice(self.SAFE_CHARS) for _ in range(self.length))
    
    def generate_from_url(self, url: str) -> str:
        """基于URL内容生成短链接代码"""
        # 使用MD5哈希
        hash_object = hashlib.md5(url.encode())
        hex_dig = hash_object.hexdigest()
        
        # 转换为base62编码
        return self._hex_to_base62(hex_dig)[:self.length]
    
    def generate_sequential(self, counter: int) -> str:
        """生成序列化短链接代码"""
        return self._int_to_base62(counter)
    
    def generate_with_timestamp(self) -> str:
        """基于时间戳生成短链接代码"""
        import time
        timestamp = int(time.time() * 1000)  # 毫秒时间戳
        base_code = self._int_to_base62(timestamp)
        
        # 如果长度不够，补充随机字符
        if len(base_code) < self.length:
            random_suffix = ''.join(
                secrets.choice(self.SAFE_CHARS) 
                for _ in range(self.length - len(base_code))
            )
            return base_code + random_suffix
        
        return base_code[:self.length]
    
    def generate_unique(self, max_attempts: int = 100) -> str:
        """
        生成唯一的短链接代码
        
        Args:
            max_attempts: 最大尝试次数
            
        Returns:
            唯一的短链接代码
            
        Raises:
            Exception: 如果无法生成唯一代码
        """
        for _ in range(max_attempts):
            code = self.generate_random()
            if code not in self.used_codes:
                self.used_codes.add(code)
                return code
        
        raise Exception("无法生成唯一的短链接代码")
    
    def is_valid_code(self, code: str) -> bool:
        """验证短链接代码是否有效"""
        if not code:
            return False
        
        if len(code) > 50:  # 设置最大长度限制
            return False
        
        # 检查字符是否都在允许的字符集中
        return all(c in self.SAFE_CHARS for c in code)
    
    def add_used_code(self, code: str):
        """添加已使用的代码到集合中"""
        self.used_codes.add(code)
    
    def remove_used_code(self, code: str):
        """从已使用代码集合中移除代码"""
        self.used_codes.discard(code)
    
    def _int_to_base62(self, num: int) -> str:
        """将整数转换为base62编码"""
        if num == 0:
            return self.SAFE_CHARS[0]
        
        result = []
        base = len(self.SAFE_CHARS)
        
        while num:
            result.append(self.SAFE_CHARS[num % base])
            num //= base
        
        return ''.join(reversed(result))
    
    def _hex_to_base62(self, hex_string: str) -> str:
        """将十六进制字符串转换为base62编码"""
        # 将十六进制转换为整数
        num = int(hex_string, 16)
        return self._int_to_base62(num)
    
    def _base62_to_int(self, base62_string: str) -> int:
        """将base62编码转换为整数"""
        num = 0
        base = len(self.SAFE_CHARS)
        
        for char in base62_string:
            num = num * base + self.SAFE_CHARS.index(char)
        
        return num
    
    @classmethod
    def create_custom_generator(cls, charset: str, length: int = 6) -> 'ShortURLGenerator':
        """创建自定义字符集的生成器"""
        generator = cls(length)
        generator.SAFE_CHARS = charset
        return generator


# 全局生成器实例
default_generator = ShortURLGenerator()


def generate_short_code(length: int = 6) -> str:
    """生成短链接代码的便捷函数"""
    generator = ShortURLGenerator(length)
    return generator.generate_random()


def validate_short_code(code: str) -> bool:
    """验证短链接代码的便捷函数"""
    generator = ShortURLGenerator()
    return generator.is_valid_code(code) 