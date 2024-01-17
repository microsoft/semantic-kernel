package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;
import java.util.List;

public class KernelFunctionMetadata {

    /// <summary>The name of the function.</summary>
    private final String name;
    /// <summary>The description of the function.</summary>
    private final String description;
    /// <summary>The function's parameters.</summary>
    private final List<KernelParameterMetadata> parameters;


    /// <summary>The function's return parameter.</summary>
    private final KernelReturnParameterMetadata returnParameter;


    public KernelFunctionMetadata(
        String name,
        String description,
        List<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata returnParameter) {
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

    public KernelReturnParameterMetadata getReturnParameter() {
        return returnParameter;
    }
}
