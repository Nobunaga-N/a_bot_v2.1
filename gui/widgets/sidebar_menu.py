from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QFont


class SidebarMenu(QFrame):
    """
    Боковое меню с навигацией по разделам приложения.

    Сигналы:
        page_changed(str): Испускается при переключении между разделами.
    """

    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")

        # Настройка размеров
        self.setFixedWidth(75)

        # Активная страница
        self.active_page = "home"

        # Определение разделов
        self.pages = {
            "home": {"icon": "home.png", "tooltip": "Главная"},
            "stats": {"icon": "stats.png", "tooltip": "Статистика"},
            "settings": {"icon": "settings.png", "tooltip": "Настройки"},
            "license": {"icon": "license.png", "tooltip": "Лицензия"}
        }

        # Инициализация UI
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса бокового меню."""
        # Основной лэйаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Логотип приложения
        logo_layout = QHBoxLayout()
        logo_layout.setContentsMargins(0, 15, 0, 15)

        logo_label = QLabel("AoM")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #3FE0C8;
        """)

        logo_layout.addWidget(logo_label)
        layout.addLayout(logo_layout)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #353E65;")
        separator.setMaximumHeight(1)
        layout.addWidget(separator)

        # Кнопки навигации
        self.buttons = {}

        for page_id, page_info in self.pages.items():
            button = self.create_sidebar_button(
                page_id,
                page_info["icon"],
                page_info["tooltip"]
            )
            layout.addWidget(button)
            self.buttons[page_id] = button

        # Отметить активную страницу
        self.buttons[self.active_page].setChecked(True)

        # Автоматическое расширение в конце
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def create_sidebar_button(self, page_id, icon_name, tooltip):
        """
        Создает кнопку для бокового меню.

        Args:
            page_id (str): ID страницы
            icon_name (str): Имя файла иконки
            tooltip (str): Текст всплывающей подсказки

        Returns:
            QPushButton: Созданная кнопка
        """
        button = QPushButton()
        button.setObjectName("sidebar_button")
        button.setToolTip(tooltip)
        button.setCheckable(True)
        button.setFixedHeight(60)

        # Загрузить иконку
        try:
            from PyQt6.QtCore import QSize
            # Добавим проверку на наличие файла иконки
            import os
            icon_path = f"resources/icons/{icon_name}"
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
            else:
                # Установим текстовый заголовок, если иконка не найдена
                first_letter = tooltip[0] if tooltip else page_id[0]
                button.setText(first_letter.upper())
        except Exception as e:
            print(f"Ошибка загрузки иконки {icon_name}: {e}")
            button.setText(tooltip[0].upper())

        button.setIconSize(QSize(24, 24))

        # Подключение события
        button.clicked.connect(lambda: self.change_page(page_id))

        return button

    def change_page(self, page_id):
        """
        Изменяет активную страницу.

        Args:
            page_id (str): ID страницы для отображения
        """
        # Если страница уже активна - ничего не делаем
        if page_id == self.active_page:
            self.buttons[page_id].setChecked(True)
            return

        # Обновляем состояние кнопок
        for page, button in self.buttons.items():
            button.setChecked(page == page_id)

        # Обновляем активную страницу
        self.active_page = page_id

        # Отправляем сигнал об изменении страницы
        self.page_changed.emit(page_id)