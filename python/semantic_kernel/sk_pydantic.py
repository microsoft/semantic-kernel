
from pydantic import BaseModel, ConfigDict, HttpUrl


class HttpsUrl(HttpUrl):
    allowed_schemes = {"https"}


class SKBaseModel(BaseModel):
    """Base class for all pydantic models in the SK."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


# TODO: remove these aliases in SK v1
PydanticField = SKBaseModel
SKGenericModel = SKBaseModel
