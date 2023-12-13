package com.microsoft.semantickernel.plugin;

public class KernelReturnParameterMetadata {

    private final String description;
    private final String parameterType;

    public KernelReturnParameterMetadata(String description, String parameterType) {
        this.description = description;
        this.parameterType = parameterType;
    }

    public String getDescription() {
        return description;
    }

    public String getParameterType() {
        return parameterType;
    }
}
