import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict
from pprint import pprint

# ========================
# 🔐 Настройки доступа
# ========================
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_NAME = "Абрамченко Александр. Дневник тренировок"  # название Google Таблицы
WORKSHEET_NAME = "тренировки"    # название листа (вкладки)

# ========================
# 📡 Подключение
# ========================
def connect_to_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    return sheet


# ========================
# 📥 Получение последней тренировки (самая верхняя)
# ========================
def get_latest_workout() -> Dict:
    sheet = connect_to_sheet()
    data = sheet.get_all_values()

    latest_workout = {}
    current_index = 0

    # Найдём первую строку, начинающуюся с "Дата тренировки"
    for i, row in enumerate(data):
        if row and row[0].strip().lower().startswith(" Дата тренировки"):
            current_index = i
            break

    # Считаем упражнения от первой значимой строки
    exercises = []
    for row in data[current_index + 2:]:
        # Стоп — если встретили блок "самочувствие" или пустую строку
        if not any(cell.strip() for cell in row):
            break
        if row[0].strip().lower().startswith("самочувствие"):
            break
        exercises.append(row)

    latest_workout["exercises"] = exercises

    # Поиск комментария
    for row in exercises:
        if len(row) >= 39 and row[38].strip():
            latest_workout["comment"] = row[38]
            break
    else:
        latest_workout["comment"] = ""

    return latest_workout


# ========================
# 📝 Форматированный вывод
# ========================
def format_workout_readable(workout: Dict) -> str:
    lines = ["💪 **Тренировка (без даты)**", ""]

    for i, row in enumerate(workout["exercises"]):
        if not row or len(row) < 10:
            continue

        name = row[0].strip()
        last_best_weight = row[1].strip()
        last_best_reps = row[2].strip()
        last_best_rpe = row[3].strip()
        warmups = row[4].strip()
        burnout_notes = row[5].strip()  # пояснение (опционально)
        burnout_count = row[6].strip()  # число добивочных подходов
        work_weight = row[7].strip()
        work_reps = row[8].strip()
        work_rpe = row[9].strip() or "8"

        lines.append(f"**{i+1}. {name}**")

        if last_best_weight:
            lines.append(f"  └ Пред. лучший сет: {last_best_weight} кг × {last_best_reps} повт., RPE {last_best_rpe}")

        if warmups:
            warmup_sets = [w.strip().replace("*", "×") for w in warmups.split(";")]
            lines.append(f"  └ Разминка: {', '.join(warmup_sets)}")

        if work_weight:
            lines.append(f"  └ Рабочий вес: {work_weight} кг")

        if work_reps:
            lines.append(f"  └ Повторы: {work_reps}")

        if burnout_count:
            try:
                n_sets = int(burnout_count)
                note = f"{burnout_notes}" if burnout_notes else "по 5 повторений"
                lines.append(f"  └ Добивочных подходов: {n_sets} × {note}")
            except ValueError:
                pass

        lines.append("")  # Пустая строка между упражнениями

    if workout.get("comment"):
        lines.append(f"📝 Комментарий: {workout['comment']}")

    return "\n".join(lines)


# ========================
# 🧪 Отладка через терминал
# ========================
if __name__ == "__main__":
    workout = get_latest_workout()
    formatted = format_workout_readable(workout)
    print(formatted)