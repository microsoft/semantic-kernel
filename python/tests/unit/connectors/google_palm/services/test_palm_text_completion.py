# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import MagicMock, patch

import pytest
from google.generativeai.types import Completion
from google.generativeai.types.text_types import TextCompletion

from semantic_kernel.connectors.ai.google_palm import GooglePalmTextPromptExecutionSettings
from semantic_kernel.connectors.ai.google_palm.services.gp_text_completion import GooglePalmTextCompletion
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_google_palm_text_completion_init(google_palm_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    # Test successful initialization
    gp_text_completion = GooglePalmTextCompletion(
        ai_model_id=ai_model_id,
    )

    assert gp_text_completion.ai_model_id == ai_model_id
    assert gp_text_completion.api_key == google_palm_unit_test_env["GOOGLE_PALM_API_KEY"]
    assert isinstance(gp_text_completion, GooglePalmTextCompletion)


@pytest.mark.parametrize("exclude_list", [["GOOGLE_PALM_API_KEY"]], indirect=True)
def test_google_palm_text_completion_init_with_empty_api_key(google_palm_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    with pytest.raises(ServiceInitializationError):
        GooglePalmTextCompletion(
            ai_model_id=ai_model_id,
            env_file_path="test.env",
        )


@pytest.mark.asyncio
async def test_google_palm_text_completion_complete_call_with_parameters(google_palm_unit_test_env) -> None:
    gp_completion = Completion()
    gp_completion.candidates = [TextCompletion(output="Example response")]
    gp_completion.filters = None
    gp_completion.safety_feedback = None
    mock_gp = MagicMock()
    mock_gp.generate_text.return_value = gp_completion
    with patch(
        "semantic_kernel.connectors.ai.google_palm.services.gp_text_completion.palm",
        new=mock_gp,
    ):
        ai_model_id = "test_model_id"
        prompt = "hello world"
        gp_text_completion = GooglePalmTextCompletion(
            ai_model_id=ai_model_id,
        )
        settings = GooglePalmTextPromptExecutionSettings()
        response = await gp_text_completion.get_text_contents(prompt, settings)
        assert isinstance(response[0].text, str) and len(response) > 0

        mock_gp.generate_text.assert_called_once_with(
            model=ai_model_id,
            prompt=prompt,
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
            candidate_count=settings.candidate_count,
            top_p=settings.top_p,
            top_k=settings.top_k,
        )
