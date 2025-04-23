from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
import os
import json
import tempfile

from gui.styles import Styles


class BattlesChartWidget(QWidget):
    """Виджет для отображения графика побед и поражений."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Настройка лейаута
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок графика
        header_layout = QHBoxLayout()

        title_label = QLabel("Тренд побед и поражений (7 дней)")
        title_label.setObjectName("header")
        header_layout.addWidget(title_label)

        self.layout.addLayout(header_layout)

        # Контейнер для графика
        chart_container = QFrame()
        chart_container.setObjectName("chart-container")
        chart_container.setMinimumHeight(250)
        chart_container.setStyleSheet(f"""
            QFrame#chart-container {{
                background-color: {Styles.COLORS['background_medium']};
                border-radius: 4px;
            }}
        """)

        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(1, 1, 1, 1)

        # Создание и настройка WebEngineView
        self.web_view = QWebEngineView()
        chart_layout.addWidget(self.web_view)

        self.layout.addWidget(chart_container)

        # Легенда для графика
        legend_layout = QHBoxLayout()
        legend_layout.setContentsMargins(15, 10, 15, 15)

        victory_legend = QLabel("● Победы")
        victory_legend.setStyleSheet(f"color: {Styles.COLORS['secondary']};")
        legend_layout.addWidget(victory_legend)

        defeat_legend = QLabel("● Поражения")
        defeat_legend.setStyleSheet(f"color: {Styles.COLORS['accent']};")
        legend_layout.addWidget(defeat_legend)

        win_rate_legend = QLabel("◆ % побед")
        win_rate_legend.setStyleSheet(f"color: {Styles.COLORS['primary']};")
        legend_layout.addWidget(win_rate_legend)

        legend_layout.addStretch()

        self.layout.addLayout(legend_layout)

        # Временный HTML-файл для графика
        self.html_path = None

        # Создать базовый HTML
        self.create_html_template()

    def create_html_template(self):
        """Создает HTML-шаблон с необходимыми библиотеками и контейнером для React."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Battles Chart</title>
            <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
            <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
            <script src="https://unpkg.com/recharts@2.1.9/umd/Recharts.min.js"></script>
            <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    background-color: transparent;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }
                #chart-container {
                    width: 100%;
                    height: 100vh;
                    display: flex;
                }
            </style>
        </head>
        <body>
            <div id="chart-container"></div>

            <script type="text/babel">
                // Данные будут добавлены динамически
                const chartData = CHART_DATA_PLACEHOLDER;

                const BattlesChart = () => {
                    const { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } = Recharts;

                    const transformedData = chartData.dates.map((date, index) => ({
                        date,
                        victories: chartData.victories[index],
                        defeats: chartData.defeats[index],
                        winRate: chartData.win_rates[index]
                    }));

                    return (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={transformedData}
                                margin={{ top: 10, right: 30, left: 0, bottom: 10 }}
                                barGap={4}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="#353E65" />
                                <XAxis dataKey="date" stroke="#9BA0BC" />
                                <YAxis yAxisId="left" stroke="#9BA0BC" />
                                <YAxis yAxisId="right" orientation="right" stroke="#9BA0BC" />
                                <Tooltip 
                                    contentStyle={{ 
                                        backgroundColor: '#2A3158', 
                                        border: '1px solid #353E65',
                                        color: '#FFFFFF'
                                    }} 
                                />
                                <Bar name="Победы" dataKey="victories" yAxisId="left" fill="#42E189" radius={[3, 3, 0, 0]} />
                                <Bar name="Поражения" dataKey="defeats" yAxisId="left" fill="#FF6B6C" radius={[3, 3, 0, 0]} />
                                <Line name="% побед" type="monotone" dataKey="winRate" yAxisId="right" stroke="#3FE0C8" strokeWidth={2} dot={{ r: 4 }} />
                            </BarChart>
                        </ResponsiveContainer>
                    );
                };

                ReactDOM.render(<BattlesChart />, document.getElementById('chart-container'));
            </script>
        </body>
        </html>
        """

        # Создаем временный файл
        fd, self.html_path = tempfile.mkstemp(suffix=".html", prefix="aom_battles_chart_")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def update_chart(self, trend_data):
        """Обновляет график новыми данными."""
        if not trend_data or not self.html_path:
            return

        # Чтение текущего HTML
        with open(self.html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Подготовка данных для JSON
        json_data = json.dumps(trend_data)

        # Замена плейсхолдера данными
        updated_html = html_content.replace('CHART_DATA_PLACEHOLDER', json_data)

        # Запись обновленного HTML
        with open(self.html_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)

        # Загрузка обновленного HTML в WebView
        self.web_view.load(QUrl.fromLocalFile(self.html_path))

    def clear(self):
        """Очищает график."""
        empty_data = {
            "dates": [],
            "victories": [],
            "defeats": [],
            "win_rates": []
        }
        self.update_chart(empty_data)

    def __del__(self):
        """Удаляет временный файл при уничтожении объекта."""
        try:
            if self.html_path and os.path.exists(self.html_path):
                os.remove(self.html_path)
        except:
            pass


class KeysChartWidget(QWidget):
    """Виджет для отображения графика собранных ключей."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Настройка лейаута
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок графика
        header_layout = QHBoxLayout()

        title_label = QLabel("Сбор ключей (7 дней)")
        title_label.setObjectName("header")
        header_layout.addWidget(title_label)

        self.layout.addLayout(header_layout)

        # Контейнер для графика
        chart_container = QFrame()
        chart_container.setObjectName("chart-container")
        chart_container.setMinimumHeight(250)
        chart_container.setStyleSheet(f"""
            QFrame#chart-container {{
                background-color: {Styles.COLORS['background_medium']};
                border-radius: 4px;
            }}
        """)

        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(1, 1, 1, 1)

        # Создание и настройка WebEngineView
        self.web_view = QWebEngineView()
        chart_layout.addWidget(self.web_view)

        self.layout.addWidget(chart_container)

        # Легенда для графика
        legend_layout = QHBoxLayout()
        legend_layout.setContentsMargins(15, 10, 15, 15)

        keys_legend = QLabel("● Собрано ключей")
        keys_legend.setStyleSheet(f"color: {Styles.COLORS['warning']};")
        legend_layout.addWidget(keys_legend)

        keys_per_victory_legend = QLabel("◆ Ключей за победу")
        keys_per_victory_legend.setStyleSheet(f"color: {Styles.COLORS['primary']};")
        legend_layout.addWidget(keys_per_victory_legend)

        legend_layout.addStretch()

        self.layout.addLayout(legend_layout)

        # Временный HTML-файл для графика
        self.html_path = None

        # Создать базовый HTML
        self.create_html_template()

    def create_html_template(self):
        """Создает HTML-шаблон с необходимыми библиотеками и контейнером для React."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Keys Chart</title>
            <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
            <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
            <script src="https://unpkg.com/recharts@2.1.9/umd/Recharts.min.js"></script>
            <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    background-color: transparent;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }
                #chart-container {
                    width: 100%;
                    height: 100vh;
                    display: flex;
                }
            </style>
        </head>
        <body>
            <div id="chart-container"></div>

            <script type="text/babel">
                // Данные будут добавлены динамически
                const chartData = CHART_DATA_PLACEHOLDER;

                const KeysChart = () => {
                    const { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } = Recharts;

                    const transformedData = chartData.dates.map((date, index) => ({
                        date,
                        keys: chartData.keys_collected[index],
                        keysPerVictory: chartData.keys_per_victory[index]
                    }));

                    return (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={transformedData}
                                margin={{ top: 10, right: 30, left: 0, bottom: 10 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="#353E65" />
                                <XAxis dataKey="date" stroke="#9BA0BC" />
                                <YAxis yAxisId="left" stroke="#9BA0BC" />
                                <YAxis yAxisId="right" orientation="right" stroke="#9BA0BC" />
                                <Tooltip 
                                    contentStyle={{ 
                                        backgroundColor: '#2A3158', 
                                        border: '1px solid #353E65',
                                        color: '#FFFFFF'
                                    }} 
                                />
                                <Bar name="Собрано ключей" dataKey="keys" yAxisId="left" fill="#FFB169" radius={[3, 3, 0, 0]} />
                                <Line name="Ключей за победу" type="monotone" dataKey="keysPerVictory" yAxisId="right" stroke="#3FE0C8" strokeWidth={2} dot={{ r: 4 }} />
                            </BarChart>
                        </ResponsiveContainer>
                    );
                };

                ReactDOM.render(<KeysChart />, document.getElementById('chart-container'));
            </script>
        </body>
        </html>
        """

        # Создаем временный файл
        fd, self.html_path = tempfile.mkstemp(suffix=".html", prefix="aom_keys_chart_")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def update_chart(self, trend_data):
        """Обновляет график новыми данными."""
        if not trend_data or not self.html_path:
            return

        # Чтение текущего HTML
        with open(self.html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Подготовка данных для JSON
        json_data = json.dumps(trend_data)

        # Замена плейсхолдера данными
        updated_html = html_content.replace('CHART_DATA_PLACEHOLDER', json_data)

        # Запись обновленного HTML
        with open(self.html_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)

        # Загрузка обновленного HTML в WebView
        self.web_view.load(QUrl.fromLocalFile(self.html_path))

    def clear(self):
        """Очищает график."""
        empty_data = {
            "dates": [],
            "keys_collected": [],
            "keys_per_victory": []
        }
        self.update_chart(empty_data)

    def __del__(self):
        """Удаляет временный файл при уничтожении объекта."""
        try:
            if self.html_path and os.path.exists(self.html_path):
                os.remove(self.html_path)
        except:
            pass