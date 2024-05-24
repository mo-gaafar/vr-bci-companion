
from pydantic_settings import BaseSettings
from pydantic import Field
from .models import StorageType


class MLConfig(BaseSettings):
    MODEL_STORAGE: StorageType = Field(
        StorageType.local,
        title="Model Storage Type",
        description="Default storage type for models",
    )
    # ML_MODEL_TYPE: str = Field(

    #     title="ML Model",
    #     description="ML Model",
    # )
    ML_MODEL_FILE: str = Field(
        "trained_model.pkl",
        title="ML Model File",
        description="ML Model File",
    )
    # ML_MODEL_FILE_TEST: str = Field(
    #     title="ML Model File Test",
    #     description="ML Model File Test",
    # )
    # ML_DATA_FILE: str = Field(
    #     title="ML Data File",
    #     description="ML Data File",
    # )
    # ML_DATA_FILE_TEST: str = Field(
    #     title="ML Data File Test",
    #     description="ML Data File Test",
    # )
    UNTRAINED_MODEL_FILE: str = Field(
        "untrained_model.pkl",
        title="Untrained Model File Name",
        description="Untrained Model File",
    )
    TRAINED_MODEL_FILE: str = Field(
        "trained_model.pkl",
        title="Trained Model File",
        description="Trained Model File",
    )
    MODELS_DIR: str = Field(
        "models",
        title="Models Directory",
        description="Models Directory",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # extra inputs permitted
        extra = "allow"
