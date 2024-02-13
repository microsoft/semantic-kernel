package com.microsoft.semantickernel.orchestration;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;

public class KernelFunctionMetadata<T> {

    private final String name;
    @Nullable
    private final String description;
    private final List<KernelParameterMetadata<?>> parameters;
    private final KernelReturnParameterMetadata<T> returnParameter;

    public KernelFunctionMetadata(
        String name,
        @Nullable
        String description,
        @Nullable
        List<KernelParameterMetadata<?>> parameters,
        KernelReturnParameterMetadata<T> returnParameter) {
        this.name = name;
        this.description = description;
        if (parameters == null) {
            this.parameters = new ArrayList<>();
        } else {
            this.parameters = new ArrayList<>(parameters);
        }

        this.returnParameter = returnParameter;
    }

    public String getName() {
        return name;
    }

    public List<KernelParameterMetadata<?>> getParameters() {
        return Collections.unmodifiableList(parameters);
    }

    @Nullable
    public String getDescription() {
        return description;
    }

    public KernelReturnParameterMetadata<T> getReturnParameter() {
        return returnParameter;
    }
}
