# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class PlannerException(KernelException):
    """Base class for all planner exceptions."""

    pass


class PlannerExecutionException(PlannerException):
    """Base class for all planner execution exceptions."""

    pass


class PlannerInvalidGoalError(PlannerException):
    """An error occurred while validating the goal."""

    pass


class PlannerInvalidPlanError(PlannerException):
    """An error occurred while validating the plan."""

    pass


class PlannerInvalidConfigurationError(PlannerException):
    """An error occurred while validating the configuration."""

    pass


class PlannerCreatePlanError(PlannerException):
    """An error occurred while creating the plan."""

    pass


__all__ = [
    "PlannerCreatePlanError",
    "PlannerException",
    "PlannerExecutionException",
    "PlannerInvalidConfigurationError",
    "PlannerInvalidGoalError",
    "PlannerInvalidPlanError",
]
