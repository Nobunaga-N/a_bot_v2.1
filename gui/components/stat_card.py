from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class StatCard(QFrame):
    """
    Карточка для отображения статистических данных.

    Отображает заголовок и значение в виде стилизованной карточки.
    """

    def __init__(self, title, value, color, icon=None, parent=None):
        """
        Инициализирует карточку статистики.

        Args:
            title (str): Заголовок карточки
            value (str): Значение статистики
            color (str): Цвет карточки (hex формат)
            icon (str, optional): Имя иконки (если есть)
            parent (QWidget, optional): Родительский виджет
        """
        super().__init__(parent)
        self.setObjectName("stat_card")

        # Настройка внешнего вида
        self.setStyleSheet(f"""
            QFrame#stat_card {{
                background-color: #2A3158;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 15px;
                min-height: 100px;
            }}
        """)

        # Создание лейаута
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Заголовок
        self.title_label = QLabel(title)
        self.title_label.setObjectName("title")
        self.title_label.setStyleSheet(f"""
            font-size: 12px;
            color: #9BA0BC;
            background-color: transparent;
        """)
        layout.addWidget(self.title_label)

        # Значение
        self.value_label = QLabel(value)
        self.value_label.setObjectName("value")
        self.value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {color};
            background-color: transparent;
        """)
        layout.addWidget(self.value_label)

        # Добавляем автоматическое расширение снизу
        layout.addStretch()

    def set_value(self, value):
        """
        Обновляет значение в карточке.

        Args:
            value (str): Новое значение
        """
        self.value_label.setText(value)