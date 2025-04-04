# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import Annotated, Any
from uuid import uuid4

from pandas import DataFrame
from pydantic import BaseModel, Field

from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)

# This concept shows the different ways you can create a vector store data model
# using dataclasses, Pydantic, and Python classes.
# As well as using types like Pandas Dataframes.

# There are a number of universal things about these data models:
# they must specify the type of field through the annotation (or the definition).
# there must be at least one field of type VectorStoreRecordKeyField.
# If you set the embedding_property_name in the VectorStoreRecordDataField, that field must exist and be a vector field.
# A unannotated field is allowed but must have a default value.

# The purpose of these models is to be what you pass to and get back from a vector store.
# There maybe limitations to data types that the vector store can handle,
# so not every store will be able to handle completely the same model.
# for instance, some stores only allow a string as the keyfield, while others allow str and int,
# so defining the key with a int, might make some stores unusable.

# The decorator takes the class and pulls out the fields and annotations to create a definition,
# of type VectorStoreRecordDefinition.
# This definition is used for the vector store to know how to handle the data model.

# You can also create the definition yourself, and pass it to the vector stores together with a standard type,
# like a dict or list.
# Or you can use the definition in container mode with something like a Pandas Dataframe.


# Data model using built-in Python dataclasses
@vectorstoremodel
@dataclass
class DataModelDataclass:
    vector: Annotated[list[float], VectorStoreRecordVectorField]
    key: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
    content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")] = (
        "content1"
    )
    other: str | None = None


# Data model using Pydantic BaseModels
@vectorstoremodel
class DataModelPydantic(BaseModel):
    id: Annotated[str, VectorStoreRecordKeyField()] = Field(default_factory=lambda: str(uuid4()))
    content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")] = (
        "content1"
    )
    vector: Annotated[list[float], VectorStoreRecordVectorField]
    other: str | None = None


# Data model using Python classes
# This one includes a custom serialize and deserialize method
@vectorstoremodel
class DataModelPython:
    def __init__(
        self,
        vector: Annotated[list[float], VectorStoreRecordVectorField],
        key: Annotated[str, VectorStoreRecordKeyField] = None,
        content: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")
        ] = "content1",
        other: str | None = None,
    ):
        self.vector = vector
        self.other = other
        self.key = key or str(uuid4())
        self.content = content

    def __str__(self) -> str:
        return f"DataModelPython(vector={self.vector}, key={self.key}, content={self.content}, other={self.other})"

    def serialize(self) -> dict[str, Any]:
        return {
            "vector": self.vector,
            "key": self.key,
            "content": self.content,
        }

    @classmethod
    def deserialize(cls, obj: dict[str, Any]) -> "DataModelDataclass":
        return cls(
            vector=obj["vector"],
            key=obj["key"],
            content=obj["content"],
        )


# Data model definition for use with Pandas
# note the container mode flag, which makes sure that records that are returned are in a container
# even when requesting a batch of records.
# There is also a to_dict and from_dict method, which are used to convert the data model to and from a dict,
# these should be specific to the type used, if using dict as type then these can be left off.
data_model_definition_pandas = VectorStoreRecordDefinition(
    fields={
        "vector": VectorStoreRecordVectorField(property_type="list[float]"),
        "key": VectorStoreRecordKeyField(property_type="str"),
        "content": VectorStoreRecordDataField(
            property_type="str", has_embedding=True, embedding_property_name="vector"
        ),
    },
    container_mode=True,
    to_dict=lambda record, **_: record.to_dict(orient="records"),
    from_dict=lambda records, **_: DataFrame(records),
)


if __name__ == "__main__":
    data_item1 = DataModelDataclass(content="Hello, world!", vector=[1.0, 2.0, 3.0], other=None)
    data_item2 = DataModelPydantic(content="Hello, world!", vector=[1.0, 2.0, 3.0], other=None)
    data_item3 = DataModelPython(content="Hello, world!", vector=[1.0, 2.0, 3.0], other=None)
    print("Example records:")
    print(f"DataClass:\n  {data_item1}", end="\n\n")
    print(f"Pydantic:\n  {data_item2}", end="\n\n")
    print(f"Python:\n  {data_item3}", end="\n\n")

    print("Item definitions:")
    print(f"DataClass:\n  {data_item1.__kernel_vectorstoremodel_definition__}", end="\n\n")
    print(f"Pydantic:\n  {data_item2.__kernel_vectorstoremodel_definition__}", end="\n\n")
    print(f"Python:\n  {data_item3.__kernel_vectorstoremodel_definition__}", end="\n\n")
    print(f"Definition for use with Pandas:\n  {data_model_definition_pandas}", end="\n\n")
    if (
        data_item1.__kernel_vectorstoremodel_definition__.fields
        == data_item2.__kernel_vectorstoremodel_definition__.fields
        == data_item3.__kernel_vectorstoremodel_definition__.fields
        == data_model_definition_pandas.fields
    ):
        print("All data models are the same")
    else:
        print("Data models are not the same")
