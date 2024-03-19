from typing import TYPE_CHECKING, Tuple, Union

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.exceptions import KernelServiceNotFoundError
from semantic_kernel.functions.kernel_arguments import KernelArguments

ALL_COMPLETION_SERVICE_TYPES = Union[TextCompletionClientBase, ChatCompletionClientBase]

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel


class AIServiceSelector:
    """Default service selector, can be subclassed and overridden.

    To use a custom service selector, subclass this class and override the select_ai_service method.
    Make sure that the function signature stays the same.
    """

    def select_ai_service(
        self, kernel: "Kernel", function: "KernelFunction", arguments: KernelArguments
    ) -> Tuple[ALL_COMPLETION_SERVICE_TYPES, PromptExecutionSettings]:
        """Select a AI Service on a first come, first served basis,
        starting with execution settings in the arguments,
        followed by the execution settings from the function.
        If the same service_id is in both, the one in the arguments will be used.
        """
        execution_settings_dict = arguments.execution_settings or {}
        if func_exec_settings := getattr(function, "prompt_execution_settings", None):
            for id, settings in func_exec_settings.items():
                if id not in execution_settings_dict:
                    execution_settings_dict[id] = settings
        for service_id, settings in execution_settings_dict.items():
            service = kernel.get_service(service_id, type=(TextCompletionClientBase, ChatCompletionClientBase))
            if service:
                service_settings = service.get_prompt_execution_settings_from_settings(settings)
                return service, service_settings
        raise KernelServiceNotFoundError("No service found.")
