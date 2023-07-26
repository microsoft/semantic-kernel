// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import javax.annotation.Nullable;

/** Provides the base exception from which all CHECKED Semantic Kernel exceptions derive. */
public class SKCheckedException extends Exception {

    /** Initializes a new instance of the {@code SKCheckedException} class with a default message. */
    protected SKCheckedException() {
        super();
    }

    /**
     * Initializes a new instance of the {@code SKCheckedException} class with its message set to {@code
     * message}.
     *
     * @param message A string that describes the error.
     */
    protected SKCheckedException(@Nullable String message) {
        super(message);
    }

    /**
     * Initializes a new instance of the {@code SKCheckedException} class with its message set to {@code
     * message}.
     *
     * @param message A string that describes the error.
     * @param cause The exception that is the cause of the current exception.
     */
    protected SKCheckedException(@Nullable String message, @Nullable Throwable cause) {
        super(message, cause);
    }
}
