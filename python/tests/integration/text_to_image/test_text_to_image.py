# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai.text_to_image_client_base import TextToImageClientBase
from tests.integration.text_to_image.text_to_image_test_base import TextToImageTestBase

pytestmark = pytest.mark.parametrize(
    "service_id, prompt",
    [
        pytest.param(
            "openai",
            "A cute tuxedo cat driving a race car.",
            id="openai",
        ),
        pytest.param(
            "azure_openai",
            "A cute tuxedo cat driving a race car.",
            id="azure_openai",
            marks=[
                pytest.mark.xfail(
                    reason="Temporary failure due to Internal Server Error (500) from Azure OpenAI.",
                ),
            ],
        ),
    ],
)


class TestTextToImage(TextToImageTestBase):
    """Test text-to-image services."""

    async def test_text_to_image(
        self,
        services: dict[str, TextToImageClientBase],
        service_id: str,
        prompt: str,
    ):
        service = services[service_id]
        image_url = await service.generate_image(prompt, 1024, 1024)
        assert image_url
