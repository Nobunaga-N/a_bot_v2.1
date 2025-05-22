import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional
from functools import wraps


def validate_stats_data(func):
    """Декоратор для валидации данных статистики."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"Ошибка в {func.__name__}: {e}")
            return {} if 'dict' in str(func.__annotations__.get('return', '')) else []

    return wrapper


class FileManager:
    """Менеджер для безопасной работы с файлами."""

    def __init__(self, logger):
        self.logger = logger

    def safe_save(self, file_path: str, data: dict) -> bool:
        """Безопасное сохранение данных в файл."""
        try:
            # Добавляем timestamp
            data["last_updated"] = datetime.datetime.now().isoformat()

            # Сохраняем через временный файл
            temp_file = f"{file_path}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # Создаем резервную копию если нужно
            if os.path.exists(file_path):
                backup_file = f"{file_path}.bak"
                try:
                    import shutil
                    shutil.copy2(file_path, backup_file)
                except Exception as e:
                    self.logger.warning(f"Не удалось создать резервную копию: {e}")

            # Заменяем оригинальный файл
            os.replace(temp_file, file_path)
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении {file_path}: {e}")
            return False

    def safe_load(self, file_path: str) -> dict:
        """Безопасная загрузка данных из файла."""
        if not os.path.exists(file_path):
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке {file_path}: {e}")
            return {}


class StatsAggregator:
    """Агрегатор для расчета статистики."""

    @staticmethod
    def calculate_derived_stats(stats: Dict[str, int]) -> Dict[str, float]:
        """Вычисляет производные показатели."""
        battles = stats.get("victories", 0) + stats.get("defeats", 0)
        victories = stats.get("victories", 0)

        result = {
            "battles": battles,
            "win_rate": (victories / battles * 100) if battles > 0 else 0,
            "keys_per_victory": (stats.get("keys_collected", 0) / victories) if victories > 0 else 0
        }

        return result

    @staticmethod
    def calculate_time_metrics(duration_hours: float, stats: Dict[str, int]) -> Dict[str, float]:
        """Вычисляет временные метрики."""
        if duration_hours <= 0:
            return {"battles_per_hour": 0, "keys_per_hour": 0}

        battles = stats.get("victories", 0) + stats.get("defeats", 0)
        return {
            "battles_per_hour": battles / duration_hours,
            "keys_per_hour": stats.get("keys_collected", 0) / duration_hours
        }

    @staticmethod
    def merge_stats(*stats_dicts) -> Dict[str, int]:
        """Объединяет несколько словарей статистики."""
        result = {
            "battles_started": 0, "victories": 0, "defeats": 0,
            "connection_losses": 0, "errors": 0, "keys_collected": 0,
            "silver_collected": 0
        }

        for stats in stats_dicts:
            if not stats:
                continue
            for key, value in stats.items():
                if key in result and isinstance(value, (int, float)):
                    result[key] += value

        return result


class StatsManager:
    """Управляет статистикой бота с централизованной логикой."""

    # Шаблон статистики по умолчанию
    DEFAULT_STATS = {
        "battles_started": 0, "victories": 0, "defeats": 0,
        "connection_losses": 0, "errors": 0, "keys_collected": 0,
        "silver_collected": 0
    }

    def __init__(self, stats_dir: str):
        """Инициализация менеджера статистики."""
        self.logger = logging.getLogger("BotLogger")
        self.stats_dir = stats_dir

        # Создаем каталог если нужно
        os.makedirs(self.stats_dir, exist_ok=True)

        # Пути к файлам
        self.stats_file = os.path.join(self.stats_dir, "bot_stats.json")
        self.keys_progress_file = os.path.join(self.stats_dir, "keys_progress.json")

        # Инициализируем компоненты
        self.file_manager = FileManager(self.logger)
        self.aggregator = StatsAggregator()

        # Данные
        self.history = []
        self.keys_target = 1000
        self.keys_current = 0

        # Загружаем данные
        self._load_all_data()

        self.logger.info(f"StatsManager инициализирован. История: {len(self.history)} записей. "
                         f"Ключи: {self.keys_current}/{self.keys_target}")

    def _load_all_data(self):
        """Загружает все данные из файлов."""
        # Загружаем основную статистику
        stats_data = self.file_manager.safe_load(self.stats_file)
        self.history = stats_data.get("history", [])

        # Загружаем прогресс ключей
        keys_data = self.file_manager.safe_load(self.keys_progress_file)
        self.keys_target = keys_data.get("target", 1000)
        self.keys_current = keys_data.get("current", 0)

        # Валидация данных
        self._validate_keys_data()

    def _validate_keys_data(self):
        """Валидирует и исправляет данные ключей."""
        if not isinstance(self.keys_target, int) or self.keys_target <= 0:
            self.logger.warning(f"Некорректная цель ключей ({self.keys_target}), установлено 1000")
            self.keys_target = 1000

        if not isinstance(self.keys_current, int) or self.keys_current < 0:
            self.logger.warning(f"Некорректный прогресс ключей ({self.keys_current}), установлено 0")
            self.keys_current = 0

    # Методы загрузки/сохранения
    def load_stats(self) -> bool:
        """Загружает статистику из файла."""
        stats_data = self.file_manager.safe_load(self.stats_file)
        if stats_data:
            self.history = stats_data.get("history", [])
            self.logger.info(f"Загружено {len(self.history)} записей истории")
            return True
        return False

    def save_stats(self) -> bool:
        """Сохраняет статистику в файл."""
        data = {
            "total": self.get_total_stats(),
            "history": self.history
        }
        return self.file_manager.safe_save(self.stats_file, data)

    def load_keys_progress(self) -> bool:
        """Загружает прогресс ключей."""
        keys_data = self.file_manager.safe_load(self.keys_progress_file)
        if keys_data:
            old_target, old_current = self.keys_target, self.keys_current
            self.keys_target = keys_data.get("target", 1000)
            self.keys_current = keys_data.get("current", 0)
            self._validate_keys_data()

            self.logger.info(f"Загружен прогресс: {self.keys_current}/{self.keys_target} "
                             f"(было: {old_current}/{old_target})")
            return True
        return False

    def save_keys_progress(self) -> bool:
        """Сохраняет прогресс ключей."""
        self._validate_keys_data()
        data = {
            "target": self.keys_target,
            "current": self.keys_current
        }
        success = self.file_manager.safe_save(self.keys_progress_file, data)
        if success:
            self.logger.info(f"Прогресс ключей сохранен: {self.keys_current}/{self.keys_target}")
        return success

    # Основные методы работы со статистикой
    def register_session(self, session_stats: Dict[str, int], start_time: float,
                         end_time: float, duration_seconds: float) -> bool:
        """Регистрирует сессию в истории."""
        if not session_stats:
            self.logger.warning("Попытка зарегистрировать пустую сессию")
            return False

        try:
            # Создаем запись сессии
            session_record = {
                "start_time": datetime.datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.datetime.fromtimestamp(end_time).isoformat(),
                "duration_seconds": duration_seconds,
                "stats": session_stats.copy()
            }

            self.history.append(session_record)

            # Обновляем прогресс ключей
            keys_collected = session_stats.get("keys_collected", 0)
            if keys_collected > 0:
                self.keys_current += keys_collected
                self.save_keys_progress()

            # Сохраняем статистику
            success = self.save_stats()
            if success:
                self.logger.info(f"Сессия зарегистрирована. Прогресс: {self.keys_current}/{self.keys_target}")

            return success

        except Exception as e:
            self.logger.error(f"Ошибка при регистрации сессии: {e}")
            return False

    @validate_stats_data
    def get_total_stats(self) -> Dict[str, int]:
        """Получает общую статистику из истории."""
        if not self.history:
            return self.DEFAULT_STATS.copy()

        # Берем структуру из последней записи или используем дефолтную
        template = self.history[-1].get("stats", self.DEFAULT_STATS)
        total = {key: 0 for key in template}

        # Суммируем все записи
        for record in self.history:
            stats = record.get("stats", {})
            for key, value in stats.items():
                if key in total and isinstance(value, (int, float)):
                    total[key] += value

        return total

    def get_stats_by_period(self, period: str, current_session_stats: Optional[Dict[str, int]] = None) -> Dict[
        str, Any]:
        """Универсальный метод получения статистики за период."""
        # Определяем дату отсечения
        now = datetime.datetime.now()
        cutoff_dates = {
            "day": now.replace(hour=0, minute=0, second=0, microsecond=0),
            "week": now - datetime.timedelta(weeks=1),
            "month": now - datetime.timedelta(days=30),
            "all": datetime.datetime.min
        }
        cutoff = cutoff_dates.get(period, datetime.datetime.min)

        # Фильтруем записи
        filtered_records = []
        for record in self.history:
            try:
                end_time = datetime.datetime.fromisoformat(record["end_time"])
                if end_time >= cutoff:
                    filtered_records.append(record)
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Ошибка обработки записи: {e}")

        # Агрегируем статистику
        stats = self.DEFAULT_STATS.copy()
        total_duration_hours = 0

        for record in filtered_records:
            # Суммируем длительность
            total_duration_hours += record.get("duration_seconds", 0) / 3600

            # Суммируем статистику
            record_stats = record.get("stats", {})
            for key, value in record_stats.items():
                if key in stats and isinstance(value, (int, float)):
                    stats[key] += value

        # Добавляем текущую сессию если нужно
        if current_session_stats:
            stats = self.aggregator.merge_stats(stats, current_session_stats)

        # Формируем результат
        result = {
            "period": period,
            "record_count": len(filtered_records),
            "total_duration_hours": total_duration_hours,
            "stats": stats
        }

        # Добавляем производные показатели
        derived = self.aggregator.calculate_derived_stats(stats)
        result.update(derived)

        # Добавляем временные метрики
        if total_duration_hours > 0:
            time_metrics = self.aggregator.calculate_time_metrics(total_duration_hours, stats)
            result.update(time_metrics)
        else:
            result.update({"battles_per_hour": 0, "keys_per_hour": 0})

        return result

    # Методы совместимости (делегируют к основному методу)
    def get_stats_by_period_with_current_session(self, period: str,
                                                 current_session_stats: Optional[Dict[str, int]]) -> Dict[str, Any]:
        """Совместимость: получение статистики с текущей сессией."""
        return self.get_stats_by_period(period, current_session_stats)

    @validate_stats_data
    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Получает статистику по дням."""
        daily_stats = []
        current_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Инициализируем пустые дни
        for i in range(days):
            date = current_date - datetime.timedelta(days=i)
            day_data = {
                "date": date.strftime("%Y-%m-%d"),
                "display_date": date.strftime("%d.%m"),
                "stats": self.DEFAULT_STATS.copy()
            }
            daily_stats.append(day_data)

        # Заполняем данными из истории
        for record in self.history:
            try:
                end_time = datetime.datetime.fromisoformat(record["end_time"])
                end_date = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
                days_difference = (current_date - end_date).days

                if 0 <= days_difference < days:
                    record_stats = record.get("stats", {})
                    for key, value in record_stats.items():
                        if key in daily_stats[days_difference]["stats"]:
                            daily_stats[days_difference]["stats"][key] += value

            except (KeyError, ValueError) as e:
                self.logger.warning(f"Ошибка обработки записи для дней: {e}")

        # Добавляем производные показатели
        for day in daily_stats:
            derived = self.aggregator.calculate_derived_stats(day["stats"])
            day.update(derived)

        # Возвращаем в хронологическом порядке
        daily_stats.reverse()
        return daily_stats

    def get_daily_stats_with_current_session(self, days: int = 7,
                                             current_session_stats: Optional[Dict[str, int]] = None) -> List[
        Dict[str, Any]]:
        """Получает ежедневную статистику с учетом текущей сессии."""
        daily_stats = self.get_daily_stats(days)

        if not current_session_stats:
            return daily_stats

        # Добавляем текущую сессию к сегодняшнему дню
        today = datetime.datetime.now().strftime("%d.%m")

        for day in daily_stats:
            if day["display_date"] == today:
                # Обновляем статистику сегодняшнего дня
                day["stats"] = self.aggregator.merge_stats(day["stats"], current_session_stats)

                # Пересчитываем производные показатели
                derived = self.aggregator.calculate_derived_stats(day["stats"])
                day.update(derived)
                break
        else:
            # Если сегодня нет в данных, добавляем новый день
            today_stats = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "display_date": today,
                "stats": current_session_stats.copy()
            }
            derived = self.aggregator.calculate_derived_stats(today_stats["stats"])
            today_stats.update(derived)
            daily_stats.append(today_stats)

        return daily_stats

    def get_trend_data(self) -> Dict[str, List]:
        """Получает данные для графиков трендов."""
        daily_data = self.get_daily_stats(7)

        trend_data = {
            "dates": [], "victories": [], "defeats": [], "win_rates": [],
            "keys_collected": [], "keys_per_victory": [], "silver_collected": []
        }

        for day in daily_data:
            trend_data["dates"].append(day["display_date"])
            trend_data["victories"].append(day["stats"]["victories"])
            trend_data["defeats"].append(day["stats"]["defeats"])
            trend_data["win_rates"].append(round(day.get("win_rate", 0), 1))
            trend_data["keys_collected"].append(day["stats"]["keys_collected"])
            trend_data["keys_per_victory"].append(round(day.get("keys_per_victory", 0), 1))
            trend_data["silver_collected"].append(day["stats"].get("silver_collected", 0))

        return trend_data

    def get_trend_data_with_current_session(self, current_session_stats: Optional[Dict[str, int]]) -> Dict[str, List]:
        """Получает данные трендов с учетом текущей сессии."""
        trend_data = self.get_trend_data()

        if not current_session_stats:
            return trend_data

        # Обновляем данные для сегодняшнего дня
        today = datetime.datetime.now().strftime("%d.%m")

        if trend_data["dates"] and trend_data["dates"][-1] == today:
            # Обновляем последний день
            index = len(trend_data["dates"]) - 1
            trend_data["victories"][index] += current_session_stats.get("victories", 0)
            trend_data["defeats"][index] += current_session_stats.get("defeats", 0)
            trend_data["keys_collected"][index] += current_session_stats.get("keys_collected", 0)
            trend_data["silver_collected"][index] += current_session_stats.get("silver_collected", 0)

            # Пересчитываем производные показатели
            victories = trend_data["victories"][index]
            defeats = trend_data["defeats"][index]
            battles = victories + defeats

            if battles > 0:
                trend_data["win_rates"][index] = round((victories / battles) * 100, 1)
                trend_data["keys_per_victory"][index] = round(trend_data["keys_collected"][index] / victories,
                                                              1) if victories > 0 else 0
        else:
            # Добавляем новый день
            for key in trend_data:
                if key == "dates":
                    trend_data[key].append(today)
                elif key in current_session_stats:
                    trend_data[key].append(current_session_stats[key])
                else:
                    # Рассчитываем производные показатели
                    victories = current_session_stats.get("victories", 0)
                    defeats = current_session_stats.get("defeats", 0)
                    battles = victories + defeats

                    if key == "win_rates":
                        trend_data[key].append(round((victories / battles) * 100, 1) if battles > 0 else 0)
                    elif key == "keys_per_victory":
                        trend_data[key].append(round(current_session_stats.get("keys_collected", 0) / victories,
                                                     1) if victories > 0 else 0)
                    else:
                        trend_data[key].append(0)

        return trend_data

    # Методы работы с ключами
    def update_keys_target(self, target: int) -> bool:
        """Обновляет целевое значение ключей."""
        if not isinstance(target, int) or target <= 0:
            self.logger.warning(f"Некорректная цель ключей: {target}")
            return False

        old_target = self.keys_target
        self.keys_target = target
        success = self.save_keys_progress()

        if success:
            self.logger.info(f"Цель ключей обновлена: {old_target} -> {self.keys_target}")

        return success

    def add_keys_to_progress(self, keys_count: int) -> int:
        """Добавляет ключи к общему прогрессу."""
        if keys_count <= 0:
            return self.keys_current

        self.keys_current += keys_count
        self.save_keys_progress()

        self.logger.info(f"Добавлено {keys_count} ключей. Текущий прогресс: {self.keys_current}")
        return self.keys_current

    def reset_keys_progress(self) -> bool:
        """Сбрасывает прогресс ключей."""
        old_progress = self.keys_current
        self.keys_current = 0
        success = self.save_keys_progress()

        if success:
            self.logger.info(f"Прогресс ключей сброшен: {old_progress} -> 0")

        return success

    def get_keys_progress(self) -> Dict[str, int]:
        """Возвращает информацию о прогрессе ключей."""
        return {
            "target": self.keys_target,
            "current": self.keys_current,
            "remaining": max(0, self.keys_target - self.keys_current),
            "percent": min(100, int((self.keys_current / self.keys_target) * 100)) if self.keys_target > 0 else 0
        }