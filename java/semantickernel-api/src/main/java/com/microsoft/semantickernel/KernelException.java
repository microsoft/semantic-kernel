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
        UnknownError("Unknown error"),

        InvalidFunctionDescription("Invalid function description"),

        FunctionOverloadNotSupported("Function overload not supported"),

        FunctionNotAvailable("Function not available"),

        FunctionTypeNotSupported("Function type not supported"),

        InvalidFunctionType("Invalid function type"),

        InvalidServiceConfiguration("Invalid service configuration"),

        ServiceNotFound("Service not found"),

        SkillCollectionNotSet("Skill collection not set"),

        FunctionInvokeError("Represents an error that occurs when invoking a function");

        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        public String getMessage() {
            return message;
        }
    }
}
