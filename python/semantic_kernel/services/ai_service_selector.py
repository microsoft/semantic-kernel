# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.exceptions import KernelServiceNotFoundError
from semantic_kernel.kernel_types import AI_SERVICE_CLIENT_TYPE

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
    from semantic_kernel.services.kernel_services_extension import KernelServicesExtension


class AIServiceSelector:
    """Default service selector, can be subclassed and overridden.

    To use a custom service selector, subclass this class and override the select_ai_service method.
    Make sure that the function signature stays the same.
    """

    def select_ai_service(
        self,
        kernel: "KernelServicesExtension",
        function: "KernelFunction | None" = None,
        arguments: "KernelArguments | None" = None,
        type_: type[AI_SERVICE_CLIENT_TYPE] | tuple[type[AI_SERVICE_CLIENT_TYPE], ...] | None = None,
    ) -> tuple["AIServiceClientBase", "PromptExecutionSettings"]:
        """Select an AI Service on a first come, first served basis.

        Starts with execution settings in the arguments,
        followed by the execution settings from the function.
        If the same service_id is in both, the one in the arguments will be used.

        Args:
            kernel: The kernel used.
            function: The function used. (optional)
            arguments: The arguments used. (optional)
            type_: The type of service to select. (optional)
        """
        if type_ is None:
            from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
            from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
            from semantic_kernel.connectors.ai.text_to_audio_client_base import TextToAudioClientBase
            from semantic_kernel.connectors.ai.text_to_image_client_base import TextToImageClientBase

            type_ = (TextCompletionClientBase, ChatCompletionClientBase, TextToAudioClientBase, TextToImageClientBase)  # type: ignore

        execution_settings_dict = arguments.execution_settings if arguments and arguments.execution_settings else {}
        if func_exec_settings := getattr(function, "prompt_execution_settings", None):
            for id, settings in func_exec_settings.items():
                if id not in execution_settings_dict:
                    execution_settings_dict[id] = settings
        if not execution_settings_dict:
            from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

            execution_settings_dict = {DEFAULT_SERVICE_NAME: PromptExecutionSettings()}
        for service_id, settings in execution_settings_dict.items():
            try:
                if (service := kernel.get_service(service_id, type=type_)) is not None:
                    settings_class = service.get_prompt_execution_settings_class()
                    if isinstance(settings, settings_class):
                        return service, settings
                    return service, settings_class.from_prompt_execution_settings(settings)
            except KernelServiceNotFoundError:
                continue
        raise KernelServiceNotFoundError("No service found.")
