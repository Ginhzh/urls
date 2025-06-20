import pytest
from app.utils.short_url_generator import ShortURLGenerator, generate_short_code, validate_short_code


class TestShortURLGenerator:
    """短链接生成器测试类"""

    def test_init(self):
        """测试初始化"""
        generator = ShortURLGenerator(length=8)
        assert generator.length == 8
        assert len(generator.used_codes) == 0

    def test_generate_random(self):
        """测试生成随机短链接"""
        generator = ShortURLGenerator(length=6)
        code = generator.generate_random()
        
        assert len(code) == 6
        assert generator.is_valid_code(code)

    def test_generate_from_url(self):
        """测试基于URL生成短链接"""
        generator = ShortURLGenerator(length=6)
        url = "https://www.example.com"
        
        code1 = generator.generate_from_url(url)
        code2 = generator.generate_from_url(url)
        
        # 相同URL应该生成相同的代码
        assert code1 == code2
        assert len(code1) == 6

    def test_generate_sequential(self):
        """测试序列化生成"""
        generator = ShortURLGenerator()
        
        code1 = generator.generate_sequential(1)
        code2 = generator.generate_sequential(2)
        
        assert code1 != code2
        assert generator.is_valid_code(code1)
        assert generator.is_valid_code(code2)

    def test_generate_with_timestamp(self):
        """测试基于时间戳生成"""
        generator = ShortURLGenerator(length=6)
        
        code = generator.generate_with_timestamp()
        
        assert len(code) == 6
        assert generator.is_valid_code(code)

    def test_generate_unique(self):
        """测试生成唯一代码"""
        generator = ShortURLGenerator(length=6)
        
        # 生成多个代码，应该都是唯一的
        codes = set()
        for _ in range(10):
            code = generator.generate_unique()
            assert code not in codes
            codes.add(code)

    def test_is_valid_code(self):
        """测试代码验证"""
        generator = ShortURLGenerator()
        
        # 有效代码
        assert generator.is_valid_code("abc123")
        assert generator.is_valid_code("XYZ789")
        
        # 无效代码
        assert not generator.is_valid_code("")
        assert not generator.is_valid_code("abc@123")  # 包含特殊字符
        assert not generator.is_valid_code("a" * 100)  # 过长

    def test_add_remove_used_code(self):
        """测试添加和移除已使用代码"""
        generator = ShortURLGenerator()
        
        code = "test123"
        generator.add_used_code(code)
        assert code in generator.used_codes
        
        generator.remove_used_code(code)
        assert code not in generator.used_codes

    def test_custom_generator(self):
        """测试自定义字符集生成器"""
        charset = "0123456789"
        generator = ShortURLGenerator.create_custom_generator(charset, length=4)
        
        code = generator.generate_random()
        assert len(code) == 4
        assert all(c in charset for c in code)

    def test_convenience_functions(self):
        """测试便捷函数"""
        code = generate_short_code(8)
        assert len(code) == 8
        
        assert validate_short_code(code)
        assert not validate_short_code("invalid@code") 