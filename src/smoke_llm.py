import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(model="gpt-5", temperature=0)  # можно gpt-4o-mini для скорости

resp = llm.invoke("Скажи 'проверка связи' одним словом.")
print(resp.content)