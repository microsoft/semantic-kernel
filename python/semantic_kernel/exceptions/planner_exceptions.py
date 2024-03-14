# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class PlannerException(KernelException):
    pass


class PlannerExecutionException(PlannerException):
    pass


class PlannerInvalidGoalError(PlannerException):
    pass


class PlannerInvalidPlanError(PlannerException):
    pass


class PlannerInvalidConfigurationError(PlannerException):
    pass


class PlannerCreatePlanError(PlannerException):
    pass


__all__ = [
    "PlannerException",
    "PlannerExecutionException",
    "PlannerInvalidGoalError",
    "PlannerInvalidPlanError",
    "PlannerInvalidConfigurationError",
    "PlannerCreatePlanError",
]
