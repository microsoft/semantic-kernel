# Copyright (c) Microsoft. All rights reserved.


import numpy as np

RAW_RECORD_LIST = {
    "id": "e6103c03-487f-4d7d-9c23-4723651c17f4",
    "content": "test content",
    "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
}


RAW_RECORD_ARRAY = {
    "id": "e6103c03-487f-4d7d-9c23-4723651c17f4",
    "content": "test content",
    "vector": np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
}


# PANDAS_RECORD_DEFINITION = VectorStoreRecordDefinition(
#     fields={
#         "vector": VectorStoreRecordVectorField(
#             name="vector",
#             index_kind="hnsw",
#             dimensions=5,
#             distance_function="cosine_similarity",
#             property_type="float",
#         ),
#         "id": VectorStoreRecordKeyField(name="id"),
#         "content": VectorStoreRecordDataField(
#             name="content", has_embedding=True, embedding_property_name="vector", property_type="str"
#         ),
#     },
#     container_mode=True,
#     to_dict=lambda x: x.to_dict(orient="records"),
#     from_dict=lambda x, **_: pd.DataFrame(x),
# )

# A Pandas record definition with flat index kind
# PANDAS_RECORD_DEFINITION_FLAT = VectorStoreRecordDefinition(
#     fields={
#         "vector": VectorStoreRecordVectorField(
#             name="vector",
#             index_kind="flat",
#             dimensions=5,
#             distance_function="cosine_similarity",
#             property_type="float",
#         ),
#         "id": VectorStoreRecordKeyField(name="id"),
#         "content": VectorStoreRecordDataField(
#             name="content", has_embedding=True, embedding_property_name="vector", property_type="str"
#         ),
#     },
#     container_mode=True,
#     to_dict=lambda x: x.to_dict(orient="records"),
#     from_dict=lambda x, **_: pd.DataFrame(x),
# )


# @vectorstoremodel
# @dataclass
# class TestDataModelArray(distance_function: str):
#     """A data model where the vector is a numpy array."""

#     vector: Annotated[
#         np.ndarray | None,
#         VectorStoreRecordVectorField(
#             index_kind="hnsw",
#             dimensions=5,
#             distance_function=distance_function,
#             property_type="float",
#             serialize_function=np.ndarray.tolist,
#             deserialize_function=np.array,
#         ),
#     ] = None
#     other: str | None = None
#     id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
#     content: Annotated[
#         str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
#     ] = "content1"


# @vectorstoremodel
# @dataclass
# class TestDataModelArrayFlat(distance_function:str):
#     """A data model where the vector is a numpy array and the index kind is IndexKind.Flat."""

#     vector: Annotated[
#         np.ndarray | None,
#         VectorStoreRecordVectorField(
#             index_kind="flat",
#             dimensions=5,
#             distance_function=distance_function,
#             property_type="float",
#             serialize_function=np.ndarray.tolist,
#             deserialize_function=np.array,
#         ),
#     ] = None
#     other: str | None = None
#     id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
#     content: Annotated[
#         str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
#     ] = "content1"


# @vectorstoremodel
# @dataclass
# class TestDataModelList(distance_function: str):
#     """A data model where the vector is a list."""

#     vector: Annotated[
#         list[float] | None,
#         VectorStoreRecordVectorField(
#             index_kind="hnsw",
#             dimensions=5,
#             distance_function=distance_function,
#             property_type="float",
#         ),
#     ] = None
#     other: str | None = None
#     id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
#     content: Annotated[
#         str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
#     ] = "content1"


# @vectorstoremodel
# @dataclass
# class TestDataModelListFlat:
#     """A data model where the vector is a list and the index kind is IndexKind.Flat."""

#     vector: Annotated[
#         list[float] | None,
#         VectorStoreRecordVectorField(
#             index_kind="flat",
#             dimensions=5,
#             distance_function="cosine_similarity",
#             property_type="float",
#         ),
#     ] = None
#     other: str | None = None
#     id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
#     content: Annotated[
#         str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
#     ] = "content1"
