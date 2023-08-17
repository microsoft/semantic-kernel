// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Kernel logic exception */
public class KernelException extends SKException {

    @Nonnull private final ErrorCodes errorCode;

    public KernelException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

    public KernelException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    public KernelException(
            @Nonnull ErrorCodes errorCode,
            @Nullable String message,
            @Nullable Throwable innerException) {
        super(formatDefaultMessage(errorCode.getMessage(), message), innerException);
        this.errorCode = errorCode;
    }

    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    /// <summary>
    /// Semantic kernel error codes.
    /// </summary>
    public enum ErrorCodes {
        /// <summary>
        /// Unknown error.
        /// </summary>
        UNKOWN_ERROR("Unknown error"),

        INVALID_FUNCTION_DESCRIPTION("Invalid function description"),

        FUNCTION_OVERLOAD_NOT_SUPPORTED("Function overload not supported"),

        FUNCTION_NOT_AVAILABLE("Function not available"),

        FUNCTION_TYPE_NOT_SUPPORTED("Function type not supported"),

        INVALID_FUNCTION_TYPE("Invalid function type"),

        INVALID_SERVICE_CONFIGURATION("Invalid service configuration"),

        SERVICE_NOT_FOUND("Service not found"),

        SKILL_COLLECTION_NOT_SET("Skill collection not set"),

        FUNCTION_INVOCATION_ERROR("Represents an error that occurs when invoking a function");

        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        public String getMessage() {
            return message;
        }
    }
}
