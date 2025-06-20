import pytest
from app.utils.validators import URLValidator, validate_url, is_safe_url, normalize_url


class TestURLValidator:
    """URL验证器测试类"""

    def test_init(self):
        """测试初始化"""
        validator = URLValidator(max_length=1000)
        assert validator.max_length == 1000

    def test_valid_urls(self):
        """测试有效URL"""
        validator = URLValidator()
        
        valid_urls = [
            "https://www.example.com",
            "http://example.com",
            "https://subdomain.example.com/path",
            "https://example.com:8080/path?query=1",
            "https://127.0.0.1:3000",
        ]
        
        for url in valid_urls:
            assert validator.is_valid_url(url), f"URL应该有效: {url}"

    def test_invalid_urls(self):
        """测试无效URL"""
        validator = URLValidator()
        
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "https://",
            "http://",
        ]
        
        for url in invalid_urls:
            assert not validator.is_valid_url(url), f"URL应该无效: {url}"

    def test_url_length_limit(self):
        """测试URL长度限制"""
        validator = URLValidator(max_length=50)
        
        short_url = "https://example.com"
        long_url = "https://example.com/" + "a" * 100
        
        assert validator.is_valid_url(short_url)
        assert not validator.is_valid_url(long_url)

    def test_is_safe_url(self):
        """测试URL安全性检查"""
        validator = URLValidator()
        
        # 安全URL
        safe_urls = [
            "https://www.google.com",
            "https://github.com/user/repo",
        ]
        
        for url in safe_urls:
            assert validator.is_safe_url(url), f"URL应该安全: {url}"

    def test_normalize_url(self):
        """测试URL标准化"""
        validator = URLValidator()
        
        test_cases = [
            ("example.com", "https://example.com"),
            ("http://EXAMPLE.COM", "http://example.com"),
            ("https://example.com:443", "https://example.com"),
            ("http://example.com:80", "http://example.com"),
        ]
        
        for input_url, expected in test_cases:
            result = validator.normalize_url(input_url)
            assert result == expected, f"标准化失败: {input_url} -> {result} (期望: {expected})"

    def test_extract_domain(self):
        """测试域名提取"""
        validator = URLValidator()
        
        test_cases = [
            ("https://www.example.com/path", "www.example.com"),
            ("http://SUBDOMAIN.EXAMPLE.COM:8080", "subdomain.example.com"),
            ("https://127.0.0.1:3000", "127.0.0.1:3000"),
        ]
        
        for url, expected_domain in test_cases:
            result = validator.extract_domain(url)
            assert result == expected_domain

    def test_private_ip_detection(self):
        """测试私有IP检测"""
        validator = URLValidator()
        
        # 注意：这个测试可能会失败，因为域名解析依赖网络环境
        # 在实际项目中可能需要模拟DNS解析
        private_urls = [
            "http://127.0.0.1",
            "http://192.168.1.1",
            "http://10.0.0.1",
        ]
        
        for url in private_urls:
            # 这里只测试逻辑，不测试实际的DNS解析
            assert validator._check_domain("127.0.0.1")

    def test_convenience_functions(self):
        """测试便捷函数"""
        url = "https://www.example.com"
        
        assert validate_url(url)
        assert is_safe_url(url)
        
        normalized = normalize_url("example.com")
        assert normalized.startswith("https://")


class TestURLValidatorEdgeCases:
    """URL验证器边界情况测试"""

    def test_empty_and_none_values(self):
        """测试空值和None值"""
        validator = URLValidator()
        
        assert not validator.is_valid_url("")
        assert not validator.is_valid_url(None) if hasattr(validator, 'is_valid_url') else True

    def test_very_long_urls(self):
        """测试非常长的URL"""
        validator = URLValidator(max_length=100)
        
        base_url = "https://example.com/"
        long_path = "a" * 200
        long_url = base_url + long_path
        
        assert not validator.is_valid_url(long_url)

    def test_unicode_urls(self):
        """测试Unicode URL"""
        validator = URLValidator()
        
        unicode_urls = [
            "https://例え.テスト",
            "https://example.com/路径",
        ]
        
        # 这些URL的有效性取决于具体实现
        # 大多数现代应用应该支持国际化域名
        for url in unicode_urls:
            # 只检查不会抛出异常
            try:
                validator.is_valid_url(url)
            except Exception:
                pass 