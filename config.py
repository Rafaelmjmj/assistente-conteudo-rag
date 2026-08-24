import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "chave-super-segura"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:1234@localhost:5433/tcc_db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")