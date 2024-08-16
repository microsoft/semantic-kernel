# Copyright (c) Microsoft. All rights reserved.

import json
from logging import Logger

from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments


class KernelFunctionLogMessages:
    """Kernel function log messages.

    This class contains static methods to log messages related to kernel functions.
    """

    @staticmethod
    def log_function_invoking(logger: Logger, kernel_function_name: str):
        """Log message when a kernel function is invoked."""
        logger.info("Function %s invoking.", kernel_function_name)

    @staticmethod
    def log_function_arguments(logger: Logger, arguments: KernelArguments):
        """Log message when a kernel function is invoked."""
        logger.debug("Function arguments: %s", arguments)

    @staticmethod
    def log_function_invoked_success(logger: Logger, kernel_function_name: str):
        """Log message when a kernel function is invoked successfully."""
        logger.info("Function %s succeeded.", kernel_function_name)

    @staticmethod
    def log_function_result_value(logger: Logger, function_result: FunctionResult | None):
        """Log message when a kernel function result is returned."""
        if function_result is not None:
            if isinstance(function_result.value, str):
                logger.debug("Function result value: %s", function_result.value)
            else:
                logger.debug("Function result value: %s", json.dumps(function_result.value))
        else:
            logger.debug("Function result: None")

    @staticmethod
    def log_function_error(logger: Logger, error: Exception):
        """Log message when a kernel function fails."""
        logger.error("Function failed. Error: %s", error)

    @staticmethod
    def log_function_completed(logger: Logger, duration: float):
        """Log message when a kernel function is completed."""
        logger.info("Function completed. Duration: %fs", duration)

    @staticmethod
    def log_function_streaming_invoking(logger: Logger, kernel_function_name: str):
        """Log message when a kernel function is invoked via streaming."""
        logger.info("Function %s streaming.", kernel_function_name)

    @staticmethod
    def log_function_streaming_completed(logger: Logger, duration: float):
        """Log message when a kernel function is completed via streaming."""
        logger.info("Function streaming completed. Duration: %fs", duration)
