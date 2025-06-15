# src/interactive_feedback_server/utils/config_manager.py
"""
配置管理器 - V3.2 性能优化版本
Configuration Manager - V3.2 Performance Optimized Version

V3.2 新增：支持显示模式配置和功能开关
V3.2 New: Support for display mode configuration and feature toggles

V3.2 性能优化：集成配置缓存机制，显著提升配置获取速度
V3.2 Performance Optimization: Integrated configuration caching for significant speed improvement
"""

import os
import sys
import json
from typing import Dict, Any, List
from datetime import datetime


# 配置文件路径 - 简化路径选择
def _get_config_file_path() -> str:
    """
    简化的配置文件路径选择，支持开发模式和生产模式
    Simplified config file path selection for development and production modes

    优先级：
    1. 项目根目录 config.json（开发模式优先）
    2. 用户主目录 ~/.interactive-feedback/config.json（uvx安装）
    """
    # 1. 项目根目录（开发模式优先）
    try:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        project_config_path = os.path.join(project_root, "config.json")

        # 如果项目目录可写，使用项目配置
        if os.access(project_root, os.W_OK):
            return project_config_path
    except Exception:
        pass

    # 2. 用户主目录（uvx安装回退）
    try:
        user_config_dir = os.path.expanduser("~/.interactive-feedback")
        os.makedirs(user_config_dir, exist_ok=True)
        return os.path.join(user_config_dir, "config.json")
    except Exception:
        # 最后的回退选项
        return os.path.expanduser("~/.interactive-feedback/config.json")


CONFIG_FILE_PATH = _get_config_file_path()

# 出厂默认配置 - V4.1 增强版本
DEFAULT_CONFIG = {
    "display_mode": "simple",
    "enable_custom_options": False,  # V4.0 保留：启用自定义选项（默认禁用，用户主动启用）
    "fallback_options": [
        "好的，我明白了",
        "请继续",
        "需要更多信息",
        "返回上一步",
        "暂停，让我思考一下",
    ],
    # 英文默认选项
    "fallback_options_en": [
        "Okay, I understand",
        "Please continue",
        "Need more information",
        "Go back to previous step",
        "Pause, let me think",
    ],
    "expression_optimizer": {
        "enabled": False,  # 默认禁用，用户配置 API key 后自动启用
        "active_provider": "openai",
        "prompts": {
            "optimize": "你是一个专业的文本优化助手。请将用户的输入文本改写为结构化、逻辑清晰的指令。只需要输出优化后的文本，不要包含任何技术参数、函数定义或元数据信息。",
            "reinforce": "你是一个指令执行助手。请严格按照用户提供的'强化指令'，对用户提供的'原始文本'进行处理和改写。只输出改写结果，不要包含任何技术信息。",
            "optimize_en": "You are a professional text optimization assistant. Please rewrite the user's input text into structured, logically clear instructions. Only output the optimized text without any technical parameters, function definitions or metadata.",
            "reinforce_en": "You are an instruction execution assistant. Please strictly process and rewrite the 'original text' according to the 'reinforcement instruction' provided by the user. Only output the rewritten result without any technical information.",
        },
        "performance": {
            "timeout_seconds": 30,
            "max_retries": 3,
            "retry_delay_seconds": 1,
            "rate_limit_requests_per_minute": 60,
        },
        "providers": {},  # 空的提供商配置，用户配置后填充
    },
    "version": "3.2",
    "created_at": datetime.now().isoformat() + "Z",
    "updated_at": datetime.now().isoformat() + "Z",
}


# 环境变量 API key 配置功能已移除
# 现在用户只能通过 UI 设置页面管理 API key，避免配置冲突


# _merge_env_config 函数已移除，不再支持环境变量配置合并


