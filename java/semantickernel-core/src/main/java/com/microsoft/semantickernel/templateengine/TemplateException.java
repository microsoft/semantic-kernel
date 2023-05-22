// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine;

import com.microsoft.semantickernel.SKException;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class TemplateException extends SKException {

    @Nonnull private final ErrorCodes errorCode;

    /**
     * Initializes a new instance of the {@code TemplateException} class with a provided error code.
     *
     * @param error The error code.
     */
    public TemplateException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

    /**
     * Initializes a new instance of the {@code TemplateException} class with a provided error code.
     *
     * @param error The error code.
     * @param message The exception message.
     */
    public TemplateException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    /**
     * Initializes a new instance of the {@code TemplateException} class with a provided error code.
     *
     * @param error The error code.
     * @param message The exception message.
     * @param innerException The exception that is the cause of the current exception.
     */
    public TemplateException(
            @Nonnull ErrorCodes errorCode,
            @Nullable String message,
            @Nullable Throwable innerException) {
        super(getDefaultMessage(errorCode, message), innerException);
        this.errorCode = errorCode;
    }

/**
 * <p>
 * Gets the error code for this exception.
 * </p>
 */
    public ErrorCodes getErrorCode() {
        return errorCode;
    }

/**
 * <p>
 * Translate the error code into a default message.
 * </p>
 */
    private static String getDefaultMessage(
            @Nonnull ErrorCodes errorCode, @Nullable String message) {
        return String.format("%s: %s", errorCode.getMessage(), message);
    }

/**
 * <p>
 * Error codes for {@code TemplateException}.
 * </p>
 */

    public enum ErrorCodes {
      /**
        * <p>
        * Unknown error.
        * </p>
        */
        UnknownError("Unknown error"),

      /**
        * <p>
        * Syntax error, the template syntax used is not valid.
        * </p>
        */
        SyntaxError("Syntax error, the template syntax used is not valid"),

        UnexpectedBlockType("The block type produced be the tokenizer was not expected"),

        FunctionNotFound("The template requires an unknown function"),


      /**
        * <p>
        * The template execution failed, e.g. a function call threw an exception.
        * </p>
        */
        RuntimeError("The template execution failed, e.g. a function call threw an exception"),
        ;

        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        public String getMessage() {
            return message;
        }
    }
}
