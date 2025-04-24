from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QMessageBox, QApplication, QProgressBar, QGridLayout,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont, QPixmap
import datetime

from gui.styles import Styles


class ScrollFriendlyLineEdit(QLineEdit):
    """Класс QLineEdit, который игнорирует события прокрутки колеса мыши."""

    def wheelEvent(self, event):
        # Игнорируем событие прокрутки, чтобы его обработал родительский скролл
        event.ignore()


class LicenseInfoCard(QFrame):
    """Карточка с детальной информацией о лицензии."""

    def __init__(self, license_info, parent=None):
        super().__init__(parent)
        self.setObjectName("section_box")

        # Настройка лейаута
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Заголовок
        header = QLabel("Статус лицензии")
        header.setObjectName("header")
        layout.addWidget(header)

        # Содержимое
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # Основная информация о лицензии
        status_layout = QHBoxLayout()

        # Иконка лицензии
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(64, 64)
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_icon.setStyleSheet(f"""
            background-color: {Styles.COLORS['background_medium']};
            border-radius: 32px;
            font-size: 32px;
        """)
        status_layout.addWidget(self.status_icon)

        # Информация о статусе
        info_layout = QVBoxLayout()

        self.status_title = QLabel()
        self.status_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
        """)
        info_layout.addWidget(self.status_title)

        self.status_description = QLabel()
        self.status_description.setWordWrap(True)
        self.status_description.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        info_layout.addWidget(self.status_description)

        status_layout.addLayout(info_layout)
        status_layout.addStretch()

        content_layout.addLayout(status_layout)

        # Прогресс-бар срока лицензии
        progress_layout = QVBoxLayout()

        progress_title = QLabel("Осталось дней до истечения лицензии")
        progress_title.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        progress_layout.addWidget(progress_title)

        self.license_progress = QProgressBar()
        self.license_progress.setTextVisible(True)
        self.license_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Styles.COLORS['background_medium']};
                border-radius: 4px;
                text-align: center;
                color: {Styles.COLORS['text_primary']};
                min-height: 25px;
            }}

            QProgressBar::chunk {{
                background-color: {Styles.COLORS['primary']};
                border-radius: 4px;
            }}
        """)
        progress_layout.addWidget(self.license_progress)

        content_layout.addLayout(progress_layout)

        # Детальная информация о лицензии (сетка)
        details_grid = QGridLayout()
        details_grid.setColumnStretch(1, 1)
        details_grid.setColumnStretch(3, 1)
        details_grid.setVerticalSpacing(15)  # Увеличиваем вертикальное расстояние

        # Строка 1: Статус и дата истечения
        details_grid.addWidget(QLabel("Статус:"), 0, 0)
        self.status_value = QLabel()
        details_grid.addWidget(self.status_value, 0, 1)

        details_grid.addWidget(QLabel("Дата истечения:"), 0, 2)
        self.expiration_value = QLabel()
        details_grid.addWidget(self.expiration_value, 0, 3)

        # Строка 2: Осталось дней и дата активации
        details_grid.addWidget(QLabel("Осталось дней:"), 1, 0)
        self.days_left_value = QLabel()
        details_grid.addWidget(self.days_left_value, 1, 1)

        details_grid.addWidget(QLabel("Дата активации:"), 1, 2)
        self.activation_date = QLabel("Н/Д")  # Пока нет в данных
        details_grid.addWidget(self.activation_date, 1, 3)

        content_layout.addLayout(details_grid)

        layout.addWidget(content)

        # Обновление данных
        self.update_license_info(license_info)

    def update_license_info(self, license_info):
        """Обновляет отображаемую информацию о лицензии."""
        # Статус лицензии
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

        # Устанавливаем цвет и иконку в зависимости от статуса
        if status == "valid":
            self.status_title.setText("Лицензия активна")
            self.status_title.setStyleSheet(f"color: {Styles.COLORS['secondary']}; font-size: 16px; font-weight: bold;")
            self.status_description.setText("Ваша лицензия действительна и активирована для текущего устройства")
            self.status_icon.setText("✓")
            self.status_icon.setStyleSheet(f"""
                background-color: {Styles.COLORS['secondary']};
                color: {Styles.COLORS['background_dark']};
                border-radius: 32px;
                font-size: 32px;
            """)
            self.status_value.setStyleSheet(f"color: {Styles.COLORS['secondary']};")
        elif status == "expired":
            self.status_title.setText("Лицензия истекла")
            self.status_title.setStyleSheet(f"color: {Styles.COLORS['accent']}; font-size: 16px; font-weight: bold;")
            self.status_description.setText("Срок действия вашей лицензии истек, пожалуйста, обновите лицензию")
            self.status_icon.setText("!")
            self.status_icon.setStyleSheet(f"""
                background-color: {Styles.COLORS['accent']};
                color: {Styles.COLORS['background_dark']};
                border-radius: 32px;
                font-size: 32px;
            """)
            self.status_value.setStyleSheet(f"color: {Styles.COLORS['accent']};")
        else:
            self.status_title.setText("Лицензия не активирована")
            self.status_title.setStyleSheet(f"color: {Styles.COLORS['warning']}; font-size: 16px; font-weight: bold;")
            self.status_description.setText("Активируйте лицензию с помощью полученного ключа")
            self.status_icon.setText("?")
            self.status_icon.setStyleSheet(f"""
                background-color: {Styles.COLORS['warning']};
                color: {Styles.COLORS['background_dark']};
                border-radius: 32px;
                font-size: 32px;
            """)
            self.status_value.setStyleSheet(f"color: {Styles.COLORS['warning']};")

        # Дата истечения
        expiration = license_info.get("expiration")
        if expiration:
            self.expiration_value.setText(expiration.strftime("%d.%m.%Y"))
        else:
            self.expiration_value.setText("Н/Д")

        # Осталось дней
        days_left = license_info.get("days_left", 0)
        self.days_left_value.setText(str(days_left))

        # Цвет в зависимости от оставшегося времени
        if days_left > 30:
            self.days_left_value.setStyleSheet(f"color: {Styles.COLORS['secondary']};")
        elif days_left > 7:
            self.days_left_value.setStyleSheet(f"color: {Styles.COLORS['warning']};")
        else:
            self.days_left_value.setStyleSheet(f"color: {Styles.COLORS['accent']};")

        # Прогресс-бар
        # Предполагаем, что максимальный срок лицензии 365 дней
        total_days = 365
        if expiration:
            # Если известна дата истечения, вычисляем общую продолжительность лицензии
            now = datetime.datetime.utcnow()
            if status == "valid":
                # Предполагаем, что activation_date это дата активации, которую нужно получить
                # Если нет точной даты активации, можно оценить ее по дате истечения и days_left
                total_days = days_left  # Изначально инициализируем как оставшиеся дни

                # Ищем дату активации в лицензионной информации
                if hasattr(self, 'activation_date') and self.activation_date.text() != "Н/Д":
                    try:
                        activation_date = datetime.datetime.strptime(self.activation_date.text(), "%d.%m.%Y")
                        total_original_days = (expiration - activation_date).days
                        if total_original_days > 0:
                            total_days = total_original_days
                    except:
                        pass

                # Вычисляем прогресс как оставшиеся дни / общее количество дней
                self.license_progress.setRange(0, total_days)
                self.license_progress.setValue(days_left)
                self.license_progress.setFormat(f"Осталось {days_left} из {total_days} дней (%p%)")
            else:
                self.license_progress.setRange(0, 100)
                self.license_progress.setValue(0)
                self.license_progress.setFormat("Лицензия недействительна")
        else:
            self.license_progress.setRange(0, 100)
            self.license_progress.setValue(0)
            self.license_progress.setFormat("Нет данных о лицензии")