def validate_config(config: Dict[str, Any]) -> bool:
    """
    验证配置文件的有效性
    Validate configuration file validity

    Args:
        config: 配置字典

    Returns:
        bool: 配置是否有效
    """
    try:
        # 检查必需字段
        if "display_mode" not in config:
            return False
        if "fallback_options" not in config:
            return False

        # V4.0 简化：检查自定义选项控制字段（可选，有默认值）
        if "enable_custom_options" in config:
            if not isinstance(config["enable_custom_options"], bool):
                return False

        # 验证display_mode值
        if config["display_mode"] not in ["simple", "full"]:
            return False

        # 验证fallback_options
        fallback_options = config["fallback_options"]
        if not isinstance(fallback_options, list):
            return False
        if len(fallback_options) != 5:
            return False

        # 验证每个选项（允许占位符存在）
        for option in fallback_options:
            if not isinstance(option, str):
                return False
            if len(option) > 50:  # 字符长度限制
                return False
            # 允许占位符和空字符串存在，由过滤函数处理

        return True

    except Exception as e:
        print(f"配置验证异常 (Config validation error): {e}", file=sys.stderr)
        return False


def get_config() -> Dict[str, Any]:
    """
    安全地读取并解析配置文件，与出厂默认值合并
    Safely read and parse config file, merge with factory defaults

    配置优先级：配置文件 > 默认配置

    Returns:
        Dict[str, Any]: 合并后的配置字典
    """
    return _load_config_with_fallback()


def _load_config_with_fallback() -> Dict[str, Any]:
    """
    简化的配置加载逻辑
    Simplified config loading logic

    配置优先级：配置文件 > 默认配置

    Returns:
        Dict[str, Any]: 配置字典
    """
    # 从默认配置开始
    config = DEFAULT_CONFIG.copy()

    try:
        # 1. 检查配置文件是否存在
        if not os.path.exists(CONFIG_FILE_PATH):
            print(
                f"配置文件不存在，使用默认配置 (Config file not found, using defaults): {CONFIG_FILE_PATH}",
                file=sys.stderr,
            )
            return config

        # 2. 读取配置文件
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print(
                    "配置文件为空，使用默认配置 (Config file empty, using defaults)",
                    file=sys.stderr,
                )
                return config

            user_config = json.loads(content)

        # 3. 验证用户配置
        if not validate_config(user_config):
            print(
                "配置文件无效，使用默认配置 (Invalid config file, using defaults)",
                file=sys.stderr,
            )
            return config

        # 4. 合并配置：默认配置 <- 文件配置
        config.update(user_config)

        # 5. 更新时间戳
        config["updated_at"] = datetime.now().isoformat() + "Z"

        return config

    except json.JSONDecodeError as e:
        print(
            f"配置文件JSON解析失败，使用默认配置 (JSON parse error, using defaults): {e}",
            file=sys.stderr,
        )
        return config
    except Exception as e:
        print(
            f"读取配置文件失败，使用默认配置 (Failed to read config, using defaults): {e}",
            file=sys.stderr,
        )
        return config


def save_config(config: Dict[str, Any]) -> bool:
    """
    保存配置到文件 (V3.2 缓存优化版本)
    Save configuration to file (V3.2 Cached Version)

    V3.2 性能优化：
    - 保存后自动清除缓存，确保下次读取最新配置
    - 支持缓存失效通知

    Args:
        config: 要保存的配置字典

    Returns:
        bool: 保存是否成功
    """
    try:
        # 验证配置
        if not validate_config(config):
            print("配置无效，无法保存 (Invalid config, cannot save)", file=sys.stderr)
            return False

        # 更新时间戳
        config["updated_at"] = datetime.now().isoformat() + "Z"

        # 确保目录存在
        config_dir = os.path.dirname(CONFIG_FILE_PATH)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        # 保存配置文件
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"配置已保存 (Config saved): {CONFIG_FILE_PATH}")
        return True

    except Exception as e:
        print(f"保存配置失败 (Failed to save config): {e}", file=sys.stderr)
        return False


# 占位符常量定义
PLACEHOLDER_VALUES = ["请输入选项", "null"]


def filter_valid_options(options: List[str]) -> List[str]:
    """
    过滤有效选项，移除占位符和空值
    Filter valid options, remove placeholders and empty values

    Args:
        options: 原始选项列表

    Returns:
        List[str]: 过滤后的有效选项列表
    """
    filtered_options = []
    for option in options:
        if isinstance(option, str):
            option = option.strip()
            if option and option not in PLACEHOLDER_VALUES:
                filtered_options.append(option)
    return filtered_options


