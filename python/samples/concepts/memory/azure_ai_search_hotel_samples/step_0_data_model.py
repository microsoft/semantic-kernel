# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated, Any

from pydantic import BaseModel

from semantic_kernel.connectors.ai.open_ai import OpenAIEmbeddingPromptExecutionSettings
from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)

###
# The data model used for this sample is based on the hotel data model from the Azure AI Search samples.
# When deploying a new index in Azure AI Search using the import wizard you can choose to deploy the 'hotel-samples'
# dataset, see here: https://learn.microsoft.com/en-us/azure/search/search-get-started-portal.
# This is the dataset used in this sample with some modifications.
# This model adds vectors for the 2 descriptions in English and French.
# Both are based on the 1536 dimensions of the OpenAI models.
# You can adjust this at creation time and then make the change below as well.
# Refer to the README for more information.
###


@vectorstoremodel
class HotelSampleClass(BaseModel):
    hotel_id: Annotated[str, VectorStoreRecordKeyField]
    hotel_name: Annotated[str | None, VectorStoreRecordDataField()] = None
    description: Annotated[
        str,
        VectorStoreRecordDataField(
            has_embedding=True, embedding_property_name="description_vector", is_full_text_searchable=True
        ),
    ]
    description_vector: Annotated[
        list[float] | None,
        VectorStoreRecordVectorField(
            dimensions=1536,
            local_embedding=True,
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
        ),
    ] = None
    description_fr: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="description_fr_vector")
    ]
    description_fr_vector: Annotated[
        list[float] | None,
        VectorStoreRecordVectorField(
            dimensions=1536,
            local_embedding=True,
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
        ),
    ] = None
    category: Annotated[str, VectorStoreRecordDataField()]
    tags: Annotated[list[str], VectorStoreRecordDataField()]
    parking_included: Annotated[bool | None, VectorStoreRecordDataField()] = None
    last_renovation_date: Annotated[str | None, VectorStoreRecordDataField()] = None
    rating: Annotated[float, VectorStoreRecordDataField()]
    location: Annotated[dict[str, Any], VectorStoreRecordDataField()]
    address: Annotated[dict[str, str | None], VectorStoreRecordDataField()]
    rooms: Annotated[list[dict[str, Any]], VectorStoreRecordDataField()]
