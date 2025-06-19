"""
Interactive Feedback Server Utils

工具模块，包含配置管理、规则引擎等核心功能。
Utility modules containing configuration management, rule engine and other core features.
"""

# 导出主要功能模块
from .config_manager import (
    get_config,
    save_config,
    validate_config,
    get_display_mode,
    get_fallback_options,
    get_fallback_options_by_language,
    # V4.1 简化：自定义选项开关
    get_custom_options_enabled,
    set_custom_options_enabled,
    get_feature_enabled,
)
from .rule_engine import (
    resolve_final_options,
    # V4.0 简化：保留核心选项解析功能
)

# V3.2 优化：新增配置辅助工具
from .config_helpers import (
    safe_get_config,
    safe_get_feature_states,
    safe_get_fallback_options,
    handle_config_error,
    safe_config_operation,
)

# V3.2 Day 3 优化：新增文本处理工具 - V4.1 精简版本
from .text_processor import (
    fast_normalize_text,
    fast_extract_keywords,
    fast_find_match,
    get_text_processor,
    get_optimized_matcher,
    # V4.1 移除：get_text_processing_stats未使用
)

__all__ = [
    "get_config",
    "save_config",
    "validate_config",
    "get_display_mode",
    "get_fallback_options",
    "get_fallback_options_by_language",
    "filter_valid_options",  # 新增：公共过滤函数
    # V4.1 简化：自定义选项开关
    "get_custom_options_enabled",
    "set_custom_options_enabled",
    "get_feature_enabled",
    # 文本处理工具 - V4.1 精简版本
    "fast_normalize_text",
    "fast_extract_keywords",
    "fast_find_match",
    "get_text_processor",
    "get_optimized_matcher",
    # V4.1 移除：get_text_processing_stats未使用
    "resolve_final_options",
    # V4.1 简化：保留核心功能
    # 配置辅助工具
    "safe_get_config",
    "safe_get_feature_states",
    "safe_get_fallback_options",
    "handle_config_error",
    "safe_config_operation",
]
