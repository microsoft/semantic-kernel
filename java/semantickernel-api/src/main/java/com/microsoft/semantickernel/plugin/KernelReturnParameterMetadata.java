package com.microsoft.semantickernel.plugin;

import javax.annotation.Nullable;

public class KernelReturnParameterMetadata<T> {

    @Nullable
    private final String description;
    private final Class<T> parameterType;

    public KernelReturnParameterMetadata(
        @Nullable
        String description,
        Class<T> parameterType) {
        this.description = description;
        this.parameterType = parameterType;
    }

    @Nullable
    public String getDescription() {
        return description;
    }

    public Class<T> getParameterType() {
        return parameterType;
    }
}
