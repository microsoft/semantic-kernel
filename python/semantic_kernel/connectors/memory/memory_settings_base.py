# Copyright (c) Microsoft. All rights reserved.

from pydantic_settings import BaseSettings


class BaseModelSettings(BaseSettings):
    env_file_path: str | None = None

    class Config:
        env_file = None
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def create(cls, **kwargs):
        if "env_file_path" in kwargs and kwargs["env_file_path"]:
            cls.Config.env_file = kwargs["env_file_path"]
        else:
            cls.Config.env_file = None
        return cls(**kwargs)
