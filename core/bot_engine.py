import time
import logging
import threading
from enum import Enum, auto
from typing import Dict, Tuple, Optional, List, Callable
from core.stats_manager import StatsManager


class BotState(Enum):
    """Possible states of the bot."""
    IDLE = auto()
    STARTING = auto()
    SELECTING_BATTLE = auto()
    CONFIRMING_BATTLE = auto()
    IN_BATTLE = auto()
    BATTLE_ENDED = auto()
    CONNECTION_LOST = auto()
    RECONNECTING = auto()
    ERROR = auto()


class BotEngine:
    """Main bot logic and state management."""

    def __init__(self, adb_controller, image_matcher):
        self.adb = adb_controller
        self.image_matcher = image_matcher
        self.logger = logging.getLogger("BotLogger")

        # Event to control the bot thread
        self.running = threading.Event()

        # Current state of the bot
        self.state = BotState.IDLE

        # Click coordinates for different actions
        self.click_coords = {
            "start_battle": (1227, 832),
            "confirm_battle": (1430, 830),
            "auto_battle": (66, 642),
            "exit_after_win": (743, 819),
            "refresh_opponents": (215, 826),
            "reconnect_button": (803, 821)
        }

        # Define actions for different bot states
        self.state_actions = {
            BotState.IDLE: self._handle_idle,
            BotState.STARTING: self._handle_starting,
            BotState.SELECTING_BATTLE: self._handle_selecting_battle,
            BotState.CONFIRMING_BATTLE: self._handle_confirming_battle,
            BotState.IN_BATTLE: self._handle_in_battle,
            BotState.BATTLE_ENDED: self._handle_battle_ended,
            BotState.CONNECTION_LOST: self._handle_connection_lost,
            BotState.RECONNECTING: self._handle_reconnecting,
            BotState.ERROR: self._handle_error
        }

        # Bot statistics
        self.stats = {
            "battles_started": 0,
            "victories": 0,
            "defeats": 0,
            "connection_losses": 0,
            "errors": 0,
            "keys_collected": 0,  # Статистика по ключам
            "silver_collected": 0  # Новая статистика по серебру
        }

        # Инициализация stats_manager
        self.stats_manager = None  # Будет установлен позже в main.py

        # Signals for communicating with the UI (will be set in the main application)
        self.signals = None

    def set_signals(self, signals):
        """Sets the signals object for UI communication."""
        self.signals = signals

    def capture_screen(self):
        """Captures the screen and returns the data."""
        return self.adb.capture_screen()

    def start(self):
        """Starts the bot in a separate thread."""
        if not self.running.is_set():
            if not self.adb.check_connection():
                self.logger.error("🚨 ADB не подключен. Проверьте настройки эмулятора!")
                if self.signals:
                    self.signals.error.emit("ADB не подключен. Проверьте настройки эмулятора!")
                return False

            self.running.set()
            self.state = BotState.STARTING
            threading.Thread(target=self._bot_loop, daemon=True).start()
            self.logger.info("▶ Бот запущен")
            return True
        return False

    def stop(self):
        """Stops the bot."""
        if self.running.is_set():
            # Перед остановкой бота сохраняем собранные в текущей сессии ключи в stats_manager.keys_current
            if hasattr(self, 'stats_manager') and self.stats_manager:
                current_keys = self.stats.get("keys_collected", 0)
                if current_keys > 0 and hasattr(self.stats_manager, 'keys_current'):
                    self.logger.info(f"Добавляем {current_keys} ключей из текущей сессии к общему прогрессу")
                    # Сохраняем текущее значение в stats_manager.keys_current
                    self.stats_manager.keys_current += current_keys

            # Сохраняем статистику ПЕРЕД сбросом self.running, чтобы сохранилась текущая сессия
            if self.stats_manager:
                self.logger.info("Сохранение статистики перед остановкой бота")
                # Сначала сохраняем прогресс ключей (чтобы гарантировать сохранение)
                if hasattr(self.stats_manager, 'save_keys_progress'):
                    self.stats_manager.save_keys_progress()
                # Затем сохраняем общую статистику
                self.stats_manager.save_stats()

            # Теперь можно остановить бота
            self.running.clear()
            self.state = BotState.IDLE
            self.logger.info("⛔ Бот остановлен")

            return True
        return False

    def _bot_loop(self):
        """Main bot loop that handles state transitions and actions."""
        round_count = 0
        try:
            while self.running.is_set():
                # Call the appropriate handler for the current state
                handler = self.state_actions.get(self.state)
                if handler:
                    # State handlers return the next state
                    next_state = handler()
                    if next_state and next_state != self.state:
                        self.logger.info(f"Переход состояния: {self.state} -> {next_state}")
                        self.state = next_state

                        # Update UI with state change
                        if self.signals:
                            self.signals.state_changed.emit(self.state.name)
                else:
                    self.logger.error(f"🚨 Нет обработчика для состояния: {self.state}")
                    self.state = BotState.ERROR

                # Short sleep to prevent CPU hogging
                time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"🚨 Ошибка в цикле бота: {e}")
            self.state = BotState.ERROR
            self.stats["errors"] += 1
            if self.signals:
                self.signals.error.emit(f"Ошибка бота: {e}")
        finally:
            # Clean up when the bot stops
            self.running.clear()
            self.state = BotState.IDLE
            if self.signals:
                self.signals.state_changed.emit(self.state.name)

    def _handle_idle(self):
        """Handler for IDLE state."""
        # In the idle state, we just wait for the start command
        time.sleep(0.5)
        return BotState.IDLE

    def _handle_starting(self):
        """Handler for STARTING state."""
        self.logger.info("🔄 Запуск бота...")

        # Look for the battle screen
        self.logger.info("Делаем скриншот экрана...")
        screen_data = self.capture_screen()
        if screen_data:
            self.logger.info("Скриншот получен, анализируем...")

            # Check for connection issues first
            if self._check_connection_issues(screen_data):
                self.logger.info("Обнаружены проблемы с соединением")
                return BotState.CONNECTION_LOST

            # Check if we're already on the battle screen
            if self.image_matcher.find_in_screen(screen_data, "cheak.png"):
                self.logger.info("Найден экран выбора боя (cheak.png)")
                return BotState.SELECTING_BATTLE

            # Check if we're at the battle confirmation screen
            if self.image_matcher.find_in_screen(screen_data, "confirm_battle.png"):
                self.logger.info("Найден экран подтверждения боя (confirm_battle.png)")
                return BotState.CONFIRMING_BATTLE

            # Check if we're already in a battle
            if self.image_matcher.find_in_screen(screen_data, "auto_battle.png"):
                self.logger.info("Найден экран боя (auto_battle.png)")
                return BotState.IN_BATTLE

            # Check if a battle just ended
            victory_found = self.image_matcher.find_in_screen(screen_data, "victory.png")
            defeat_found = self.image_matcher.find_in_screen(screen_data, "defeat.png")

            if victory_found:
                self.logger.info("Найден экран победы (victory.png)")
                return BotState.BATTLE_ENDED
            elif defeat_found:
                self.logger.info("Найден экран поражения (defeat.png)")
                return BotState.BATTLE_ENDED

            self.logger.warning("Не удалось найти ни один известный экран")
        else:
            self.logger.error("Не удалось получить скриншот экрана")

        # If we couldn't find a known screen, wait and try again
        self.logger.info("Ожидаем 2 секунды и пробуем снова...")
        time.sleep(2)
        return BotState.STARTING

    def _handle_selecting_battle(self):
        """Handler for SELECTING_BATTLE state."""
        self.logger.info("Выбор боя...")
        self.adb.tap(*self.click_coords["start_battle"])
        time.sleep(2)
        return BotState.CONFIRMING_BATTLE

    def _handle_confirming_battle(self):
        """Handler for CONFIRMING_BATTLE state."""
        self.logger.info("Подтверждение боя...")
        self.adb.tap(*self.click_coords["confirm_battle"])
        self.stats["battles_started"] += 1

        # Wait for the auto battle button to appear
        _, match_loc = self.image_matcher.wait_for_images(
            self.capture_screen, ["auto_battle.png"], timeout=50, check_interval=3
        )

        if match_loc:
            return BotState.IN_BATTLE
        else:
            self.logger.error("🚨 Кнопка автобоя не найдена!")

            # Check for connection issues
            screen_data = self.capture_screen()
            if screen_data and self._check_connection_issues(screen_data):
                return BotState.CONNECTION_LOST

            return BotState.ERROR

    def update_settings(self, battle_timeout=None, max_refresh_attempts=None):
        """Обновляет настройки бота во время выполнения.

        Args:
            battle_timeout (int, optional): Время ожидания боя в секундах
            max_refresh_attempts (int, optional): Максимальное количество попыток обновления
        """
        from config import config

        # Обновляем только если значения переданы
        if battle_timeout is not None:
            self.logger.info(f"Обновлено время ожидания боя: {battle_timeout} сек")

        if max_refresh_attempts is not None:
            self.logger.info(f"Обновлено макс. количество попыток обновления: {max_refresh_attempts}")

        # Логируем обновление настроек
        self.logger.info("Настройки бота обновлены")

    def _handle_in_battle(self):
        """Handler for IN_BATTLE state."""
        from config import config

        self.logger.info("В бою, включаем автобой...")
        self.adb.tap(*self.click_coords["auto_battle"])

        # Получаем значения из конфигурации
        battle_timeout = config.get("bot", "battle_timeout", 120)
        check_interval = config.get("bot", "check_interval", 3)

        self.logger.info(f"Ожидание окончания боя (таймаут: {battle_timeout} сек)...")

        # Wait for battle to end (victory or defeat)
        result, _ = self.image_matcher.wait_for_images(
            self.capture_screen, ["victory.png", "defeat.png"],
            timeout=battle_timeout,
            check_interval=check_interval
        )

        if result:
            return BotState.BATTLE_ENDED
        else:
            # Check for connection issues
            screen_data = self.capture_screen()
            if screen_data and self._check_connection_issues(screen_data):
                return BotState.CONNECTION_LOST

            # Battle seems to be stuck, try emergency clicks
            self.logger.warning("⚠ Бой, похоже, застрял! Выполняем экстренные нажатия.")
            self._perform_emergency_clicks()
            return BotState.STARTING

    def _handle_battle_ended(self):
        """Handler for BATTLE_ENDED state."""
        from config import config

        # Check which result screen we're on
        screen_data = self.capture_screen()
        if not screen_data:
            return BotState.ERROR

        if self.image_matcher.find_in_screen(screen_data, "victory.png"):
            self.logger.info("🏆 Победа! Анализ полученных наград...")
            self.stats["victories"] += 1

            # Detect and count keys before clicking to exit
            keys_count = self.image_matcher.detect_keys(screen_data)
            if keys_count > 0:
                self.stats["keys_collected"] += keys_count
                self.logger.info(f"🔑 Получено {keys_count} ключей. Всего собрано: {self.stats['keys_collected']}")

                if hasattr(self, 'stats_manager') and self.stats_manager is not None:
                    # Просто для отладки записываем значение до и после
                    old_keys_current = getattr(self.stats_manager, 'keys_current', 0)

                    # Обновляем только общий прогресс, но не текущую сессию
                    # Текущая сессия обновляется выше через self.stats["keys_collected"]
                    if hasattr(self.stats_manager, 'keys_current'):
                        # Не добавляем ключи дважды, так как они уже будут добавлены
                        # при вызове save_stats() или при закрытии приложения
                        # self.stats_manager.keys_current += keys_count
                        self.logger.debug(f"Текущий общий прогресс ключей: {self.stats_manager.keys_current}")

            # Detect and count silver before clicking to exit
            silver_count = self.image_matcher.detect_silver(screen_data)
            if silver_count > 0:
                self.stats["silver_collected"] += silver_count
                self.logger.info(
                    f"🔶 Получено {silver_count}K серебра. Всего собрано: {self.stats['silver_collected']}K")

            # If signals is set, emit stats_updated to refresh UI
            if self.signals:
                self.signals.stats_updated.emit(self.stats)

            # Continue with normal flow - exit after win
            self.adb.tap(*self.click_coords["exit_after_win"])
            time.sleep(5)

            # Обновление статистики в реальном времени
            if self.stats_manager:
                self.stats_manager.update_stats(self.stats)

            return BotState.STARTING

        elif self.image_matcher.find_in_screen(screen_data, "defeat.png"):
            self.logger.info("❌ Поражение! Обновляем список соперников и пробуем снова.")
            self.stats["defeats"] += 1

            # НОВЫЙ КОД: Эмитируем сигнал обновления статистики
            if self.signals:
                self.signals.stats_updated.emit(self.stats)

            self.adb.tap(*self.click_coords["exit_after_win"])
            time.sleep(10)

            # Проверяем, не превышено ли максимальное количество попыток обновления
            max_refresh = config.get("bot", "max_refresh_attempts", 3)
            self.logger.info(f"Обновление списка соперников (макс. попыток: {max_refresh})...")

            self.adb.tap(*self.click_coords["refresh_opponents"])
            time.sleep(2)

            # Обновление статистики в реальном времени
            if self.stats_manager:
                self.stats_manager.update_stats(self.stats)

            return BotState.STARTING

        # Обновление статистики в любом случае
        if self.stats_manager:
            self.stats_manager.update_stats(self.stats)

        return BotState.STARTING

    def _handle_connection_lost(self):
        """Handler for CONNECTION_LOST state."""
        self.logger.warning("⚠ Соединение с сервером потеряно! Пытаемся переподключиться...")
        self.stats["connection_losses"] += 1

        # Wait for the "Связаться с нами" button to appear
        screen_data = self.capture_screen()
        if not screen_data:
            return BotState.ERROR

        # Check if we already see the contact us button
        if self.image_matcher.find_in_screen(screen_data, "contact_us.png"):
            # Click on the "Связаться с нами" button at coordinates 803, 821
            self.adb.tap(*self.click_coords["reconnect_button"])
            time.sleep(7)
            return BotState.RECONNECTING

        # If not, wait for it to appear
        result, _ = self.image_matcher.wait_for_images(
            self.capture_screen, ["contact_us.png"], timeout=60, check_interval=3
        )

        if result:
            self.adb.tap(*self.click_coords["reconnect_button"])
            time.sleep(7)
            return BotState.RECONNECTING
        else:
            self.logger.error("🚨 Не удалось найти кнопку переподключения!")
            return BotState.ERROR

    def _handle_reconnecting(self):
        """Handler for RECONNECTING state - implements the recovery algorithm."""
        self.logger.info("Переподключение к игре...")

        # Try to find cheak.png or confirm_battle.png first (5 seconds)
        result, _ = self.image_matcher.wait_for_images(
            self.capture_screen,
            ["cheak.png", "confirm_battle.png"],
            timeout=5,
            check_interval=1
        )

        if result == "cheak.png":
            return BotState.SELECTING_BATTLE
        elif result == "confirm_battle.png":
            return BotState.CONFIRMING_BATTLE

        # If not found, try to find victory.png or defeat.png (another 5 seconds)
        result, _ = self.image_matcher.wait_for_images(
            self.capture_screen,
            ["victory.png", "defeat.png"],
            timeout=5,
            check_interval=1
        )

        if result in ["victory.png", "defeat.png"]:
            return BotState.BATTLE_ENDED

        # If still not found, look for auto_battle.png
        result, _ = self.image_matcher.wait_for_images(
            self.capture_screen,
            ["auto_battle.png"],
            timeout=5,
            check_interval=1
        )

        if result == "auto_battle.png":
            return BotState.IN_BATTLE

        # If we still can't find any known screens, return to starting state
        self.logger.warning("⚠ Не удалось определить состояние игры после переподключения. Перезапуск...")
        return BotState.STARTING

    def _handle_error(self):
        """Handler for ERROR state."""
        self.logger.error("🚨 Бот столкнулся с ошибкой. Пытаемся восстановиться...")
        time.sleep(5)
        return BotState.STARTING

    def _check_connection_issues(self, screen_data: bytes) -> bool:
        """
        Checks if there are connection issues on the current screen.

        Returns:
            True if connection issues detected, False otherwise
        """
        # Check for "Ожидание ответа от сервера" message
        if self.image_matcher.find_in_screen(screen_data, "waiting_for_server.png"):
            self.logger.warning("⚠ Обнаружено сообщение 'Ожидание ответа от сервера'")
            return True

        # Check for "Связаться с нами" button
        if self.image_matcher.find_in_screen(screen_data, "contact_us.png"):
            self.logger.warning("⚠ Обнаружена кнопка 'Связаться с нами'")
            return True

        return False

    def _perform_emergency_clicks(self):
        """Performs emergency clicks to try to recover from a stuck state."""
        self.logger.warning("⚠ Выполнение экстренных нажатий...")

        # Click back button
        self.adb.tap(49, 50)
        time.sleep(2)

        # Click center of screen
        self.adb.tap(588, 825)
        time.sleep(2)

        # Click exit button position
        self.adb.tap(743, 819)
        time.sleep(10)

        # Click refresh button position
        self.adb.tap(215, 826)
        time.sleep(2)