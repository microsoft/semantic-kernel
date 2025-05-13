# Copyright (c) Microsoft. All rights reserved.


import json
from pathlib import Path
from typing import Annotated, Any

from azure.search.documents.indexes.models import (
    ComplexField,
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    VectorSearch,
    VectorSearchProfile,
)
from pydantic import BaseModel

from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)

"""
The data model used for this sample is based on the hotel data model from the Azure AI Search samples.
The source can be found here: https://github.com/Azure/azure-search-vector-samples/blob/main/data/hotels.json
The version in this folder, is modified to have python style names and no vectors.
Below we define a custom index for the hotel data model.
The reason for this is that the built-in connector cannot properly handle the complex data types.
"""


class Rooms(BaseModel):
    type: str
    description: str
    description_fr: str
    base_rate: float
    bed_options: str
    sleeps_count: int
    smoking_allowed: bool
    tags: list[str]


class Address(BaseModel):
    street_address: str
    city: str | None
    state_province: str | None
    postal_code: str | None
    country: str | None


@vectorstoremodel(collection_name="hotel-index")
class HotelSampleClass(BaseModel):
    hotel_id: Annotated[str, VectorStoreRecordKeyField]
    hotel_name: Annotated[str | None, VectorStoreRecordDataField()] = None
    description: Annotated[
        str,
        VectorStoreRecordDataField(is_full_text_indexed=True),
    ]
    description_vector: Annotated[
        list[float] | str | None,
        VectorStoreRecordVectorField(dimensions=1536),
    ] = None
    description_fr: Annotated[str, VectorStoreRecordDataField(is_full_text_indexed=True)]
    description_fr_vector: Annotated[
        list[float] | str | None,
        VectorStoreRecordVectorField(dimensions=1536),
    ] = None
    category: Annotated[str, VectorStoreRecordDataField()]
    tags: Annotated[list[str], VectorStoreRecordDataField(is_indexed=True)]
    parking_included: Annotated[bool | None, VectorStoreRecordDataField()] = None
    last_renovation_date: Annotated[
        str | None, VectorStoreRecordDataField(property_type=SearchFieldDataType.DateTimeOffset)
    ] = None
    rating: Annotated[float, VectorStoreRecordDataField()]
    location: Annotated[dict[str, Any], VectorStoreRecordDataField(property_type=SearchFieldDataType.GeographyPoint)]
    address: Annotated[Address, VectorStoreRecordDataField()]
    rooms: Annotated[list[Rooms], VectorStoreRecordDataField()]

    def model_post_init(self, context: Any) -> None:
        # This is called after the model is created, you can use this to set default values
        # or to do any other initialization.
        if self.description_vector is None:
            self.description_vector = self.description
        if self.description_fr_vector is None:
            self.description_fr_vector = self.description_fr


def load_records(file_path: str = "hotels.json") -> list[HotelSampleClass]:
    """
    Load the records from the hotels.json file.
    :param file_path: The path to the hotels.json file.
    :return: A list of HotelSampleClass objects.
    """
    path = Path.cwd() / "samples" / "concepts" / "memory" / "azure_ai_search_hotel_samples" / file_path
    if not path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist.")
    if not path.is_file():
        raise ValueError(f"Path {file_path} is not a file.")
    with open(path, encoding="utf-8") as f:
        all_records = json.load(f)
    return [HotelSampleClass.model_validate(record) for record in all_records]


custom_index = SearchIndex(
    name="hotel-index",
    fields=[
        SearchField(
            name="hotel_id",
            type="Edm.String",
            key=True,
            hidden=False,
            filterable=True,
            sortable=False,
            facetable=False,
            searchable=True,
        ),
        SearchField(
            name="hotel_name",
            type="Edm.String",
            hidden=False,
            filterable=True,
            sortable=True,
            facetable=False,
            searchable=True,
        ),
        SearchField(
            name="description",
            type="Edm.String",
            hidden=False,
            filterable=False,
            sortable=False,
            facetable=False,
            searchable=True,
        ),
        SearchField(
            name="description_vector",
            type="Collection(Edm.Single)",
            hidden=False,
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="hnsw",
        ),
        SearchField(
            name="description_fr",
            type="Edm.String",
            hidden=False,
            filterable=False,
            sortable=False,
            facetable=False,
            searchable=True,
            analyzer_name="fr.microsoft",
        ),
        SearchField(
            name="description_fr_vector",
            type="Collection(Edm.Single)",
            hidden=False,
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="hnsw",
        ),
        SearchField(
            name="category",
            type="Edm.String",
            hidden=False,
            filterable=True,
            sortable=False,
            facetable=True,
            searchable=True,
        ),
        SearchField(
            name="tags",
            type="Collection(Edm.String)",
            hidden=False,
            filterable=True,
            sortable=False,
            facetable=True,
            searchable=True,
        ),
        SearchField(
            name="parking_included",
            type="Edm.Boolean",
            hidden=False,
            filterable=True,
            sortable=False,
            facetable=True,
            searchable=False,
        ),
        SearchField(
            name="last_renovation_date",
            type="Edm.DateTimeOffset",
            hidden=False,
            filterable=False,
            sortable=True,
            facetable=False,
            searchable=False,
        ),
        SearchField(
            name="rating",
            type="Edm.Double",
            hidden=False,
            filterable=True,
            sortable=True,
            facetable=True,
            searchable=False,
        ),
        ComplexField(
            name="address",
            collection=False,
            fields=[
                SearchField(
                    name="street_address",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=False,
                    searchable=True,
                ),
                SearchField(
                    name="city",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="state_province",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="postal_code",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="country",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
            ],
        ),
        SearchField(
            name="location",
            type="Edm.GeographyPoint",
            hidden=False,
            filterable=True,
            sortable=True,
            facetable=False,
            searchable=False,
        ),
        ComplexField(
            name="rooms",
            collection=True,
            fields=[
                SearchField(
                    name="description",
                    type="Edm.String",
                    hidden=False,
                    filterable=False,
                    sortable=False,
                    facetable=False,
                    searchable=True,
                ),
                SearchField(
                    name="description_fr",
                    type="Edm.String",
                    hidden=False,
                    filterable=False,
                    sortable=False,
                    facetable=False,
                    searchable=True,
                    analyzer_name="fr.microsoft",
                ),
                SearchField(
                    name="type",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="base_rate",
                    type="Edm.Double",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=False,
                ),
                SearchField(
                    name="bed_options",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="sleeps_count",
                    type="Edm.Int64",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=False,
                ),
                SearchField(
                    name="smoking_allowed",
                    type="Edm.Boolean",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=False,
                ),
                SearchField(
                    name="tags",
                    type="Collection(Edm.String)",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
            ],
        ),
    ],
    vector_search=VectorSearch(
        profiles=[VectorSearchProfile(name="hnsw", algorithm_configuration_name="hnsw")],
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        vectorizers=[],
    ),
)
