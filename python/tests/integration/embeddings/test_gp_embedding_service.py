# Copyright (c) Microsoft. All rights reserved.

import os
import sys

import pytest

import semantic_kernel as sk

if sys.version_info >= (3, 9):
    import semantic_kernel.connectors.ai.google_palm as sk_gp

pytestmark = [
    pytest.mark.skipif(sys.version_info < (3, 9), reason="Google Palm requires Python 3.9 or greater"),
    pytest.mark.skipif(
        "Python_Integration_Tests" in os.environ,
        reason="Google Palm integration tests are only set up to run locally",
    ),
]


@pytest.mark.asyncio
async def test_gp_embedding_service(create_kernel, get_gp_config):
    kernel = create_kernel

    api_key = get_gp_config

    palm_text_embed = sk_gp.GooglePalmTextEmbedding("models/embedding-gecko-001", api_key)
    kernel.add_service(palm_text_embed)
    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=palm_text_embed)

    await kernel.memory.save_information("test", id="info1", text="this is a test")
    await kernel.memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )
