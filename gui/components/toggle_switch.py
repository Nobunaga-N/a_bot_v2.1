from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

from gui.styles import Styles


class ToggleSwitch(QFrame):
    """
    Анимированный переключатель (Toggle Switch).

    Визуальный компонент, который позволяет переключаться между состояниями Вкл/Выкл.
    """

    def __init__(self, parent=None):
        """
        Инициализирует переключатель.

        Args:
            parent (QWidget, optional): Родительский виджет
        """
        super().__init__(parent)

        # Настройка внешнего вида
        self.setObjectName("toggle_switch")
        self.setFixedSize(50, 24)

        # Инициализация состояния
        self._checked = False

        # Позиция кружка переключателя
        self._circle_position = 4

        # Настройка анимации
        self.animation = QPropertyAnimation(self, b"circle_position")
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setDuration(200)  # 200 мс

        # Обновляем вид
        self.update_styles()

    def update_styles(self):
        """Обновляет стили переключателя в зависимости от состояния."""
        # Применяем атрибут toggled для CSS-стилизации
        self.setProperty("toggled", self._checked)

        # Необходимо для обновления стилей
        self.style().unpolish(self)
        self.style().polish(self)

    def get_circle_position(self):
        """Геттер для позиции кружка."""
        return self._circle_position

    def set_circle_position(self, position):
        """Сеттер для позиции кружка."""
        self._circle_position = position
        self.update()  # Перерисовка

    # Определение свойства для анимации
    circle_position = pyqtProperty(float, get_circle_position, set_circle_position)

    def paintEvent(self, event):
        """Событие отрисовки переключателя."""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Отрисовка кружка переключателя
        painter.setPen(Qt.PenStyle.NoPen)

        if self._checked:
            # Цвет индикатора для включенного состояния
            painter.setBrush(QBrush(QColor("#FFFFFF")))
        else:
            # Цвет индикатора для выключенного состояния
            painter.setBrush(QBrush(QColor("#AAAAAA")))

        # Отрисовка кружка
        circle_radius = 10
        painter.drawEllipse(
            int(self._circle_position),
            int(self.height() / 2 - circle_radius / 2),
            circle_radius,
            circle_radius
        )

    def mousePressEvent(self, event):
        """Обработка нажатия мыши."""
        # Меняем состояние
        self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def isChecked(self):
        """Возвращает текущее состояние переключателя."""
        return self._checked

    def setChecked(self, checked):
        """Устанавливает состояние переключателя."""
        if self._checked != checked:
            self._checked = checked

            # Определяем начальную и конечную позиции для анимации
            if checked:
                start_pos = 4
                end_pos = self.width() - 14
            else:
                start_pos = self.width() - 14
                end_pos = 4

            # Настраиваем и запускаем анимацию
            self.animation.setStartValue(start_pos)
            self.animation.setEndValue(end_pos)
            self.animation.start()

            # Обновляем стили
            self.update_styles()

            # Вызываем сигнал toggled (если нужен)