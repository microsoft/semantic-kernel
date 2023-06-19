# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from unittest.mock import MagicMock, patch

import pytest

import semantic_kernel.connectors.ai.guidance as sk_guidance
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.utils.null_logger import NullLogger


def test_guidance_text_completion_init() -> None:
    deployment_name = "test_deployment"
    model_id = "text-davinci-001"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    # Test successful initialization
    guidance_text_completion = sk_guidance.GuidanceAOAITextCompletion(
        model_id=model_id,
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        logger=logger,
    )

    assert isinstance(guidance_text_completion, sk_guidance.GuidanceAOAITextCompletion)


def test_guidance_text_completion_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    model_id = "text-davinci-001"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(
        ValueError, match="The deployment name cannot be `None` or empty"
    ):
        sk_guidance.GuidanceAOAITextCompletion(
            model_id=model_id,
            deployment_name="",
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_guidance_text_completion_init_with_empty_api_key() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    model_id = "text-davinci-001"
    # api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(
        ValueError, match="The Azure API key cannot be `None` or empty`"
    ):
        sk_guidance.GuidanceAOAITextCompletion(
            model_id=model_id,
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key="",
            api_version=api_version,
            logger=logger,
        )


def test_guidance_text_completion_init_with_empty_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    model_id = "text-davinci-001"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(
        ValueError, match="The Azure endpoint cannot be `None` or empty"
    ):
        sk_guidance.GuidanceAOAITextCompletion(
            model_id=model_id,
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_guidance_text_completion_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    model_id = "text-davinci-001"
    endpoint = "http://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(ValueError, match="The Azure endpoint must start with https://"):
        sk_guidance.GuidanceAOAITextCompletion(
            model_id=model_id,
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


@pytest.mark.asyncio
async def test_guidance_text_completion_call_with_parameters() -> None:
    mock_program = MagicMock()
    with patch(
        "semantic_kernel.connectors.ai.guidance.services.guidance_oai_text_completion.guidance.Program",
        new=mock_program,
    ):
        deployment_name = "test_deployment"
        model_id = "text-davinci-001"
        endpoint = "https://test-endpoint.com"
        api_key = "test_api_key"
        Logger("test_logger")
        prompt = "hello world"
        complete_request_settings = CompleteRequestSettings()
        context_var = ContextVariables("test")
        context = SKContext(context_var, NullMemory(), None, NullLogger())

        guidance_text_completion = sk_guidance.GuidanceAOAITextCompletion(
            model_id=model_id,
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
        )

        await guidance_text_completion.complete_async(
            prompt, complete_request_settings, context
        )

        mock_program.assert_called_once_with(prompt)
