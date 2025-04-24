from PyQt6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from gui.styles import Styles


class StyledTable(QTableWidget):
    """
    Стилизованная таблица с консистентным дизайном.
    """

    def __init__(self, parent=None):
        """
        Инициализирует стилизованную таблицу.

        Args:
            parent (QWidget, optional): Родительский виджет
        """
        super().__init__(parent)

        # Настройка внешнего вида
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Styles.COLORS['background_medium']};
                color: {Styles.COLORS['text_primary']};
                border: none;
                gridline-color: {Styles.COLORS['border']};
            }}

            QTableWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {Styles.COLORS['border']};
            }}

            QTableWidget::item:selected {{
                background-color: {Styles.COLORS['primary']};
                color: {Styles.COLORS['background_dark']};
            }}

            QHeaderView::section {{
                background-color: {Styles.COLORS['background_light']};
                color: {Styles.COLORS['text_secondary']};
                padding: 5px;
                border: none;
                border-bottom: 1px solid {Styles.COLORS['border']};
                border-right: 1px solid {Styles.COLORS['border']};
            }}

            QHeaderView::section:checked {{
                background-color: {Styles.COLORS['primary']};
                color: {Styles.COLORS['background_dark']};
            }}
        """)

        # Настройка заголовков
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)

        # Отключение редактирования
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Настройка выделения
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Включение чередующихся цветов строк
        self.setAlternatingRowColors(True)

        # Применяем шрифт
        font = QFont(Styles.FONTS["family"], Styles.FONTS["size_normal"])
        self.setFont(font)

    def customize_cell_colors(self):
        """
        Настраивает цвета ячеек на основе их содержимого.
        Вызывайте этот метод после заполнения таблицы.
        """
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    # Если ячейка содержит процент
                    if "%" in item.text():
                        value = float(item.text().strip("%"))
                        if value >= 75:
                            item.setForeground(QColor(Styles.COLORS["secondary"]))
                        elif value >= 50:
                            item.setForeground(QColor(Styles.COLORS["primary"]))
                        elif value >= 25:
                            item.setForeground(QColor(Styles.COLORS["warning"]))
                        else:
                            item.setForeground(QColor(Styles.COLORS["accent"]))

                    # Если ячейка содержит количество ключей
                    elif col == 5 or col == 6:  # Колонки с ключами
                        item.setForeground(QColor(Styles.COLORS["warning"]))

                    # Если ячейка содержит количество серебра (с K на конце)
                    elif col == 7:  # Колонка с серебром
                        item.setForeground(QColor(Styles.COLORS["primary"]))

                    # Если ячейка содержит победы
                    elif col == 2:  # Колонка с победами
                        item.setForeground(QColor(Styles.COLORS["secondary"]))

                    # Если ячейка содержит поражения
                    elif col == 3:  # Колонка с поражениями
                        item.setForeground(QColor(Styles.COLORS["accent"]))

                    # Если ячейка содержит потери связи
                    elif col == 8:  # Колонка с потерями связи (индекс изменен из-за добавления серебра)
                        value = int(item.text())
                        if value > 0:
                            item.setForeground(QColor(Styles.COLORS["accent"]))

    def set_data(self, data, headers=None):
        """
        Устанавливает данные в таблицу.

        Args:
            data (list): Список списков с данными для отображения
            headers (list, optional): Список заголовков колонок
        """
        # Очистка таблицы
        self.clearContents()

        # Установка размеров
        self.setRowCount(len(data))
        if data and len(data) > 0:
            self.setColumnCount(len(data[0]))

        # Установка заголовков
        if headers:
            self.setHorizontalHeaderLabels(headers)

        # Заполнение данными
        for row, row_data in enumerate(data):
            for col, cell_data in enumerate(row_data):
                from PyQt6.QtWidgets import QTableWidgetItem
                self.setItem(row, col, QTableWidgetItem(str(cell_data)))

        # Настройка цветов
        self.customize_cell_colors()