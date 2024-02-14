package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromMethod.ImplementationFunc;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.annotation.Nullable;

/**
 * Metadata for a method that can be used as a kernel function.
 */
public class MethodDetails {

    private final String name;
    @Nullable
    private final String description;
    private final ImplementationFunc<?> function;
    private final List<KernelParameterMetadata<?>> parameters;
    private final KernelReturnParameterMetadata<?> returnParameter;

    /**
     * Constructor.
     *
     * @param name            The name of the method.
     * @param description     The description of the method.
     * @param function        The function that implements the method.
     * @param parameters      The parameters of the method.
     * @param returnParameter The return parameter of the method.
     */
    public MethodDetails(
        String name,
        @Nullable String description,
        ImplementationFunc<?> function,
        List<KernelParameterMetadata<?>> parameters,
        KernelReturnParameterMetadata<?> returnParameter) {
        this.name = name;
        this.description = description;
        this.function = function;
        this.parameters = new ArrayList<>(parameters);
        this.returnParameter = returnParameter;
    }

    /**
     * Get the name of the method.
     * @return The name of the method.
     */
    public String getName() {
        return name;
    }

    /**
     * Get the description of the method.
     * @return The description of the method.
     */
    @Nullable
    public String getDescription() {
        return description;
    }

    /**
     * Get the function that implements the method. This is an internal detail.
     * @return The function that implements the method.
     */
    public ImplementationFunc<?> getFunction() {
        return function;
    }

    /**
     * Get the parameters of the method.
     * @return The parameters of the method.
     */
    public List<KernelParameterMetadata<?>> getParameters() {
        return Collections.unmodifiableList(parameters);
    }

    /**
     * Get the return parameter of the method.
     * @return The return parameter of the method.
     */
    public KernelReturnParameterMetadata<?> getReturnParameter() {
        return returnParameter;
    }
}
