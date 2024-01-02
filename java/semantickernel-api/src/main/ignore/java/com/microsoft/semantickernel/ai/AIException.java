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
        super(formatDefaultMessage(errorCode.getMessage(), message), innerException);
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

    /** Error codes */
    public enum ErrorCodes {
        /** Unknown error. */
        UNKNOWN_ERROR("Unknown error"),

        /** No response. */
        NO_RESPONSE("No response"),
        /** Access denied. */
        ACCESS_DENIED("Access is denied"),

        /** Invalid request. */
        INVALID_REQUEST("The request was invalid"),
        /** Invalid response. */
        INVALID_RESPONSE_CONTENT("The content of the response was invalid"),

        /** Throttling. */
        THROTTLING("The request was throttled"),
        /** Request timeout. */
        REQUEST_TIMEOUT("The request timed out"),

        /** Service error. */
        SERVICE_ERROR("There was an error in the service"),

        /** Model not available. */
        MODEL_NOT_AVAILABLE("The requested model is not available"),

        /** Invalid configuration. */
        INVALID_CONFIGURATION("The supplied configuration was invalid"),
        /** Function type not supported. */
        FUNCTION_TYPE_NOT_SUPPORTED("The function is not supported");
        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        /**
         * Gets the error message.
         *
         * @return The error message.
         */
        public String getMessage() {
            return message;
        }
    }
}
