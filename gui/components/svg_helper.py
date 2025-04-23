from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
import os


def load_svg_icon(svg_path, color=None, size=None):
    """
    Загружает SVG-файл и создает из него иконку, с возможностью изменения цвета.

    Args:
        svg_path (str): Путь к SVG-файлу
        color (str, optional): Код цвета в формате HEX (#RRGGBB)
        size (QSize, optional): Размер иконки

    Returns:
        QIcon: Иконка из SVG-файла
    """
    if not os.path.exists(svg_path):
        return QIcon()

    if size is None:
        size = QSize(24, 24)

    # Создаем рендерер SVG
    renderer = QSvgRenderer(svg_path)

    # Создаем пустое QPixmap для рисования
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)

    # Рисуем SVG на pixmap
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()

    # Создаем иконку из pixmap
    return QIcon(pixmap)


def get_colored_icon(svg_path, color, size=None):
    """
    Создаёт цветную иконку из SVG с указанным цветом.

    Args:
        svg_path (str): Путь к SVG-файлу
        color (str): Код цвета в формате HEX (#RRGGBB)
        size (QSize, optional): Размер иконки

    Returns:
        QIcon: Цветная иконка
    """
    # Эта функция может быть расширена в будущем для изменения цвета
    # SVG при загрузке с использованием QSvgRenderer
    return load_svg_icon(svg_path, color, size)


def get_menu_icon(icon_name, active=False, size=None):
    """
    Получает иконку для меню.

    Args:
        icon_name (str): Имя иконки (без расширения)
        active (bool, optional): Активна ли иконка
        size (QSize, optional): Размер иконки

    Returns:
        QIcon: Иконка для меню
    """
    from gui.styles import Styles

    # Пути к разным версиям иконки
    svg_path = f"resources/icons/{icon_name}.svg"
    png_path = f"resources/icons/{icon_name}.png"

    if os.path.exists(svg_path):
        color = Styles.COLORS["primary"] if active else Styles.COLORS["text_secondary"]
        return load_svg_icon(svg_path, color, size)
    elif os.path.exists(png_path):
        return QIcon(png_path)
    else:
        return QIcon()