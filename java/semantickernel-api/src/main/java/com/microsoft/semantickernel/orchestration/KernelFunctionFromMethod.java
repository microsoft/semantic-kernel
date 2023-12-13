package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;
import java.lang.reflect.Method;
import java.util.List;

public class KernelFunctionFromMethod {

    public static KernelFunction create(
        Method method,
        Object target,
        String functionName,
        String description,
        List<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata returnParameter) {
        return null;
    }
}
