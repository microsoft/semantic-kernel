# Copyright (c) Microsoft. All rights reserved.

from pydantic_settings import BaseSettings

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class BaseModelSettings(BaseSettings):
    env_file_path: str | None = None

    class Config:
        """Pydantic configuration settings."""

        env_file = None
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def create(cls, **kwargs):
        """Create an instance of the class."""
        if "env_file_path" in kwargs and kwargs["env_file_path"]:
            cls.Config.env_file = kwargs["env_file_path"]
        else:
            cls.Config.env_file = None
        return cls(**kwargs)
