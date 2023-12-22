package com.microsoft.semantickernel.orchestration;

import java.util.List;

import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;

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
}
