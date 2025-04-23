from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QSpinBox, QMessageBox, QFileDialog, QGridLayout,
    QScrollArea, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

from gui.styles import Styles
from gui.components.toggle_switch import ToggleSwitch
from config import config


class SettingsWidget(QWidget):
    """Страница настроек параметров бота и интерфейса."""

    # Сигнал для обновления цели по ключам
    target_keys_changed = pyqtSignal(int)

    def __init__(self, bot_engine, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine

        # Инициализация UI
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса страницы настроек."""
        # Основной лэйаут
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # Заголовок страницы
        title_layout = QVBoxLayout()

        title_label = QLabel("Настройки")
        title_label.setObjectName("title")
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {Styles.COLORS['text_primary']};
        """)
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("Настройка параметров бота и интерфейса")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setStyleSheet(f"""
            font-size: 14px;
            color: {Styles.COLORS['text_secondary']};
        """)
        title_layout.addWidget(subtitle_label)

        main_layout.addLayout(title_layout)

        # Создаем область прокрутки для всего содержимого
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Контейнер для прокручиваемого содержимого
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)

        # Секция "Подключение ADB"
        adb_frame = self._create_section_frame("Подключение ADB")
        adb_content = QWidget()
        adb_content_layout = QGridLayout(adb_content)
        adb_content_layout.setContentsMargins(15, 15, 15, 15)
        adb_content_layout.setVerticalSpacing(15)  # Увеличиваем расстояние между строками

        # Статус ADB
        status_label = QLabel("Статус ADB:")
        status_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        adb_content_layout.addWidget(status_label, 0, 0)

        self.adb_status_layout = QHBoxLayout()

        self.adb_status_indicator = QLabel("●")
        self.adb_status_indicator.setStyleSheet(f"color: {Styles.COLORS['text_secondary']}; font-size: 18px;")
        self.adb_status_layout.addWidget(self.adb_status_indicator)

        self.adb_status_label = QLabel("Не проверено")
        self.adb_status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.adb_status_layout.addWidget(self.adb_status_label)
        self.adb_status_layout.addStretch()

        adb_content_layout.addLayout(self.adb_status_layout, 0, 1)

        # Путь к ADB
        path_label = QLabel("Путь к ADB:")
        path_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        adb_content_layout.addWidget(path_label, 1, 0)

        self.adb_path_input = QLineEdit()
        self.adb_path_input.setText(config.get("adb", "path", "adb.exe" if __import__('os').name == "nt" else "adb"))
        self.adb_path_input.setReadOnly(True)
        self.adb_path_input.setMinimumHeight(30)  # Установка минимальной высоты
        adb_content_layout.addWidget(self.adb_path_input, 1, 1)

        # Кнопка проверки соединения
        test_button = QPushButton("Проверить подключение")
        test_button.clicked.connect(self.test_adb_connection)
        test_button.setFixedWidth(200)
        test_button.setMinimumHeight(30)  # Установка минимальной высоты
        adb_content_layout.addWidget(test_button, 2, 1, Qt.AlignmentFlag.AlignRight)

        # Информационный текст
        info_text = QLabel(
            "ADB включен в дистрибутив бота и должен работать автоматически "
            "при использовании эмулятора LDPlayer. Убедитесь, что эмулятор запущен "
            "перед запуском бота."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        adb_content_layout.addWidget(info_text, 3, 0, 1, 2)

        adb_frame.layout().addWidget(adb_content)
        scroll_layout.addWidget(adb_frame)

        # Секция "Настройки бота"
        bot_frame = self._create_section_frame("Настройки бота")
        bot_content = QWidget()
        bot_content_layout = QGridLayout(bot_content)
        bot_content_layout.setContentsMargins(15, 15, 15, 15)
        bot_content_layout.setVerticalSpacing(15)  # Увеличиваем расстояние между строками

        # Время ожидания боя
        battle_timeout_label = QLabel("Время ожидания боя (секунды)")
        battle_timeout_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bot_content_layout.addWidget(battle_timeout_label, 0, 0)

        self.battle_timeout_input = self._create_spinbox(
            30, 300, config.get("bot", "battle_timeout", 120)
        )
        bot_content_layout.addWidget(self.battle_timeout_input, 0, 1)

        # Подсказка для времени ожидания
        timeout_hint = QLabel("Рекомендуемое значение: 90-180 секунд")
        timeout_hint.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        bot_content_layout.addWidget(timeout_hint, 1, 1)

        # Макс. попыток обновления
        refresh_label = QLabel("Макс. попыток обновления")
        refresh_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bot_content_layout.addWidget(refresh_label, 2, 0)

        self.max_refresh_input = self._create_spinbox(
            1, 10, config.get("bot", "max_refresh_attempts", 3)
        )
        bot_content_layout.addWidget(self.max_refresh_input, 2, 1)

        # Интервал проверки
        interval_label = QLabel("Интервал проверки (секунды)")
        interval_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bot_content_layout.addWidget(interval_label, 3, 0)

        self.check_interval_input = self._create_spinbox(
            1, 10, config.get("bot", "check_interval", 3)
        )
        bot_content_layout.addWidget(self.check_interval_input, 3, 1)

        # Цель по ключам
        keys_label = QLabel("Цель по сбору ключей")
        keys_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bot_content_layout.addWidget(keys_label, 4, 0)

        self.target_keys_input = self._create_spinbox(
            100, 10000, config.get("bot", "target_keys", 1000), 100
        )
        bot_content_layout.addWidget(self.target_keys_input, 4, 1)

        # Режим отладки
        debug_label = QLabel("Включить режим отладки")
        debug_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bot_content_layout.addWidget(debug_label, 5, 0)

        self.debug_mode_toggle = ToggleSwitch()
        self.debug_mode_toggle.setChecked(config.get("bot", "debug_mode", False))
        debug_layout = QHBoxLayout()
        debug_layout.addWidget(self.debug_mode_toggle)
        debug_layout.addStretch()
        bot_content_layout.addLayout(debug_layout, 5, 1)

        # Кнопка сохранения настроек
        save_button = QPushButton("Сохранить настройки")
        save_button.setObjectName("success")
        save_button.clicked.connect(self.save_settings)
        save_button.setFixedWidth(200)
        save_button.setMinimumHeight(30)  # Установка минимальной высоты
        bot_content_layout.addWidget(save_button, 6, 0, 1, 2, Qt.AlignmentFlag.AlignRight)

        bot_frame.layout().addWidget(bot_content)
        scroll_layout.addWidget(bot_frame)

        # Секция "Настройки интерфейса"
        ui_frame = self._create_section_frame("Настройки интерфейса")
        ui_content = QWidget()
        ui_content_layout = QGridLayout(ui_content)
        ui_content_layout.setContentsMargins(15, 15, 15, 15)
        ui_content_layout.setVerticalSpacing(15)  # Увеличиваем расстояние между строками

        # Уровень логирования
        log_level_label = QLabel("Уровень логирования")
        log_level_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ui_content_layout.addWidget(log_level_label, 0, 0)

        # Создаем кастомный класс выпадающего списка, который перенаправляет события колеса мыши
        from PyQt6.QtWidgets import QComboBox
        from PyQt6.QtGui import QWheelEvent

        class ScrollFriendlyComboBox(QComboBox):
            def wheelEvent(self, event):
                # Просто игнорируем событие колеса мыши
                event.ignore()
                # Событие будет автоматически передано дальше по иерархии виджетов

        self.log_level_combo = ScrollFriendlyComboBox()
        self.log_level_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(config.get("ui", "log_level", "INFO"))
        self.log_level_combo.setMinimumHeight(30)  # Установка минимальной высоты
        ui_content_layout.addWidget(self.log_level_combo, 0, 1)

        # Тема
        theme_label = QLabel("Тема")
        theme_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ui_content_layout.addWidget(theme_label, 1, 0)

        self.theme_combo = ScrollFriendlyComboBox()  # Используем тот же класс что и выше
        self.theme_combo.addItems(["Тёмная"])
        self.theme_combo.setCurrentIndex(0)
        self.theme_combo.setMinimumHeight(30)  # Установка минимальной высоты
        ui_content_layout.addWidget(self.theme_combo, 1, 1)

        ui_frame.layout().addWidget(ui_content)
        scroll_layout.addWidget(ui_frame)

        # Завершаем настройку скролла
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Инициализация состояния ADB
        self.check_adb_status()

    def _create_section_frame(self, title):
        """Создает рамку секции с заголовком."""
        frame = QFrame()
        frame.setObjectName("section_box")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Заголовок секции
        header = QLabel(title)
        header.setObjectName("header")
        layout.addWidget(header)

        return frame

    def _create_spinbox(self, min_value, max_value, default_value, step=1):
        """Создает настроенный спинбокс с указанными параметрами."""
        from PyQt6.QtGui import QWheelEvent
        from PyQt6.QtCore import QEvent

        # Создаем кастомный класс спинбокса, который предотвращает обработку события колеса мыши
        class ScrollFriendlySpinBox(QSpinBox):
            def wheelEvent(self, event):
                # Игнорируем событие колеса мыши, чтобы его обработал родительский скролл
                event.ignore()
                # Ничего больше не делаем, событие будет обработано вышестоящими виджетами

        spinbox = ScrollFriendlySpinBox()
        spinbox.setRange(min_value, max_value)
        spinbox.setValue(default_value)
        spinbox.setSingleStep(step)
        spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)  # Убираем кнопки
        spinbox.setMinimumHeight(30)  # Установка минимальной высоты
        spinbox.setMinimumWidth(100)  # Установка минимальной ширины

        # Установка стиля для улучшения видимости
        spinbox.setStyleSheet(f"""
            QSpinBox {{
                padding: 5px;
                background-color: {Styles.COLORS['background_input']};
                color: {Styles.COLORS['text_primary']};
                border: 1px solid {Styles.COLORS['border']};
                border-radius: 4px;
            }}
        """)

        return spinbox

    def test_adb_connection(self):
        """Проверка соединения с ADB."""
        if self.bot_engine.adb.check_connection():
            self.update_adb_status(True)
            QMessageBox.information(
                self,
                "Подключение ADB",
                "Успешное подключение к устройству ADB!"
            )
        else:
            self.update_adb_status(False)
            QMessageBox.warning(
                self,
                "Ошибка подключения ADB",
                "Не удалось подключиться к устройству ADB. Пожалуйста, проверьте настройки эмулятора."
            )

    def update_adb_status(self, connected):
        """
        Обновляет индикатор статуса ADB.

        Args:
            connected (bool): True если соединение установлено, False иначе
        """
        if connected:
            self.adb_status_indicator.setStyleSheet(f"color: {Styles.COLORS['secondary']}; font-size: 18px;")
            self.adb_status_label.setText("Подключено")
            self.adb_status_label.setStyleSheet(f"color: {Styles.COLORS['secondary']};")
        else:
            self.adb_status_indicator.setStyleSheet(f"color: {Styles.COLORS['accent']}; font-size: 18px;")
            self.adb_status_label.setText("Не подключено")
            self.adb_status_label.setStyleSheet(f"color: {Styles.COLORS['accent']};")

    def check_adb_status(self):
        """Проверяет текущий статус ADB при инициализации."""
        try:
            connected = self.bot_engine.adb.check_connection()
            self.update_adb_status(connected)
        except Exception as e:
            print(f"Ошибка при проверке статуса ADB: {e}")
            self.update_adb_status(False)

    def save_settings(self):
        """Сохранение настроек в конфигурацию."""
        # Получаем значения из полей
        battle_timeout = self.battle_timeout_input.value()
        max_refresh = self.max_refresh_input.value()
        check_interval = self.check_interval_input.value()
        debug_mode = self.debug_mode_toggle.isChecked()
        log_level = self.log_level_combo.currentText()
        target_keys = self.target_keys_input.value()

        # Сохраняем в конфигурацию
        config.set("bot", "battle_timeout", battle_timeout)
        config.set("bot", "max_refresh_attempts", max_refresh)
        config.set("bot", "check_interval", check_interval)
        config.set("bot", "debug_mode", debug_mode)
        config.set("bot", "target_keys", target_keys)
        config.set("ui", "log_level", log_level)

        # Сохраняем конфигурационный файл
        if config.save():
            QMessageBox.information(
                self,
                "Настройки сохранены",
                "Настройки успешно сохранены."
            )

            # Обновляем настройки в движке бота
            self.bot_engine.update_settings(battle_timeout, max_refresh)

            # Отправляем сигнал об изменении цели по ключам
            self.target_keys_changed.emit(target_keys)

            # Обновляем уровень логирования, если это возможно
            try:
                import logging
                py_logger = logging.getLogger("BotLogger")
                log_level_value = getattr(logging, log_level)

                for handler in py_logger.handlers:
                    handler.setLevel(log_level_value)

                py_logger.setLevel(log_level_value)
                py_logger.info(f"Уровень логирования изменен на {log_level}")
            except Exception as e:
                print(f"Ошибка при обновлении уровня логирования: {e}")
        else:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Ошибка при сохранении настроек."
            )