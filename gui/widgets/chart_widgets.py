from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
import os
import json
import tempfile
import logging

from gui.styles import Styles
from config import resource_path


class ChartConfig:
    """Конфигурация для разных типов графиков."""

    BATTLES = {
        'title': 'Тренд побед и поражений (7 дней)',
        'chart_id': 'battles-chart',
        'type': 'dual_bars',
        'data_keys': ['victories', 'defeats'],
        'colors': {
            'primary': '#42E189',
            'secondary': '#FF6B6C',
        },
        'legends': [
            ('● Победы', Styles.COLORS['secondary']),
            ('● Поражения', Styles.COLORS['accent'])
        ],
        'formatter': 'number',
        'axis_step_func': 'calculateBattlesAxisStep'
    }

    KEYS = {
        'title': 'Сбор ключей (7 дней)',
        'chart_id': 'keys-chart',
        'type': 'single_bar',
        'data_keys': ['keys_collected'],
        'colors': {
            'primary': '#FFB169',
        },
        'legends': [
            ('● Собрано ключей', Styles.COLORS['warning'])
        ],
        'formatter': 'number',
        'axis_step_func': 'calculateKeysAxisStep'
    }

    SILVER = {
        'title': 'Сбор серебра (7 дней)',
        'chart_id': 'silver-chart',
        'type': 'single_bar',
        'data_keys': ['silver_collected'],
        'colors': {
            'primary': '#3FE0C8',
        },
        'legends': [
            ('● Собрано серебра', Styles.COLORS['primary'])
        ],
        'formatter': 'silver',
        'axis_step_func': 'calculateSilverAxisStep'
    }


