// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

/**
 * Interface for all builders that create Buildable objects. Typically, these builders can be
 * obtained via {@link com.microsoft.semantickernel.SKBuilders}.
 *
 * @param <T>
 */
public interface SemanticKernelBuilder<T extends Buildable> {

    /**
     * Build the object.
     *
     * @return a constructed object.
     */
    T build();
}
