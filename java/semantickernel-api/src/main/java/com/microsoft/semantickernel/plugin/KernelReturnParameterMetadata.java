package com.microsoft.semantickernel.plugin;

public class KernelReturnParameterMetadata<T> {

    private final String description;
    private final Class<T> parameterType;

    public KernelReturnParameterMetadata(
        String description,
        Class<T> parameterType) {
        this.description = description;
        this.parameterType = parameterType;
    }

    public String getDescription() {
        return description;
    }

    public Class<T> getParameterType() {
        return parameterType;
    }
}
