# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class PlannerException(KernelException):
    pass


class PlannerExecutionException(PlannerException):
    pass


class PlannerInvalidGoalError(KernelException):
    pass


class PlannerInvalidPlanError(KernelException):
    pass


class PlannerInvalidConfigurationError(KernelException):
    pass


class PlannerCreatePlanError(KernelException):
    pass


__all__ = [
    "PlannerException",
    "PlannerExecutionException",
    "PlannerInvalidGoalError",
    "PlannerInvalidPlanError",
    "PlannerInvalidConfigurationError",
    "PlannerCreatePlanError",
]
