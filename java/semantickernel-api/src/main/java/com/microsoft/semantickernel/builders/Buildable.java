// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

/**
 * A marker interface for all classes that are buildable. By convention, {@code Buildable}
 * classes will have a {@code public static Builder builder()} method for obtaining a
 * {@link SemanticKernelBuilder} for the given class.
 */
public interface Buildable {}
