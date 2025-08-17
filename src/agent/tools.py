from langchain_core.tools import tool
from src.sheets_workout import get_latest_workout, format_workout_readable
from src.sheets_weights import (
    get_current_month_weight_stats,
    format_weight_summary,
    plot_weight_trend,
)

@tool
def show_latest_workout() -> str:
    """Показать ближайшую  тренировку из вкладки 'тренировки'."""
    w = get_latest_workout()
    return format_workout_readable(w)

@tool
def weight_summary() -> str:
    """Краткий отчёт по вкладке 'вес' за текущий месяц: мин/макс, среднее за 7 дней, заполнен ли сегодня."""
    s = get_current_month_weight_stats()
    return format_weight_summary(s)

@tool
def weight_plot(period: str = "last") -> str:
    """
    Построить график веса.
    period:
      - 'last' : текущий месяц, каждая точка = 1 день (есть линия тренда и подписи)
      - 'all'  : весь период, каждая точка = среднее за неделю (есть линия тренда и подписи)
    Возвращает путь к PNG.
    """
    path = plot_weight_trend(period=period, save_path=f"weight_{period}.png")
    return f"График сохранён: {path}"