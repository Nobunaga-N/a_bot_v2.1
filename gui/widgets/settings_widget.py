from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QSpinBox, QMessageBox, QFileDialog, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

from gui.styles import Styles
from gui.components.toggle_switch import ToggleSwitch
from config import config


class SettingsWidget(QWidget):
    """Страница настроек параметров бота и интерфейса."""

    def __init__(self, bot_engine, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine

        # Инициализация UI
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса страницы настроек."""
        # Основной лэйаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

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

        layout.addLayout(title_layout)

        # Секция "Подключение ADB"
        adb_frame = QFrame()
        adb_frame.setObjectName("section_box")
        adb_layout = QVBoxLayout(adb_frame)
        adb_layout.setContentsMargins(0, 0, 0, 0)
        adb_layout.setSpacing(0)

        # Заголовок секции
        adb_header = QLabel("Подключение ADB")
        adb_header.setObjectName("header")
        adb_layout.addWidget(adb_header)

        # Содержимое секции
        adb_content = QWidget()
        adb_content_layout = QGridLayout(adb_content)
        adb_content_layout.setContentsMargins(15, 15, 15, 15)

        # Статус ADB
        adb_content_layout.addWidget(QLabel("Статус ADB:"), 0, 0)

        self.adb_status_layout = QHBoxLayout()

        self.adb_status_indicator = QLabel("●")
        self.adb_status_indicator.setStyleSheet(f"color: {Styles.COLORS['text_secondary']}; font-size: 18px;")
        self.adb_status_layout.addWidget(self.adb_status_indicator)

        self.adb_status_label = QLabel("Не проверено")
        self.adb_status_layout.addWidget(self.adb_status_label)
        self.adb_status_layout.addStretch()

        adb_content_layout.addLayout(self.adb_status_layout, 0, 1)

        # Путь к ADB
        adb_content_layout.addWidget(QLabel("Путь к ADB:"), 1, 0)

        adb_path_layout = QHBoxLayout()

        self.adb_path_input = QLineEdit()
        self.adb_path_input.setText(config.get("adb", "path", "adb.exe" if __import__('os').name == "nt" else "adb"))
        self.adb_path_input.setReadOnly(True)
        adb_path_layout.addWidget(self.adb_path_input)

        adb_content_layout.addLayout(adb_path_layout, 1, 1)

        # Кнопка проверки соединения
        test_button = QPushButton("Проверить подключение")
        test_button.clicked.connect(self.test_adb_connection)
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

        adb_layout.addWidget(adb_content)

        layout.addWidget(adb_frame)

        # Секция "Настройки бота"
        bot_frame = QFrame()
        bot_frame.setObjectName("section_box")
        bot_layout = QVBoxLayout(bot_frame)
        bot_layout.setContentsMargins(0, 0, 0, 0)
        bot_layout.setSpacing(0)

        # Заголовок секции
        bot_header = QLabel("Настройки бота")
        bot_header.setObjectName("header")
        bot_layout.addWidget(bot_header)

        # Содержимое секции
        bot_content = QWidget()
        bot_content_layout = QGridLayout(bot_content)
        bot_content_layout.setContentsMargins(15, 15, 15, 15)
        bot_content_layout.setColumnStretch(0, 1)  # Первая колонка (названия параметров) может растягиваться
        bot_content_layout.setColumnStretch(1, 0)  # Вторая колонка (поля ввода) фиксированной ширины

        # Время ожидания боя
        battle_timeout_label = QLabel("Время ожидания боя (секунды)")
        battle_timeout_label.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        bot_content_layout.addWidget(battle_timeout_label, 0, 0)

        self.battle_timeout_input = QSpinBox()
        self.battle_timeout_input.setRange(30, 300)
        self.battle_timeout_input.setValue(config.get("bot", "battle_timeout", 120))
        self.battle_timeout_input.setMinimumWidth(120)  # Увеличиваем минимальную ширину
        self.battle_timeout_input.setFixedHeight(30)  # Увеличиваем высоту
        self.battle_timeout_input.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)  # Убираем кнопки +/-
        self.battle_timeout_input.setStyleSheet(f"""
            QSpinBox {{
                padding: 4px 10px;
                background-color: {Styles.COLORS['background_input']};
                color: {Styles.COLORS['text_primary']};
                border: 1px solid {Styles.COLORS['border']};
                border-radius: 4px;
            }}
        """)
        bot_content_layout.addWidget(self.battle_timeout_input, 0, 1)

        # Подсказка для времени ожидания
        timeout_hint = QLabel("Рекомендуемое значение: 90-180 секунд")
        timeout_hint.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        bot_content_layout.addWidget(timeout_hint, 1, 1)

        # Макс. попыток обновления
        max_refresh_label = QLabel("Макс. попыток обновления")
        max_refresh_label.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        bot_content_layout.addWidget(max_refresh_label, 2, 0)

        self.max_refresh_input = QSpinBox()
        self.max_refresh_input.setRange(1, 10)
        self.max_refresh_input.setValue(config.get("bot", "max_refresh_attempts", 3))
        self.max_refresh_input.setMinimumWidth(120)  # Увеличиваем минимальную ширину
        self.max_refresh_input.setFixedHeight(30)  # Увеличиваем высоту
        self.max_refresh_input.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)  # Убираем кнопки +/-
        self.max_refresh_input.setStyleSheet(f"""
            QSpinBox {{
                padding: 4px 10px;
                background-color: {Styles.COLORS['background_input']};
                color: {Styles.COLORS['text_primary']};
                border: 1px solid {Styles.COLORS['border']};
                border-radius: 4px;
            }}
        """)
        bot_content_layout.addWidget(self.max_refresh_input, 2, 1)

        # Интервал проверки
        check_interval_label = QLabel("Интервал проверки (секунды)")
        check_interval_label.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        bot_content_layout.addWidget(check_interval_label, 3, 0)

        self.check_interval_input = QSpinBox()
        self.check_interval_input.setRange(1, 10)
        self.check_interval_input.setValue(config.get("bot", "check_interval", 3))
        self.check_interval_input.setMinimumWidth(120)  # Увеличиваем минимальную ширину
        self.check_interval_input.setFixedHeight(30)  # Увеличиваем высоту
        self.check_interval_input.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)  # Убираем кнопки +/-
        self.check_interval_input.setStyleSheet(f"""
            QSpinBox {{
                padding: 4px 10px;
                background-color: {Styles.COLORS['background_input']};
                color: {Styles.COLORS['text_primary']};
                border: 1px solid {Styles.COLORS['border']};
                border-radius: 4px;
            }}
        """)
        bot_content_layout.addWidget(self.check_interval_input, 3, 1)

        # Режим отладки
        debug_mode_label = QLabel("Включить режим отладки")
        debug_mode_label.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        bot_content_layout.addWidget(debug_mode_label, 4, 0)

        self.debug_mode_toggle = ToggleSwitch()
        self.debug_mode_toggle.setChecked(config.get("bot", "debug_mode", False))
        bot_content_layout.addWidget(self.debug_mode_toggle, 4, 1)

        # Кнопка сохранения настроек
        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch()

        save_button = QPushButton("Сохранить настройки")
        save_button.setObjectName("success")
        save_button.setMinimumWidth(200)  # Увеличиваем ширину кнопки
        save_button.setFixedHeight(40)  # Увеличиваем высоту кнопки
        save_button.clicked.connect(self.save_settings)
        save_button_layout.addWidget(save_button)

        bot_content_layout.addLayout(save_button_layout, 5, 0, 1, 2)

        bot_layout.addWidget(bot_content)

        layout.addWidget(bot_frame)

        # Секция "Настройки интерфейса"
        ui_frame = QFrame()
        ui_frame.setObjectName("section_box")
        ui_layout = QVBoxLayout(ui_frame)
        ui_layout.setContentsMargins(0, 0, 0, 0)
        ui_layout.setSpacing(0)

        # Заголовок секции
        ui_header = QLabel("Настройки интерфейса")
        ui_header.setObjectName("header")
        ui_layout.addWidget(ui_header)

        # Содержимое секции
        ui_content = QWidget()
        ui_content_layout = QGridLayout(ui_content)
        ui_content_layout.setContentsMargins(15, 15, 15, 15)
        ui_content_layout.setColumnStretch(0, 1)  # Первая колонка (названия параметров) может растягиваться
        ui_content_layout.setColumnStretch(1, 0)  # Вторая колонка (поля ввода) фиксированной ширины

        # Уровень логирования
        log_level_label = QLabel("Уровень логирования")
        log_level_label.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        ui_content_layout.addWidget(log_level_label, 0, 0)

        from PyQt6.QtWidgets import QComboBox
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(config.get("ui", "log_level", "INFO"))
        self.log_level_combo.setMinimumWidth(120)  # Увеличиваем минимальную ширину
        self.log_level_combo.setFixedHeight(30)  # Увеличиваем высоту
        self.log_level_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 4px 10px;
                background-color: {Styles.COLORS['background_input']};
                color: {Styles.COLORS['text_primary']};
                border: 1px solid {Styles.COLORS['border']};
                border-radius: 4px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)
        ui_content_layout.addWidget(self.log_level_combo, 0, 1)

        # Тема
        theme_label = QLabel("Тема")
        theme_label.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        ui_content_layout.addWidget(theme_label, 1, 0)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Тёмная"])
        self.theme_combo.setCurrentIndex(0)
        self.theme_combo.setMinimumWidth(120)  # Увеличиваем минимальную ширину
        self.theme_combo.setFixedHeight(30)  # Увеличиваем высоту
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 4px 10px;
                background-color: {Styles.COLORS['background_input']};
                color: {Styles.COLORS['text_primary']};
                border: 1px solid {Styles.COLORS['border']};
                border-radius: 4px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)
        ui_content_layout.addWidget(self.theme_combo, 1, 1)

        ui_layout.addWidget(ui_content)

        layout.addWidget(ui_frame)

        # Растягивающийся элемент в конце
        layout.addStretch()

        # Инициализация состояния ADB
        self.check_adb_status()

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

        # Сохраняем в конфигурацию
        config.set("bot", "battle_timeout", battle_timeout)
        config.set("bot", "max_refresh_attempts", max_refresh)
        config.set("bot", "check_interval", check_interval)
        config.set("bot", "debug_mode", debug_mode)
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