from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTextEdit, QLineEdit, QComboBox, QScrollArea, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QColor, QFont, QTextCursor

from gui.styles import Styles
from gui.components.log_viewer import LogViewer


class LogWidget(QWidget):
    """Виджет для отображения и управления журналом работы приложения."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Автоматическое обновление последней активности
        self.auto_scroll = True

        # Буфер сообщений для поиска
        self.log_messages = []

        # Инициализация UI
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса страницы логов."""
        # Основной лэйаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Заголовок и управление
        header_layout = QVBoxLayout()

        # Заголовок страницы
        title_label = QLabel("Журнал работы")
        title_label.setObjectName("title")
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {Styles.COLORS['text_primary']};
        """)
        header_layout.addWidget(title_label)

        # Подзаголовок
        subtitle_label = QLabel("Детальный журнал всех действий бота")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setStyleSheet(f"""
            font-size: 14px;
            color: {Styles.COLORS['text_secondary']};
        """)
        header_layout.addWidget(subtitle_label)

        layout.addLayout(header_layout)

        # Панель управления логами
        control_panel = QFrame()
        control_panel.setObjectName("section_box")
        control_panel_layout = QVBoxLayout(control_panel)
        control_panel_layout.setContentsMargins(0, 0, 0, 0)
        control_panel_layout.setSpacing(0)

        # Заголовок панели
        panel_header = QLabel("Управление журналом")
        panel_header.setObjectName("header")
        control_panel_layout.addWidget(panel_header)

        # Содержимое панели
        panel_content = QWidget()
        panel_content_layout = QVBoxLayout(panel_content)
        panel_content_layout.setContentsMargins(15, 15, 15, 15)
        panel_content_layout.setSpacing(10)

        # Верхняя строка - фильтры и чекбоксы
        top_controls = QHBoxLayout()
        top_controls.setSpacing(15)

        # Фильтр по уровню логирования
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_label = QLabel("Фильтр:")
        filter_layout.addWidget(filter_label)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["Все", "INFO", "WARNING", "ERROR", "DEBUG"])
        self.level_combo.setFixedWidth(150)
        self.level_combo.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.level_combo)

        top_controls.addLayout(filter_layout)

        # Чекбоксы для уровней логирования
        self.info_checkbox = QCheckBox("INFO")
        self.info_checkbox.setChecked(True)
        self.info_checkbox.stateChanged.connect(self.apply_filter)
        top_controls.addWidget(self.info_checkbox)

        self.warning_checkbox = QCheckBox("WARNING")
        self.warning_checkbox.setChecked(True)
        self.warning_checkbox.stateChanged.connect(self.apply_filter)
        top_controls.addWidget(self.warning_checkbox)

        self.error_checkbox = QCheckBox("ERROR")
        self.error_checkbox.setChecked(True)
        self.error_checkbox.stateChanged.connect(self.apply_filter)
        top_controls.addWidget(self.error_checkbox)

        self.debug_checkbox = QCheckBox("DEBUG")
        self.debug_checkbox.setChecked(False)
        self.debug_checkbox.stateChanged.connect(self.apply_filter)
        top_controls.addWidget(self.debug_checkbox)

        # Чекбокс автопрокрутки
        self.auto_scroll_checkbox = QCheckBox("Автопрокрутка")
        self.auto_scroll_checkbox.setChecked(self.auto_scroll)
        self.auto_scroll_checkbox.stateChanged.connect(self.toggle_auto_scroll)
        top_controls.addWidget(self.auto_scroll_checkbox)

        # Добавляем растягиватель для равномерного распределения
        top_controls.addStretch(1)

        panel_content_layout.addLayout(top_controls)

        # Нижняя строка - поисковая строка
        bottom_controls = QHBoxLayout()
        bottom_controls.setSpacing(10)

        search_label = QLabel("Поиск:")
        bottom_controls.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.textChanged.connect(self.search_logs)
        bottom_controls.addWidget(self.search_input)

        panel_content_layout.addLayout(bottom_controls)

        control_panel_layout.addWidget(panel_content)
        layout.addWidget(control_panel)

        # Журнал активности
        log_frame = QFrame()
        log_frame.setObjectName("section_box")
        log_frame_layout = QVBoxLayout(log_frame)
        log_frame_layout.setContentsMargins(0, 0, 0, 0)
        log_frame_layout.setSpacing(0)

        # Заголовок журнала
        log_header = QLabel("Содержимое журнала")
        log_header.setObjectName("header")
        log_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        log_frame_layout.addWidget(log_header)

        # Компонент просмотра логов с увеличенной высотой для лучшего отображения
        self.log_viewer = LogViewer()
        self.log_viewer.setMinimumHeight(400)
        log_frame_layout.addWidget(self.log_viewer, 1)

        # Кнопки действий
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(15, 10, 15, 15)
        action_layout.addStretch()

        # Кнопка очистки журнала
        clear_log_button = QPushButton("Очистить журнал")
        clear_log_button.clicked.connect(self.clear_log)
        clear_log_button.setFixedWidth(150)
        action_layout.addWidget(clear_log_button)

        # Кнопка экспорта журнала
        export_log_button = QPushButton("Экспорт в файл")
        export_log_button.clicked.connect(self.export_log)
        export_log_button.setFixedWidth(150)
        action_layout.addWidget(export_log_button)

        log_frame_layout.addLayout(action_layout)

        # Добавляем журнал в основной лейаут и указываем, что он должен растягиваться
        layout.addWidget(log_frame, 1)  # Растягиваем журнал на все доступное пространство

    def append_log(self, level, message):
        """
        Добавляет сообщение в журнал.

        Args:
            level (str): Уровень сообщения
            message (str): Текст сообщения
        """
        # Сохраняем сообщение в буфере
        self.log_messages.append((level, message))

        # Проверяем, проходит ли сообщение через фильтр
        if self._passes_filter(level):
            # Если поисковый запрос не пустой, проверяем совпадение
            search_text = self.search_input.text().strip().lower()
            if not search_text or search_text in message.lower():
                self.log_viewer.append_log(level, message)

                # Прокручиваем вниз, если включена автопрокрутка
                if self.auto_scroll:
                    self.log_viewer.moveCursor(QTextCursor.MoveOperation.End)

    def _passes_filter(self, level):
        """Проверяет, проходит ли сообщение через текущий фильтр."""
        level = level.upper()

        # Проверяем чекбоксы для каждого уровня
        if level == "INFO" and not self.info_checkbox.isChecked():
            return False
        if level == "WARNING" and not self.warning_checkbox.isChecked():
            return False
        if level == "ERROR" and not self.error_checkbox.isChecked():
            return False
        if level == "DEBUG" and not self.debug_checkbox.isChecked():
            return False

        # Проверяем фильтр в комбобоксе
        current_filter = self.level_combo.currentText()
        if current_filter != "Все" and level != current_filter:
            return False

        return True

    def clear_log(self):
        """Очищает журнал."""
        self.log_viewer.clear()
        self.log_messages = []

    def export_log(self):
        """Экспортирует журнал в файл."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import datetime

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт журнала",
            f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )

        if filename:
            try:
                # Получаем текст из LogViewer
                text = self.log_viewer.toPlainText()

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)

                QMessageBox.information(
                    self,
                    "Экспорт завершен",
                    f"Журнал успешно экспортирован в файл:\n{filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка экспорта",
                    f"Не удалось экспортировать журнал: {str(e)}"
                )

    def apply_filter(self):
        """Применяет выбранный фильтр к журналу."""
        # Очищаем текущее содержимое лога
        self.log_viewer.clear()

        # Заново отображаем все сообщения, учитывая текущие фильтры и поиск
        search_text = self.search_input.text().strip().lower()

        for level, message in self.log_messages:
            if self._passes_filter(level):
                if not search_text or search_text in message.lower():
                    self.log_viewer.append_log(level, message)

        # Если включена автопрокрутка, прокручиваем в конец
        if self.auto_scroll:
            self.log_viewer.moveCursor(QTextCursor.MoveOperation.End)

    def search_logs(self):
        """Выполняет поиск по журналу."""
        # Применяем тот же метод, что и для фильтрации
        self.apply_filter()

    def toggle_auto_scroll(self, state):
        """Включает/выключает автопрокрутку."""
        self.auto_scroll = bool(state)

        # Прокручиваем в конец, если автопрокрутка включена
        if self.auto_scroll:
            self.log_viewer.moveCursor(QTextCursor.MoveOperation.End)