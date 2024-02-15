// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.semantickernel;

import com.microsoft.semantickernel.exceptions.SKException;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * Exception thrown when a template error occurs.
 */
public class TemplateException extends SKException {

    @Nonnull
    private final ErrorCodes errorCode;

    /**
     * Initializes a new instance of the {@code TemplateException} class with a provided error
     * code.
     *
     * @param error The error code.
     */
    public TemplateException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

    /**
     * Initializes a new instance of the {@code TemplateException} class with a provided error
     * code.
     *
     * @param errorCode The error code.
     * @param message   The exception message.
     */
    public TemplateException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    /**
     * Initializes a new instance of the {@code TemplateException} class with a provided error
     * code.
     *
     * @param errorCode      The error code.
     * @param message        The exception message.
     * @param innerException The exception that is the cause of the current exception.
     */
    public TemplateException(
        @Nonnull ErrorCodes errorCode,
        @Nullable String message,
        @Nullable Throwable innerException) {
        super(formatDefaultMessage(errorCode.getMessage(), message), innerException);
        this.errorCode = errorCode;
    }

    // spotless:off

    /**
     * Gets the error code for this exception.
     * @return The error code.
     */
    //spotless:on
    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    // spotless:off

    /**
     * Error codes for {@code TemplateException}.
     */
    //spotless:on
    public enum ErrorCodes {

        // spotless:off
        /**
         * Unknown error.
         */
        //spotless:on
        UNKNOWN_ERROR("Unknown error"),

        // spotless:off
        /**
         * Syntax error, the template syntax used is not valid.
         */
        //spotless:on
        SYNTAX_ERROR("Syntax error, the template syntax used is not valid"),

        // spotless:off
        /**
         * The block type produced be the tokenizer was not expected.
         */
        UNEXPECTED_BLOCK_TYPE("The block type produced be the tokenizer was not expected"),

        //spotless:off
        /**
         * The template requires an unknown function.
         */
        //spotless:on
        FUNCTION_NOT_FOUND("The template requires an unknown function"),

        // spotless:off
        /**
         * The template execution failed, e.g. a function call threw an exception.
         */
        //spotless:on
        RUNTIME_ERROR("The template execution failed, e.g. a function call threw an exception");

        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        // spotless:off
        /**
         * Gets the message for the error code.
         * @return The error code message
         */
        //spotless:on
        public String getMessage() {
            return message;
        }
    }
}
