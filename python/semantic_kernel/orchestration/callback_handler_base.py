from typing import List, Tuple, Union

from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


class CallbackHandlerBase:
    def on_pipeline_start(self, context: SKContext, pipeline_label: str):
        pass

    def on_function_start(self, context: SKContext, func: SKFunctionBase):
        pass

    def on_prompt_rendered(
        self,
        context: SKContext,
        func: SKFunctionBase,
        prompt: Union[str, List[Tuple[str, str]]],
    ):
        pass

    def on_function_end(self, context: SKContext, func: SKFunctionBase):
        pass

    def on_function_error(self, context: SKContext, func: SKFunctionBase):
        pass

    def on_pipeline_end(self, context: SKContext, pipeline_label: str):
        pass


class MultiplexHandler(CallbackHandlerBase):
    _handlers: List[CallbackHandlerBase]

    def __init__(self, handlers: List[CallbackHandlerBase]) -> None:
        self._handlers = handlers

    def on_pipeline_start(self, context: SKContext):
        for handler in self._handlers:
            handler.on_pipeline_start(context)

    def on_function_start(self, context: SKContext, func: SKFunctionBase):
        for handler in self._handlers:
            handler.on_function_start(context, func)

    def on_prompt_rendered(
        self,
        context: SKContext,
        func: SKFunctionBase,
        prompt: Union[str, List[Tuple[str, str]]],
    ):
        for handler in self._handlers:
            handler.on_prompt_rendered(context, func, prompt)

    def on_function_end(self, context: SKContext, func: SKFunctionBase):
        for handler in self._handlers:
            handler.on_function_end(context, func)

    def on_function_error(self, context: SKContext, func: SKFunctionBase):
        for handler in self._handlers:
            handler.on_function_error(context, func)

    def on_pipeline_end(self, context: SKContext):
        for handler in self._handlers:
            handler.on_pipeline_end(context)
