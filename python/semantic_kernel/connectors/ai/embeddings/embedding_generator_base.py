# Copyright (c) Microsoft. All rights reserved.

from typing_extensions import deprecated

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase as NewEmbeddingGeneratorBase
from semantic_kernel.utils.feature_stage_decorator import experimental


@deprecated(
    "This class has been moved to semantic_kernel.connectors.ai.embedding_generator_base. Please update your imports."
)
@experimental
class EmbeddingGeneratorBase(NewEmbeddingGeneratorBase):
    """Base class for embedding generators."""

    pass
