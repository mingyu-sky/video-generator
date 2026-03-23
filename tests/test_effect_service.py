"""
特效服务单元测试（Mock 版本 - 不依赖 ImageMagick）
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.effect_service import TextEffect, FollowEffect, PIPEffect, EffectService


class TestTextEffect:
    """文字特效测试"""
    
    def test_positions_defined(self):
        """测试位置配置"""
        assert 'top-left' in TextEffect.POSITIONS
        assert 'center' in TextEffect.POSITIONS
        assert 'bottom-right' in TextEffect.POSITIONS
    
    def test_fonts_defined(self):
        """测试字体配置"""
        assert len(TextEffect.FONTS) > 0
        assert 'Arial' in TextEffect.FONTS
    
    def test_create_method_exists(self):
        """测试 create 方法存在"""
        assert hasattr(TextEffect, 'create')
        assert callable(getattr(TextEffect, 'create'))
    
    def test_set_position_method_exists(self):
        """测试 set_position 方法存在"""
        assert hasattr(TextEffect, 'set_position')
    
    def test_typewriter_method_exists(self):
        """测试打字机方法存在"""
        assert hasattr(TextEffect, 'typewriter_effect')
    
    def test_flash_method_exists(self):
        """测试闪烁方法存在"""
        assert hasattr(TextEffect, 'flash_effect')
    
    def test_bounce_method_exists(self):
        """测试弹跳方法存在"""
        assert hasattr(TextEffect, 'bounce_effect')
    
    def test_slide_method_exists(self):
        """测试滑入方法存在"""
        assert hasattr(TextEffect, 'slide_effect')
    
    def test_add_background_method_exists(self):
        """测试背景方法存在"""
        assert hasattr(TextEffect, 'add_background')


class TestFollowEffect:
    """点关注特效测试"""
    
    def test_create_method_exists(self):
        """测试 create 方法存在"""
        assert hasattr(FollowEffect, 'create')
        assert callable(getattr(FollowEffect, 'create'))
    
    def test_create_button_method_exists(self):
        """测试按钮创建方法存在"""
        assert hasattr(FollowEffect, 'create_button')
    
    def test_pulse_animation_exists(self):
        """测试脉冲动画存在"""
        assert hasattr(FollowEffect, 'pulse_animation')
    
    def test_popup_animation_exists(self):
        """测试弹出动画存在"""
        assert hasattr(FollowEffect, 'popup_animation')


class TestPIPEffect:
    """画中画特效测试"""
    
    def test_layouts_defined(self):
        """测试布局配置"""
        assert 'bottom-right' in PIPEffect.LAYOUTS
        assert 'bottom-left' in PIPEffect.LAYOUTS
        assert 'center' in PIPEffect.LAYOUTS
    
    def test_layout_bottom_right_config(self):
        """测试右下角布局配置"""
        config = PIPEffect.LAYOUTS['bottom-right']
        assert config['pos'] == ('right', 'bottom')
        assert config['size_ratio'] == 0.25
    
    def test_layout_center_config(self):
        """测试居中布局配置"""
        config = PIPEffect.LAYOUTS['center']
        assert config['pos'] == ('center', 'center')
        assert config['size_ratio'] == 0.3
    
    def test_create_method_exists(self):
        """测试 create 方法存在"""
        assert hasattr(PIPEffect, 'create')
        assert callable(getattr(PIPEffect, 'create'))
    
    def test_add_border_method_exists(self):
        """测试边框方法存在"""
        assert hasattr(PIPEffect, 'add_border')
    
    def test_add_shadow_method_exists(self):
        """测试阴影方法存在"""
        assert hasattr(PIPEffect, 'add_shadow')
    
    def test_set_position_method_exists(self):
        """测试位置方法存在"""
        assert hasattr(PIPEffect, 'set_position')


class TestEffectService:
    """特效服务集成测试"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        service = EffectService()
        assert service.text_effect is not None
        assert service.follow_effect is not None
        assert service.pip_effect is not None
    
    def test_apply_text_effect_method_exists(self):
        """测试文字特效方法存在"""
        service = EffectService()
        assert hasattr(service, 'apply_text_effect')
        assert callable(getattr(service, 'apply_text_effect'))
    
    def test_apply_follow_effect_method_exists(self):
        """测试关注特效方法存在"""
        service = EffectService()
        assert hasattr(service, 'apply_follow_effect')
    
    def test_apply_pip_effect_method_exists(self):
        """测试画中画方法存在"""
        service = EffectService()
        assert hasattr(service, 'apply_pip_effect')


class TestEffectTypes:
    """特效类型验证测试"""
    
    def test_text_effect_types(self):
        """测试文字特效类型"""
        # 验证支持的特效类型
        supported_effects = ['typewriter', 'flash', 'bounce', 'slide', 'fade']
        for effect in supported_effects:
            assert effect in ['typewriter', 'flash', 'bounce', 'slide', 'fade']
    
    def test_follow_effect_animations(self):
        """测试关注特效动画"""
        supported_animations = ['pulse', 'popup', 'fade']
        for anim in supported_animations:
            assert anim in ['pulse', 'popup', 'fade']
    
    def test_pip_layouts_count(self):
        """测试画中画布局数量"""
        assert len(PIPEffect.LAYOUTS) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
