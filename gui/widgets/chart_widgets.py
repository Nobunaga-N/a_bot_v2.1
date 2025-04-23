from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, QLineF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPainterPath

from gui.styles import Styles


class BaseChartWidget(QWidget):
    """Базовый класс для графиков."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setMinimumWidth(300)

        # Данные графика
        self.categories = []
        self.values = []

        # Настройки отображения - увеличиваем левый отступ для значений оси Y
        self.margin_left = 60  # Увеличенный отступ слева для значений
        self.margin_bottom = 40  # Отступ снизу для категорий
        self.margin_top = 20  # Отступ сверху
        self.margin_right = 20  # Отступ справа
        self.chart_margin = 10  # Дополнительный отступ графика

        # Цвета
        self.background_color = QColor(Styles.COLORS["background_medium"])
        self.grid_color = QColor(Styles.COLORS["border"])
        self.text_color = QColor(Styles.COLORS["text_secondary"])

        # Настройки сетки
        self.show_grid = True
        self.h_grid_count = 5

        # Пустой график
        self.is_empty = True
        self.empty_text = "Нет данных для отображения"

    def set_data(self, categories, values):
        """
        Устанавливает данные для графика.

        Args:
            categories: Список категорий (метки по оси X)
            values: Список значений или список списков значений
        """
        self.categories = categories
        self.values = values
        self.is_empty = len(categories) == 0 or (
                isinstance(values, list) and len(values) == 0
        )
        self.update()

    def paintEvent(self, event):
        """Событие отрисовки графика."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Очищаем фон
        painter.fillRect(self.rect(), self.background_color)

        # Если данных нет, показываем сообщение
        if self.is_empty:
            self._draw_empty_state(painter)
            return

        # Рисуем график
        self._draw_chart(painter)

    def _draw_empty_state(self, painter):
        """Отрисовка пустого состояния."""
        painter.setPen(QColor(Styles.COLORS["text_secondary"]))
        painter.setFont(QFont(Styles.FONTS["family"], Styles.FONTS["size_normal"]))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            self.empty_text
        )

    def _draw_chart(self, painter):
        """Отрисовка графика. Переопределяется в дочерних классах."""
        pass

    def _draw_grid(self, painter, chart_rect, max_value):
        """
        Отрисовка сетки графика.

        Args:
            painter: QPainter для отрисовки
            chart_rect: Прямоугольник области графика
            max_value: Максимальное значение на графике
        """
        if not self.show_grid:
            return

        painter.setPen(QPen(self.grid_color, 1, Qt.PenStyle.DotLine))

        # Горизонтальные линии
        step = max_value / self.h_grid_count if max_value > 0 else 0
        for i in range(self.h_grid_count + 1):  # Добавляем +1 чтобы нарисовать линию у основания
            y = chart_rect.bottom() - (i * chart_rect.height() / self.h_grid_count)

            # Используем QLineF вместо отдельных координат
            line = QLineF(
                chart_rect.left(), y,
                chart_rect.right(), y
            )
            painter.drawLine(line)

            # Подписи значений
            if step > 0:
                value = i * step
                if value.is_integer():
                    value_text = str(int(value))
                else:
                    value_text = f"{value:.1f}"

                painter.setPen(self.text_color)

                # Увеличиваем ширину области для текста значений
                text_rect = QRectF(
                    chart_rect.left() - self.margin_left + 5,  # Немного отступаем от края
                    y - 10,  # Центрируем текст по вертикали относительно линии
                    self.margin_left - 10,  # Увеличиваем ширину области для текста
                    20  # Высота области для текста
                )

                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    value_text
                )

            # Возвращаем перо для следующих линий
            painter.setPen(QPen(self.grid_color, 1, Qt.PenStyle.DotLine))

        # Вертикальные линии (по категориям)
        if len(self.categories) > 1:
            category_width = chart_rect.width() / (len(self.categories) - 1) if len(
                self.categories) > 1 else chart_rect.width()
            for i in range(len(self.categories)):
                x = chart_rect.left() + i * category_width

                # Подписи категорий
                painter.setPen(self.text_color)

                # Центрируем подписи категорий
                text_rect = QRectF(
                    x - 40,  # Центрируем текст по горизонтали
                    chart_rect.bottom() + 5,  # Немного отступаем от оси X
                    80,  # Ширина области для текста
                    self.margin_bottom - 10  # Высота области для текста
                )

                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                    self.categories[i]
                )


