from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QUrl, Qt, QSize, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
import os
import json
import tempfile
import logging

from gui.styles import Styles


class ChartConfig:
    """Конфигурация для разных типов графиков."""

    BATTLES = {
        'title': 'Тренд побед и поражений (7 дней)',
        'chart_id': 'battles-chart',
        'type': 'dual_bars',  # два столбца
        'data_keys': ['victories', 'defeats'],
        'colors': {
            'primary': '#42E189',  # победы
            'secondary': '#FF6B6C',  # поражения
            'tooltip': '#42E189'
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
        'type': 'single_bar',  # один столбец
        'data_keys': ['keys_collected'],
        'colors': {
            'primary': '#FFB169',
            'tooltip': '#FFB169'
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
            'tooltip': '#3FE0C8'
        },
        'legends': [
            ('● Собрано серебра', Styles.COLORS['primary'])
        ],
        'formatter': 'silver',  # специальное форматирование
        'axis_step_func': 'calculateSilverAxisStep'
    }


class ResponsiveChartWidget(QWidget):
    """Базовый класс для отзывчивых графиков с общей логикой."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._py_logger = logging.getLogger("BotLogger")
        self.config = config
        self.title = config['title']

        # Настройка лейаута
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Заголовок графика
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
                border-radius: 0;
                border: none;
            }}
        """)

        chart_layout = QVBoxLayout(self.chart_container)
        chart_layout.setContentsMargins(1, 1, 1, 1)

        # Создание и настройка WebEngineView
        self.web_view = QWebEngineView()
        settings = self.web_view.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)

        self.web_view.setStyleSheet(f"background-color: {Styles.COLORS['background_dark']};")

        chart_layout.addWidget(self.web_view)
        self.layout.addWidget(self.chart_container)

        # Легенда для графика
        self.legend_layout = QHBoxLayout()
        self.legend_layout.setContentsMargins(15, 5, 15, 10)
        self.legend_layout.addStretch()

        # Добавляем легенды из конфигурации
        for legend_text, color in config['legends']:
            legend = QLabel(legend_text)
            legend.setStyleSheet(f"color: {color}; font-size: 12px;")
            self.legend_layout.addWidget(legend)

        self.legend_layout.addStretch()
        self.layout.addLayout(self.legend_layout)

        # Таймер для оптимизации отрисовки при изменении размера
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.handle_resize)

        # Переменная для хранения последних данных
        self.last_data = None

        # Временный HTML-файл для графика
        self.html_path = None

        # Создать HTML шаблон
        self.create_html_template()

    def create_html_template(self):
        """Создает HTML-шаблон с универсальным графиком."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.config['title']}</title>
            <style>
                :root {{
                    --bg-color: #171D33;
                    --grid-color: #28304d;
                    --text-color: #FFFFFF;
                    --text-secondary: #9BA0BC;
                    --primary-color: {self.config['colors']['primary']};
                    --secondary-color: {self.config['colors'].get('secondary', self.config['colors']['primary'])};
                    --tooltip-bg: #2A3158;
                    --tooltip-border: #353E65;
                }}

                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    margin: 0;
                    padding: 0;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    font-family: 'Segoe UI', Arial, sans-serif;
                    overflow: hidden;
                    height: 100vh;
                    width: 100vw;
                }}

                #chart-container {{
                    width: 100%;
                    height: 100%;
                    position: relative;
                }}

                canvas {{
                    width: 100%;
                    height: 100%;
                    position: absolute;
                    top: 0;
                    left: 0;
                }}

                .tooltip {{
                    position: absolute;
                    display: none;
                    background-color: var(--tooltip-bg);
                    border: 1px solid var(--tooltip-border);
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: var(--text-color);
                    font-size: 12px;
                    pointer-events: none;
                    z-index: 100;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                    transition: all 0.1s ease;
                    max-width: 200px;
                    word-wrap: break-word;
                }}

                .tooltip strong {{
                    display: block;
                    margin-bottom: 4px;
                    color: var(--primary-color);
                }}

                .no-data {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: var(--text-secondary);
                    font-size: 14px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div id="chart-container">
                <canvas id="{self.config['chart_id']}"></canvas>
                <div id="tooltip" class="tooltip"></div>
                <div id="no-data" class="no-data" style="display:none;">Нет данных для отображения</div>
            </div>

            <script>
                // Конфигурация графика
                const CONFIG = {json.dumps(self.config)};

                // Данные будут добавлены динамически
                const chartData = CHART_DATA_PLACEHOLDER;

                // Настройки анимации
                const ENABLE_ANIMATIONS = ENABLE_ANIMATION_PLACEHOLDER && window.innerWidth > 600;
                const ANIMATION_DURATION = 800;

                // Объект для отслеживания состояния графика
                const chartState = {{
                    hoveredBar: null,
                    tooltip: document.getElementById('tooltip'),
                    noDataMessage: document.getElementById('no-data'),
                    canvas: null,
                    ctx: null,
                    layout: {{
                        padding: null,
                        graphArea: {{ x: 0, y: 0, width: 0, height: 0 }}
                    }},
                    mouse: {{ x: 0, y: 0 }},
                    bars: [],
                    devicePixelRatio: window.devicePixelRatio || 1,
                    animation: {{
                        progress: 0,
                        startTime: 0,
                        isAnimating: false
                    }}
                }};

                // Универсальные функции форматирования
                const formatters = {{
                    number: (num) => num.toLocaleString('ru-RU'),
                    silver: (value) => {{
                        if (value === null || value === undefined || value === 0) return "0K";
                        if (value < 1) return value.toFixed(1).replace('.0', '') + "K";
                        if (value < 1000) {{
                            const formatted = value.toFixed(1);
                            return formatted.endsWith('.0') ? Math.floor(value) + "K" : formatted + "K";
                        }}
                        if (value < 1000000) {{
                            const millions = value / 1000;
                            const formatted = millions.toFixed(1);
                            return formatted.endsWith('.0') ? Math.floor(millions) + "млн" : formatted + "млн";
                        }}
                        if (value < 1000000000) {{
                            const billions = value / 1000000;
                            const formatted = billions.toFixed(1);
                            return formatted.endsWith('.0') ? Math.floor(billions) + "млрд" : formatted + "млрд";
                        }}
                        const trillions = value / 1000000000;
                        const formatted = trillions.toFixed(1);
                        return formatted.endsWith('.0') ? Math.floor(trillions) + "трлн" : formatted + "трлн";
                    }}
                }};

                // Функции для расчета шага оси
                const axisStepFunctions = {{
                    calculateBattlesAxisStep: (maxValue) => {{
                        if (maxValue <= 5) return 1;
                        if (maxValue <= 20) return 5;
                        if (maxValue <= 50) return 10;
                        if (maxValue <= 100) return 20;
                        if (maxValue <= 500) return 100;
                        const magnitude = Math.pow(10, Math.floor(Math.log10(maxValue)));
                        return Math.ceil(maxValue / 5 / magnitude) * magnitude;
                    }},
                    calculateKeysAxisStep: (maxValue) => {{
                        if (maxValue <= 5) return 1;
                        if (maxValue <= 20) return 5;
                        if (maxValue <= 50) return 10;
                        if (maxValue <= 100) return 20;
                        if (maxValue <= 500) return 100;
                        if (maxValue <= 1000) return 200;
                        if (maxValue <= 5000) return 1000;
                        if (maxValue <= 10000) return 2000;
                        if (maxValue <= 50000) return 10000;
                        const magnitude = Math.pow(10, Math.floor(Math.log10(maxValue)));
                        return Math.ceil(maxValue / 5 / magnitude) * magnitude;
                    }},
                    calculateSilverAxisStep: (maxValue) => {{
                        if (maxValue <= 5) return 1;
                        if (maxValue <= 10) return 2;
                        if (maxValue <= 25) return 5;
                        if (maxValue <= 50) return 10;
                        if (maxValue <= 100) return 20;
                        if (maxValue <= 200) return 50;
                        if (maxValue <= 500) return 100;
                        if (maxValue <= 1000) return 200;
                        const magnitude = Math.pow(10, Math.floor(Math.log10(maxValue)));
                        return Math.ceil(maxValue / 5 / magnitude) * magnitude;
                    }}
                }};

                function getOptimalFontSize() {{
                    const canvas = chartState.canvas;
                    if (!canvas) return 10;
                    const width = canvas.clientWidth;
                    if (width < 400) return 8;
                    if (width < 600) return 9;
                    return 10;
                }}

                function calculateOptimalPadding() {{
                    const canvas = chartState.canvas;
                    const width = canvas.clientWidth;
                    const height = canvas.clientHeight;

                    return {{
                        left: Math.max(40, width * 0.06),
                        right: Math.max(20, width * 0.03),
                        top: Math.max(15, height * 0.06),
                        bottom: Math.max(25, height * 0.1)
                    }};
                }}

                function drawChart(animationProgress = 1) {{
                    const canvas = document.getElementById(CONFIG.chart_id);
                    const ctx = canvas.getContext('2d');

                    chartState.canvas = canvas;
                    chartState.ctx = ctx;

                    const dpr = chartState.devicePixelRatio;
                    const rect = canvas.getBoundingClientRect();

                    canvas.width = rect.width * dpr;
                    canvas.height = rect.height * dpr;
                    ctx.scale(dpr, dpr);
                    canvas.style.width = rect.width + 'px';
                    canvas.style.height = rect.height + 'px';

                    if (!chartData || !chartData.dates || chartData.dates.length === 0) {{
                        chartState.noDataMessage.style.display = 'block';
                        return;
                    }} else {{
                        chartState.noDataMessage.style.display = 'none';
                    }}

                    chartState.layout.padding = calculateOptimalPadding();
                    const padding = chartState.layout.padding;

                    const graphWidth = rect.width - padding.left - padding.right;
                    const graphHeight = rect.height - padding.top - padding.bottom;

                    chartState.layout.graphArea = {{
                        x: padding.left,
                        y: padding.top,
                        width: graphWidth,
                        height: graphHeight
                    }};

                    ctx.clearRect(0, 0, rect.width, rect.height);

                    // Находим максимальные значения
                    let maxValue = 0;
                    CONFIG.data_keys.forEach(key => {{
                        if (chartData[key]) {{
                            chartData[key].forEach(value => {{
                                maxValue = Math.max(maxValue, value || 0);
                            }});
                        }}
                    }});

                    // Для графика боев суммируем победы и поражения
                    if (CONFIG.type === 'dual_bars') {{
                        maxValue = 0;
                        for (let i = 0; i < chartData.dates.length; i++) {{
                            const total = (chartData.victories[i] || 0) + (chartData.defeats[i] || 0);
                            maxValue = Math.max(maxValue, total);
                        }}
                    }}

                    maxValue = maxValue || 10;

                    drawAxes(ctx, padding, graphWidth, graphHeight, maxValue, rect.width, rect.height);
                    chartState.bars = [];
                    drawBars(ctx, padding, graphWidth, graphHeight, maxValue, rect.width, rect.height, animationProgress);
                }}

                function drawAxes(ctx, padding, graphWidth, graphHeight, maxValue, canvasWidth, canvasHeight) {{
                    const baselineY = canvasHeight - padding.bottom;
                    const baselineX = padding.left;
                    const fontSize = getOptimalFontSize();

                    // Фон области графика
                    ctx.fillStyle = 'rgba(20, 26, 47, 0.5)';
                    ctx.fillRect(padding.left, padding.top, graphWidth, graphHeight);

                    // Сетка
                    ctx.strokeStyle = 'rgba(40, 48, 77, 0.8)';
                    ctx.lineWidth = 0.8;
                    ctx.beginPath();

                    // Шаг оси
                    const stepFunc = axisStepFunctions[CONFIG.axis_step_func];
                    const step = stepFunc(maxValue);
                    const numLines = Math.floor(maxValue / step) + 1;

                    // Горизонтальные линии
                    for (let i = 0; i < numLines; i++) {{
                        const value = i * step;
                        const y = baselineY - (value / maxValue) * graphHeight;

                        ctx.moveTo(baselineX, y);
                        ctx.lineTo(baselineX + graphWidth, y);

                        if (canvasWidth > 300) {{
                            ctx.fillStyle = 'rgba(155, 160, 188, 0.7)';
                            ctx.font = `${{fontSize}}px Arial`;
                            ctx.textAlign = 'right';
                            ctx.textBaseline = 'middle';
                            const formatter = formatters[CONFIG.formatter];
                            ctx.fillText(formatter(value), baselineX - 5, y);
                        }}
                    }}

                    // Вертикальные линии и даты
                    const dataLength = chartData.dates.length;
                    const availableWidth = graphWidth / dataLength;
                    let skipFactor = 1;
                    if (availableWidth < 50) skipFactor = 2;
                    if (availableWidth < 30) skipFactor = 3;

                    for (let i = 0; i < dataLength; i++) {{
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));

                        ctx.moveTo(x, padding.top);
                        ctx.lineTo(x, baselineY);

                        if (i % skipFactor === 0 || i === dataLength - 1) {{
                            ctx.fillStyle = 'rgba(155, 160, 188, 0.9)';
                            ctx.font = `${{fontSize}}px Arial`;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'top';
                            ctx.fillText(chartData.dates[i], x, baselineY + 5);
                        }}
                    }}

                    ctx.stroke();

                    // Базовая линия
                    ctx.beginPath();
                    ctx.strokeStyle = 'rgba(155, 160, 188, 0.3)';
                    ctx.lineWidth = 1;
                    ctx.moveTo(padding.left, baselineY);
                    ctx.lineTo(padding.left + graphWidth, baselineY);
                    ctx.stroke();
                }}

                function drawBars(ctx, padding, graphWidth, graphHeight, maxValue, canvasWidth, canvasHeight, animationProgress) {{
                    const baselineY = canvasHeight - padding.bottom;
                    const dataLength = chartData.dates.length;

                    if (CONFIG.type === 'dual_bars') {{
                        drawDualBars(ctx, padding, graphWidth, graphHeight, maxValue, baselineY, dataLength, animationProgress);
                    }} else {{
                        drawSingleBars(ctx, padding, graphWidth, graphHeight, maxValue, baselineY, dataLength, animationProgress);
                    }}
                }}

                function drawDualBars(ctx, padding, graphWidth, graphHeight, maxValue, baselineY, dataLength, animationProgress) {{
                    const maxBarWidth = 40;
                    let barWidth = Math.min((graphWidth / dataLength) * 0.7, maxBarWidth);
                    const barGap = Math.max(1, Math.min(2, barWidth * 0.1));
                    const halfBarWidth = barWidth / 2;
                    const singleBarWidth = (barWidth - barGap) / 2;

                    for (let i = 0; i < dataLength; i++) {{
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));
                        const barX = x - halfBarWidth;

                        // Получаем актуальные данные из chartData
                        const victories = chartData.victories ? (chartData.victories[i] || 0) : 0;
                        const defeats = chartData.defeats ? (chartData.defeats[i] || 0) : 0;
                        const date = chartData.dates ? chartData.dates[i] : '';

                        const victoryHeight = (victories / maxValue) * graphHeight * animationProgress;
                        const defeatHeight = (defeats / maxValue) * graphHeight * animationProgress;

                        // Столбец побед
                        const victoryGradient = ctx.createLinearGradient(0, baselineY - victoryHeight, 0, baselineY);
                        victoryGradient.addColorStop(0, 'rgba(66, 225, 137, 1)');
                        victoryGradient.addColorStop(1, 'rgba(66, 225, 137, 0.7)');

                        ctx.fillStyle = victoryGradient;
                        const victoryRect = {{
                            x: barX,
                            y: baselineY - victoryHeight,
                            width: singleBarWidth,
                            height: Math.max(1, victoryHeight),
                            type: 'victory',
                            value: victories,
                            date: date,
                            index: i
                        }};

                        drawRoundedBar(ctx, victoryRect);
                        chartState.bars.push(victoryRect);

                        // Столбец поражений
                        const defeatGradient = ctx.createLinearGradient(0, baselineY - defeatHeight, 0, baselineY);
                        defeatGradient.addColorStop(0, 'rgba(255, 107, 108, 1)');
                        defeatGradient.addColorStop(1, 'rgba(255, 107, 108, 0.7)');

                        ctx.fillStyle = defeatGradient;
                        const defeatRect = {{
                            x: barX + singleBarWidth + barGap,
                            y: baselineY - defeatHeight,
                            width: singleBarWidth,
                            height: Math.max(1, defeatHeight),
                            type: 'defeat',
                            value: defeats,
                            date: date,
                            index: i
                        }};

                        drawRoundedBar(ctx, defeatRect);
                        chartState.bars.push(defeatRect);
                    }}
                }}

                function drawSingleBars(ctx, padding, graphWidth, graphHeight, maxValue, baselineY, dataLength, animationProgress) {{
                    const maxBarWidth = 60;
                    let barWidth = Math.min((graphWidth / dataLength) * 0.8, maxBarWidth);
                    const dataKey = CONFIG.data_keys[0];

                    // Создаем градиент
                    const primaryColor = CONFIG.colors.primary;
                    const rgbColor = hexToRgb(primaryColor);

                    for (let i = 0; i < dataLength; i++) {{
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));
                        const barX = x - (barWidth / 2);

                        // Получаем актуальные данные из chartData
                        const value = chartData[dataKey] ? (chartData[dataKey][i] || 0) : 0;
                        const date = chartData.dates ? chartData.dates[i] : '';
                        const barHeight = (value / maxValue) * graphHeight * animationProgress;

                        const gradient = ctx.createLinearGradient(0, baselineY - barHeight, 0, baselineY);
                        gradient.addColorStop(0, `rgba(${{rgbColor.r}}, ${{rgbColor.g}}, ${{rgbColor.b}}, 1)`);
                        gradient.addColorStop(1, `rgba(${{rgbColor.r}}, ${{rgbColor.g}}, ${{rgbColor.b}}, 0.7)`);

                        ctx.fillStyle = gradient;
                        const rect = {{
                            x: barX,
                            y: baselineY - barHeight,
                            width: barWidth,
                            height: Math.max(1, barHeight),
                            value: value,
                            date: date,
                            index: i
                        }};

                        drawRoundedBar(ctx, rect);

                        // Добавляем блик
                        const highlightWidth = barWidth * 0.4;
                        const highlightGradient = ctx.createLinearGradient(
                            rect.x + barWidth * 0.3, rect.y,
                            rect.x + barWidth * 0.3 + highlightWidth, rect.y
                        );
                        highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.2)');
                        highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

                        ctx.fillStyle = highlightGradient;
                        ctx.beginPath();
                        ctx.rect(rect.x + barWidth * 0.3, rect.y, highlightWidth, rect.height);
                        ctx.fill();

                        chartState.bars.push(rect);
                    }}
                }}

                function drawRoundedBar(ctx, rect) {{
                    const radius = Math.min(3, rect.width / 4);

                    ctx.beginPath();
                    ctx.moveTo(rect.x + radius, rect.y);
                    ctx.lineTo(rect.x + rect.width - radius, rect.y);
                    ctx.quadraticCurveTo(rect.x + rect.width, rect.y, rect.x + rect.width, rect.y + radius);
                    ctx.lineTo(rect.x + rect.width, rect.y + rect.height);
                    ctx.lineTo(rect.x, rect.y + rect.height);
                    ctx.lineTo(rect.x, rect.y + radius);
                    ctx.quadraticCurveTo(rect.x, rect.y, rect.x + radius, rect.y);
                    ctx.closePath();
                    ctx.fill();
                }}

                function hexToRgb(hex) {{
                    const result = /^#?([a-f\\d]{{2}})([a-f\\d]{{2}})([a-f\\d]{{2}})$/i.exec(hex);
                    return result ? {{
                        r: parseInt(result[1], 16),
                        g: parseInt(result[2], 16),
                        b: parseInt(result[3], 16)
                    }} : {{r: 255, g: 255, b: 255}};
                }}

                function checkForInteractions(event) {{
                    const canvas = chartState.canvas;
                    if (!canvas || !chartState.bars || chartState.bars.length === 0) {{
                        return;
                    }}

                    const rect = canvas.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const y = event.clientY - rect.top;

                    chartState.mouse = {{ x, y }};

                    let hoveredBar = null;

                    // Ищем бар под курсором
                    for (const bar of chartState.bars) {{
                        if (x >= bar.x && x <= bar.x + bar.width && y >= bar.y && y <= bar.y + bar.height) {{
                            hoveredBar = bar;
                            break;
                        }}
                    }}

                    if (hoveredBar && hoveredBar !== chartState.hoveredBar) {{
                        const tooltip = chartState.tooltip;
                        if (!tooltip) return;

                        tooltip.style.display = 'block';

                        // Позиционирование тултипа с учетом границ экрана
                        let tooltipX = Math.min(x + 10, canvas.clientWidth - 150);
                        let tooltipY = Math.max(y - 10, 10);

                        if (y > canvas.clientHeight - 80) {{
                            tooltipY = y - 70;
                        }}

                        tooltip.style.left = tooltipX + 'px';
                        tooltip.style.top = tooltipY + 'px';

                        // Получаем актуальные данные для тултипа
                        const formatter = formatters[CONFIG.formatter];
                        const valueText = formatter(hoveredBar.value);

                        // Форматируем контент тултипа в зависимости от типа графика
                        if (CONFIG.type === 'dual_bars') {{
                            const typeText = hoveredBar.type === 'victory' ? 'Победы' : 'Поражения';
                            tooltip.innerHTML = `<strong>${{hoveredBar.date}}</strong>${{typeText}}: ${{valueText}}`;
                        }} else {{
                            let label = 'Значение';
                            if (CONFIG.data_keys[0] === 'keys_collected') {{
                                label = 'Собрано ключей';
                            }} else if (CONFIG.data_keys[0] === 'silver_collected') {{
                                label = 'Собрано серебра';
                            }}
                            tooltip.innerHTML = `<strong>${{hoveredBar.date}}</strong>${{label}}: ${{valueText}}`;
                        }}

                        chartState.hoveredBar = hoveredBar;
                    }} else if (!hoveredBar && chartState.hoveredBar) {{
                        // Скрываем тултип если курсор вне всех баров
                        if (chartState.tooltip) {{
                            chartState.tooltip.style.display = 'none';
                        }}
                        chartState.hoveredBar = null;
                    }}
                }}

                function animateChart(timestamp) {{
                    if (!chartState.animation.isAnimating) return;

                    if (!chartState.animation.startTime) {{
                        chartState.animation.startTime = timestamp;
                    }}

                    const elapsed = timestamp - chartState.animation.startTime;
                    let progress = Math.min(1, elapsed / ANIMATION_DURATION);
                    const animationProgress = 1 - Math.pow(1 - progress, 3);

                    drawChart(animationProgress);

                    if (progress < 1) {{
                        requestAnimationFrame(animateChart);
                    }} else {{
                        chartState.animation.isAnimating = false;
                    }}
                }}

                function setupEventListeners() {{
                    const canvas = document.getElementById(CONFIG.chart_id);

                    // Удаляем старые обработчики если они есть
                    if (canvas._chartMouseMoveHandler) {{
                        canvas.removeEventListener('mousemove', canvas._chartMouseMoveHandler);
                    }}
                    if (canvas._chartMouseLeaveHandler) {{
                        canvas.removeEventListener('mouseleave', canvas._chartMouseLeaveHandler);
                    }}
                    if (window._chartResizeHandler) {{
                        window.removeEventListener('resize', window._chartResizeHandler);
                    }}

                    // Создаем новые обработчики
                    canvas._chartMouseMoveHandler = function(event) {{
                        checkForInteractions(event);
                    }};

                    canvas._chartMouseLeaveHandler = function() {{
                        if (chartState.tooltip) {{
                            chartState.tooltip.style.display = 'none';
                        }}
                        chartState.hoveredBar = null;
                    }};

                    window._chartResizeHandler = function() {{
                        // Добавляем небольшую задержку для стабилизации размера
                        clearTimeout(window._resizeTimeout);
                        window._resizeTimeout = setTimeout(function() {{
                            drawChart(1);
                        }}, 100);
                    }};

                    // Добавляем новые обработчики
                    canvas.addEventListener('mousemove', canvas._chartMouseMoveHandler);
                    canvas.addEventListener('mouseleave', canvas._chartMouseLeaveHandler);
                    window.addEventListener('resize', window._chartResizeHandler);
                }}

                window.onload = function() {{
                    setupEventListeners();

                    if (ENABLE_ANIMATIONS) {{
                        chartState.animation.isAnimating = true;
                        requestAnimationFrame(animateChart);
                    }} else {{
                        drawChart(1);
                    }}
                }};
            </script>
        </body>
        </html>
        """

        try:
            fd, self.html_path = tempfile.mkstemp(suffix=".html", prefix=f"aom_{self.config['type']}_chart_")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self._py_logger.debug(f"Создан шаблон графика {self.title}: {self.html_path}")
        except Exception as e:
            self._py_logger.error(f"Ошибка при создании HTML-шаблона: {e}")

    def resizeEvent(self, event):
        """Обработчик изменения размера виджета."""
        super().resizeEvent(event)
        self.resize_timer.start(50)

    def handle_resize(self):
        """Обработка изменения размера с задержкой для оптимизации."""
        if hasattr(self, '_is_currently_updating') and self._is_currently_updating:
            return

        if hasattr(self, 'last_data') and self.last_data:
            self._is_currently_updating = True
            try:
                self.update_chart(self.last_data, force_no_animation=True)
            finally:
                self._is_currently_updating = False

    def update_chart(self, data, force_no_animation=False):
        """Обновляет график новыми данными."""
        if not data or not self.html_path:
            self._py_logger.warning("Невозможно обновить график: нет данных или шаблона")
            return

        try:
            self.last_data = data

            # УПРОЩЕННАЯ ЛОГИКА: анимация включается только когда force_no_animation=False
            enable_animation = not force_no_animation

            # Чтение базового HTML шаблона
            with open(self.html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Проверка данных
            if not data.get("dates") or len(data.get("dates", [])) == 0:
                self._py_logger.warning(f"Пустой набор данных для графика {self.title}")
                data = {"dates": []}
                for key in self.config['data_keys']:
                    data[key] = []

            # Замена плейсхолдеров
            json_data = json.dumps(data)
            updated_html = html_content.replace('CHART_DATA_PLACEHOLDER', json_data)
            updated_html = updated_html.replace('ENABLE_ANIMATION_PLACEHOLDER',
                                                'true' if enable_animation else 'false')

            # Добавляем уникальный идентификатор для обновления, чтобы избежать кэширования
            import time
            update_id = int(time.time() * 1000)  # Миллисекунды для уникальности

            # Добавляем скрипт для принудительного обновления данных и обработчиков
            additional_script = f"""
            <script>
            // Уникальный ID обновления: {update_id}
            window.chartUpdateId = {update_id};

            // Принудительно очищаем старые обработчики
            window.addEventListener('load', function() {{
                // Небольшая задержка для полной загрузки
                setTimeout(function() {{
                    // Обновляем данные принудительно
                    if (typeof chartData !== 'undefined' && typeof drawChart === 'function') {{
                        // Очищаем старое состояние
                        if (typeof chartState !== 'undefined') {{
                            chartState.bars = [];
                            chartState.hoveredBar = null;
                            if (chartState.tooltip) {{
                                chartState.tooltip.style.display = 'none';
                            }}
                        }}

                        // Перерисовываем график с новыми данными
                        drawChart(1);

                        // Переустанавливаем обработчики событий
                        setupEventListeners();
                    }}
                }}, 50);
            }});
            </script>
            """

            # Вставляем дополнительный скрипт перед закрывающим тегом body
            updated_html = updated_html.replace('</body>', additional_script + '</body>')

            # Принудительно очищаем кэш профиля браузера
            try:
                profile = self.web_view.page().profile()
                profile.clearHttpCache()
                profile.clearAllVisitedLinks()
            except Exception as e:
                self._py_logger.debug(f"Не удалось очистить кэш браузера: {e}")

            # Используем setHtml вместо load для избежания проблем с кэшированием файлов
            base_url = QUrl.fromLocalFile(os.path.dirname(self.html_path) + "/")
            self.web_view.setHtml(updated_html, base_url)

            animation_status = "с анимацией" if enable_animation else "без анимации"
            self._py_logger.debug(
                f"График {self.title} обновлен {animation_status} (ID: {update_id}), точек данных: {len(data.get('dates', []))}")

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении графика {self.title}: {e}")
            import traceback
            self._py_logger.debug(traceback.format_exc())

    def clear(self):
        """Очищает график."""
        empty_data = {"dates": []}
        for key in self.config['data_keys']:
            empty_data[key] = []
        self.update_chart(empty_data)

    def __del__(self):
        """Очистка ресурсов при уничтожении объекта."""
        try:
            if self.html_path and os.path.exists(self.html_path):
                os.remove(self.html_path)
        except Exception:
            pass


# Конкретные реализации графиков
class BattlesChartWidget(ResponsiveChartWidget):
    """Виджет для отображения графика побед и поражений."""

    def __init__(self, parent=None):
        super().__init__(ChartConfig.BATTLES, parent)


class KeysChartWidget(ResponsiveChartWidget):
    """Виджет для отображения графика собранных ключей."""

    def __init__(self, parent=None):
        super().__init__(ChartConfig.KEYS, parent)


class SilverChartWidget(ResponsiveChartWidget):
    """Виджет для отображения графика собранного серебра."""

    def __init__(self, parent=None):
        super().__init__(ChartConfig.SILVER, parent)