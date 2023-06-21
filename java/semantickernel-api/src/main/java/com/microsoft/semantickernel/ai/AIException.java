// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai;

import com.microsoft.semantickernel.SKException;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** AI logic exception */
public class AIException extends SKException {

    @Nonnull private final ErrorCodes errorCode;

    /**
     * Initializes a new instance of the {@link AIException} class.
     *
     * @param error The error code.
     */
    public AIException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

    /**
     * Initializes a new instance of the {@link AIException} class.
     *
     * @param errorCode The error code.
     * @param message The message.
     */
    public AIException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    /**
     * Initializes a new instance of the {@link AIException} class.
     *
     * @param errorCode The error code.
     * @param message The message.
     * @param innerException The cause of the exception.
     */
    public AIException(
            @Nonnull ErrorCodes errorCode,
            @Nullable String message,
            @Nullable Throwable innerException) {
        super(getDefaultMessage(errorCode, message), innerException);
        this.errorCode = errorCode;
    }

    /**
     * Gets the error code.
     *
     * @return The error code.
     */
    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    /** Translate the error code into a default message */
    private static String getDefaultMessage(
            @Nonnull ErrorCodes errorCode, @Nullable String message) {
        return String.format("%s: %s", errorCode.getMessage(), message);
    }

    public enum ErrorCodes {
        UnknownError("Unknown error"),

        NoResponse("No response"),

        AccessDenied("Access is denied"),

        InvalidRequest("The request was invalid"),

        InvalidResponseContent("The content of the response was invalid"),

        Throttling("The request was throttled"),

        RequestTimeout("The request timed out"),

        ServiceError("There was an error in the service"),

        ModelNotAvailable("The requested model is not available"),

        InvalidConfiguration("The supplied configuration was invalid"),

        FunctionTypeNotSupported("The function is not supported");
        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        public String getMessage() {
            return message;
        }
    }
}
