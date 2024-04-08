from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings
from dotenv import dotenv_values
# from dateutil import tz
# import pytz


# Global config
DEVELOPMENT = False  # ! Change this to False when deploying
VERSION = "v1"
TZ = "Africa/Cairo"
ROOT_PREFIX = f"/api/{VERSION}"

# Environment variables


class Settings(BaseSettings):
    PORT: int = Field(
        default=8000,
        title="Port",
        description="Port used for running the app",
        type="integer",
    )
    SERVER_DOMAIN: str = Field(
        default="http://localhost",
        title="Server domain",
        description="Server domain",
        type="string",
    )

    ROOT_URL: str = Field(
        default=f"{SERVER_DOMAIN}:{PORT}",
        title="Root URL",
        description="Root URL",
        type="string",
    )

    APP_NAME: str = Field(
        default="VR BCI Game Server",
        title="App name",
        description="App name",
        type="string",
    )

    SECRET_KEY: SecretStr = Field(
        default="thisisaseriouscaseofmonkeybusiness",
        title="Secret key",
        description="Secret key used for JWT token",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        title="Access token expire minutes",
        description="Access token expire minutes",
        type="integer",
    )

    ADMIN_PASS: SecretStr = Field(
        title="Admin password",
        description="Admin password",
    )

    MONGO_URI: str = Field(
        title="Mongo URI",
        description="Mongo URI",
    )
    MONGO_DB: str = Field(
        title="Mongo DB",
        description="Mongo DB",
    )
    MONGO_DB_TEST: str = Field(
        title="Mongo DB Test",
        description="Mongo DB Test",
    )

    PRODUCTION: bool = Field(
        default=True,
        title="Production",
        description="Production",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # extra inputs permitted
        extra = "allow"


CONFIG = Settings()


# Server
try:
    CONFIG.MONGO_URI
except KeyError:
    print("Using different method to get env variables")
    import os
    CONFIG = dict(os.environ)
