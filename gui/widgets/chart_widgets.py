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


class ResponsiveChartWidget(QWidget):
    """Базовый класс для отзывчивых графиков."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._py_logger = logging.getLogger("BotLogger")
        self.title = title

        # Настройка лейаута
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)  # Убираем лишние отступы

        # Заголовок графика
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 5)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("chart-title")
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {Styles.COLORS['text_primary']};
            background-color: transparent;
        """)
        header_layout.addWidget(self.title_label)

        self.layout.addLayout(header_layout)

        # Контейнер для графика с более тёмным фоном
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

        # Создание и настройка WebEngineView с улучшенными параметрами
        self.web_view = QWebEngineView()

        # Настраиваем параметры браузера
        settings = self.web_view.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)

        # Устанавливаем цвет фона соответствующий теме
        self.web_view.setStyleSheet(f"background-color: {Styles.COLORS['background_dark']};")

        chart_layout.addWidget(self.web_view)
        self.layout.addWidget(self.chart_container)

        # Легенда для графика (будет переопределена в дочерних классах)
        self.legend_layout = QHBoxLayout()
        self.legend_layout.setContentsMargins(15, 5, 15, 10)
        self.legend_layout.addStretch()
        self.layout.addLayout(self.legend_layout)

        # Временный HTML-файл для графика
        self.html_path = None

        # Таймер для оптимизации отрисовки при изменении размера
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.handle_resize)

        # Создать базовый HTML шаблон
        self.create_html_template()

        # Флаг первой загрузки (для управления анимацией)
        self.first_load = True

        # Переменная для хранения последних данных (для перерисовки при изменении размера)
        self.last_data = None

    def create_html_template(self):
        """Создает HTML-шаблон с графиком."""
        # Будет реализован в дочерних классах
        pass

    def resizeEvent(self, event):
        """Обработчик изменения размера виджета."""
        super().resizeEvent(event)
        # Запуск таймера при изменении размера - предотвращает многократную перерисовку
        self.resize_timer.start(50)  # 50мс задержка

    def handle_resize(self):
        """Обработка изменения размера с небольшой задержкой для оптимизации."""
        # Проверяем, была ли уже инициирована перерисовка
        if hasattr(self, '_is_currently_updating') and self._is_currently_updating:
            return

        # Если есть данные, перерисовываем график
        if hasattr(self, 'last_data') and self.last_data:
            # Устанавливаем флаг, что перерисовка в процессе
            self._is_currently_updating = True

            # Обновляем график
            try:
                self.update_chart(self.last_data)
            finally:
                # Сбрасываем флаг после окончания операции
                self._is_currently_updating = False

    def update_chart(self, data):
        """Обновляет график новыми данными."""
        # Пропускаем обновление, если данные не изменились или их нет
        if not data or (hasattr(self, 'last_data') and data == self.last_data):
            return

        # Сохраняем данные для возможной перерисовки
        self.last_data = data

    def clear(self):
        """Очищает график."""
        # Будет реализован в дочерних классах
        pass

    def __del__(self):
        """Очистка ресурсов при уничтожении объекта."""
        try:
            if self.html_path and os.path.exists(self.html_path):
                os.remove(self.html_path)
        except Exception as e:
            if hasattr(self, '_py_logger'):
                self._py_logger.error(f"Ошибка при удалении временного файла: {e}")

    def clear_cache(self):
        """Очищает кэш и создает новый HTML-шаблон для принудительного обновления графика."""
        try:
            # Удаляем старый файл HTML, если он существует
            if self.html_path and os.path.exists(self.html_path):
                os.remove(self.html_path)
                self._py_logger.debug(f"Удален временный файл шаблона: {self.html_path}")

            # Создаем новый шаблон
            self.create_html_template()
            self._py_logger.debug("Создан новый HTML-шаблон для графика")

            # Сбрасываем флаг первой загрузки для включения анимации
            self.first_load = True

            # Сбрасываем сохраненные данные
            self.last_data = None
        except Exception as e:
            self._py_logger.error(f"Ошибка при очистке кэша графика: {e}")


