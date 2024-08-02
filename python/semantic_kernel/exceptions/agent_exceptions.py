# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class AgentException(KernelException):
    pass


class AgentFileNotFoundException(AgentException):
    pass


class AgentInitializationError(AgentException):
    pass


class AgentExecutionError(AgentException):
    pass


class AgentInvokeError(AgentException):
    pass
