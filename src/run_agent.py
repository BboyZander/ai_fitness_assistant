from pathlib import Path
from src.agent.graph import agent

BASE_DIR = Path(__file__).resolve().parent.parent  # /src
PROMPT_PATHS = [
    BASE_DIR / "src" / "prompts" / "system.txt",  # путь внутри src
    BASE_DIR / "prompts" / "system.txt"           # путь в корне проекта
]

SYSTEM_PROMPT = None
for path in PROMPT_PATHS:
    if path.exists():
        SYSTEM_PROMPT = path.read_text(encoding="utf-8")
        break

if SYSTEM_PROMPT is None:
    raise FileNotFoundError(
        "Не найден файл системного промпта. Ожидались пути:\n - "
        + "\n - ".join(str(p) for p in PROMPT_PATHS)
    )

def main():
    print("AI–ассистент запущен. Напиши запрос (exit/выход для выхода).")
    thread = "local-cli"

    while True:
        q = input("\nВы: ").strip()
        if q.lower() in {"exit", "quit", "выход"}:
            break

        result = agent.invoke(
            {"messages": [("system", SYSTEM_PROMPT), ("user", q)]},
            config={
                "configurable": {"thread_id": thread, "user_id": "local_user"}
            },
        )

        msgs = result.get("messages", [])
        print("AI:", msgs[-1].content if msgs else "(пустой ответ)")

if __name__ == "__main__":
    main()