class LicenseActivationCard(QFrame):
    """Карточка для активации лицензии."""

    def __init__(self, license_validator, parent=None):
        super().__init__(parent)
        self.license_validator = license_validator
        self.setObjectName("section_box")

        # Настройка лейаута
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Заголовок
        header = QLabel("Активация лицензии")
        header.setObjectName("header")
        layout.addWidget(header)

        # Содержимое
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # Информационный текст
        info_text = QLabel(
            "Введите лицензионный ключ для активации программы.\n"
            "Если у вас нет ключа, обратитесь к разработчику, предоставив отпечаток устройства."
        )
        info_text.setWordWrap(True)
        content_layout.addWidget(info_text)

        # Поле ввода лицензионного ключа
        key_layout = QVBoxLayout()

        key_label = QLabel("Лицензионный ключ:")
        key_layout.addWidget(key_label)

        self.license_key_input = ScrollFriendlyLineEdit()
        self.license_key_input.setPlaceholderText("Введите лицензионный ключ")
        self.license_key_input.setMinimumHeight(35)  # Увеличиваем высоту поля
        self.license_key_input.setStyleSheet(f"""
            padding: 10px;
            font-family: monospace;
            background-color: {Styles.COLORS['background_input']};
            color: {Styles.COLORS['text_primary']};
            border: 1px solid {Styles.COLORS['border']};
            border-radius: 4px;
        """)
        key_layout.addWidget(self.license_key_input)

        content_layout.addLayout(key_layout)

        # Кнопка активации
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.activate_button = QPushButton("Активировать лицензию")
        self.activate_button.setObjectName("success")
        self.activate_button.setMinimumHeight(35)  # Увеличиваем высоту кнопки
        self.activate_button.setFixedWidth(200)  # Фиксируем ширину кнопки
        self.activate_button.clicked.connect(self.activate_license)
        button_layout.addWidget(self.activate_button)

        content_layout.addLayout(button_layout)

        layout.addWidget(content)

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

            # Поиск LicenseWidget в иерархии родителей
            from gui.widgets.license_widget import LicenseWidget
            parent = self.parent()
            license_widget = None

            # Ищем родительский виджет типа LicenseWidget
            while parent:
                if isinstance(parent, LicenseWidget):
                    license_widget = parent
                    break
                parent = parent.parent()

            # Если нашли LicenseWidget, обновляем информацию о лицензии
            if license_widget and hasattr(license_widget, 'update_license_info'):
                license_widget.update_license_info()

            # Ищем главное окно для обновления статуса лицензии
            from gui.main_window import MainWindow
            parent = self.parent()
            while parent:
                if isinstance(parent, MainWindow):
                    # Обновляем статус лицензии в MainWindow
                    parent.update_license_status()
                    # Отправляем сигнал об обновлении лицензии
                    if hasattr(parent, 'signals'):
                        parent.signals.license_updated.emit()
                    break
                parent = parent.parent()
        else:
            QMessageBox.critical(
                self,
                "Ошибка лицензии",
                "Лицензионный ключ недействителен или истек.\n"
                "Пожалуйста, проверьте ключ и попробуйте снова."
            )


