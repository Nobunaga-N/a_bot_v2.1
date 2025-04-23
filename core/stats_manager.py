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
            "keys_collected": 0
        }

        # Historical stats with timestamps
        self.history = []

        # Session start time
        self.session_start = datetime.datetime.now()

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
                        record["stats"] = self.current_stats.copy()
                        is_new_session = False
                        break

                if is_new_session and any(val > 0 for val in self.current_stats.values()):
                    session_record = {
                        "start_time": self.session_start.isoformat(),
                        "end_time": session_end.isoformat(),
                        "duration_seconds": (session_end - self.session_start).total_seconds(),
                        "stats": self.current_stats.copy()
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

        # Define cutoff date based on period
        if period == "day":
            cutoff = now - datetime.timedelta(days=1)
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

        # Add current session if applicable
        current_duration = (now - self.session_start).total_seconds() / 3600
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
        now = datetime.datetime.now()

        # Initialize empty data for each day
        for i in range(days):
            date = now - datetime.timedelta(days=i)
            day_data = {
                "date": date.strftime("%Y-%m-%d"),
                "display_date": date.strftime("%d.%m"),
                "stats": {key: 0 for key in self.current_stats}
            }
            daily_stats.append(day_data)

        # Process history records
        for record in self.history:
            try:
                end_time = datetime.datetime.fromisoformat(record["end_time"])
                days_ago = (now - end_time).days

                if 0 <= days_ago < days:
                    day_index = days_ago

                    # Add stats to the appropriate day
                    for key, value in record["stats"].items():
                        if key in daily_stats[day_index]["stats"]:
                            daily_stats[day_index]["stats"][key] += value
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Ошибка обработки записи истории для разбивки по дням: {e}")

        # Add current session stats to today (index 0)
        if len(daily_stats) > 0:
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
            "keys_per_victory": []
        }

        for day in daily_data:
            trend_data["dates"].append(day["display_date"])
            trend_data["victories"].append(day["stats"]["victories"])
            trend_data["defeats"].append(day["stats"]["defeats"])
            trend_data["win_rates"].append(round(day.get("win_rate", 0), 1))
            trend_data["keys_collected"].append(day["stats"]["keys_collected"])
            trend_data["keys_per_victory"].append(round(day.get("keys_per_victory", 0), 1))

        return trend_data