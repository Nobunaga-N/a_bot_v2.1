from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
import os

# Проверим, доступен ли модуль SVG
SVG_AVAILABLE = False
try:
    from PyQt6.QtSvg import QSvgRenderer

    SVG_AVAILABLE = True
except ImportError:
    print("Модуль QtSvg недоступен, SVG-иконки будут заменены на текст")


def load_svg_icon(svg_path, color=None, size=None):
    """
    Загружает SVG-файл и создает из него иконку, с возможностью изменения цвета.

    Args:
        svg_path (str): Путь к SVG-файлу
        color (str, optional): Код цвета в формате HEX (#RRGGBB)
        size (QSize, optional): Размер иконки

    Returns:
        QIcon: Иконка из SVG-файла или пустая иконка, если SVG недоступен
    """
    if not os.path.exists(svg_path):
        return QIcon()

    if not SVG_AVAILABLE:
        # Если модуль SVG недоступен, возвращаем просто иконку из файла
        # (будет работать как обычное изображение без специальной обработки)
        return QIcon(svg_path)

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
    В этой версии просто возвращает обычную иконку, так как
    изменение цвета требует специальных возможностей SVG.

    Args:
        svg_path (str): Путь к SVG-файлу или PNG-файлу
        color (str): Код цвета в формате HEX (#RRGGBB) - игнорируется, если SVG недоступен
        size (QSize, optional): Размер иконки

    Returns:
        QIcon: Иконка
    """
    # Проверяем доступность SVG и существование файла
    if not SVG_AVAILABLE or not os.path.exists(svg_path):
        # Если это PNG или SVG недоступен, просто возвращаем иконку
        if svg_path.lower().endswith('.png'):
            return QIcon(svg_path)
        elif os.path.exists(svg_path.replace('.svg', '.png')):
            return QIcon(svg_path.replace('.svg', '.png'))
        return QIcon()

    # Если SVG доступен, используем его
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

    # Определяем цвет в зависимости от состояния
    color = Styles.COLORS["primary"] if active else Styles.COLORS["text_secondary"]

    # Сначала проверяем SVG
    if os.path.exists(svg_path):
        return get_colored_icon(svg_path, color, size)
    # Если SVG не найден, проверяем PNG
    elif os.path.exists(png_path):
        return QIcon(png_path)
    else:
        return QIcon()