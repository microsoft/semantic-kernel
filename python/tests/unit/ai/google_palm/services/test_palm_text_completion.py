# Copyright (c) Microsoft. All rights reserved.

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.google_palm.services.gp_text_completion import (
    GooglePalmTextCompletion
)


def test_google_palm_text_completion_init() -> None:
    model_id = "test_model_id"
    api_key = "test_api_key"

    # Test successful initialization
    gp_text_completion = GooglePalmTextCompletion(
        model_id=model_id,
        api_key=api_key,
    )

    assert gp_text_completion._model_id == model_id
    assert gp_text_completion._api_key == api_key
    assert isinstance(gp_text_completion, GooglePalmTextCompletion)

def test_google_palm_text_completion_init_with_empty_api_key() -> None:
    model_id = "test_model_id"
    #api_key = "test_api_key"

    with pytest.raises(
        ValueError, match="The Google PaLM API key cannot be `None` or empty"
    ):
        GooglePalmTextCompletion(
            model_id=model_id,
            api_key="",
        )

@pytest.mark.asyncio
async def test_google_palm_text_completion_complete_async_call_with_parameters() -> None:
    mock_response = MagicMock()
    mock_response.result = asyncio.Future()
    mock_response.result.set_result("Example response")
    mock_gp = MagicMock()
    mock_gp.generate_text.return_value = mock_response
    with patch (
        "semantic_kernel.connectors.ai.google_palm.services.gp_text_completion.palm",
        new=mock_gp,
    ):
        model_id = "test_model_id"
        api_key = "test_api_key"
        prompt = "hello world"
        gp_text_completion = GooglePalmTextCompletion(
            model_id=model_id,
            api_key=api_key,
        )
        settings = CompleteRequestSettings()
        response = await gp_text_completion.complete_async(prompt, settings)
        assert isinstance(response.result(), str) and len(response.result()) > 0

        mock_gp.generate_text.assert_called_once_with(
            model=model_id, 
            prompt=prompt,
            temperature=settings.temperature,
            max_output_tokens=settings.max_tokens,
            stop_sequences=None,
            candidate_count=settings.number_of_responses,
            top_p=settings.top_p,
        )