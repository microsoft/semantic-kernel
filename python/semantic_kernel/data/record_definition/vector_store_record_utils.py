# Copyright (c) Microsoft. All rights reserved.


from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from semantic_kernel.data.record_definition.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import VectorStoreModelException
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
    from semantic_kernel.kernel import Kernel

TModel = TypeVar("TModel", bound=object)


@experimental
class VectorStoreRecordUtils:
    """Helper class to easily add embeddings to a (set of) vector store record."""

    def __init__(self, kernel: "Kernel"):
        """Initializes the VectorStoreRecordUtils with a kernel."""
        self.kernel = kernel

    async def add_vector_to_records(
        self,
        records: OneOrMany[TModel],
        data_model_type: type[TModel] | None = None,
        data_model_definition: "VectorStoreRecordDefinition | None" = None,
        **kwargs,
    ) -> OneOrMany[TModel]:
        """Vectorize the vector record.

        This function can be passed to upsert or upsert batch of a VectorStoreRecordCollection.

        Loops through the fields of the data model definition,
        looks at data fields, if they have a vector field,
        looks up that vector field and checks if is a local embedding.

        If so adds that to a list of embeddings to make.

        Finally calls Kernel add_embedding_to_object with the list of embeddings to make.

        Optional arguments are passed onto the Kernel add_embedding_to_object call.
        """
        # dict of embedding_field.name and tuple of record, settings, field_name
        embeddings_to_make: list[tuple[str, str, dict[str, "PromptExecutionSettings"], Callable | None]] = []
        if not data_model_definition:
            data_model_definition = getattr(data_model_type, "__kernel_vectorstoremodel_definition__", None)
        if not data_model_definition:
            raise VectorStoreModelException(
                "Data model definition is required, either directly or from the data model type."
            )
        for name, field in data_model_definition.fields.items():  # type: ignore
            if (
                not isinstance(field, VectorStoreRecordDataField)
                or not field.has_embedding
                or not field.embedding_property_name
            ):
                continue
            embedding_field = data_model_definition.fields.get(field.embedding_property_name)
            if not isinstance(embedding_field, VectorStoreRecordVectorField):
                raise VectorStoreModelException("Embedding field must be a VectorStoreRecordVectorField")
            if embedding_field.local_embedding:
                embeddings_to_make.append((
                    name,
                    field.embedding_property_name,
                    embedding_field.embedding_settings,
                    embedding_field.deserialize_function,
                ))

        for field_to_embed, field_to_store, settings, cast_callable in embeddings_to_make:
            await self.kernel.add_embedding_to_object(
                inputs=records,
                field_to_embed=field_to_embed,
                field_to_store=field_to_store,
                execution_settings=settings,
                container_mode=data_model_definition.container_mode,
                cast_function=cast_callable,
                **kwargs,
            )
        return records
