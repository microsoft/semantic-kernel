# Copyright (c) Microsoft. All rights reserved.


import logging
from typing import Annotated, Any, ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict, Field, UrlConstraints
from pydantic.networks import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

HttpsUrl = Annotated[AnyUrl, UrlConstraints(max_length=2083, allowed_schemes=["https"])]

logger = logging.getLogger("semantic_kernel")


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
    env_file_path: str | None = Field(default=None, exclude=True)
    env_file_encoding: str | None = Field(default="utf-8", exclude=True)

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """Initialize the settings class."""
        # Remove any None values from the kwargs so that defaults are used.
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        super().__init__(**kwargs)

    def __new__(cls: type["T"], *args: Any, **kwargs: Any) -> "T":
        """Override the __new__ method to set the env_prefix."""
        # for both, if supplied but None, set to default
        if "env_file_encoding" in kwargs and kwargs["env_file_encoding"] is not None:
            env_file_encoding = kwargs["env_file_encoding"]
        else:
            env_file_encoding = "utf-8"
        if "env_file_path" in kwargs and kwargs["env_file_path"] is not None:
            env_file_path = kwargs["env_file_path"]
        else:
            env_file_path = ".env"
        cls.model_config.update(  # type: ignore
            env_prefix=cls.env_prefix,
            env_file=env_file_path,
            env_file_encoding=env_file_encoding,
        )
        cls.model_rebuild()
        return super().__new__(cls)

    @classmethod
    def create(cls: type["T"], **data: Any) -> "T":
        """Update the model_config with the prefix."""
        logger.warning(
            "The create method is deprecated. Use the __new__ method instead.",
        )
        return cls(**data)
