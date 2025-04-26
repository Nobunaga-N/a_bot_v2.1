from PyQt6.QtWidgets import QPushButton, QButtonGroup
from PyQt6.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QFont, QPen, QBrush


class FancyButton(QPushButton):
    """
    Стилизованная кнопка с анимированным градиентом.

    Особенности:
    - Анимированный движущийся градиент
    - Эффекты при наведении и нажатии
    - Прямоугольная форма с закругленными углами
    """

    def __init__(self, text, parent=None, success=True):
        """
        Инициализирует кнопку с анимированным градиентом.

        Args:
            text (str): Текст кнопки
            parent (QWidget, optional): Родительский виджет
            success (bool, optional): Тип кнопки: True для зеленой/желтой (успех), False для красной (отмена)
        """
        super().__init__(text, parent)

        # Состояние кнопки
        self.hovered = False
        self.pressed = False
        self._active = False

        # Параметр для анимации градиента
        self._gradient_position = 0.0

        # Определение цветов для разных типов кнопок
        if success:
            # Зеленая кнопка для "Start"
            self.primary_color = QColor("#22c55e")  # Зеленый
            self.secondary_color = QColor("#16a34a")  # Темно-зеленый
            self.hover_color = QColor("#4ade80")  # Светло-зеленый
            self.text_color = QColor("#ffffff")  # Белый для лучшей читаемости на зеленом
        else:
            # Красная кнопка для "Stop"
            self.primary_color = QColor("#FF6B6C")  # Красный
            self.secondary_color = QColor("#e53e3f")  # Темно-красный
            self.hover_color = QColor("#FF8E8F")  # Светло-красный
            self.text_color = QColor("#ffffff")  # Белый для лучшей читаемости на красном

        # Настройка шрифта
        font = self.font()
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)

        # Настройка размеров
        self.setFixedHeight(40)
        self.setMinimumWidth(120)

        # Курсор при наведении
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Таймер для анимации градиента
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_gradient)
        self.animation_timer.start(50)  # Обновление каждые 50мс

        # Анимация для нажатия
        self.press_animation = QPropertyAnimation(self, b"pressed_scale")
        self.press_animation.setDuration(150)
        self.press_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Стилизация кнопки
        self.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 8px 16px;
            }
        """)

    def update_gradient(self):
        """Обновляет позицию градиента для анимации."""
        self._gradient_position = (self._gradient_position + 0.05) % 2.0

        # Обновляем только данную кнопку, а не весь интерфейс
        # Это предотвращает нежелательное мерцание других кнопок
        self.update()  # Перерисовка только этой кнопки

    def get_pressed_scale(self):
        """Геттер для масштаба при нажатии."""
        return getattr(self, "_pressed_scale", 1.0)

    def set_pressed_scale(self, scale):
        """Сеттер для масштаба при нажатии."""
        self._pressed_scale = scale
        self.update()

    # Свойство для анимации масштаба при нажатии
    pressed_scale = pyqtProperty(float, get_pressed_scale, set_pressed_scale)

    def isActive(self):
        """Возвращает активность кнопки."""
        return self._active

    def setActive(self, active):
        """Устанавливает активность кнопки."""
        if self._active == active:
            return

        self._active = active

        # Если кнопка становится активной, деактивируем другие кнопки в группе
        if active and hasattr(self, 'group') and self.group:
            for button in self.group.buttons:
                if button != self and button.isActive():
                    # Отключаем таймер анимации градиента временно, чтобы избежать мерцания
                    old_timer_state = button.animation_timer.isActive()
                    if old_timer_state:
                        button.animation_timer.stop()

                    # Деактивируем другую кнопку
                    button._active = False
                    button.update()

                    # Восстанавливаем состояние таймера
                    if old_timer_state:
                        button.animation_timer.start()

        # Запускаем анимацию масштаба
        self.press_animation.stop()

        if active:
            # Слегка уменьшаем активную кнопку для показа "нажатого" состояния
            self.press_animation.setStartValue(self.get_pressed_scale())
            self.press_animation.setEndValue(0.97)
            self.press_animation.start()
        else:
            # Возвращаем к обычному размеру неактивную кнопку
            self.press_animation.setStartValue(self.get_pressed_scale())
            self.press_animation.setEndValue(1.0)
            self.press_animation.start()

        # Обновляем только эту кнопку
        self.update()

    def paintEvent(self, event):
        """Отрисовка кнопки с градиентом."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Масштабируем внутренний прямоугольник при нажатии
        scale = getattr(self, "_pressed_scale", 1.0)
        if scale < 1.0:
            # Создаем эффект нажатия, уменьшая внутренний размер
            diff_w = int(rect.width() * (1 - scale) / 2)
            diff_h = int(rect.height() * (1 - scale) / 2)
            rect = rect.adjusted(diff_w, diff_h, -diff_w, -diff_h)

        # Определяем цвета в зависимости от состояния
        if self._active:
            # Активная кнопка имеет более насыщенный цвет
            primary = self.secondary_color.darker(110)
            secondary = self.primary_color.darker(110)
            highlight = self.hover_color.darker(110)
        elif self.hovered:
            # Наведение - более яркие цвета
            primary = self.hover_color
            secondary = self.primary_color
            highlight = self.secondary_color
        else:
            # Обычное состояние
            primary = self.primary_color
            secondary = self.secondary_color
            highlight = self.primary_color

        # Создаем градиент с анимацией движения
        gradient = QLinearGradient(
            rect.width() * self._gradient_position - rect.width(),
            0,
            rect.width() * self._gradient_position,
            rect.height()
        )

        gradient.setColorAt(0.0, primary)
        gradient.setColorAt(0.5, secondary)
        gradient.setColorAt(1.0, highlight)

        # Рисуем белую обводку (чуть шире для видимости)
        border_width = 2
        painter.setPen(QPen(QColor(255, 255, 255), border_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(
            rect.adjusted(border_width // 2, border_width // 2, -border_width // 2, -border_width // 2), 10, 10)

        # Рисуем фон кнопки
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect.adjusted(border_width, border_width, -border_width, -border_width), 8, 8)

        # Добавляем эффект блика только для неактивной и ненажатой кнопки
        if not self.pressed and not self._active:
            highlight_rect = rect.adjusted(border_width, border_width, -border_width, int(-rect.height() * 0.7))
            highlight_gradient = QLinearGradient(
                highlight_rect.x(), highlight_rect.y(),
                highlight_rect.x(), highlight_rect.y() + highlight_rect.height()
            )
            highlight_gradient.setColorAt(0, QColor(255, 255, 255, 60))
            highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(highlight_gradient)
            painter.setClipRect(highlight_rect)
            painter.drawRoundedRect(highlight_rect, 8, 8)
            painter.setClipping(False)

        # Рисуем текст с тенью
        text_rect = rect

        # Тень текста (небольшое смещение вниз и вправо)
        shadow_offset = 1
        text_shadow_rect = text_rect.adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset)
        painter.setPen(QColor(0, 0, 0, 70))
        painter.drawText(text_shadow_rect, Qt.AlignmentFlag.AlignCenter, self.text())

        # Основной текст
        painter.setPen(self.text_color)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())

    def enterEvent(self, event):
        """Обработка события при наведении мыши."""
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Обработка события при уходе мыши."""
        self.hovered = False
        self.pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Обработка события при нажатии мыши."""
        self.pressed = True

        # Анимация уменьшения при нажатии
        self.press_animation.stop()
        self.press_animation.setStartValue(1.0)
        self.press_animation.setEndValue(0.95)  # Уменьшаем размер на 5%
        self.press_animation.start()

        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Обработка события при отпускании мыши."""
        self.pressed = False

        # Анимация возвращения к нормальному размеру
        self.press_animation.stop()
        self.press_animation.setStartValue(self.get_pressed_scale())
        self.press_animation.setEndValue(1.0)
        self.press_animation.start()

        # Активируем кнопку если она была нажата в пределах кнопки
        if self.rect().contains(event.pos()):
            self.setActive(True)

        self.update()
        super().mouseReleaseEvent(event)


class FancyButtonGroup:
    """Группа для управления связанными FancyButton, где только одна кнопка может быть активной."""

    def __init__(self):
        self.buttons = []

    def addButton(self, button):
        """Добавляет кнопку в группу."""
        self.buttons.append(button)
        button.group = self

    def setExclusive(self, exclusive):
        """Устанавливает эксклюзивный режим (только одна активная кнопка)."""
        # В текущей реализации группа всегда эксклюзивна
        pass

    def findChildren(self, cls):
        """Возвращает все кнопки в группе указанного класса."""
        return [b for b in self.buttons if isinstance(b, cls)]