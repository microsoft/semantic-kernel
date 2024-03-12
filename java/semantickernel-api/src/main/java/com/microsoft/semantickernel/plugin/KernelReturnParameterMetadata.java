// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.plugin;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import java.util.Objects;

/**
 * Metadata for a return parameter of a {@link KernelFunction}.
 *
 * @param <T> the type of the return parameter
 */
public class KernelReturnParameterMetadata<T> {

    @Nullable
    private final String description;
    private final Class<T> parameterType;

    /**
     * Creates a new instance of {@link KernelReturnParameterMetadata}.
     *
     * @param description   the description of the return parameter
     * @param parameterType the type of the return parameter
     */
    public KernelReturnParameterMetadata(
        @Nullable String description,
        Class<T> parameterType) {
        this.description = description;
        this.parameterType = parameterType;
    }

    /**
     * Gets the description of the return parameter.
     *
     * @return the description of the return parameter
     */
    @Nullable
    public String getDescription() {
        return description;
    }

    /**
     * Gets the type of the return parameter.
     *
     * @return the type of the return parameter
     */
    public Class<T> getParameterType() {
        return parameterType;
    }

    @Override
    public int hashCode() {
        return Objects.hash(description, parameterType);
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (obj == null || getClass() != obj.getClass())
            return false;
        
        KernelReturnParameterMetadata<?> other = (KernelReturnParameterMetadata<?>) obj;
        if (!Objects.equals(description, other.description))
            return false;
        return Objects.equals(parameterType, other.parameterType);
    }

    
}
