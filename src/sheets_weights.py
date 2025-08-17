# src/weights.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
# import os
from typing import Dict, List, Optional
from gspread.utils import rowcol_to_a1

# --- ДО ЛЮБОГО ИМПОРТА pyplot ---
try:
    import matplotlib
    matplotlib.use("Agg")  # безопасный безоконный бэкенд
    import matplotlib.pyplot as plt
except Exception:
    plt = None  # позволяем тулу отработать без графиков

# -------- Настройки доступа --------
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_NAME = "Абрамченко Александр. Дневник тренировок"
WEIGHT_WORKSHEET_NAME = "вес"


# -------- Подключение к листу "вес" --------
def connect_to_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).worksheet(WEIGHT_WORKSHEET_NAME)


# -------- Утилиты --------
def _to_float(s: str) -> Optional[float]:
    if s is None:
        return None
    s = s.strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _get_columns(ws) -> List[List[str]]:
    """Забираем данные КОЛОНКАМИ (важно!), ограничим до первых ~40 строк."""
    last_addr = rowcol_to_a1(40, ws.col_count)  # например, 'ZZ40'
    rng = f"A1:{last_addr}"
    return ws.get(rng, major_dimension="COLUMNS")


# -------- Основная логика --------
def get_current_month_weight_stats() -> Dict:
    """
    Возвращает словарь:
      - min/max           : минимум/максимум за текущий месяц
      - today_filled      : внесён ли вес за сегодня
      - avg_last_7        : среднее за последние 7 календарных дней (по имеющимся)
      - weights           : список весов по дням месяца (1..31), None если пусто
      - rolling7          : скользящее среднее 7 дней
      - filled_days       : сколько дней заполнено
      - missing_days      : сколько дней пустых (до сегодняшнего дня включительно)
    """
    ws = connect_to_sheet()
    cols = _get_columns(ws)
    today = date.today()


    month_col_idx = today.month - 1
    col = cols[month_col_idx*4 + 3]
    # значения за дни 1..31
    daily_vals = [_to_float(x) for x in col[0:32]]

    existing = [x for x in daily_vals if x is not None]
    w_min = min(existing) if existing else None
    w_max = max(existing) if existing else None

    today_filled = False
    if 1 <= today.day <= len(daily_vals):
        today_filled = daily_vals[today.day - 1] is not None

    # среднее за последние 7 календарных дней (по имеющимся значениям)
    last7_slice = daily_vals[max(0, today.day - 7): today.day]
    last7_vals = [x for x in last7_slice if x is not None]
    avg_last_7 = round(sum(last7_vals) / len(last7_vals), 2) if last7_vals else None

    # скользящее среднее 7 дней по всему месяцу
    rolling7: List[Optional[float]] = []
    for i in range(len(daily_vals)):
        window = [x for x in daily_vals[max(0, i - 6): i + 1] if x is not None]
        rolling7.append(round(sum(window) / len(window), 2) if window else None)

    filled_days = sum(1 for x in daily_vals[: today.day] if x is not None)
    missing_days = today.day - filled_days if today.day <= 31 else 0

    return {
        "min": w_min,
        "max": w_max,
        "today_filled": today_filled,
        "avg_last_7": avg_last_7,
        "weights": daily_vals,
        "rolling7": rolling7,
        "filled_days": filled_days,
        "missing_days": max(missing_days, 0),
    }


def format_weight_summary(stats: Dict) -> str:
    lines = ["⚖️ Вес — текущий месяц:"]
    lines.append(f"- Минимум: {stats['min']} кг" if stats["min"] is not None else "- Минимум: —")
    lines.append(f"- Максимум: {stats['max']} кг" if stats["max"] is not None else "- Максимум: —")
    lines.append(f"- Вес на сегодня внесён: {'да' if stats['today_filled'] else 'нет'}")
    lines.append(
        f"- Среднее за последние 7 дней: {stats['avg_last_7']} кг"
        if stats["avg_last_7"] is not None
        else "- Среднее за последние 7 дней: —"
    )
    lines.append(f"- Заполнено дней (до сегодня): {stats['filled_days']}")
    lines.append(f"- Пропусков (до сегодня): {stats['missing_days']}")
    return "\n".join(lines)


def plot_weight_trend(period: str = "last", save_path: str = "weight_plot.png") -> str | None:
    """
    Строит график веса.
    period:
      - "last" : текущий месяц, каждая точка = 1 день
      - "all"  : весь период, каждая точка = среднее значение за неделю
    """
    if plt is None:
        print("matplotlib не установлен: график не будет создан.")
        return None

    from numpy import polyfit, poly1d
    from statistics import mean

    ws = connect_to_sheet()
    cols = _get_columns(ws)
    today = date.today()

    # Режим: текущий месяц (каждый день)
    if period == "last":
        weight_col_idx = 3 + (today.month - 1) * 4
        if weight_col_idx >= len(cols):
            print(f"Недостаточно данных: нужен индекс {weight_col_idx}, всего {len(cols)} колонок.")
            return None

        weight_col = cols[weight_col_idx]
        daily_vals = [_to_float(x) for x in weight_col[:32]]
        days = list(range(1, len(daily_vals) + 1))

        x = [d for d, w in zip(days, daily_vals) if w is not None]
        y = [w for w in daily_vals if w is not None]
        xlabel = "День месяца"
        title = f"Вес по дням — {today.year}-{today.month:02d}"

    # Режим: весь период (недельные средние)
    elif period == "all":
        weight_cols = cols[3::4]
        weekly_means = []
        week_idx = []

        week_counter = 1
        for col in weight_cols:
            daily_vals = [_to_float(x) for x in col[1:32] if x.strip() != ""]
            for i in range(0, len(daily_vals), 7):
                week = [w for w in daily_vals[i:i+7] if w is not None]
                if week:
                    weekly_means.append(round(mean(week), 2))
                    week_idx.append(week_counter)
                week_counter += 1

        x = week_idx
        y = weekly_means
        xlabel = "Номер недели с начала отслеживания"
        title = "Вес (среднее за неделю) — весь период"

    else:
        raise ValueError("period должен быть 'last' или 'all'")

    if not x:
        print("Нет данных для построения графика.")
        return None

    # Построение графика
    plt.figure(figsize=(10, 5))
    plt.plot(x, y, marker="o", color="skyblue", alpha=0.7, label="Вес")

    # Подписи к точкам
    for xi, yi in zip(x, y):
        plt.text(xi - 0.24, yi + 0.03 , str(yi), ha="center", fontsize=8)

    # Линия тренда
    if len(x) >= 2:
        coeffs = polyfit(x, y, 1)
        trend_fn = poly1d(coeffs)
        plt.plot(
            x,
            trend_fn(x),
            color="red",
            alpha=0.5,
            linewidth=2,
            label="Тренд"
        )

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Вес, кг")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    return save_path


# -------- Отладка из консоли --------
if __name__ == "__main__":
    stats = get_current_month_weight_stats()
    print(format_weight_summary(stats))
    out = plot_weight_trend()
    if out:
        print(f"\nГрафик сохранён: {out}")