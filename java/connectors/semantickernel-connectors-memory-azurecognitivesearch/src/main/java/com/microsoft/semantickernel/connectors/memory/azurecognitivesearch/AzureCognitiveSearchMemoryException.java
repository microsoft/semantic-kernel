// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.microsoft.semantickernel.SKException;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class AzureCognitiveSearchMemoryException extends SKException {
    private final ErrorCodes errorCode;

    /**
     * Create an exception with a message
     *
     * @param errorCode The error code
     */
    public AzureCognitiveSearchMemoryException(@Nonnull ErrorCodes errorCode) {
        this(errorCode, null, null);
    }

    /**
     * Create an exception with a message
     *
     * @param message a description of the cause of the exception
     */
    public AzureCognitiveSearchMemoryException(
            @Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    /**
     * Create an exception with a message and a cause
     *
     * @param errorCode the error code
     * @param message a description of the cause of the exception
     * @param cause the cause of the exception
     */
    public AzureCognitiveSearchMemoryException(
            @Nonnull ErrorCodes errorCode, @Nullable String message, @Nullable Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    public enum ErrorCodes {
        UNKNOWN_ERROR("Unknown error"),
        INVALID_EMBEDDING_SIZE("Invalid embedding size"),
        INVALID_INDEX_NAME("Invalid index name"),
        READ_FAILURE("Read failure"),
        WRITE_FAILURE("Write failure");

        final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        public String getMessage() {
            return message;
        }
    }
}