class DeviceInfoCard(QFrame):
    """Карточка с информацией об устройстве и отпечатком."""

    def __init__(self, fingerprint_generator, parent=None):
        super().__init__(parent)
        self.fingerprint_generator = fingerprint_generator
        self.setObjectName("section_box")

        # Настройка лейаута
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Заголовок
        header = QLabel("Информация об устройстве")
        header.setObjectName("header")
        layout.addWidget(header)

        # Содержимое
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # Пояснительный текст
        info_text = QLabel(
            "Для получения лицензионного ключа необходимо предоставить "
            "разработчику уникальный отпечаток вашего устройства. "
            "Скопируйте этот отпечаток и отправьте его вместе с запросом на лицензию."
        )
        info_text.setWordWrap(True)
        content_layout.addWidget(info_text)

        # Отпечаток устройства
        fingerprint_layout = QVBoxLayout()

        fingerprint_label = QLabel("Отпечаток устройства:")
        fingerprint_layout.addWidget(fingerprint_label)

        self.fingerprint_input = ScrollFriendlyLineEdit()
        self.fingerprint_input.setReadOnly(True)
        self.fingerprint_input.setMinimumHeight(35)  # Увеличиваем высоту поля
        self.fingerprint_input.setStyleSheet(f"""
            background-color: {Styles.COLORS['background_input']};
            color: {Styles.COLORS['text_secondary']};
            padding: 10px;
            font-family: monospace;
            border: 1px solid {Styles.COLORS['border']};
            border-radius: 4px;
        """)
        fingerprint_layout.addWidget(self.fingerprint_input)

        content_layout.addLayout(fingerprint_layout)

        # Кнопки действий
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.copy_button = QPushButton("Копировать")
        self.copy_button.setMinimumHeight(35)  # Увеличиваем высоту кнопки
        self.copy_button.setFixedWidth(150)  # Фиксируем ширину кнопки
        self.copy_button.clicked.connect(self.copy_fingerprint)
        buttons_layout.addWidget(self.copy_button)

        content_layout.addLayout(buttons_layout)

        layout.addWidget(content)

        # Инициализация отпечатка
        self.update_fingerprint()

    def update_fingerprint(self):
        """Обновляет отображение отпечатка устройства."""
        fingerprint = self.fingerprint_generator.generate()
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

            # Подтверждение копирования
            old_text = self.copy_button.text()
            self.copy_button.setText("Скопировано!")

            # Возвращаем старый текст через 1.5 секунды
            QTimer.singleShot(1500, lambda: self.copy_button.setText(old_text))


class LicenseWidget(QWidget):
    """Страница управления лицензией."""

    def __init__(self, license_validator, parent=None):
        super().__init__(parent)
        self.license_validator = license_validator

        # Инициализация UI
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса страницы лицензии."""
        # Основной лэйаут
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

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

        # Информация о лицензии
        self.license_info_card = LicenseInfoCard(
            self.license_validator.get_license_info()
        )
        scroll_layout.addWidget(self.license_info_card)

        # Активация лицензии
        self.activation_card = LicenseActivationCard(
            self.license_validator,
            parent=self
        )
        scroll_layout.addWidget(self.activation_card)

        # Информация об устройстве
        self.device_info_card = DeviceInfoCard(
            self.license_validator.fingerprint,
            parent=self
        )
        scroll_layout.addWidget(self.device_info_card)

        # Добавляем растягивающийся элемент в конце
        scroll_layout.addStretch()

        # Устанавливаем виджет содержимого в область прокрутки
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)  # Растягиваем по вертикали

    def update_license_info(self):
        """Обновляет информацию о лицензии."""
        # Получаем актуальную информацию от валидатора
        license_info = self.license_validator.get_license_info()

        # Обновляем карточку с информацией
        self.license_info_card.update_license_info(license_info)

        # Логируем обновление информации о лицензии
        import logging
        logger = logging.getLogger("BotLogger")
        status = license_info.get("status", "неизвестно")
        logger.debug(f"Обновлена информация о лицензии. Статус: {status}")