class LineChartWidget(BaseChartWidget):
    """Виджет для отображения линейного графика."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Массив цветов для разных линий
        self.line_colors = [
            QColor(Styles.COLORS["secondary"]),
            QColor(Styles.COLORS["accent"]),
            QColor(Styles.COLORS["primary"]),
            QColor(Styles.COLORS["warning"])
        ]

        # Подписи для легенды
        self.labels = []

    def set_data(self, categories, values, labels=None):
        """
        Устанавливает данные для линейного графика.

        Args:
            categories: Список категорий (метки по оси X)
            values: Список списков значений для разных линий
            labels: Список подписей для линий
        """
        super().set_data(categories, values)

        if labels:
            self.labels = labels
        elif isinstance(values, list) and isinstance(values[0], list):
            self.labels = [f"Линия {i + 1}" for i in range(len(values))]

    def _draw_chart(self, painter):
        """Отрисовка линейного графика."""
        width = self.width()
        height = self.height()

        # Определяем область для рисования графика с учетом новых отступов
        chart_rect = QRectF(
            self.margin_left + self.chart_margin,
            self.margin_top,
            width - self.margin_left - self.margin_right - 2 * self.chart_margin,
            height - self.margin_top - self.margin_bottom - self.chart_margin
        )

        # Находим максимальное значение для масштабирования
        max_value = 0
        if isinstance(self.values[0], list):
            for series in self.values:
                current_max = max(series) if series else 0
                max_value = max(max_value, current_max)
        else:
            max_value = max(self.values) if self.values else 0

        # Если максимальное значение равно 0, устанавливаем его на 1 для избежания деления на ноль
        if max_value == 0:
            max_value = 1

        # Увеличиваем максимальное значение на 10% для отступа сверху
        max_value *= 1.1

        # Рисуем сетку
        self._draw_grid(painter, chart_rect, max_value)

        # Рисуем оси
        painter.setPen(QPen(self.grid_color, 1))

        # Используем QLineF вместо отдельных координат
        x_axis = QLineF(
            chart_rect.left(), chart_rect.bottom(),
            chart_rect.right(), chart_rect.bottom()
        )
        painter.drawLine(x_axis)

        y_axis = QLineF(
            chart_rect.left(), chart_rect.bottom(),
            chart_rect.left(), chart_rect.top()
        )
        painter.drawLine(y_axis)

        # Рисуем линии графика
        if isinstance(self.values[0], list):
            # Множество линий
            for i, series in enumerate(self.values):
                self._draw_line_series(painter, chart_rect, series, max_value, i)
        else:
            # Одна линия
            self._draw_line_series(painter, chart_rect, self.values, max_value, 0)

    def _draw_line_series(self, painter, chart_rect, series, max_value, line_index):
        """
        Отрисовка одной линии графика.

        Args:
            painter: QPainter для отрисовки
            chart_rect: Прямоугольник области графика
            series: Список значений для линии
            max_value: Максимальное значение для масштабирования
            line_index: Индекс линии для выбора цвета
        """
        if not series or len(series) != len(self.categories):
            return

        # Выбираем цвет из массива цветов
        color_index = line_index % len(self.line_colors)
        line_color = self.line_colors[color_index]

        # Настраиваем перо
        painter.setPen(QPen(line_color, 2))

        # Создаем путь для линии
        path = QPainterPath()

        # Ширина одного сегмента
        segment_width = chart_rect.width() / (len(series) - 1) if len(series) > 1 else 0

        # Начальная точка
        start_x = chart_rect.left()
        start_y = chart_rect.bottom() - (series[0] / max_value) * chart_rect.height()
        path.moveTo(start_x, start_y)

        # Добавляем точки в путь
        for i in range(1, len(series)):
            x = chart_rect.left() + i * segment_width
            y = chart_rect.bottom() - (series[i] / max_value) * chart_rect.height()
            path.lineTo(x, y)

        # Рисуем линию
        painter.drawPath(path)

        # Рисуем точки на графике
        for i in range(len(series)):
            x = chart_rect.left() + i * segment_width
            y = chart_rect.bottom() - (series[i] / max_value) * chart_rect.height()

            # Обводка точки
            painter.setPen(QPen(self.background_color, 1))
            painter.setBrush(QBrush(line_color))
            painter.drawEllipse(QPointF(x, y), 4, 4)


class BarChartWidget(BaseChartWidget):
    """Виджет для отображения столбчатого графика."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Цвет столбцов
        self.bar_color = QColor(Styles.COLORS["warning"])

        # Ширина столбца (в процентах от доступной ширины)
        self.bar_width_percent = 0.6

    def set_data(self, categories, values, color=None):
        """
        Устанавливает данные для столбчатого графика.

        Args:
            categories: Список категорий (метки по оси X)
            values: Список значений для столбцов
            color: Цвет столбцов (опционально)
        """
        super().set_data(categories, values)

        if color:
            self.bar_color = QColor(color)

    def _draw_chart(self, painter):
        """Отрисовка столбчатого графика."""
        width = self.width()
        height = self.height()

        # Определяем область для рисования графика с учетом новых отступов
        chart_rect = QRectF(
            self.margin_left + self.chart_margin,
            self.margin_top,
            width - self.margin_left - self.margin_right - 2 * self.chart_margin,
            height - self.margin_top - self.margin_bottom - self.chart_margin
        )

        # Находим максимальное значение для масштабирования
        max_value = max(self.values) if self.values else 0

        # Если максимальное значение равно 0, устанавливаем его на 1 для избежания деления на ноль
        if max_value == 0:
            max_value = 1

        # Увеличиваем максимальное значение на 10% для отступа сверху
        max_value *= 1.1

        # Рисуем сетку
        self._draw_grid(painter, chart_rect, max_value)

        # Рисуем оси
        painter.setPen(QPen(self.grid_color, 1))

        # Используем QLineF вместо отдельных координат
        x_axis = QLineF(
            chart_rect.left(), chart_rect.bottom(),
            chart_rect.right(), chart_rect.bottom()
        )
        painter.drawLine(x_axis)

        y_axis = QLineF(
            chart_rect.left(), chart_rect.bottom(),
            chart_rect.left(), chart_rect.top()
        )
        painter.drawLine(y_axis)

        # Рисуем столбцы
        if not self.values or len(self.values) != len(self.categories):
            return

        # Ширина одного сегмента
        segment_width = chart_rect.width() / len(self.values)

        # Ширина столбца
        bar_width = segment_width * self.bar_width_percent

        for i in range(len(self.values)):
            # Значение столбца
            value = self.values[i]

            # Координаты столбца
            bar_height = (value / max_value) * chart_rect.height()
            bar_left = chart_rect.left() + i * segment_width + (segment_width - bar_width) / 2
            bar_top = chart_rect.bottom() - bar_height

            # Рисуем столбец
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.bar_color))
            painter.drawRect(QRectF(bar_left, bar_top, bar_width, bar_height))

            # Рисуем значение над столбцом, только если столбец достаточно высокий
            if bar_height > 15:
                painter.setPen(self.text_color)
                painter.setFont(QFont(Styles.FONTS["family"], Styles.FONTS["size_small"]))

                # Форматируем значение
                if value.is_integer():
                    value_text = str(int(value))
                else:
                    value_text = f"{value:.1f}"

                # Рисуем текст над столбцом
                text_rect = QRectF(
                    bar_left,
                    bar_top - 20,
                    bar_width,
                    20
                )

                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                    value_text
                )


