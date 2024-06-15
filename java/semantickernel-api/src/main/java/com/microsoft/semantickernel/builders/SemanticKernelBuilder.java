// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

/**
 * Interface for all builders.
 *
 * @param <T> the type to build.
 */
public interface SemanticKernelBuilder<T> {

    /**
     * Build the object.
     *
     * @return a constructed object.
     */
    T build();
}
