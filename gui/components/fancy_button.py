from PyQt6.QtWidgets import QPushButton, QButtonGroup
from PyQt6.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient


class FancyButton(QPushButton):
    """
    Объемная анимированная кнопка с эффектом переключения.

    Особенности:
    - Постоянная плавная анимация
    - Эффект вдавливания при нажатии
    - Режим "активации" для переключения между кнопками
    - Эффект объема и тени
    """

    def __init__(self, text, parent=None, success=True):
        """
        Инициализирует объемную кнопку с живой анимацией.

        Args:
            text (str): Текст кнопки
            parent (QWidget, optional): Родительский виджет
            success (bool, optional): Тип кнопки: True для зеленой (успех), False для красной (отмена)
        """
        super().__init__(text, parent)

        # Параметры анимации и состояния
        self.success = success
        self.max_shadow_offset = 4
        self._shadow_offset = self.max_shadow_offset
        self._active = False  # Состояние активации (вдавленности)
        self.hover = False
        self.pressed = False
        self.wave_position = 0  # Позиция анимации волны
        self.group = None  # Группа кнопок для переключения

        # Настройка шрифта и размеров
        font = self.font()
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)

        # Определение цветов для разных типов кнопок
        if success:
            # Зеленая кнопка для "Запустить"
            self.bg_color = QColor("#42E189")  # Зеленый
            self.highlight_color = QColor("#67E7A1")  # Светло-зеленый
            self.shadow_color = QColor("#30C973")  # Темно-зеленый
            self.glow_color = QColor(66, 225, 137, 80)  # Полупрозрачный зеленый для свечения
        else:
            # Красная кнопка для "Остановить"
            self.bg_color = QColor("#FF6B6C")  # Красный
            self.highlight_color = QColor("#FF8E8F")  # Светло-красный
            self.shadow_color = QColor("#E63E3F")  # Темно-красный
            self.glow_color = QColor(255, 107, 108, 80)  # Полупрозрачный красный для свечения

        # Цвета рамки и текста (общие для обоих типов)
        self.border_color = QColor("#292524")  # Темно-серый
        self.text_color = QColor("#292524")  # Темно-серый
        self.outline_color = QColor("#fafaf9")  # Почти белый

        # Установка фиксированного размера
        self.setFixedHeight(46)
        self.setMinimumWidth(160)

        # Курсор в виде указательного пальца при наведении
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Создание анимации для эффекта вдавливания
        self.press_animation = QPropertyAnimation(self, b"shadow_offset")
        self.press_animation.setDuration(150)
        self.press_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Таймер для постоянной анимации
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(30)  # Обновление каждые 30мс для более плавной анимации

    # Свойство для анимации смещения тени
    def get_shadow_offset(self):
        return self._shadow_offset

    def set_shadow_offset(self, value):
        self._shadow_offset = value
        self.update()

    shadow_offset = pyqtProperty(float, get_shadow_offset, set_shadow_offset)

    # Свойство для состояния активации
    def isActive(self):
        return self._active

    def setActive(self, active):
        """
        Устанавливает состояние активации кнопки и деактивирует другие кнопки в группе.

        Args:
            active (bool): Новое состояние активации
        """
        if self._active == active:
            return

        self._active = active

        # Анимация для изменения состояния
        self.press_animation.stop()

        if active:
            # Деактивируем другие кнопки в группе
            if self.group:
                for button in self.group.findChildren(FancyButton):
                    if button != self and button.isActive():
                        button.setActive(False)

            # Анимация "вдавливания"
            self.press_animation.setStartValue(self._shadow_offset)
            self.press_animation.setEndValue(0)
            self.press_animation.start()
        else:
            # Анимация "выхода" из вдавленного состояния
            self.press_animation.setStartValue(self._shadow_offset)
            self.press_animation.setEndValue(self.max_shadow_offset)
            self.press_animation.start()

        self.update()

    def update_animation(self):
        """Обновляет состояние анимации волны."""
        # Продвигаем позицию волны для создания эффекта движения
        self.wave_position = (self.wave_position + 1) % 100
        self.update()  # Перерисовка кнопки

    def paintEvent(self, event):
        """Кастомная отрисовка кнопки со всеми эффектами."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        width = rect.width()
        height = rect.height()

        # Расчет смещения (целое число для текущего отображения)
        shadow_offset = int(self._shadow_offset)

        # Внешняя рамка (черная)
        painter.setPen(QPen(self.border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        outer_border_rect = QRect(1, 1, width - 2, height - 2)
        painter.drawRoundedRect(outer_border_rect, 20, 20)

        # Светлый контур
        painter.setPen(QPen(self.outline_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        light_outline_rect = QRect(4, 4, width - 8, height - 8)
        painter.drawRoundedRect(light_outline_rect, 18, 18)

        # Тени (несколько слоев для создания объема)
        for i in range(shadow_offset, 0, -1):
            shadow_rect = QRect(i, i, width - i * 2, height - i * 2)
            painter.setPen(QPen(self.border_color, 1))
            painter.setBrush(QBrush(self.shadow_color))
            painter.drawRoundedRect(shadow_rect, 19 - i, 19 - i)

        # Основной фон кнопки (с градиентом)
        button_rect = QRect(shadow_offset, shadow_offset,
                            width - shadow_offset * 2,
                            height - shadow_offset * 2)

        # Создаем градиент для основного фона
        gradient = QLinearGradient(0, button_rect.top(), 0, button_rect.bottom())
        gradient.setColorAt(0, self.highlight_color)
        gradient.setColorAt(1, self.bg_color)

        painter.setPen(QPen(self.border_color, 1.5))
        painter.setBrush(gradient)
        painter.drawRoundedRect(button_rect, 18, 18)

        # Белая внутренняя граница для объема
        painter.setPen(QPen(QColor(255, 255, 255, 90), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inner_border = QRect(button_rect.x() + 2, button_rect.y() + 2,
                             button_rect.width() - 4, button_rect.height() - 4)
        painter.drawRoundedRect(inner_border, 16, 16)

        # Анимированная волна/свечение
        # Используем радиальный градиент, который перемещается внутри кнопки
        x_position = (button_rect.width() * self.wave_position / 100) + button_rect.x()

        glow = QRadialGradient(
            x_position, button_rect.center().y(),
            button_rect.width() * 0.6
        )

        # Настраиваем цвета градиента
        glow.setColorAt(0, self.glow_color)
        glow.setColorAt(0.8, QColor(255, 255, 255, 10))
        glow.setColorAt(1, QColor(255, 255, 255, 0))

        # Отрисовка свечения
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)

        # Используем клип-маску для ограничения свечения границами кнопки
        painter.setClipRect(button_rect)
        painter.setOpacity(0.7)
        painter.drawEllipse(
            int(x_position - button_rect.width() * 0.6),
            int(button_rect.center().y() - button_rect.width() * 0.6),
            int(button_rect.width() * 1.2),
            int(button_rect.width() * 1.2)
        )
        painter.setClipping(False)
        painter.setOpacity(1.0)

        # Отрисовка текста с тенью
        text_rect = button_rect

        # Тень текста (эффект обводки)
        shadow_offset = 1
        text_shadow_rect = text_rect.adjusted(shadow_offset, shadow_offset, 0, 0)
        painter.setPen(QColor(0, 0, 0, 60))
        painter.drawText(text_shadow_rect, Qt.AlignmentFlag.AlignCenter, self.text())

        # Основной текст
        painter.setPen(self.text_color)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())

    def enterEvent(self, event):
        """Анимация при наведении курсора."""
        self.hover = True

        # Запускаем анимацию только если кнопка не активна
        if not self._active:
            self.press_animation.stop()
            self.press_animation.setStartValue(self._shadow_offset)
            self.press_animation.setEndValue(self.max_shadow_offset * 0.5)
            self.press_animation.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Анимация при уходе курсора."""
        self.hover = False
        self.pressed = False

        # Запускаем анимацию только если кнопка не активна
        if not self._active:
            self.press_animation.stop()
            self.press_animation.setStartValue(self._shadow_offset)
            self.press_animation.setEndValue(self.max_shadow_offset)
            self.press_animation.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Анимация при нажатии кнопки."""
        self.pressed = True

        # Запуск анимации "вдавливания" кнопки
        self.press_animation.stop()
        self.press_animation.setStartValue(self._shadow_offset)
        self.press_animation.setEndValue(0)
        self.press_animation.start()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Анимация при отпускании кнопки."""
        self.pressed = False

        # Активируем кнопку если она была нажата правильно
        if self.rect().contains(event.pos()):
            self.setActive(True)
        elif not self._active:
            # Если кнопка не была активирована, восстанавливаем ее состояние
            target_offset = self.max_shadow_offset * 0.5 if self.hover else self.max_shadow_offset
            self.press_animation.stop()
            self.press_animation.setStartValue(self._shadow_offset)
            self.press_animation.setEndValue(target_offset)
            self.press_animation.start()

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