from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(model="gpt-5", temperature=0)  

resp = llm.invoke("Скажи 'проверка связи' одним словом.")
print(resp.content)