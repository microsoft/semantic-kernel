# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated, Any, ClassVar, Type, TypeVar

from pydantic import BaseModel, ConfigDict, UrlConstraints
from pydantic.networks import Url
from pydantic_settings import BaseSettings, SettingsConfigDict

HttpsUrl = Annotated[Url, UrlConstraints(max_length=2083, allowed_schemes=["https"])]


class KernelBaseModel(BaseModel):
    """Base class for all pydantic models in the SK."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True)


T = TypeVar("T", bound="KernelBaseSettings")


class KernelBaseSettings(BaseSettings):
    """Base class for all settings classes in the SK.

    A subclass creates it's fields and overrides the env_prefix class variable
    with the prefix for the environment variables.
    """

    env_prefix: ClassVar[str] = ""
    env_file_path: str | None = None

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )

    @classmethod
    def create(cls: Type["T"], **data: Any) -> "T":
        """Update the model_config with the prefix."""
        cls.model_config["env_prefix"] = cls.env_prefix
        if data.get("env_file_path"):
            cls.model_config["env_file"] = data["env_file_path"]
            cls.model_config["env_file_encoding"] = "utf-8"
        data = {k: v for k, v in data.items() if v is not None}
        return cls(**data)
