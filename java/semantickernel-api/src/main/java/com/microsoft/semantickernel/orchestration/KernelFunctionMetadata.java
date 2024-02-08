package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;
import java.util.List;

public class KernelFunctionMetadata {

    private final String name;
    private final String description;
    private final List<KernelParameterMetadata> parameters;
    private final KernelReturnParameterMetadata<?> returnParameter;

    public KernelFunctionMetadata(
        String name,
        String description,
        List<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata<?> returnParameter) {
        this.name = name;
        this.description = description;
        this.parameters = parameters;
        this.returnParameter = returnParameter;
    }

    public String getName() {
        return name;
    }

    public List<KernelParameterMetadata> getParameters() {
        return parameters;
    }

    public String getDescription() {
        return description;
    }

    public KernelReturnParameterMetadata<?> getReturnParameter() {
        return returnParameter;
    }
}
