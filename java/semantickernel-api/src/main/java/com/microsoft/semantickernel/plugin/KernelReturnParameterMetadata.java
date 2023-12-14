package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.Todo;

public class KernelReturnParameterMetadata {

    private final String description;

    public KernelReturnParameterMetadata(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }

    public String getParameterType() {
        throw new Todo();
    }
}
