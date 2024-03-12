// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.plugin.KernelReturnParameterMetadata;

/**
 * Metadata about a kernel function.
 *
 * @param <T> The type of the return value of the function.
 */
public class KernelFunctionMetadata<T> {

    private final String name;
    @Nullable
    private final String pluginName;
    @Nullable
    private final String description;
    private final List<KernelParameterMetadata<?>> parameters;
    private final KernelReturnParameterMetadata<T> returnParameter;

    /**
     * Create a new instance of KernelFunctionMetadata.
     *
     * @param pluginName      The name of the plugin to which the function belongs
     * @param name            The name of the function.
     * @param description     The description of the function.
     * @param parameters      The parameters of the function.
     * @param returnParameter The return parameter of the function.
     */
    public KernelFunctionMetadata(
        @Nullable String pluginName,
        String name,
        @Nullable String description,
        @Nullable List<KernelParameterMetadata<?>> parameters,
        KernelReturnParameterMetadata<T> returnParameter) {
        this.pluginName = pluginName;
        this.name = name;
        this.description = description;
        if (parameters == null) {
            this.parameters = new ArrayList<>();
        } else {
            this.parameters = new ArrayList<>(parameters);
        }

        this.returnParameter = returnParameter;
    }

    /**
     * Get the name of the plugin to which the function belongs
     *
     * @return The name of the function.
     */
    @Nullable
    public String getPluginName() {
        return pluginName;
    }

    /**
     * Get the name of the function.
     *
     * @return The name of the function.
     */
    public String getName() {
        return name;
    }

    /**
     * Get the parameters of the function.
     *
     * @return The parameters of the function.
     */
    public List<KernelParameterMetadata<?>> getParameters() {
        return Collections.unmodifiableList(parameters);
    }

    /**
     * Get the description of the function.
     *
     * @return The description of the function.
     */
    @Nullable
    public String getDescription() {
        return description;
    }

    /**
     * Get the return parameter of the function.
     *
     * @return The return parameter of the function.
     */
    public KernelReturnParameterMetadata<T> getReturnParameter() {
        return returnParameter;
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, pluginName, description, parameters, returnParameter);
    }
        

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (obj == null || getClass() != obj.getClass())
            return false;
            
        KernelFunctionMetadata<?> other = (KernelFunctionMetadata<?>) obj;
        if (!Objects.equals(name, other.name))
            return false;
        if (!Objects.equals(pluginName, other.pluginName))
            return false;
        if (!Objects.equals(description, other.description))
            return false;
        if (!Objects.equals(parameters, other.parameters))
            return false;
        return Objects.equals(returnParameter, other.returnParameter);
    }

    
}
