// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.microsoft.semantickernel.SKException;

import javax.annotation.Nullable;

/** Exception thrown by the Azure Cognitive Search connector */
public class AzureCognitiveSearchMemoryException extends SKException {
    /**
     * Initializes a new instance of the {@code AzureCognitiveSearchMemoryException} class.
     *
     * @param message Exception message.
     */
    public AzureCognitiveSearchMemoryException(@Nullable String message) {
        super(message);
    }

    /**
     * Initializes a new instance of the {@code AzureCognitiveSearchMemoryException} class.
     *
     * @param message Exception message.
     * @param cause Cause of the exception, if any.
     */
    public AzureCognitiveSearchMemoryException(
            @Nullable String message, @Nullable Throwable cause) {
        super(message, cause);
    }
}
