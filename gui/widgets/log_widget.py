from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTextEdit, QLineEdit, QComboBox, QScrollArea, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QColor, QFont

from gui.styles import Styles
from gui.components.log_viewer import LogViewer


class LogWidget(QWidget):
    """Виджет для отображения и управления журналом работы приложения."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Автоматическое обновление последней активности
        self.auto_scroll = True

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
        panel_content_layout = QHBoxLayout(panel_content)
        panel_content_layout.setContentsMargins(15, 15, 15, 15)
        panel_content_layout.setSpacing(15)

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

        # Чекбоксы для фильтрации
        self.info_checkbox = QCheckBox("INFO")
        self.info_checkbox.setChecked(True)
        self.info_checkbox.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.info_checkbox)

        self.warning_checkbox = QCheckBox("WARNING")
        self.warning_checkbox.setChecked(True)
        self.warning_checkbox.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.warning_checkbox)

        self.error_checkbox = QCheckBox("ERROR")
        self.error_checkbox.setChecked(True)
        self.error_checkbox.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.error_checkbox)

        self.debug_checkbox = QCheckBox("DEBUG")
        self.debug_checkbox.setChecked(True)
        self.debug_checkbox.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.debug_checkbox)

        panel_content_layout.addLayout(filter_layout)

        # Автопрокрутка
        self.auto_scroll_checkbox = QCheckBox("Автопрокрутка")
        self.auto_scroll_checkbox.setChecked(self.auto_scroll)
        self.auto_scroll_checkbox.stateChanged.connect(self.toggle_auto_scroll)
        panel_content_layout.addWidget(self.auto_scroll_checkbox)

        # Поиск
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        search_label = QLabel("Поиск:")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.textChanged.connect(self.search_logs)
        search_layout.addWidget(self.search_input)

        panel_content_layout.addLayout(search_layout)

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

        # Компонент просмотра логов
        self.log_viewer = LogViewer()
        self.log_viewer.setMinimumHeight(500)  # Увеличенная высота для удобства
        log_frame_layout.addWidget(self.log_viewer, 1)

        # Кнопки действий
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(15, 10, 15, 15)
        action_layout.addStretch()

        # Кнопка очистки журнала
        clear_log_button = QPushButton("Очистить журнал")
        clear_log_button.clicked.connect(self.clear_log)
        action_layout.addWidget(clear_log_button)

        # Кнопка экспорта журнала (в перспективе)
        export_log_button = QPushButton("Экспорт в файл")
        export_log_button.clicked.connect(self.export_log)
        action_layout.addWidget(export_log_button)

        log_frame_layout.addLayout(action_layout)

        layout.addWidget(log_frame, 1)  # Растягиваем журнал на все доступное пространство

    def append_log(self, level, message):
        """
        Добавляет сообщение в журнал.

        Args:
            level (str): Уровень сообщения
            message (str): Текст сообщения
        """
        # Проверяем, проходит ли сообщение через фильтр
        current_filter = self.level_combo.currentText()

        if current_filter != "Все" and level.upper() != current_filter:
            return

        # Проверяем чекбоксы
        if level.upper() == "INFO" and not self.info_checkbox.isChecked():
            return
        if level.upper() == "WARNING" and not self.warning_checkbox.isChecked():
            return
        if level.upper() == "ERROR" and not self.error_checkbox.isChecked():
            return
        if level.upper() == "DEBUG" and not self.debug_checkbox.isChecked():
            return

        # Добавляем сообщение
        self.log_viewer.append_log(level, message)

        # Проверяем, есть ли текст для поиска
        search_text = self.search_input.text().strip()
        if search_text and search_text.lower() not in message.lower():
            # Скрываем сообщение, которое не содержит искомый текст
            # Примечание: это упрощенная реализация, для полной реализации
            # потребуется модификация LogViewer для поддержки фильтрации
            pass

    def clear_log(self):
        """Очищает журнал."""
        self.log_viewer.clear()

    def export_log(self):
        """Экспортирует журнал в файл."""
        # В будущем здесь будет код экспорта журнала
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
        # Здесь должен быть код для фильтрации отображаемых логов
        # В текущей реализации мы просто перезагружаем логи
        # При реальной реализации нужно модифицировать LogViewer
        # для поддержки фильтрации уже отображенных сообщений

        # Для теста пока просто выводим сообщение
        level = self.level_combo.currentText()
        self.log_viewer.append_log("info", f"Фильтр установлен: {level}")

    def search_logs(self):
        """Выполняет поиск по журналу."""
        # Здесь должен быть код для поиска в журнале
        # Для полной реализации нужно модифицировать LogViewer
        search_text = self.search_input.text().strip()
        if search_text:
            self.log_viewer.append_log("info", f"Поиск: {search_text}")

    def toggle_auto_scroll(self, state):
        """Включает/выключает автопрокрутку."""
        self.auto_scroll = bool(state)