class OptimizedChartWidget(QWidget):
    """Оптимизированный базовый класс для графиков."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._py_logger = logging.getLogger("BotLogger")
        self.config = config
        self.title = config['title']

        # Флаги состояния
        self._last_data = None
        self._is_initialized = False
        self._should_animate_once = False

        # Создание UI
        self._create_ui()

        # Создание HTML файла
        self._create_html_file()

    def _create_ui(self):
        """Создает пользовательский интерфейс виджета."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Заголовок
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 5)

        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("chart-title")
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {Styles.COLORS['text_primary']};
            background-color: transparent;
        """)
        header_layout.addWidget(self.title_label)
        self.layout.addLayout(header_layout)

        # Контейнер для графика
        self.chart_container = QFrame()
        self.chart_container.setObjectName("chart-container")
        self.chart_container.setMinimumHeight(250)
        self.chart_container.setStyleSheet(f"""
            QFrame#chart-container {{
                background-color: {Styles.COLORS['background_dark']};
                border: none;
            }}
        """)

        chart_layout = QVBoxLayout(self.chart_container)
        chart_layout.setContentsMargins(1, 1, 1, 1)

        # WebEngine виджет
        self.web_view = QWebEngineView()
        settings = self.web_view.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)

        self.web_view.setStyleSheet(f"background-color: {Styles.COLORS['background_dark']};")
        chart_layout.addWidget(self.web_view)
        self.layout.addWidget(self.chart_container)

        # Легенда
        self.legend_layout = QHBoxLayout()
        self.legend_layout.setContentsMargins(15, 5, 15, 10)
        self.legend_layout.addStretch()

        for legend_text, color in self.config['legends']:
            legend = QLabel(legend_text)
            legend.setStyleSheet(f"color: {color}; font-size: 12px;")
            self.legend_layout.addWidget(legend)

        self.legend_layout.addStretch()
        self.layout.addLayout(self.legend_layout)

    def _create_html_file(self):
        """Создает HTML файл из шаблона."""
        try:
            # Путь к шаблону HTML
            template_path = resource_path("resources/chart_template.html")

            # Если шаблон не найден, создаем временный файл с HTML кодом
            if not os.path.exists(template_path):
                self._create_fallback_html()
                return

            # Читаем шаблон
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Создаем временный файл для этого графика
            fd, self.html_path = tempfile.mkstemp(suffix=".html", prefix=f"aom_{self.config['type']}_chart_")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self._py_logger.debug(f"HTML файл для графика {self.title} создан: {self.html_path}")

        except Exception as e:
            self._py_logger.error(f"Ошибка при создании HTML файла: {e}")
            self._create_fallback_html()

    def _create_fallback_html(self):
        """Создает резервный HTML файл если шаблон не найден."""
        # Здесь используем упрощенную версию HTML (без встроенного шаблона)
        html_content = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Chart</title></head>
<body>
    <div id="chart-container" style="width:100%;height:100vh;background:#171D33;color:#fff;display:flex;align-items:center;justify-content:center;">
        <div>Шаблон графика не найден</div>
    </div>
</body>
</html>"""

        try:
            fd, self.html_path = tempfile.mkstemp(suffix=".html", prefix="aom_chart_fallback_")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            self._py_logger.error(f"Ошибка при создании резервного HTML: {e}")
            self.html_path = None

    def set_should_animate_once(self):
        """Устанавливает флаг для одноразовой анимации при следующем обновлении."""
        self._should_animate_once = True
        self._py_logger.debug(f"График {self.title}: установлен флаг анимации")

    def update_chart(self, data, force_no_animation=False):
        """Обновляет график с новыми данными."""
        if not data or not self.html_path:
            self._py_logger.warning(f"График {self.title}: нет данных или HTML файла")
            return

        try:
            self._last_data = data

            # Определяем нужна ли анимация
            should_animate = self._should_animate_once and not force_no_animation

            if should_animate:
                self._should_animate_once = False  # Сбрасываем флаг после использования
                self._py_logger.debug(f"График {self.title}: обновление с анимацией")
            else:
                self._py_logger.debug(f"График {self.title}: обновление без анимации")

            # Читаем HTML шаблон
            with open(self.html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Проверяем и подготавливаем данные
            if not data.get("dates") or len(data.get("dates", [])) == 0:
                data = {"dates": []}
                for key in self.config['data_keys']:
                    data[key] = []

            # Заменяем плейсхолдеры
            updated_html = html_content.replace('{CONFIG_PLACEHOLDER}', json.dumps(self.config))
            updated_html = updated_html.replace('{DATA_PLACEHOLDER}', json.dumps(data))
            updated_html = updated_html.replace('{ANIMATE_PLACEHOLDER}', 'true' if should_animate else 'false')

            # Загружаем обновленный HTML
            base_url = QUrl.fromLocalFile(os.path.dirname(self.html_path) + "/")
            self.web_view.setHtml(updated_html, base_url)

            self._is_initialized = True

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении графика {self.title}: {e}")

    def update_data_only(self, data):
        """Обновляет только данные в графике без перезагрузки (для тултипов)."""
        if not self._is_initialized or not data:
            return

        try:
            # Вызываем JavaScript функцию для обновления данных
            js_code = f"if (window.updateChartData) {{ window.updateChartData({json.dumps(data)}); }}"
            self.web_view.page().runJavaScript(js_code)

            self._last_data = data
            self._py_logger.debug(f"График {self.title}: данные обновлены через JavaScript")

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении данных графика {self.title}: {e}")

    def clear(self):
        """Очищает график."""
        empty_data = {"dates": []}
        for key in self.config['data_keys']:
            empty_data[key] = []
        self.update_chart(empty_data, force_no_animation=True)

    def showEvent(self, event):
        """Обработчик показа виджета."""
        super().showEvent(event)
        # При показе виджета обновляем график если есть данные
        if self._last_data and self.isVisible():
            QTimer.singleShot(100, self._refresh_on_show)

    def _refresh_on_show(self):
        """Обновляет график при показе без анимации."""
        if self._last_data:
            self.update_chart(self._last_data, force_no_animation=True)

    def __del__(self):
        """Очистка ресурсов."""
        try:
            if hasattr(self, 'html_path') and self.html_path and os.path.exists(self.html_path):
                os.remove(self.html_path)
        except Exception:
            pass


# Конкретные классы графиков
class BattlesChartWidget(OptimizedChartWidget):
    """Виджет графика побед и поражений."""

    def __init__(self, parent=None):
        super().__init__(ChartConfig.BATTLES, parent)


class KeysChartWidget(OptimizedChartWidget):
    """Виджет графика ключей."""

    def __init__(self, parent=None):
        super().__init__(ChartConfig.KEYS, parent)


class SilverChartWidget(OptimizedChartWidget):
    """Виджет графика серебра."""

    def __init__(self, parent=None):
        super().__init__(ChartConfig.SILVER, parent)