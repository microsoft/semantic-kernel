package com.microsoft.semantickernel.plugin;

import javax.annotation.Nullable;

/**
 * Metadata for a parameter to a kernel function. The Semantic Kernel creates
 * this metadata from the annotations on the method that defines the function,
 * or by introspection of a Java method. 
 * @param <T> The type of the parameter.
 */
public class KernelParameterMetadata<T> {

    private final String name;
    @Nullable
    private final String description;
    @Nullable
    private final String defaultValue;
    private final boolean isRequired;
    private final Class<T> parameterType;

    /**
     * Creates a new instance of the {@link KernelParameterMetadata} class.
     * @param name The name of the parameter.
     * @param description The description of the parameter.
     * @param parameterType The type of the parameter.
     * @param defaultValue The default value of the parameter.
     * @param isRequired Whether the parameter is required.
     */
    public KernelParameterMetadata(
        String name,
        @Nullable String description,
        Class<T> parameterType,
        @Nullable String defaultValue,
        boolean isRequired) {
        this.name = name;
        this.description = description;
        this.defaultValue = defaultValue;
        this.isRequired = isRequired;
        this.parameterType = parameterType;
    }

    /**
     * Gets the name of the parameter.
     * @return The name of the parameter.
     */
    public String getName() {
        return name;
    }

    /**
     * Gets the description of the parameter.
     * @return The description of the parameter.
     */
    @Nullable
    public String getDescription() {
        return description;
    }

    /**
     * Gets the default value of the parameter.
     * @return The default value of the parameter.
     */
    @Nullable
    public String getDefaultValue() {
        return defaultValue;
    }

    /**
     * Gets whether the parameter is required.
     * @return Whether the parameter is required.
     */
    public boolean isRequired() {
        return isRequired;
    }

    /**
     * Gets the type of the parameter.
     * @return The type of the parameter.
     */
    public Class<?> getType() {
        return parameterType;
    }
}
