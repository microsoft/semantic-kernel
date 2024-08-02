# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated, Any, ClassVar, TypeVar

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

    In the case where a value is specified for the same Settings field in multiple ways,
    the selected value is determined as follows (in descending order of priority):
      - Arguments passed to the Settings class initializer.
      - Environment variables, e.g. my_prefix_special_function as described above.
      - Variables loaded from a dotenv (.env) file.
      - Variables loaded from the secrets directory.
      - The default field values for the Settings model.
    """

    env_prefix: ClassVar[str] = ""
    env_file_path: str | None = None
    env_file_encoding: str = "utf-8"

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )

    @classmethod
    def create(cls: type["T"], **data: Any) -> "T":
        """Update the model_config with the prefix."""
        cls.model_config["env_prefix"] = cls.env_prefix
        if data.get("env_file_path"):
            cls.model_config["env_file"] = data["env_file_path"]
        else:
            cls.model_config["env_file"] = ".env"
        cls.model_config["env_file_encoding"] = data.get("env_file_encoding", "utf-8")
        data = {k: v for k, v in data.items() if v is not None}
        return cls(**data)
