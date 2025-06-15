# interactive_feedback_server/utils/option_strategies/fallback_options_strategy.py

"""
后备选项策略 - V3.3 架构改进版本
Fallback Options Strategy - V3.3 Architecture Improvement Version

提供用户配置的后备选项，作为第三层回退逻辑。
Provides user-configured fallback options as the third layer of fallback logic.
"""

from typing import List, Optional
from ..option_strategy import BaseOptionStrategy, OptionContext, OptionResult


class FallbackOptionsStrategy(BaseOptionStrategy):
    """
    后备选项策略
    Fallback Options Strategy

    使用用户配置的后备选项作为最后的选择
    Uses user-configured fallback options as the last resort
    """

    def __init__(self):
        """初始化后备选项策略"""
        super().__init__(
            name="fallback_options",
            priority=3,  # 最低优先级
            min_text_length=0,  # 后备选项不依赖文本内容
            max_options=5,  # 后备选项可能较多
        )

        # 默认后备选项
        self._default_fallback_options = {
            "zh_CN": ["是的", "不是", "需要更多信息"],
            "en_US": ["Yes", "No", "Need more info"],
        }

    def is_applicable(self, context: OptionContext) -> bool:
        """
        检查后备选项策略是否适用
        Check if fallback options strategy is applicable

        Args:
            context: 选项解析上下文

        Returns:
            bool: 是否适用
        """
        # 检查配置是否启用自定义选项
        if context.config:
            custom_options_enabled = self._get_custom_options_enabled(context.config)
            if not custom_options_enabled:
                return False

        # 后备选项作为最后的保障，在启用时总是适用
        return True

    def parse_options(self, context: OptionContext) -> Optional[OptionResult]:
        """
        解析后备选项
        Parse fallback options

        Args:
            context: 选项解析上下文

        Returns:
            Optional[OptionResult]: 解析结果
        """
        # 尝试从配置获取后备选项
        fallback_options = self._get_fallback_options_from_config(context)

        # 如果配置中没有，使用默认选项
        if not fallback_options:
            fallback_options = self._get_default_fallback_options(context.language)

        if not fallback_options:
            return None

        # 计算置信度
        confidence = self._calculate_confidence(fallback_options, context)

        return self.create_result(
            options=fallback_options,
            confidence=confidence,
            should_stop=True,  # 后备选项是最后一层，必须停止
            source="fallback",
            language=context.language,
            from_config=context.config is not None,
            is_default=not bool(
                context.config and self._has_custom_fallback_options(context.config)
            ),
        )

    def _get_fallback_options_from_config(self, context: OptionContext) -> List[str]:
        """
        从配置中获取后备选项
        Get fallback options from configuration

        Args:
            context: 选项解析上下文

        Returns:
            List[str]: 后备选项列表
        """
        if not context.config:
            return []

        # 使用语言感知的后备选项获取函数
        # Use language-aware fallback options function
        try:
            from ..config_manager import get_fallback_options_by_language
            
            # 使用语言感知的函数获取后备选项
            valid_options = get_fallback_options_by_language(context.config, context.language)
            if valid_options:
                return valid_options
        except ImportError:
            # 回退到原有逻辑（兼容性保证）
            # Fallback to original logic (compatibility guarantee)
            if "fallback_options" in context.config:
                options = context.config["fallback_options"]
                if isinstance(options, list):
                    # 使用公共过滤函数
                    from ..config_manager import filter_valid_options

                    valid_options = filter_valid_options(options)
                    if valid_options:
                        return valid_options

        return []

    def _get_custom_options_enabled(self, config: dict) -> bool:
        """
        检查配置中是否启用自定义选项
        Check if custom options are enabled in configuration

        Args:
            config: 配置字典

        Returns:
            bool: 是否启用自定义选项
        """
        # 使用统一的配置检查工具
        try:
            from ..config_manager import get_feature_enabled

            return get_feature_enabled(config, "enable_custom_options", False)
        except ImportError:
            # 回退到本地实现
            if "enable_custom_options" in config:
                value = config["enable_custom_options"]
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ["true", "1", "yes", "on", "enabled"]
                elif isinstance(value, int):
                    return value != 0
            return False

    def _has_custom_fallback_options(self, config: dict) -> bool:
        """
        检查配置中是否有自定义后备选项
        Check if configuration has custom fallback options

        Args:
            config: 配置字典

        Returns:
            bool: 是否有自定义选项
        """
        fallback_keys = [
            "fallback_options",
            "default_options",
            "backup_options",
            "last_resort_options",
        ]

        for key in fallback_keys:
            if key in config and isinstance(config[key], list) and config[key]:
                return True

        return False

    def _get_default_fallback_options(self, language: str) -> List[str]:
        """
        获取默认后备选项
        Get default fallback options

        Args:
            language: 语言代码

        Returns:
            List[str]: 默认后备选项
        """
        if language in self._default_fallback_options:
            return self._default_fallback_options[language].copy()

        # 如果不支持该语言，回退到中文
        return self._default_fallback_options["zh_CN"].copy()

    def _calculate_confidence(
        self, options: List[str], context: OptionContext
    ) -> float:
        """
        计算后备选项的置信度
        Calculate confidence of fallback options

        Args:
            options: 选项列表
            context: 选项解析上下文

        Returns:
            float: 置信度 (0.0-1.0)
        """
        if not options:
            return 0.0

        # 后备选项的基础置信度较低
        base_confidence = 0.5

        # 如果是用户自定义的后备选项，置信度稍高
        if context.config and self._has_custom_fallback_options(context.config):
            base_confidence = 0.6

        # 根据选项数量调整
        if len(options) == 1:
            confidence = base_confidence * 0.8
        elif len(options) <= 3:
            confidence = base_confidence
        else:
            confidence = base_confidence * 0.9

        # 根据选项质量调整
        quality_score = self._assess_option_quality(options)
        confidence *= quality_score

        return min(1.0, max(0.1, confidence))  # 最低保证0.1的置信度

    def _assess_option_quality(self, options: List[str]) -> float:
        """
        评估后备选项质量
        Assess fallback option quality

        Args:
            options: 选项列表

        Returns:
            float: 质量分数 (0.0-1.0)
        """
        if not options:
            return 0.0

        quality_factors = []

        for option in options:
            # 长度合理性
            length_score = 1.0
            if len(option) < 1:
                length_score = 0.1
            elif len(option) > 30:
                length_score = 0.8

            # 内容有效性
            content_score = 1.0
            if not option.strip():
                content_score = 0.1
            elif option.strip() in ["", " ", "　"]:  # 空白字符
                content_score = 0.1

            # 常见有效回复检测
            common_valid = [
                "是",
                "否",
                "是的",
                "不是",
                "好的",
                "取消",
                "确定",
                "需要更多信息",
                "yes",
                "no",
                "ok",
                "cancel",
                "confirm",
                "need more info",
            ]
            if option.lower().strip() in [p.lower() for p in common_valid]:
                content_score = 1.2  # 常见有效回复加分

            option_quality = length_score * content_score
            quality_factors.append(min(1.0, option_quality))

        return sum(quality_factors) / len(quality_factors)

    def add_default_language(self, language: str, options: List[str]) -> None:
        """
        添加新语言的默认后备选项
        Add default fallback options for new language

        Args:
            language: 语言代码
            options: 选项列表
        """
        if options and all(isinstance(opt, str) and opt.strip() for opt in options):
            self._default_fallback_options[language] = [opt.strip() for opt in options]

    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言列表
        Get supported language list

        Returns:
            List[str]: 语言代码列表
        """
        return list(self._default_fallback_options.keys())

    def get_default_options_for_language(self, language: str) -> List[str]:
        """
        获取指定语言的默认选项
        Get default options for specified language

        Args:
            language: 语言代码

        Returns:
            List[str]: 默认选项列表
        """
        return self._get_default_fallback_options(language)

    def get_strategy_info(self) -> dict:
        """
        获取策略详细信息
        Get detailed strategy information

        Returns:
            dict: 策略信息
        """
        return {
            "name": self.name,
            "description": "后备选项策略 - 提供用户配置的后备选项",
            "priority": self.priority,
            "layer": 3,
            "features": [
                "总是可用",
                "支持用户自定义",
                "多语言默认选项",
                "质量评估",
                "最低置信度保证",
            ],
            "applicable_when": ["总是适用（最后保障）"],
            "supported_languages": self.get_supported_languages(),
            "default_options": self._default_fallback_options,
        }
