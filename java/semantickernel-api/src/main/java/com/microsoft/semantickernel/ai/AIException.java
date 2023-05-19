// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai; // Copyright (c) Microsoft. All rights reserved.

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** AI logic exception */
public class AIException extends RuntimeException {

    @Nonnull private final ErrorCodes errorCode;

    public AIException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

    public AIException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    public AIException(
            @Nonnull ErrorCodes errorCode,
            @Nullable String message,
            @Nullable Throwable innerException) {
        super(getDefaultMessage(errorCode, message), innerException);
        this.errorCode = errorCode;
    }

    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    /* Translate the error code into a default message */
    private static String getDefaultMessage(
            @Nonnull ErrorCodes errorCode, @Nullable String message) {
        return String.format("%s: %s", errorCode.getMessage(), message);
    }

    /// <summary>
    /// Possible error codes for exceptions
    /// </summary>
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
