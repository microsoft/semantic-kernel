// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * Provides the base exception from which all CHECKED Semantic Kernel exceptions derive.
 */
public class SKCheckedException extends Exception {

    /**
     * Initializes a new instance of the {@code SKCheckedException} class with a default message.
     */
    protected SKCheckedException() {
        super();
    }

    /**
     * Initializes a new instance of the {@code SKCheckedException} class with its message set to
     * {@code message}.
     *
     * @param message A string that describes the error.
     */
    public SKCheckedException(@Nullable String message) {
        super(message);
    }

    /**
     * Initializes a new instance of the {@code SKCheckedException} class with its message set to
     * {@code message}.
     *
     * @param message A string that describes the error.
     * @param cause   The exception that is the cause of the current exception.
     */
    public SKCheckedException(@Nullable String message, @Nullable Throwable cause) {
        super(message, cause);
    }

    public SKCheckedException(Throwable e) {
        super(e);
    }

    /**
     * Forms a checked exception, if the exception is already an SK exception, it will be unwrapped
     * and the cause extracted.
     *
     * @param message The message to be displayed
     * @param e       The exception to be thrown
     * @return A checked exception
     */
    public static SKCheckedException build(
        String message,
        @Nullable Exception e) {

        if (e == null) {
            return new SKCheckedException(message);
        }

        Throwable cause = e.getCause();

        if ((e instanceof SKCheckedException || e instanceof SKException) && cause != null) {
            return new SKCheckedException(message, cause);
        } else {
            return new SKCheckedException(message, e);
        }
    }

    /**
     * Translate the error code into a default message format.
     *
     * @param errorMessage The error message from an error code
     * @param message      The message from the code which throws the exception
     * @return A formatted message
     */
    protected static String formatDefaultMessage(
        @Nonnull String errorMessage, @Nullable String message) {
        return SKException.formatDefaultMessage(errorMessage, message);
    }
}
