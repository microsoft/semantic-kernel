# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class AgentException(KernelException):
    """Base class for all agent exceptions."""

    pass


class AgentFileNotFoundException(AgentException):
    """The requested file was not found."""

    pass


class AgentInitializationException(AgentException):
    """An error occurred while initializing the agent."""

    pass


class AgentExecutionException(AgentException):
    """An error occurred while executing the agent."""

    pass


class AgentInvokeException(AgentException):
    """An error occurred while invoking the agent."""

    pass


class AgentChatException(AgentException):
    """An error occurred while invoking the agent chat."""

    pass
