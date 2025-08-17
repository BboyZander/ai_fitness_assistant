import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from .tools import show_latest_workout, weight_summary, weight_plot
from .memory import memory

load_dotenv()

# Системный промт передаётся при вызове (см. run_agent.py), здесь держим чистую модель
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
)

# Регистрируем инструменты
tools = [show_latest_workout, weight_summary, weight_plot]

# Создаём ReAct-агента с чекпоинтером-памятью
agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
)