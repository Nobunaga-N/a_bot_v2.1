from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSpinBox, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

from gui.styles import Styles


class BaseDialog(QDialog):
    """Базовый класс для создания стилизованных диалогов."""

    def __init__(self, title, parent=None):
        super().__init__(parent)

        # Настройка окна
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Основной лэйаут
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Заголовок
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {Styles.COLORS['text_primary']};
        """)
        self.layout.addWidget(self.title_label)

        # Контейнер для содержимого
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet(f"""
            background-color: {Styles.COLORS['background_light']};
            border-radius: 8px;
        """)

        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(10)

        self.layout.addWidget(self.content_frame)

        # Кнопки действий
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)
        self.button_layout.addStretch()

        # По умолчанию добавляем кнопку закрытия
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.close_button)

        self.layout.addLayout(self.button_layout)

    def add_widget(self, widget):
        """Добавляет виджет в основную область содержимого."""
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Добавляет лэйаут в основную область содержимого."""
        self.content_layout.addLayout(layout)

    def add_spacer(self):
        """Добавляет растягивающийся элемент в содержимое."""
        self.content_layout.addSpacerItem(
            QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    def add_button(self, text, callback, is_primary=False, is_danger=False):
        """Добавляет кнопку в нижнюю панель действий."""
        button = QPushButton(text)

        if is_primary:
            button.setObjectName("success")
        elif is_danger:
            button.setObjectName("danger")

        button.clicked.connect(callback)

        # Вставляем перед последним элементом (обычно это spacer или кнопка закрытия)
        self.button_layout.insertWidget(self.button_layout.count() - 1, button)

        return button


class ConfirmDialog(BaseDialog):
    """Диалог для подтверждения действия."""

    def __init__(self, title, message, parent=None, confirm_text="Да", cancel_text="Нет", is_danger=False):
        super().__init__(title, parent)

        # Сообщение
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        self.add_widget(message_label)

        # Кнопки
        self.add_button(confirm_text, self.accept, is_primary=not is_danger, is_danger=is_danger)
        self.close_button.setText(cancel_text)


class InputDialog(BaseDialog):
    """Диалог для ввода данных."""

    value_entered = pyqtSignal(str)

    def __init__(self, title, label_text, parent=None, placeholder="", default_value="", multiline=False):
        super().__init__(title, parent)

        # Метка
        label = QLabel(label_text)
        self.add_widget(label)

        # Поле ввода
        if multiline:
            self.input_field = QTextEdit()
            self.input_field.setPlaceholderText(placeholder)
            self.input_field.setText(default_value)
            self.input_field.setMinimumHeight(100)
        else:
            self.input_field = QLineEdit()
            self.input_field.setPlaceholderText(placeholder)
            self.input_field.setText(default_value)

        self.add_widget(self.input_field)

        # Кнопки
        self.add_button("OK", self._on_ok, is_primary=True)

    def _on_ok(self):
        """Обработка нажатия кнопки OK."""
        if isinstance(self.input_field, QTextEdit):
            value = self.input_field.toPlainText()
        else:
            value = self.input_field.text()

        self.value_entered.emit(value)
        self.accept()

    def get_value(self):
        """Возвращает введенное значение."""
        if isinstance(self.input_field, QTextEdit):
            return self.input_field.toPlainText()
        else:
            return self.input_field.text()


class NumberInputDialog(BaseDialog):
    """Диалог для ввода числового значения."""

    value_entered = pyqtSignal(int)

    def __init__(self, title, label_text, parent=None, min_value=0, max_value=1000, step=1, default_value=0):
        super().__init__(title, parent)

        # Метка
        label = QLabel(label_text)
        self.add_widget(label)

        # Поле ввода
        self.input_field = QSpinBox()
        self.input_field.setRange(min_value, max_value)
        self.input_field.setSingleStep(step)
        self.input_field.setValue(default_value)

        self.add_widget(self.input_field)

        # Кнопки
        self.add_button("OK", self._on_ok, is_primary=True)

    def _on_ok(self):
        """Обработка нажатия кнопки OK."""
        value = self.input_field.value()
        self.value_entered.emit(value)
        self.accept()

    def get_value(self):
        """Возвращает введенное значение."""
        return self.input_field.value()


class OptionsDialog(BaseDialog):
    """Диалог для выбора из нескольких вариантов."""

    option_selected = pyqtSignal(str)

    def __init__(self, title, label_text, options, parent=None, default_option=None):
        super().__init__(title, parent)

        # Метка
        label = QLabel(label_text)
        self.add_widget(label)

        # Выпадающий список
        self.combo_box = QComboBox()
        for option in options:
            self.combo_box.addItem(option)

        if default_option and default_option in options:
            self.combo_box.setCurrentText(default_option)

        self.add_widget(self.combo_box)

        # Кнопки
        self.add_button("OK", self._on_ok, is_primary=True)

    def _on_ok(self):
        """Обработка нажатия кнопки OK."""
        selected = self.combo_box.currentText()
        self.option_selected.emit(selected)
        self.accept()

    def get_selected_option(self):
        """Возвращает выбранную опцию."""
        return self.combo_box.currentText()


# Пример использования:
"""
# Диалог подтверждения
confirm_dialog = ConfirmDialog(
    "Подтверждение сброса", 
    "Вы уверены, что хотите сбросить все настройки?",
    parent=self,
    is_danger=True
)

if confirm_dialog.exec() == QDialog.DialogCode.Accepted:
    # Пользователь подтвердил действие
    print("Сброс подтвержден")

# Диалог ввода текста
input_dialog = InputDialog(
    "Ввод названия", 
    "Введите название профиля:",
    parent=self,
    placeholder="Мой профиль",
    default_value="Профиль 1"
)

if input_dialog.exec() == QDialog.DialogCode.Accepted:
    profile_name = input_dialog.get_value()
    print(f"Введено название: {profile_name}")

# Диалог ввода числа
number_dialog = NumberInputDialog(
    "Настройка цели", 
    "Укажите целевое количество ключей:",
    parent=self,
    min_value=100,
    max_value=5000,
    step=100,
    default_value=1000
)

if number_dialog.exec() == QDialog.DialogCode.Accepted:
    target_keys = number_dialog.get_value()
    print(f"Установлена цель: {target_keys}")

# Диалог выбора опции
options_dialog = OptionsDialog(
    "Выбор сложности", 
    "Выберите уровень сложности:",
    ["Легкий", "Средний", "Сложный"],
    parent=self,
    default_option="Средний"
)

if options_dialog.exec() == QDialog.DialogCode.Accepted:
    difficulty = options_dialog.get_selected_option()
    print(f"Выбран уровень сложности: {difficulty}")
"""