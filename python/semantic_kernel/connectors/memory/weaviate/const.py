# Copyright (c) Microsoft. All rights reserved.

from weaviate.classes.config import DataType

TYPE_MAPPER_DATA = {
    "str": DataType.TEXT,
    "int": DataType.INT,
    "float": DataType.NUMBER,
    "bool": DataType.BOOL,
    "list[str]": DataType.TEXT_ARRAY,
    "list[int]": DataType.INT_ARRAY,
    "list[float]": DataType.NUMBER_ARRAY,
    "list[bool]": DataType.BOOL_ARRAY,
    "default": DataType.TEXT,
}
