// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import com.microsoft.semantickernel.SKException;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Exception thrown for errors related to memory logic. */
public class MemoryException extends SKException {
    @Nonnull private final ErrorCodes errorCode;

    /**
     * Initializes a new instance of the {@code MemoryException} class with a provided error code.
     *
     * @param error The error code.
     */
    public MemoryException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

    /**
     * Initializes a new instance of the {@code MemoryException} class with a provided error code
     * and message.
     *
     * @param errorCode The error code.
     * @param message A string that describes the error.
     */
    public MemoryException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    /**
     * Initializes a new instance of the {@code MemoryException} class with a provided error code,
     * message, and inner exception.
     *
     * @param errorCode The error code.
     * @param message A string that describes the error.
     * @param innerException The exception that is the cause of the current exception.
     */
    public MemoryException(
            @Nonnull ErrorCodes errorCode,
            @Nullable String message,
            @Nullable Throwable innerException) {
        super(formatDefaultMessage(errorCode.getMessage(), message), innerException);
        this.errorCode = errorCode;
    }

    /**
     * Gets the error code for this exception.
     *
     * @return The error code for this exception.
     */
    public ErrorCodes getErrorCode() {
        return errorCode;
    }


    /** Semantic kernel memory error codes. */
    public enum ErrorCodes {
        /** Unknown error. */
        UNKNOWN("Unknown error"),

        /** Failed to create collection. */
        FAILED_TO_CREATE_COLLECTION("Failed to create collection"),

        /** Failed to delete collection. */
        FAILED_TO_DELETE_COLLECTION("Failed to delete collection"),

        /** Unable to construct memory from serialized metadata. */
        UNABLE_TO_DESERIALIZE_MEMORY("Unable to deserialize memory"),

        /** Unable to serialize a memory . */
        UNABLE_TO_SERIALIZE_MEMORY("Unable to serialize memory"),

        /** Attempted to access a memory collection that does not exist. */
        ATTEMPTED_TO_ACCESS_NONEXISTENT_COLLECTION("Attempted to access non-existent collection"),
        MEMORY_NOT_FOUND("Memory not found");

        /**
         * Gets the error message.
         *
         * @return The error message.
         */
        public String getMessage() {
            return message;
        }

        private ErrorCodes(String message) {
            this.message = message;
        }

        private final String message;
    }
}
