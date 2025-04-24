from PyQt6.QtGui import QColor, QPalette, QFont
from PyQt6.QtCore import Qt


class Styles:
    """
    Централизованное хранилище стилей для приложения.
    Содержит цвета, шрифты и таблицы стилей для единообразного отображения.
    """

    # Цветовая палитра
    COLORS = {
        # Основные цвета
        "primary": "#3FE0C8",  # Бирюзовый
        "primary_light": "#5CE8D5",
        "primary_dark": "#2BC8B0",

        # Второстепенные цвета
        "secondary": "#42E189",  # Зеленый
        "secondary_light": "#67E7A1",
        "secondary_dark": "#30C973",

        # Акцентные цвета
        "accent": "#FF6B6C",  # Красный
        "accent_light": "#FF8E8F",
        "accent_dark": "#E63E3F",

        # Цвета предупреждений
        "warning": "#FFB169",  # Оранжевый
        "warning_light": "#FFC490",
        "warning_dark": "#F49744",

        # Цвет ссылок
        "link": "#66B8FF",  # Голубой

        # Нейтральные цвета
        "background_dark": "#171D33",  # Темно-синий фон
        "background_medium": "#1E2645",  # Средне-темный синий
        "background_light": "#2A3158",  # Более светлый синий для карточек
        "background_input": "#1C2339",  # Цвет фона для полей ввода
        "text_primary": "#FFFFFF",  # Белый текст
        "text_secondary": "#9BA0BC",  # Серо-голубой текст
        "border": "#353E65",  # Цвет границ
        "sidebar": "#161C30",  # Цвет бокового меню
        "sidebar_active": "#1E2542",  # Активная вкладка в боковом меню
    }

    # Настройки шрифтов
    FONTS = {
        "family": "Segoe UI",
        "size_small": 9,
        "size_normal": 10,
        "size_large": 12,
        "size_title": 14,
    }

    @classmethod
    def get_dark_palette(cls):
        """Создание темной цветовой палитры для приложения."""
        palette = QPalette()

        # Установка фона окна и виджетов
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.COLORS["background_dark"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.COLORS["text_primary"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.COLORS["background_medium"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(cls.COLORS["background_light"]))

        # Установка цветов текста
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.COLORS["text_primary"]))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(cls.COLORS["text_primary"]))

        # Установка цветов кнопок
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.COLORS["background_light"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.COLORS["text_primary"]))

        # Установка цветов выделения
        palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.COLORS["primary"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(cls.COLORS["text_primary"]))

        # Установка цветов для отключенных элементов
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText,
                         QColor(cls.COLORS["text_secondary"]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,
                         QColor(cls.COLORS["text_secondary"]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
                         QColor(cls.COLORS["text_secondary"]))

        # Установка цветов всплывающих подсказок
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(cls.COLORS["background_light"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(cls.COLORS["text_primary"]))

        return palette

    @classmethod
    def get_base_stylesheet(cls):
        """Получить базовую таблицу стилей для приложения."""
        return f"""
            QWidget {{
                background-color: {cls.COLORS["background_dark"]};
                color: {cls.COLORS["text_primary"]};
                font-family: "{cls.FONTS["family"]}";
                font-size: {cls.FONTS["size_normal"]}pt;
            }}

            QLabel {{
                color: {cls.COLORS["text_primary"]};
                background-color: transparent;
            }}

            QLabel#title {{
                font-size: {cls.FONTS["size_title"]}pt;
                font-weight: bold;
                color: {cls.COLORS["text_primary"]};
            }}

            QLabel#subtitle {{
                font-size: {cls.FONTS["size_large"]}pt;
                color: {cls.COLORS["text_secondary"]};
            }}

            QPushButton {{
                background-color: {cls.COLORS["primary"]};
                color: {cls.COLORS["background_dark"]};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {cls.COLORS["primary_light"]};
            }}

            QPushButton:pressed {{
                background-color: {cls.COLORS["primary_dark"]};
            }}

            QPushButton:disabled {{
                background-color: {cls.COLORS["background_light"]};
                color: {cls.COLORS["text_secondary"]};
            }}

            QPushButton#success {{
                background-color: {cls.COLORS["secondary"]};
            }}

            QPushButton#success:hover {{
                background-color: {cls.COLORS["secondary_light"]};
            }}

            QPushButton#success:pressed {{
                background-color: {cls.COLORS["secondary_dark"]};
            }}

            QPushButton#danger {{
                background-color: {cls.COLORS["accent"]};
            }}

            QPushButton#danger:hover {{
                background-color: {cls.COLORS["accent_light"]};
            }}

            QPushButton#danger:pressed {{
                background-color: {cls.COLORS["accent_dark"]};
            }}

            QPushButton#warning {{
                background-color: {cls.COLORS["warning"]};
            }}

            QPushButton#warning:hover {{
                background-color: {cls.COLORS["warning_light"]};
            }}

            QPushButton#warning:pressed {{
                background-color: {cls.COLORS["warning_dark"]};
            }}

            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {{
                background-color: {cls.COLORS["background_input"]};
                color: {cls.COLORS["text_primary"]};
                border: 1px solid {cls.COLORS["border"]};
                border-radius: 4px;
                padding: 6px;
            }}

            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {{
                border: 1px solid {cls.COLORS["primary"]};
            }}

            QTextEdit#log, QPlainTextEdit#log {{
                background-color: {cls.COLORS["background_input"]};
                color: {cls.COLORS["text_primary"]};
                font-family: "Consolas", "Courier New", monospace;
                font-size: {cls.FONTS["size_normal"]}pt;
            }}

            QProgressBar {{
                border: 1px solid {cls.COLORS["border"]};
                border-radius: 4px;
                text-align: center;
                background-color: {cls.COLORS["background_medium"]};
            }}

            QProgressBar::chunk {{
                background-color: {cls.COLORS["primary"]};
                width: 1px;
            }}

            QStatusBar {{
                background-color: {cls.COLORS["background_medium"]};
                color: {cls.COLORS["text_primary"]};
            }}

            QMenuBar {{
                background-color: {cls.COLORS["background_medium"]};
                color: {cls.COLORS["text_primary"]};
            }}

            QMenuBar::item:selected {{
                background-color: {cls.COLORS["primary"]};
            }}

            QMenu {{
                background-color: {cls.COLORS["background_medium"]};
                color: {cls.COLORS["text_primary"]};
            }}

            QMenu::item:selected {{
                background-color: {cls.COLORS["primary"]};
            }}

            QToolTip {{
                background-color: {cls.COLORS["background_light"]};
                color: {cls.COLORS["text_primary"]};
                border: 1px solid {cls.COLORS["border"]};
            }}

            QTabWidget::pane {{
                border: 1px solid {cls.COLORS["border"]};
                background-color: {cls.COLORS["background_medium"]};
            }}

            QTabBar::tab {{
                background-color: {cls.COLORS["background_light"]};
                color: {cls.COLORS["text_primary"]};
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}

            QTabBar::tab:selected {{
                background-color: {cls.COLORS["primary"]};
                color: {cls.COLORS["background_dark"]};
            }}

            QGroupBox {{
                border: 1px solid {cls.COLORS["border"]};
                border-radius: 4px;
                margin-top: 16px;
                font-weight: bold;
                background-color: {cls.COLORS["background_light"]};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {cls.COLORS["text_primary"]};
                background-color: transparent;
            }}

            QScrollArea {{
                border: none;
                background-color: transparent;
            }}

            QScrollBar:vertical {{
                background: {cls.COLORS["background_dark"]};
                width: 12px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {cls.COLORS["border"]};
                min-height: 20px;
                border-radius: 6px;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar:horizontal {{
                background: {cls.COLORS["background_dark"]};
                height: 12px;
                margin: 0px;
            }}

            QScrollBar::handle:horizontal {{
                background: {cls.COLORS["border"]};
                min-width: 20px;
                border-radius: 6px;
            }}

            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}

            QComboBox {{
                background-color: {cls.COLORS["background_input"]};
                color: {cls.COLORS["text_primary"]};
                border: 1px solid {cls.COLORS["border"]};
                border-radius: 4px;
                padding: 4px 10px;
                min-width: 6em;
            }}

            QComboBox:focus {{
                border: 1px solid {cls.COLORS["primary"]};
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {cls.COLORS["border"]};
                border-left-style: solid;
            }}

            QComboBox QAbstractItemView {{
                background-color: {cls.COLORS["background_medium"]};
                color: {cls.COLORS["text_primary"]};
                selection-background-color: {cls.COLORS["primary"]};
                selection-color: {cls.COLORS["background_dark"]};
            }}

            /* Стили для боковой панели */
            QFrame#sidebar {{
                background-color: {cls.COLORS["sidebar"]};
                border-right: 1px solid {cls.COLORS["border"]};
            }}

            QPushButton#sidebar_button {{
                background-color: transparent;
                color: {cls.COLORS["text_secondary"]};
                border: none;
                border-radius: 0;
                text-align: center;
                padding: 10px 0px;
                font-size: {cls.FONTS["size_normal"]}pt;
            }}

            QPushButton#sidebar_button:hover {{
                background-color: {cls.COLORS["sidebar_active"]};
                color: {cls.COLORS["text_primary"]};
            }}

            QPushButton#sidebar_button:checked {{
                background-color: {cls.COLORS["sidebar_active"]};
                color: {cls.COLORS["primary"]};
                border-left: 3px solid {cls.COLORS["primary"]};
            }}

            /* Стили для карточек статистики */
            QFrame#stat_card {{
                background-color: {cls.COLORS["background_light"]};
                border-radius: 8px;
                padding: 15px;
                min-height: 100px;
            }}

            QFrame#stat_card QLabel#value {{
                font-size: 24pt;
                font-weight: bold;
            }}

            QFrame#stat_card QLabel#title {{
                font-size: {cls.FONTS["size_normal"]}pt;
                color: {cls.COLORS["text_secondary"]};
            }}

            QFrame#section_box {{
                background-color: {cls.COLORS["background_light"]};
                border-radius: 8px;
                padding: 0px;
            }}

            QFrame#section_box QLabel#header {{
                padding: 15px;
                font-weight: bold;
                border-bottom: 1px solid {cls.COLORS["border"]};
                height: 25px;
                min-height: 25px;
                max-height: 25px;
            }}

            QFrame#toggle_switch {{
                border-radius: 10px;
                border: 2px solid {cls.COLORS["border"]};
                background-color: {cls.COLORS["background_input"]};
            }}

            QFrame#toggle_switch[toggled="true"] {{
                background-color: {cls.COLORS["primary"]};
                border: 2px solid {cls.COLORS["primary"]};
            }}
            
                        /* Специальные стили для основных кнопок действий */
            QPushButton#action_button_success {{
                background-color: rgba(66, 225, 137, 0.15);  /* Полупрозрачный зеленый фон */
                color: %(secondary)s;
                border: 2px solid %(secondary)s;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 140px;
                height: 40px;
                font-size: 13px;
            }}
            
            QPushButton#action_button_success:hover {{
                background-color: rgba(66, 225, 137, 0.25);  /* Более яркий при наведении */
                border-color: %(secondary_light)s;
            }}
            
            QPushButton#action_button_success:pressed {{
                background-color: rgba(66, 225, 137, 0.35);  /* Еще ярче при нажатии */
                border-color: %(secondary_dark)s;
            }}
            
            QPushButton#action_button_danger {{
                background-color: rgba(255, 107, 108, 0.15);  /* Полупрозрачный красный фон */
                color: %(accent)s;
                border: 2px solid %(accent)s;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 140px;
                height: 40px;
                font-size: 13px;
            }}
            
            QPushButton#action_button_danger:hover {{
                background-color: rgba(255, 107, 108, 0.25);  /* Более яркий при наведении */
                border-color: %(accent_light)s;
            }}
            
            QPushButton#action_button_danger:pressed {{
                background-color: rgba(255, 107, 108, 0.35);  /* Еще ярче при нажатии */
                border-color: %(accent_dark)s;
            }}
            
            QPushButton#action_button_primary {{
                background-color: rgba(63, 224, 200, 0.15);  /* Полупрозрачный бирюзовый фон */
                color: %(primary)s;
                border: 2px solid %(primary)s;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 140px;
                height: 40px;
                font-size: 13px;
            }}
            
            QPushButton#action_button_primary:hover {{
                background-color: rgba(63, 224, 200, 0.25);  /* Более яркий при наведении */
                border-color: %(primary_light)s;
            }}
            
            QPushButton#action_button_primary:pressed {{
                background-color: rgba(63, 224, 200, 0.35);  /* Еще ярче при нажатии */
                border-color: %(primary_dark)s;
            }}
        """

    @classmethod
    def get_log_colors(cls):
        """Получить цвета для различных уровней логирования."""
        return {
            "info": cls.COLORS["text_primary"],
            "warning": cls.COLORS["warning"],
            "error": cls.COLORS["accent"],
            "debug": cls.COLORS["secondary"],
        }