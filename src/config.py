import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CREDENTIALS_PATH = "credentials.json"
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")