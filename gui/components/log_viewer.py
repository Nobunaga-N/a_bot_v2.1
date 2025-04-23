import datetime
from PyQt6.QtWidgets import QTextEdit, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor

from gui.styles import Styles


class LogViewer(QTextEdit):
    """
    Компонент для отображения логов с цветовой дифференциацией по уровням.
    """

    def __init__(self, parent=None):
        """
        Инициализирует просмотрщик логов.

        Args:
            parent (QWidget, optional): Родительский виджет
        """
        super().__init__(parent)

        # Настройка внешнего вида
        self.setObjectName("log")
        self.setReadOnly(True)

        # Используем моноширинный шрифт для лучшего отображения логов
        font = QFont("Consolas", Styles.FONTS["size_normal"])
        self.setFont(font)

        # Цвета для разных уровней логирования
        self.log_colors = Styles.get_log_colors()

    def append_log(self, level, message):
        """
        Добавляет сообщение в лог с соответствующим уровнем.

        Args:
            level (str): Уровень логирования (info, warning, error, debug)
            message (str): Текст сообщения
        """
        # Получаем текущее время
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # Получаем цвет для уровня логирования
        color = self.log_colors.get(level.lower(), self.log_colors["info"])

        # Иконки для разных уровней логирования
        level_icons = {
            "info": "ℹ",
            "warning": "⚠",
            "error": "🚨",
            "debug": "🔍"
        }

        icon = level_icons.get(level.lower(), "")

        # Форматируем сообщение лога с HTML
        html_message = f'<span style="color:{color};">[{timestamp}] [{level.upper()}] {icon} {message}</span><br>'

        # Добавляем в лог
        self.insertHtml(html_message)

        # Прокручиваем до конца
        self.moveCursor(QTextCursor.MoveOperation.End)

    def clear(self):
        """Очищает содержимое лога."""
        super().clear()

        # Добавляем сообщение о очистке
        self.append_log("info", "Журнал был очищен")