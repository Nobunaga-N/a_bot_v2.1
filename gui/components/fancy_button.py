from PyQt6.QtWidgets import QPushButton, QButtonGroup
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QFont, QPainterPath


class FancyButton(QPushButton):
    """
    Стилизованная анимированная кнопка с эффектом тактильности.

    Особенности:
    - Постоянная плавная градиентная анимация
    - Эффект вдавливания при нажатии
    - Овальная форма с белой обводкой
    - Смещение при наведении/нажатии
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
        self._active = False  # Состояние активации
        self.hover = False
        self.pressed = False

        # Параметры смещения - начинаем с 0 (кнопка в левом верхнем углу)
        self._offset = QPoint(0, 0)  # Начальное смещение кнопки (нет смещения)
        self._max_offset = QPoint(4, 4)  # Максимальное смещение (при нажатии)

        # Параметры анимации точек
        self.dots_position = 0  # Позиция анимированных точек

        # Настройка шрифта и размеров
        font = self.font()
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)

        # Определение цветов для разных типов кнопок
        if success:
            # Зеленая кнопка для "Start"
            self.bg_color = QColor("#facc15")  # Желтый
            self.shadow_color = QColor("#292524")  # Темно-серый
            self.glow_color = QColor(250, 204, 21, 40)  # Полупрозрачный желтый
        else:
            # Красная кнопка для "Stop"
            self.bg_color = QColor("#FF6B6C")  # Красный
            self.highlight_color = QColor("#FF8E8F")  # Светло-красный
            self.shadow_color = QColor("#292524")  # Темно-серый
            self.glow_color = QColor(255, 107, 108, 40)  # Полупрозрачный красный

        # Общие цвета
        self.border_color = QColor("#292524")  # Темно-серый
        self.outline_color = QColor("#fafaf9")  # Почти белый
        self.text_color = QColor("#292524")  # Темно-серый

        # Установка фиксированного размера
        self.setFixedHeight(40)
        self.setMinimumWidth(120)

        # Курсор в виде указательного пальца при наведении
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Создание анимации для эффекта вдавливания
        self.press_animation = QPropertyAnimation(self, b"offset")
        self.press_animation.setDuration(150)
        self.press_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Таймер для постоянной анимации
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(50)  # Обновление каждые 50мс для плавной анимации

    # Свойство для анимации смещения кнопки
    def get_offset(self):
        return self._offset

    def set_offset(self, offset):
        self._offset = offset
        self.update()

    offset = pyqtProperty(QPoint, get_offset, set_offset)

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
            if hasattr(self, 'group') and self.group:
                for button in self.group.buttons:
                    if button != self and button.isActive():
                        button.setActive(False)

            # Анимация "вдавливания" - полное смещение
            self.press_animation.setStartValue(self._offset)
            self.press_animation.setEndValue(self._max_offset)
            self.press_animation.start()
        else:
            # Анимация "выхода" из вдавленного состояния - возврат в начальное положение
            self.press_animation.setStartValue(self._offset)
            self.press_animation.setEndValue(QPoint(0, 0))
            self.press_animation.start()

        self.update()

    def update_animation(self):
        """Обновляет состояние анимации точек."""
        # Продвигаем позицию точек для создания эффекта движения
        self.dots_position = (self.dots_position + 1) % 8
        self.update()  # Перерисовка кнопки

    def paintEvent(self, event):
        """Кастомная отрисовка кнопки со всеми эффектами."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        width = rect.width()
        height = rect.height()

        # Получаем текущее смещение
        offset_x = self._offset.x()
        offset_y = self._offset.y()

        # Создаем путь для скругленной прямоугольной формы (овал)
        button_path = QPainterPath()
        button_path.addRoundedRect(0, 0, width, height, height / 2, height / 2)

        # Рисуем внешнюю тень (черная)
        # Тень с фиксированным размером внизу-справа, кнопка смещается внутри неё
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(
            0, 0, width, height,
            height / 2, height / 2
        )

        painter.setPen(QPen(self.shadow_color, 2))
        painter.setBrush(self.shadow_color)
        painter.drawPath(shadow_path)

        # Рисуем белую обводку поверх черной тени
        stroke_path = QPainterPath()
        stroke_path.addRoundedRect(
            2, 2, width - 4, height - 4,
                  (height - 4) / 2, (height - 4) / 2
        )

        painter.setPen(QPen(self.outline_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(stroke_path)

        # Рисуем фон кнопки с учетом смещения
        # Смещение вправо-вниз от позиции (0,0) - заполняет пространство справа и снизу
        button_rect = QRect(
            int(0 + offset_x), int(0 + offset_y),
            int(width - 8 + (self._max_offset.x() - offset_x)),
            int(height - 8 + (self._max_offset.y() - offset_y))
        )
        button_radius = (height - 8) / 2

        # Создаем градиент для фона
        gradient = QLinearGradient(
            button_rect.x(), button_rect.y(),
            button_rect.x() + button_rect.width(), button_rect.y() + button_rect.height()
        )
        if self.success:
            gradient.setColorAt(0, QColor("#facc15"))  # Желтый
            gradient.setColorAt(1, QColor("#eab308"))  # Немного темнее
        else:
            gradient.setColorAt(0, QColor("#FF6B6C"))  # Красный
            gradient.setColorAt(1, QColor("#e53e3f"))  # Темнее

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(button_rect, button_radius, button_radius)

        # Рисуем анимированные точки
        if not self._active:  # Показываем точки только когда кнопка не активна
            painter.save()
            painter.setClipRect(button_rect)

            dot_size = 3
            dot_spacing = 8
            dot_offset = self.dots_position

            for x in range(-dot_offset, button_rect.width() + dot_spacing, dot_spacing):
                for y in range(dot_offset % dot_spacing, button_rect.height() + dot_spacing, dot_spacing):
                    # Проверяем, находится ли точка внутри кнопки
                    point_x = int(button_rect.x() + x)
                    point_y = int(button_rect.y() + y)
                    if (button_rect.left() <= point_x <= button_rect.right() and
                            button_rect.top() <= point_y <= button_rect.bottom()):
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(QColor(255, 255, 255, 60))  # Полупрозрачный белый
                        painter.drawEllipse(point_x, point_y, dot_size, dot_size)

            painter.restore()

        # Добавляем эффект блика вверху
        highlight_rect = QRect(
            int(button_rect.x()), int(button_rect.y()),
            int(button_rect.width()), int(button_rect.height() // 3)
        )
        highlight_gradient = QLinearGradient(
            highlight_rect.x(), highlight_rect.y(),
            highlight_rect.x(), highlight_rect.y() + highlight_rect.height()
        )
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 80))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(highlight_gradient)

        highlight_path = QPainterPath()
        highlight_path.addRoundedRect(
            highlight_rect.x(), highlight_rect.y(),
            highlight_rect.width(), highlight_rect.height(),
            button_radius, button_radius
        )

        # Обрезаем путь блика, чтобы он был только в верхней части
        painter.setClipRect(highlight_rect)
        painter.drawPath(highlight_path)
        painter.setClipping(False)

        # Отрисовка текста
        text_rect = button_rect

        # Тень текста
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
            self.press_animation.setStartValue(self._offset)
            # Наполовину смещаем при наведении (вправо-вниз)
            self.press_animation.setEndValue(QPoint(2, 2))
            self.press_animation.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Анимация при уходе курсора."""
        self.hover = False
        self.pressed = False

        # Запускаем анимацию только если кнопка не активна
        if not self._active:
            self.press_animation.stop()
            self.press_animation.setStartValue(self._offset)
            # Возвращаем в исходную позицию
            self.press_animation.setEndValue(QPoint(0, 0))
            self.press_animation.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Анимация при нажатии кнопки."""
        self.pressed = True

        # Запуск анимации "вдавливания" кнопки (полностью вправо-вниз)
        self.press_animation.stop()
        self.press_animation.setStartValue(self._offset)
        self.press_animation.setEndValue(self._max_offset)
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
            target_offset = QPoint(2, 2) if self.hover else QPoint(0, 0)
            self.press_animation.stop()
            self.press_animation.setStartValue(self._offset)
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