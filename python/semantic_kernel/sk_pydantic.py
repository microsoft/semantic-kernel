from __future__ import annotations

# the above is needed for python 3.8 compatibility, can be removed once we drop support for 3.8
from typing import Annotated

from pydantic import BaseModel, ConfigDict, UrlConstraints
from pydantic.networks import Url

HttpsUrl = Annotated[Url, UrlConstraints(max_length=2083, allowed_schemes=["https"])]


class SKBaseModel(BaseModel):
    """Base class for all pydantic models in the SK."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


# TODO: remove these aliases in SK v1
PydanticField = SKBaseModel
SKGenericModel = SKBaseModel
