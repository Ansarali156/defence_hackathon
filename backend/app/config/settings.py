from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    PORT: int = 8000

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_EXPIRY_HOURS: int = 2
    REFRESH_TOKEN_EXPIRY_DAYS: int = 7

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "defense-hackathon-2026"
    AWS_REGION: str = "ap-south-1"

    # Email
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@defensehackathon2026.com"
    EMAIL_FROM_NAME: str = "Defense Hackathon 2026"

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    ADMIN_EMAIL: str = "admin@defensehackathon2026.com"


settings = Settings()
