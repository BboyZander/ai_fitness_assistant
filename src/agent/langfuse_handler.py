from langchain_core.callbacks import BaseCallbackHandler
from langfuse import Langfuse
import os

class LangfuseHandler(BaseCallbackHandler):
    def __init__(self):
        self.lf = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        self._gen = None  # дескриптор текущего LLM-вызова

    def on_llm_start(self, serialized, prompts, **kwargs):
        model = (serialized or {}).get("id", "openai")
        # v3 API: используем generation()
        # у некоторых сборок типы не прописаны — подавим ворнинг тайпчекера:
        self._gen = self.lf.generation(  # type: ignore[attr-defined]
            name="llm.chat",
            model=model,
            input={"prompts": prompts},
            metadata={"provider": "openai"},
            tags=["llm", "react"],
        )

    def on_llm_end(self, response, **kwargs):
        if not self._gen:
            return
        try:
            outputs = []
            # LangChain возвращает список generations; соберём текст
            for choice in response.generations[0]:
                outputs.append(getattr(choice, "text", None) or getattr(choice, "message", None))
            self._gen.end(output={"responses": outputs})  # type: ignore[attr-defined]
        finally:
            self._gen = None

    def on_llm_error(self, error, **kwargs):
        if not self._gen:
            return
        try:
            self._gen.end(error=str(error))  # type: ignore[attr-defined]
        finally:
            self._gen = None