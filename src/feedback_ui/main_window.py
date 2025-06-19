# feedback_ui/main_window.py
import os
import re  # 正则表达式 (Regular expressions)
import subprocess
import sys

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .dialogs.select_canned_response_dialog import SelectCannedResponseDialog
from .dialogs.settings_dialog import SettingsDialog

# --- 从子模块导入 (Imports from submodules) ---
from .utils.constants import (
    ContentItem,
    FeedbackResult,
    LAYOUT_HORIZONTAL,
    MIN_LEFT_AREA_WIDTH,
    MIN_LOWER_AREA_HEIGHT,
    MIN_RIGHT_AREA_WIDTH,
    MIN_UPPER_AREA_HEIGHT,
    SCREENSHOT_WINDOW_MINIMIZE_DELAY,
    SCREENSHOT_FOCUS_DELAY,
)
from .utils.image_processor import get_image_items_from_widgets
from .utils.settings_manager import SettingsManager
from .utils.ui_helpers import set_selection_colors

from .widgets.feedback_text_edit import FeedbackTextEdit
from .widgets.image_preview import ImagePreviewWidget
from .widgets.selectable_label import SelectableLabel
from .widgets.screenshot_window import ScreenshotWindow


class FeedbackUI(QMainWindow):
    """
    Main window for the Interactive Feedback MCP application.
    交互式反馈MCP应用程序的主窗口。
    """

    def __init__(
        self,
        prompt: str,
        predefined_options: list[str] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.output_result = FeedbackResult(
            content=[]
        )  # 初始化为空结果 (Initialize with empty result)

        # --- 内部状态 (Internal State) ---
        self.image_widgets: dict[int, ImagePreviewWidget] = {}  # image_id: widget
        self.option_checkboxes: list[QCheckBox] = (
            []
        )  # Initialize here to prevent AttributeError
        self.next_image_id = 0
        self.canned_responses: list[str] = []
        self.dropped_file_references: dict[str, str] = {}  # display_name: file_path
        self.disable_auto_minimize = False
        self.window_pinned = False

        # 按钮文本的双语映射
        self.button_texts = {
            "submit_button": {"zh_CN": "提交反馈", "en_US": "Submit Feedback"},
            "canned_responses_button": {
                "zh_CN": "常用语",
                "en_US": "Responses",
            },
            "select_file_button": {"zh_CN": "选择文件", "en_US": "Select Files"},
            "screenshot_button": {"zh_CN": "截图", "en_US": "Screenshot"},
            "open_terminal_button": {
                "zh_CN": "打开终端",
                "en_US": "Terminal",
            },
            "pin_window_button": {"zh_CN": "固定窗口", "en_US": "Pin Window"},
            "settings_button": {"zh_CN": "设置", "en_US": "Settings"},
            # V4.0 新增：优化按钮
            "optimize_button": {"zh_CN": "优化", "en_US": "Optimize"},
            "enhance_button": {"zh_CN": "增强", "en_US": "Enhance"},
        }

        # 工具提示的双语映射
        self.tooltip_texts = {
            "canned_responses_button": {
                "zh_CN": "选择或管理常用语",
                "en_US": "Select or manage canned responses",
            },
            "select_file_button": {
                "zh_CN": "打开文件选择器，选择要添加的文件或图片",
                "en_US": "Open file selector to choose files or images to add",
            },
            "screenshot_button": {
                "zh_CN": "截取屏幕区域并添加到输入框",
                "en_US": "Capture screen area and add to input box",
            },
            "open_terminal_button": {
                "zh_CN": "在当前项目路径中打开PowerShell终端",
                "en_US": "Open PowerShell terminal in current project path",
            },
            "settings_button": {
                "zh_CN": "打开设置面板",
                "en_US": "Open settings panel",
            },
            # V4.0 新增：优化按钮工具提示
            "optimize_button": {
                "zh_CN": "一键优化文本表达",
                "en_US": "One-click text optimization",
            },
            "enhance_button": {
                "zh_CN": "增强提示词效果",
                "en_US": "Enhance prompt effectiveness",
            },
        }

        # 占位符文本的双语映射
        self.placeholder_texts = {
            "input_placeholder": {
                "zh_CN": "在此输入反馈... (可拖拽文件和图片到输入框，Enter提交反馈，Shift+Enter换行，Ctrl+V复制剪切板信息)",
                "en_US": "Enter feedback here... (Drag files and images to input box, Enter to submit, Shift+Enter for new line, Ctrl+V to paste clipboard)"
            }
        }

        # 优化功能相关的双语文本
        self.optimization_texts = {
            "loading_optimize": {
                "zh_CN": "🔄 正在优化文本，请稍候...",
                "en_US": "🔄 Optimizing text, please wait..."
            },
            "loading_enhance": {
                "zh_CN": "🔄 正在增强文本，请稍候...",
                "en_US": "🔄 Enhancing text, please wait..."
            },
            "dialog_title": {
                "zh_CN": "输入表达优化",
                "en_US": "Input Expression Optimization"
            },
            "unknown_error": {
                "zh_CN": "优化过程中出现未知问题，请稍后重试",
                "en_US": "Unknown error occurred during optimization, please try again later"
            },
            "api_key_error": {
                "zh_CN": "API密钥配置有误，请在设置中检查并更新您的API密钥",
                "en_US": "API key configuration error, please check and update your API key in settings"
            },
            "rate_limit_error": {
                "zh_CN": "请求过于频繁，请稍等片刻后再试",
                "en_US": "Too many requests, please wait a moment and try again"
            },
            "timeout_error": {
                "zh_CN": "网络连接超时，请检查网络连接后重试",
                "en_US": "Network connection timeout, please check your connection and try again"
            },
            "config_error": {
                "zh_CN": "系统配置异常，请检查设置或重启应用",
                "en_US": "System configuration error, please check settings or restart the application"
            },
            "model_error": {
                "zh_CN": "所选AI模型不可用，请在设置中选择其他模型",
                "en_US": "Selected AI model is not available, please choose another model in settings"
            },
            "safety_error": {
                "zh_CN": "输入内容被安全过滤器拦截，请修改后重试",
                "en_US": "Input content was blocked by safety filter, please modify and try again"
            },
            "optimization_failed": {
                "zh_CN": "文本优化失败，请检查网络连接和API配置",
                "en_US": "Text optimization failed, please check network connection and API configuration"
            },
            "general_error": {
                "zh_CN": "优化过程中遇到问题，请稍后重试或检查设置",
                "en_US": "Encountered an issue during optimization, please try again later or check settings"
            }
        }

        self.settings_manager = SettingsManager(self)

        # 初始化音频管理器
        self._setup_audio_manager()

        self._setup_window()
        self._load_settings()

        self._create_ui_layout()
        self._connect_signals()

        self._apply_pin_state_on_load()

        # 初始化时更新界面文本显示
        self._update_displayed_texts()

        # 立即执行初始化，避免窗口显示后的布局变化
        self._perform_delayed_initialization()

        # 为主窗口安装事件过滤器，以实现点击背景聚焦输入框的功能
        self.installEventFilter(self)

        # 添加窗口大小变化监听，用于动态调整选项间距
        self._setup_resize_monitoring()

        # 配置工具提示显示延迟，减少悬浮提示的延迟
        self._configure_tooltip_timing()

        # V4.1 新增：创建加载覆盖层
        self._setup_loading_overlay()

    def _perform_delayed_initialization(self):
        """合并的延迟初始化操作，减少布局闪烁"""
        try:
            # 首先应用字体设置，避免后续样式变化
            self._apply_initial_font_settings()

            # 设置分割器样式，确保在窗口显示后应用
            self._ensure_splitter_visibility()
        except Exception as e:
            print(f"DEBUG: 延迟初始化时出错: {e}", file=sys.stderr)

    def _apply_initial_font_settings(self):
        """应用初始字体设置，避免布局闪烁"""
        try:
            app = QApplication.instance()
            if app:
                from .utils.style_manager import apply_theme

                current_theme = self.settings_manager.get_current_theme()
                apply_theme(app, current_theme)

                # 直接应用所有样式更新
                self._apply_all_style_updates()

        except Exception as e:
            print(f"DEBUG: 应用初始字体设置时出错: {e}", file=sys.stderr)

    def _apply_all_style_updates(self):
        """统一应用所有样式更新的方法"""
        current_theme = self.settings_manager.get_current_theme()

        # 重新应用分割器样式，确保颜色与主题一致
        if hasattr(self, "main_splitter"):
            self._force_splitter_style()

        # 更新输入框字体大小，与提示文字保持一致
        if hasattr(self, "text_input") and self.text_input:
            self.text_input.update_font_size()

        # 更新复选框样式，确保主题切换时颜色正确
        self._update_all_checkbox_styles()

        # 更新优化按钮样式，确保主题切换时颜色正确
        self._update_optimization_buttons_styles()

        # V4.1 新增：更新加载覆盖层主题
        if hasattr(self, "loading_overlay"):
            is_dark_theme = current_theme == "dark"
            self.loading_overlay.set_theme(is_dark_theme)

    def _setup_audio_manager(self):
        """设置音频管理器"""
        try:
            from .utils.audio_manager import get_audio_manager

            self.audio_manager = get_audio_manager()

            if self.audio_manager:
                # 从设置中加载音频配置
                enabled = self.settings_manager.get_audio_enabled()
                volume = self.settings_manager.get_audio_volume()

                self.audio_manager.set_enabled(enabled)
                self.audio_manager.set_volume(volume)

                pass  # 音频管理器初始化成功

        except Exception as e:
            print(f"设置音频管理器时出错: {e}", file=sys.stderr)
            self.audio_manager = None

    def _configure_tooltip_timing(self):
        """配置工具提示显示延迟，减少悬浮提示的延迟"""
        try:
            # 通过设置应用程序属性来优化工具提示显示
            app = QApplication.instance()
            if app:
                # 设置工具提示相关属性
                app.setAttribute(
                    Qt.ApplicationAttribute.AA_DisableWindowContextHelpButton, True
                )

                # 使用QToolTip的静态方法设置全局工具提示字体
                from PySide6.QtWidgets import QToolTip
                from PySide6.QtGui import QFont

                # 设置工具提示字体，这也会影响显示性能
                font = QFont("Segoe UI", 12)
                QToolTip.setFont(font)

                print("DEBUG: 工具提示延迟配置已应用", file=sys.stderr)
        except Exception as e:
            print(f"DEBUG: 配置工具提示延迟时出错: {e}", file=sys.stderr)

    def _setup_loading_overlay(self):
        """V4.1 新增：设置加载覆盖层"""
        from .widgets.loading_overlay import LoadingOverlay

        self.loading_overlay = LoadingOverlay(self)

        # 根据当前主题设置样式
        current_theme = self.settings_manager.get_current_theme()
        is_dark_theme = current_theme == "dark"
        self.loading_overlay.set_theme(is_dark_theme)

    def _setup_window(self):
        """Sets up basic window properties like title, size."""
        self.setWindowTitle("交互式反馈 MCP (Interactive Feedback MCP)")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)
        self.setWindowFlags(Qt.WindowType.Window)

        # 设置窗口图标
        self._setup_window_icon()

    def _setup_window_icon(self):
        """设置窗口图标"""
        # 获取图标文件路径
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(script_dir, "feedback_ui", "images", "feedback.png")

        # 尝试加载图标，如果不存在则创建一个空目录确保后续程序正确运行
        try:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # 如果图标文件不存在，确保images目录存在
                images_dir = os.path.join(script_dir, "feedback_ui", "images")
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir, exist_ok=True)
                print(f"警告: 图标文件不存在: {icon_path}")
        except Exception as e:
            print(f"警告: 无法加载图标文件: {e}")

    def _load_settings(self):
        """从设置中加载保存的窗口状态和几何形状"""

        # 设置默认大小
        default_width, default_height = 1000, 750

        # 尝试恢复保存的窗口几何信息（位置和大小）
        saved_geometry = self.settings_manager.get_main_window_geometry()
        if saved_geometry:
            # 使用Qt标准方法恢复几何信息
            if not self.restoreGeometry(saved_geometry):
                # 如果恢复失败，使用默认设置
                self._set_default_window_geometry(default_width, default_height)
        else:
            # 没有保存的几何信息，使用默认设置
            self._set_default_window_geometry(default_width, default_height)

        # 恢复窗口状态（工具栏、停靠窗口等）
        state = self.settings_manager.get_main_window_state()
        if state:
            self.restoreState(state)

        self.window_pinned = self.settings_manager.get_main_window_pinned()
        self._load_canned_responses_from_settings()

    def _set_default_window_geometry(self, width: int, height: int):
        """设置默认的窗口几何信息"""
        # 设置默认大小
        self.resize(width, height)

        # 获取屏幕大小并居中显示
        screen = QApplication.primaryScreen().geometry()
        screen_width, screen_height = screen.width(), screen.height()

        # 计算居中位置
        default_x = (screen_width - width) // 2
        default_y = (screen_height - height) // 2

        # 确保窗口在屏幕范围内
        default_x = max(0, min(default_x, screen_width - width))
        default_y = max(0, min(default_y, screen_height - height))

        self.move(default_x, default_y)

    def _create_ui_layout(self):
        """根据设置创建对应的UI布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 获取布局方向设置
        layout_direction = self.settings_manager.get_layout_direction()

        if layout_direction == LAYOUT_HORIZONTAL:
            self._create_horizontal_layout(central_widget)
        else:
            self._create_vertical_layout(central_widget)

    def _create_vertical_layout(self, central_widget: QWidget):
        """创建上下布局（当前布局）"""
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 5, 20, 10)
        main_layout.setSpacing(15)

        # 创建垂直分割器
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)

        # 上部区域和下部区域
        self.upper_area = self._create_upper_area()
        self.lower_area = self._create_lower_area()

        self.main_splitter.addWidget(self.upper_area)
        self.main_splitter.addWidget(self.lower_area)

        self._setup_vertical_splitter_properties()
        main_layout.addWidget(self.main_splitter)

        # 强制设置分割器样式
        self._force_splitter_style()

        # 底部按钮和GitHub链接
        self._setup_bottom_bar(main_layout)
        self._create_submit_button(main_layout)
        self._create_github_link_area(main_layout)

        self._update_submit_button_text_status()

    def _create_horizontal_layout(self, central_widget: QWidget):
        """创建左右布局（混合布局）"""
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 5, 20, 10)
        main_layout.setSpacing(15)

        # 创建上部分割区域
        upper_splitter_area = self._create_upper_splitter_area()
        main_layout.addWidget(upper_splitter_area, 1)  # 占据主要空间

        # 创建底部按钮区域（横跨全宽）
        self._setup_bottom_bar(main_layout)
        self._create_submit_button(main_layout)
        self._create_github_link_area(main_layout)

        self._update_submit_button_text_status()

    def _create_submit_button(self, parent_layout: QVBoxLayout):
        """创建提交按钮"""
        current_language = self.settings_manager.get_current_language()
        self.submit_button = QPushButton(
            self.button_texts["submit_button"][current_language]
        )
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setMinimumHeight(42)
        parent_layout.addWidget(self.submit_button)

    def _recreate_layout(self):
        """重新创建布局（用于布局方向切换）"""
        # 保存当前的文本内容和选项状态
        current_text = ""
        selected_options = []

        if hasattr(self, "text_input") and self.text_input:
            current_text = self.text_input.toPlainText()

        if hasattr(self, "option_checkboxes"):
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked() and i < len(self.predefined_options):
                    selected_options.append(i)

        # 重新创建UI布局
        self._create_ui_layout()

        # 恢复文本内容和选项状态
        if current_text and hasattr(self, "text_input"):
            self.text_input.setPlainText(current_text)

        if selected_options and hasattr(self, "option_checkboxes"):
            for i in selected_options:
                if i < len(self.option_checkboxes):
                    self.option_checkboxes[i].setChecked(True)

        # 重新连接信号
        self._connect_signals()

        # 应用主题和字体设置
        self.update_font_sizes()

        # 设置焦点
        self._set_initial_focus()

    def _create_upper_splitter_area(self) -> QWidget:
        """创建上部分割区域（左右布局专用）"""
        splitter_container = QWidget()
        splitter_layout = QVBoxLayout(splitter_container)
        splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 创建水平分割器
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)

        # 左侧：提示文字区域
        self.left_area = self._create_left_area()
        self.main_splitter.addWidget(self.left_area)

        # 右侧：选项+输入框区域
        self.right_area = self._create_right_area()
        self.main_splitter.addWidget(self.right_area)

        self._setup_horizontal_splitter_properties()
        splitter_layout.addWidget(self.main_splitter)

        # 强制设置分割器样式
        self._force_splitter_style()

        return splitter_container

    def _create_left_area(self) -> QWidget:
        """创建左侧区域（提示文字 + 选项）"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        # 添加提示文字区域，在左右布局中给予更多空间
        self._create_description_area(left_layout)

        # 在左右布局中，将选项区域添加到左侧
        if self.predefined_options:
            self._create_options_checkboxes(left_layout)

        return left_widget

    def _create_right_area(self) -> QWidget:
        """创建右侧区域（仅输入框）"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)

        # 在左右布局中，右侧只包含输入框区域
        # 选项区域已移动到左侧
        self._create_input_submission_area(right_layout)

        return right_widget

    def _create_upper_area(self) -> QWidget:
        """创建上部区域容器（提示文字 + 选项）"""
        upper_widget = QWidget()
        upper_layout = QVBoxLayout(upper_widget)
        upper_layout.setContentsMargins(15, 5, 15, 15)
        upper_layout.setSpacing(10)

        # 添加现有的描述区域
        self._create_description_area(upper_layout)

        # 添加选项复选框（如果有）
        if self.predefined_options:
            self._create_options_checkboxes(upper_layout)

        return upper_widget

    def _create_lower_area(self) -> QWidget:
        """创建下部区域容器（输入框）"""
        lower_widget = QWidget()
        lower_layout = QVBoxLayout(lower_widget)
        lower_layout.setContentsMargins(15, 5, 15, 15)
        lower_layout.setSpacing(10)

        # 添加输入提交区域
        self._create_input_submission_area(lower_layout)

        return lower_widget

    def _setup_vertical_splitter_properties(self):
        """配置垂直分割器属性"""
        self.main_splitter.setHandleWidth(6)
        self.upper_area.setMinimumHeight(MIN_UPPER_AREA_HEIGHT)
        self.lower_area.setMinimumHeight(MIN_LOWER_AREA_HEIGHT)

        saved_sizes = self.settings_manager.get_splitter_sizes()
        self.main_splitter.setSizes(saved_sizes)

        self.main_splitter.splitterMoved.connect(self._on_vertical_splitter_moved)
        self._setup_splitter_double_click()

    def _setup_horizontal_splitter_properties(self):
        """配置水平分割器属性"""
        self.main_splitter.setHandleWidth(6)
        self.left_area.setMinimumWidth(MIN_LEFT_AREA_WIDTH)
        self.right_area.setMinimumWidth(MIN_RIGHT_AREA_WIDTH)

        saved_sizes = self.settings_manager.get_horizontal_splitter_sizes()
        self.main_splitter.setSizes(saved_sizes)

        self.main_splitter.splitterMoved.connect(self._on_horizontal_splitter_moved)
        self._setup_splitter_double_click()

    def _force_splitter_style(self):
        """强制设置分割器样式，确保可见性"""
        # 获取当前主题的分割器颜色配置
        from .utils.theme_colors import ThemeColors

        current_theme = self.settings_manager.get_current_theme()
        colors = ThemeColors.get_splitter_colors(current_theme)

        base_color = colors["base_color"]
        hover_color = colors["hover_color"]
        pressed_color = colors["pressed_color"]

        # 精致的分割线样式：细线，与UI风格一致
        splitter_style = f"""
        QSplitter::handle:vertical {{
            background-color: {base_color} !important;
            border: none !important;
            border-radius: 2px;
            height: 6px !important;
            min-height: 6px !important;
            max-height: 6px !important;
            margin: 2px 4px;
        }}
        QSplitter::handle:vertical:hover {{
            background-color: {hover_color} !important;
        }}
        QSplitter::handle:vertical:pressed {{
            background-color: {pressed_color} !important;
        }}
        QSplitter::handle:horizontal {{
            width: 6px !important;
            min-width: 6px !important;
            max-width: 6px !important;
            background-color: {base_color} !important;
            border: none !important;
            border-radius: 2px;
            margin: 4px 2px;
        }}
        QSplitter::handle:horizontal:hover {{
            background-color: {hover_color} !important;
        }}
        QSplitter::handle:horizontal:pressed {{
            background-color: {pressed_color} !important;
        }}
        """
        self.main_splitter.setStyleSheet(splitter_style)

        # 设置精致的手柄宽度
        self.main_splitter.setHandleWidth(6)

        # 确保分割器手柄可见
        layout_direction = self.settings_manager.get_layout_direction()
        for i in range(self.main_splitter.count() - 1):
            handle = self.main_splitter.handle(i + 1)
            if handle:
                handle.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

                # 根据布局方向设置不同的尺寸属性
                if layout_direction == LAYOUT_HORIZONTAL:
                    # 水平分割器（左右布局）：设置宽度
                    handle.setMinimumWidth(6)
                    handle.setMaximumWidth(6)
                    # 设置与主题一致的背景色，保持与横向分割线相同的margin比例
                    handle.setStyleSheet(
                        f"background-color: {base_color}; border: none; border-radius: 2px; margin: 2px 0px;"
                    )
                else:
                    # 垂直分割器（上下布局）：设置高度
                    handle.setMinimumHeight(6)
                    handle.setMaximumHeight(6)
                    # 设置与主题一致的背景色
                    handle.setStyleSheet(
                        f"background-color: {base_color}; border: none; border-radius: 2px; margin: 2px 4px;"
                    )

    def _ensure_splitter_visibility(self):
        """确保分割器在窗口显示后可见"""
        if hasattr(self, "main_splitter"):
            # 重新应用样式
            self._force_splitter_style()

            # 强制刷新分割器
            self.main_splitter.update()

    def _setup_splitter_double_click(self):
        """设置分割器双击重置功能"""
        # 获取分割器手柄并设置双击事件
        handle = self.main_splitter.handle(1)
        if handle:
            handle.mouseDoubleClickEvent = self._reset_splitter_to_default

    def _reset_splitter_to_default(self, event):
        """双击分割器手柄时重置为默认比例"""
        layout_direction = self.settings_manager.get_layout_direction()

        if layout_direction == LAYOUT_HORIZONTAL:
            from .utils.constants import DEFAULT_HORIZONTAL_SPLITTER_RATIO

            self.main_splitter.setSizes(DEFAULT_HORIZONTAL_SPLITTER_RATIO)
            self._on_horizontal_splitter_moved(0, 0)
        else:
            from .utils.constants import DEFAULT_SPLITTER_RATIO

            self.main_splitter.setSizes(DEFAULT_SPLITTER_RATIO)
            self._on_vertical_splitter_moved(0, 0)

    def _on_vertical_splitter_moved(self, pos: int, index: int):
        """垂直分割器移动时保存状态"""
        sizes = self.main_splitter.sizes()
        self.settings_manager.set_splitter_sizes(sizes)
        self.settings_manager.set_splitter_state(self.main_splitter.saveState())

        # 延迟更新选项间距，因为分割器移动可能影响可用空间
        QTimer.singleShot(100, self._update_option_spacing)

    def _on_horizontal_splitter_moved(self, pos: int, index: int):
        """水平分割器移动时保存状态"""
        sizes = self.main_splitter.sizes()
        self.settings_manager.set_horizontal_splitter_sizes(sizes)
        self.settings_manager.set_horizontal_splitter_state(
            self.main_splitter.saveState()
        )

        # 延迟更新选项间距，因为分割器移动可能影响可用空间
        QTimer.singleShot(100, self._update_option_spacing)

    def _create_description_area(self, parent_layout: QVBoxLayout):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 在左右布局模式下不限制高度，让其充分利用可用空间
        # 修复：在上下布局中也移除高度限制，允许描述区域随分割器拖拽正常扩展
        layout_direction = self.settings_manager.get_layout_direction()
        if layout_direction == LAYOUT_HORIZONTAL:
            # 左右布局：不限制高度，让其充分利用可用空间
            pass
        else:
            # 上下布局：移除高度限制，允许描述区域正常扩展
            # 注释掉原有的高度限制：scroll_area.setMaximumHeight(200)
            pass

        desc_widget_container = QWidget()
        desc_layout = QVBoxLayout(desc_widget_container)
        desc_layout.setContentsMargins(15, 5, 15, 15)

        self.description_label = SelectableLabel(self.prompt, self)
        self.description_label.setProperty("class", "prompt-label")
        self.description_label.setWordWrap(True)
        # 在左右布局模式下，确保文字从顶部开始对齐
        if layout_direction == LAYOUT_HORIZONTAL:
            self.description_label.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )
        desc_layout.addWidget(self.description_label)

        self.status_label = SelectableLabel("", self)
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setVisible(False)
        desc_layout.addWidget(self.status_label)

        # 在左右布局模式下，添加弹性空间确保内容顶部对齐
        if layout_direction == LAYOUT_HORIZONTAL:
            desc_layout.addStretch()

        scroll_area.setWidget(desc_widget_container)
        parent_layout.addWidget(scroll_area)

        # 保存引用以便后续操作（例如确保滚动位置在顶部）
        self.description_scroll_area = scroll_area

        # 修复初次加载时可能显示在内容中部的问题：窗口显示后立即滚动到顶部
        QTimer.singleShot(0, lambda: self.description_scroll_area.verticalScrollBar().setValue(0))

    def _create_options_checkboxes(self, parent_layout: QVBoxLayout):
        self.option_checkboxes: list[QCheckBox] = []
        self.options_frame = QFrame()

        # 动态调整：设置选项框架的大小策略为可扩展，允许动态调整高度
        self.options_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.options_layout = QVBoxLayout(self.options_frame)
        # 使用负边距补偿复选框宽度(~20px)和间距(5px)，实现与提示文字的精确对齐
        self.options_layout.setContentsMargins(-10, 0, 0, 0)

        # 动态间距：初始设置为默认间距，后续会根据可用空间动态调整
        from .utils.constants import DEFAULT_OPTION_SPACING

        self.current_option_spacing = DEFAULT_OPTION_SPACING
        self.options_layout.setSpacing(self.current_option_spacing)

        for i, option_text in enumerate(self.predefined_options):
            # 创建一个水平容器用于放置复选框和可选择的标签
            option_container = QWidget()
            option_container_layout = QHBoxLayout(option_container)
            option_container_layout.setContentsMargins(0, 0, 0, 0)
            option_container_layout.setSpacing(5)

            # 创建无文本的复选框
            checkbox = QCheckBox("", self)
            checkbox.setObjectName(f"optionCheckbox_{i}")

            # 应用主题样式，确保覆盖系统默认蓝色
            self._apply_checkbox_theme_style(checkbox)

            # 创建可选择文本的标签
            label = SelectableLabel(option_text, self)
            label.setProperty("class", "option-label")
            label.setWordWrap(True)

            # 连接标签的点击信号到复选框的切换方法
            label.clicked.connect(checkbox.toggle)

            # 将复选框和标签添加到水平容器
            option_container_layout.addWidget(checkbox)
            option_container_layout.addWidget(label, 1)  # 标签使用剩余的空间

            # 将复选框添加到列表，保持与原有逻辑兼容
            self.option_checkboxes.append(checkbox)

            # 将整个容器添加到选项布局
            self.options_layout.addWidget(option_container)

        parent_layout.addWidget(self.options_frame)

        # 延迟初始化动态间距计算，确保所有选项都已创建
        QTimer.singleShot(200, self._setup_dynamic_option_spacing)

    def _apply_checkbox_theme_style(self, checkbox: QCheckBox):
        """为复选框应用主题相关的样式，确保覆盖系统默认蓝色"""
        from .utils.theme_colors import ThemeColors

        current_theme = self.settings_manager.get_current_theme()
        colors = ThemeColors.get_checkbox_colors(current_theme)

        # 直接设置强制样式，确保覆盖系统默认蓝色
        checkbox_style = f"""
        QCheckBox {{
            color: {colors['text_color']};
            spacing: 8px;
            min-height: 28px;
            padding: 1px;
        }}
        QCheckBox::indicator {{
            width: 22px; height: 22px;
            border: 1px solid {colors['border_color']};
            border-radius: 4px;
            background-color: {colors['bg_color']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {colors['checked_bg']} !important;
            border: 2px solid {colors['checked_border']} !important;
            image: none;
            background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24'><path fill='%23ffffff' d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z'/></svg>");
            background-position: center;
            background-repeat: no-repeat;
        }}
        QCheckBox::indicator:hover:!checked {{
            border: 1px solid {colors['hover_border']};
            background-color: {colors['hover_bg']};
        }}
        QCheckBox::indicator:checked:hover {{
            background-color: {colors['hover_border']} !important;
            border-color: {colors['hover_border']} !important;
        }}
        """

        checkbox.setStyleSheet(checkbox_style)

    def _update_all_checkbox_styles(self):
        """更新所有复选框的样式（主题切换时调用）"""
        if hasattr(self, "option_checkboxes"):
            for checkbox in self.option_checkboxes:
                self._apply_checkbox_theme_style(checkbox)

    def _update_optimization_buttons_styles(self):
        """更新优化按钮的样式（主题切换时调用）"""
        if hasattr(self, "optimize_button"):
            self._apply_optimization_button_style(self.optimize_button)
        if hasattr(self, "enhance_button"):
            self._apply_optimization_button_style(self.enhance_button)

    def _setup_dynamic_option_spacing(self):
        """设置动态选项间距功能"""
        # 立即执行，因为已经延迟调用了这个方法
        self._update_option_spacing()

    def _calculate_dynamic_option_spacing(self) -> int:
        """计算动态选项间距"""
        from .utils.constants import (
            DEFAULT_OPTION_SPACING,
            MAX_OPTION_SPACING,
            MIN_OPTION_SPACING,
        )

        try:
            # 获取当前布局方向
            layout_direction = self.settings_manager.get_layout_direction()

            # 获取容器和内容信息
            container_height = 0
            content_height = 0

            if layout_direction == "horizontal":
                # 水平布局：检查左侧区域的可用空间
                if hasattr(self, "left_area") and hasattr(self, "description_label"):
                    container_height = self.left_area.height()
                    content_height = self._get_description_content_height()
                else:
                    return DEFAULT_OPTION_SPACING
            else:
                # 垂直布局：检查上部区域的可用空间
                if hasattr(self, "upper_area") and hasattr(self, "description_label"):
                    container_height = self.upper_area.height()
                    content_height = self._get_description_content_height()
                else:
                    return DEFAULT_OPTION_SPACING

            # 计算选项区域的基础高度需求
            option_count = (
                len(self.predefined_options) if self.predefined_options else 0
            )
            if option_count == 0:
                return DEFAULT_OPTION_SPACING

            # 估算每个选项的基础高度（复选框 + 文本）
            base_option_height = 30  # 调整为更准确的选项高度
            base_options_height = option_count * base_option_height

            # 计算选项间距的总高度（选项数量-1个间距）
            total_spacing_height = max(0, option_count - 1) * DEFAULT_OPTION_SPACING

            # 计算可用的额外空间
            available_space = (
                container_height
                - content_height
                - base_options_height
                - total_spacing_height
                - 80
            )  # 增加边距缓冲

            if available_space > 50:  # 只有当可用空间足够大时才增加间距
                # 计算可以增加的间距，使用更保守的算法
                extra_spacing_per_gap = min(
                    available_space // max(1, option_count + 1), 16
                )  # 限制最大额外间距
                new_spacing = min(
                    DEFAULT_OPTION_SPACING + extra_spacing_per_gap, MAX_OPTION_SPACING
                )
                return max(new_spacing, MIN_OPTION_SPACING)
            else:
                return DEFAULT_OPTION_SPACING

        except Exception as e:
            print(f"DEBUG: 计算动态间距时出错: {e}", file=sys.stderr)
            return DEFAULT_OPTION_SPACING

    def _get_description_content_height(self) -> int:
        """获取描述文字的实际内容高度"""
        try:
            if hasattr(self, "description_label"):
                # 获取文本的实际渲染高度
                font_metrics = self.description_label.fontMetrics()
                text = self.description_label.text()

                # 计算文本在当前宽度下的高度
                available_width = self.description_label.width() - 20  # 减去边距
                if available_width > 0:
                    text_rect = font_metrics.boundingRect(
                        0, 0, available_width, 0, Qt.TextFlag.TextWordWrap, text
                    )
                    return text_rect.height() + 40  # 加上一些边距
            return 100  # 默认高度
        except Exception as e:
            print(f"DEBUG: 获取描述内容高度时出错: {e}", file=sys.stderr)
            return 100

    def _update_option_spacing(self):
        """更新选项间距"""
        try:
            if hasattr(self, "options_layout") and hasattr(self, "predefined_options"):
                new_spacing = self._calculate_dynamic_option_spacing()
                if new_spacing != self.current_option_spacing:
                    self.current_option_spacing = new_spacing
                    self.options_layout.setSpacing(new_spacing)
        except Exception as e:
            print(f"DEBUG: 更新选项间距时出错: {e}", file=sys.stderr)

    def _setup_resize_monitoring(self):
        """设置窗口大小变化监听"""
        # 创建定时器，用于延迟处理窗口大小变化
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._on_window_resized)

    def resizeEvent(self, event):
        """窗口大小变化事件"""
        super().resizeEvent(event)
        # 延迟更新选项间距，避免频繁计算
        if hasattr(self, "resize_timer"):
            self.resize_timer.start(300)  # 300ms延迟，避免与初始化定时器冲突

    def _on_window_resized(self):
        """窗口大小变化后的处理"""
        # 重新计算选项间距
        self._update_option_spacing()

    def _create_input_submission_area(self, parent_layout: QVBoxLayout):
        self.text_input = FeedbackTextEdit(self)
        # 设置包含拖拽和快捷键提示的placeholder text（语言感知）
        current_language = self.settings_manager.get_current_language()
        placeholder_text = self.placeholder_texts["input_placeholder"][current_language]
        self.text_input.setPlaceholderText(placeholder_text)

        # 连接焦点事件来动态控制placeholder显示
        self.text_input.focusInEvent = self._on_text_input_focus_in
        self.text_input.focusOutEvent = self._on_text_input_focus_out

        # QTextEdit should expand vertically, so we give it a stretch factor
        parent_layout.addWidget(self.text_input, 1)

    def _setup_bottom_bar(self, parent_layout: QVBoxLayout):
        """Creates the bottom bar with canned responses, pin, and settings buttons."""
        bottom_bar_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 5)
        bottom_layout.setSpacing(8)  # Reduced spacing between buttons

        current_language = self.settings_manager.get_current_language()

        # 使用语言相关的文本
        self.canned_responses_button = QPushButton(
            self.button_texts["canned_responses_button"][current_language]
        )
        self.canned_responses_button.setObjectName("secondary_button")
        self.canned_responses_button.setToolTip(
            self.tooltip_texts["canned_responses_button"][current_language]
        )

        # 为常用语按钮添加hover事件处理
        self.canned_responses_button.enterEvent = self._on_canned_responses_button_enter
        self.canned_responses_button.leaveEvent = self._on_canned_responses_button_leave

        # 初始化hover预览窗口变量
        self.canned_responses_preview_window = None

        bottom_layout.addWidget(self.canned_responses_button)

        # 选择文件按钮
        self.select_file_button = QPushButton(
            self.button_texts["select_file_button"][current_language]
        )
        self.select_file_button.setObjectName("secondary_button")
        self.select_file_button.setToolTip(
            self.tooltip_texts["select_file_button"][current_language]
        )
        bottom_layout.addWidget(self.select_file_button)

        # 启用终端按钮
        self.open_terminal_button = QPushButton(
            self.button_texts["open_terminal_button"][current_language]
        )
        self.open_terminal_button.setObjectName("secondary_button")
        self.open_terminal_button.setToolTip(
            self.tooltip_texts["open_terminal_button"][current_language]
        )

        # 重构终端预览功能 - 简单直接的实现
        self.terminal_preview_window = None
        self._setup_simple_terminal_preview()

        # 截图按钮（在启用终端按钮前，固定窗口按钮前）
        self.screenshot_button = QPushButton(
            self.button_texts["screenshot_button"][current_language]
        )
        self.screenshot_button.setObjectName("secondary_button")
        self.screenshot_button.setToolTip(
            self.tooltip_texts["screenshot_button"][current_language]
        )
        bottom_layout.addWidget(self.screenshot_button)

        bottom_layout.addWidget(self.open_terminal_button)

        self.pin_window_button = QPushButton(
            self.button_texts["pin_window_button"][current_language]
        )
        self.pin_window_button.setCheckable(True)
        self.pin_window_button.setObjectName("secondary_button")
        bottom_layout.addWidget(self.pin_window_button)

        # --- Settings Button (设置按钮) ---
        self.settings_button = QPushButton(
            self.button_texts["settings_button"][current_language]
        )
        self.settings_button.setObjectName("secondary_button")
        self.settings_button.setToolTip(
            self.tooltip_texts["settings_button"][current_language]
        )
        bottom_layout.addWidget(self.settings_button)

        # V4.0 新增：优化按钮
        self._create_optimization_buttons(bottom_layout, current_language)

        bottom_layout.addStretch()  # Pushes buttons to the left

        parent_layout.addWidget(bottom_bar_widget)

    def _create_optimization_buttons(self, layout, current_language):
        """V4.0 新增：创建优化按钮"""
        # 优化按钮
        self.optimize_button = QPushButton(
            self.button_texts["optimize_button"][current_language]
        )
        self.optimize_button.setObjectName("optimization_button")
        self.optimize_button.setToolTip(
            self.tooltip_texts["optimize_button"][current_language]
        )
        layout.addWidget(self.optimize_button)

        # 增强按钮
        self.enhance_button = QPushButton(
            self.button_texts["enhance_button"][current_language]
        )
        self.enhance_button.setObjectName("optimization_button")
        self.enhance_button.setToolTip(
            self.tooltip_texts["enhance_button"][current_language]
        )
        layout.addWidget(self.enhance_button)

        # 初始化时立即设置正确的可见性，避免后续布局变化
        self._set_initial_optimization_buttons_visibility()

    def _apply_optimization_button_style(self, button: QPushButton):
        """为优化按钮应用主题感知的样式"""
        from .utils.theme_colors import ThemeColors

        current_theme = self.settings_manager.get_current_theme()
        colors = ThemeColors.get_optimization_button_colors(current_theme)

        # 根据语言调整按钮尺寸
        current_language = self.settings_manager.get_current_language()
        if current_language == "en_US":
            # 英文需要更宽的按钮
            min_width = "50px"
            max_width = "60px"
            font_size = "10px"
        else:
            # 中文可以使用较小的按钮
            min_width = "30px"
            max_width = "30px"
            font_size = "11px"

        button_style = f"""
            QPushButton#optimization_button {{
                min-width: {min_width};
                max-width: {max_width};
                min-height: 32px;
                max-height: 32px;
                border-radius: 16px;
                background-color: {colors['bg_color']};
                color: {colors['text_color']};
                border: 2px solid {colors['border_color']};
                font-size: {font_size};
                font-weight: bold;
            }}
            QPushButton#optimization_button:hover {{
                background-color: {colors['hover_bg']};
                border-color: {colors['hover_border']};
            }}
            QPushButton#optimization_button:pressed {{
                background-color: {colors['pressed_bg']};
                border-color: {colors['pressed_border']};
            }}
        """
        button.setStyleSheet(button_style)

    def _get_optimization_enabled_status(self) -> bool:
        """获取优化功能启用状态的统一方法"""
        try:
            # 检查优化功能是否启用
            import sys
            import os

            # 添加项目根目录到路径
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from src.interactive_feedback_server.utils import get_config

            config = get_config()
            optimizer_config = config.get("expression_optimizer", {})
            return optimizer_config.get("enabled", False)

        except Exception as e:
            print(f"DEBUG: 获取优化功能状态失败: {e}", file=sys.stderr)
            return False

    def _set_initial_optimization_buttons_visibility(self):
        """初始化时设置优化按钮的可见性，避免后续布局变化"""
        enabled = self._get_optimization_enabled_status()
        self.optimize_button.setVisible(enabled)
        self.enhance_button.setVisible(enabled)

    def _create_github_link_area(self, parent_layout: QVBoxLayout):
        """Creates the GitHub link at the bottom."""
        github_container = QWidget()
        github_layout = QHBoxLayout(github_container)
        github_layout.setContentsMargins(0, 5, 0, 0)

        # 重构：使用可点击的纯文本标签而不是HTML链接
        github_label = QLabel("GitHub")
        github_label.setCursor(Qt.CursorShape.PointingHandCursor)

        # 启用文本选择功能
        github_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        # 设置灰色文字颜色，与主题协调
        github_label.setStyleSheet(
            "font-size: 10pt; color: #666666; text-decoration: underline;"
        )

        # 连接点击事件
        github_label.mousePressEvent = lambda event: self._open_github_link()

        # 设置选择文本时的高亮颜色为灰色
        set_selection_colors(github_label)

        github_layout.addStretch()
        github_layout.addWidget(github_label)
        github_layout.addStretch()
        parent_layout.addWidget(github_container)

    def _open_github_link(self):
        """打开GitHub链接"""
        import webbrowser

        webbrowser.open("https://github.com/pawaovo/interactive-feedback-mcp")

    def _connect_signals(self):
        self.text_input.textChanged.connect(self._update_submit_button_text_status)
        self.canned_responses_button.clicked.connect(self._show_canned_responses_dialog)
        self.select_file_button.clicked.connect(self._open_file_dialog)
        self.screenshot_button.clicked.connect(self._take_screenshot)
        self.open_terminal_button.clicked.connect(self._open_terminal)
        self.pin_window_button.toggled.connect(self._toggle_pin_window_action)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        # V4.0 新增：连接优化按钮事件
        self.optimize_button.clicked.connect(self._optimize_text)
        self.enhance_button.clicked.connect(self._reinforce_text)
        self.submit_button.clicked.connect(self._prepare_and_submit_feedback)

    def _setup_simple_terminal_preview(self):
        """设置简单的终端预览功能"""
        print("DEBUG: 设置简单终端预览功能", file=sys.stderr)

        # 创建自定义按钮类
        class TerminalPreviewButton(QPushButton):
            def __init__(self, text, parent_window):
                super().__init__(text)
                self.parent_window = parent_window

            def enterEvent(self, event):
                print("DEBUG: 终端按钮鼠标进入", file=sys.stderr)
                super().enterEvent(event)
                self.parent_window._show_simple_terminal_preview()

            def leaveEvent(self, event):
                print("DEBUG: 终端按钮鼠标离开", file=sys.stderr)
                super().leaveEvent(event)
                QTimer.singleShot(300, self.parent_window._hide_simple_terminal_preview)

        # 简化方案：直接替换按钮的事件方法
        original_enter = self.open_terminal_button.enterEvent
        original_leave = self.open_terminal_button.leaveEvent

        def new_enter(event):
            print("DEBUG: 终端按钮鼠标进入", file=sys.stderr)
            original_enter(event)
            self._show_simple_terminal_preview()

        def new_leave(event):
            print("DEBUG: 终端按钮鼠标离开", file=sys.stderr)
            original_leave(event)
            # 使用实例变量存储计时器，以便可以取消
            self.terminal_hide_timer = QTimer()
            self.terminal_hide_timer.setSingleShot(True)
            self.terminal_hide_timer.timeout.connect(self._hide_simple_terminal_preview)
            self.terminal_hide_timer.start(300)

        self.open_terminal_button.enterEvent = new_enter
        self.open_terminal_button.leaveEvent = new_leave

        print("DEBUG: 终端预览事件已绑定", file=sys.stderr)

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.WindowDeactivate:
            if (
                not self.window_pinned
                and self.isVisible()
                and not self.isMinimized()
                and not self.disable_auto_minimize
            ):
                QTimer.singleShot(100, self.showMinimized)
        return super().event(event)

    def closeEvent(self, event: QEvent):
        # 保存分割器状态
        if hasattr(self, "main_splitter"):
            sizes = self.main_splitter.sizes()
            self.settings_manager.set_splitter_sizes(sizes)
            self.settings_manager.set_splitter_state(self.main_splitter.saveState())

        # 保存窗口几何和状态（使用Qt标准方法）
        self.settings_manager.set_main_window_geometry(self.saveGeometry())
        self.settings_manager.set_main_window_state(self.saveState())
        self.settings_manager.set_main_window_pinned(self.window_pinned)

        # 确保在用户直接关闭窗口时也返回空结果
        # 此处不需要检查 self.output_result 是否已设置，因为在 __init__ 中已初始化为空结果
        # 如果没有显式通过 _prepare_and_submit_feedback 设置结果，则保持初始的空结果

        super().closeEvent(event)

    def _load_canned_responses_from_settings(self):
        self.canned_responses = self.settings_manager.get_canned_responses()

    def _update_submit_button_text_status(self):
        has_text = bool(self.text_input.toPlainText().strip())
        has_images = bool(self.image_widgets)

        has_options_selected = any(cb.isChecked() for cb in self.option_checkboxes)

        # 修改：按钮应始终可点击，即使没有内容，以支持提交空反馈
        # self.submit_button.setEnabled(has_text or has_images or has_options_selected)
        self.submit_button.setEnabled(True)

    def _show_canned_responses_dialog(self):
        # 立即设置自动最小化保护，确保在任何操作之前就有保护
        self.disable_auto_minimize = True

        # 禁用预览功能，防止对话框触发预览窗口
        self._preview_disabled = True
        # 隐藏任何现有的预览窗口（注意：这可能会尝试恢复disable_auto_minimize，但我们已经设置了保护）
        if self.canned_responses_preview_window:
            self.canned_responses_preview_window.close()
            self.canned_responses_preview_window = None
            # 不调用_hide_canned_responses_preview()，避免它恢复disable_auto_minimize

        dialog = SelectCannedResponseDialog(self.canned_responses, self)
        dialog.exec()

        self.disable_auto_minimize = False
        # 延迟重新启用预览功能，确保双击操作完全完成且鼠标事件处理完毕
        QTimer.singleShot(500, self._re_enable_preview)
        # After the dialog closes, settings are updated internally by the dialog.
        # We just need to reload them here.
        self._load_canned_responses_from_settings()

    def _re_enable_preview(self):
        """重新启用预览功能"""
        self._preview_disabled = False

    def _open_file_dialog(self):
        """打开文件选择对话框，允许用户选择多个文件"""
        # 禁用自动最小化，防止对话框导致窗口最小化
        self.disable_auto_minimize = True

        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "选择文件 (Select Files)",
                "",  # 默认目录
                "所有文件 (All Files) (*.*)",
            )

            if file_paths:  # 用户选择了文件
                self._process_selected_files(file_paths)

        except Exception as e:
            print(f"ERROR: 文件选择对话框出错: {e}", file=sys.stderr)
        finally:
            # 恢复自动最小化功能
            self.disable_auto_minimize = False

    def _process_selected_files(self, file_paths: list[str]):
        """处理用户选择的文件列表"""
        from .utils.constants import SUPPORTED_IMAGE_EXTENSIONS

        for file_path in file_paths:
            try:
                if not os.path.isfile(file_path):
                    continue

                file_name = os.path.basename(file_path)
                file_ext = os.path.splitext(file_path)[1].lower()

                # 判断是否为图片文件
                if file_ext in SUPPORTED_IMAGE_EXTENSIONS:
                    self._process_selected_image(file_path)
                else:
                    self._process_selected_file(file_path, file_name)

            except Exception as e:
                print(f"ERROR: 处理文件失败 {file_path}: {e}", file=sys.stderr)

    def _process_selected_image(self, file_path: str):
        """处理选择的图片文件"""
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull() and pixmap.width() > 0:
                self.add_image_preview(pixmap)
            else:
                print(f"WARNING: 无法加载图片: {file_path}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: 加载图片失败 {file_path}: {e}", file=sys.stderr)

    def _process_selected_file(self, file_path: str, file_name: str):
        """处理选择的普通文件"""
        try:
            # 复用现有的文件引用插入逻辑
            self.text_input._insert_file_reference_text(self, file_path, file_name)

            # 设置焦点到输入框
            self.text_input.setFocus()

        except Exception as e:
            print(f"ERROR: 插入文件引用失败 {file_path}: {e}", file=sys.stderr)

    def _open_terminal(self):
        """打开默认类型的嵌入式终端窗口"""
        # 获取默认终端类型
        default_terminal_type = self.settings_manager.get_default_terminal_type()
        self._open_terminal_with_type(default_terminal_type)

    def _open_terminal_with_type(self, terminal_type: str):
        """打开指定类型的嵌入式终端窗口"""
        # 禁用自动最小化，防止终端启动时窗口最小化
        self.disable_auto_minimize = True

        try:
            project_path = self._get_project_path()

            # 导入嵌入式终端窗口
            from .widgets.embedded_terminal_window import EmbeddedTerminalWindow

            # 创建并显示嵌入式终端窗口（不设置父窗口，使其独立显示）
            terminal_window = EmbeddedTerminalWindow(
                working_directory=project_path, terminal_type=terminal_type, parent=None
            )

            # 保存终端窗口引用，防止被垃圾回收
            if not hasattr(self, "_terminal_windows"):
                self._terminal_windows = []
            self._terminal_windows.append(terminal_window)

            # 连接关闭信号，清理引用
            terminal_window.destroyed.connect(
                lambda: (
                    self._terminal_windows.remove(terminal_window)
                    if hasattr(self, "_terminal_windows")
                    and terminal_window in self._terminal_windows
                    else None
                )
            )

            # 显示窗口并获取焦点
            terminal_window.show_and_focus()

        except Exception as e:
            # 如果嵌入式终端失败，回退到原始方法
            self._open_terminal_fallback()
        finally:
            # 延迟恢复自动最小化功能，给终端窗口足够时间完成启动
            QTimer.singleShot(
                1000, lambda: setattr(self, "disable_auto_minimize", False)
            )

    def _open_terminal_fallback(self):
        """回退到原始的外部终端启动方法"""
        try:
            project_path = self._get_project_path()
            print(f"DEBUG: 回退方法 - 项目路径: {project_path}", file=sys.stderr)

            # 使用TerminalManager获取终端命令
            from .utils.terminal_manager import get_terminal_manager

            terminal_manager = get_terminal_manager()
            terminal_command = terminal_manager.get_terminal_command("powershell")
            print(
                f"DEBUG: 回退方法 - 检测到的终端命令: {terminal_command}",
                file=sys.stderr,
            )

            if not terminal_command:
                print("ERROR: 回退方法 - 未找到可用的终端程序", file=sys.stderr)
                return

            # 启动终端进程
            if os.name == "nt":  # Windows
                print("DEBUG: 回退方法 - 在Windows系统上启动终端", file=sys.stderr)

                if "pwsh" in terminal_command.lower():
                    # PowerShell Core - 使用正确的参数
                    cmd_args = [
                        terminal_command,
                        "-NoExit",
                        "-Command",
                        f'Set-Location "{project_path}"',
                    ]
                    print(
                        f"DEBUG: 回退方法 - PowerShell Core 命令: {cmd_args}",
                        file=sys.stderr,
                    )
                else:
                    # Windows PowerShell - 使用正确的参数
                    cmd_args = [
                        terminal_command,
                        "-NoExit",
                        "-Command",
                        f'Set-Location "{project_path}"',
                    ]
                    print(
                        f"DEBUG: 回退方法 - Windows PowerShell 命令: {cmd_args}",
                        file=sys.stderr,
                    )

                # 启动进程 - 确保创建新的控制台窗口
                creation_flags = 0
                if os.name == "nt":
                    # Windows下创建新的控制台窗口
                    creation_flags = subprocess.CREATE_NEW_CONSOLE

                process = subprocess.Popen(
                    cmd_args,
                    cwd=project_path,
                    shell=False,
                    creationflags=creation_flags,
                )
                print(
                    f"DEBUG: 回退方法 - 进程已启动，PID: {process.pid}", file=sys.stderr
                )

            else:
                # Linux/macOS
                print("DEBUG: 回退方法 - 在Linux/macOS系统上启动终端", file=sys.stderr)
                if "gnome-terminal" in terminal_command:
                    cmd_args = [terminal_command, "--working-directory", project_path]
                elif "xterm" in terminal_command:
                    cmd_args = [
                        terminal_command,
                        "-e",
                        "bash",
                        "-c",
                        f'cd "{project_path}"; bash',
                    ]
                else:
                    cmd_args = [terminal_command]

                process = subprocess.Popen(cmd_args, cwd=project_path, shell=False)
                print(
                    f"DEBUG: 回退方法 - 进程已启动，PID: {process.pid}", file=sys.stderr
                )

            print(
                f"INFO: 回退方法 - 已在路径 {project_path} 中启动终端", file=sys.stderr
            )

        except Exception as e:
            print(f"ERROR: 回退方法启动终端失败: {e}", file=sys.stderr)
            import traceback

            print(
                f"ERROR: 回退方法详细错误信息: {traceback.format_exc()}",
                file=sys.stderr,
            )

    def _get_project_path(self) -> str:
        """获取项目路径，优先使用当前工作目录"""
        try:
            # 首先尝试获取当前工作目录
            current_path = os.getcwd()
            if os.path.exists(current_path):
                return current_path
        except Exception:
            pass

        # 如果获取失败，使用用户主目录
        try:
            return os.path.expanduser("~")
        except Exception:
            # 最后的回退选项
            return "C:\\" if os.name == "nt" else "/"

    # 移除重复的PowerShell检测代码，现在使用TerminalManager统一管理

    def open_settings_dialog(self):
        """Opens the settings dialog."""
        self.disable_auto_minimize = True
        dialog = SettingsDialog(self)
        dialog.exec()
        self.disable_auto_minimize = False

    def _apply_window_flags(self):
        """应用窗口标志 - 统一的窗口标志设置方法"""
        if self.window_pinned:
            # 固定窗口：添加置顶标志，保留所有标准窗口功能
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowSystemMenuHint
                | Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowMaximizeButtonHint
                | Qt.WindowType.WindowCloseButtonHint
                | Qt.WindowType.WindowStaysOnTopHint
            )
        else:
            # 标准窗口：使用标准窗口标志，确保所有按钮功能正常
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowSystemMenuHint
                | Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowMaximizeButtonHint
                | Qt.WindowType.WindowCloseButtonHint
            )

    def _apply_pin_state_on_load(self):
        # 从设置中加载固定窗口状态，但不改变按钮样式
        self.pin_window_button.setChecked(self.window_pinned)

        # 应用窗口标志（使用统一的方法）
        self._apply_window_flags()

        # 设置按钮样式和提示文本
        if self.window_pinned:
            self.pin_window_button.setObjectName("pin_window_active")
            self.pin_window_button.setToolTip(
                "固定窗口，防止自动最小化 (Pin window to prevent auto-minimize)"
            )
        else:
            self.pin_window_button.setObjectName("secondary_button")
            self.pin_window_button.setToolTip("")

        # 只应用样式到固定窗口按钮，避免影响其他按钮
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        self.pin_window_button.update()

    def _toggle_pin_window_action(self):
        # 获取按钮当前的勾选状态
        self.window_pinned = self.pin_window_button.isChecked()
        self.settings_manager.set_main_window_pinned(self.window_pinned)

        # 保存当前窗口几何信息
        current_geometry = self.saveGeometry()

        # 应用窗口标志（使用统一的方法）
        self._apply_window_flags()

        # 设置按钮样式和提示文本
        if self.window_pinned:
            self.pin_window_button.setObjectName("pin_window_active")
            self.pin_window_button.setToolTip(
                "固定窗口，防止自动最小化 (Pin window to prevent auto-minimize)"
            )
        else:
            self.pin_window_button.setObjectName("secondary_button")
            self.pin_window_button.setToolTip("")

        # 只应用样式变化到固定窗口按钮，避免影响其他按钮
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        self.pin_window_button.update()

        # 重新显示窗口并恢复几何信息（因为改变了窗口标志）
        self.show()
        self.restoreGeometry(current_geometry)

    def add_image_preview(self, pixmap: QPixmap) -> int | None:
        if pixmap and not pixmap.isNull():
            image_id = self.next_image_id
            self.next_image_id += 1

            image_widget = ImagePreviewWidget(
                pixmap, image_id, self.text_input.images_container
            )
            image_widget.image_deleted.connect(self._remove_image_widget)

            self.text_input.images_layout.addWidget(image_widget)
            self.image_widgets[image_id] = image_widget

            self.text_input.show_images_container(True)
            self._update_submit_button_text_status()
            return image_id
        return None

    def _remove_image_widget(self, image_id: int):
        if image_id in self.image_widgets:
            widget_to_remove = self.image_widgets.pop(image_id)
            self.text_input.images_layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

            if not self.image_widgets:
                self.text_input.show_images_container(False)
            self._update_submit_button_text_status()

    def _prepare_and_submit_feedback(self):
        final_content_list: list[ContentItem] = []
        feedback_plain_text = self.text_input.toPlainText().strip()

        # 获取选中的选项
        selected_options = []
        for i, checkbox in enumerate(self.option_checkboxes):
            if checkbox.isChecked() and i < len(self.predefined_options):
                # 使用预定义选项列表中的文本
                selected_options.append(self.predefined_options[i])

        combined_text_parts = []
        if selected_options:
            combined_text_parts.append("; ".join(selected_options))
        if feedback_plain_text:
            combined_text_parts.append(feedback_plain_text)

        final_text = "\n".join(combined_text_parts).strip()
        # 允许提交空内容，即使 final_text 为空
        if final_text:
            final_content_list.append({"type": "text", "text": final_text})

        image_items = get_image_items_from_widgets(self.image_widgets)
        final_content_list.extend(image_items)

        # 处理文件引用（恢复之前移除的代码）
        current_text_content_for_refs = self.text_input.toPlainText()
        file_references = {
            k: v
            for k, v in self.dropped_file_references.items()
            if k in current_text_content_for_refs
        }

        # 将文件引用添加到final_content_list中，确保AI收到完整路径信息
        for display_name, file_path in file_references.items():
            file_reference_item: ContentItem = {
                "type": "file_reference",
                "display_name": display_name,
                "path": file_path,
                "text": None,
                "data": None,
                "mimeType": None,
            }
            final_content_list.append(file_reference_item)

        # 不管 final_content_list 是否为空，都设置结果并关闭窗口
        self.output_result = FeedbackResult(content=final_content_list)

        # 保存窗口几何和状态信息，确保即使通过提交反馈关闭窗口时也能保存这些信息
        # 使用Qt标准方法保存完整的几何信息
        self.settings_manager.set_main_window_geometry(self.saveGeometry())
        self.settings_manager.set_main_window_state(self.saveState())

        self.close()

    def run_ui_and_get_result(self) -> FeedbackResult:
        # 延迟显示窗口，确保所有初始化完成
        QTimer.singleShot(10, self._show_window_when_ready)

        app_instance = QApplication.instance()
        if app_instance:
            app_instance.exec()

        # 直接返回 self.output_result，它在 __init__ 中已初始化为空结果
        # 如果用户有提交内容，它已在 _prepare_and_submit_feedback 中被更新
        return self.output_result

    def _show_window_when_ready(self):
        """在窗口完全准备好后显示"""
        self.show()
        self.activateWindow()

        # 延迟设置焦点，确保窗口完全显示
        QTimer.singleShot(50, self._set_initial_focus)

        # 播放提示音
        self._play_notification_sound()

    def _play_notification_sound(self):
        """播放提示音"""
        try:
            if hasattr(self, "audio_manager") and self.audio_manager:
                # 获取自定义音频文件路径
                custom_sound_path = self.settings_manager.get_notification_sound_path()

                # 播放提示音
                self.audio_manager.play_notification_sound(
                    custom_sound_path if custom_sound_path else None
                )

        except Exception as e:
            print(f"播放提示音时出错: {e}", file=sys.stderr)

    def _set_initial_focus(self):
        """Sets initial focus to the feedback text edit."""
        if hasattr(self, "text_input") and self.text_input:
            self.text_input.setFocus(Qt.FocusReason.OtherFocusReason)
            cursor = self.text_input.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.text_input.setTextCursor(cursor)
            self.text_input.ensureCursorVisible()

    # --- 截图功能 (Screenshot Functions) ---
    def _take_screenshot(self):
        """开始截图流程"""
        try:
            # 保存当前窗口状态
            self._save_window_state_for_screenshot()

            # 最小化主窗口（即使在固定状态下）
            self._minimize_for_screenshot()

            # 增加延迟时间确保窗口完全最小化，减少闪烁
            QTimer.singleShot(
                SCREENSHOT_WINDOW_MINIMIZE_DELAY, self._show_screenshot_window
            )

        except Exception as e:
            print(f"ERROR: 截图流程启动失败: {e}", file=sys.stderr)
            self._restore_window_after_screenshot()

    def _save_window_state_for_screenshot(self):
        """保存窗口状态用于截图后恢复"""
        self._screenshot_window_geometry = self.saveGeometry()
        self._screenshot_window_state = self.saveState()
        self._screenshot_was_pinned = self.window_pinned
        self._screenshot_was_visible = self.isVisible()

    def _minimize_for_screenshot(self):
        """为截图最小化窗口"""
        # 临时禁用自动最小化，避免干扰
        self.disable_auto_minimize = True

        # 最小化窗口
        self.showMinimized()

    def _show_screenshot_window(self):
        """显示截图窗口"""
        try:
            # 创建截图窗口
            self.screenshot_window = ScreenshotWindow(self)

            # 连接信号
            self.screenshot_window.screenshot_taken.connect(self._on_screenshot_taken)
            self.screenshot_window.screenshot_cancelled.connect(
                self._on_screenshot_cancelled
            )

            print("DEBUG: 截图窗口已显示", file=sys.stderr)

        except Exception as e:
            print(f"ERROR: 显示截图窗口失败: {e}", file=sys.stderr)
            self._restore_window_after_screenshot()

    def _on_screenshot_taken(self, pixmap):
        """截图完成回调"""
        try:
            # 恢复主窗口
            self._restore_window_after_screenshot()

            # 将截图添加到输入框
            if pixmap and not pixmap.isNull():
                self.add_image_preview(pixmap)

        except Exception as e:
            print(f"ERROR: 处理截图失败: {e}", file=sys.stderr)
            self._restore_window_after_screenshot()

    def _on_screenshot_cancelled(self):
        """截图取消回调"""
        self._restore_window_after_screenshot()

    def _restore_window_after_screenshot(self):
        """截图后恢复窗口状态"""
        try:
            # 重新启用自动最小化
            self.disable_auto_minimize = False

            # 恢复窗口显示
            if (
                hasattr(self, "_screenshot_was_visible")
                and self._screenshot_was_visible
            ):
                # 先显示窗口
                self.show()

                # 恢复窗口几何信息
                if hasattr(self, "_screenshot_window_geometry"):
                    self.restoreGeometry(self._screenshot_window_geometry)

                # 恢复窗口状态
                if hasattr(self, "_screenshot_window_state"):
                    self.restoreState(self._screenshot_window_state)

                # 强制激活窗口并置顶
                self.setWindowState(
                    self.windowState() & ~Qt.WindowState.WindowMinimized
                    | Qt.WindowState.WindowActive
                )
                self.activateWindow()
                self.raise_()

                # 延迟设置焦点，确保窗口完全恢复
                QTimer.singleShot(
                    SCREENSHOT_FOCUS_DELAY, self._set_focus_after_screenshot
                )

            # 清理临时变量
            self._cleanup_screenshot_variables()

        except Exception as e:
            print(f"ERROR: 恢复窗口状态失败: {e}", file=sys.stderr)
            # 确保重新启用自动最小化
            self.disable_auto_minimize = False

    def _set_focus_after_screenshot(self):
        """截图后设置焦点"""
        try:
            # 再次确保窗口激活
            self.activateWindow()
            self.raise_()

            # 设置焦点到输入框
            if hasattr(self, "text_input"):
                self.text_input.setFocus()

        except Exception as e:
            print(f"ERROR: 设置焦点失败: {e}", file=sys.stderr)

    def _cleanup_screenshot_variables(self):
        """清理截图相关的临时变量"""
        attrs_to_remove = [
            "_screenshot_window_geometry",
            "_screenshot_window_state",
            "_screenshot_was_pinned",
            "_screenshot_was_visible",
        ]

        for attr in attrs_to_remove:
            if hasattr(self, attr):
                delattr(self, attr)

        # 清理截图窗口引用
        if hasattr(self, "screenshot_window"):
            self.screenshot_window = None

    def changeEvent(self, event: QEvent):
        """处理语言变化事件，更新界面文本"""
        if event.type() == QEvent.Type.LanguageChange:
            print("FeedbackUI: 接收到语言变化事件，更新UI文本")
            # 更新所有文本
            self._update_displayed_texts()
        super().changeEvent(event)

    def _update_displayed_texts(self):
        """根据当前语言设置更新显示的文本内容"""
        current_lang = self.settings_manager.get_current_language()

        # 更新提示文字
        if self.description_label:
            self.description_label.setText(
                self._filter_text_by_language(self.prompt, current_lang)
            )

        # 更新输入框占位符文本
        if hasattr(self, "text_input") and self.text_input:
            # 只有在输入框为空时才更新占位符文本
            if not self.text_input.toPlainText().strip():
                placeholder_text = self.placeholder_texts["input_placeholder"][current_lang]
                self.text_input.setPlaceholderText(placeholder_text)

        # 更新选项复选框的关联标签
        for i, checkbox in enumerate(self.option_checkboxes):
            if i < len(self.predefined_options):
                # 找到复选框所在的容器
                option_container = checkbox.parent()
                if option_container:
                    # 找到容器中的SelectableLabel
                    for child in option_container.children():
                        if isinstance(child, SelectableLabel):
                            # 更新标签文本
                            child.setText(
                                self._filter_text_by_language(
                                    self.predefined_options[i], current_lang
                                )
                            )
                            break

        # 更新按钮文本
        self._update_button_texts(current_lang)

    def _update_button_texts(self, language_code):
        """根据当前语言更新所有按钮的文本"""
        # 更新提交按钮
        if hasattr(self, "submit_button") and self.submit_button:
            self.submit_button.setText(
                self.button_texts["submit_button"].get(language_code, "提交")
            )

        # 更新底部按钮
        if hasattr(self, "canned_responses_button") and self.canned_responses_button:
            self.canned_responses_button.setText(
                self.button_texts["canned_responses_button"].get(
                    language_code, "常用语"
                )
            )
            self.canned_responses_button.setToolTip(
                self.tooltip_texts["canned_responses_button"].get(
                    language_code, "选择或管理常用语"
                )
            )

        if hasattr(self, "select_file_button") and self.select_file_button:
            self.select_file_button.setText(
                self.button_texts["select_file_button"].get(language_code, "选择文件")
            )
            self.select_file_button.setToolTip(
                self.tooltip_texts["select_file_button"].get(
                    language_code, "打开文件选择器，选择要添加的文件或图片"
                )
            )

        if hasattr(self, "screenshot_button") and self.screenshot_button:
            self.screenshot_button.setText(
                self.button_texts["screenshot_button"].get(language_code, "窗口截图")
            )
            self.screenshot_button.setToolTip(
                self.tooltip_texts["screenshot_button"].get(
                    language_code, "截取屏幕区域并添加到输入框"
                )
            )

        if hasattr(self, "open_terminal_button") and self.open_terminal_button:
            self.open_terminal_button.setText(
                self.button_texts["open_terminal_button"].get(language_code, "启用终端")
            )
            self.open_terminal_button.setToolTip(
                self.tooltip_texts["open_terminal_button"].get(
                    language_code, "在当前项目路径中打开PowerShell终端"
                )
            )

        if hasattr(self, "pin_window_button") and self.pin_window_button:
            # 保存当前按钮的样式类名
            current_object_name = self.pin_window_button.objectName()
            self.pin_window_button.setText(
                self.button_texts["pin_window_button"].get(language_code, "固定窗口")
            )
            # 单独刷新固定窗口按钮的样式，避免影响其他按钮
            self.pin_window_button.style().unpolish(self.pin_window_button)
            self.pin_window_button.style().polish(self.pin_window_button)
            self.pin_window_button.update()

        if hasattr(self, "settings_button") and self.settings_button:
            self.settings_button.setText(
                self.button_texts["settings_button"].get(language_code, "设置")
            )
            self.settings_button.setToolTip(
                self.tooltip_texts["settings_button"].get(language_code, "打开设置面板")
            )

        # V4.0 新增：更新优化按钮文本
        if hasattr(self, "optimize_button"):
            self.optimize_button.setText(
                self.button_texts["optimize_button"][current_language]
            )
            self.optimize_button.setToolTip(
                self.tooltip_texts["optimize_button"][current_language]
            )

        if hasattr(self, "enhance_button"):
            self.enhance_button.setText(
                self.button_texts["enhance_button"][current_language]
            )
            self.enhance_button.setToolTip(
                self.tooltip_texts["enhance_button"][current_language]
            )

    def _filter_text_by_language(self, text: str, lang_code: str) -> str:
        """
        从双语文本中提取指定语言的部分
        支持的格式:
        - "中文 (English)" 或 "中文（English）"
        - "中文 - English" 或类似分隔符
        """
        if not text or not isinstance(text, str):
            return text

        # 快速检测文本是否包含中文字符
        has_chinese = bool(re.search(r"[\u4e00-\u9fff]", text))
        # 快速检测文本是否包含英文单词（至少两个连续字母，以排除单个字母变量等）
        has_english = bool(re.search(r"[A-Za-z]{2,}", text))

        # 如果当前语言是中文，但文本本身几乎不包含中文，则直接返回原文本，避免误截断
        if lang_code == "zh_CN" and not has_chinese:
            return text

        # 如果当前语言是英文，但文本本身几乎不包含中文，则直接返回原文本
        if lang_code == "en_US" and not has_chinese:
            return text

        # 如果是中文模式
        if lang_code == "zh_CN":
            # 格式1：标准括号格式 "中文 (English)" 或 "中文（English）"
            match = re.match(r"^(.*?)[\s]*[\(（].*?[\)）](\s*|$)", text)
            if match:
                return match.group(1).strip()

            # 格式2：中英文之间有破折号或其他分隔符 "中文 - English"
            match = re.match(r"^(.*?)[\s]*[-—–][\s]*[A-Za-z].*?$", text)
            if match:
                return match.group(1).strip()

            # 如果都不匹配，可能是纯中文，直接返回
            return text

        # 如果是英文模式
        elif lang_code == "en_US":
            # 格式1：标准括号格式，提取括号内的英文
            match = re.search(r"[\(（](.*?)[\)）]", text)
            if match:
                return match.group(1).strip()

            # 格式2：中英文之间有破折号或其他分隔符 "中文 - English"
            match = re.search(r"[-—–][\s]*(.*?)$", text)
            if match and re.search(r"[A-Za-z]", match.group(1)):
                return match.group(1).strip()

            # 如果上述格式都不匹配，检查是否包含英文单词
            if has_english:  # 已经确认包含英文
                return text

            # 可能是纯中文，那就返回原文本
            return text

        # 默认返回原文本
        return text

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        事件过滤器，用于实现无论点击窗口哪个区域，都自动保持文本输入框的活跃状态。
        Event filter to keep the text input active regardless of where the user clicks.
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            # 对于任何鼠标点击，都激活输入框
            # For any mouse click, activate the text input

            # 如果文本输入框当前没有焦点，则设置焦点并移动光标到末尾
            if not self.text_input.hasFocus():
                self.text_input.setFocus()
                cursor = self.text_input.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.text_input.setTextCursor(cursor)

            # 重要：不消耗事件，让它继续传递，确保被点击的控件（如按钮）能正常响应
            # Important: Don't consume the event, let it pass through to ensure clicked controls (like buttons) respond normally

        # 将事件传递给父类处理，保持所有控件的原有功能
        return super().eventFilter(obj, event)

    def _on_text_input_focus_in(self, event):
        """输入框获得焦点时的处理 - 隐藏placeholder text"""
        # 调用原始的focusInEvent
        FeedbackTextEdit.focusInEvent(self.text_input, event)

        # 如果输入框为空，临时清除placeholder text以避免显示
        if not self.text_input.toPlainText().strip():
            self.text_input.setPlaceholderText("")

    def _on_text_input_focus_out(self, event):
        """输入框失去焦点时的处理 - 恢复placeholder text"""
        # 调用原始的focusOutEvent
        FeedbackTextEdit.focusOutEvent(self.text_input, event)

        # 如果输入框为空，恢复placeholder text
        if not self.text_input.toPlainText().strip():
            current_language = self.settings_manager.get_current_language()
            placeholder_text = self.placeholder_texts["input_placeholder"][current_language]
            self.text_input.setPlaceholderText(placeholder_text)

    def _on_canned_responses_button_enter(self, event):
        """常用语按钮鼠标进入事件 - 显示常用语预览"""
        # 调用原始的enterEvent
        QPushButton.enterEvent(self.canned_responses_button, event)

        # 如果有常用语且没有禁用预览，显示预览窗口
        if self.canned_responses and not getattr(self, "_preview_disabled", False):
            self._show_canned_responses_preview()

    def _on_canned_responses_button_leave(self, event):
        """常用语按钮鼠标离开事件 - 延迟隐藏常用语预览"""
        # 调用原始的leaveEvent
        QPushButton.leaveEvent(self.canned_responses_button, event)

        # 延迟隐藏预览窗口，给用户时间移动到预览窗口
        QTimer.singleShot(200, self._delayed_hide_preview)

    def _on_preview_window_enter(self, event):
        """预览窗口鼠标进入事件 - 取消隐藏计时器"""
        # 取消延迟隐藏
        pass

    def _on_preview_window_leave(self, event):
        """预览窗口鼠标离开事件 - 隐藏预览窗口"""
        # 立即隐藏预览窗口
        self._hide_canned_responses_preview()

    def _delayed_hide_preview(self):
        """延迟隐藏预览窗口 - 检查鼠标是否在预览窗口内"""
        if (
            self.canned_responses_preview_window
            and self.canned_responses_preview_window.isVisible()
        ):
            # 获取鼠标位置
            from PySide6.QtGui import QCursor

            mouse_pos = QCursor.pos()

            # 检查鼠标是否在预览窗口内
            preview_rect = self.canned_responses_preview_window.geometry()
            if not preview_rect.contains(mouse_pos):
                # 鼠标不在预览窗口内，隐藏窗口
                self._hide_canned_responses_preview()

    def _show_canned_responses_preview(self):
        """显示常用语预览窗口"""
        if not self.canned_responses:
            return

        # 预先设置自动最小化保护，防止预览窗口交互导致窗口最小化
        self.disable_auto_minimize = True

        # 如果预览窗口已存在，先关闭
        if self.canned_responses_preview_window:
            self.canned_responses_preview_window.close()
            self.canned_responses_preview_window = None

        # 创建预览窗口
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        from PySide6.QtCore import Qt

        self.canned_responses_preview_window = QWidget()
        self.canned_responses_preview_window.setWindowFlags(
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        )
        self.canned_responses_preview_window.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating
        )

        # 为预览窗口添加hover事件处理，支持鼠标移动到预览窗口
        self.canned_responses_preview_window.enterEvent = self._on_preview_window_enter
        self.canned_responses_preview_window.leaveEvent = self._on_preview_window_leave

        # 主布局 - 直接使用VBoxLayout，不使用滚动区域
        main_layout = QVBoxLayout(self.canned_responses_preview_window)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(1)  # 减少间距，与终端预览窗口保持一致

        # 获取当前主题的颜色配置
        from .utils.theme_colors import ThemeColors

        current_theme = self.settings_manager.get_current_theme()
        colors = ThemeColors.get_preview_colors(current_theme)

        bg_color = colors["bg_color"]
        border_color = colors["border_color"]
        text_color = colors["text_color"]
        item_bg = colors["item_bg"]
        item_border = colors["item_border"]
        item_hover_bg = colors["item_hover_bg"]
        item_hover_border = colors["item_hover_border"]

        # 添加所有常用语项目
        for i, response in enumerate(self.canned_responses):
            response_label = QLabel(response)

            # 设置固定高度和文本省略模式
            response_label.setFixedHeight(40)  # 调整到40px以获得更好的文字显示效果
            response_label.setWordWrap(False)  # 禁用自动换行

            # 使用Qt原生的文本省略功能
            from PySide6.QtCore import Qt

            response_label.setTextFormat(Qt.TextFormat.PlainText)

            # 设置文本省略模式为末尾省略
            font_metrics = response_label.fontMetrics()
            available_width = 260 - 20  # 预览窗口宽度减去padding
            elided_text = font_metrics.elidedText(
                response, Qt.TextElideMode.ElideRight, available_width
            )
            response_label.setText(elided_text)

            response_label.setStyleSheet(
                f"""
                QLabel {{
                    padding: 4px 10px;
                    border-radius: 6px;
                    background-color: {item_bg};
                    color: {text_color};
                    border: 1px solid {item_border};
                    margin: 1px 0px;
                }}
                QLabel:hover {{
                    background-color: {item_hover_bg};
                    border-color: {item_hover_border};
                    color: white;
                }}
            """
            )
            response_label.setCursor(Qt.CursorShape.PointingHandCursor)

            # 为每个标签添加点击事件
            response_label.mousePressEvent = (
                lambda event, text=response: self._on_preview_item_clicked(text)
            )

            main_layout.addWidget(response_label)

        # 设置窗口样式（包含阴影效果）
        self.canned_responses_preview_window.setStyleSheet(
            f"""
            QWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """
        )

        # 计算位置（在按钮上方显示）
        button_pos = self.canned_responses_button.mapToGlobal(
            self.canned_responses_button.rect().topLeft()
        )
        preview_width = 280  # 减少宽度，使预览窗口更紧凑

        # 根据实际常用语数量动态计算高度，不限制最大数量
        # 每个项目40px高度 + 间距1px + 上下边距16px
        item_height = 40
        spacing = 1
        padding = 16

        # 计算总高度：项目高度 + 间距 + 边距
        if len(self.canned_responses) > 0:
            preview_height = (
                len(self.canned_responses) * item_height  # 所有项目的高度
                + max(0, len(self.canned_responses) - 1) * spacing  # 项目间距
                + padding  # 上下边距
            )
        else:
            preview_height = 50  # 最小高度，防止空列表时窗口过小

        # 在按钮上方显示
        x = button_pos.x()
        y = button_pos.y() - preview_height - 10

        self.canned_responses_preview_window.setGeometry(
            x, y, preview_width, preview_height
        )
        self.canned_responses_preview_window.show()

    def _hide_canned_responses_preview(self):
        """隐藏常用语预览窗口"""
        if self.canned_responses_preview_window:
            self.canned_responses_preview_window.close()
            self.canned_responses_preview_window = None

        # 恢复自动最小化功能
        self.disable_auto_minimize = False

    def _on_preview_item_clicked(self, text):
        """预览项目被点击时插入到输入框"""
        if self.text_input:
            self.text_input.insertPlainText(text)
            self.text_input.setFocus()

            # 移动光标到末尾
            cursor = self.text_input.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.text_input.setTextCursor(cursor)

        # 隐藏预览窗口（会自动恢复disable_auto_minimize）
        self._hide_canned_responses_preview()

    # --- 终端预览功能 (Terminal Preview Functions) ---
    def _on_terminal_button_enter(self, event):
        """终端按钮鼠标进入事件 - 显示终端预览"""
        # 显示终端预览窗口
        try:
            self._show_simple_terminal_preview()
        except Exception:
            pass  # 静默处理错误

    def _on_terminal_button_leave(self, event):
        """终端按钮鼠标离开事件 - 延迟隐藏终端预览"""
        # 延迟隐藏预览窗口，给用户时间移动到预览窗口
        QTimer.singleShot(200, self._delayed_hide_terminal_preview)

    def _delayed_hide_terminal_preview(self):
        """延迟隐藏终端预览窗口"""
        self._hide_terminal_preview()

    def _on_terminal_preview_window_enter(self, event):
        """终端预览窗口鼠标进入事件 - 取消隐藏计时器"""
        # 取消延迟隐藏
        pass

    def _on_terminal_preview_window_leave(self, event):
        """终端预览窗口鼠标离开事件 - 隐藏预览窗口"""
        # 立即隐藏预览窗口
        self._hide_terminal_preview()

    # --- 简单终端预览功能 (Simple Terminal Preview Functions) ---
    def _show_simple_terminal_preview(self):
        """显示简单的终端预览窗口"""
        if self.terminal_preview_window:
            self.terminal_preview_window.close()

        # 预先设置自动最小化保护，防止预览窗口交互导致窗口最小化
        self.disable_auto_minimize = True

        # 创建预览窗口 - 参考常用语预览窗口的实现
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        from PySide6.QtCore import Qt

        self.terminal_preview_window = QWidget()
        self.terminal_preview_window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.terminal_preview_window.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating
        )

        # 添加预览窗口的鼠标事件处理
        def preview_enter_event(event):
            # 取消隐藏计时器
            if hasattr(self, "terminal_hide_timer") and self.terminal_hide_timer:
                self.terminal_hide_timer.stop()
                self.terminal_hide_timer = None

        def preview_leave_event(event):
            # 立即隐藏预览窗口
            self._hide_simple_terminal_preview()

        self.terminal_preview_window.enterEvent = preview_enter_event
        self.terminal_preview_window.leaveEvent = preview_leave_event

        # 获取主题颜色配置
        from .utils.theme_colors import ThemeColors

        current_theme = self.settings_manager.get_current_theme()
        colors = ThemeColors.get_preview_colors(current_theme)

        bg_color = colors["bg_color"]
        border_color = colors["border_color"]
        text_color = colors["text_color"]
        item_bg = colors["item_bg"]
        item_border = colors["item_border"]
        item_hover_bg = colors["item_hover_bg"]
        item_hover_border = colors["item_hover_border"]

        # 创建主布局 - 完全参考常用语预览窗口
        main_layout = QVBoxLayout(self.terminal_preview_window)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建滚动区域 - 参考常用语预览窗口
        from PySide6.QtWidgets import QScrollArea

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 创建滚动内容
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(1)

        # 添加3个终端选项 - 使用与常用语完全相同的样式
        terminals = [
            {"type": "powershell", "name": "🔷 PowerShell"},
            {"type": "gitbash", "name": "🔶 Git Bash"},
            {"type": "cmd", "name": "⬛ Command Prompt"},
        ]

        for terminal in terminals:
            label = QLabel(terminal["name"])
            label.setWordWrap(True)
            label.setStyleSheet(
                f"""
                QLabel {{
                    padding: 4px 10px;
                    border-radius: 6px;
                    background-color: {item_bg};
                    color: {text_color};
                    border: 1px solid {item_border};
                    margin: 1px 0px;
                }}
                QLabel:hover {{
                    background-color: {item_hover_bg};
                    border-color: {item_hover_border};
                    color: white;
                }}
            """
            )
            label.setCursor(Qt.CursorShape.PointingHandCursor)

            # 添加点击事件
            terminal_type = terminal["type"]
            label.mousePressEvent = (
                lambda event, t=terminal_type: self._on_simple_terminal_clicked(t)
            )

            layout.addWidget(label)

        # 设置滚动内容
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # 设置滚动区域样式 - 完全参考常用语预览窗口
        scroll_area.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: {bg_color};
                border: none;
                border-radius: 10px;
            }}
            QScrollBar:vertical {{
                background-color: {bg_color};
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {item_border};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {item_hover_border};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """
        )

        # 设置窗口样式 - 完全参考常用语预览窗口
        self.terminal_preview_window.setStyleSheet(
            f"""
            QWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """
        )

        # 计算位置和大小 - 完全参考常用语预览窗口
        button_pos = self.open_terminal_button.mapToGlobal(
            self.open_terminal_button.rect().topLeft()
        )
        preview_width = 280  # 与常用语预览窗口相同宽度

        # 计算高度：3个终端选项的高度
        preview_height = 3 * 40 + 20  # 每个项目约40px高度，加上边距

        # 在按钮上方显示
        x = button_pos.x()
        y = button_pos.y() - preview_height - 10

        self.terminal_preview_window.setGeometry(x, y, preview_width, preview_height)

        # 显示窗口
        self.terminal_preview_window.show()

    def _on_simple_terminal_clicked(self, terminal_type: str):
        """简单终端预览项目被点击"""
        # 隐藏预览窗口
        self._hide_simple_terminal_preview()

        # 注意：不需要在这里设置disable_auto_minimize，
        # 因为_open_terminal_with_type()方法已经有了保护机制
        self._open_terminal_with_type(terminal_type)

    def _hide_simple_terminal_preview(self):
        """隐藏简单终端预览窗口"""
        if self.terminal_preview_window:
            self.terminal_preview_window.close()
            self.terminal_preview_window = None

        # 恢复自动最小化功能
        self.disable_auto_minimize = False

    def _hide_terminal_preview(self):
        """隐藏终端预览窗口（兼容性方法）"""
        self._hide_simple_terminal_preview()

    def update_font_sizes(self):
        """
        通过重新应用当前主题来更新UI中的字体大小。
        style_manager会处理动态字体大小的注入。
        """
        app = QApplication.instance()
        if app:
            from .utils.style_manager import apply_theme

            current_theme = self.settings_manager.get_current_theme()
            apply_theme(app, current_theme)

            # 使用单个定时器统一处理所有样式更新，避免布局闪烁
            QTimer.singleShot(50, self._update_all_styles_after_theme_change)

    def _update_all_styles_after_theme_change(self):
        """主题切换后统一更新所有样式，避免多个定时器导致的布局闪烁"""
        try:
            self._apply_all_style_updates()
        except Exception as e:
            print(f"DEBUG: 主题切换后样式更新时出错: {e}", file=sys.stderr)

    # V4.0 新增：输入表达优化功能
    def _optimize_text(self):
        """一键优化当前输入文本"""
        current_text = self.text_input.toPlainText().strip()
        if not current_text:
            self._show_optimization_message("请先输入要优化的文本")
            return

        self._perform_optimization(current_text, "optimize")

    def _reinforce_text(self):
        """提示词强化当前输入文本"""
        current_text = self.text_input.toPlainText().strip()
        if not current_text:
            self._show_optimization_message("请先输入要强化的文本")
            return

        # 弹出对话框获取强化指令
        from PySide6.QtWidgets import QInputDialog

        self.disable_auto_minimize = True
        try:
            reinforcement_prompt, ok = QInputDialog.getText(
                self,
                "提示词强化",
                "请输入强化指令（例如：用更专业的语气重写）:",
                text="",
            )

            if ok and reinforcement_prompt.strip():
                self._perform_optimization(
                    current_text, "reinforce", reinforcement_prompt.strip()
                )
            elif ok:
                self._show_optimization_message("强化指令不能为空")

        finally:
            self.disable_auto_minimize = False

    def _perform_optimization(
        self, text: str, mode: str, reinforcement_prompt: str = None
    ):
        """执行优化操作 - V4.1 异步加载效果"""
        # V4.1 新增：立即显示加载覆盖层
        loading_message = (
            "🔄 正在优化文本，请稍候..."
            if mode == "optimize"
            else "🔄 正在增强文本，请稍候..."
        )
        self.loading_overlay.show_loading(loading_message)

        # 显示加载状态
        self._set_optimization_loading_state(True)

        # V4.1 修复：使用QTimer异步执行优化，避免阻塞UI
        QTimer.singleShot(
            50,
            lambda: self._execute_optimization_async(text, mode, reinforcement_prompt),
        )

    def _execute_optimization_async(
        self, text: str, mode: str, reinforcement_prompt: str = None
    ):
        """异步执行优化操作 - V4.1 新增"""
        try:
            # 调用后端MCP工具
            import sys
            import os

            # 添加项目根目录到路径
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from src.interactive_feedback_server.cli import optimize_user_input

            if mode == "reinforce" and reinforcement_prompt:
                result = optimize_user_input(text, mode, reinforcement_prompt)
            else:
                result = optimize_user_input(text, mode)

            # V4.1 智能切换：根据结果类型选择不同的反馈方式
            if self._is_optimization_error(result):
                # 错误时：隐藏loading，显示详细的错误对话框
                self.loading_overlay.hide_loading()
                self._show_optimization_message(result)
            else:
                # 成功时：只更新文本，不显示弹窗（用户能直接看到变化）
                clean_result = result
                is_cached = False

                if result.startswith("[CACHED] "):
                    clean_result = result[9:]  # 移除 "[CACHED] " 前缀
                    is_cached = True

                # 验证优化结果的质量
                if self._validate_optimization_result(clean_result, text):
                    # 成功：使用支持撤销的文本替换方法
                    self.text_input.replace_text_with_undo_support(clean_result)
                    # V4.1 新增：激活输入框焦点，让用户可以直接输入
                    QTimer.singleShot(100, self.text_input.activate_input_focus)
                    # V4.1 智能反馈：显示简短的成功状态，然后自动消失
                    success_msg = "✅ 优化完成！" + (" (缓存)" if is_cached else "")
                    self.loading_overlay.show_success(success_msg, 500)
                    return  # 提前返回，避免执行finally中的hide_loading
                else:
                    # 质量警告：仍然应用文本，使用支持撤销的方法
                    self.text_input.replace_text_with_undo_support(clean_result)
                    # V4.1 新增：激活输入框焦点
                    QTimer.singleShot(100, self.text_input.activate_input_focus)
                    self.loading_overlay.hide_loading()
                    self._show_optimization_message(
                        "⚠️ 优化完成，但结果可能需要手动调整", success=True
                    )

        except Exception as e:
            error_msg = f"优化过程中发生错误: {str(e)}"
            self._show_optimization_message(error_msg)
            # 异常时隐藏loading overlay
            self.loading_overlay.hide_loading()
        finally:
            # V4.1 修改：只重置按钮状态，loading overlay由具体逻辑控制
            self._set_optimization_loading_state(False)

    def _is_optimization_error(self, result: str) -> bool:
        """
        检测优化结果是否为错误 - V4.1 新增
        Detect if optimization result is an error - V4.1 New
        """
        if not result or not isinstance(result, str):
            return True

        # 检查明显的错误标识
        error_indicators = [
            "[ERROR",
            "[错误",
            "[失败",
            "[系统错误]",
            "[配置错误]",
            "[优化失败]",
            "不可用",
            "异常",
            "Exception",
        ]

        return any(indicator in result for indicator in error_indicators)

    def _validate_optimization_result(self, result: str, original: str) -> bool:
        """
        验证优化结果的基本质量 - V4.1 新增
        Validate basic quality of optimization result - V4.1 New
        """
        if not result or not isinstance(result, str):
            return False

        result = result.strip()
        original = original.strip()

        # 基本长度检查
        if len(result) < 2:
            return False

        # 检查是否过短（相对于原文）
        if len(result) < len(original) * 0.3:
            return False

        # 检查是否过长（可能包含了不必要的内容）
        if len(result) > len(original) * 3:
            return False

        # 检查是否包含明显的技术内容
        technical_indicators = [
            "function",
            "def ",
            "class ",
            "import ",
            "from ",
            "Args:",
            "Returns:",
            "Parameters:",
            "Type:",
        ]

        if any(indicator in result for indicator in technical_indicators):
            return False

        return True

    def _set_optimization_loading_state(self, loading: bool):
        """设置优化按钮的加载状态 - V4.1 增强视觉反馈"""
        # V4.1 更新：改进加载状态的视觉反馈
        if hasattr(self, "optimize_button") and hasattr(self, "enhance_button"):
            self.optimize_button.setEnabled(not loading)
            self.enhance_button.setEnabled(not loading)

            current_language = self.settings_manager.get_current_language()

            if loading:
                # 加载时显示动态提示
                self.optimize_button.setToolTip(
                    self.optimization_texts["loading_optimize"][current_language]
                )
                self.enhance_button.setToolTip(
                    self.optimization_texts["loading_enhance"][current_language]
                )

                # 改变按钮样式以显示加载状态
                self.optimize_button.setStyleSheet(
                    self.optimize_button.styleSheet() + "QPushButton { opacity: 0.6; }"
                )
                self.enhance_button.setStyleSheet(
                    self.enhance_button.styleSheet() + "QPushButton { opacity: 0.6; }"
                )
            else:
                # 恢复正常状态
                self.optimize_button.setToolTip(
                    self.tooltip_texts["optimize_button"][current_language]
                )
                self.enhance_button.setToolTip(
                    self.tooltip_texts["enhance_button"][current_language]
                )

                # 恢复按钮样式
                original_style = self.optimize_button.styleSheet().replace(
                    "QPushButton { opacity: 0.6; }", ""
                )
                self.optimize_button.setStyleSheet(original_style)
                original_style = self.enhance_button.styleSheet().replace(
                    "QPushButton { opacity: 0.6; }", ""
                )
                self.enhance_button.setStyleSheet(original_style)

            # 同时禁用/启用输入框，防止用户在优化过程中修改文本
            if hasattr(self, "text_input"):
                self.text_input.setEnabled(not loading)

            if hasattr(self.text_input, "reinforce_button"):
                self.text_input.reinforce_button.setEnabled(not loading)
                if loading:
                    self.text_input.reinforce_button.setToolTip("🔄 强化中...")
                else:
                    self.text_input.reinforce_button.setToolTip("提示词强化")

    def _convert_error_to_user_friendly(self, error_message: str) -> str:
        """
        将技术性错误消息转换为用户友好的提示 - V4.1 新增
        Convert technical error messages to user-friendly prompts - V4.1 New
        """
        current_language = self.settings_manager.get_current_language()
        
        if not error_message:
            return self.optimization_texts["unknown_error"][current_language]

        # 处理常见的技术错误
        if "[ERROR:AUTH]" in error_message or "API密钥无效" in error_message:
            return self.optimization_texts["api_key_error"][current_language]

        if "[ERROR:RATE]" in error_message or "频率过高" in error_message:
            return self.optimization_texts["rate_limit_error"][current_language]

        if "[ERROR:TIMEOUT]" in error_message or "超时" in error_message:
            return self.optimization_texts["timeout_error"][current_language]

        if "[配置错误]" in error_message or "导入失败" in error_message:
            return self.optimization_texts["config_error"][current_language]

        if (
            "[ERROR:MODEL]" in error_message
            or "模型" in error_message
            and "不存在" in error_message
        ):
            return self.optimization_texts["model_error"][current_language]

        if "[ERROR:SAFETY]" in error_message or "安全过滤" in error_message:
            return self.optimization_texts["safety_error"][current_language]

        # 处理优化失败的情况
        if "[优化失败]" in error_message:
            return self.optimization_texts["optimization_failed"][current_language]

        # 如果是其他错误，提供通用的友好提示
        if error_message.startswith("[") and any(
            keyword in error_message for keyword in ["错误", "失败", "异常"]
        ):
            return self.optimization_texts["general_error"][current_language]

        # 返回原始消息（如果不是错误消息）
        return error_message

    def _show_optimization_message(self, message: str, success: bool = False):
        """显示优化结果消息 - V4.1 增强用户体验"""
        from PySide6.QtWidgets import QMessageBox

        self.disable_auto_minimize = True
        try:
            # 转换错误消息为用户友好格式
            if not success:
                message = self._convert_error_to_user_friendly(message)

            current_language = self.settings_manager.get_current_language()
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(self.optimization_texts["dialog_title"][current_language])
            msg_box.setText(message)

            if success:
                msg_box.setIcon(QMessageBox.Icon.Information)
                # 成功时自动关闭对话框（2秒后）
                QTimer.singleShot(2000, msg_box.accept)
            else:
                msg_box.setIcon(QMessageBox.Icon.Warning)

            msg_box.exec()
        finally:
            self.disable_auto_minimize = False

    def _update_displayed_texts(self):
        """更新界面显示的文本（包括优化按钮）"""
        current_language = self.settings_manager.get_current_language()

        # 更新现有按钮文本
        if hasattr(self, "submit_button"):
            self.submit_button.setText(
                self.button_texts["submit_button"][current_language]
            )

        if hasattr(self, "canned_responses_button"):
            self.canned_responses_button.setText(
                self.button_texts["canned_responses_button"][current_language]
            )
            self.canned_responses_button.setToolTip(
                self.tooltip_texts["canned_responses_button"][current_language]
            )

        if hasattr(self, "select_file_button"):
            self.select_file_button.setText(
                self.button_texts["select_file_button"][current_language]
            )
            self.select_file_button.setToolTip(
                self.tooltip_texts["select_file_button"][current_language]
            )

        if hasattr(self, "screenshot_button"):
            self.screenshot_button.setText(
                self.button_texts["screenshot_button"][current_language]
            )
            self.screenshot_button.setToolTip(
                self.tooltip_texts["screenshot_button"][current_language]
            )

        if hasattr(self, "open_terminal_button"):
            self.open_terminal_button.setText(
                self.button_texts["open_terminal_button"][current_language]
            )
            self.open_terminal_button.setToolTip(
                self.tooltip_texts["open_terminal_button"][current_language]
            )

        if hasattr(self, "pin_window_button"):
            self.pin_window_button.setText(
                self.button_texts["pin_window_button"][current_language]
            )

        if hasattr(self, "settings_button"):
            self.settings_button.setText(
                self.button_texts["settings_button"][current_language]
            )
            self.settings_button.setToolTip(
                self.tooltip_texts["settings_button"][current_language]
            )

        # V4.0 新增：更新优化按钮文本
        if hasattr(self, "optimize_button"):
            self.optimize_button.setText(
                self.button_texts["optimize_button"][current_language]
            )
            self.optimize_button.setToolTip(
                self.tooltip_texts["optimize_button"][current_language]
            )

        if hasattr(self, "enhance_button"):
            self.enhance_button.setText(
                self.button_texts["enhance_button"][current_language]
            )
            self.enhance_button.setToolTip(
                self.tooltip_texts["enhance_button"][current_language]
            )