def get_fallback_options(config: Dict[str, Any] = None) -> List[str]:
    """
    获取后备选项列表（过滤空选项）
    Get fallback options list (filter empty options)

    Args:
        config: 配置字典，如果为None则自动读取

    Returns:
        List[str]: 后备选项列表（已过滤空选项）
    """
    if config is None:
        config = get_config()

    options = config.get("fallback_options", DEFAULT_CONFIG["fallback_options"])
    return filter_valid_options(options)


def get_fallback_options_by_language(config: Dict[str, Any] = None, language: str = "zh_CN") -> List[str]:
    """
    根据语言获取后备选项列表（过滤空选项）
    Get fallback options list by language (filter empty options)

    Args:
        config: 配置字典，如果为None则自动读取
        language: 语言代码 ("zh_CN" 或 "en_US")

    Returns:
        List[str]: 后备选项列表（已过滤空选项）
    """
    if config is None:
        config = get_config()

    # 只有在明确启用自定义选项时才使用用户配置的选项
    custom_options_enabled = config.get("enable_custom_options", False)
    if custom_options_enabled:
        # 根据语言选择对应的选项字段
        if language == "en_US":
            # 英文模式：优先使用 fallback_options_en，如果没有则使用默认英文选项
            options = config.get("fallback_options_en", [])
            if not options:
                # 如果没有英文选项，使用默认英文选项
                return DEFAULT_CONFIG["fallback_options_en"]
        else:
            # 中文模式：使用 fallback_options
            options = config.get("fallback_options", [])
            if not options:
                # 如果没有中文选项，使用默认中文选项
                return DEFAULT_CONFIG["fallback_options"]
        
        # 过滤有效选项
        filtered = filter_valid_options(options)
        if filtered:
            return filtered
     
    # 如果自定义选项未启用或没有有效选项，根据语言返回默认选项
    if language == "en_US":
        return DEFAULT_CONFIG["fallback_options_en"]
    else:
        return DEFAULT_CONFIG["fallback_options"]


def safe_get_fallback_options(config: Dict[str, Any] = None) -> List[str]:
    """
    安全获取后备选项列表（确保至少有一个有效选项）
    Safely get fallback options list (ensure at least one valid option)

    Args:
        config: 配置字典，如果为None则自动读取

    Returns:
        List[str]: 后备选项列表（确保非空）
    """
    options = get_fallback_options(config)

    # 如果没有有效选项，返回默认选项
    if not options:
        return DEFAULT_CONFIG["fallback_options"]

    return options


def get_display_mode(config: Dict[str, Any] = None) -> str:
    """
    获取显示模式
    Get display mode

    Args:
        config: 配置字典，如果为None则自动读取

    Returns:
        str: 显示模式 ("simple" 或 "full")
    """
    if config is None:
        config = get_config()

    return config.get("display_mode", DEFAULT_CONFIG["display_mode"])


# V4.0 移除：get_rule_engine_enabled 函数已删除


def get_custom_options_enabled(config: Dict[str, Any] = None) -> bool:
    """
    获取自定义选项启用状态
    Get custom options enabled status

    Args:
        config: 配置字典，如果为None则自动读取

    Returns:
        bool: 是否启用自定义选项
    """
    if config is None:
        config = get_config()

    return get_feature_enabled(
        config, "enable_custom_options", DEFAULT_CONFIG["enable_custom_options"]
    )


# V4.0 移除：set_rule_engine_enabled 函数已删除


def set_custom_options_enabled(enabled: bool) -> bool:
    """
    设置自定义选项启用状态
    Set custom options enabled status

    Args:
        enabled: 是否启用自定义选项

    Returns:
        bool: 设置是否成功
    """
    config = get_config()
    config["enable_custom_options"] = enabled
    return save_config(config)


def get_feature_enabled(
    config: Dict[str, Any], feature_key: str, default: bool = True
) -> bool:
    """
    统一的功能启用状态检查工具
    Unified feature enabled status check utility

    Args:
        config: 配置字典
        feature_key: 功能配置键
        default: 默认值

    Returns:
        bool: 是否启用该功能
    """
    if not config or feature_key not in config:
        return default

    value = config[feature_key]
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() in ["true", "1", "yes", "on", "enabled"]
    elif isinstance(value, int):
        return value != 0

    return default


# V4.1 简化：移除复杂的缓存管理函数，使用直接的配置加载逻辑