class BattlesChartWidget(ResponsiveChartWidget):
    """Виджет для отображения графика побед и поражений (без линии процента побед)."""

    def __init__(self, parent=None):
        super().__init__("Тренд побед и поражений (7 дней)", parent)

        # Настройка легенды (только для столбцов, без линии процента побед)
        victory_legend = QLabel("● Победы")
        victory_legend.setStyleSheet(f"color: {Styles.COLORS['secondary']}; font-size: 12px;")
        self.legend_layout.addWidget(victory_legend)

        defeat_legend = QLabel("● Поражения")
        defeat_legend.setStyleSheet(f"color: {Styles.COLORS['accent']}; font-size: 12px;")
        self.legend_layout.addWidget(defeat_legend)

        self.legend_layout.addStretch()

    def create_html_template(self):
        """Создает HTML-шаблон с улучшенным Canvas-графиком."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Battles Chart</title>
            <style>
                :root {
                    --bg-color: #171D33;
                    --grid-color: #28304d;
                    --text-color: #FFFFFF;
                    --text-secondary: #9BA0BC;
                    --victory-color: #42E189;
                    --defeat-color: #FF6B6C;
                    --tooltip-bg: #2A3158;
                    --tooltip-border: #353E65;
                }

                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    margin: 0;
                    padding: 0;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    font-family: 'Segoe UI', Arial, sans-serif;
                    overflow: hidden;
                    height: 100vh;
                    width: 100vw;
                }

                #chart-container {
                    width: 100%;
                    height: 100%;
                    position: relative;
                }

                canvas {
                    width: 100%;
                    height: 100%;
                    position: absolute;
                    top: 0;
                    left: 0;
                }

                .tooltip {
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
                }

                .tooltip strong {
                    display: block;
                    margin-bottom: 4px;
                    color: var(--victory-color);
                }

                .no-data {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: var(--text-secondary);
                    font-size: 14px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div id="chart-container">
                <canvas id="battles-chart"></canvas>
                <div id="tooltip" class="tooltip"></div>
                <div id="no-data" class="no-data" style="display:none;">Нет данных для отображения</div>
            </div>

            <script>
                // Данные будут добавлены динамически
                const chartData = CHART_DATA_PLACEHOLDER;

                // Настройки анимации
                const ENABLE_ANIMATIONS = window.innerWidth > 600;
                const ANIMATION_DURATION = 800;

                // Объект для отслеживания состояния графика
                const chartState = {
                    hoveredBar: null,
                    tooltip: document.getElementById('tooltip'),
                    noDataMessage: document.getElementById('no-data'),
                    canvas: null,
                    ctx: null,
                    layout: {
                        padding: null,
                        graphArea: { x: 0, y: 0, width: 0, height: 0 }
                    },
                    mouse: { x: 0, y: 0 },
                    bars: [],
                    devicePixelRatio: window.devicePixelRatio || 1,
                    // Для анимации
                    animation: {
                        progress: 0,
                        startTime: 0,
                        isAnimating: false
                    }
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

                    let leftPadding = Math.max(35, width * 0.06);
                    let rightPadding = Math.max(20, width * 0.03); // Уменьшаем правый отступ, т.к. нет второй оси Y
                    let topPadding = Math.max(15, height * 0.06);
                    let bottomPadding = Math.max(25, height * 0.1);

                    return {
                        left: leftPadding,
                        right: rightPadding, 
                        top: topPadding,
                        bottom: bottomPadding
                    };
                }

                function drawChart(animationProgress = 1) {
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
                        chartState.noDataMessage.style.display = 'block';
                        return;
                    } else {
                        chartState.noDataMessage.style.display = 'none';
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

                    for (let i = 0; i < chartData.dates.length; i++) {
                        const victories = chartData.victories[i] || 0;
                        const defeats = chartData.defeats[i] || 0;
                        const total = victories + defeats;

                        maxBattles = Math.max(maxBattles, total);
                    }

                    // Защита от нулевых максимумов
                    maxBattles = maxBattles || 10;

                    // Рисуем оси и сетку
                    drawAxes(ctx, padding, graphWidth, graphHeight, maxBattles, rect.width, rect.height);

                    // Сбрасываем массивы элементов для интерактивности
                    chartState.bars = [];

                    // Отрисовка столбцов побед и поражений с учетом анимации
                    drawBars(ctx, padding, graphWidth, graphHeight, maxBattles, rect.width, rect.height, animationProgress);
                }

                function drawAxes(ctx, padding, graphWidth, graphHeight, maxBattles, canvasWidth, canvasHeight) {
                    const baselineY = canvasHeight - padding.bottom;
                    const baselineX = padding.left;
                    const fontSize = getOptimalFontSize();

                    // Фон области графика (полупрозрачный)
                    ctx.fillStyle = 'rgba(20, 26, 47, 0.5)';
                    ctx.fillRect(padding.left, padding.top, graphWidth, graphHeight);

                    // Отрисовка сетки
                    ctx.strokeStyle = 'rgba(40, 48, 77, 0.8)';
                    ctx.lineWidth = 0.8;
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
                        if (canvasWidth > 300) {
                            ctx.fillStyle = 'rgba(155, 160, 188, 0.7)';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'right';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(value, baselineX - 5, y);
                        }
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

                        // Рисуем вертикальную линию сетки
                        ctx.moveTo(x, padding.top);
                        ctx.lineTo(x, baselineY);

                        // Подпись даты (пропускаем некоторые для экономии места)
                        if (i % skipFactor === 0 || i === dataLength - 1) {
                            ctx.fillStyle = 'rgba(155, 160, 188, 0.9)';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'top';
                            ctx.fillText(chartData.dates[i], x, baselineY + 5);
                        }
                    }

                    ctx.stroke();

                    // Горизонтальная базовая линия
                    ctx.beginPath();
                    ctx.strokeStyle = 'rgba(155, 160, 188, 0.3)';
                    ctx.lineWidth = 1;
                    ctx.moveTo(padding.left, baselineY);
                    ctx.lineTo(padding.left + graphWidth, baselineY);
                    ctx.stroke();
                }

                function drawBars(ctx, padding, graphWidth, graphHeight, maxBattles, canvasWidth, canvasHeight, animationProgress) {
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

                        // Вычисляем высоту столбцов с учетом анимации
                        const victoryHeight = (victories / maxBattles) * graphHeight * animationProgress;
                        const defeatHeight = (defeats / maxBattles) * graphHeight * animationProgress;

                        // Создаем градиент для побед
                        const victoryGradient = ctx.createLinearGradient(0, baselineY - victoryHeight, 0, baselineY);
                        victoryGradient.addColorStop(0, 'rgba(66, 225, 137, 1)');    // Ярче вверху
                        victoryGradient.addColorStop(1, 'rgba(66, 225, 137, 0.7)');  // Более прозрачный внизу

                        // Рисуем столбец побед
                        ctx.fillStyle = victoryGradient;
                        const victoryRect = {
                            x: barX,
                            y: baselineY - victoryHeight,
                            width: singleBarWidth,
                            height: Math.max(1, victoryHeight),
                            type: 'victory',
                            value: victories,
                            date: chartData.dates[i],
                            index: i
                        };

                        // Скругленные углы для верхней части
                        const radius = Math.min(3, singleBarWidth / 4);

                        // Рисуем столбец со скругленными углами вверху
                        ctx.beginPath();
                        ctx.moveTo(victoryRect.x + radius, victoryRect.y);
                        ctx.lineTo(victoryRect.x + victoryRect.width - radius, victoryRect.y);
                        ctx.quadraticCurveTo(victoryRect.x + victoryRect.width, victoryRect.y, victoryRect.x + victoryRect.width, victoryRect.y + radius);
                        ctx.lineTo(victoryRect.x + victoryRect.width, victoryRect.y + victoryRect.height);
                        ctx.lineTo(victoryRect.x, victoryRect.y + victoryRect.height);
                        ctx.lineTo(victoryRect.x, victoryRect.y + radius);
                        ctx.quadraticCurveTo(victoryRect.x, victoryRect.y, victoryRect.x + radius, victoryRect.y);
                        ctx.closePath();
                        ctx.fill();

                        chartState.bars.push(victoryRect);

                        // Создаем градиент для поражений
                        const defeatGradient = ctx.createLinearGradient(0, baselineY - defeatHeight, 0, baselineY);
                        defeatGradient.addColorStop(0, 'rgba(255, 107, 108, 1)');   // Ярче вверху
                        defeatGradient.addColorStop(1, 'rgba(255, 107, 108, 0.7)'); // Более прозрачный внизу

                        // Рисуем столбец поражений
                        ctx.fillStyle = defeatGradient;
                        const defeatRect = {
                            x: barX + singleBarWidth + barGap,
                            y: baselineY - defeatHeight,
                            width: singleBarWidth,
                            height: Math.max(1, defeatHeight),
                            type: 'defeat',
                            value: defeats,
                            date: chartData.dates[i],
                            index: i
                        };

                        // Рисуем столбец со скругленными углами вверху
                        ctx.beginPath();
                        ctx.moveTo(defeatRect.x + radius, defeatRect.y);
                        ctx.lineTo(defeatRect.x + defeatRect.width - radius, defeatRect.y);
                        ctx.quadraticCurveTo(defeatRect.x + defeatRect.width, defeatRect.y, defeatRect.x + defeatRect.width, defeatRect.y + radius);
                        ctx.lineTo(defeatRect.x + defeatRect.width, defeatRect.y + defeatRect.height);
                        ctx.lineTo(defeatRect.x, defeatRect.y + defeatRect.height);
                        ctx.lineTo(defeatRect.x, defeatRect.y + radius);
                        ctx.quadraticCurveTo(defeatRect.x, defeatRect.y, defeatRect.x + radius, defeatRect.y);
                        ctx.closePath();
                        ctx.fill();

                        chartState.bars.push(defeatRect);
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

                    // Обновляем подсказку
                    if (hoveredBar) {
                        const tooltip = chartState.tooltip;
                        tooltip.style.display = 'block';

                        // Позиционируем подсказку, чтобы она не выходила за границы экрана
                        let tooltipX = Math.min(x + 10, canvas.clientWidth - 150);
                        let tooltipY = Math.max(y - 10, 10);

                        // Если подсказка слишком низко, показываем ее выше
                        if (y > canvas.clientHeight - 80) {
                            tooltipY = y - 70;
                        }

                        tooltip.style.left = tooltipX + 'px';
                        tooltip.style.top = tooltipY + 'px';

                        const typeText = hoveredBar.type === 'victory' ? 'Победы' : 'Поражения';
                        const valueText = formatNumber(hoveredBar.value);

                        // Улучшенное форматирование подсказки
                        tooltip.innerHTML = `
                            <strong>${hoveredBar.date}</strong>
                            ${typeText}: ${valueText}
                        `;
                    } else {
                        chartState.tooltip.style.display = 'none';
                    }

                    // Обновляем состояние графика
                    chartState.hoveredBar = hoveredBar;
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

                function animateChart(timestamp) {
                    if (!chartState.animation.isAnimating) return;

                    if (!chartState.animation.startTime) {
                        chartState.animation.startTime = timestamp;
                    }

                    const elapsed = timestamp - chartState.animation.startTime;
                    const duration = ANIMATION_DURATION;

                    // Рассчитываем прогресс анимации (от 0 до 1) с эффектом ease-out
                    let progress = elapsed / duration;
                    progress = Math.min(1, progress);

                    // Применяем кривую плавности (ease-out)
                    const animationProgress = 1 - Math.pow(1 - progress, 3);

                    // Обновляем график с текущим прогрессом анимации
                    drawChart(animationProgress);

                    if (progress < 1) {
                        // Если анимация не завершена, запрашиваем следующий кадр
                        requestAnimationFrame(animateChart);
                    } else {
                        // Анимация завершена
                        chartState.animation.isAnimating = false;
                    }
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
                        // При изменении размера перерисовываем без анимации
                        drawChart(1);
                    });
                }

                // Инициализация с анимацией
                window.onload = function() {
                    setupEventListeners();

                    // Проверяем, нужно ли включать анимацию
                    if (ENABLE_ANIMATIONS) {
                        chartState.animation.isAnimating = true;
                        requestAnimationFrame(animateChart);
                    } else {
                        // Если анимация отключена, рисуем график сразу полностью
                        drawChart(1);
                    }
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
                    "defeats": []
                }

            # Сохраняем данные для возможной перерисовки при изменении размера
            self.last_data = trend_data

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
            "defeats": []
        }
        self.update_chart(empty_data)


class KeysChartWidget(ResponsiveChartWidget):
    """Виджет для отображения графика собранных ключей (без линии ключей за победу)."""

    def __init__(self, parent=None):
        super().__init__("Сбор ключей (7 дней)", parent)

        # Настройка легенды (только для столбцов ключей, без линии)
        keys_legend = QLabel("● Собрано ключей")
        keys_legend.setStyleSheet(f"color: {Styles.COLORS['warning']}; font-size: 12px;")
        self.legend_layout.addWidget(keys_legend)

        self.legend_layout.addStretch()

    def create_html_template(self):
        """Создает HTML-шаблон с улучшенным Canvas-графиком для ключей."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Keys Chart</title>
            <style>
                :root {
                    --bg-color: #171D33;
                    --grid-color: #28304d;
                    --text-color: #FFFFFF;
                    --text-secondary: #9BA0BC;
                    --keys-color: #FFB169;
                    --tooltip-bg: #2A3158;
                    --tooltip-border: #353E65;
                }

                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    margin: 0;
                    padding: 0;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    font-family: 'Segoe UI', Arial, sans-serif;
                    overflow: hidden;
                    height: 100vh;
                    width: 100vw;
                }

                #chart-container {
                    width: 100%;
                    height: 100%;
                    position: relative;
                }

                canvas {
                    width: 100%;
                    height: 100%;
                    position: absolute;
                    top: 0;
                    left: 0;
                }

                .tooltip {
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
                }

                .tooltip strong {
                    display: block;
                    margin-bottom: 4px;
                    color: var(--keys-color);
                }

                .no-data {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: var(--text-secondary);
                    font-size: 14px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div id="chart-container">
                <canvas id="keys-chart"></canvas>
                <div id="tooltip" class="tooltip"></div>
                <div id="no-data" class="no-data" style="display:none;">Нет данных для отображения</div>
            </div>

            <script>
                // Данные будут добавлены динамически
                const chartData = CHART_DATA_PLACEHOLDER;

                // Настройки анимации
                const ENABLE_ANIMATIONS = window.innerWidth > 600;
                const ANIMATION_DURATION = 800;

                // Объект для отслеживания состояния графика
                const chartState = {
                    hoveredBar: null,
                    tooltip: document.getElementById('tooltip'),
                    noDataMessage: document.getElementById('no-data'),
                    canvas: null,
                    ctx: null,
                    layout: {
                        padding: null,
                        graphArea: { x: 0, y: 0, width: 0, height: 0 }
                    },
                    mouse: { x: 0, y: 0 },
                    bars: [],
                    devicePixelRatio: window.devicePixelRatio || 1,
                    // Для анимации
                    animation: {
                        progress: 0,
                        startTime: 0,
                        isAnimating: false
                    }
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
                    let rightPadding = Math.max(20, width * 0.03); // Уменьшаем правый отступ, т.к. нет второй оси Y
                    let topPadding = Math.max(15, height * 0.06);
                    let bottomPadding = Math.max(25, height * 0.1);

                    return {
                        left: leftPadding,
                        right: rightPadding, 
                        top: topPadding,
                        bottom: bottomPadding
                    };
                }

                function drawChart(animationProgress = 1) {
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
                        chartState.noDataMessage.style.display = 'block';
                        return;
                    } else {
                        chartState.noDataMessage.style.display = 'none';
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

                    for (let i = 0; i < chartData.dates.length; i++) {
                        const keys = chartData.keys_collected[i] || 0;
                        maxKeys = Math.max(maxKeys, keys);
                    }

                    // Защита от нулевых максимумов
                    maxKeys = maxKeys || 1000;

                    // Рисуем оси и сетку
                    drawAxes(ctx, padding, graphWidth, graphHeight, maxKeys, rect.width, rect.height);

                    // Сбрасываем массивы элементов для интерактивности
                    chartState.bars = [];

                    // Отрисовка столбцов ключей с учетом анимации
                    drawBars(ctx, padding, graphWidth, graphHeight, maxKeys, rect.width, rect.height, animationProgress);
                }

                function drawAxes(ctx, padding, graphWidth, graphHeight, maxKeys, canvasWidth, canvasHeight) {
                    const baselineY = canvasHeight - padding.bottom;
                    const baselineX = padding.left;
                    const fontSize = getOptimalFontSize();

                    // Фон области графика (полупрозрачный)
                    ctx.fillStyle = 'rgba(20, 26, 47, 0.5)';
                    ctx.fillRect(padding.left, padding.top, graphWidth, graphHeight);

                    // Отрисовка сетки
                    ctx.strokeStyle = 'rgba(40, 48, 77, 0.8)';
                    ctx.lineWidth = 0.8;
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
                        if (canvasWidth > 300) {
                            ctx.fillStyle = 'rgba(155, 160, 188, 0.7)';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'right';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(formatNumber(value), baselineX - 5, y);
                        }
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

                        // Рисуем вертикальную линию сетки
                        ctx.moveTo(x, padding.top);
                        ctx.lineTo(x, baselineY);

                        // Подпись даты (пропускаем некоторые для экономии места)
                        if (i % skipFactor === 0 || i === dataLength - 1) {
                            ctx.fillStyle = 'rgba(155, 160, 188, 0.9)';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'top';
                            ctx.fillText(chartData.dates[i], x, baselineY + 5);
                        }
                    }

                    ctx.stroke();

                    // Горизонтальная базовая линия
                    ctx.beginPath();
                    ctx.strokeStyle = 'rgba(155, 160, 188, 0.3)';
                    ctx.lineWidth = 1;
                    ctx.moveTo(padding.left, baselineY);
                    ctx.lineTo(padding.left + graphWidth, baselineY);
                    ctx.stroke();
                }

                function drawBars(ctx, padding, graphWidth, graphHeight, maxKeys, canvasWidth, canvasHeight, animationProgress) {
                    const baselineY = canvasHeight - padding.bottom;
                    const dataLength = chartData.dates.length;

                    // Вычисляем оптимальную ширину столбцов (можем сделать их шире, т.к. теперь только один тип столбцов)
                    const maxBarWidth = 60;
                    let barWidth = Math.min((graphWidth / dataLength) * 0.8, maxBarWidth);

                    for (let i = 0; i < dataLength; i++) {
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));
                        const barX = x - (barWidth / 2);

                        const keys = chartData.keys_collected[i] || 0;

                        // Вычисляем высоту столбца с учетом анимации
                        const keyHeight = (keys / maxKeys) * graphHeight * animationProgress;

                        // Создаем градиент для столбца ключей
                        const keyGradient = ctx.createLinearGradient(0, baselineY - keyHeight, 0, baselineY);
                        keyGradient.addColorStop(0, 'rgba(255, 177, 105, 1)');    // Ярче вверху
                        keyGradient.addColorStop(1, 'rgba(255, 177, 105, 0.7)');  // Более прозрачный внизу

                        // Рисуем столбец ключей
                        ctx.fillStyle = keyGradient;
                        const keyRect = {
                            x: barX,
                            y: baselineY - keyHeight,
                            width: barWidth,
                            height: Math.max(1, keyHeight),
                            value: keys,
                            date: chartData.dates[i],
                            index: i
                        };

                        // Скругленные углы для верхней части
                        const radius = Math.min(4, barWidth / 4);

                        // Рисуем столбец со скругленными углами вверху
                        ctx.beginPath();
                        ctx.moveTo(keyRect.x + radius, keyRect.y);
                        ctx.lineTo(keyRect.x + keyRect.width - radius, keyRect.y);
                        ctx.quadraticCurveTo(keyRect.x + keyRect.width, keyRect.y, keyRect.x + keyRect.width, keyRect.y + radius);
                        ctx.lineTo(keyRect.x + keyRect.width, keyRect.y + keyRect.height);
                        ctx.lineTo(keyRect.x, keyRect.y + keyRect.height);
                        ctx.lineTo(keyRect.x, keyRect.y + radius);
                        ctx.quadraticCurveTo(keyRect.x, keyRect.y, keyRect.x + radius, keyRect.y);
                        ctx.closePath();
                        ctx.fill();

                        // Добавляем блик на столбце
                        const highlightWidth = barWidth * 0.4;
                        const highlightGradient = ctx.createLinearGradient(
                            keyRect.x + barWidth * 0.3, keyRect.y,
                            keyRect.x + barWidth * 0.3 + highlightWidth, keyRect.y
                        );
                        highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.2)');
                        highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

                        ctx.fillStyle = highlightGradient;
                        ctx.beginPath();
                        ctx.moveTo(keyRect.x + barWidth * 0.3, keyRect.y);
                        ctx.lineTo(keyRect.x + barWidth * 0.3 + highlightWidth, keyRect.y);
                        ctx.lineTo(keyRect.x + barWidth * 0.3 + highlightWidth, keyRect.y + keyRect.height);
                        ctx.lineTo(keyRect.x + barWidth * 0.3, keyRect.y + keyRect.height);
                        ctx.closePath();
                        ctx.fill();

                        chartState.bars.push(keyRect);
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

                    // Обновляем подсказку
                    if (hoveredBar) {
                        const tooltip = chartState.tooltip;
                        tooltip.style.display = 'block';

                        // Позиционируем подсказку, чтобы она не выходила за границы экрана
                        let tooltipX = Math.min(x + 10, canvas.clientWidth - 150);
                        let tooltipY = Math.max(y - 10, 10);

                        // Если подсказка слишком низко, показываем ее выше
                        if (y > canvas.clientHeight - 80) {
                            tooltipY = y - 70;
                        }

                        tooltip.style.left = tooltipX + 'px';
                        tooltip.style.top = tooltipY + 'px';

                        const valueText = formatNumber(hoveredBar.value);

                        // Улучшенное форматирование подсказки
                        tooltip.innerHTML = `
                            <strong>${hoveredBar.date}</strong>
                            Собрано ключей: ${valueText}
                        `;
                    } else {
                        chartState.tooltip.style.display = 'none';
                    }

                    // Обновляем состояние графика
                    chartState.hoveredBar = hoveredBar;
                }

                function calculateAxisStep(maxValue) {
                    // Помогает определить удобный шаг для оси
                    if (maxValue <= 5) return 1;
                    if (maxValue <= 20) return 5;
                    if (maxValue <= 50) return 10;
                    if (maxValue <= 100) return 20;
                    if (maxValue <= 500) return 100;
                    if (maxValue <= 1000) return 200;
                    if (maxValue <= 5000) return 1000;
                    if (maxValue <= 10000) return 2000;
                    if (maxValue <= 50000) return 10000;

                    // Для больших значений
                    const magnitude = Math.pow(10, Math.floor(Math.log10(maxValue)));
                    return Math.ceil(maxValue / 5 / magnitude) * magnitude;
                }

                function animateChart(timestamp) {
                    if (!chartState.animation.isAnimating) return;

                    if (!chartState.animation.startTime) {
                        chartState.animation.startTime = timestamp;
                    }

                    const elapsed = timestamp - chartState.animation.startTime;
                    const duration = ANIMATION_DURATION;

                    // Рассчитываем прогресс анимации (от 0 до 1) с эффектом ease-out
                    let progress = elapsed / duration;
                    progress = Math.min(1, progress);

                    // Применяем кривую плавности (ease-out)
                    const animationProgress = 1 - Math.pow(1 - progress, 3);

                    // Обновляем график с текущим прогрессом анимации
                    drawChart(animationProgress);

                    if (progress < 1) {
                        // Если анимация не завершена, запрашиваем следующий кадр
                        requestAnimationFrame(animateChart);
                    } else {
                        // Анимация завершена
                        chartState.animation.isAnimating = false;
                    }
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
                        // При изменении размера перерисовываем без анимации
                        drawChart(1);
                    });
                }

                // Инициализация с анимацией
                window.onload = function() {
                    setupEventListeners();

                    // Проверяем, нужно ли включать анимацию
                    if (ENABLE_ANIMATIONS) {
                        chartState.animation.isAnimating = true;
                        requestAnimationFrame(animateChart);
                    } else {
                        // Если анимация отключена, рисуем график сразу полностью
                        drawChart(1);
                    }
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
                    "keys_collected": []
                }

            # Сохраняем данные для возможной перерисовки при изменении размера
            self.last_data = trend_data

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
            "keys_collected": []
        }
        self.update_chart(empty_data)


