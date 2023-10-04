from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition.function_view import FunctionView


class SKEventArgs:
    def __init__(self, function_view: FunctionView, context: SKContext):
        if context is None or function_view is None:
            raise ValueError("function_view and context cannot be None")

        self._function_view = function_view
        self._context = context

    @property
    def function_view(self):
        return self._function_view

    @property
    def context(self):
        return self._context
