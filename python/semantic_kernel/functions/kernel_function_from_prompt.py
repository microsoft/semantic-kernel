# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, AsyncIterable, Dict, List, Optional, Tuple, Union

from pydantic import Field, ValidationError, model_validator

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import (
    OpenAIChatMessageContent,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.contents.streaming_kernel_content import StreamingKernelContent
from semantic_kernel.exceptions import FunctionExecutionException, FunctionInitializationError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.chat import store_results

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

PROMPT_RETURN_PARAM = KernelParameterMetadata(
    name="return",
    description="The completion result",
    default_value=None,
    type="FunctionResult",
    required=True,
)


class KernelFunctionFromPrompt(KernelFunction):
    """Semantic Kernel Function from a prompt."""

    prompt_template: KernelPromptTemplate
    prompt_execution_settings: Dict[str, PromptExecutionSettings] = Field(default_factory=dict)

    def __init__(
        self,
        function_name: str,
        plugin_name: str,
        description: Optional[str] = None,
        prompt: Optional[str] = None,
        template_format: Optional[str] = "semantic-kernel",
        prompt_template: Optional[KernelPromptTemplate] = None,
        prompt_template_config: Optional[PromptTemplateConfig] = None,
        prompt_execution_settings: Optional[
            Union[PromptExecutionSettings, List[PromptExecutionSettings], Dict[str, PromptExecutionSettings]]
        ] = None,
    ) -> None:
        """
        Initializes a new instance of the KernelFunctionFromPrompt class

        Args:
            function_name (str): The name of the function
            plugin_name (str): The name of the plugin
            description (str): The description for the function

            prompt (Optional[str]): The prompt
            template_format (Optional[str]): The template format, default is "semantic-kernel"
            prompt_template (Optional[KernelPromptTemplate]): The prompt template
            prompt_template_config (Optional[PromptTemplateConfig]): The prompt template configuration
            prompt_execution_settings (Optional): instance, list or dict of PromptExecutionSettings to be used
                by the function, can also be supplied through prompt_template_config,
                but the supplied one is used if both are present.
                prompt_template_config (Optional[PromptTemplateConfig]): the prompt template config.
        """
        if not prompt and not prompt_template_config and not prompt_template:
            raise FunctionInitializationError(
                "The prompt cannot be empty, must be supplied directly, \
through prompt_template_config or in the prompt_template."
            )

        if not prompt_template:
            if not prompt_template_config:
                # prompt must be there if prompt_template and prompt_template_config is not supplied
                prompt_template_config = PromptTemplateConfig(
                    name=function_name,
                    description=description,
                    template=prompt,
                    template_format=template_format,
                )
            prompt_template = KernelPromptTemplate(prompt_template_config=prompt_template_config)

        try:
            metadata = KernelFunctionMetadata(
                name=function_name,
                plugin_name=plugin_name,
                description=description,
                parameters=prompt_template.prompt_template_config.get_kernel_parameter_metadata(),
                is_prompt=True,
                is_asynchronous=True,
                return_parameter=PROMPT_RETURN_PARAM,
            )
        except ValidationError as exc:
            raise FunctionInitializationError("Failed to create KernelFunctionMetadata") from exc
        super().__init__(
            metadata=metadata, prompt_template=prompt_template, prompt_execution_settings=prompt_execution_settings
        )

    @model_validator(mode="before")
    @classmethod
    def rewrite_execution_settings(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, PromptExecutionSettings]:
        """Rewrite execution settings to a dictionary.

        If the prompt_execution_settings is not a dictionary, it is converted to a dictionary.
        If it is not supplied, but prompt_template is, the prompt_template's execution settings are used.
        """
        prompt_execution_settings = data.get("prompt_execution_settings")
        prompt_template = data.get("prompt_template")
        if not prompt_execution_settings:
            if prompt_template:
                prompt_execution_settings = prompt_template.prompt_template_config.execution_settings
                data["prompt_execution_settings"] = prompt_execution_settings
            if not prompt_execution_settings:
                return data
        if isinstance(prompt_execution_settings, PromptExecutionSettings):
            data["prompt_execution_settings"] = {
                prompt_execution_settings.service_id or "default": prompt_execution_settings
            }
        if isinstance(prompt_execution_settings, list):
            data["prompt_execution_settings"] = {s.service_id or "default": s for s in prompt_execution_settings}
        return data

    async def _invoke_internal(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> "FunctionResult":
        """Invokes the function with the given arguments."""
        arguments = self.add_default_values(arguments)
        service, execution_settings = kernel.select_ai_service(self, arguments)
        prompt = await self.prompt_template.render(kernel, arguments)

        if isinstance(service, ChatCompletionClientBase):
            auto_invoke, max_iterations = self._get_auto_invoke_execution_settings(execution_settings)
            return await self._handle_chat_service(
                kernel=kernel,
                service=service,
                execution_settings=execution_settings,
                prompt=prompt,
                auto_invoke=auto_invoke,
                max_iterations=max_iterations,
                arguments=arguments,
            )

        if isinstance(service, TextCompletionClientBase):
            return await self._handle_text_service(
                service=service,
                execution_settings=execution_settings,
                prompt=prompt,
                arguments=arguments,
            )

        raise ValueError(f"Service `{type(service).__name__}` is not a valid AI service")

    def _get_auto_invoke_execution_settings(self, execution_settings: PromptExecutionSettings) -> Tuple[bool, int]:
        """Gets the auto invoke and max iterations settings."""
        if isinstance(execution_settings, OpenAIPromptExecutionSettings):
            auto_invoke = execution_settings.auto_invoke_kernel_functions
            max_iterations = execution_settings.max_allowed_tool_calls if auto_invoke else 1
        else:
            auto_invoke = False
            max_iterations = 1
        return auto_invoke, max_iterations

    async def _handle_chat_service(
        self,
        kernel: "Kernel",
        service: ChatCompletionClientBase,
        execution_settings: PromptExecutionSettings,
        prompt: str,
        auto_invoke: bool,
        max_iterations: int,
        arguments: KernelArguments,
    ) -> FunctionResult:
        """Handles the chat service call."""
        chat_history = ChatHistory.from_rendered_prompt(prompt, service.get_chat_message_content_class())
        try:
            for _ in range(max_iterations):
                completions = await service.complete_chat(chat_history, execution_settings)
                if not completions:
                    raise FunctionExecutionException(f"No completions returned while invoking function {self.name}")

                chat_history = store_results(chat_history=chat_history, results=completions)
                if self._should_return(completions, auto_invoke):
                    return self._create_function_result(completions, chat_history, arguments)

                # Process each tool call
                for result in completions:
                    await self._process_tool_calls(result, kernel, chat_history)

        except Exception as exc:
            raise FunctionExecutionException(f"Error occurred while invoking function {self.name}: {exc}") from exc

    async def _handle_text_service(
        self,
        service: TextCompletionClientBase,
        execution_settings: PromptExecutionSettings,
        prompt: str,
        arguments: KernelArguments,
    ) -> FunctionResult:
        """Handles the text service call."""
        try:
            completions = await service.complete(prompt, execution_settings)
            return self._create_function_result(completions, None, arguments, prompt=prompt)
        except Exception as e:
            logger.error(f"Error occurred while invoking function {self.name}: {e}")
            raise

    def _should_return(self, completions: List[ChatMessageContent], auto_invoke: bool) -> bool:
        """Determines if the completions should be returned."""
        return (
            not auto_invoke
            or any(not isinstance(completion, OpenAIChatMessageContent) for completion in completions)
            or len(completions) > 1
            or any(not hasattr(completion, "tool_calls") or not completion.tool_calls for completion in completions)
        )

    def _create_function_result(
        self, completions: List[ChatMessageContent], chat_history, arguments, prompt=None
    ) -> FunctionResult:
        """Creates a function result with the given completions."""
        metadata = {
            "arguments": arguments,
            "metadata": [completion.metadata for completion in completions],
        }
        if chat_history:
            metadata["messages"] = chat_history
        if prompt:
            metadata["prompt"] = prompt
        return FunctionResult(
            function=self.metadata,
            value=completions,
            metadata=metadata,
        )

    async def _process_tool_calls(
        self, result: ChatMessageContent, kernel: "Kernel", chat_history: ChatHistory
    ) -> None:
        """Processes the tool calls in the result."""
        for tool_call in result.tool_calls:
            func = kernel.func(**tool_call.function.split_name_dict())
            arguments = tool_call.function.to_kernel_arguments()
            func_result = await kernel.invoke(func, arguments)
            chat_history.add_tool_message(
                str(func_result.value),
                metadata={"tool_call_id": tool_call.id, "function_name": tool_call.function.name},
            )

    async def _invoke_internal_stream(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> AsyncIterable[Union[FunctionResult, List[StreamingKernelContent]]]:
        arguments = self.add_default_values(arguments)
        service, execution_settings = kernel.select_ai_service(self, arguments)
        prompt = await self.prompt_template.render(kernel, arguments)
        complete_stream_content = []
        tools = []
        auto_invoke, max_iterations = self._get_auto_invoke_execution_settings(execution_settings)

        if isinstance(service, ChatCompletionClientBase):
            chat_history = ChatHistory.from_rendered_prompt(prompt, service.get_chat_message_content_class())
            try:
                for _ in range(max_iterations):
                    async for partial_content, stored_data in service.complete_chat_stream(
                        chat_history=chat_history, settings=execution_settings
                    ):
                        finish_reason = getattr(partial_content[0], "finish_reason", None)

                        # Check for tool calls and accumulate if present
                        if partial_content[0].tool_calls:
                            complete_stream_content.append(partial_content)
                            tools.append(stored_data)
                            if finish_reason == FinishReason.STOP:
                                break  # Stop processing further if finish reason indicates to stop
                            continue
                        # yield partial_content

                        # Yield non-tool call content if not stopping
                        if finish_reason != FinishReason.STOP and finish_reason != FinishReason.TOOL_CALLS:
                            yield partial_content
                        else:
                            # If we hit STOP, break from the loop
                            break

                    # Process accumulated tool calls
                    if complete_stream_content:
                        chat_content = None
                        for result in complete_stream_content:
                            content_to_add = result[0]  # Assuming result[0] is the content
                            # TODO: This line is building up the tool_calls again, even though it is already formed
                            chat_content = content_to_add if chat_content is None else chat_content + content_to_add

                        # TODO: fix this -- right now overwrite the tool_calls with the last tool_calls
                        last_item = tools[-1]
                        tool_calls = last_item["tool_call_ids_by_index"]
                        tools_to_add = [tool_call_list[0] for tool_call_list in tool_calls.values()]
                        chat_content.tool_calls = tools_to_add  # Directly assign the list

                        chat_content.role = ChatRole.ASSISTANT
                        chat_history = store_results(chat_history=chat_history, results=[chat_content])

                        # Process each tool call
                        for _, tool_call_list in tool_calls.items():
                            tool_call = tool_call_list[0]
                            func = kernel.func(**tool_call.function.split_name_dict())
                            # print(f"Debugging only: {tool_call.function}")
                            arguments = tool_call.function.to_kernel_arguments()
                            func_result = await kernel.invoke(func, arguments)
                            chat_history.add_tool_message(
                                str(func_result.value),
                                metadata={"tool_call_id": tool_call.id, "function_name": tool_call.function.name},
                            )
                        complete_stream_content = []
                        tools = []  # Reset tools list for next iteration

                    if finish_reason == FinishReason.STOP:
                        break

                return  # Exit after processing all iterations
            except Exception as e:
                logger.error(f"Error occurred while invoking function {self.name}: {e}")
                yield FunctionResult(function=self.metadata, value=None, metadata={"error": e})

        if isinstance(service, TextCompletionClientBase):
            try:
                async for partial_content in service.complete_stream(prompt=prompt, settings=execution_settings):
                    yield partial_content
                return
            except Exception as e:
                logger.error(f"Error occurred while invoking function {self.name}: {e}")
                yield FunctionResult(function=self.metadata, value=None, metadata={"error": e})

        raise FunctionExecutionException(f"Service `{type(service)}` is not a valid AI service")  # pragma: no cover

    def add_default_values(self, arguments: "KernelArguments") -> KernelArguments:
        """Gathers the function parameters from the arguments."""
        for parameter in self.prompt_template.prompt_template_config.input_variables:
            if parameter.name not in arguments and parameter.default not in {None, "", False, 0}:
                arguments[parameter.name] = parameter.default
        return arguments
