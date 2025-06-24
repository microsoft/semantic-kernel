# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated, Any

import requests
from azure.search.documents.indexes.models import (
    ComplexField,
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    VectorSearch,
    VectorSearchProfile,
)
from pydantic import BaseModel, ConfigDict

from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel

"""
The data model used for this sample is based on the hotel data model from the Azure AI Search samples.
The source can be found here: https://github.com/Azure/azure-search-vector-samples/blob/main/data/hotels.json
The version in this folder, is modified to have python style names and no vectors.
Below we define a custom index for the hotel data model.
The reason for this is that the built-in connector cannot properly handle the complex data types.

This file is referenced by the two scripts and does not have to be executed directly.
The first script (1_interact_with_the_collection.py) will show interacting with the records.
The second script (2_use_as_a_plugin.py) will show interacting with the collection as a plugin.
"""


class Rooms(BaseModel):
    Type: str
    Description: str
    Description_fr: str
    BaseRate: float
    BedOptions: str
    SleepsCount: int
    SmokingAllowed: bool
    Tags: list[str]

    model_config = ConfigDict(extra="ignore")


class Address(BaseModel):
    StreetAddress: str
    City: str | None
    StateProvince: str | None
    PostalCode: str | None
    Country: str | None

    model_config = ConfigDict(extra="ignore")


@vectorstoremodel(collection_name="hotel-index")
class HotelSampleClass(BaseModel):
    HotelId: Annotated[str, VectorStoreField("key")]
    HotelName: Annotated[str | None, VectorStoreField("data")] = None
    Description: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)]
    DescriptionVector: Annotated[list[float] | str | None, VectorStoreField("vector", dimensions=1536)] = None
    Description_fr: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)]
    DescriptionFrVector: Annotated[list[float] | str | None, VectorStoreField("vector", dimensions=1536)] = None
    Category: Annotated[str, VectorStoreField("data")]
    Tags: Annotated[list[str], VectorStoreField("data", is_indexed=True)]
    ParkingIncluded: Annotated[bool | None, VectorStoreField("data")] = None
    LastRenovationDate: Annotated[str | None, VectorStoreField("data", type=SearchFieldDataType.DateTimeOffset)] = None
    Rating: Annotated[float, VectorStoreField("data")]
    Location: Annotated[dict[str, Any], VectorStoreField("data", type=SearchFieldDataType.GeographyPoint)]
    Address: Annotated[Address, VectorStoreField("data")]
    Rooms: Annotated[list[Rooms], VectorStoreField("data")]

    model_config = ConfigDict(extra="ignore")

    def model_post_init(self, context: Any) -> None:
        if self.DescriptionVector is None:
            self.DescriptionVector = self.Description
        if self.DescriptionFrVector is None:
            self.DescriptionFrVector = self.Description_fr


def load_records(url: str | None = None) -> list[HotelSampleClass]:
    """
    Load the records from the given URL (default: Azure hotels.json).
    Removes the 'DescriptionEmbedding' field.
    :param url: The URL to the hotels.json file.
    :return: A list of HotelSampleClass objects.
    """
    if url is None:
        url = "https://raw.githubusercontent.com/Azure/azure-search-vector-samples/refs/heads/main/data/hotels.json"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    all_records = response.json()
    return [HotelSampleClass.model_validate(record) for record in all_records]


custom_index = SearchIndex(
    name="hotel-index",
    fields=[
        SearchField(
            name="HotelId",
            type="Edm.String",
            key=True,
            hidden=False,
            filterable=True,
            sortable=False,
            facetable=False,
            searchable=True,
        ),
        SearchField(
            name="HotelName",
            type="Edm.String",
            hidden=False,
            filterable=True,
            sortable=True,
            facetable=False,
            searchable=True,
        ),
        SearchField(
            name="Description",
            type="Edm.String",
            hidden=False,
            filterable=False,
            sortable=False,
            facetable=False,
            searchable=True,
        ),
        SearchField(
            name="DescriptionVector",
            type="Collection(Edm.Single)",
            hidden=False,
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="hnsw",
        ),
        SearchField(
            name="Description_fr",
            type="Edm.String",
            hidden=False,
            filterable=False,
            sortable=False,
            facetable=False,
            searchable=True,
            analyzer_name="fr.microsoft",
        ),
        SearchField(
            name="DescriptionFrVector",
            type="Collection(Edm.Single)",
            hidden=False,
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="hnsw",
        ),
        SearchField(
            name="Category",
            type="Edm.String",
            hidden=False,
            filterable=True,
            sortable=False,
            facetable=True,
            searchable=True,
        ),
        SearchField(
            name="Tags",
            type="Collection(Edm.String)",
            hidden=False,
            filterable=True,
            sortable=False,
            facetable=True,
            searchable=True,
        ),
        SearchField(
            name="ParkingIncluded",
            type="Edm.Boolean",
            hidden=False,
            filterable=True,
            sortable=False,
            facetable=True,
            searchable=False,
        ),
        SearchField(
            name="LastRenovationDate",
            type="Edm.DateTimeOffset",
            hidden=False,
            filterable=False,
            sortable=True,
            facetable=False,
            searchable=False,
        ),
        SearchField(
            name="Rating",
            type="Edm.Double",
            hidden=False,
            filterable=True,
            sortable=True,
            facetable=True,
            searchable=False,
        ),
        ComplexField(
            name="Address",
            collection=False,
            fields=[
                SearchField(
                    name="StreetAddress",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=False,
                    searchable=True,
                ),
                SearchField(
                    name="City",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="StateProvince",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="PostalCode",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="Country",
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
            name="Location",
            type="Edm.GeographyPoint",
            hidden=False,
            filterable=True,
            sortable=True,
            facetable=False,
            searchable=False,
        ),
        ComplexField(
            name="Rooms",
            collection=True,
            fields=[
                SearchField(
                    name="Description",
                    type="Edm.String",
                    hidden=False,
                    filterable=False,
                    sortable=False,
                    facetable=False,
                    searchable=True,
                ),
                SearchField(
                    name="Description_fr",
                    type="Edm.String",
                    hidden=False,
                    filterable=False,
                    sortable=False,
                    facetable=False,
                    searchable=True,
                    analyzer_name="fr.microsoft",
                ),
                SearchField(
                    name="Type",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="BaseRate",
                    type="Edm.Double",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=False,
                ),
                SearchField(
                    name="BedOptions",
                    type="Edm.String",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=True,
                ),
                SearchField(
                    name="SleepsCount",
                    type="Edm.Int64",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=False,
                ),
                SearchField(
                    name="SmokingAllowed",
                    type="Edm.Boolean",
                    hidden=False,
                    filterable=True,
                    sortable=False,
                    facetable=True,
                    searchable=False,
                ),
                SearchField(
                    name="Tags",
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
