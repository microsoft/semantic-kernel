// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine;

import com.microsoft.semantickernel.SKException;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class TemplateException extends SKException {

    @Nonnull private final ErrorCodes errorCode;

/**
 * <p>
 * Initializes a new instance of the {@code TemplateException} class with a provided error code.
 * </p>
 * @param error The error code.
 */
    public TemplateException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

/**
 * <p>
 * Initializes a new instance of the {@code TemplateException} class with a provided error code.
 * </p>
 * @param error The error code.
 * @param message The exception message.
 */
    public TemplateException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    public TemplateException(
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

    public enum ErrorCodes {
        UnknownError("Unknown error"),

        SyntaxError("Syntax error, the template syntax used is not valid"),

        UnexpectedBlockType("The block type produced be the tokenizer was not expected"),

        FunctionNotFound("The template requires an unknown function"),

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
