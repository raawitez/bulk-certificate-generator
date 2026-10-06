from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator"
    API_KEY: str
    DATABASE_URL: str
    RABBITMQ_URL: str

    class Config:
        env_file = ".env"

settings = Settings()