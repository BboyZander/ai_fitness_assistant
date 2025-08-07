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
        if row and row[0].strip().lower().startswith("дата тренировки"):
            current_index = i
            break

    # Считаем упражнения от первой значимой строки
    for row in data[current_index + 3:]:
        if row[0].strip().lower().startswith("дата тренировки"):
            break
        elif not row[0]:
            break
        else:
            latest_workout[row[0]] = row[1:]

    return latest_workout


# ========================
# 📝 Форматированный вывод
# ========================
def format_workout_readable(workout: Dict) -> str:
    lines = ["💪 **Тренировка **", ""]

    for i, ex in enumerate(list(workout.keys())):
        
        name = ex.strip()
        exercise_reps_count = workout[ex][0].strip()

        last_best_weight = workout[ex][1].strip()
        last_best_reps = workout[ex][2].strip()
        last_best_rpe = workout[ex][3].strip()

        warmups = workout[ex][4].strip()
        burnout_count = workout[ex][5].strip()  # число добивочных подходов
        work_weight = workout[ex][6].strip()
        work_reps = workout[ex][7].strip()
        work_rpe = workout[ex][8].strip()
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
                lines.append(f"  └ Отдых-пауза: {n_sets}")
            except ValueError:
                pass

        lines.append("")  # Пустая строка между упражнениями

    return "\n".join(lines)


# ========================
# 🧪 Отладка через терминал
# ========================
if __name__ == "__main__":
    workout = get_latest_workout()
    formatted = format_workout_readable(workout)
    print(formatted)