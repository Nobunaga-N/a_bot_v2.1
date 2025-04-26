import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional


class StatsManager:
    """
    Manages statistics for the bot, including persistence between sessions.

    Ответственность:
    - Хранение и управление историческими данными
    - Управление общим прогрессом ключей
    - Агрегирование статистики по разным периодам
    - Сохранение/загрузка данных из файлов
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

        # Path to the keys progress file
        self.keys_progress_file = os.path.join(self.stats_dir, "keys_progress.json")

        # Общий прогресс по ключам (сохраняется между сессиями)
        self.keys_target = 1000  # Целевое значение
        self.keys_current = 0  # Текущее значение

        # Historical stats with timestamps
        self.history = []

        # Загружаем данные из файлов
        self.load_keys_progress()
        self.load_stats()

        # Log initialization
        self.logger.info(f"StatsManager инициализирован. Загружено {len(self.history)} исторических записей.")
        self.logger.info(f"Текущий прогресс ключей: {self.keys_current}/{self.keys_target}")

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

            self.logger.info(f"Статистика успешно загружена. Количество исторических записей: {len(self.history)}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке статистики: {e}")
            return False

    def load_keys_progress(self) -> bool:
        """
        Загружает цель и прогресс сбора ключей из файла.

        Returns:
            True if progress was successfully loaded, False otherwise
        """
        if not os.path.exists(self.keys_progress_file):
            self.logger.info("Файл прогресса ключей не найден. Будет создан новый файл.")
            return False

        try:
            with open(self.keys_progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            old_target = self.keys_target
            old_current = self.keys_current

            self.keys_target = data.get("target", 1000)
            self.keys_current = data.get("current", 0)

            self.logger.info(f"Загружен прогресс сбора ключей: {self.keys_current}/{self.keys_target} " +
                             f"(было: {old_current}/{old_target})")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке прогресса ключей: {e}")
            return False

    def save_keys_progress(self) -> bool:
        """
        Сохраняет цель и прогресс сбора ключей в файл.

        Returns:
            True if progress was successfully saved, False otherwise
        """
        try:
            # Проверка значений перед сохранением
            if not isinstance(self.keys_target, int) or self.keys_target <= 0:
                self.logger.warning(f"Некорректное значение keys_target ({self.keys_target}), установлено 1000")
                self.keys_target = 1000

            if not isinstance(self.keys_current, int) or self.keys_current < 0:
                self.logger.warning(f"Некорректное значение keys_current ({self.keys_current}), установлено 0")
                self.keys_current = 0

            # Формируем данные для сохранения
            data = {
                "target": self.keys_target,
                "current": self.keys_current,
                "last_updated": datetime.datetime.now().isoformat()
            }

            # Сохраняем через временный файл для безопасности
            temp_file = f"{self.keys_progress_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # Если временный файл успешно создан, переименовываем его
            import os
            if os.path.exists(self.keys_progress_file):
                # Создаем резервную копию текущего файла
                backup_file = f"{self.keys_progress_file}.bak"
                try:
                    import shutil
                    shutil.copy2(self.keys_progress_file, backup_file)
                except Exception as backup_e:
                    self.logger.warning(f"Не удалось создать резервную копию: {backup_e}")

            # Переименовываем временный файл в целевой
            os.replace(temp_file, self.keys_progress_file)

            self.logger.info(f"Прогресс сбора ключей успешно сохранен: {self.keys_current}/{self.keys_target}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении прогресса ключей: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def save_stats(self) -> bool:
        """
        Save statistics to file.

        Returns:
            True if statistics were successfully saved, False otherwise
        """
        try:
            # Calculate total stats from history
            total_stats = self.get_total_stats()

            # Prepare data for saving
            data = {
                "total": total_stats,
                "history": self.history,
                "last_updated": datetime.datetime.now().isoformat()
            }

            # Save to file safely using a temporary file
            temp_file = f"{self.stats_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # Create a backup of the current file if it exists
            if os.path.exists(self.stats_file):
                backup_file = f"{self.stats_file}.bak"
                try:
                    import shutil
                    shutil.copy2(self.stats_file, backup_file)
                except Exception as backup_e:
                    self.logger.warning(f"Не удалось создать резервную копию статистики: {backup_e}")

            # Replace the original file with the temporary file
            os.replace(temp_file, self.stats_file)

            self.logger.info("Статистика успешно сохранена.")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении статистики: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def register_session(self, session_stats: Dict[str, int], start_time: float, end_time: float,
                         duration_seconds: float) -> bool:
        """
        Регистрирует сессию бота в истории и обновляет общий прогресс ключей.

        Args:
            session_stats: Статистика сессии
            start_time: Время начала сессии (timestamp)
            end_time: Время окончания сессии (timestamp)
            duration_seconds: Длительность сессии в секундах

        Returns:
            True if session was successfully registered, False otherwise
        """
        try:
            # Проверяем наличие статистики
            if not session_stats:
                self.logger.warning("Попытка зарегистрировать пустую сессию")
                return False

            # Преобразуем timestamp в datetime
            start_datetime = datetime.datetime.fromtimestamp(start_time) if start_time else datetime.datetime.now()
            end_datetime = datetime.datetime.fromtimestamp(end_time) if end_time else datetime.datetime.now()

            # Создаем запись о сессии
            session_record = {
                "start_time": start_datetime.isoformat(),
                "end_time": end_datetime.isoformat(),
                "duration_seconds": duration_seconds,
                "stats": session_stats.copy()  # Копируем, чтобы избежать проблем с изменением оригинала
            }

            # Добавляем в историю
            self.history.append(session_record)

            # Добавляем ключи к общему прогрессу
            keys_collected = session_stats.get("keys_collected", 0)
            if keys_collected > 0:
                self.logger.info(f"Добавляем {keys_collected} ключей к общему прогрессу ({self.keys_current})")
                self.keys_current += keys_collected
                self.logger.info(f"Новое значение общего прогресса: {self.keys_current}")

                # Сохраняем прогресс ключей
                self.save_keys_progress()

            # Сохраняем обновленную статистику
            self.save_stats()

            self.logger.info(
                f"Сессия успешно зарегистрирована. Общий прогресс ключей: {self.keys_current}/{self.keys_target}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при регистрации сессии: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def update_keys_target(self, target: int) -> bool:
        """
        Обновляет целевое значение прогресса ключей.

        Args:
            target: Новое целевое значение

        Returns:
            True if target was successfully updated, False otherwise
        """
        try:
            # Проверяем корректность значения
            if not isinstance(target, int) or target <= 0:
                self.logger.warning(f"Некорректное значение цели: {target}")
                return False

            # Сохраняем старое значение для логирования
            old_target = self.keys_target

            # Обновляем цель
            self.keys_target = target

            # Сохраняем изменения
            self.save_keys_progress()

            self.logger.info(f"Цель по ключам обновлена: {old_target} -> {self.keys_target}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении цели по ключам: {e}")
            return False

    def add_keys_to_progress(self, keys_count: int) -> int:
        """
        Добавляет указанное количество ключей к общему прогрессу.

        Args:
            keys_count: Количество ключей для добавления

        Returns:
            Обновленное значение прогресса ключей
        """
        try:
            if keys_count <= 0:
                return self.keys_current

            # Обновляем прогресс
            self.keys_current += keys_count

            # Сохраняем изменения
            self.save_keys_progress()

            self.logger.info(f"Добавлено {keys_count} ключей к общему прогрессу. Текущее значение: {self.keys_current}")
            return self.keys_current
        except Exception as e:
            self.logger.error(f"Ошибка при добавлении ключей к прогрессу: {e}")
            return self.keys_current

    def reset_keys_progress(self) -> bool:
        """
        Сбрасывает прогресс сбора ключей.

        Returns:
            True if progress was successfully reset, False otherwise
        """
        try:
            # Сохраняем старое значение для логирования
            old_progress = self.keys_current

            # Сбрасываем прогресс
            self.keys_current = 0

            # Сохраняем изменения
            self.save_keys_progress()

            self.logger.info(f"Прогресс ключей сброшен: {old_progress} -> 0")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сбросе прогресса ключей: {e}")
            return False

    def get_total_stats(self) -> Dict[str, int]:
        """
        Calculate total statistics from all historical records.

        Returns:
            Dictionary with total statistics
        """
        # Определяем структуру статистики на основе последней записи
        if self.history:
            last_record = self.history[-1]
            if "stats" in last_record:
                total = {key: 0 for key in last_record["stats"]}
            else:
                total = {
                    "battles_started": 0,
                    "victories": 0,
                    "defeats": 0,
                    "connection_losses": 0,
                    "errors": 0,
                    "keys_collected": 0,
                    "silver_collected": 0
                }
        else:
            total = {
                "battles_started": 0,
                "victories": 0,
                "defeats": 0,
                "connection_losses": 0,
                "errors": 0,
                "keys_collected": 0,
                "silver_collected": 0
            }

        # Add up all historical stats
        for record in self.history:
            if "stats" in record:
                for key, value in record["stats"].items():
                    if key in total:
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

        # Логируем выбранный период и дату отсечения
        self.logger.debug(f"Агрегация статистики для периода: {period}, дата отсечения: {cutoff}")

        # Filter history records by period
        filtered_records = []
        for record in self.history:
            try:
                end_time = datetime.datetime.fromisoformat(record["end_time"])
                if end_time >= cutoff:
                    filtered_records.append(record)
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Ошибка обработки записи истории: {e}")

        # Логируем количество отфильтрованных записей
        self.logger.debug(f"Отфильтровано записей для периода {period}: {len(filtered_records)}")

        # Aggregate stats
        aggregated = {
            "period": period,
            "record_count": len(filtered_records),
            "total_duration_hours": 0,
            "stats": {}
        }

        # Обязательно инициализируем все поля статистики, включая серебро
        aggregated["stats"] = {
            "battles_started": 0,
            "victories": 0,
            "defeats": 0,
            "connection_losses": 0,
            "errors": 0,
            "keys_collected": 0,
            "silver_collected": 0  # Всегда инициализируем поле серебра
        }

        # Add up stats from filtered records
        for record in filtered_records:
            if "duration_seconds" in record:
                aggregated["total_duration_hours"] += record["duration_seconds"] / 3600

            if "stats" in record:
                # Проверяем наличие поля silver_collected в каждой записи
                if "silver_collected" not in record["stats"]:
                    self.logger.warning(
                        f"Поле silver_collected отсутствует в записи от {record.get('end_time', 'неизвестная дата')}")
                    # Добавляем поле серебра со значением 0, если его нет
                    record["stats"]["silver_collected"] = 0

                # Суммируем все статистические данные
                for key, value in record["stats"].items():
                    if key in aggregated["stats"]:
                        # Проверка типа данных для предотвращения ошибок
                        if isinstance(value, (int, float)) and isinstance(aggregated["stats"][key], (int, float)):
                            aggregated["stats"][key] += value
                        else:
                            # Логируем проблему с типами данных
                            self.logger.warning(
                                f"Несовместимые типы данных для ключа {key}: {type(value)} и {type(aggregated['stats'][key])}")
                            # Устанавливаем безопасное значение по умолчанию
                            if key == "silver_collected":
                                aggregated["stats"][key] = 0
                    else:
                        # Если ключ отсутствует в агрегированных данных, добавляем его
                        aggregated["stats"][key] = value

        # Проверяем наличие и тип поля серебра после агрегации
        if "silver_collected" not in aggregated["stats"]:
            self.logger.warning(f"После агрегации поле silver_collected отсутствует, добавляем со значением 0")
            aggregated["stats"]["silver_collected"] = 0
        elif not isinstance(aggregated["stats"]["silver_collected"], (int, float)):
            self.logger.warning(
                f"Некорректный тип данных silver_collected: {type(aggregated['stats']['silver_collected'])}")
            aggregated["stats"]["silver_collected"] = 0

        # Логируем агрегированные данные для отладки, особенно серебро
        self.logger.debug(f"Агрегация для периода {period}: {len(filtered_records)} записей")
        self.logger.debug(f"Агрегированная статистика: {aggregated['stats']}")
        self.logger.debug(f"Серебро за период {period}: {aggregated['stats']['silver_collected']}")

        # Calculate derived statistics
        stats = aggregated["stats"]
        battles = stats.get("victories", 0) + stats.get("defeats", 0)

        if battles > 0:
            aggregated["win_rate"] = (stats.get("victories", 0) / battles) * 100
        else:
            aggregated["win_rate"] = 0

        if stats.get("victories", 0) > 0:
            aggregated["keys_per_victory"] = stats.get("keys_collected", 0) / stats.get("victories", 0)
        else:
            aggregated["keys_per_victory"] = 0

        if aggregated["total_duration_hours"] > 0:
            aggregated["battles_per_hour"] = battles / aggregated["total_duration_hours"]
            aggregated["keys_per_hour"] = stats.get("keys_collected", 0) / aggregated["total_duration_hours"]
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
                "stats": {
                    "battles_started": 0,
                    "victories": 0,
                    "defeats": 0,
                    "connection_losses": 0,
                    "errors": 0,
                    "keys_collected": 0,
                    "silver_collected": 0
                }
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
            "silver_collected": []
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

        return trend_data

    def get_keys_progress(self) -> Dict[str, int]:
        """
        Возвращает информацию о прогрессе сбора ключей.

        Returns:
            Dictionary with keys progress information
        """
        return {
            "target": self.keys_target,
            "current": self.keys_current,
            "remaining": max(0, self.keys_target - self.keys_current),
            "percent": min(100, int((self.keys_current / self.keys_target) * 100)) if self.keys_target > 0 else 0
        }