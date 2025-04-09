# Copyright (c) Microsoft. All rights reserved.


class OperationSelectionPredicateContext:
    """The context for the operation selection predicate."""

    def __init__(self, operation_id: str, path: str, method: str, description: str | None = None):
        """Initialize the operation selection predicate context."""
        self.operation_id = operation_id
        self.path = path
        self.method = method
        self.description = description
