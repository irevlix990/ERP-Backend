from pydantic import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_URL_ROLE_KEY: str
    
    class Config:
        env_file = ".env"
        
settings = Settings()