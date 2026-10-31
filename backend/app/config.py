import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    PORT: int = Field(default=8000)

    # Database
    MONGODB_URI: Optional[str] = Field(default=None)
    MONGODB_DB: str = Field(default="cit_scheduler")

    # Security
    JWT_SECRET: str = Field(default="dev_secret_key_antigravity_cit_2026_super_secure_32chars")
    JWT_EXPIRE_MINUTES: int = Field(default=480)

    # CORS
    FRONTEND_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
    FRONTEND_ORIGIN_REGEX: Optional[str] = Field(default=r"https://.*\.vercel\.app")

    # AI / LLM
    LLM_PROVIDER: str = Field(default="gemini") # gemini | anthropic | openai | none
    LLM_API_KEY: Optional[str] = Field(default=None)
    LLM_MODEL: str = Field(default="gemini-1.5-flash")

    # Solver
    SOLVER_TIME_LIMIT_SECONDS: int = Field(default=60)
    SOLVER_WORKERS: int = Field(default=2)
    SEED_ON_STARTUP: bool = Field(default=True)

    @property
    def cors_origins(self) -> List[str]:
        if not self.FRONTEND_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
