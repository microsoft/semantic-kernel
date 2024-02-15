// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

/**
 * Interface for all builders that create Buildable objects.
 *
 * @param <T> the type of {@code Buildable} to build.
 */
public interface SemanticKernelBuilder<T extends Buildable> {

    /**
     * Build the object.
     *
     * @return a constructed object.
     */
    T build();
}
