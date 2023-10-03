from semantic_kernel.events.sk_events_args import SKEventArgs

class FunctionInvokingEventArgs(SKEventArgs):
    def __init__(self, function_view, context):
        super().__init__(function_view, context)
        self._skip_requested = False
    
    @property
    def is_skip_requested(self):
        return self._skip_requested
    
    def skip(self):
        self._skip_requested = True
