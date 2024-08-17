from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"

    MARIADB_HOST: str = os.getenv("MARIADB_HOST")
    MARIADB_PORT: str = os.getenv("MARIADB_PORT")
    MARIADB_USERNAME: str = os.getenv("MARIADB_USERNAME")
    MARIADB_PASSWORD: str = os.getenv("MARIADB_PASSWORD")
    MARIADB_DATABASE: str = os.getenv("MARIADB_DATABASE")

    MARIADB_URL: str = (f'mariadb+pymysql://{MARIADB_USERNAME}:{MARIADB_PASSWORD}@{MARIADB_HOST}:{MARIADB_PORT}'
                        f'/{MARIADB_DATABASE}?charset=utf8mb4')

    ACCESS_TOKEN_ENCODE_ALGORITHM: str = os.getenv('ACCESS_TOKEN_ENCODE_ALGORITHM')
    ACCESS_SECRET_KEY: str = os.getenv('ACCESS_SECRET_KEY')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 2

    REFRESH_TOKEN_ENCODE_ALGORITHM: str = os.getenv('REFRESH_TOKEN_ENCODE_ALGORITHM')
    REFRESH_SECRET_KEY: str = os.getenv('REFRESH_SECRET_KEY')
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14

    PASSWORD_SALT: str = os.getenv('PASSWORD_SALT')

    TOURAPI_LDM_KEY: str = os.getenv('TOURAPI_LDM_KEY')

    class Config:
        case_sensitive = True


settings = Settings()