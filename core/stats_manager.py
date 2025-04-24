import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional


class StatsManager:
    """
    Manages statistics for the bot, including persistence between sessions.

    Features:
    - Load and save statistics to a JSON file
    - Track statistics over time with timestamps
    - Provide aggregated statistics for different time periods
    - Maintain a historical record of all bot runs
    """

    def __init__(self, stats_dir: str):
        """
        Initialize the stats manager.

        Args:
            stats_dir: Directory to store statistics files
        """
        self.logger = logging.getLogger("BotLogger")
        self.stats_dir = stats_dir

        # Create stats directory if it doesn't exist
        if not os.path.exists(self.stats_dir):
            os.makedirs(self.stats_dir, exist_ok=True)

        # Path to the main stats file
        self.stats_file = os.path.join(self.stats_dir, "bot_stats.json")

        # Current session stats
        self.current_stats = {
            "battles_started": 0,
            "victories": 0,
            "defeats": 0,
            "connection_losses": 0,
            "errors": 0,
            "keys_collected": 0,
            "silver_collected": 0  # Добавляем учет серебра
        }

        # Historical stats with timestamps
        self.history = []

        # Session start time
        self.session_start = datetime.datetime.now()

        self.keys_target = 1000  # значение по умолчанию
        self.keys_current = 0  # текущее количество собранных ключей
        # Пытаемся загрузить цель и прогресс
        self.load_keys_progress()

        # Load previous stats
        self.load_stats()

        # Log initialization
        self.logger.info(f"Статистика инициализирована. Загружено {len(self.history)} исторических записей.")

    def load_stats(self) -> bool:
        """
        Load statistics from file.

        Returns:
            True if statistics were successfully loaded, False otherwise
        """
        if not os.path.exists(self.stats_file):
            self.logger.info("Файл статистики не найден. Будет создан новый файл.")
            return False

        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "history" in data:
                self.history = data["history"]

            if "total" in data:
                # Initialize current stats with total values
                for key in self.current_stats:
                    if key in data["total"]:
                        # Only keep the value for display purposes, will be added to later
                        pass

            self.logger.info("Статистика успешно загружена.")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке статистики: {e}")
            return False

    def save_stats(self) -> bool:
        """
        Save statistics to file.

        Returns:
            True if statistics were successfully saved, False otherwise
        """
        try:
            # Calculate total stats from history plus current session
            total_stats = self.get_total_stats()

            # Add current session to history if there are any battles
            if sum(self.current_stats.values()) > 0:
                session_end = datetime.datetime.now()

                # Проверка, чтобы не добавлять пустые сессии или дублирующиеся записи
                is_new_session = True

                # Проверяем, существует ли уже запись с тем же временем начала
                for record in self.history:
                    if record.get("start_time") == self.session_start.isoformat():
                        # Обновляем существующую запись
                        record["end_time"] = session_end.isoformat()
                        record["duration_seconds"] = (session_end - self.session_start).total_seconds()
                        record[
                            "stats"] = self.current_stats.copy()  # Используем copy() чтобы избежать проблем с указателями
                        is_new_session = False
                        break

                if is_new_session and any(val > 0 for val in self.current_stats.values()):
                    session_record = {
                        "start_time": self.session_start.isoformat(),
                        "end_time": session_end.isoformat(),
                        "duration_seconds": (session_end - self.session_start).total_seconds(),
                        "stats": self.current_stats.copy()  # Используем copy() чтобы избежать проблем с указателями
                    }

                    self.history.append(session_record)

            # Prepare data for saving
            data = {
                "total": total_stats,
                "history": self.history,
                "last_updated": datetime.datetime.now().isoformat()
            }

            # Save to file
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # Обновление общего прогресса ключей: добавляем ключи текущей сессии к общему прогрессу
            if hasattr(self, 'keys_current'):
                # Если в текущей сессии есть собранные ключи, добавляем их к общему прогрессу
                keys_collected = self.current_stats.get("keys_collected", 0)
                if keys_collected > 0:
                    # Сохраняем текущее значение ключей собранных в этой сессии для логирования
                    self.logger.info(
                        f"Добавляем {keys_collected} ключей из текущей сессии к общему прогрессу ({self.keys_current})")
                    # Добавляем собранные в текущей сессии ключи к общему прогрессу
                    self.keys_current += keys_collected
                    self.logger.info(f"Новое значение общего прогресса: {self.keys_current}")

                    # ВАЖНО: НЕ сбрасываем счетчик текущей сессии при остановке бота
                    # Это позволит правильно отображать статистику в интерфейсе
                    # self.current_stats["keys_collected"] = 0

                # Безусловно сохраняем текущее значение прогресса ключей, даже если в этой сессии не было собрано ключей
                self.save_keys_progress()

            self.logger.info("Статистика успешно сохранена.")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении статистики: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def update_stats(self, stats: Dict[str, int]) -> None:
        """
        Update the current session statistics.

        Args:
            stats: Dictionary with updated statistics
        """
        # Проверяем, изменилась ли статистика
        stats_changed = False
        for key, value in stats.items():
            if key in self.current_stats and self.current_stats[key] != value:
                self.current_stats[key] = value
                stats_changed = True

        # Если статистика изменилась, сохраняем её, но не слишком часто
        if stats_changed:
            # Используем счетчик для сохранения только каждые N обновлений
            # чтобы избежать частых операций записи на диск
            if not hasattr(self, '_update_counter'):
                self._update_counter = 0

            self._update_counter += 1
            if self._update_counter >= 5:  # Сохраняем каждые 5 изменений
                self.save_stats()
                self._update_counter = 0
                self.logger.debug("Автоматическое сохранение статистики выполнено")

    def reset_current_session(self) -> None:
        """Reset the current session statistics."""
        for key in self.current_stats:
            self.current_stats[key] = 0

        self.session_start = datetime.datetime.now()
        self.logger.info("Текущая сессия статистики сброшена.")

    def get_total_stats(self) -> Dict[str, int]:
        """
        Calculate total statistics from all historical records plus current session.

        Returns:
            Dictionary with total statistics
        """
        total = {key: 0 for key in self.current_stats}

        # Add up all historical stats
        for record in self.history:
            if "stats" in record:
                for key, value in record["stats"].items():
                    if key in total:
                        total[key] += value

        # Add current session stats
        for key, value in self.current_stats.items():
            total[key] += value

        return total

    def get_stats_by_period(self, period: str) -> Dict[str, Any]:
        """
        Get statistics aggregated by a specific time period.

        Args:
            period: Time period ("day", "week", "month", "all")

        Returns:
            Dictionary with aggregated statistics for the period
        """
        now = datetime.datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Define cutoff date based on period
        if period == "day":
            cutoff = today_start  # Начало текущего дня
        elif period == "week":
            cutoff = now - datetime.timedelta(weeks=1)
        elif period == "month":
            cutoff = now - datetime.timedelta(days=30)
        else:  # "all" or any other value
            cutoff = datetime.datetime.min

        # Filter history records by period
        filtered_records = []
        for record in self.history:
            try:
                end_time = datetime.datetime.fromisoformat(record["end_time"])
                if end_time >= cutoff:
                    filtered_records.append(record)
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Ошибка обработки записи истории: {e}")

        # Aggregate stats
        aggregated = {
            "period": period,
            "record_count": len(filtered_records),
            "total_duration_hours": 0,
            "stats": {key: 0 for key in self.current_stats}
        }

        # Add up stats from filtered records
        for record in filtered_records:
            if "duration_seconds" in record:
                aggregated["total_duration_hours"] += record["duration_seconds"] / 3600

            if "stats" in record:
                for key, value in record["stats"].items():
                    if key in aggregated["stats"]:
                        aggregated["stats"][key] += value

        # Add current session if applicable, только для текущего дня учитываем текущую сессию
        current_duration = (now - self.session_start).total_seconds() / 3600

        # Добавляем статистику текущей сессии только если просматриваем текущий день, неделю, месяц или все время
        if (period == "day" and self.session_start >= today_start) or period != "day":
            aggregated["total_duration_hours"] += current_duration

            for key, value in self.current_stats.items():
                aggregated["stats"][key] += value

        # Calculate derived statistics
        stats = aggregated["stats"]
        battles = stats["victories"] + stats["defeats"]

        if battles > 0:
            aggregated["win_rate"] = (stats["victories"] / battles) * 100
        else:
            aggregated["win_rate"] = 0

        if stats["victories"] > 0:
            aggregated["keys_per_victory"] = stats["keys_collected"] / stats["victories"]
        else:
            aggregated["keys_per_victory"] = 0

        if aggregated["total_duration_hours"] > 0:
            aggregated["battles_per_hour"] = battles / aggregated["total_duration_hours"]
            aggregated["keys_per_hour"] = stats["keys_collected"] / aggregated["total_duration_hours"]
        else:
            aggregated["battles_per_hour"] = 0
            aggregated["keys_per_hour"] = 0

        return aggregated

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get statistics broken down by day for the past N days.

        Args:
            days: Number of past days to include

        Returns:
            List of daily statistics dictionaries
        """
        daily_stats = []
        # Используем current_date для однозначного определения текущей даты
        current_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Initialize empty data for each day
        for i in range(days):
            # Создаем дату, начиная с текущего дня (i=0) и назад
            date = current_date - datetime.timedelta(days=i)
            day_data = {
                "date": date.strftime("%Y-%m-%d"),
                "display_date": date.strftime("%d.%m"),
                "stats": {key: 0 for key in self.current_stats}
            }
            daily_stats.append(day_data)

        # Process history records
        for record in self.history:
            try:
                # Преобразуем время окончания в объект datetime
                end_time = datetime.datetime.fromisoformat(record["end_time"])

                # Приводим к началу дня для корректного сравнения дат
                end_date = end_time.replace(hour=0, minute=0, second=0, microsecond=0)

                # Считаем разницу в днях между текущей датой и датой записи
                days_difference = (current_date - end_date).days

                # Если запись попадает в запрашиваемый период
                if 0 <= days_difference < days:
                    day_index = days_difference

                    # Add stats to the appropriate day
                    for key, value in record["stats"].items():
                        if key in daily_stats[day_index]["stats"]:
                            daily_stats[day_index]["stats"][key] += value
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Ошибка обработки записи истории для разбивки по дням: {e}")

        # Проверяем, относится ли текущая сессия к текущему дню
        session_start_day = self.session_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # Add current session stats to today (index 0) только если сессия начата сегодня
        if len(daily_stats) > 0 and session_start_day == current_date:
            for key, value in self.current_stats.items():
                daily_stats[0]["stats"][key] += value

        # Calculate additional metrics for each day
        for day in daily_stats:
            stats = day["stats"]
            battles = stats["victories"] + stats["defeats"]

            if battles > 0:
                day["win_rate"] = (stats["victories"] / battles) * 100
            else:
                day["win_rate"] = 0

            if stats["victories"] > 0:
                day["keys_per_victory"] = stats["keys_collected"] / stats["victories"]
            else:
                day["keys_per_victory"] = 0

        # Reverse to get chronological order (oldest to newest)
        daily_stats.reverse()
        return daily_stats

    def get_trend_data(self) -> Dict[str, List]:
        """
        Get data formatted for trend visualization.

        Returns:
            Dictionary with lists of data points for different metrics
        """
        # Get daily stats for the past 7 days in chronological order
        daily_data = self.get_daily_stats(7)

        trend_data = {
            "dates": [],
            "victories": [],
            "defeats": [],
            "win_rates": [],
            "keys_collected": [],
            "keys_per_victory": [],
            "silver_collected": []  # Добавляем данные по серебру
        }

        for day in daily_data:
            trend_data["dates"].append(day["display_date"])
            trend_data["victories"].append(day["stats"]["victories"])
            trend_data["defeats"].append(day["stats"]["defeats"])
            trend_data["win_rates"].append(round(day.get("win_rate", 0), 1))
            trend_data["keys_collected"].append(day["stats"]["keys_collected"])
            trend_data["keys_per_victory"].append(round(day.get("keys_per_victory", 0), 1))
            # Добавляем данные серебра
            trend_data["silver_collected"].append(day["stats"].get("silver_collected", 0))

        self.logger.debug(
            f"Тренд данные: даты={trend_data['dates']}, ключи={trend_data['keys_collected']}, серебро={trend_data['silver_collected']}")
        return trend_data

    def load_keys_progress(self):
        """Загружает цель и прогресс сбора ключей из файла."""
        progress_file = os.path.join(self.stats_dir, "keys_progress.json")

        self.logger.info(f"Попытка загрузки прогресса ключей из файла: {progress_file}")

        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Получаем значения с проверкой типов и лимитов
                try:
                    self.keys_target = int(data.get("target", 1000))
                    if self.keys_target <= 0:
                        self.logger.warning(
                            f"Некорректное значение target: {self.keys_target}, будет установлено значение по умолчанию")
                        self.keys_target = 1000
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Ошибка при конвертации target в int: {e}")
                    self.keys_target = 1000

                try:
                    self.keys_current = int(data.get("current", 0))
                    if self.keys_current < 0:
                        self.logger.warning(f"Отрицательное значение current: {self.keys_current}, будет установлен 0")
                        self.keys_current = 0
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Ошибка при конвертации current в int: {e}")
                    self.keys_current = 0

                self.logger.info(f"Загружен прогресс сбора ключей: {self.keys_current}/{self.keys_target}")

                # Важно: не присваиваем keys_current в current_stats["keys_collected"],
                # чтобы разделить общий прогресс и статистику текущей сессии
                # self.current_stats["keys_collected"] = 0

                return True
            except json.JSONDecodeError as e:
                self.logger.error(f"Ошибка формата JSON при загрузке прогресса ключей: {e}")
                # Создаем резервную копию поврежденного файла
                import shutil
                backup_file = f"{progress_file}.bak"
                try:
                    shutil.copy(progress_file, backup_file)
                    self.logger.info(f"Создана резервная копия поврежденного файла: {backup_file}")
                except Exception as backup_e:
                    self.logger.error(f"Не удалось создать резервную копию файла: {backup_e}")
            except Exception as e:
                self.logger.error(f"Ошибка при загрузке прогресса ключей: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
        else:
            self.logger.info(f"Файл прогресса ключей не найден: {progress_file}")
            # Инициализируем значения по умолчанию
            self.keys_target = 1000
            self.keys_current = 0
            # Сразу сохраняем значения по умолчанию в файл
            self.save_keys_progress()

        return False

    def save_keys_progress(self):
        """Сохраняет цель и прогресс сбора ключей в файл."""
        import os
        progress_file = os.path.join(self.stats_dir, "keys_progress.json")

        try:
            # Проверка значений перед сохранением
            if not hasattr(self, 'keys_target') or not isinstance(self.keys_target, int) or self.keys_target <= 0:
                self.logger.warning(
                    f"Некорректное значение keys_target ({getattr(self, 'keys_target', 'не задано')}), установлено 1000")
                self.keys_target = 1000

            if not hasattr(self, 'keys_current') or not isinstance(self.keys_current, int) or self.keys_current < 0:
                self.logger.warning(
                    f"Некорректное значение keys_current ({getattr(self, 'keys_current', 'не задано')}), установлено 0")
                self.keys_current = 0

            # Сохраняем текущие значения для логирования
            self.logger.info(f"Сохранение прогресса ключей: target={self.keys_target}, current={self.keys_current}")

            # Формируем данные для сохранения
            data = {
                "target": self.keys_target,
                "current": self.keys_current,
                "last_updated": datetime.datetime.now().isoformat()
            }

            # Создаем директорию, если она не существует
            if not os.path.exists(self.stats_dir):
                os.makedirs(self.stats_dir, exist_ok=True)
                self.logger.info(f"Создана директория для сохранения прогресса: {self.stats_dir}")

            # Сначала сохраняем во временный файл, затем переименовываем
            # Это предотвращает повреждение файла при сбое во время записи
            temp_file = f"{progress_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # Если временный файл успешно создан, переименовываем его
            import os
            if os.path.exists(progress_file):
                # Создаем резервную копию текущего файла
                backup_file = f"{progress_file}.bak"
                try:
                    import shutil
                    shutil.copy2(progress_file, backup_file)
                    self.logger.debug(f"Создана резервная копия файла прогресса: {backup_file}")
                except Exception as backup_e:
                    self.logger.warning(f"Не удалось создать резервную копию: {backup_e}")

            # Переименовываем временный файл в целевой
            import os
            os.replace(temp_file, progress_file)

            self.logger.info(f"Прогресс сбора ключей успешно сохранен: {self.keys_current}/{self.keys_target}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении прогресса ключей: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def reset_keys_progress(self):
        """Сбрасывает прогресс сбора ключей."""
        # Сбрасываем только текущий прогресс, оставляя цель неизменной
        self.keys_current = 0
        self.current_stats["keys_collected"] = 0

        # Сохраняем обновленные данные
        self.save_keys_progress()
        self.logger.info("Прогресс сбора ключей сброшен")

    def update_keys_target(self, target: int):
        """Обновляет цель по сбору ключей."""
        self.keys_target = target
        self.save_keys_progress()
        self.logger.info(f"Обновлена цель по сбору ключей: {target}")

    def add_to_keys_progress(self, keys_to_add=None):
        """
        Добавляет собранные в текущей сессии ключи к общему прогрессу.
        Если количество ключей не указано, берется из текущей статистики.

        Args:
            keys_to_add (int, optional): Количество ключей для добавления

        Returns:
            int: Обновленное общее количество ключей
        """
        if keys_to_add is None:
            keys_to_add = self.current_stats["keys_collected"]

        if keys_to_add > 0:
            # Добавляем ключи текущей сессии к общему прогрессу
            self.keys_current += keys_to_add

            # Сбрасываем счетчик ключей текущей сессии
            # Это опционально и может быть закомментировано,
            # если нужно сохранить статистику текущей сессии
            # self.current_stats["keys_collected"] = 0

            # Сохраняем обновленный прогресс
            self.save_keys_progress()

            self.logger.info(f"Добавлено {keys_to_add} ключей к общему прогрессу. "
                             f"Общий прогресс: {self.keys_current}/{self.keys_target}")

        return self.keys_current