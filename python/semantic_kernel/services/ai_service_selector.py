<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.exceptions import KernelServiceNotFoundError
from semantic_kernel.kernel_types import AI_SERVICE_CLIENT_TYPE

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
    from semantic_kernel.services.kernel_services_extension import (
        KernelServicesExtension,
    )
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
from typing import TYPE_CHECKING, Tuple, Union

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.functions.kernel_arguments import KernelArguments

ALL_COMPLETION_SERVICE_TYPES = Union[TextCompletionClientBase, ChatCompletionClientBase]

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


class AIServiceSelector:
    """Default service selector, can be subclassed and overridden.

    To use a custom service selector, subclass this class and override the select_ai_service method.
    Make sure that the function signature stays the same.
    """

    def select_ai_service(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        self,
        kernel: "KernelServicesExtension",
        function: "KernelFunction",
        arguments: "KernelArguments",
        type_: (
            type[AI_SERVICE_CLIENT_TYPE]
            | tuple[type[AI_SERVICE_CLIENT_TYPE], ...]
            | None
        ) = None,
    ) -> tuple["AIServiceClientBase", "PromptExecutionSettings"]:
        """Select an AI Service on a first come, first served basis.

        Starts with execution settings in the arguments,
        followed by the execution settings from the function.
        If the same service_id is in both, the one in the arguments will be used.
        """
        if type_ is None:
            from semantic_kernel.connectors.ai.chat_completion_client_base import (
                ChatCompletionClientBase,
            )
            from semantic_kernel.connectors.ai.text_completion_client_base import (
                TextCompletionClientBase,
            )

            type_ = (TextCompletionClientBase, ChatCompletionClientBase)  # type: ignore

        execution_settings_dict = arguments.execution_settings or {}
        if func_exec_settings := getattr(function, "prompt_execution_settings", None):
            for id, settings in func_exec_settings.items():
                if id not in execution_settings_dict:
                    execution_settings_dict[id] = settings
        if not execution_settings_dict:
            from semantic_kernel.connectors.ai.prompt_execution_settings import (
                PromptExecutionSettings,
            )

            execution_settings_dict = {DEFAULT_SERVICE_NAME: PromptExecutionSettings()}
        for service_id, settings in execution_settings_dict.items():
            try:
                if (service := kernel.get_service(service_id, type=type_)) is not None:
                    settings_class = service.get_prompt_execution_settings_class()
                    if isinstance(settings, settings_class):
                        return service, settings
                    return service, settings_class.from_prompt_execution_settings(
                        settings
                    )
            except KernelServiceNotFoundError:
                continue
        raise KernelServiceNotFoundError("No service found.")
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
        self, kernel: "Kernel", function: "KernelFunction", arguments: KernelArguments
    ) -> Tuple[ALL_COMPLETION_SERVICE_TYPES, PromptExecutionSettings]:
        """Select a AI Service on a first come, first served basis,
        starting with execution settings in the arguments,
        followed by the execution settings from the function.
        If the same service_id is in both, the one in the arguments will be used.
        """
        execution_settings_dict = arguments.execution_settings or {}
        for id, settings in function.prompt_execution_settings.items():
            if id not in execution_settings_dict:
                execution_settings_dict[id] = settings
        for service_id, settings in execution_settings_dict.items():
            service = kernel.get_service(service_id, type=(TextCompletionClientBase, ChatCompletionClientBase))
            if service:
                service_settings = service.get_prompt_execution_settings_from_settings(settings)
                return service, service_settings
        raise AIException(AIException.ErrorCodes.NoServiceFound, "No service found.")
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
