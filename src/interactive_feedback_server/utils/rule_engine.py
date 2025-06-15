# src/interactive_feedback_server/utils/rule_engine.py
"""
规则引擎模块 - V3.3 架构改进版本
Rule Engine Module - V3.3 Architecture Improvement Version

V3.3 架构改进：集成可配置规则引擎，支持外部化配置
V3.3 Architecture Improvement: Integrated configurable rule engine with externalized configuration

V3.2 性能优化：集成缓存机制，显著提升处理速度
V3.2 Performance Optimization: Integrated caching mechanism for significant speed improvement

提供三层回退逻辑：
1. AI提供的选项（第一层）
2. 规则引擎生成的选项（第二层）
3. 用户配置的后备选项（第三层）

Three-layer fallback logic:
1. AI-provided options (first layer)
2. Rule engine generated options (second layer)
3. User-configured fallback options (third layer)
"""

from typing import List, Dict, Any
from .text_processor import fast_find_match

# 规则引擎相关导入已移除 - V4.0 简化

# 核心模式定义 - 精选高频场景
CORE_PATTERNS = {
    # 疑问场景 - 最高优先级
    "question": {
        "triggers": [
            "?",
            "？",
            "是否",
            "如何",
            "怎么",
            "什么",
            "为什么",
            "哪个",
            "哪些",
        ],
        "options": ["是的", "不是", "需要更多信息"],
    },
    # 确认场景 - 高优先级
    "confirmation": {
        "triggers": ["确认", "同意", "继续", "下一步", "开始", "执行", "好的"],
        "options": ["好的，继续", "我明白了", "暂停一下"],
    },
    # 选择场景 - 中优先级
    "choice": {
        "triggers": ["选择", "决定", "考虑", "建议", "推荐", "方案", "选项"],
        "options": ["选择这个", "看看其他的", "让我想想"],
    },
    # 操作场景 - 中优先级
    "action": {
        "triggers": ["修改", "更改", "调整", "优化", "删除", "添加", "创建", "生成"],
        "options": ["执行操作", "先预览", "取消操作"],
    },
}


# V4.0 移除：extract_options_from_text 函数已删除
# 规则引擎功能已完全移除，简化为AI选项+用户自定义选项的2级逻辑


def is_valid_ai_options(ai_options) -> bool:
    """
    严格验证AI选项的有效性 - V3.2边界控制
    Strictly validate the validity of AI options - V3.2 boundary control

    Args:
        ai_options: AI提供的选项

    Returns:
        bool: 是否为有效的AI选项
    """
    # 检查是否为None
    if ai_options is None:
        return False

    # 检查是否为空列表
    if isinstance(ai_options, list) and len(ai_options) == 0:
        return False

    # 检查是否为非列表类型
    if not isinstance(ai_options, list):
        return False

    # 检查列表中是否包含有效选项
    valid_count = 0
    for option in ai_options:
        if isinstance(option, str) and option.strip():
            valid_count += 1

    # 至少要有一个有效选项
    return valid_count > 0


def resolve_final_options(
    ai_options: List[str] = None, text: str = "", config: Dict[str, Any] = None, language: str = None
) -> List[str]:
    """
    V4.0 简化的两层回退逻辑 - 支持语言感知
    V4.0 Simplified two-layer fallback logic - Language-aware

    V4.0 简化改进：
    - 移除规则引擎层，简化为AI选项 + 用户自定义选项
    - 保持严格的边界控制
    - 提高性能和可维护性
    - 新增：支持语言感知的后备选项

    严格的边界规则：
    1. 第一层：AI选项优先，有效时完全阻断后续层级
    2. 第二层：用户自定义选项，仅在AI选项无效时使用（支持语言感知）
    3. 每一层都有严格的有效性检查，确保边界清晰

    Args:
        ai_options: AI提供的预定义选项
        text: 文本内容（保留参数以兼容现有调用）
        config: 配置字典，包含用户自定义的后备选项
        language: 语言代码 ("zh_CN" 或 "en_US")，如果为None则尝试自动检测

    Returns:
        List[str]: 最终的选项列表
    """
    # 导入配置管理器（避免循环导入）
    from .config_manager import (
        get_config,
        get_fallback_options_by_language,
        get_custom_options_enabled,
    )

    if config is None:
        config = get_config()

    # 语言检测逻辑
    if language is None:
        # 尝试从配置中检测语言（如果有UI设置）
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("InteractiveFeedback", "FeedbackUI")
            language = settings.value("ui/language", "zh_CN")
        except ImportError:
            # 如果没有PySide6，默认使用中文
            language = "zh_CN"
        except Exception:
            # 其他异常，默认使用中文
            language = "zh_CN"

    # 第一层：AI选项优先 - 严格边界检查
    if is_valid_ai_options(ai_options):
        # AI提供了有效选项，严格过滤并直接返回，完全阻断后续处理
        valid_ai_options = [
            option.strip()
            for option in ai_options
            if isinstance(option, str) and option.strip()
        ]
        if valid_ai_options:  # 双重检查确保有效性
            return valid_ai_options

    # 第二层：用户自定义后备选项 - 可控制启用/禁用，支持语言感知
    custom_options_enabled = get_custom_options_enabled(config)
    if custom_options_enabled:
        try:
            # 使用语言感知的后备选项获取函数
            fallback_options = get_fallback_options_by_language(config, language)
            if fallback_options and len(fallback_options) > 0:
                return fallback_options
        except Exception:
            # 后备选项获取失败，静默处理
            pass

    # V4.0 严格边界控制：如果用户禁用了所有层级，返回空选项
    # 这样UI就不会显示任何选项，完全由用户手动输入
    return []


def get_options_summary(options: List[str]) -> str:
    """
    获取选项的简要描述，用于调试和日志
    Get brief description of options for debugging and logging

    Args:
        options: 选项列表

    Returns:
        str: 选项的简要描述
    """
    if not options:
        return "无选项 (No options)"

    if len(options) <= 3:
        return f"选项: {', '.join(options)}"
    else:
        return f"选项: {', '.join(options[:3])}... (共{len(options)}个)"


# V4.0 移除：规则引擎性能监控函数已删除


# V4.0 移除：规则引擎管理函数已删除


# V4.0 移除：规则引擎基准测试函数已删除


# V4.0 移除：规则引擎测试函数已删除
# 简化后的规则引擎只保留核心的2级逻辑：AI选项 → 用户自定义选项
