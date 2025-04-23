from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

from gui.styles import Styles


class LicenseWidget(QWidget):
    """Страница управления лицензией."""

    def __init__(self, license_validator, parent=None):
        super().__init__(parent)
        self.license_validator = license_validator

        # Инициализация UI
        self.init_ui()

        # Обновление информации о лицензии
        self.update_license_info()

    def init_ui(self):
        """Инициализация интерфейса страницы лицензии."""
        # Основной лэйаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Заголовок страницы
        title_layout = QVBoxLayout()

        title_label = QLabel("Управление лицензией")
        title_label.setObjectName("title")
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {Styles.COLORS['text_primary']};
        """)
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("Информация о лицензии и активация")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setStyleSheet(f"""
            font-size: 14px;
            color: {Styles.COLORS['text_secondary']};
        """)
        title_layout.addWidget(subtitle_label)

        layout.addLayout(title_layout)

        # Секция "Информация о лицензии"
        license_frame = QFrame()
        license_frame.setObjectName("section_box")
        license_layout = QVBoxLayout(license_frame)
        license_layout.setContentsMargins(0, 0, 0, 0)
        license_layout.setSpacing(0)

        # Заголовок секции
        license_header = QLabel("Информация о лицензии")
        license_header.setObjectName("header")
        license_layout.addWidget(license_header)

        # Содержимое секции
        license_content = QWidget()
        license_content_layout = QVBoxLayout(license_content)
        license_content_layout.setContentsMargins(15, 15, 15, 15)
        license_content_layout.setSpacing(15)

        # Статус лицензии с иконкой
        license_status_layout = QHBoxLayout()

        # Иконка
        license_icon = QLabel()
        license_icon.setFixedSize(48, 48)
        license_icon.setStyleSheet(f"""
            background-color: {Styles.COLORS['background_medium']};
            border-radius: 24px;
        """)

        # Временное отображение иконки (в реальности будет нормальная иконка)
        license_icon_text = QLabel("🔑")
        license_icon_text.setStyleSheet(f"""
            font-size: 20px;
            color: {Styles.COLORS['primary']};
        """)

        license_icon_layout = QHBoxLayout(license_icon)
        license_icon_layout.setContentsMargins(0, 0, 0, 0)
        license_icon_layout.addWidget(license_icon_text, alignment=Qt.AlignmentFlag.AlignCenter)

        license_status_layout.addWidget(license_icon)

        # Текст статуса
        license_status_text = QVBoxLayout()

        self.license_status_title = QLabel("Лицензия активна")
        self.license_status_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {Styles.COLORS['primary']};
        """)
        license_status_text.addWidget(self.license_status_title)

        self.license_status_subtitle = QLabel("Ваша лицензия действительна и активирована для текущего устройства")
        self.license_status_subtitle.setWordWrap(True)
        self.license_status_subtitle.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        license_status_text.addWidget(self.license_status_subtitle)

        license_status_layout.addLayout(license_status_text)
        license_status_layout.addStretch()

        license_content_layout.addLayout(license_status_layout)

        # Информация о сроке действия лицензии (3 колонки)
        license_info_layout = QHBoxLayout()
        license_info_layout.setSpacing(20)

        # Колонка "Статус"
        status_layout = QVBoxLayout()

        status_title = QLabel("Статус")
        status_title.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        status_layout.addWidget(status_title)

        self.status_indicator_layout = QHBoxLayout()
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"color: {Styles.COLORS['secondary']}; font-size: 18px;")
        self.status_indicator_layout.addWidget(self.status_indicator)

        self.status_value = QLabel("Действительна")
        self.status_value.setStyleSheet(f"color: {Styles.COLORS['text_primary']};")
        self.status_indicator_layout.addWidget(self.status_value)

        status_layout.addLayout(self.status_indicator_layout)
        license_info_layout.addLayout(status_layout)

        # Колонка "Срок действия до"
        expiration_layout = QVBoxLayout()

        expiration_title = QLabel("Срок действия до")
        expiration_title.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        expiration_layout.addWidget(expiration_title)

        self.expiration_value = QLabel("31.12.2025")
        self.expiration_value.setStyleSheet(f"color: {Styles.COLORS['text_primary']};")
        expiration_layout.addWidget(self.expiration_value)

        license_info_layout.addLayout(expiration_layout)

        # Колонка "Осталось дней"
        days_left_layout = QVBoxLayout()

        days_left_title = QLabel("Осталось дней")
        days_left_title.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        days_left_layout.addWidget(days_left_title)

        self.days_left_value = QLabel("283")
        self.days_left_value.setStyleSheet(f"color: {Styles.COLORS['primary']};")
        days_left_layout.addWidget(self.days_left_value)

        license_info_layout.addLayout(days_left_layout)

        license_content_layout.addLayout(license_info_layout)

        license_layout.addWidget(license_content)

        layout.addWidget(license_frame)

        # Секция "Отпечаток устройства"
        fingerprint_frame = QFrame()
        fingerprint_frame.setObjectName("section_box")
        fingerprint_layout = QVBoxLayout(fingerprint_frame)
        fingerprint_layout.setContentsMargins(0, 0, 0, 0)
        fingerprint_layout.setSpacing(0)

        # Заголовок секции
        fingerprint_header = QLabel("Отпечаток устройства")
        fingerprint_header.setObjectName("header")
        fingerprint_layout.addWidget(fingerprint_header)

        # Содержимое секции
        fingerprint_content = QWidget()
        fingerprint_content_layout = QVBoxLayout(fingerprint_content)
        fingerprint_content_layout.setContentsMargins(15, 15, 15, 15)
        fingerprint_content_layout.setSpacing(15)

        # Информационный текст
        fingerprint_info = QLabel(
            "Этот уникальный идентификатор используется для активации лицензии на данном устройстве. "
            "Отправьте его разработчику для получения лицензионного ключа."
        )
        fingerprint_info.setWordWrap(True)
        fingerprint_info.setStyleSheet(f"color: {Styles.COLORS['text_primary']};")
        fingerprint_content_layout.addWidget(fingerprint_info)

        # Отпечаток с кнопкой копирования
        fingerprint_input_layout = QHBoxLayout()

        self.fingerprint_input = QLineEdit()
        self.fingerprint_input.setReadOnly(True)
        self.fingerprint_input.setStyleSheet(f"""
            background-color: {Styles.COLORS['background_input']};
            color: {Styles.COLORS['text_secondary']};
            padding: 10px;
        """)
        fingerprint_input_layout.addWidget(self.fingerprint_input)

        copy_button = QPushButton("Копировать")
        copy_button.setFixedWidth(150)
        copy_button.clicked.connect(self.copy_fingerprint)
        fingerprint_input_layout.addWidget(copy_button)

        fingerprint_content_layout.addLayout(fingerprint_input_layout)

        fingerprint_layout.addWidget(fingerprint_content)

        layout.addWidget(fingerprint_frame)

        # Секция "Активация лицензии"
        activation_frame = QFrame()
        activation_frame.setObjectName("section_box")
        activation_layout = QVBoxLayout(activation_frame)
        activation_layout.setContentsMargins(0, 0, 0, 0)
        activation_layout.setSpacing(0)

        # Заголовок секции
        activation_header = QLabel("Активация лицензии")
        activation_header.setObjectName("header")
        activation_layout.addWidget(activation_header)

        # Содержимое секции
        activation_content = QWidget()
        activation_content_layout = QVBoxLayout(activation_content)
        activation_content_layout.setContentsMargins(15, 15, 15, 15)
        activation_content_layout.setSpacing(15)

        # Информационный текст
        activation_info = QLabel("Введите полученный лицензионный ключ для активации программы")
        activation_info.setStyleSheet(f"color: {Styles.COLORS['text_primary']};")
        activation_content_layout.addWidget(activation_info)

        # Поле ввода лицензионного ключа
        self.license_key_input = QLineEdit()
        self.license_key_input.setPlaceholderText("Введите лицензионный ключ")
        self.license_key_input.setStyleSheet(f"""
            padding: 10px;
        """)
        activation_content_layout.addWidget(self.license_key_input)

        # Кнопка активации
        activate_button_layout = QHBoxLayout()
        activate_button_layout.addStretch()

        activate_button = QPushButton("Активировать лицензию")
        activate_button.setObjectName("success")
        activate_button.setFixedWidth(200)
        activate_button.clicked.connect(self.activate_license)
        activate_button_layout.addWidget(activate_button)

        activation_content_layout.addLayout(activate_button_layout)

        activation_layout.addWidget(activation_content)

        layout.addWidget(activation_frame)

        # Заполняем отпечаток устройства
        self.update_fingerprint()

    def update_license_info(self):
        """Обновляет информацию о лицензии."""
        license_info = self.license_validator.get_license_info()

        # Обновляем статус
        status = license_info.get("status", "unknown")
        status_translations = {
            "valid": "Действительна",
            "expired": "Истекла",
            "missing": "Отсутствует",
            "invalid": "Недействительна",
            "error": "Ошибка",
            "unknown": "Неизвестно"
        }

        status_text = status_translations.get(status, status.capitalize())
        self.status_value.setText(status_text)

        # Устанавливаем цвет в зависимости от статуса
        if status == "valid":
            self.license_status_title.setText("Лицензия активна")
            self.license_status_title.setStyleSheet(
                f"color: {Styles.COLORS['secondary']}; font-size: 16px; font-weight: bold;")
            self.license_status_subtitle.setText("Ваша лицензия действительна и активирована для текущего устройства")

            self.status_indicator.setStyleSheet(f"color: {Styles.COLORS['secondary']}; font-size: 18px;")
            self.status_value.setStyleSheet(f"color: {Styles.COLORS['secondary']};")
        elif status == "expired":
            self.license_status_title.setText("Лицензия истекла")
            self.license_status_title.setStyleSheet(
                f"color: {Styles.COLORS['accent']}; font-size: 16px; font-weight: bold;")
            self.license_status_subtitle.setText("Срок действия вашей лицензии истек, пожалуйста, обновите лицензию")

            self.status_indicator.setStyleSheet(f"color: {Styles.COLORS['accent']}; font-size: 18px;")
            self.status_value.setStyleSheet(f"color: {Styles.COLORS['accent']};")
        else:
            self.license_status_title.setText("Лицензия не активирована")
            self.license_status_title.setStyleSheet(
                f"color: {Styles.COLORS['warning']}; font-size: 16px; font-weight: bold;")
            self.license_status_subtitle.setText("Активируйте лицензию с помощью полученного ключа")

            self.status_indicator.setStyleSheet(f"color: {Styles.COLORS['warning']}; font-size: 18px;")
            self.status_value.setStyleSheet(f"color: {Styles.COLORS['warning']};")

        # Обновляем дату истечения
        expiration = license_info.get("expiration")
        if expiration:
            self.expiration_value.setText(expiration.strftime("%d.%m.%Y"))
        else:
            self.expiration_value.setText("Н/Д")

        # Обновляем количество оставшихся дней
        days_left = license_info.get("days_left", 0)
        self.days_left_value.setText(str(days_left))

    def update_fingerprint(self):
        """Обновляет отображение отпечатка устройства."""
        fingerprint = self.license_validator.fingerprint.generate()
        if fingerprint:
            self.fingerprint_input.setText(fingerprint)
        else:
            self.fingerprint_input.setText("Ошибка получения отпечатка")

    def copy_fingerprint(self):
        """Копирует отпечаток устройства в буфер обмена."""
        fingerprint = self.fingerprint_input.text()
        if fingerprint:
            clipboard = QApplication.clipboard()
            clipboard.setText(fingerprint)

            # Меняем текст кнопки на короткое время
            sender = self.sender()
            original_text = sender.text()
            sender.setText("Скопировано!")

            # Возвращаем оригинальный текст через 1.5 секунды
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: sender.setText(original_text))

    def activate_license(self):
        """Активирует лицензию с введенным ключом."""
        license_key = self.license_key_input.text().strip()

        if not license_key:
            QMessageBox.warning(
                self,
                "Пустой лицензионный ключ",
                "Пожалуйста, введите действительный лицензионный ключ."
            )
            return

        if self.license_validator.verify_license(license_key):
            # Сохраняем лицензионный ключ
            self.license_validator.storage.save_license(license_key)

            QMessageBox.information(
                self,
                "Лицензия активирована",
                "Ваша лицензия была успешно активирована!"
            )

            # Очищаем поле ввода
            self.license_key_input.clear()

            # Обновляем информацию о лицензии
            self.update_license_info()
        else:
            QMessageBox.critical(
                self,
                "Ошибка лицензии",
                "Лицензионный ключ недействителен или истек.\n"
                "Пожалуйста, проверьте ключ и попробуйте снова."
            )