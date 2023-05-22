// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

/** Provides the base exception from which all Semantic Kernel exceptions derive. */
public class SKException extends RuntimeException {
    public SKException(String message) {
        super(message);
    }
}
