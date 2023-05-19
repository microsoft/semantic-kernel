// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.diagnostics;

import javax.annotation.Nullable;

/** Provides the base exception from which all Semantic Kernel exceptions derive. */
public class SKException extends RuntimeException {

    /** Initializes a new instance of the {@code SKException} class with a default message. */
    protected SKException() {
        super();
    }

    /**
     * Initializes a new instance of the {@code SKException} class with its message set to {@code
     * message}.
     *
     * @param message A string that describes the error.
     */
    protected SKException(@Nullable String message) {
        super(message);
    }

    /**
     * Initializes a new instance of the {@code SKException} class with its message set to {@code
     * message}.
     *
     * @param message A string that describes the error.
     * @param cause The exception that is the cause of the current exception.
     */
    protected SKException(@Nullable String message, @Nullable Throwable cause) {
        super(message, cause);
    }
}
