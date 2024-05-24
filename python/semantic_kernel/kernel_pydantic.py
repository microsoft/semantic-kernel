# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated

from pydantic import BaseModel, ConfigDict, UrlConstraints
from pydantic.networks import Url

HttpsUrl = Annotated[Url, UrlConstraints(max_length=2083, allowed_schemes=["https"])]


class KernelBaseModel(BaseModel):
    """Base class for all pydantic models in the SK."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True)
