# Copyright (c) Microsoft. All rights reserved.
import asyncio
import sys
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

if sys.version_info >= (3, 9):
    from semantic_kernel.connectors.ai.google_palm import (
        GooglePalmTextRequestSettings,
    )
    from semantic_kernel.connectors.ai.google_palm.services.gp_text_completion import (
        GooglePalmTextCompletion,
    )


pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 9), reason="Google Palm requires Python 3.9 or greater"
)


def test_google_palm_text_completion_init() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"

    # Test successful initialization
    gp_text_completion = GooglePalmTextCompletion(
        ai_model_id=ai_model_id,
        api_key=api_key,
    )

    assert gp_text_completion.ai_model_id == ai_model_id
    assert gp_text_completion.api_key == api_key
    assert isinstance(gp_text_completion, GooglePalmTextCompletion)


def test_google_palm_text_completion_init_with_empty_api_key() -> None:
    ai_model_id = "test_model_id"
    # api_key = "test_api_key"

    with pytest.raises(ValidationError, match="api_key"):
        GooglePalmTextCompletion(
            ai_model_id=ai_model_id,
            api_key="",
        )


@pytest.mark.asyncio
async def test_google_palm_text_completion_complete_async_call_with_parameters() -> None:
    mock_response = MagicMock()
    mock_response.result = asyncio.Future()
    mock_response.result.set_result("Example response")
    mock_gp = MagicMock()
    mock_gp.generate_text.return_value = mock_response
    with patch(
        "semantic_kernel.connectors.ai.google_palm.services.gp_text_completion.palm",
        new=mock_gp,
    ):
        ai_model_id = "test_model_id"
        api_key = "test_api_key"
        prompt = "hello world"
        gp_text_completion = GooglePalmTextCompletion(
            ai_model_id=ai_model_id,
            api_key=api_key,
        )
        settings = GooglePalmTextRequestSettings()
        response = await gp_text_completion.complete_async(prompt, settings)
        assert isinstance(response.result(), str) and len(response.result()) > 0

        mock_gp.generate_text.assert_called_once_with(
            model=ai_model_id,
            prompt=prompt,
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
            candidate_count=settings.candidate_count,
            top_p=settings.top_p,
            top_k=settings.top_k,
        )
