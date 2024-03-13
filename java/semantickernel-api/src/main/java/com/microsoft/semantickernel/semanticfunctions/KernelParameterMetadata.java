// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import java.util.Objects;
import javax.annotation.Nullable;

/**
 * Metadata for a parameter to a kernel function. The Semantic Kernel creates this metadata from the
 * annotations on the method that defines the function, or by introspection of a Java method.
 *
 * @param <T> The type of the parameter.
 */
public class KernelParameterMetadata<T> {

    private final InputVariable inputVariable;
    private final Class<T> parameterType;

    /**
     * Creates a new instance of the {@link KernelParameterMetadata} class.
     *
     * @param inputVariable The input variable.
     * @param typeClass     The type of the parameter.
     */
    KernelParameterMetadata(InputVariable inputVariable, Class<T> typeClass) {
        this.inputVariable = inputVariable;
        this.parameterType = typeClass;
    }

    /**
     * Creates a new instance of the {@link KernelParameterMetadata} class.
     *
     * @param inputVariable The input variable.
     * @return The new instance of the {@link KernelParameterMetadata} class.
     */
    public static KernelParameterMetadata<?> build(InputVariable inputVariable) {
        return new KernelParameterMetadata<>(inputVariable, inputVariable.getTypeClass());
    }

    /**
     * Creates a new instance of the {@link KernelParameterMetadata} class.
     *
     * @param <T>           The type of the parameter.
     * @param inputVariable The input variable.
     * @param tClass        The type of the parameter.
     * @return The new instance of the {@link KernelParameterMetadata} class.
     */
    public static <T> KernelParameterMetadata<T> build(
        InputVariable inputVariable,
        Class<T> tClass) {
        Class<?> inputClass = inputVariable.getTypeClass();

        if (tClass.isAssignableFrom(inputClass)) {
            return new KernelParameterMetadata<>(inputVariable, tClass);
        } else {
            throw new IllegalArgumentException(
                "The type of the input variable does not match the type of the parameter.");
        }
    }

    /**
     * Creates a new instance of the {@link KernelParameterMetadata} class.
     *
     * @param name         The name of the parameter.
     * @param type         The type of the parameter.
     * @param description  The description of the parameter.
     * @param defaultValue The default value of the parameter.
     * @param required     Whether the parameter is required.
     * @return The new instance of the {@link KernelParameterMetadata} class.
     */
    public static KernelParameterMetadata<?> build(
        String name,
        Class<?> type,
        @Nullable String description,
        @Nullable String defaultValue,
        boolean required) {
        return build(new InputVariable(name, type.getName(), description, defaultValue, required));
    }

    /**
     * Gets the name of the parameter.
     *
     * @return The name of the parameter.
     */
    public String getName() {
        return inputVariable.getName();
    }

    /**
     * Gets the description of the parameter.
     *
     * @return The description of the parameter.
     */
    @Nullable
    public String getDescription() {
        return inputVariable.getDescription();
    }

    /**
     * Gets the default value of the parameter.
     *
     * @return The default value of the parameter.
     */
    @Nullable
    public String getDefaultValue() {
        return inputVariable.getDefaultValue();
    }

    /**
     * Gets whether the parameter is required.
     *
     * @return Whether the parameter is required.
     */
    public boolean isRequired() {
        return inputVariable.isRequired();
    }

    /**
     * Gets the type of the parameter.
     *
     * @return The type of the parameter.
     */
    public Class<?> getType() {
        return inputVariable.getTypeClass();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!getClass().isInstance(o)) {
            return false;
        }
        KernelParameterMetadata<?> that = (KernelParameterMetadata<?>) o;
        return Objects.equals(inputVariable, that.inputVariable) && Objects.equals(parameterType,
            that.parameterType);
    }

    @Override
    public int hashCode() {
        return Objects.hash(inputVariable, parameterType);
    }
}
