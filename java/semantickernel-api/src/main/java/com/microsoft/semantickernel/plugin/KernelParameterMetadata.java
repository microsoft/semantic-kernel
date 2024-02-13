package com.microsoft.semantickernel.plugin;

import javax.annotation.Nullable;

public class KernelParameterMetadata<T> {

    /// <summary>The name of the parameter.</summary>
    private final String name;
    /// <summary>The description of the parameter.</summary>
    @Nullable
    private final String description;
    @Nullable
    private final String defaultValue;
    private final boolean isRequired;
    private final Class<T> parameterType;

    public KernelParameterMetadata(
        String name,
        @Nullable
        String description,
        Class<T> parameterType,
        @Nullable
        String defaultValue,
        boolean isRequired) {
        this.name = name;
        this.description = description;
        this.defaultValue = defaultValue;
        this.isRequired = isRequired;
        this.parameterType = parameterType;
    }

    public String getName() {
        return name;
    }

    @Nullable
    public String getDescription() {
        return description;
    }

    @Nullable
    public String getDefaultValue() {
        return defaultValue;
    }

    public boolean isRequired() {
        return isRequired;
    }

    public Class<?> getType() {
        return parameterType;
    }

    //private KernelJsonSchema schema;
}