class CombinedChartWidget(QWidget):
    """
    Виджет, объединяющий график и легенду.
    """

    def __init__(self, chart_widget, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(250)

        # Основной лэйаут
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # Виджет графика
        self.chart_widget = chart_widget
        self.layout.addWidget(self.chart_widget)

        # Виджет легенды (будет добавлен при необходимости)
        self.legend_widget = None

    def set_legend(self, items):
        """
        Устанавливает легенду для графика.

        Args:
            items: Список кортежей (текст, цвет)
        """
        # Удаляем предыдущую легенду, если она есть
        if self.legend_widget:
            self.layout.removeWidget(self.legend_widget)
            self.legend_widget.deleteLater()
            self.legend_widget = None

        if not items:
            return

        # Создаем новый виджет для легенды
        self.legend_widget = QWidget()
        legend_layout = QHBoxLayout(self.legend_widget)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(15)

        # Добавляем элементы легенды
        for text, color in items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(5)

            # Цветной индикатор
            color_indicator = QLabel("●")
            color_indicator.setStyleSheet(f"color: {color}; font-size: 16px;")
            item_layout.addWidget(color_indicator)

            # Текст
            text_label = QLabel(text)
            text_label.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
            item_layout.addWidget(text_label)

            # Добавляем элемент в легенду
            legend_layout.addLayout(item_layout)

        # Добавляем растягивающийся элемент в конец
        legend_layout.addStretch()

        # Добавляем легенду в лэйаут
        self.layout.addWidget(self.legend_widget)