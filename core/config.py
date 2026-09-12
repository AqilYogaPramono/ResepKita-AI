import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret_key_resep_kita")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "resep_kita")
    DB_MIN_POOL: int = int(os.getenv("DB_MIN_POOL", "2"))
    DB_MAX_POOL: int = int(os.getenv("DB_MAX_POOL", "10"))

settings = Settings()
