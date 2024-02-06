package com.microsoft.semantickernel.orchestration;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromMethod.ImplementationFunc;

public class MethodDetails {

    private final String name;
    @Nullable
    private final String description;
    private final ImplementationFunc function;
    private final List<KernelParameterMetadata<?>> parameters;
    private final KernelReturnParameterMetadata<?> returnParameter;

    public MethodDetails(
        String name,
        @Nullable
        String description,
        ImplementationFunc function,
        List<KernelParameterMetadata<?>> parameters,
        KernelReturnParameterMetadata<?> returnParameter) {
        this.name = name;
        this.description = description;
        this.function = function;
        this.parameters = new ArrayList<>(parameters);
        this.returnParameter = returnParameter;
    }

    public String getName() {
        return name;
    }

    @Nullable
    public String getDescription() {
        return description;
    }

    public ImplementationFunc getFunction() {
        return function;
    }

    public List<KernelParameterMetadata<?>> getParameters() {
        return Collections.unmodifiableList(parameters);
    }

    public KernelReturnParameterMetadata<?> getReturnParameter() {
        return returnParameter;
    }
}
