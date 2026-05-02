from decouple import config


class Settings:
    PORT: int = config("PORT", default=8087, cast=int)
    ENVIRONMENT: str = config("NODE_ENV", default="production")
    SERVICE_NAME: str = "verificacion-legal-api"
    SERVICE_VERSION: str = config("SERVICE_VERSION", default="0.0.1")
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
    SKIP_AUTH: bool = config("SKIP_AUTH", default=False, cast=bool)

    GOOGLE_CLIENT_ID: str = config("GOOGLE_CLIENT_ID", default="")

    DB_HOST: str = config("DB_HOST", default="localhost")
    DB_USER: str = config("DB_USER", default="postgres")
    DB_PASSWORD: str = config("DB_PASSWORD", default="")
    DB_NAME: str = config("DB_NAME", default="hipotecai")
    DB_PORT: int = config("DB_PORT", default=5432, cast=int)
    INSTANCE_CONNECTION_NAME: str = config("INSTANCE_CONNECTION_NAME", default="")

    # Servicios laterales
    SINTETIZADOR_URL: str = config("SINTETIZADOR_URL", default="http://localhost:8086")

    # Configuración legal
    DIAS_VALIDEZ_CERTIFICADOS_CBR: int = config("DIAS_VALIDEZ_CERTIFICADOS_CBR", default=30, cast=int)
    DIAS_VALIDEZ_CERTIFICADOS_SII: int = config("DIAS_VALIDEZ_CERTIFICADOS_SII", default=180, cast=int)

    ALLOWED_ORIGINS: list = config(
        "ALLOWED_ORIGINS",
        default="http://localhost:3030,http://localhost:3000",
        cast=lambda v: [s.strip() for s in v.split(",")],
    )


settings = Settings()
