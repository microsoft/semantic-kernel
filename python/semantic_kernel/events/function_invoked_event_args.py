from semantic_kernel.events.sk_events_args import SKEventArgs


class FunctionInvokedEventArgs(SKEventArgs):
    def __init__(self, function_view, context):
        super().__init__(function_view, context)
        self._repeat_requested = False

    @property
    def is_repeat_requested(self):
        return self._repeat_requested

    def repeat(self):
        self._repeat_requested = True
