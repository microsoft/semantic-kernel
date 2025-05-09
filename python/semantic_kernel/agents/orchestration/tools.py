# Copyright (c) Microsoft. All rights reserved.


from collections.abc import Awaitable, Callable

from pydantic import BaseModel

from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel import Kernel


def structure_output_transform(
    target_structure: type[BaseModel],
    service: ChatCompletionClientBase,
    prompt_execution_settings: PromptExecutionSettings | None = None,
) -> Callable[[DefaultTypeAlias], Awaitable[BaseModel]]:
    """Return a function that transforms the output of a chat completion service into a target structure.

    Args:
        target_structure (type): The target structure to transform the output into.
        service (ChatCompletionClientBase): The chat completion service to use for the transformation. This service
            must support structured output.
        prompt_execution_settings (PromptExecutionSettings, optional): The settings to use for the prompt execution.

    Returns:
        Callable[[DefaultTypeAlias], Awaitable[BaseModel]]: A function that takes the output of
            the chat completion service and transforms it into the target structure.
    """
    kernel = Kernel()
    kernel.add_service(service)

    settings = kernel.get_prompt_execution_settings_from_service_id(service.service_id)
    if prompt_execution_settings:
        settings.update_from_prompt_execution_settings(prompt_execution_settings)
    if not hasattr(settings, "response_format"):
        raise ValueError("The service must support structured output.")
    settings.response_format = target_structure

    chat_history = ChatHistory(
        system_message=(
            "Try your best to summarize the conversation into structured format:\n"
            f"{target_structure.model_json_schema()}."
        ),
    )

    async def output_transform(output: DefaultTypeAlias) -> BaseModel:
        """Transform the output of the chat completion service into the target structure."""
        if isinstance(output, ChatMessageContent):
            chat_history.add_message(output)
        elif isinstance(output, list) and all(isinstance(item, ChatMessageContent) for item in output):
            for item in output:
                chat_history.add_message(item)
        else:
            raise ValueError(f"Output must be {DefaultTypeAlias}.")

        response = await service.get_chat_message_content(chat_history, settings)
        assert response is not None  # nosec B101

        return target_structure.model_validate_json(response.content)

    return output_transform
