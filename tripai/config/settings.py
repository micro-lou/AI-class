import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    DOUBAN_API_KEY = os.getenv("DOUBAN_API_KEY", "")
    DOUBAN_API_BASE = os.getenv("DOUBAN_API_BASE", "https://api.doubao.com/v1")
    DOUBAN_MODEL = os.getenv("DOUBAN_MODEL", "Doubao-3.5")
    
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

settings = Settings()