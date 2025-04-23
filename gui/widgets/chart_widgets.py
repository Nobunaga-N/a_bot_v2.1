from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
import os
import json
import tempfile
import logging

from gui.styles import Styles


class BattlesChartWidget(QWidget):
    """Виджет для отображения графика побед и поражений."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._py_logger = logging.getLogger("BotLogger")

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

        # Установка фонового цвета
        self.web_view.setStyleSheet(f"background-color: {Styles.COLORS['background_medium']};")

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
        """Создает HTML-шаблон с улучшенным Canvas-графиком."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Battles Chart</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    background-color: #1E2645;
                    color: #FFFFFF;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    overflow: hidden;
                }
                #chart-container {
                    width: 100%;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    position: relative;
                }
                canvas {
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                }
                .tooltip {
                    position: absolute;
                    display: none;
                    background-color: #2A3158;
                    border: 1px solid #353E65;
                    border-radius: 4px;
                    padding: 8px;
                    color: #FFFFFF;
                    font-size: 12px;
                    pointer-events: none;
                    z-index: 100;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                }
                .no-data {
                    color: #9BA0BC;
                    font-size: 14px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div id="chart-container">
                <canvas id="battles-chart"></canvas>
                <div id="tooltip" class="tooltip"></div>
            </div>

            <script>
                // Данные будут добавлены динамически
                const chartData = CHART_DATA_PLACEHOLDER;

                // Объект для отслеживания состояния графика
                const chartState = {
                    hoveredBar: null,
                    hoveredPoint: null,
                    tooltip: document.getElementById('tooltip'),
                    canvas: null,
                    ctx: null,
                    layout: {
                        padding: null,
                        graphArea: { x: 0, y: 0, width: 0, height: 0 }
                    },
                    mouse: { x: 0, y: 0 },
                    bars: [],
                    points: [],
                    devicePixelRatio: window.devicePixelRatio || 1
                };

                function formatNumber(num) {
                    return num.toLocaleString('ru-RU');
                }

                function getOptimalFontSize() {
                    // Адаптивный размер шрифта в зависимости от ширины канваса
                    const canvas = chartState.canvas;
                    if (!canvas) return 10;

                    const width = canvas.clientWidth;
                    if (width < 400) return 8;
                    if (width < 600) return 9;
                    return 10;
                }

                function calculateOptimalPadding() {
                    // Рассчитываем оптимальные отступы в зависимости от размера канваса
                    const canvas = chartState.canvas;
                    const width = canvas.clientWidth;
                    const height = canvas.clientHeight;

                    let leftPadding = Math.max(40, width * 0.06);
                    let rightPadding = Math.max(35, width * 0.05);
                    let topPadding = Math.max(20, height * 0.08);
                    let bottomPadding = Math.max(30, height * 0.12);

                    return {
                        left: leftPadding,
                        right: rightPadding, 
                        top: topPadding,
                        bottom: bottomPadding
                    };
                }

                function drawChart() {
                    const canvas = document.getElementById('battles-chart');
                    const ctx = canvas.getContext('2d');

                    chartState.canvas = canvas;
                    chartState.ctx = ctx;

                    // Адаптивные размеры для высокого DPI
                    const dpr = chartState.devicePixelRatio;
                    const rect = canvas.getBoundingClientRect();

                    canvas.width = rect.width * dpr;
                    canvas.height = rect.height * dpr;

                    ctx.scale(dpr, dpr);
                    canvas.style.width = rect.width + 'px';
                    canvas.style.height = rect.height + 'px';

                    // Проверка наличия данных
                    if (!chartData || !chartData.dates || chartData.dates.length === 0) {
                        ctx.font = '14px Arial';
                        ctx.fillStyle = '#9BA0BC';
                        ctx.textAlign = 'center';
                        ctx.fillText('Нет данных для отображения', canvas.width / (2 * dpr), canvas.height / (2 * dpr));
                        return;
                    }

                    // Рассчитываем оптимальные отступы
                    chartState.layout.padding = calculateOptimalPadding();
                    const padding = chartState.layout.padding;

                    const graphWidth = rect.width - padding.left - padding.right;
                    const graphHeight = rect.height - padding.top - padding.bottom;

                    chartState.layout.graphArea = {
                        x: padding.left,
                        y: padding.top,
                        width: graphWidth,
                        height: graphHeight
                    };

                    // Очистка canvas
                    ctx.clearRect(0, 0, rect.width, rect.height);

                    // Находим максимальные значения для масштабирования
                    let maxBattles = 0;
                    let maxRate = 0;

                    for (let i = 0; i < chartData.dates.length; i++) {
                        const victories = chartData.victories[i] || 0;
                        const defeats = chartData.defeats[i] || 0;
                        const total = victories + defeats;
                        const rate = chartData.win_rates[i] || 0;

                        maxBattles = Math.max(maxBattles, total);
                        maxRate = Math.max(maxRate, rate);
                    }

                    // Защита от нулевых максимумов
                    maxBattles = maxBattles || 10;
                    maxRate = maxRate || 100;

                    // Рисуем оси
                    drawAxes(ctx, padding, graphWidth, graphHeight, maxBattles, maxRate, rect.width, rect.height);

                    // Сбрасываем массивы элементов для интерактивности
                    chartState.bars = [];
                    chartState.points = [];

                    // Отрисовка столбцов побед и поражений
                    drawBars(ctx, padding, graphWidth, graphHeight, maxBattles, rect.width, rect.height);

                    // Отрисовка графика процента побед
                    drawWinRateLine(ctx, padding, graphWidth, graphHeight, maxRate);
                }

                function drawAxes(ctx, padding, graphWidth, graphHeight, maxBattles, maxRate, canvasWidth, canvasHeight) {
                    const baselineY = canvasHeight - padding.bottom;
                    const baselineX = padding.left;
                    const fontSize = getOptimalFontSize();

                    // Фон области графика
                    ctx.fillStyle = '#171D33';
                    ctx.fillRect(padding.left, padding.top, graphWidth, graphHeight);

                    // Отрисовка сетки
                    ctx.strokeStyle = '#353E65';
                    ctx.lineWidth = 1;
                    ctx.beginPath();

                    // Определяем интервалы для шкалы боев
                    const battleStep = calculateAxisStep(maxBattles);
                    const numBattleLines = Math.floor(maxBattles / battleStep) + 1;

                    // Горизонтальные линии сетки (шкала боев)
                    for (let i = 0; i < numBattleLines; i++) {
                        const value = i * battleStep;
                        const y = baselineY - (value / maxBattles) * graphHeight;

                        ctx.moveTo(baselineX, y);
                        ctx.lineTo(baselineX + graphWidth, y);

                        // Подпись значения оси Y (бои)
                        if (canvasWidth > 300) {  // Только для достаточно широких экранов
                            ctx.fillStyle = '#9BA0BC';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'right';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(value, baselineX - 5, y);
                        }
                    }

                    // Подпись оси Y для боев (при достаточной высоте)
                    if (canvasHeight > 200) {
                        ctx.save();
                        ctx.translate(baselineX - 25, padding.top + graphHeight / 2);
                        ctx.rotate(-Math.PI / 2);
                        ctx.font = `${fontSize + 1}px Arial`;
                        ctx.textAlign = 'center';
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fillText('Бои', 0, 0);
                        ctx.restore();
                    }

                    // Вертикальные линии сетки и подписи дат
                    const dataLength = chartData.dates.length;
                    const availableWidth = graphWidth / dataLength;
                    let skipFactor = 1;

                    // Определяем, нужно ли пропускать даты
                    if (availableWidth < 50) skipFactor = 2;
                    if (availableWidth < 30) skipFactor = 3;

                    for (let i = 0; i < dataLength; i++) {
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));

                        ctx.moveTo(x, padding.top);
                        ctx.lineTo(x, baselineY);

                        // Подпись даты (пропускаем некоторые для экономии места)
                        if (i % skipFactor === 0 || i === dataLength - 1) {
                            ctx.fillStyle = '#9BA0BC';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'top';
                            ctx.fillText(chartData.dates[i], x, baselineY + 5);
                        }
                    }

                    ctx.stroke();

                    // Отрисовка правой оси Y (процент побед)
                    ctx.beginPath();
                    ctx.strokeStyle = '#353E65';

                    // Определяем интервалы для шкалы процентов
                    const rateStep = 20; // Шаг 20%
                    const numRateLines = 6; // 0%, 20%, 40%, 60%, 80%, 100%

                    const rightAxisX = baselineX + graphWidth;

                    // Отрисовка делений процента побед
                    for (let i = 0; i < numRateLines; i++) {
                        const value = i * rateStep;
                        const y = baselineY - (value / 100) * graphHeight;

                        if (canvasWidth > 400) {  // Только для достаточно широких экранов
                            // Подпись значения оси Y (процент)
                            ctx.fillStyle = '#9BA0BC';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'left';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(value + '%', rightAxisX + 5, y);
                        }
                    }

                    // Подпись оси Y для процента побед (при достаточной высоте)
                    if (canvasHeight > 200 && canvasWidth > 400) {
                        ctx.save();
                        ctx.translate(rightAxisX + 30, padding.top + graphHeight / 2);
                        ctx.rotate(-Math.PI / 2);
                        ctx.font = `${fontSize + 1}px Arial`;
                        ctx.textAlign = 'center';
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fillText('% побед', 0, 0);
                        ctx.restore();
                    }

                    ctx.stroke();
                }

                function drawBars(ctx, padding, graphWidth, graphHeight, maxBattles, canvasWidth, canvasHeight) {
                    const baselineY = canvasHeight - padding.bottom;
                    const dataLength = chartData.dates.length;

                    // Вычисляем оптимальную ширину столбцов
                    const maxBarWidth = 40;
                    let barWidth = Math.min((graphWidth / dataLength) * 0.7, maxBarWidth);
                    const barGap = Math.max(1, Math.min(2, barWidth * 0.1));
                    const halfBarWidth = barWidth / 2;
                    const singleBarWidth = (barWidth - barGap) / 2;

                    for (let i = 0; i < dataLength; i++) {
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));
                        const barX = x - halfBarWidth;

                        const victories = chartData.victories[i] || 0;
                        const defeats = chartData.defeats[i] || 0;

                        // Вычисляем высоту столбцов
                        const victoryHeight = (victories / maxBattles) * graphHeight;
                        const defeatHeight = (defeats / maxBattles) * graphHeight;

                        // Рисуем столбец побед
                        ctx.fillStyle = '#42E189'; // Зеленый цвет для побед
                        const victoryRect = {
                            x: barX,
                            y: baselineY - victoryHeight,
                            width: singleBarWidth,
                            height: Math.max(1, victoryHeight), // Минимальная высота 1px
                            type: 'victory',
                            value: victories,
                            date: chartData.dates[i],
                            index: i
                        };

                        chartState.bars.push(victoryRect);
                        ctx.fillRect(victoryRect.x, victoryRect.y, victoryRect.width, victoryRect.height);

                        // Рисуем столбец поражений
                        ctx.fillStyle = '#FF6B6C'; // Красный цвет для поражений
                        const defeatRect = {
                            x: barX + singleBarWidth + barGap,
                            y: baselineY - defeatHeight,
                            width: singleBarWidth,
                            height: Math.max(1, defeatHeight), // Минимальная высота 1px
                            type: 'defeat',
                            value: defeats,
                            date: chartData.dates[i],
                            index: i
                        };

                        chartState.bars.push(defeatRect);
                        ctx.fillRect(defeatRect.x, defeatRect.y, defeatRect.width, defeatRect.height);
                    }
                }

                function drawWinRateLine(ctx, padding, graphWidth, graphHeight, maxRate) {
                    const baselineY = ctx.canvas.height / chartState.devicePixelRatio - padding.bottom;
                    const dataLength = chartData.dates.length;

                    ctx.strokeStyle = '#3FE0C8'; // Цвет процента побед
                    ctx.lineWidth = 2;
                    ctx.beginPath();

                    // Сбрасываем массив точек
                    chartState.points = [];

                    let firstPointDrawn = false;

                    for (let i = 0; i < dataLength; i++) {
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));
                        const winRate = chartData.win_rates[i] || 0;

                        // Используем 100 как максимум для процентов
                        const y = baselineY - (winRate / 100) * graphHeight;

                        // Сохраняем точку для интерактивности
                        const pointObj = {
                            x: x,
                            y: y,
                            radius: 4,
                            value: winRate,
                            date: chartData.dates[i],
                            index: i
                        };

                        chartState.points.push(pointObj);

                        // Рисуем линию только если есть данные (winRate > 0)
                        if (winRate > 0) {
                            if (!firstPointDrawn) {
                                ctx.moveTo(x, y);
                                firstPointDrawn = true;
                            } else {
                                ctx.lineTo(x, y);
                            }
                        }
                    }

                    ctx.stroke();

                    // Рисуем точки на графике процента побед
                    ctx.fillStyle = '#3FE0C8';
                    for (const point of chartState.points) {
                        if (point.value > 0) {  // Рисуем точки только если есть данные
                            ctx.beginPath();
                            ctx.arc(point.x, point.y, point.radius, 0, Math.PI * 2);
                            ctx.fill();
                        }
                    }
                }

                function checkForInteractions(event) {
                    const canvas = chartState.canvas;
                    const rect = canvas.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const y = event.clientY - rect.top;

                    chartState.mouse = { x, y };

                    // Проверяем наведение на столбцы
                    let hoveredBar = null;
                    for (const bar of chartState.bars) {
                        if (
                            x >= bar.x && 
                            x <= bar.x + bar.width && 
                            y >= bar.y && 
                            y <= bar.y + bar.height
                        ) {
                            hoveredBar = bar;
                            break;
                        }
                    }

                    // Проверяем наведение на точки линии
                    let hoveredPoint = null;
                    for (const point of chartState.points) {
                        if (point.value === 0) continue; // Пропускаем точки без данных

                        const dx = x - point.x;
                        const dy = y - point.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);

                        if (distance <= point.radius + 2) {
                            hoveredPoint = point;
                            break;
                        }
                    }

                    // Обновляем подсказку
                    if (hoveredBar) {
                        const tooltip = chartState.tooltip;
                        tooltip.style.display = 'block';

                        // Позиционируем подсказку с учетом границ экрана
                        const tooltipX = Math.min(x + 10, canvas.clientWidth - 150);
                        const tooltipY = Math.max(y - 10, 10);

                        tooltip.style.left = tooltipX + 'px';
                        tooltip.style.top = tooltipY + 'px';

                        const typeText = hoveredBar.type === 'victory' ? 'Победы' : 'Поражения';
                        const valueText = formatNumber(hoveredBar.value);

                        tooltip.innerHTML = `
                            <strong>${hoveredBar.date}</strong><br>
                            ${typeText}: ${valueText}
                        `;
                    } else if (hoveredPoint) {
                        const tooltip = chartState.tooltip;
                        tooltip.style.display = 'block';

                        // Позиционируем подсказку с учетом границ экрана
                        const tooltipX = Math.min(x + 10, canvas.clientWidth - 150);
                        const tooltipY = Math.max(y - 10, 10);

                        tooltip.style.left = tooltipX + 'px';
                        tooltip.style.top = tooltipY + 'px';

                        tooltip.innerHTML = `
                            <strong>${hoveredPoint.date}</strong><br>
                            Процент побед: ${hoveredPoint.value.toFixed(1)}%
                        `;
                    } else {
                        chartState.tooltip.style.display = 'none';
                    }

                    // Обновляем состояние графика
                    chartState.hoveredBar = hoveredBar;
                    chartState.hoveredPoint = hoveredPoint;
                }

                function calculateAxisStep(maxValue) {
                    // Помогает определить удобный шаг для оси
                    if (maxValue <= 5) return 1;
                    if (maxValue <= 20) return 5;
                    if (maxValue <= 50) return 10;
                    if (maxValue <= 100) return 20;
                    if (maxValue <= 500) return 100;

                    // Для больших значений
                    const magnitude = Math.pow(10, Math.floor(Math.log10(maxValue)));
                    return Math.ceil(maxValue / 5 / magnitude) * magnitude;
                }

                // Обработчики событий
                function setupEventListeners() {
                    const canvas = document.getElementById('battles-chart');

                    canvas.addEventListener('mousemove', checkForInteractions);

                    canvas.addEventListener('mouseleave', function() {
                        chartState.tooltip.style.display = 'none';
                    });

                    // Обработка изменения размера
                    window.addEventListener('resize', function() {
                        drawChart();
                    });
                }

                // Инициализация
                window.onload = function() {
                    drawChart();
                    setupEventListeners();
                };
            </script>
        </body>
        </html>
        """

        try:
            # Создаем временный файл
            fd, self.html_path = tempfile.mkstemp(suffix=".html", prefix="aom_battles_chart_")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self._py_logger.debug(f"Создан шаблон графика побед: {self.html_path}")
        except Exception as e:
            self._py_logger.error(f"Ошибка при создании HTML-шаблона графика побед: {e}")

    def update_chart(self, trend_data):
        """Обновляет график новыми данными."""
        if not trend_data or not self.html_path:
            self._py_logger.warning("Невозможно обновить график: нет данных или шаблона")
            return

        try:
            # Чтение текущего HTML
            with open(self.html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Проверка данных
            if not trend_data.get("dates") or len(trend_data.get("dates", [])) == 0:
                self._py_logger.warning("Пустой набор данных для графика побед")

                # Создаем пустой набор данных для отображения сообщения
                trend_data = {
                    "dates": [],
                    "victories": [],
                    "defeats": [],
                    "win_rates": []
                }

            # Подготовка данных для JSON
            json_data = json.dumps(trend_data)

            # Замена плейсхолдера данными
            updated_html = html_content.replace('CHART_DATA_PLACEHOLDER', json_data)

            # Запись обновленного HTML
            with open(self.html_path, 'w', encoding='utf-8') as f:
                f.write(updated_html)

            # Загрузка обновленного HTML в WebView
            self.web_view.load(QUrl.fromLocalFile(self.html_path))
            self._py_logger.debug("График побед обновлен")

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении графика побед: {e}")

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
        except Exception as e:
            if hasattr(self, '_py_logger'):
                self._py_logger.error(f"Ошибка при удалении временного файла: {e}")


class KeysChartWidget(QWidget):
    """Виджет для отображения графика собранных ключей."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._py_logger = logging.getLogger("BotLogger")

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

        # Установка фонового цвета
        self.web_view.setStyleSheet(f"background-color: {Styles.COLORS['background_medium']};")

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
        """Создает HTML-шаблон с улучшенным Canvas-графиком."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Keys Chart</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    background-color: #1E2645;
                    color: #FFFFFF;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    overflow: hidden;
                }
                #chart-container {
                    width: 100%;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    position: relative;
                }
                canvas {
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                }
                .tooltip {
                    position: absolute;
                    display: none;
                    background-color: #2A3158;
                    border: 1px solid #353E65;
                    border-radius: 4px;
                    padding: 8px;
                    color: #FFFFFF;
                    font-size: 12px;
                    pointer-events: none;
                    z-index: 100;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                }
                .no-data {
                    color: #9BA0BC;
                    font-size: 14px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div id="chart-container">
                <canvas id="keys-chart"></canvas>
                <div id="tooltip" class="tooltip"></div>
            </div>

            <script>
                // Данные будут добавлены динамически
                const chartData = CHART_DATA_PLACEHOLDER;

                // Объект для отслеживания состояния графика
                const chartState = {
                    hoveredBar: null,
                    hoveredPoint: null,
                    tooltip: document.getElementById('tooltip'),
                    canvas: null,
                    ctx: null,
                    layout: {
                        padding: null,
                        graphArea: { x: 0, y: 0, width: 0, height: 0 }
                    },
                    mouse: { x: 0, y: 0 },
                    bars: [],
                    points: [],
                    devicePixelRatio: window.devicePixelRatio || 1
                };

                function formatNumber(num) {
                    return num.toLocaleString('ru-RU');
                }

                function getOptimalFontSize() {
                    // Адаптивный размер шрифта в зависимости от ширины канваса
                    const canvas = chartState.canvas;
                    if (!canvas) return 10;

                    const width = canvas.clientWidth;
                    if (width < 400) return 8;
                    if (width < 600) return 9;
                    return 10;
                }

                function calculateOptimalPadding() {
                    // Рассчитываем оптимальные отступы в зависимости от размера канваса
                    const canvas = chartState.canvas;
                    const width = canvas.clientWidth;
                    const height = canvas.clientHeight;

                    let leftPadding = Math.max(40, width * 0.06);
                    let rightPadding = Math.max(35, width * 0.05);
                    let topPadding = Math.max(20, height * 0.08);
                    let bottomPadding = Math.max(30, height * 0.12);

                    return {
                        left: leftPadding,
                        right: rightPadding, 
                        top: topPadding,
                        bottom: bottomPadding
                    };
                }

                function drawChart() {
                    const canvas = document.getElementById('keys-chart');
                    const ctx = canvas.getContext('2d');

                    chartState.canvas = canvas;
                    chartState.ctx = ctx;

                    // Адаптивные размеры для высокого DPI
                    const dpr = chartState.devicePixelRatio;
                    const rect = canvas.getBoundingClientRect();

                    canvas.width = rect.width * dpr;
                    canvas.height = rect.height * dpr;

                    ctx.scale(dpr, dpr);
                    canvas.style.width = rect.width + 'px';
                    canvas.style.height = rect.height + 'px';

                    // Проверка наличия данных
                    if (!chartData || !chartData.dates || chartData.dates.length === 0) {
                        ctx.font = '14px Arial';
                        ctx.fillStyle = '#9BA0BC';
                        ctx.textAlign = 'center';
                        ctx.fillText('Нет данных для отображения', canvas.width / (2 * dpr), canvas.height / (2 * dpr));
                        return;
                    }

                    // Рассчитываем оптимальные отступы
                    chartState.layout.padding = calculateOptimalPadding();
                    const padding = chartState.layout.padding;

                    const graphWidth = rect.width - padding.left - padding.right;
                    const graphHeight = rect.height - padding.top - padding.bottom;

                    chartState.layout.graphArea = {
                        x: padding.left,
                        y: padding.top,
                        width: graphWidth,
                        height: graphHeight
                    };

                    // Очистка canvas
                    ctx.clearRect(0, 0, rect.width, rect.height);

                    // Находим максимальные значения для масштабирования
                    let maxKeys = 0;
                    let maxKeyPerVictory = 0;

                    for (let i = 0; i < chartData.dates.length; i++) {
                        const keys = chartData.keys_collected[i] || 0;
                        const keysPerVictory = chartData.keys_per_victory[i] || 0;

                        maxKeys = Math.max(maxKeys, keys);
                        maxKeyPerVictory = Math.max(maxKeyPerVictory, keysPerVictory);
                    }

                    // Защита от нулевых максимумов
                    maxKeys = maxKeys || 10;
                    maxKeyPerVictory = maxKeyPerVictory || 10;

                    // Рисуем оси
                    drawAxes(ctx, padding, graphWidth, graphHeight, maxKeys, maxKeyPerVictory, rect.width, rect.height);

                    // Сбрасываем массивы элементов для интерактивности
                    chartState.bars = [];
                    chartState.points = [];

                    // Отрисовка столбцов собранных ключей
                    drawBars(ctx, padding, graphWidth, graphHeight, maxKeys, rect.width, rect.height);

                    // Отрисовка графика ключей за победу
                    drawKeysPerVictoryLine(ctx, padding, graphWidth, graphHeight, maxKeyPerVictory);
                }

                function drawAxes(ctx, padding, graphWidth, graphHeight, maxKeys, maxKeyPerVictory, canvasWidth, canvasHeight) {
                    const baselineY = canvasHeight - padding.bottom;
                    const baselineX = padding.left;
                    const fontSize = getOptimalFontSize();

                    // Фон области графика
                    ctx.fillStyle = '#171D33';
                    ctx.fillRect(padding.left, padding.top, graphWidth, graphHeight);

                    // Отрисовка сетки
                    ctx.strokeStyle = '#353E65';
                    ctx.lineWidth = 1;
                    ctx.beginPath();

                    // Определяем интервалы для шкалы ключей
                    const keyStep = calculateAxisStep(maxKeys);
                    const numKeyLines = Math.floor(maxKeys / keyStep) + 1;

                    // Горизонтальные линии сетки (шкала ключей)
                    for (let i = 0; i < numKeyLines; i++) {
                        const value = i * keyStep;
                        const y = baselineY - (value / maxKeys) * graphHeight;

                        ctx.moveTo(baselineX, y);
                        ctx.lineTo(baselineX + graphWidth, y);

                        // Подпись значения оси Y (ключи)
                        if (canvasWidth > 300) {  // Только для достаточно широких экранов
                            ctx.fillStyle = '#9BA0BC';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'right';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(formatNumber(value), baselineX - 5, y);
                        }
                    }

                    // Подпись оси Y для ключей (при достаточной высоте)
                    if (canvasHeight > 200) {
                        ctx.save();
                        ctx.translate(baselineX - 25, padding.top + graphHeight / 2);
                        ctx.rotate(-Math.PI / 2);
                        ctx.font = `${fontSize + 1}px Arial`;
                        ctx.textAlign = 'center';
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fillText('Ключи', 0, 0);
                        ctx.restore();
                    }

                    // Вертикальные линии сетки и подписи дат
                    const dataLength = chartData.dates.length;
                    const availableWidth = graphWidth / dataLength;
                    let skipFactor = 1;

                    // Определяем, нужно ли пропускать даты
                    if (availableWidth < 50) skipFactor = 2;
                    if (availableWidth < 30) skipFactor = 3;

                    for (let i = 0; i < dataLength; i++) {
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));

                        ctx.moveTo(x, padding.top);
                        ctx.lineTo(x, baselineY);

                        // Подпись даты (пропускаем некоторые для экономии места)
                        if (i % skipFactor === 0 || i === dataLength - 1) {
                            ctx.fillStyle = '#9BA0BC';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'top';
                            ctx.fillText(chartData.dates[i], x, baselineY + 5);
                        }
                    }

                    ctx.stroke();

                    // Отрисовка правой оси Y (ключей за победу)
                    ctx.beginPath();
                    ctx.strokeStyle = '#353E65';

                    // Определяем интервалы для шкалы ключей за победу
                    const kpvStep = calculateAxisStep(maxKeyPerVictory);
                    const numKpvLines = Math.floor(maxKeyPerVictory / kpvStep) + 1;

                    const rightAxisX = baselineX + graphWidth;

                    // Отрисовка делений ключей за победу
                    for (let i = 0; i < numKpvLines; i++) {
                        const value = i * kpvStep;
                        const y = baselineY - (value / maxKeyPerVictory) * graphHeight;

                        if (canvasWidth > 400) {  // Только для достаточно широких экранов
                            // Подпись значения оси Y (ключей за победу)
                            ctx.fillStyle = '#9BA0BC';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'left';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(value.toFixed(value < 1 ? 1 : 0), rightAxisX + 5, y);
                        }
                    }

                    // Подпись оси Y для ключей за победу (при достаточной высоте)
                    if (canvasHeight > 200 && canvasWidth > 400) {
                        ctx.save();
                        ctx.translate(rightAxisX + 30, padding.top + graphHeight / 2);
                        ctx.rotate(-Math.PI / 2);
                        ctx.font = `${fontSize + 1}px Arial`;
                        ctx.textAlign = 'center';
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fillText('Ключей/победа', 0, 0);
                        ctx.restore();
                    }

                    ctx.stroke();
                }

                function drawBars(ctx, padding, graphWidth, graphHeight, maxKeys, canvasWidth, canvasHeight) {
                    const baselineY = canvasHeight - padding.bottom;
                    const dataLength = chartData.dates.length;

                    // Вычисляем оптимальную ширину столбцов
                    const maxBarWidth = 40;
                    let barWidth = Math.min((graphWidth / dataLength) * 0.7, maxBarWidth);

                    for (let i = 0; i < dataLength; i++) {
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));
                        const barX = x - (barWidth / 2);

                        const keys = chartData.keys_collected[i] || 0;

                        // Вычисляем высоту столбца
                        const keyHeight = (keys / maxKeys) * graphHeight;

                        // Рисуем столбец ключей
                        ctx.fillStyle = '#FFB169'; // Оранжевый цвет для ключей
                        const keyRect = {
                            x: barX,
                            y: baselineY - keyHeight,
                            width: barWidth,
                            height: Math.max(1, keyHeight), // Минимальная высота 1px
                            value: keys,
                            date: chartData.dates[i],
                            index: i
                        };

                        chartState.bars.push(keyRect);
                        ctx.fillRect(keyRect.x, keyRect.y, keyRect.width, keyRect.height);
                    }
                }

                function drawKeysPerVictoryLine(ctx, padding, graphWidth, graphHeight, maxKeyPerVictory) {
                    const baselineY = ctx.canvas.height / chartState.devicePixelRatio - padding.bottom;
                    const dataLength = chartData.dates.length;

                    ctx.strokeStyle = '#3FE0C8'; // Цвет линии ключей за победу
                    ctx.lineWidth = 2;
                    ctx.beginPath();

                    // Сбрасываем массив точек
                    chartState.points = [];

                    let firstPointDrawn = false;

                    for (let i = 0; i < dataLength; i++) {
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));
                        const keysPerVictory = chartData.keys_per_victory[i] || 0;

                        const y = baselineY - (keysPerVictory / maxKeyPerVictory) * graphHeight;

                        // Сохраняем точку для интерактивности
                        const pointObj = {
                            x: x,
                            y: y,
                            radius: 4,
                            value: keysPerVictory,
                            date: chartData.dates[i],
                            index: i
                        };

                        chartState.points.push(pointObj);

                        // Рисуем линию только если есть данные (keysPerVictory > 0)
                        if (keysPerVictory > 0) {
                            if (!firstPointDrawn) {
                                ctx.moveTo(x, y);
                                firstPointDrawn = true;
                            } else {
                                ctx.lineTo(x, y);
                            }
                        }
                    }

                    ctx.stroke();

                    // Рисуем точки на графике ключей за победу
                    ctx.fillStyle = '#3FE0C8';
                    for (const point of chartState.points) {
                        if (point.value > 0) {  // Рисуем точки только если есть данные
                            ctx.beginPath();
                            ctx.arc(point.x, point.y, point.radius, 0, Math.PI * 2);
                            ctx.fill();
                        }
                    }
                }

                function checkForInteractions(event) {
                    const canvas = chartState.canvas;
                    const rect = canvas.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const y = event.clientY - rect.top;

                    chartState.mouse = { x, y };

                    // Проверяем наведение на столбцы
                    let hoveredBar = null;
                    for (const bar of chartState.bars) {
                        if (
                            x >= bar.x && 
                            x <= bar.x + bar.width && 
                            y >= bar.y && 
                            y <= bar.y + bar.height
                        ) {
                            hoveredBar = bar;
                            break;
                        }
                    }

                    // Проверяем наведение на точки линии
                    let hoveredPoint = null;
                    for (const point of chartState.points) {
                        if (point.value === 0) continue; // Пропускаем точки без данных

                        const dx = x - point.x;
                        const dy = y - point.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);

                        if (distance <= point.radius + 2) {
                            hoveredPoint = point;
                            break;
                        }
                    }

                    // Обновляем подсказку
                    if (hoveredBar) {
                        const tooltip = chartState.tooltip;
                        tooltip.style.display = 'block';

                        // Позиционируем подсказку с учетом границ экрана
                        const tooltipX = Math.min(x + 10, canvas.clientWidth - 150);
                        const tooltipY = Math.max(y - 10, 10);

                        tooltip.style.left = tooltipX + 'px';
                        tooltip.style.top = tooltipY + 'px';

                        tooltip.innerHTML = `
                            <strong>${hoveredBar.date}</strong><br>
                            Собрано ключей: ${formatNumber(hoveredBar.value)}
                        `;
                    } else if (hoveredPoint) {
                        const tooltip = chartState.tooltip;
                        tooltip.style.display = 'block';

                        // Позиционируем подсказку с учетом границ экрана
                        const tooltipX = Math.min(x + 10, canvas.clientWidth - 150);
                        const tooltipY = Math.max(y - 10, 10);

                        tooltip.style.left = tooltipX + 'px';
                        tooltip.style.top = tooltipY + 'px';

                        tooltip.innerHTML = `
                            <strong>${hoveredPoint.date}</strong><br>
                            Ключей за победу: ${hoveredPoint.value.toFixed(1)}
                        `;
                    } else {
                        chartState.tooltip.style.display = 'none';
                    }

                    // Обновляем состояние графика
                    chartState.hoveredBar = hoveredBar;
                    chartState.hoveredPoint = hoveredPoint;
                }

                function calculateAxisStep(maxValue) {
                    // Помогает определить удобный шаг для оси
                    if (maxValue <= 5) return 1;
                    if (maxValue <= 20) return 5;
                    if (maxValue <= 50) return 10;
                    if (maxValue <= 100) return 20;
                    if (maxValue <= 500) return 100;
                    if (maxValue <= 1000) return 200;

                    // Для больших значений
                    const magnitude = Math.pow(10, Math.floor(Math.log10(maxValue)));
                    return Math.ceil(maxValue / 5 / magnitude) * magnitude;
                }

                // Обработчики событий
                function setupEventListeners() {
                    const canvas = document.getElementById('keys-chart');

                    canvas.addEventListener('mousemove', checkForInteractions);

                    canvas.addEventListener('mouseleave', function() {
                        chartState.tooltip.style.display = 'none';
                    });

                    // Обработка изменения размера
                    window.addEventListener('resize', function() {
                        drawChart();
                    });
                }

                // Инициализация
                window.onload = function() {
                    drawChart();
                    setupEventListeners();
                };
            </script>
        </body>
        </html>
        """

        try:
            # Создаем временный файл
            fd, self.html_path = tempfile.mkstemp(suffix=".html", prefix="aom_keys_chart_")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self._py_logger.debug(f"Создан шаблон графика ключей: {self.html_path}")
        except Exception as e:
            self._py_logger.error(f"Ошибка при создании HTML-шаблона графика ключей: {e}")

    def update_chart(self, trend_data):
        """Обновляет график новыми данными."""
        if not trend_data or not self.html_path:
            self._py_logger.warning("Невозможно обновить график: нет данных или шаблона")
            return

        try:
            # Чтение текущего HTML
            with open(self.html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Проверка данных
            if not trend_data.get("dates") or len(trend_data.get("dates", [])) == 0:
                self._py_logger.warning("Пустой набор данных для графика ключей")

                # Создаем пустой набор данных для отображения сообщения
                trend_data = {
                    "dates": [],
                    "keys_collected": [],
                    "keys_per_victory": []
                }

            # Подготовка данных для JSON
            json_data = json.dumps(trend_data)

            # Замена плейсхолдера данными
            updated_html = html_content.replace('CHART_DATA_PLACEHOLDER', json_data)

            # Запись обновленного HTML
            with open(self.html_path, 'w', encoding='utf-8') as f:
                f.write(updated_html)

            # Загрузка обновленного HTML в WebView
            self.web_view.load(QUrl.fromLocalFile(self.html_path))
            self._py_logger.debug("График ключей обновлен")

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении графика ключей: {e}")

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
        except Exception as e:
            if hasattr(self, '_py_logger'):
                self._py_logger.error(f"Ошибка при удалении временного файла: {e}")