class SilverChartWidget(ResponsiveChartWidget):
    """Виджет для отображения графика собранного серебра."""

    def __init__(self, parent=None):
        super().__init__("Сбор серебра (7 дней)", parent)

        # Настройка легенды для серебра
        silver_legend = QLabel("● Собрано серебра")
        silver_legend.setStyleSheet(f"color: {Styles.COLORS['primary']}; font-size: 12px;")
        self.legend_layout.addWidget(silver_legend)

        self.legend_layout.addStretch()

    def create_html_template(self):
        """Создает HTML-шаблон с улучшенным Canvas-графиком для серебра."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Silver Chart</title>
            <style>
                :root {
                    --bg-color: #171D33;
                    --grid-color: #28304d;
                    --text-color: #FFFFFF;
                    --text-secondary: #9BA0BC;
                    --silver-color: #3FE0C8;
                    --tooltip-bg: #2A3158;
                    --tooltip-border: #353E65;
                }

                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    margin: 0;
                    padding: 0;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    font-family: 'Segoe UI', Arial, sans-serif;
                    overflow: hidden;
                    height: 100vh;
                    width: 100vw;
                }

                #chart-container {
                    width: 100%;
                    height: 100%;
                    position: relative;
                }

                canvas {
                    width: 100%;
                    height: 100%;
                    position: absolute;
                    top: 0;
                    left: 0;
                }

                .tooltip {
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
                }

                .tooltip strong {
                    display: block;
                    margin-bottom: 4px;
                    color: var(--silver-color);
                }

                .no-data {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: var(--text-secondary);
                    font-size: 14px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div id="chart-container">
                <canvas id="silver-chart"></canvas>
                <div id="tooltip" class="tooltip"></div>
                <div id="no-data" class="no-data" style="display:none;">Нет данных для отображения</div>
            </div>

            <script>
                // Данные будут добавлены динамически
                const chartData = CHART_DATA_PLACEHOLDER;

                // Настройки анимации
                const ENABLE_ANIMATIONS = window.innerWidth > 600;
                const ANIMATION_DURATION = 800;

                // Объект для отслеживания состояния графика
                const chartState = {
                    hoveredBar: null,
                    tooltip: document.getElementById('tooltip'),
                    noDataMessage: document.getElementById('no-data'),
                    canvas: null,
                    ctx: null,
                    layout: {
                        padding: null,
                        graphArea: { x: 0, y: 0, width: 0, height: 0 }
                    },
                    mouse: { x: 0, y: 0 },
                    bars: [],
                    devicePixelRatio: window.devicePixelRatio || 1,
                    // Для анимации
                    animation: {
                        progress: 0,
                        startTime: 0,
                        isAnimating: false
                    }
                };

                function formatNumber(num) {
                    return num.toLocaleString('ru-RU', {
                        minimumFractionDigits: 1,
                        maximumFractionDigits: 1
                    });
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
                    let rightPadding = Math.max(20, width * 0.03); // Уменьшаем правый отступ, т.к. нет второй оси Y
                    let topPadding = Math.max(15, height * 0.06);
                    let bottomPadding = Math.max(25, height * 0.1);

                    return {
                        left: leftPadding,
                        right: rightPadding, 
                        top: topPadding,
                        bottom: bottomPadding
                    };
                }

                function drawChart(animationProgress = 1) {
                    const canvas = document.getElementById('silver-chart');
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
                        chartState.noDataMessage.style.display = 'block';
                        return;
                    } else {
                        chartState.noDataMessage.style.display = 'none';
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
                    let maxSilver = 0;

                    for (let i = 0; i < chartData.dates.length; i++) {
                        const silver = chartData.silver_collected[i] || 0;
                        maxSilver = Math.max(maxSilver, silver);
                    }

                    // Защита от нулевых максимумов
                    maxSilver = maxSilver || 10;

                    // Округляем maxSilver до ближайшего большего "красивого" числа
                    maxSilver = calculateAxisMaxValue(maxSilver);

                    // Рисуем оси и сетку
                    drawAxes(ctx, padding, graphWidth, graphHeight, maxSilver, rect.width, rect.height);

                    // Сбрасываем массивы элементов для интерактивности
                    chartState.bars = [];

                    // Отрисовка столбцов серебра с учетом анимации
                    drawBars(ctx, padding, graphWidth, graphHeight, maxSilver, rect.width, rect.height, animationProgress);
                }

                function calculateAxisMaxValue(value) {
                    // Округляем до ближайшего большего "красивого" числа для оси
                    // Для чисел серебра, которые обычно в K (тысячах)
                    if (value <= 5) return 5;
                    if (value <= 10) return 10;
                    if (value <= 25) return 25;
                    if (value <= 50) return 50;
                    if (value <= 100) return 100;

                    // Для больших чисел, округляем до ближайшей сотни или тысячи
                    const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
                    return Math.ceil(value / magnitude) * magnitude;
                }

                function drawAxes(ctx, padding, graphWidth, graphHeight, maxSilver, canvasWidth, canvasHeight) {
                    const baselineY = canvasHeight - padding.bottom;
                    const baselineX = padding.left;
                    const fontSize = getOptimalFontSize();

                    // Фон области графика (полупрозрачный)
                    ctx.fillStyle = 'rgba(20, 26, 47, 0.5)';
                    ctx.fillRect(padding.left, padding.top, graphWidth, graphHeight);

                    // Отрисовка сетки
                    ctx.strokeStyle = 'rgba(40, 48, 77, 0.8)';
                    ctx.lineWidth = 0.8;
                    ctx.beginPath();

                    // Определяем интервалы для шкалы серебра
                    const silverStep = calculateAxisStep(maxSilver);
                    const numSilverLines = Math.floor(maxSilver / silverStep) + 1;

                    // Горизонтальные линии сетки (шкала серебра)
                    for (let i = 0; i < numSilverLines; i++) {
                        const value = i * silverStep;
                        const y = baselineY - (value / maxSilver) * graphHeight;

                        ctx.moveTo(baselineX, y);
                        ctx.lineTo(baselineX + graphWidth, y);

                        // Подпись значения оси Y (серебро)
                        if (canvasWidth > 300) {
                            ctx.fillStyle = 'rgba(155, 160, 188, 0.7)';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'right';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(value.toFixed(1) + 'K', baselineX - 5, y);
                        }
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

                        // Рисуем вертикальную линию сетки
                        ctx.moveTo(x, padding.top);
                        ctx.lineTo(x, baselineY);

                        // Подпись даты (пропускаем некоторые для экономии места)
                        if (i % skipFactor === 0 || i === dataLength - 1) {
                            ctx.fillStyle = 'rgba(155, 160, 188, 0.9)';
                            ctx.font = `${fontSize}px Arial`;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'top';
                            ctx.fillText(chartData.dates[i], x, baselineY + 5);
                        }
                    }

                    ctx.stroke();

                    // Горизонтальная базовая линия
                    ctx.beginPath();
                    ctx.strokeStyle = 'rgba(155, 160, 188, 0.3)';
                    ctx.lineWidth = 1;
                    ctx.moveTo(padding.left, baselineY);
                    ctx.lineTo(padding.left + graphWidth, baselineY);
                    ctx.stroke();
                }

                function drawBars(ctx, padding, graphWidth, graphHeight, maxSilver, canvasWidth, canvasHeight, animationProgress) {
                    const baselineY = canvasHeight - padding.bottom;
                    const dataLength = chartData.dates.length;

                    // Вычисляем оптимальную ширину столбцов (можем сделать их шире, т.к. только один тип столбцов)
                    const maxBarWidth = 60;
                    let barWidth = Math.min((graphWidth / dataLength) * 0.8, maxBarWidth);

                    for (let i = 0; i < dataLength; i++) {
                        const x = padding.left + ((i + 0.5) * (graphWidth / dataLength));
                        const barX = x - (barWidth / 2);

                        const silver = chartData.silver_collected[i] || 0;

                        // Вычисляем высоту столбца с учетом анимации
                        const silverHeight = (silver / maxSilver) * graphHeight * animationProgress;

                        // Создаем градиент для столбца серебра
                        const silverGradient = ctx.createLinearGradient(0, baselineY - silverHeight, 0, baselineY);
                        silverGradient.addColorStop(0, 'rgba(63, 224, 200, 1)');    // Ярче вверху
                        silverGradient.addColorStop(1, 'rgba(63, 224, 200, 0.7)');  // Более прозрачный внизу

                        // Рисуем столбец серебра
                        ctx.fillStyle = silverGradient;
                        const silverRect = {
                            x: barX,
                            y: baselineY - silverHeight,
                            width: barWidth,
                            height: Math.max(1, silverHeight),
                            value: silver,
                            date: chartData.dates[i],
                            index: i
                        };

                        // Скругленные углы для верхней части
                        const radius = Math.min(4, barWidth / 4);

                        // Рисуем столбец со скругленными углами вверху
                        ctx.beginPath();
                        ctx.moveTo(silverRect.x + radius, silverRect.y);
                        ctx.lineTo(silverRect.x + silverRect.width - radius, silverRect.y);
                        ctx.quadraticCurveTo(silverRect.x + silverRect.width, silverRect.y, silverRect.x + silverRect.width, silverRect.y + radius);
                        ctx.lineTo(silverRect.x + silverRect.width, silverRect.y + silverRect.height);
                        ctx.lineTo(silverRect.x, silverRect.y + silverRect.height);
                        ctx.lineTo(silverRect.x, silverRect.y + radius);
                        ctx.quadraticCurveTo(silverRect.x, silverRect.y, silverRect.x + radius, silverRect.y);
                        ctx.closePath();
                        ctx.fill();

                        // Добавляем блик на столбце
                        const highlightWidth = barWidth * 0.4;
                        const highlightGradient = ctx.createLinearGradient(
                            silverRect.x + barWidth * 0.3, silverRect.y,
                            silverRect.x + barWidth * 0.3 + highlightWidth, silverRect.y
                        );
                        highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.2)');
                        highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

                        ctx.fillStyle = highlightGradient;
                        ctx.beginPath();
                        ctx.moveTo(silverRect.x + barWidth * 0.3, silverRect.y);
                        ctx.lineTo(silverRect.x + barWidth * 0.3 + highlightWidth, silverRect.y);
                        ctx.lineTo(silverRect.x + barWidth * 0.3 + highlightWidth, silverRect.y + silverRect.height);
                        ctx.lineTo(silverRect.x + barWidth * 0.3, silverRect.y + silverRect.height);
                        ctx.closePath();
                        ctx.fill();

                        chartState.bars.push(silverRect);
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

                    // Обновляем подсказку
                    if (hoveredBar) {
                        const tooltip = chartState.tooltip;
                        tooltip.style.display = 'block';

                        // Позиционируем подсказку, чтобы она не выходила за границы экрана
                        let tooltipX = Math.min(x + 10, canvas.clientWidth - 150);
                        let tooltipY = Math.max(y - 10, 10);

                        // Если подсказка слишком низко, показываем ее выше
                        if (y > canvas.clientHeight - 80) {
                            tooltipY = y - 70;
                        }

                        tooltip.style.left = tooltipX + 'px';
                        tooltip.style.top = tooltipY + 'px';

                        const valueText = formatNumber(hoveredBar.value) + "K";

                        // Улучшенное форматирование подсказки
                        tooltip.innerHTML = `
                            <strong>${hoveredBar.date}</strong>
                            Собрано серебра: ${valueText}
                        `;
                    } else {
                        chartState.tooltip.style.display = 'none';
                    }

                    // Обновляем состояние графика
                    chartState.hoveredBar = hoveredBar;
                }

                function calculateAxisStep(maxValue) {
                    // Помогает определить удобный шаг для оси
                    if (maxValue <= 5) return 1;
                    if (maxValue <= 10) return 2;
                    if (maxValue <= 25) return 5;
                    if (maxValue <= 50) return 10;
                    if (maxValue <= 100) return 20;
                    if (maxValue <= 200) return 50;
                    if (maxValue <= 500) return 100;
                    if (maxValue <= 1000) return 200;

                    // Для больших значений
                    const magnitude = Math.pow(10, Math.floor(Math.log10(maxValue)));
                    return Math.ceil(maxValue / 5 / magnitude) * magnitude;
                }

                function animateChart(timestamp) {
                    if (!chartState.animation.isAnimating) return;

                    if (!chartState.animation.startTime) {
                        chartState.animation.startTime = timestamp;
                    }

                    const elapsed = timestamp - chartState.animation.startTime;
                    const duration = ANIMATION_DURATION;

                    // Рассчитываем прогресс анимации (от 0 до 1) с эффектом ease-out
                    let progress = elapsed / duration;
                    progress = Math.min(1, progress);

                    // Применяем кривую плавности (ease-out)
                    const animationProgress = 1 - Math.pow(1 - progress, 3);

                    // Обновляем график с текущим прогрессом анимации
                    drawChart(animationProgress);

                    if (progress < 1) {
                        // Если анимация не завершена, запрашиваем следующий кадр
                        requestAnimationFrame(animateChart);
                    } else {
                        // Анимация завершена
                        chartState.animation.isAnimating = false;
                    }
                }

                // Обработчики событий
                function setupEventListeners() {
                    const canvas = document.getElementById('silver-chart');

                    canvas.addEventListener('mousemove', checkForInteractions);

                    canvas.addEventListener('mouseleave', function() {
                        chartState.tooltip.style.display = 'none';
                    });

                    // Обработка изменения размера
                    window.addEventListener('resize', function() {
                        // При изменении размера перерисовываем без анимации
                        drawChart(1);
                    });
                }

                // Инициализация с анимацией
                window.onload = function() {
                    setupEventListeners();

                    // Проверяем, нужно ли включать анимацию
                    if (ENABLE_ANIMATIONS) {
                        chartState.animation.isAnimating = true;
                        requestAnimationFrame(animateChart);
                    } else {
                        // Если анимация отключена, рисуем график сразу полностью
                        drawChart(1);
                    }
                };
            </script>
        </body>
        </html>
        """

        try:
            # Создаем временный файл
            import tempfile
            import os
            fd, self.html_path = tempfile.mkstemp(suffix=".html", prefix="aom_silver_chart_")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self._py_logger.debug(f"Создан шаблон графика серебра: {self.html_path}")
        except Exception as e:
            self._py_logger.error(f"Ошибка при создании HTML-шаблона графика серебра: {e}")

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
                self._py_logger.warning("Пустой набор данных для графика серебра")

                # Создаем пустой набор данных для отображения сообщения
                trend_data = {
                    "dates": [],
                    "silver_collected": []
                }

            # Сохраняем данные для возможной перерисовки при изменении размера
            self.last_data = trend_data

            # Подготовка данных для JSON
            import json
            json_data = json.dumps(trend_data)

            # Замена плейсхолдера данными
            updated_html = html_content.replace('CHART_DATA_PLACEHOLDER', json_data)

            # Запись обновленного HTML
            with open(self.html_path, 'w', encoding='utf-8') as f:
                f.write(updated_html)

            # Загрузка обновленного HTML в WebView
            from PyQt6.QtCore import QUrl
            self.web_view.load(QUrl.fromLocalFile(self.html_path))
            self._py_logger.debug("График серебра обновлен")

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении графика серебра: {e}")

    def clear(self):
        """Очищает график."""
        empty_data = {
            "dates": [],
            "silver_collected": []
        }
        self.update_chart(empty_data)